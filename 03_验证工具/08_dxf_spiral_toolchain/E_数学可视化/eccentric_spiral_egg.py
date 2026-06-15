# -*- coding: utf-8 -*-
"""
Schauberger 偏心螺旋蛋实现
解决 P027 遗留问题：现有代码生成的是同心蛋形（对称），
而 Schauberger 手绘(image11)是偏心的——焦点不在几何中心。

核心创新：引入"中心漂移项"(center_drift)，使每圈蛋形的中心
沿指定方向逐步移动，同时缩放衰减，最终收敛到偏心焦点。

输出：
  1. 同心 vs 偏心 并排对比图
  2. 偏心参数扫描（不同漂移策略的效果）
  3. 与 image11 手绘参考图的视觉匹配度评估
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import FancyArrowPatch
import math
import os

# === 铁律57：matplotlib 中文渲染三步初始化 ===
matplotlib.use("Agg")
import matplotlib.font_manager as fm

cache_dir = matplotlib.get_cachedir()
for f in os.listdir(cache_dir):
    if f.endswith('.json'):
        try:
            os.remove(os.path.join(cache_dir, f))
        except:
            pass

fm._load_fontmanager(try_read_cache=False)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 蛋形曲线生成器（复用 Die Ei-Kurve.py 核心算法）
# ============================================================
def generate_egg_curve(z0, tan_alpha, amp=1.0, num_points=1000,
                       center_x=0.0, center_y=0.0):
    """
    生成单条蛋形曲线，支持中心偏移。

    参数：
    ------
    z0 : float — 截距参数（来自斜切平面 z=kx+b 的 b）
    tan_alpha : float — 斜率参数（来自 k）
    amp : float — 整体缩放因子
    num_points : int — 采样点数
    center_x, center_y : float — 中心偏移量（偏心关键！）

    返回：(x_array, y_array)
    """
    phi_values = np.linspace(0, 2 * np.pi, num_points)

    alpha = math.atan(tan_alpha)
    sin_alpha = math.sin(alpha)
    cos_alpha = math.cos(alpha)

    sin_phi = np.sin(phi_values)
    cos_phi = np.cos(phi_values)

    denominator_inside = np.sqrt(sin_phi**2 + cos_phi**2 * cos_alpha**2)
    inside_sqrt = z0**2 - (4 * cos_phi * sin_alpha) / denominator_inside

    valid_mask = inside_sqrt >= 0
    phi_valid = phi_values[valid_mask]
    sin_phi_v = sin_phi[valid_mask]
    cos_phi_v = cos_phi[valid_mask]
    inside_sqrt_v = inside_sqrt[valid_mask]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    denominator = 2 * cos_phi_v * sin_alpha
    valid_denom = np.abs(denominator) > 1e-10
    phi_valid = phi_valid[valid_denom]
    sin_phi_v = sin_phi_v[valid_denom]
    cos_phi_v = cos_phi_v[valid_denom]
    inside_sqrt_v = inside_sqrt_v[valid_denom]
    denominator = denominator[valid_denom]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    sqrt_val = np.sqrt(inside_sqrt_v)
    r = amp * (z0 - sqrt_val) / denominator  # 负号分支 = 蛋形内部

    x = r * sin_phi_v + center_x
    y = r * cos_phi_v + center_y

    return x, y


def rotate_points(x, y, theta_rad):
    """绕原点旋转点集"""
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return x * c - y * s, x * s + y * c


# ============================================================
# 三种偏心策略
# ============================================================

def drift_linear(n, n_max, drift_amplitude, direction_deg=150):
    """
    策略A: 线性漂移
    每圈的中心沿 direction_deg 方向线性移动。
    漂移量 ∝ n/n_max（越外圈偏移越大）
    """
    progress = n / max(n_max, 1)
    dx = drift_amplitude * progress * math.cos(math.radians(direction_deg))
    dy = drift_amplitude * progress * math.sin(math.radians(direction_deg))
    return dx, dy


def drift_sqrt(n, n_max, drift_amplitude, direction_deg=150):
    """
    策略B: 平方根漂移（推荐）
    漂移量 ∝ sqrt(n/n_max)
    外圈快速偏移，内圈缓慢收敛——更接近 image11 的视觉效果
    """
    progress = math.sqrt(n / max(n_max, 1))
    dx = drift_amplitude * progress * math.cos(math.radians(direction_deg))
    dy = drift_amplitude * progress * math.sin(math.radians(direction_deg))
    return dx, dy


def drift_hyperbolic(n, n_max, drift_amplitude, direction_deg=150):
    """
    策略C: 双曲漂移（与 xy=1 宇宙原理对齐）
    漂移量 ∝ 1/(1 + n/n_scale)
    外圈大偏移，快速收敛到极限位置
    """
    scale = 5.0  # 收敛速度参数
    progress = 1.0 / (1.0 + n / scale)
    dx = drift_amplitude * progress * math.cos(math.radians(direction_deg))
    dy = drift_amplitude * progress * math.sin(math.radians(direction_deg))
    return dx, dy


def drift_spiral(n, n_max, drift_amplitude, direction_deg=150):
    """
    策略D: 螺旋式漂移（最复杂但最灵活）
    方向本身也随 n 变化，产生真正的螺旋轨迹。
    模拟 Schauberger 蛋形管的水流路径。
    """
    # 方向随 n 旋转（模拟水流旋转）
    direction = direction_deg + n * 8  # 每圈额外转 8°
    progress = math.sqrt(n / max(n_max, 1)) * 0.7 + 0.3 * (n / max(n_max, 1))
    dx = drift_amplitude * progress * math.cos(math.radians(direction))
    dy = drift_amplitude * progress * math.sin(math.radians(direction))
    return dx, dy


# ============================================================
# 图1：同心 vs 偏心 对比（主图）
# ============================================================
def plot_concentric_vs_eccentric():
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))

    # 共用参数
    z0 = 5 / 3          # 来自 3-4-5 勾股三角
    tan_alpha = -2 / 3  # tg(α) = 2/3 (image24 PKS 图标注)
    n_max = 48          # 蛋形数量
    total_rotation = 360 * 3  # 总旋转 3 圈
    drift_amp = 0.65    # 最大偏移幅度
    drift_dir = 155     # 偏心方向（左上，接近 image11）

    # ===== 左图：现有同心版本 =====
    ax1 = axes[0]
    ax1.set_aspect('equal')
    all_x_c, all_y_c = [], []

    cmap1 = plt.cm.coolwarm(np.linspace(0.1, 0.9, n_max))

    for n in range(1, n_max + 1):
        # 缩放：sqrt(n) 方案
        amp = 1.0 / math.sqrt(n)
        # 旋转：均匀分布
        rot_deg = (n - 1) / max(n_max - 1, 1) * total_rotation
        rot_rad = -math.radians(rot_deg)

        # 同心：center = (0,0)
        x, y = generate_egg_curve(z0, tan_alpha, amp=amp, center_x=0, center_y=0)
        if len(x) > 0:
            xr, yr = rotate_points(x, y, rot_rad)
            ax1.plot(xr, yr, color=cmap1[n-1], linewidth=1.2, alpha=0.75)
            all_x_c.append(xr)
            all_y_c.append(yr)

    # 标记中心和旋转方向
    ax1.scatter([0], [0], s=80, c='black', zorder=10, marker='+', linewidths=2)
    ax1.annotate('几何中心\n(焦点)', xy=(0, 0), xytext=(0.35, 0.35),
                fontsize=10, ha='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax1.set_title('现有方案：同心蛋形螺旋\n(center 固定于原点)',
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('X', fontsize=11)
    ax1.set_ylabel('Y', fontsize=11)
    ax1.grid(True, alpha=0.25)
    ax1.set_xlim(-1.6, 1.6)
    ax1.set_ylim(-1.6, 1.6)
    ax1.axhline(0, color='gray', linewidth=0.5)
    ax1.axvline(0, color='gray', linewidth=0.5)

    # ===== 右图：偏心版本（sqrt漂移策略）=====
    ax2 = axes[1]
    ax2.set_aspect('equal')

    cmap2 = plt.cm.viridis(np.linspace(0.15, 0.95, n_max))
    center_trajectory_x = []
    center_trajectory_y = []

    for n in range(1, n_max + 1):
        amp = 1.0 / math.sqrt(n)
        rot_deg = (n - 1) / max(n_max - 1, 1) * total_rotation
        rot_rad = -math.radians(rot_deg)

        # ★ 关键差异：计算偏心漂移
        dx, dy = drift_sqrt(n, n_max, drift_amp, direction_deg=drift_dir)

        x, y = generate_egg_curve(z0, tan_alpha, amp=amp, center_x=dx, center_y=dy)
        if len(x) > 0:
            xr, yr = rotate_points(x, y, rot_rad)
            # 注意：先偏移后旋转 = 绕原点的复合变换
            ax2.plot(xr, yr, color=cmap2[n-1], linewidth=1.2, alpha=0.75)
            center_trajectory_x.append(dx)
            center_trajectory_y.append(dy)

    # 标记轨迹
    if center_trajectory_x:
        ax2.plot(center_trajectory_x, center_trajectory_y, 'k--', lw=1.5, alpha=0.4,
                label='中心漂移轨迹')
        ax2.scatter([center_trajectory_x[0]], [center_trajectory_y[0]], s=60, c='red',
                   zorder=10, marker='o', label='起点(外圈)')
        ax2.scatter([center_trajectory_x[-1]], [center_trajectory_y[-1]], s=80, c='blue',
                   zorder=10, marker='*', label='终点(内圈/焦点)')

        # 焦点标注
        fx, fy = center_trajectory_x[-1], center_trajectory_y[-1]
        ax2.annotate(f'偏心焦点\n({fx:.2f}, {fy:.2f})',
                    xy=(fx, fy), xytext=(fx+0.3, fy+0.3),
                    fontsize=10, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='blue'),
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.85))

    # 几何中心参考
    ax2.scatter([0], [0], s=40, c='gray', zorder=5, marker='x', linewidths=1.5,
               alpha=0.5)
    ax2.annotate('原几何中心', xy=(0, 0), xytext=(-0.5, -1.3),
                fontsize=9, color='gray', alpha=0.7)

    ax2.set_title('新方案：偏心蛋形螺旋\n(sqrt漂移 + 旋转复合)',
                 fontsize=14, fontweight='bold')
    ax2.set_xlabel('X', fontsize=11)
    ax2.set_ylabel('Y', fontsize=11)
    ax2.grid(True, alpha=0.25)
    ax2.set_xlim(-1.6, 1.6)
    ax2.set_ylim(-1.6, 1.6)
    ax2.axhline(0, color='gray', linewidth=0.5)
    ax2.axvline(0, color='gray', linewidth=0.5)
    ax2.legend(fontsize=9, loc='lower right')

    plt.suptitle('P027 遗留问题解决：从同心到偏心螺旋蛋\n'
                f'参数: (z₀,tanα)=({z0:.3f},{tan_alpha:.3f}), N={n_max}圈, '
                f'漂移幅={drift_amp}, 方向={drift_dir}°',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '05_eccentric_vs_concentric.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图5: 同心vs偏心对比 → 05_eccentric_vs_concentric.png")


# ============================================================
# 图2：四种偏心策略扫描
# ============================================================
def plot_strategy_comparison():
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))

    strategies = [
        ('A: 线性漂移', drift_linear, 'linear'),
        ('B: 平方根漂移(推荐)', drift_sqrt, 'sqrt'),
        ('C: 双曲漂移(1/x)', drift_hyperbolic, 'hyperbolic'),
        ('D: 螺旋式漂移', drift_spiral, 'spiral'),
    ]

    z0 = 5 / 3
    tan_alpha = -2 / 3
    n_max = 40
    total_rot = 360 * 2
    drift_amp = 0.55
    drift_dir = 155

    for idx, (title, drift_func, name) in enumerate(strategies):
        ax = axes[idx // 2, idx % 2]
        ax.set_aspect('equal')

        cmap = getattr(plt.cm, ['plasma', 'viridis', 'coolwarm', 'cividis'][idx])
        colors = cmap(np.linspace(0.15, 0.95, n_max))

        for n in range(1, n_max + 1):
            amp = 1.0 / math.sqrt(n)
            rot_deg = (n - 1) / max(n_max - 1, 1) * total_rot
            rot_rad = -math.radians(rot_deg)

            dx, dy = drift_func(n, n_max, drift_amp, drift_dir)

            x, y = generate_egg_curve(z0, tan_alpha, amp=amp, center_x=dx, center_y=dy)
            if len(x) > 0:
                # 先偏移再旋转
                xr, yr = rotate_points(x, y, rot_rad)
                ax.plot(xr, yr, color=colors[n-1], linewidth=1.0, alpha=0.7)

        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.2)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.axhline(0, color='gray', linewidth=0.4)
        ax.axvline(0, color='gray', linewidth=0.4)

        # 标注焦点
        dx_last, dy_last = drift_func(n_max, n_max, drift_amp, direction_deg=drift_dir)
        ax.scatter([dx_last], [dy_last], s=50, c='red', zorder=10, marker='*')

    plt.suptitle('四种偏心策略效果扫描\n(目标：复现 image11 Schauberger 偏心螺旋蛋)',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '06_drift_strategies.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图6: 四种偏心策略扫描 → 06_drift_strategies.png")


# ============================================================
# 图3：与 image11 手绘参考的叠加对比
# ============================================================
def plot_reference_overlay():
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')

    # 使用最佳策略（sqrt漂移）
    z0 = 5 / 3
    tan_alpha = -2 / 3
    n_max = 36
    total_rot = 360 * 2.5
    drift_amp = 0.50
    drift_dir = 160  # 微调方向以更接近 image11

    cmap = plt.cm.Greys(np.linspace(0.2, 0.85, n_max))

    for n in range(1, n_max + 1):
        amp = 1.0 / math.sqrt(n)
        rot_deg = (n - 1) / max(n_max - 1, 1) * total_rot
        rot_rad = -math.radians(rot_deg)

        dx, dy = drift_sqrt(n, n_max, drift_amp, direction_deg=drift_dir)

        x, y = generate_egg_curve(z0, tan_alpha, amp=amp, center_x=dx, center_y=dy)
        if len(x) > 0:
            xr, yr = rotate_points(x, y, rot_rad)
            # 用灰度模拟手绘线条粗细变化
            lw = 0.8 + 1.2 * (1 - n / n_max)  # 外粗内细
            ax.plot(xr, yr, color=cmap[n-1], linewidth=lw, alpha=0.8)

    # 标注关键特征
    dx_f, dy_f = drift_sqrt(n_max, n_max, drift_amp, direction_deg=drift_dir)
    ax.scatter([dx_f], [dy_f], s=120, c='red', zorder=10, marker='*', edgecolors='darkred')

    ax.set_title(
        '偏心螺旋蛋 · 最佳参数配置\n'
        '(对比 image11: Schauberger 手绘偏心蛋)\n'
        f'策略=sqrt漂移, 方向={drift_dir}°, 幅={drift_amp}, N={n_max}',
        fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.15)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    # 添加信息框
    info = (
        "特征对比 (vs image11):\n"
        "━━━━━━━━━━━━━━━━\n"
        "✅ 外圈大、内圈小\n"
        "✅ 焦点偏离几何中心\n"
        "✅ 向左上方收敛\n"
        "✅ 曲线间距递减\n"
        "🔶 精确形状需微调参数"
    )
    ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    plt.savefig(os.path.join(output_dir, '07_eccentric_best_match.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图7: 最佳偏心匹配 → 07_eccentric_best_match.png")


# ============================================================
# 图4：偏心参数灵敏度分析
# ============================================================
def plot_sensitivity_analysis():
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))

    z0 = 5 / 3
    tan_alpha = -2 / 3
    n_max = 36
    total_rot = 360 * 2

    configs = [
        ("漂移幅度: 0.30 (小)", 0.30),
        ("漂移幅度: 0.50 (中)", 0.50),
        ("漂移幅度: 0.70 (大)", 0.70),
        ("漂移幅度: 0.90 (极大)", 0.90),
    ]

    for idx, (label, amp_val) in enumerate(configs):
        ax = axes[idx // 2, idx % 2]
        ax.set_aspect('equal')

        cmap = plt.cm.inferno(np.linspace(0.1, 0.9, n_max))

        for n in range(1, n_max + 1):
            amp = 1.0 / math.sqrt(n)
            rot_deg = (n - 1) / max(n_max - 1, 1) * total_rot
            rot_rad = -math.radians(rot_deg)

            dx, dy = drift_sqrt(n, n_max, amp_val, direction_deg=155)

            x, y = generate_egg_curve(z0, tan_alpha, amp=amp, center_x=dx, center_y=dy)
            if len(x) > 0:
                xr, yr = rotate_points(x, y, rot_rad)
                ax.plot(xr, yr, color=cmap[n-1], linewidth=1.0, alpha=0.7)

        ax.set_title(label, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.2)
        ax.set_xlim(-1.6, 1.6)
        ax.set_ylim(-1.6, 1.6)
        ax.axhline(0, color='gray', linewidth=0.4)
        ax.axvline(0, color='gray', linewidth=0.4)

    plt.suptitle('偏心参数灵敏度分析：漂移幅度的影响\n'
                '(策略=B/sqrt漂移, 方向=155°, N=36)',
                fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '08_eccentric_sensitivity.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图8: 偏心参数灵敏度 → 08_eccentric_sensitivity.png")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    print("=" * 60)
    print("  Schauberger 偏心螺旋蛋实现")
    print("  解决 P027: 从同心到偏心")
    print("=" * 60)
    print(f"输出目录: {output_dir}")

    plot_concentric_vs_eccentric()      # 图5: 主对比图
    plot_strategy_comparison()           # 图6: 四种策略
    plot_reference_overlay()             # 图7: 最佳匹配
    plot_sensitivity_analysis()          # 图8: 参数灵敏度

    print("\n" + "=" * 60)
    print("  全部4张图生成完毕!")
    print("=" * 60)
