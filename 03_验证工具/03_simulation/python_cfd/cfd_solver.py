"""
cfd_solver.py — 2D蛋形截面简化CFD求解器 (FDM)
=================================================
在蛋形截面上求解定常不可压缩NS方程的2D截面问题。

============================================
数学模型
============================================

涡量-流函数 (ω-ψ) 公式:
  流函数 ψ 满足: ∇²ψ = -ω      (Poisson方程)
  速度场从 ψ 重构: u_x = ∂ψ/∂y, u_y = -∂ψ/∂x

  涡量传输方程:
    ∂ω/∂t + u·∇ω = ν·∇²ω + γ·ω/2   (含轴向拉伸源项)

  其中 γ·ω/2 来自 v_z = γ·z 的分量。

边界条件:
  壁面: no-slip (u=v=0, 用掩码法实现)
  中心: 轴对称条件

求解算法（伪瞬态法）:
  1. 从当前速度计算涡量 ω
  2. 求解 Poisson 方程 ∇²ψ = -ω (Jacobi/SOR迭代)
  3. 从 ψ 重构新速度
  4. 更新涡量（含对流和扩散）
  5. 施加边界条件

⚠️ 这是一个简化求解器（笛卡尔网格 + 掩码法），
   用于快速验证和趋势分析。
   高精度计算请用 OpenFOAM 的 icoFoam/simpleFoam。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from dataclasses import dataclass
from tqdm import tqdm

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '01_geometry'))
from egg_curve import EggCurve, EggParams


@dataclass
class SolverConfig:
    """求解器配置"""
    nu: float = 0.01             # 运动粘度
    gamma: float = 1.0           # 轴向拉伸率
    Gamma: float = 1.0           # 环量
    dt: float = 0.001            # 时间步长 (伪瞬态)
    n_steps: int = 5000          # 迭代步数
    tol: float = 1e-6            # 收敛判据
    n_grid: int = 100            # 截面网格数 (每个方向)
    save_every: int = 500        # 保存间隔


class EggSectionSolver:
    """
    蛋形截面2D涡量-流函数求解器
    
    使用极坐标式网格 (r, θ), 映射到蛋形截面
    """

    def __init__(self, egg_params: EggParams, config: SolverConfig):
        self.egg = EggCurve(egg_params)
        self.cfg = config
        self.ep = egg_params

    def setup_grid(self):
        """设置计算网格"""
        n = self.cfg.n_grid

        # 在蛋形曲线的包围盒上建笛卡尔网格
        x_bnd, y_bnd = self.egg.get_curve_points(500)
        xmin, xmax = np.min(x_bnd), np.max(x_bnd)
        ymin, ymax = np.min(y_bnd), np.max(y_bnd)

        # 留余量
        margin = 0.05
        xmin -= margin * (xmax - xmin)
        xmax += margin * (xmax - xmin)
        ymin -= margin * (ymax - ymin)
        ymax += margin * (ymax - ymin)

        self.x = np.linspace(xmin, xmax, n)
        self.y = np.linspace(ymin, ymax, n)
        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]
        self.X, self.Y = np.meshgrid(self.x, self.y)

        # 蛋形内部掩码
        self.mask = self._egg_mask(self.X, self.Y)

        # 中心点
        self.cx = 0.0
        self.cy = (ymax + ymin) / 2

        # 距中心距离
        self.R = np.sqrt((self.X - self.cx)**2 + (self.Y - self.cy)**2)
        self.R_safe = np.where(self.R < 1e-10, 1e-10, self.R)
        self.Theta = np.arctan2(self.Y - self.cy, self.X - self.cx)

    def _egg_mask(self, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        """判断网格点是否在蛋形截面内部"""
        z0, sa, ca = self.ep.z0, self.ep.sin_a, self.ep.cos_a
        inner = 1.0 / (z0 - Y * sa)**2 - (Y * ca)**2
        inside = (inner > 0) & (X**2 < inner)
        return inside.astype(float)

    def initialize(self):
        """初始化场变量"""
        n = self.cfg.n_grid
        G, g, nu = self.cfg.Gamma, self.cfg.gamma, self.cfg.nu

        # Burgers涡初始场
        r = self.R_safe
        vtheta = G / (2 * np.pi * r) * (1 - np.exp(-g * r**2 / (4 * nu)))
        vr = -g * r / 2

        # 转换为笛卡尔速度
        self.ux = -vtheta * np.sin(self.Theta) + vr * np.cos(self.Theta)
        self.uy = vtheta * np.cos(self.Theta) + vr * np.sin(self.Theta)

        # 涡量
        self.omega = G * g / (4 * np.pi * nu) * np.exp(-g * r**2 / (4 * nu))

        # 流函数
        self.psi = G / (4 * np.pi) * np.log(r) - G / (4 * np.pi) * (
            np.log(r) + g * r**2 / (4 * nu)  # 近似
        )

        # 压力
        self.p = np.zeros_like(self.ux)

        # 应用蛋形掩码
        self.ux *= self.mask
        self.uy *= self.mask
        self.omega *= self.mask
        self.psi *= self.mask

        # 壁面处速度为零
        self._apply_bc()

    def _apply_bc(self):
        """施加边界条件: 壁面no-slip"""
        # 找到边界单元 (内部与外部的交界)
        boundary = np.zeros_like(self.mask)
        boundary[1:-1, 1:-1] = (
            (self.mask[1:-1, 1:-1] > 0) &
            ((self.mask[:-2, 1:-1] == 0) | (self.mask[2:, 1:-1] == 0) |
             (self.mask[1:-1, :-2] == 0) | (self.mask[1:-1, 2:] == 0))
        )

        # 壁面速度为零
        self.ux[boundary > 0] = 0
        self.uy[boundary > 0] = 0

        # 外部区域清零
        self.ux[self.mask == 0] = 0
        self.uy[self.mask == 0] = 0
        self.omega[self.mask == 0] = 0
        self.psi[self.mask == 0] = 0

    def solve_poisson(self, rhs: np.ndarray, phi: np.ndarray, n_iter: int = 50) -> np.ndarray:
        """
        求解Poisson方程: ∇²φ = f (Jacobi迭代)
        用于流函数方程: ∇²ψ = -ω
        """
        dx2 = self.dx**2
        dy2 = self.dy**2
        coeff = 2 * (1/dx2 + 1/dy2)

        for _ in range(n_iter):
            phi_new = np.copy(phi)
            phi_new[1:-1, 1:-1] = (
                (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2 +
                (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2 -
                rhs[1:-1, 1:-1]
            ) / coeff

            # 只更新内部
            phi_new *= self.mask
            phi_new[self.mask == 0] = 0

            # SOR加速
            omega_sor = 1.5
            phi = phi + omega_sor * (phi_new - phi)

        return phi

    def compute_vorticity(self) -> np.ndarray:
        """从速度场计算涡量: ω = ∂uy/∂x - ∂ux/∂y"""
        duy_dx = np.gradient(self.uy, self.dx, axis=1)
        dux_dy = np.gradient(self.ux, self.dy, axis=0)
        return (duy_dx - dux_dy) * self.mask

    def step(self) -> float:
        """
        执行一步伪瞬态迭代
        
        算法:
          1. 从当前速度计算涡量 ω
          2. 求解Poisson方程得到流函数 ψ
          3. 从流函数重构速度 u
          4. 添加非线性对流项修正
          5. 施加边界条件
        """
        dt = self.cfg.dt
        nu = self.cfg.nu
        g = self.cfg.gamma

        # 1. 计算涡量
        omega_new = self.compute_vorticity()

        # 2. 涡量传输方程 (简化, 忽略对流项):
        #    ∂ω/∂t = ν·∇²ω + γ·ω/2 (轴向拉伸产生的涡量增强)
        laplacian_omega = (
            np.gradient(np.gradient(omega_new, self.dx, axis=1), self.dx, axis=1) +
            np.gradient(np.gradient(omega_new, self.dy, axis=0), self.dy, axis=0)
        )

        # 对流项 (显式)
        domega_dx = np.gradient(omega_new, self.dx, axis=1)
        domega_dy = np.gradient(omega_new, self.dy, axis=0)
        advection = self.ux * domega_dx + self.uy * domega_dy

        # 更新涡量
        omega_new += dt * (nu * laplacian_omega + g * omega_new / 2 - advection)
        omega_new *= self.mask

        # 3. 求解流函数
        self.psi = self.solve_poisson(-omega_new, self.psi, n_iter=20)

        # 4. 从流函数重构速度
        ux_new = np.gradient(self.psi, self.dy, axis=0)
        uy_new = -np.gradient(self.psi, self.dx, axis=1)

        # 5. 残差
        residual = np.max(np.abs(ux_new - self.ux) * self.mask) + np.max(np.abs(uy_new - self.uy) * self.mask)

        # 6. 更新
        self.ux = ux_new * self.mask
        self.uy = uy_new * self.mask
        self.omega = omega_new

        # 7. 施加边界条件
        self._apply_bc()

        return residual

    def solve(self) -> list:
        """运行完整求解过程"""
        self.setup_grid()
        self.initialize()

        residuals = []
        for i in tqdm(range(self.cfg.n_steps), desc="求解中"):
            res = self.step()
            residuals.append(res)

            if i % self.cfg.save_every == 0:
                print(f"  Step {i}: residual = {res:.2e}")

            if res < self.cfg.tol:
                print(f"  ✅ 收敛于 step {i}, residual = {res:.2e}")
                break

        return residuals

    def get_results(self) -> dict:
        """获取求解结果"""
        return {
            'ux': self.ux.copy(),
            'uy': self.uy.copy(),
            'omega': self.omega.copy(),
            'psi': self.psi.copy(),
            'p': self.p.copy(),
            'X': self.X.copy(),
            'Y': self.Y.copy(),
            'mask': self.mask.copy(),
        }


def run_and_visualize():
    """运行求解器并可视化"""
    ep = EggParams(z1=1, z2=2)
    cfg = SolverConfig(n_grid=80, n_steps=3000, dt=0.002, nu=0.02)
    solver = EggSectionSolver(ep, cfg)

    print("=" * 60)
    print("蛋形截面CFD求解器")
    print("=" * 60)
    print(f"  网格: {cfg.n_grid}×{cfg.n_grid}")
    print(f"  ν={cfg.nu}, γ={cfg.gamma}, Γ={cfg.Gamma}")
    print(f"  Re={cfg.Gamma/(2*np.pi*cfg.nu):.1f}")
    print()

    residuals = solver.solve()
    results = solver.get_results()

    # === 可视化 ===
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    X, Y, mask = results['X'], results['Y'], results['mask']
    x_bnd, y_bnd = solver.egg.get_curve_points(500)

    # 涡量
    ax = axes[0, 0]
    data = np.where(mask > 0, results['omega'], np.nan)
    im = ax.pcolormesh(X, Y, data, cmap='RdBu_r', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('ω_z (涡量)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # ux
    ax = axes[0, 1]
    data = np.where(mask > 0, results['ux'], np.nan)
    im = ax.pcolormesh(X, Y, data, cmap='coolwarm', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('u_x', fontsize=13)
    plt.colorbar(im, ax=ax)

    # uy
    ax = axes[0, 2]
    data = np.where(mask > 0, results['uy'], np.nan)
    im = ax.pcolormesh(X, Y, data, cmap='coolwarm', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('u_y', fontsize=13)
    plt.colorbar(im, ax=ax)

    # 速度大小
    ax = axes[1, 0]
    speed = np.sqrt(results['ux']**2 + results['uy']**2)
    data = np.where(mask > 0, speed, np.nan)
    im = ax.pcolormesh(X, Y, data, cmap='hot', shading='auto')
    ax.plot(x_bnd, y_bnd, 'w-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('|v| (速度大小)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # 流函数
    ax = axes[1, 1]
    data = np.where(mask > 0, results['psi'], np.nan)
    im = ax.pcolormesh(X, Y, data, cmap='viridis', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('ψ (流函数)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # 收敛曲线
    ax = axes[1, 2]
    ax.semilogy(residuals)
    ax.set_xlabel('迭代步', fontsize=12)
    ax.set_ylabel('残差', fontsize=12)
    ax.set_title('收敛曲线', fontsize=13)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/sandbox/workspace/egg_vortex_cfd/output/04_cfd_results.png', dpi=150)
    plt.close()
    print("✅ CFD结果可视化已保存")

    # 保存数值结果
    np.savez('/sandbox/workspace/egg_vortex_cfd/output/cfd_results.npz', **results)
    print("✅ 数值结果已保存为 .npz")


if __name__ == '__main__':
    run_and_visualize()
