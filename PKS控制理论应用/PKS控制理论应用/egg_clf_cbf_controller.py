# -*- coding: utf-8 -*-
"""
PKS-CLF-CBF-QP 蛋形控制器 — 完整实现
========================================
基于 PKS (Pythagoras-Kepler-Schule) 蛋形几何的非线性控制器。

核心功能：
  1. 由用户指定蛋形两个顶点 (z1, z2) 自动计算 PKS 参数 (z0, α)
  2. 构造蛋形 CLF (Control Lyapunov Function)
  3. 构造蛋形 CBF (Control Barrier Function)
  4. 每步求解 QP (Quadratic Program) 得到最优控制输入
  5. 支持羚羊角管螺旋扭转模式（极限环控制）
  6. 完整仿真 + 8 子图可视化

理论来源：
  Pythagoras-Kepler-Schule: Walter Schauberger (1962)
  蛋形曲线: xy=1 双曲锥斜切
  CLF-CBF-QP: Ames et al. (2019), "Control Barrier Functions"

作者：WorkBuddy (mylove)
日期：2026-07-01
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 中文字体配置（铁律 24）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 第一部分：PKS 蛋形曲线几何计算
# ============================================================

def compute_egg_parameters(z1, z2):
    """
    由两个主顶点 (z1为尖头, z2为钝头) 计算蛋形参数 (z0, alpha)。

    数学原理：
      蛋形曲线是等边双曲线 xy=1 绕 Y 轴旋转形成的双曲锥，
      被平面 y = z0 * sin(alpha) - x * cos(alpha) * tan(alpha) 斜切的截面。

    Args:
        z1: 尖头顶点（离切割面中心最近的点）
        z2: 钝头顶点（离切割面中心最远的点）

    Returns:
        z0: 切割高度（双曲锥顶点到切割平面的垂直距离）
        alpha: 切割角度（弧度）
    """
    # 由 z1, z2 反推 z0 和 alpha
    # 关系：z1 = z0 * sin(alpha) - 1/z0, z2 = z0 * sin(alpha) + 1/z0
    # → z0 = 2/(z2 - z1)
    # → sin(alpha) = (z1 + z2)/(2*z0)

    z0 = 2.0 / (z2 - z1) if abs(z2 - z1) > 1e-10 else 1.0
    sin_alpha = (z1 + z2) / (2.0 * z0)
    sin_alpha = np.clip(sin_alpha, -1.0, 1.0)
    alpha = np.arcsin(sin_alpha)

    return z0, alpha


def egg_curve_explicit(x_range, z0, alpha):
    """
    蛋形曲线的显式形式。

    y = z0 * sin(alpha) ± sqrt(1/(x^2 + (z0*cos(alpha))^2) - (z0*cos(alpha))^2)

    Args:
        x_range: x 坐标数组
        z0: 切割高度
        alpha: 切割角度（弧度）

    Returns:
        x_valid: 有效的 x 坐标
        y_upper: 上半个蛋形
        y_lower: 下半个蛋形
    """
    cos_a = np.cos(alpha)
    sin_a = np.sin(alpha)
    z0_cos2 = (z0 * cos_a) ** 2

    # 内层必须 >= 0（铁律 29：用 >= 而非 >）
    inner = 1.0 / (x_range**2 + z0_cos2) - z0_cos2
    valid = inner >= 0

    x_valid = x_range[valid]
    inner_valid = inner[valid]
    sqrt_inner = np.sqrt(np.maximum(inner_valid, 0))

    y_upper = z0 * sin_a + sqrt_inner
    y_lower = z0 * sin_a - sqrt_inner

    return x_valid, y_upper, y_lower


def egg_curve_parametric(theta_range, z0, alpha):
    """
    蛋形曲线的参数形式。

    Args:
        theta_range: 角度参数数组 [0, 2π]
        z0: 切割高度
        alpha: 切割角度（弧度）

    Returns:
        x, y: 蛋形曲线上点的坐标
    """
    cos_a = np.cos(alpha)
    sin_a = np.sin(alpha)

    # 参数方程
    r = 1.0 / z0  # 蛋形的特征半径
    x = r * np.cos(theta_range)
    y = z0 * sin_a + r * np.sin(theta_range)

    return x, y


def egg_volume(z0, alpha):
    """计算蛋形的体积（近似）。"""
    cos_a = np.cos(alpha)
    # 近似公式：V ≈ (4/3)π * (1/z0)^3 * (1 + 0.5*sin(alpha))
    r_eff = 1.0 / z0
    return (4.0/3.0) * np.pi * r_eff**3 * (1.0 + 0.5 * np.abs(np.sin(alpha)))


def antelope_horn_3d(t_range, phi_range, z0, alpha, omega=1.0, kappa=0.5, lam=0.1):
    """
    羚羊角管（3D 螺旋扭转蛋形漏斗）的参数方程。

    x(t,φ) = e^{-λt} · r_egg(φ) · cos(ωt + κt + φ)
    y(t,φ) = e^{-λt} · r_egg(φ) · sin(ωt + κt + φ)
    z(t,φ) = t · cos(θ)

    关键物理：
      - κ = 0 → 收敛到中心点（点吸引子，适合火箭着陆）
      - κ > 0 → 绕中心形成极限环（周期吸引子，适合卫星编队）

    Args:
        t_range: 沿轴参数 [t_min, t_max]
        phi_range: 截面角度 [0, 2π]
        z0, alpha: 蛋形参数
        omega: 螺距（周向旋转速度）
        kappa: 扭转率（极限环强度，>0 = 轨道保持，=0 = 点收敛）
        lam: 径向衰减率

    Returns:
        X, Y, Z: 3D 网格坐标
    """
    # 蛋形截面半径函数
    T, Phi = np.meshgrid(t_range, phi_range)
    cos_a = np.cos(alpha)
    sin_a = np.sin(alpha)

    # 蛋形半径（角向变化）
    r_egg = (1.0 / z0) * (1.0 + 0.3 * np.cos(Phi))

    # 衰减因子
    decay = np.exp(-lam * T)

    X = decay * r_egg * np.cos(omega * T + kappa * T + Phi)
    Y = decay * r_egg * np.sin(omega * T + kappa * T + Phi)
    Z = T * cos_a

    return X, Y, Z


# ============================================================
# 第二部分：蛋形 CLF（Control Lyapunov Function）
# ============================================================

def egg_clf(x, z0, alpha):
    """
    蛋形 Control Lyapunov Function。

    V(x) = 1/(z0 - x2*sin(α))^2 + (x2*cos(α))^2 + x1^2

    性质：
      - 等值面是蛋形曲线
      - 在原点正定 (V(0) > 0 当 x ≠ 0, V(0) = 0)
      - 尖头方向梯度大（控制量大），钝头方向梯度小

    Args:
        x: 状态向量 [x1, x2]
        z0: 切割高度
        alpha: 切割角度

    Returns:
        V: Lyapunov 函数值
    """
    x1, x2 = x[0], x[1]
    sin_a = np.sin(alpha)
    cos_a = np.cos(alpha)

    # 防止分母为零
    denom = z0 - x2 * sin_a
    if abs(denom) < 1e-8:
        denom = 1e-8 * np.sign(denom) if denom != 0 else 1e-8

    V = 1.0 / denom**2 + (x2 * cos_a)**2 + x1**2
    return V


def egg_clf_gradient(x, z0, alpha):
    """蛋形 CLF 的梯度 ∇V(x)。"""
    x1, x2 = x[0], x[1]
    sin_a = np.sin(alpha)
    cos_a = np.cos(alpha)

    denom = z0 - x2 * sin_a
    if abs(denom) < 1e-8:
        denom = 1e-8

    dV_dx1 = 2.0 * x1
    dV_dx2 = 2.0 * sin_a / denom**3 + 2.0 * x2 * cos_a**2

    return np.array([dV_dx1, dV_dx2])


# ============================================================
# 第三部分：蛋形 CBF（Control Barrier Function）
# ============================================================

def egg_cbf(x, z0, alpha):
    """
    蛋形 Control Barrier Function。

    h(x) = 1/(z0 - x2*sin(α))^2 - x1^2 - (x2*cos(α))^2

    安全条件：h(x) >= 0 表示系统在蛋形安全走廊内部。

    Args:
        x: 状态向量 [x1, x2]
        z0, alpha: 蛋形参数

    Returns:
        h: Barrier 函数值 (>= 0 为安全)
    """
    x1, x2 = x[0], x[1]
    sin_a = np.sin(alpha)
    cos_a = np.cos(alpha)

    denom = z0 - x2 * sin_a
    if abs(denom) < 1e-8:
        denom = 1e-8

    h = 1.0 / denom**2 - x1**2 - (x2 * cos_a)**2
    return h


def egg_cbf_gradient(x, z0, alpha):
    """蛋形 CBF 的梯度 ∇h(x)。"""
    x1, x2 = x[0], x[1]
    sin_a = np.sin(alpha)
    cos_a = np.cos(alpha)

    denom = z0 - x2 * sin_a
    if abs(denom) < 1e-8:
        denom = 1e-8

    dh_dx1 = -2.0 * x1
    dh_dx2 = 2.0 * sin_a / denom**3 - 2.0 * x2 * cos_a**2

    return np.array([dh_dx1, dh_dx2])


# ============================================================
# 第四部分：CLF-CBF-QP 控制器
# ============================================================

def clf_cbf_qp_controller(x, z0, alpha, gamma=1.0, eta=1.0, u_max=10.0):
    """
    PKS-CLF-CBF-QP 控制器。

    每步求解：
      min_u  0.5 * u^2
      s.t.   Ḣ(x) + γ·V(x) ≤ 0      (CLF 约束：保证收敛)
             ḣ(x) + η·h(x) ≥ 0      (CBF 约束：保证安全)
             |u| ≤ u_max             (控制饱和)

    Args:
        x: 当前状态 [x1, x2]
        z0, alpha: 蛋形参数
        gamma: CLF 收敛速率（越大越快）
        eta: CBF 安全裕度（越大越安全）
        u_max: 控制量上限

    Returns:
        u_opt: 最优控制输入
        success: QP 是否求解成功
    """
    grad_V = egg_clf_gradient(x, z0, alpha)
    V_val = egg_clf(x, z0, alpha)
    grad_h = egg_cbf_gradient(x, z0, alpha)
    h_val = egg_cbf(x, z0, alpha)

    # 系统模型：双积分器 ẍ = u
    # 状态：x1 = 位置, x2 = 速度
    # ẋ1 = x2, ẋ2 = u
    f = np.array([x[1], 0.0])   # f(x): 无控动力学
    g = np.array([0.0, 1.0])    # g(x): 控制输入矩阵

    # Lie 导数
    Lf_V = np.dot(grad_V, f)
    Lg_V = np.dot(grad_V, g)
    Lf_h = np.dot(grad_h, f)
    Lg_h = np.dot(grad_h, g)

    # CLF 约束：Lf_V + Lg_V*u + gamma*V <= 0 → Lg_V*u <= -Lf_V - gamma*V
    clf_rhs = -Lf_V - gamma * V_val

    # CBF 约束：Lf_h + Lg_h*u + eta*h >= 0 → Lg_h*u >= -Lf_h - eta*h
    cbf_rhs = -Lf_h - eta * h_val

    # 求解约束优化：min 0.5*u^2 s.t. 线性不等式
    def objective(u):
        return 0.5 * u**2

    constraints = []

    # CLF 约束（如果有效）
    if abs(Lg_V) > 1e-8:
        if Lg_V > 0:
            constraints.append({'type': 'ineq', 'fun': lambda u, r=clf_rhs, gv=Lg_V: -u * gv - r})
        else:
            constraints.append({'type': 'ineq', 'fun': lambda u, r=clf_rhs, gv=Lg_V: u * gv + r})

    # CBF 约束（如果有效）
    if abs(Lg_h) > 1e-8:
        if Lg_h > 0:
            constraints.append({'type': 'ineq', 'fun': lambda u, r=cbf_rhs, gh=Lg_h: u * gh + r})
        else:
            constraints.append({'type': 'ineq', 'fun': lambda u, r=cbf_rhs, gh=Lg_h: -u * gh - r})

    bounds = [(-u_max, u_max)]

    # 初始猜测
    u0 = 0.0

    try:
        result = minimize(objective, u0, method='SLSQP',
                         bounds=bounds, constraints=constraints,
                         options={'maxiter': 100, 'ftol': 1e-8})
        return result.x[0], result.success
    except Exception:
        # 回退：若 QP 无解，用最保守控制
        u_fallback = -np.sign(x[1]) * min(abs(x[1]), u_max)
        return u_fallback, False


# ============================================================
# 第五部分：完整仿真
# ============================================================

def simulate_pks_controller(z1, z2, x0_list, T=10.0, dt=0.01,
                             gamma=1.0, eta=1.0, u_max=5.0):
    """
    完整仿真：从多个初始状态出发，验证 PKS-CLF-CBF-QP 控制器。

    Args:
        z1, z2: 蛋形顶点参数
        x0_list: 初始状态列表（每个元素为 [x1_0, x2_0]）
        T: 仿真时长
        dt: 时间步长
        gamma: CLF 收敛速率
        eta: CBF 安全裕度
        u_max: 控制量上限

    Returns:
        results: 字典，包含轨迹、V、h、u 的历史
    """
    z0, alpha = compute_egg_parameters(z1, z2)

    n_steps = int(T / dt)
    n_traj = len(x0_list)

    # 存储所有轨迹
    traj_x1 = np.zeros((n_traj, n_steps))
    traj_x2 = np.zeros((n_traj, n_steps))
    traj_V = np.zeros((n_traj, n_steps))
    traj_h = np.zeros((n_traj, n_steps))
    traj_u = np.zeros((n_traj, n_steps))

    for i, x0 in enumerate(x0_list):
        x = np.array(x0, dtype=float)

        for k in range(n_steps):
            # 记录当前状态
            traj_x1[i, k] = x[0]
            traj_x2[i, k] = x[1]
            traj_V[i, k] = egg_clf(x, z0, alpha)
            traj_h[i, k] = egg_cbf(x, z0, alpha)

            # 求解控制输入
            u, _ = clf_cbf_qp_controller(x, z0, alpha, gamma, eta, u_max)
            traj_u[i, k] = u

            # 欧拉积分
            x[0] += x[1] * dt
            x[1] += u * dt

    return {
        'z0': z0,
        'alpha': alpha,
        'traj_x1': traj_x1,
        'traj_x2': traj_x2,
        'traj_V': traj_V,
        'traj_h': traj_h,
        'traj_u': traj_u,
        'dt': dt,
        'n_steps': n_steps,
    }


# ============================================================
# 第六部分：8 子图可视化
# ============================================================

def plot_full_results(results, z1, z2, save_path=None):
    """
    生成完整的 8 子图仿真报告。

    子图布局：
      1. 蛋形曲线（参数方程）
      2. 蛋形曲线（显式方程）
      3. CLF 等值线（势场）
      4. 状态轨迹图（相平面 x1-x2）
      5. V(t) — Lyapunov 函数随时间变化
      6. h(t) — Barrier 函数随时间变化（验证安全性）
      7. u(t) — 控制输入随时间变化
      8. 状态收敛图 x1(t)

    Args:
        results: simulate_pks_controller() 的返回值
        z1, z2: 蛋形顶点
        save_path: 保存路径（可选）
    """
    z0 = results['z0']
    alpha = results['alpha']
    dt = results['dt']
    n_steps = results['n_steps']
    t = np.arange(n_steps) * dt
    n_traj = results['traj_x1'].shape[0]

    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    colors = plt.cm.viridis(np.linspace(0, 1, n_traj))

    # ---- 子图 1：蛋形曲线（参数方程） ----
    ax = axes[0, 0]
    theta = np.linspace(0, 2*np.pi, 500)
    xp, yp = egg_curve_parametric(theta, z0, alpha)
    ax.plot(xp, yp, 'b-', linewidth=2)
    ax.fill(xp, yp, alpha=0.15, color='blue')
    ax.scatter([0], [0], c='red', s=50, zorder=5, label='原点(目标)')
    ax.set_xlabel('x (铁律 24B: ASCII only)')
    ax.set_ylabel('y')
    ax.set_title(f'蛋形曲线(参数) z1={z1:.2f} z2={z2:.2f}')
    ax.axis('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # ---- 子图 2：蛋形曲线（显式方程） ----
    ax = axes[0, 1]
    # 确定合理的 x 范围
    x_extent = 3.0 / z0
    x_vals = np.linspace(-x_extent, x_extent, 1000)
    x_valid, y_upper, y_lower = egg_curve_explicit(x_vals, z0, alpha)
    ax.plot(x_valid, y_upper, 'g-', linewidth=2, label='上半')
    ax.plot(x_valid, y_lower, 'g-', linewidth=2, label='下半')
    ax.fill_between(x_valid, y_lower, y_upper, alpha=0.15, color='green')
    ax.scatter([0], [z0*np.sin(alpha)], c='red', s=50, zorder=5, label='中心')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('蛋形曲线(显式)')
    ax.axis('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # ---- 子图 3：CLF 等值线 ----
    ax = axes[0, 2]
    x1_grid = np.linspace(-x_extent, x_extent, 100)
    x2_grid = np.linspace(-x_extent, x_extent, 100)
    X1, X2 = np.meshgrid(x1_grid, x2_grid)
    V_grid = np.zeros_like(X1)
    for i in range(len(x1_grid)):
        for j in range(len(x2_grid)):
            V_grid[j, i] = egg_clf([X1[j, i], X2[j, i]], z0, alpha)

    # 限制 V 的范围避免爆炸
    V_max = np.percentile(V_grid[~np.isnan(V_grid)], 95)
    V_grid = np.clip(V_grid, 0, V_max)

    contour = ax.contourf(X1, X2, V_grid, levels=20, cmap='YlOrRd')
    ax.scatter([0], [0], c='blue', s=80, marker='*', zorder=5, label='原点')
    plt.colorbar(contour, ax=ax, label='V(x)')
    ax.set_xlabel('x1 (位置)')
    ax.set_ylabel('x2 (速度)')
    ax.set_title('蛋形 CLF 势场 V(x)')
    ax.legend()

    # ---- 子图 4：状态轨迹（相平面） ----
    ax = axes[0, 3]
    for i in range(n_traj):
        ax.plot(results['traj_x1'][i, :], results['traj_x2'][i, :],
                color=colors[i], linewidth=1.0, alpha=0.8)
        ax.scatter(results['traj_x1'][i, 0], results['traj_x2'][i, 0],
                  color=colors[i], s=30, marker='o', zorder=5)
    ax.scatter([0], [0], c='red', s=80, marker='*', zorder=10, label='目标')
    ax.set_xlabel('x1 (位置)')
    ax.set_ylabel('x2 (速度)')
    ax.set_title(f'相平面轨迹 ({n_traj}条)')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # ---- 子图 5：V(t) — Lyapunov 函数 ----
    ax = axes[1, 0]
    for i in range(n_traj):
        ax.plot(t, results['traj_V'][i, :], color=colors[i], linewidth=1.0)
    ax.set_xlabel('时间 t (s)')
    ax.set_ylabel('V(x)')
    ax.set_title('Lyapunov 函数 V(t) → 0 (验证收敛)')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    # ---- 子图 6：h(t) — Barrier 函数 ----
    ax = axes[1, 1]
    for i in range(n_traj):
        ax.plot(t, results['traj_h'][i, :], color=colors[i], linewidth=1.0)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5, label='安全边界 h=0')
    ax.set_xlabel('时间 t (s)')
    ax.set_ylabel('h(x)')
    ax.set_title('Barrier 函数 h(t) >= 0 (验证安全)')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # ---- 子图 7：u(t) — 控制输入 ----
    ax = axes[1, 2]
    for i in range(n_traj):
        ax.plot(t, results['traj_u'][i, :], color=colors[i], linewidth=1.0)
    ax.set_xlabel('时间 t (s)')
    ax.set_ylabel('u (控制力)')
    ax.set_title('控制输入 u(t)')
    ax.grid(True, alpha=0.3)

    # ---- 子图 8：x1(t) — 位置收敛 ----
    ax = axes[1, 3]
    for i in range(n_traj):
        ax.plot(t, results['traj_x1'][i, :], color=colors[i], linewidth=1.0)
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.0)
    ax.set_xlabel('时间 t (s)')
    ax.set_ylabel('x1 (位置)')
    ax.set_title('状态收敛 x1(t) → 0')
    ax.grid(True, alpha=0.3)

    plt.suptitle(f'PKS-CLF-CBF-QP 蛋形控制器仿真\n'
                 f'蛋形参数: z1={z1:.2f}, z2={z2:.2f}, '
                 f'z0={z0:.3f}, alpha={np.degrees(alpha):.1f}°',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ 8子图已保存: {save_path}")

    plt.close()
    return fig


# ============================================================
# 第七部分：主入口 — 演示多种蛋形配置
# ============================================================

def main():
    """演示不同谐波比例对应的蛋形控制器性能。"""

    # 测试配置（不同音程比例 -> 不同蛋形形状）
    configs = [
        {'name': '八度 1:2 (对称蛋形)', 'z1': 1.0, 'z2': 2.0,
         'desc': '对称性最强，适合通用安全走廊'},
        {'name': '五度 2:3 (中等不对称)', 'z1': 2.0, 'z2': 3.0,
         'desc': '中等不对称，适合机械臂精细操作'},
        {'name': '四度 3:4 (较强不对称)', 'z1': 3.0, 'z2': 4.0,
         'desc': '较强不对称，适合火箭着陆偏航约束'},
    ]

    for cfg in configs:
        print(f"\n{'='*50}")
        print(f"配置: {cfg['name']}")
        print(f"用途: {cfg['desc']}")

        z1, z2 = cfg['z1'], cfg['z2']

        # 生成 5 条不同初始状态的轨迹
        np.random.seed(42)
        x0_list = []
        for _ in range(5):
            angle = np.random.uniform(0, 2*np.pi)
            dist = np.random.uniform(0.5, 2.0)
            x0_list.append([dist*np.cos(angle), np.random.uniform(-1, 1)])

        # 仿真
        results = simulate_pks_controller(
            z1, z2, x0_list, T=8.0, dt=0.01,
            gamma=1.5, eta=2.0, u_max=5.0
        )

        # 验证
        final_V = results['traj_V'][:, -1]
        min_h = np.min(results['traj_h'], axis=1)
        print(f"  最终 V: {np.mean(final_V):.6f} (目标: →0)")
        print(f"  最小 h: {np.min(min_h):.4f} (要求: >=0)")

        # 保存图片
        safe_name = cfg['name'].replace(' ', '_').replace(':', '-')
        plot_full_results(results, z1, z2,
                         save_path=f'PKS_egg_controller_{safe_name}.png')

    print(f"\n{'='*50}")
    print("全部测试完成。")


if __name__ == '__main__':
    main()
