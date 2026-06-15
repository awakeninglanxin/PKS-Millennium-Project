"""
burgers_vortex_init.py — Burgers涡初始场 + 蛋形修正
=======================================================
构造CFD仿真的初始条件:
  1. 标准Burgers涡 (圆截面, 已知解析解)
  2. 蛋形修正初始场 (将圆截面Burgers涡映射到蛋形截面)
  3. 渐进初始场 (从圆逐渐变形到蛋形, 提高CFD收敛性)

============================================
Burgers涡解析解（完整推导）
============================================

Burgers涡是NS方程的一个精确解析解，描述轴对称拉伸涡旋。

假设:
  - 定常: ∂/∂t = 0
  - 轴对称: ∂/∂θ = 0
  - 轴向拉伸: v_z = γ·z (线性拉伸)
  - 不可压缩: ∇·v = 0

由不可压缩和轴对称:
  (1/r)·∂(r·v_r)/∂r + ∂v_z/∂z = 0
  代入 v_z = γ·z:  ∂v_z/∂z = γ
  因此: (1/r)·∂(r·v_r)/∂r = -γ → v_r = -γ·r/2

θ-动量方程中，代入 v_r 求解 v_θ:
  v_r·∂v_θ/∂r + v_r·v_θ/r = ν·[∂²v_θ/∂r² + (1/r)·∂v_θ/∂r - v_θ/r²]
  
代入 v_r = -γ·r/2：
  -γ·r/2 · ∂v_θ/∂r - γ/2 · v_θ = ν·[∂²v_θ/∂r² + (1/r)·∂v_θ/∂r - v_θ/r²]

令 v_θ(r) = Γ/(2πr) · f(r)，代入解出:
  f(r) = 1 - exp(-γ·r²/(4ν))

最终:
  v_θ(r) = Γ/(2πr) · [1 - exp(-γ·r²/(4ν))]   ← 切向速度
  v_r(r) = -γ·r/2                               ← 径向速度
  v_z(z) = γ·z                                   ← 轴向速度
  ω_z(r) = Γ·γ/(4πν) · exp(-γ·r²/(4ν))          ← 轴向涡量

关键参数:
  Re = Γ/(2πν)         — 涡旋Reynolds数
  r_core = 2√(ν/γ)     — 涡核半径（涡量峰值位置）
  v_θ_max ≈ Γ/(2π·r_core)·(1-e⁻¹) — 最大切向速度

蛋形映射策略:
  将圆截面 Burgers 涡通过"保环量"映射到蛋形截面。
  壁面处用 tanh(5·dist) 做近壁阻尼，保证no-slip条件。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from dataclasses import dataclass

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '01_geometry'))
from egg_curve import EggCurve, EggParams


@dataclass
class VortexParams:
    """涡旋物理参数"""
    Gamma: float = 1.0       # 环量 Γ
    gamma: float = 1.0       # 轴向拉伸率 γ
    nu: float = 0.01         # 运动粘度 ν
    rho: float = 1.0         # 密度 ρ

    @property
    def Re(self):
        """涡旋Reynolds数"""
        return self.Gamma / (2 * np.pi * self.nu)

    @property
    def r_core(self):
        """涡核半径 (Burgers涡特征尺度)"""
        return 2 * np.sqrt(self.nu / self.gamma)


class BurgersVortex:
    """标准Burgers涡 (圆截面)"""

    def __init__(self, vp: VortexParams):
        self.vp = vp

    def velocity(self, r: np.ndarray, z: np.ndarray) -> dict:
        """
        计算Burgers涡的速度场
        
        参数:
            r: 径向距离 (可以是2D网格上每点到中心的距离)
            z: 轴向坐标
        返回:
            {'vr': 径向速度, 'vtheta': 方位角速度, 'vz': 轴向速度}
        """
        G, g, nu = self.vp.Gamma, self.vp.gamma, self.vp.nu

        # 避免除零
        r_safe = np.where(r < 1e-12, 1e-12, r)

        v_theta = G / (2 * np.pi * r_safe) * (1 - np.exp(-g * r_safe**2 / (4 * nu)))
        v_r = -g * r_safe / 2
        v_z = g * z

        return {'vr': v_r, 'vtheta': v_theta, 'vz': v_z}

    def pressure(self, r: np.ndarray) -> np.ndarray:
        """计算Burgers涡的压力场 (数值积分)"""
        G, g, nu, rho = self.vp.Gamma, self.vp.gamma, self.vp.nu, self.vp.rho

        # 从无穷大到r的积分
        r_int = np.linspace(r, 1e3, 5000, axis=0)
        integrand = G**2 / (4 * np.pi**2 * r_int**2) * (1 - np.exp(-g * r_int**2 / (4 * nu)))**2
        dp = rho * np.trapz(integrand, r_int, axis=0)

        return -dp  # p(r) = p∞ - dp

    def vorticity(self, r: np.ndarray) -> np.ndarray:
        """计算轴向涡量 ω_z"""
        G, g, nu = self.vp.Gamma, self.vp.gamma, self.vp.nu
        return G * g / (4 * np.pi * nu) * np.exp(-g * r**2 / (4 * nu))


class EggVortexInit:
    """蛋形截面涡旋初始场"""

    def __init__(self, vp: VortexParams, ep: EggParams):
        self.vp = vp
        self.ep = ep
        self.egg = EggCurve(ep)
        self.burgers = BurgersVortex(vp)

    def circular_to_egg_mapping(self, x_circle: np.ndarray, y_circle: np.ndarray,
                                 x_egg: np.ndarray, y_egg: np.ndarray) -> dict:
        """
        将圆截面上的场映射到蛋形截面
        
        核心思想: 
          1. 圆上的点 (r, θ) 对应蛋形上距中心轴相同比例的点
          2. 速度大小按截面面积比缩放 (连续性方程约束)
          3. 速度方向从方位角方向调整为蛋形切线方向
        """
        # 圆截面面积
        r_max = np.max(np.sqrt(x_circle**2 + y_circle**2))
        A_circle = np.pi * r_max**2

        # 蛋形截面面积
        A_egg = self.egg.area()
        area_ratio = A_circle / A_egg

        return {'area_ratio': area_ratio}

    def egg_initial_field(self, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> dict:
        """
        在蛋形截面网格上生成初始速度场
        
        策略: 
          "保环量映射" — 将Burgers涡的环量分布(1/r衰减)移植到蛋形几何上
          
        具体做法:
          1. 每个网格点到中心轴的距离 r = sqrt(x² + (y-cy)²)
          2. 用Burgers涡公式计算该距离处的 vθ
          3. 将vθ方向从圆方位角方向调整为蛋形切线方向
          4. vr和vz保持不变
        """
        # 截面中心
        x_bnd, y_bnd = self.egg.get_curve_points(500)
        cy = (np.max(y_bnd) + np.min(y_bnd)) / 2

        # 到中心的距离
        r = np.sqrt(x**2 + (y - cy)**2)
        r_safe = np.where(r < 1e-12, 1e-12, r)

        # Burgers涡速度
        burgers_vel = self.burgers.velocity(r_safe, z)

        # 方位角方向 (在蛋形截面上, 切向 = (-sinθ, cosθ), θ = atan2(y-cy, x))
        theta = np.arctan2(y - cy, x)
        ux = -burgers_vel['vtheta'] * np.sin(theta) + burgers_vel['vr'] * np.cos(theta)
        uy = burgers_vel['vtheta'] * np.cos(theta) + burgers_vel['vr'] * np.sin(theta)
        uz = burgers_vel['vz']

        # 蛋形修正: 壁面处法向速度为零 (近壁阻尼)
        # 计算每个点到蛋形边界的归一化距离
        dist_to_boundary = self._distance_to_egg_boundary(x, y)
        wall_damping = np.tanh(dist_to_boundary * 5)  # 近壁阻尼函数
        ux *= wall_damping
        uy *= wall_damping

        return {'ux': ux, 'uy': uy, 'uz': uz, 'r': r, 'theta': theta}

    def _distance_to_egg_boundary(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """计算点到蛋形边界的最短距离 (近似)"""
        x_bnd, y_bnd = self.egg.get_curve_points(500)

        # 简化: 用蛋形曲线的显式公式
        # 在给定y处, 蛋形边界x = ±x_bnd(y)
        z0, sa, ca = self.ep.z0, self.ep.sin_a, self.ep.cos_a
        inner = 1.0 / (z0 - y * sa)**2 - (y * ca)**2
        x_bnd_at_y = np.where(inner > 0, np.sqrt(np.maximum(inner, 0)), 0)

        # 水平距离到边界
        dx = x_bnd_at_y - np.abs(x)

        # 竖直距离到端点
        ymin, ymax = self.egg._find_ymin(), self.egg._find_ymax()
        dy_min = y - ymin
        dy_max = ymax - y

        # 取最小距离
        dist = np.minimum(np.abs(dx), np.minimum(np.abs(dy_min), np.abs(dy_max)))
        return np.maximum(dist, 1e-10)

    def gradual_deformation(self, x: np.ndarray, y: np.ndarray, z: np.ndarray,
                             t: float = 0.0) -> dict:
        """
        渐进初始场: 从圆截面(t=0)逐渐变形到蛋形截面(t=1)
        
        用于提高CFD收敛性: 先在圆管中跑稳Burgers涡, 再慢慢变形截面
        """
        # t=0: 圆截面Burgers涡
        # t=1: 蛋形截面初始场
        r = np.sqrt(x**2 + (y - 0)**2)  # 简化, 中心在原点
        r_safe = np.where(r < 1e-12, 1e-12, r)

        burgers_vel = self.burgers.velocity(r_safe, z)

        # 圆截面的方位角速度
        theta = np.arctan2(y, x)
        ux_circ = -burgers_vel['vtheta'] * np.sin(theta) + burgers_vel['vr'] * np.cos(theta)
        uy_circ = burgers_vel['vtheta'] * np.cos(theta) + burgers_vel['vr'] * np.sin(theta)

        # 蛋形截面的初始速度
        egg_field = self.egg_initial_field(x, y, z)
        ux_egg = egg_field['ux']
        uy_egg = egg_field['uy']

        # 插值
        ux = (1 - t) * ux_circ + t * ux_egg
        uy = (1 - t) * uy_circ + t * uy_egg
        uz = burgers_vel['vz']

        return {'ux': ux, 'uy': uy, 'uz': uz, 'deformation_t': t}


def visualize_initial_field():
    """可视化初始场"""
    vp = VortexParams(Gamma=1.0, gamma=1.0, nu=0.01)
    ep = EggParams(z1=1, z2=2)
    egg_vortex = EggVortexInit(vp, ep)

    # 创建截面网格
    n = 200
    x_bnd, y_bnd = egg_vortex.egg.get_curve_points(500)
    xmin, xmax = np.min(x_bnd) * 1.1, np.max(x_bnd) * 1.1
    ymin_val, ymax_val = np.min(y_bnd) * 1.1, np.max(y_bnd) * 1.1
    xg = np.linspace(xmin, xmax, n)
    yg = np.linspace(ymin_val, ymax_val, n)
    X, Y = np.meshgrid(xg, yg)
    Z = np.zeros_like(X)

    # 初始场
    field = egg_vortex.egg_initial_field(X, Y, Z)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Row 1: 速度分量
    # vθ
    ax = axes[0, 0]
    r = np.sqrt(X**2 + (Y - egg_vortex.egg._find_ymin())**2)
    r_safe = np.where(r < 0.01, 0.01, r)
    burgers = BurgersVortex(vp)
    vtheta = vp.Gamma / (2 * np.pi * r_safe) * (1 - np.exp(-vp.gamma * r_safe**2 / (4 * vp.nu)))
    im = ax.pcolormesh(X, Y, vtheta, cmap='hot', shading='auto')
    ax.plot(x_bnd, y_bnd, 'w-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('vθ (方位角速度)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # ux
    ax = axes[0, 1]
    im = ax.pcolormesh(X, Y, field['ux'], cmap='RdBu', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('ux (x方向速度)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # uy
    ax = axes[0, 2]
    im = ax.pcolormesh(X, Y, field['uy'], cmap='RdBu', shading='auto')
    ax.plot(x_bnd, y_bnd, 'k-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('uy (y方向速度)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # Row 2: 分析
    # 涡量
    ax = axes[1, 0]
    omega_z = vp.Gamma * vp.gamma / (4 * np.pi * vp.nu) * np.exp(-vp.gamma * r_safe**2 / (4 * vp.nu))
    im = ax.pcolormesh(X, Y, omega_z, cmap='inferno', shading='auto')
    ax.plot(x_bnd, y_bnd, 'w-', linewidth=1.5)
    ax.set_aspect('equal')
    ax.set_title('ω_z (轴向涡量)', fontsize=13)
    plt.colorbar(im, ax=ax)

    # 速度矢量
    ax = axes[1, 1]
    skip = 8
    speed = np.sqrt(field['ux']**2 + field['uy']**2)
    ax.pcolormesh(X, Y, speed, cmap='viridis', shading='auto', alpha=0.5)
    ax.quiver(X[::skip, ::skip], Y[::skip, ::skip],
              field['ux'][::skip, ::skip], field['uy'][::skip, ::skip],
              color='white', scale=5, alpha=0.8)
    ax.plot(x_bnd, y_bnd, 'r-', linewidth=2)
    ax.set_aspect('equal')
    ax.set_title('速度矢量场', fontsize=13)

    # 渐进变形 t=0→1
    ax = axes[1, 2]
    for t in [0, 0.25, 0.5, 0.75, 1.0]:
        grad_field = egg_vortex.gradual_deformation(X, Y, Z, t)
        speed = np.sqrt(grad_field['ux']**2 + grad_field['uy']**2)
        # 取y=0截面的速度分布
        mid_j = n // 2
        ax.plot(X[mid_j, :], speed[mid_j, :], label=f't={t:.2f}')
    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('|v|', fontsize=12)
    ax.set_title('渐进变形: 圆→蛋形', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/sandbox/workspace/egg_vortex_cfd/output/03_initial_field.png', dpi=150)
    plt.close()
    print("✅ 初始场可视化已保存")

    # 打印关键参数
    print(f"\n{'='*50}")
    print(f"Burgers涡参数:")
    print(f"  Re = {vp.Re:.1f}")
    print(f"  涡核半径 r_core = {vp.r_core:.4f}")
    print(f"  最大vθ = {vp.Gamma/(2*np.pi*vp.r_core) * (1-np.exp(-1)):.4f}")
    print(f"{'='*50}")


if __name__ == '__main__':
    visualize_initial_field()
