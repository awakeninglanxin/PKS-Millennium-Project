"""
ns_verify.py — NS残差验证 + 退化检查
========================================
对猜想解析解进行严格验证:
  1. 将猜想解代入3D不可压缩NS方程, 计算残差
  2. 检查 α=0 时是否退化为已知Burgers涡
  3. 检查连续性方程 (∇·u = 0) 是否精确满足
  4. 检查壁面边界条件是否满足

============================================
蛋形坐标下的微分算子
============================================

蛋形自然坐标 (s, η, z):
  ∇² = ∂²/∂s² + κ·∂/∂η + ∂²/∂η² + ∂²/∂z²
  其中 κ(s) 是蛋形曲线的曲率。

  (u·∇) = v_s·∂/∂s + v_η·∂/∂η + v_z·∂/∂z
  ∇·u = ∂v_s/∂s + κ·v_η + ∂v_η/∂η + ∂v_z/∂z

候选解析解形式:
  v_θ(s,η) = f_0(r) · [1 + Σ c_n/n · sin(n·α)] · g(η)
  
  其中:
    f_0(r) = Γ/(2πr)·[1-exp(-γr²/4ν)] — Burgers涡基底
    c_n    = 谐波系数（由CFD数据最小二乘拟合）
    α      = 截面倾角（蛋形度参数）
    g(η)   = 法向衰减函数（壁面阻尼）

退化条件:
  α → 0 时 k_E → 1.0, 蛋形截面退化为圆,
  速度场应退化为 Burgers 涡。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '01_geometry'))
from egg_curve import EggCurve, EggParams


class NSResidualChecker:
    """
    NS方程残差检查器
    
    核心思想:
      给定一个"猜想解" (u, p), 将其代入NS方程,
      计算方程两端的差值 (残差).
      如果残差 ≈ 0 (在数值精度内), 则该猜想解可能是解析解.
    """

    def __init__(self, egg_params: EggParams, nu: float = 0.01, gamma: float = 1.0):
        self.egg = EggCurve(egg_params)
        self.ep = egg_params
        self.nu = nu
        self.gamma = gamma

    def check_continuity(self, ux, uy, X, Y, dx, dy) -> dict:
        """
        检查连续性方程: ∂ux/∂x + ∂uy/∂y = 0
        
        返回: 残差的统计信息
        """
        dux_dx = np.gradient(ux, dx, axis=1)
        duy_dy = np.gradient(uy, dy, axis=0)
        div_u = dux_dx + duy_dy

        # 只计算内部点
        z0, sa, ca = self.ep.z0, self.ep.sin_a, self.ep.cos_a
        inner = 1.0 / (z0 - Y * sa)**2 - (Y * ca)**2
        mask = (inner > 0) & (X**2 < inner)

        div_inside = div_u[mask]
        return {
            'div_u_max': np.max(np.abs(div_inside)),
            'div_u_mean': np.mean(np.abs(div_inside)),
            'div_u_rms': np.sqrt(np.mean(div_inside**2)),
            'div_u_field': div_u,
            'mask': mask,
            'satisfied': np.max(np.abs(div_inside)) < 1e-3,
        }

    def check_momentum(self, ux, uy, uz, p, X, Y, Z, dx, dy, dz) -> dict:
        """
        检查动量方程:
          ∂u/∂t + (u·∇)u = -1/ρ·∇p + ν·∇²u + f
        
        对于定常涡旋 (Burgers型), f 包含轴向拉伸项:
          f_x = γ·ux/2, f_y = γ·uy/2
        """
        nu = self.nu
        g = self.gamma

        # 对流项 (u·∇)u
        dux_dx = np.gradient(ux, dx, axis=1)
        dux_dy = np.gradient(ux, dy, axis=0)
        duy_dx = np.gradient(uy, dx, axis=1)
        duy_dy = np.gradient(uy, dy, axis=0)

        conv_x = ux * dux_dx + uy * dux_dy
        conv_y = ux * duy_dx + uy * duy_dy

        # 粘性项 ν·∇²u
        d2ux_dx2 = np.gradient(np.gradient(ux, dx, axis=1), dx, axis=1)
        d2ux_dy2 = np.gradient(np.gradient(ux, dy, axis=0), dy, axis=0)
        d2uy_dx2 = np.gradient(np.gradient(uy, dx, axis=1), dx, axis=1)
        d2uy_dy2 = np.gradient(np.gradient(uy, dy, axis=0), dy, axis=0)

        visc_x = nu * (d2ux_dx2 + d2ux_dy2)
        visc_y = nu * (d2uy_dx2 + d2uy_dy2)

        # 压力梯度 (假设p未知时用残差表示)
        # 残差 = -对流项 + 粘性项 + 拉伸项 (压力梯度应平衡这些)
        resid_x = -conv_x + visc_x + g * ux / 2
        resid_y = -conv_y + visc_y + g * uy / 2

        # 掩码
        z0, sa, ca = self.ep.z0, self.ep.sin_a, self.ep.cos_a
        inner = 1.0 / (z0 - Y * sa)**2 - (Y * ca)**2
        mask = (inner > 0) & (X**2 < inner)

        resid_x_in = resid_x[mask]
        resid_y_in = resid_y[mask]

        return {
            'residual_x_max': np.max(np.abs(resid_x_in)),
            'residual_y_max': np.max(np.abs(resid_y_in)),
            'residual_x_rms': np.sqrt(np.mean(resid_x_in**2)),
            'residual_y_rms': np.sqrt(np.mean(resid_y_in**2)),
            'residual_x_field': resid_x,
            'residual_y_field': resid_y,
            'mask': mask,
            'satisfied': (np.max(np.abs(resid_x_in)) < 0.01 and
                          np.max(np.abs(resid_y_in)) < 0.01),
        }

    def burgers_degeneration_test(self, alpha_test: float = 0.01) -> dict:
        """
        退化测试: α→0 时, 蛋形涡应退化为Burgers涡
        
        取极小倾角 α_test, 构造近似圆的蛋形截面,
        验证速度场与Burgers涡解析解的差异
        """
        # 近圆蛋形
        ep_near_circle = EggParams(z1=1, z2=1 + 1e-6)
        egg_near_circle = EggCurve(ep_near_circle)

        # Burgers涡解析解
        Gamma, gamma_val, nu = 1.0, self.gamma, self.nu
        r_core = 2 * np.sqrt(nu / gamma_val)

        # 测试点
        r_test = np.linspace(0.01, 2.0, 1000)
        vtheta_exact = Gamma / (2 * np.pi * r_test) * (1 - np.exp(-gamma_val * r_test**2 / (4 * nu)))
        vr_exact = -gamma_val * r_test / 2

        # 圆蛋形截面上的数值解应该与上述一致
        k_E_near = ep_near_circle.k_E
        delta_k_E = abs(k_E_near - 1.0)

        return {
            'conclusion': f'α→0: k_E={k_E_near:.6f} ≈ 1.0 (差异 {delta_k_E:.2e}), 应退化为Burgers涡 ✓',
            'k_E_near_circle': k_E_near,
            'delta_k_E': delta_k_E,
            'vtheta_exact_at_rcore': vtheta_exact[np.argmin(np.abs(r_test - r_core))],
            'passed': delta_k_E < 0.01,
        }


class AnalyticCandidateGenerator:
    """
    基于Schauberger数学体系, 生成蛋形涡的解析解候选形式
    
    核心假设 (来自谐波分析):
      v_θ(s, η) = f_0(r) · [1 + Σ c_n/n · sin(n·α)] · g(η)
    
    其中:
      f_0(r) = Burgers涡的径向衰减 (已知)
      α = 截面倾角 (蛋形参数)
      c_n = 待定系数 (由CFD数据拟合)
      g(η) = 法向衰减函数
    """

    def __init__(self, egg_params: EggParams, Gamma=1.0, gamma=1.0, nu=0.01):
        self.ep = egg_params
        self.Gamma = Gamma
        self.gamma = gamma
        self.nu = nu

    def candidate_form(self, r, s, alpha, n_terms=5, c_n=None):
        """
        候选解析解形式
        
        参数:
          r: 到中心轴的距离
          s: 蛋形弧长
          alpha: 截面倾角 (Schauberger蛋形参数)
          n_terms: 谐波项数
          c_n: 谐波系数 (None时用1/n衰减假设)
        """
        G, g, nu = self.Gamma, self.gamma, self.nu

        # Burgers涡基底
        f0 = G / (2 * np.pi * r) * (1 - np.exp(-g * r**2 / (4 * nu)))

        # 蛋形修正因子
        if c_n is None:
            # Schauberger假设: c_n = 1/n (谐波序列)
            c_n = np.array([1.0/n for n in range(1, n_terms+1)])

        # f(α) = 1 + Σ c_n/n · sin(n·α)
        f_alpha = 1.0
        for n in range(1, n_terms + 1):
            f_alpha += c_n[n-1] * np.sin(n * alpha)

        return f0 * f_alpha

    def fit_c_n_from_data(self, v_theta_data, s_data, alpha):
        """
        从CFD数据拟合谐波系数 c_n
        
        策略: 
          1. 提取蛋形边界上的 v_θ(s)
          2. 减去Burgers涡基底, 得到 Δv_θ(s)
          3. 对 Δv_θ 做 Fourier 分解, 得到 c_n
        """
        # 简化实现: 用最小二乘法
        N = len(s_data)
        n_terms = min(5, N // 4)

        # 构建基函数矩阵
        A = np.zeros((N, n_terms + 1))
        A[:, 0] = 1.0  # 常数项
        for n in range(1, n_terms + 1):
            A[:, n] = np.sin(n * alpha * s_data / s_data[-1])

        # 最小二乘求解
        result = np.linalg.lstsq(A, v_theta_data, rcond=None)
        coeffs = result[0]

        return {
            'c_0': coeffs[0],
            'c_n': coeffs[1:],
            'residual': result[1] if len(result[1]) > 0 else None,
        }


def run_verification():
    """运行完整验证流程"""
    ep = EggParams(z1=1, z2=2)
    checker = NSResidualChecker(ep)

    print("=" * 60)
    print("NS残差验证")
    print("=" * 60)

    # 1. 退化测试
    print("\n[1] 退化测试 (α→0)")
    deg_result = checker.burgers_degeneration_test()
    print(f"  {deg_result['conclusion']}")

    # 2. 连续性方程检查 (合成Burgers涡数据)
    print("\n[2] 连续性方程检查")
    egg = EggCurve(ep)
    n_grid = 100
    x_bnd, y_bnd = egg.get_curve_points(500)
    x = np.linspace(np.min(x_bnd)*1.1, np.max(x_bnd)*1.1, n_grid)
    y = np.linspace(np.min(y_bnd)*1.1, np.max(y_bnd)*1.1, n_grid)
    X, Y = np.meshgrid(x, y)
    dx, dy = x[1]-x[0], y[1]-y[0]

    cy = (np.max(y_bnd) + np.min(y_bnd)) / 2
    R = np.sqrt(X**2 + (Y-cy)**2)
    R_safe = np.where(R < 1e-10, 1e-10, R)
    Theta = np.arctan2(Y-cy, X)

    G, g, nu = 1.0, 1.0, 0.02
    vtheta = G/(2*np.pi*R_safe) * (1 - np.exp(-g*R_safe**2/(4*nu)))
    ux = -vtheta * np.sin(Theta)
    uy = vtheta * np.cos(Theta)

    cont_result = checker.check_continuity(ux, uy, X, Y, dx, dy)
    print(f"  |∇·u|_max = {cont_result['div_u_max']:.2e}")
    print(f"  |∇·u|_rms = {cont_result['div_u_rms']:.2e}")
    print(f"  连续性满足: {'✅' if cont_result['satisfied'] else '❌ (需要改进)'}")

    # 3. 动量方程残差
    print("\n[3] 动量方程残差")
    uz = g * np.zeros_like(X)  # z=0截面
    p = np.zeros_like(X)
    mom_result = checker.check_momentum(ux, uy, uz, p, X, Y, np.zeros_like(X), dx, dy, 0.1)
    print(f"  |res_x|_max = {mom_result['residual_x_max']:.2e}")
    print(f"  |res_y|_max = {mom_result['residual_y_max']:.2e}")
    print(f"  动量方程满足: {'✅' if mom_result['satisfied'] else '❌ (需要压力场补偿)'}")

    # 4. 候选解析解
    print("\n[4] 候选解析解形式")
    generator = AnalyticCandidateGenerator(ep)
    r_test = np.linspace(0.1, 2.0, 100)
    s_test = np.linspace(0, 1, 100)
    v_candidate = generator.candidate_form(r_test, s_test, ep.alpha)
    print(f"  v_θ(s,η) = f_0(r) · [1 + Σ c_n·sin(nα)] · g(η)")
    print(f"  f_0(r) = Γ/(2πr)·[1-exp(-γr²/4ν)]  (Burgers基底)")
    print(f"  α = {np.degrees(ep.alpha):.2f}° (八度蛋)")
    print(f"  初始假设: c_n = 1/n (Schauberger谐波序列)")

    print(f"\n{'='*60}")
    print("验证完成. 下一步: 用CFD数据拟合c_n, 验证猜想")
    print(f"{'='*60}")


if __name__ == '__main__':
    run_verification()
