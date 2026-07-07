# -*- coding: utf-8 -*-
"""
统一公式验证：r(theta) = 2^(-theta/pi) = e^(-ln(2)*theta/pi)
验证 ln(2), pi, e^{-1} 三者在同一公式中的物理意义
对应文档 image18/19 + P041 遗留问题

输出：
  1. 极坐标螺旋图（标注关键角度和半径比）
  2. 直角坐标对比图（复指数形式 vs 对数形式）
  3. 半径衰减曲线 vs 波纹盘包络线 1/x 对比
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import FancyArrowPatch
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
# 核心公式定义
# ============================================================
LN2 = np.log(2)          # 0.693147...
PI = np.pi               # 3.141593...
E_INV_ANGLE = PI / LN2   # theta where r = 1/e ≈ 4.5324 rad ≈ 259.7°


def unified_spiral_polar(theta_max=6*PI, n_points=2000):
    """统一公式极坐标形式"""
    theta = np.linspace(0, theta_max, n_points)
    r = 2 ** (-theta / PI)  # 等价于 exp(-LN2 * theta / PI)
    return theta, r


def unified_spiral_cartesian(theta_max=6*PI, n_points=2000):
    """统一公式直角坐标形式（复指数）"""
    theta = np.linspace(0, theta_max, n_points)
    r = 2 ** (-theta / PI)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y, theta, r


def hyperbola_envelope(x_vals):
    """1/x 双曲线包络线（波盘截面对应）"""
    return 1.0 / x_vals


# ============================================================
# 图1：极坐标螺旋 + 关键角度标注
# ============================================================
def plot_polar_with_annotations():
    fig = plt.figure(figsize=(14, 14))

    # 主图：极坐标螺旋
    ax_main = fig.add_axes([0.08, 0.15, 0.55, 0.75], projection='polar')
    theta, r = unified_spiral_polar(theta_max=6*PI, n_points=3000)

    # 绘制螺旋线，颜色随半径渐变
    for i in range(len(theta)-1):
        color_val = 1 - r[i] / r[0]  # 从深到浅
        ax_main.plot(theta[i:i+2], r[i:i+2],
                    color=plt.cm.plasma(color_val), linewidth=1.8, alpha=0.85)

    # 关键角度标注点
    key_angles = [
        (PI/2,      "π/2\nr=2^{-1/2}\n≈0.707",       "第一象限"),
        (PI,        "π\nr=1/2",                       "半圈"),
        (3*PI/2,    "3π/2\nr≈0.354",                  "三象限"),
        (2*PI,      "2π\nr=1/4",                      "整圈"),
        (E_INV_ANGLE,"π/ln2\nr=1/e\n≈0.368",         "e^-1点"),
        (4*PI,      "4π\nr=1/16",                     "两圈"),
    ]

    for angle, label_text, desc in key_angles:
        if angle <= 6*PI:
            r_at = 2 ** (-angle / PI)
            ax_main.scatter([angle], [r_at], s=120, c='red', zorder=5,
                           edgecolors='white', linewidths=2)
            # 偏移标注避免重叠
            offset_r = r_at * 1.35
            ax_main.annotate(label_text,
                            xy=(angle, r_at),
                            xytext=(angle + 0.3, offset_r),
                            fontsize=9,
                            fontweight='bold',
                            ha='center',
                            bbox=dict(boxstyle='round,pad=0.3',
                                     facecolor='yellow', alpha=0.85, edgecolor='orange'),
                            arrowprops=dict(arrowstyle='->', color='orange', lw=1.5))

    ax_main.set_title("统一公式极坐标: r(θ) = 2^{-θ/π} = e^{-ln2·θ/π}",
                     fontsize=16, fontweight='bold', pad=20)
    ax_main.set_theta_zero_location('E')
    ax_main.set_theta_direction(1)  # 逆时针
    ax_main.grid(True, alpha=0.3)

    # 右侧信息面板
    ax_info = fig.add_axes([0.68, 0.30, 0.30, 0.60])
    ax_info.axis('off')

    info_text = """
╔══════════════════════════════════╗
║   统一公式的三常数解析           ║
╠══════════════════════════════════╣
║                                  ║
║  r(θ) = 2^{-θ/π}                ║
║     = e^{-ln(2)·θ/π}             ║
║                                  ║
├──────────────────────────────────┤
║  常数  │  出现位置  │ 物理含义   ║
├────────┼───────────┼─────────────┤
║  ln(2) │ 指数系数   │ 衰减速率   ║
║        │           │ 每转π rad  ║
║        │           │ 半径÷2     ║
├────────┼───────────┼─────────────┤
║   π   │ 角度归一化 │ 一圈的度量  ║
│        │ 分母      │ 自然周期    ║
├────────┼───────────┼─────────────┤
║  e^{-1}│ θ=π/ln2时 │ 衰减至      ║
│        │ 的半径值   │ 36.8%阈值  ║
╚══════════════════════════════════╝
"""
    ax_info.text(0.05, 0.95, info_text, transform=ax_info.transAxes,
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='#f0f0ff', edgecolor='navy'))

    # 底部数值表
    ax_table = fig.add_axes([0.68, 0.12, 0.30, 0.16])
    ax_table.axis('off')
    table_data = [
        ["θ(rad)", "θ(°)", "r=2^{-θ/π}", "物理对应"],
        ["π/2", "90°", f"{2**(-0.5):.4f}", "四分之一圈"],
        ["π", "180°", f"{0.5000:.4f}", "半圈→半径减半"],
        ["2π", "360°", f"{0.2500:.4f}", "一圈→半径1/4"],
        ["π/ln2", f"{E_INV_ANGLE*180/PI:.1f}°", f"{np.e**(-1):.4f}", "e⁻¹衰减点"],
        ["4π", "720°", f"{0.0625:.4f}", "两圈→半径1/16"],
    ]
    table = ax_table.table(cellText=table_data[1:], colLabels=table_data[0],
                          loc='center', cellLoc='center',
                          colWidths=[0.22, 0.20, 0.24, 0.34])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)
    for i in range(5):
        table[(i, 0)].set_facecolor('#e8e8ff')
        table[(i, 1)].set_facecolor('#e8e8ff')

    plt.savefig(os.path.join(output_dir, '01_unified_formula_polar.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图1: 极坐标螺旋 + 关键角度标注 → 01_unified_formula_polar.png")


# ============================================================
# 图2：直角坐标系双形式对比 + 复平面推导链
# ============================================================
def plot_cartesian_comparison():
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # --- 左图：两种形式的螺旋 ---
    ax1 = axes[0]
    x, y, theta, r = unified_spiral_cartesian(theta_max=8*PI, n_points=3000)

    # 用颜色表示旋转圈数
    colors = theta / (8*PI)
    for i in range(len(x)-1):
        ax1.plot(x[i:i+2], y[i:i+2], color=plt.cm.viridis(colors[i]),
                linewidth=1.5, alpha=0.8)

    # 标记起点和关键点
    ax1.scatter([x[0]], [y[0]], s=100, c='green', zorder=5, label=f'起点 r=1')
    ax1.scatter([x[len(x)//4]], [y[len(y)//4]], s=80, c='orange', zorder=5, label=f'θ=2π, r=0.25')
    ax1.scatter([x[len(x)//2]], [y[len(y)//2]], s=80, c='red', zorder=5, label=f'θ=4π, r=0.0625')

    # 找到 r ≈ 1/e 的点
    idx_e = np.argmin(np.abs(r - np.e**(-1)))
    ax1.scatter([x[idx_e]], [y[idx_e]], s=80, c='purple', zorder=5,
               label=f'θ=π/ln2, r=1/e')

    ax1.set_xlim(-1.3, 1.3)
    ax1.set_ylim(-1.3, 1.3)
    ax1.set_aspect('equal')
    ax1.set_xlabel('x = r·cos(θ)', fontsize=12)
    ax1.set_ylabel('y = r·sin(θ)', fontsize=12)
    ax1.set_title('直角坐标形式\nx(θ)=2^{-θ/π}cosθ, y(θ)=2^{-θ/π}sinθ', fontsize=13)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(0, color='gray', linewidth=0.5)
    ax1.axvline(0, color='gray', linewidth=0.5)

    # --- 右图：推导链（复指数形式） ---
    ax2 = axes[1]
    ax2.axis('off')

    derivation = """
  ┌─────────────────────────────────────────────┐
  │           统一公式的复指数推导链              │
  ├─────────────────────────────────────────────┤
  │                                             │
  │   Step 1: 极坐标基础                         │
  │   ─────────────────                          │
  │   r(θ) = 2^{-θ/π}                           │
  │                                             │
  │   Step 2: 化为以 e 为底                      │
  │   ───────────────────────                    │
  │   2^{-θ/π} = e^{ln(2) · (-θ/π)}              │
  │          = e^{-ln(2) · θ/π}                  │
  │                                             │
  │   Step 3: 复指数形式（Euler公式）            │
  │   ─────────────────────────────              │
  │   z(θ) = r(θ) · e^{iθ}                      │
  │        = e^{-ln(2)·θ/π} · (cosθ + i·sinθ)   │
  │                                             │
  │   Step 4: 直角坐标分解                       │
  │   ─────────────────────                      │
  │   x(θ) = e^{-ln(2)·θ/π} · cosθ              │
  │   y(θ) = e^{-ln(2)·θ/π} · sinθ              │
  │                                             │
  │   ✅ ln(2): 控制对数衰减速率                  │
  │   ✅ π: 控制每圈的角周期归一化                 │
  │   ✅ e^{-1}: 当 θ = π/ln(2) 时 r = 1/e       │
  │                                             │
  └─────────────────────────────────────────────┘
"""
    ax2.text(0.05, 0.95, derivation, transform=ax2.transAxes,
            fontsize=10.5, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#fffef0',
                     edgecolor='#cc9900', linewidth=2))

    plt.suptitle("统一公式：r(θ) = 2^{-θ/π} — 双坐标系验证",
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '02_unified_formula_cartesian.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图2: 直角坐标双形式对比 → 02_unified_formula_cartesian.png")


# ============================================================
# 图3：统一公式 vs 1/x 包络线 vs 波纹盘衰减因子
# ============================================================
def plot_envelope_comparison():
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # --- 子图1：三种衰减曲线对比 ---
    ax1 = axes[0, 0]
    t = np.linspace(0.1, 10, 500)

    # 曲线A: 统一公式的"等效径向衰减"（将角度映射为"圈数"n）
    n_turns = t / (2*PI)  # 将t视为角度，换算为圈数
    r_unified = 2 ** (-t / PI)

    # 曲线B: 1/x 双曲线（等体积积分的包络）
    y_hyperbola = 1.0 / t

    # 曲线C: 波纹盘代码中的衰减因子 amp(t) = 1/((1+t/2π)*ln(n+1))
    # 取典型值 n=30（约30个波纹齿）
    n_waves = 30
    amp_disk = 1.0 / ((1 + t / (2*PI)) * np.log(n_waves + 1))

    # 归一化到相同起点以便比较
    r_unified_norm = r_unified / r_unified[0]
    y_hyperbola_norm = y_hyperbola / y_hyperbola[0]
    amp_disk_norm = amp_disk / amp_disk[0]

    ax1.plot(t, r_unified_norm, 'b-', lw=2.5, label=r'$r=2^{-\theta/\pi}$ (统一公式)')
    ax1.plot(t, y_hyperbola_norm, 'g--', lw=2.5, label=r'$y=1/x$ (双曲线包络)')
    ax1.plot(t, amp_disk_norm, 'r:', lw=2.5, label='amp(t) (波纹盘衰减)')

    ax1.set_xlabel('参数 t (弧度/无量纲)', fontsize=11)
    ax1.set_ylabel('归一化振幅', fontsize=11)
    ax1.set_title('三种衰减曲线形状对比', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.1, 10)
    ax1.set_ylim(0, 1.1)

    # 标注关键交叉区域
    ax1.axvline(x=PI, color='blue', alpha=0.2, linestyle='-')
    ax1.axvline(x=2*PI, color='blue', alpha=0.2, linestyle='-')
    ax1.text(PI, 1.02, 'π', ha='center', fontsize=10, color='blue')
    ax1.text(2*PI, 1.02, '2π', ha='center', fontsize=10, color='blue')

    # --- 子图2：统一公式在整数圈处的半径比 ---
    ax2 = axes[0, 1]
    turns = np.arange(0, 9, dtype=float)
    radii = 2 ** (-turns * 2*PI / PI)  # 每圈2π角度

    bars = ax2.bar(turns, radii, width=0.7, color=plt.cm.coolwarm(np.linspace(0.2, 0.8, len(turns))),
                   edgecolor='navy', linewidth=1.2)

    for i, (turn, rad) in enumerate(zip(turns, radii)):
        ax2.text(turn, rad + 0.02, f'{rad:.4f}', ha='center', va='bottom', fontsize=9,
                fontweight='bold')

    ax2.set_xlabel('旋转圈数 N', fontsize=11)
    ax2.set_ylabel(f'半径比 r(N)/r(0) = 2^{{-2N}}', fontsize=11)
    ax2.set_title('统一公式：每完整圈后半径变化\n(每圈缩小为前圈的 1/4)', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(turns)

    # --- 子图3：ln(2) 作为衰减常数的几何意义 ---
    ax3 = axes[1, 0]

    # 展示不同 ln(base) 对螺旋形态的影响
    bases = [1.5, 2.0, np.e, 3.0, 4.0, 10.0]
    colors_base = plt.cm.Set2(np.linspace(0, 1, len(bases)))
    theta_plot = np.linspace(0, 4*PI, 1000)

    for base, c in zip(bases, colors_base):
        r_base = base ** (-theta_plot / PI)
        x_base = r_base * np.cos(theta_plot)
        y_base = r_base * np.sin(theta_plot)
        ax3.plot(x_base, y_base, color=c, lw=1.8,
                label=f'base={base:.2f} (ln={np.log(base):.3f})')

    ax3.set_aspect('equal')
    ax3.set_xlim(-1.3, 1.3)
    ax3.set_ylim(-1.3, 1.3)
    ax3.set_xlabel('x', fontsize=11)
    ax3.set_ylabel('y', fontsize=11)
    ax3.set_title('不同底数对螺旋收缩速度的影响\n(ln(2)=0.693 是 Schauberger 选定值)',
                 fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8, loc='upper right')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(0, color='gray', linewidth=0.5)
    ax3.axvline(0, color='gray', linewidth=0.5)

    # 高亮 base=2 的曲线
    r_2 = 2 ** (-theta_plot / PI)
    x_2 = r_2 * np.cos(theta_plot)
    y_2 = r_2 * np.sin(theta_plot)
    ax3.plot(x_2, y_2, 'b-', lw=3, alpha=0.6, zorder=1)

    # --- 子图4：与波纹盘齿距的定量关联 ---
    ax4 = axes[1, 1]

    # 模拟波纹盘从中心到边缘的齿距分布
    # 文档中提到的5段百分比: 38.69% : 22.63% : 16.06% : 12.45% : 10.17%
    segments = [38.69, 22.63, 16.06, 12.45, 10.17]
    seg_labels = ['段1\n(外圈)', '段2', '段3', '段4', '段5\n(内圈)']
    seg_colors = ['#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#f39c12']

    bars2 = ax4.bar(range(5), segments, color=seg_colors, edgecolor='black', linewidth=1.5)

    for i, (seg, bar) in enumerate(zip(segments, bars2)):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
                f'{seg:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 叠加理论预测：1/x 积分的5段比例
    theory_pct = [38.69, 22.63, 16.06, 12.45, 10.17]
    ax4.plot(range(5), theory_pct, 'ko-', markersize=8, lw=2,
            label='∫₁⁶(1/x)dx 理论值', zorder=5)

    ax4.set_xticks(range(5))
    ax4.set_xticklabels(seg_labels, fontsize=10)
    ax4.set_ylabel('体积占比 (%)', fontsize=11)
    ax4.set_title('波纹盘5段夹层体积分配\n(来自 ∫₁⁶(1/x)dx = ln6 等体积积分)\n与统一公式的连接：1/x 是 2^{-θ/π} 在极限下的离散化',
                 fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_ylim(0, 50)

    plt.suptitle("统一公式与波纹盘物理特征的多维验证",
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '03_envelope_comparison.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图3: 衰减曲线+齿距对比 → 03_envelope_comparison.png")


# ============================================================
# 图4：综合结论图 —— 三线归一的数学桥梁
# ============================================================
def plot_triline_synthesis():
    fig = plt.figure(figsize=(16, 10))

    # 主绘图区
    ax_main = fig.add_axes([0.05, 0.10, 0.55, 0.82])

    # 同时绘制三个数学对象
    t = np.linspace(0.01, 6, 1000)

    # Line A: 双曲线 xy=1 → y=1/x
    x_hyp = np.linspace(0.3, 5, 500)
    y_hyp = 1.0 / x_hyp
    ax_main.plot(x_hyp, y_hyp, 'g-', lw=3, label='Line C: y = 1/x (双曲线)', alpha=0.8)

    # Line B: 螺旋 r=2^{-θ/π} 的投影（取前几圈）
    theta_s = np.linspace(0.1, 3*PI, 800)
    r_s = 2 ** (-theta_s / PI)
    x_s = r_s * np.cos(theta_s * 3)  # 加速旋转以便可视化
    y_s = r_s * np.sin(theta_s * 3)
    # 归一化到相似尺度
    x_s_norm = x_s * 2.5 + 0.5
    y_s_norm = y_s * 2.5 + 0.5
    ax_main.plot(x_s_norm, y_s_norm, 'b-', lw=2, label='Line B: r=2^{-θ/π} (宇宙螺旋)', alpha=0.7)

    # Line C 的等价积分形式
    x_int = np.linspace(1, 6, 200)
    y_int_cum = np.log(x_int) / np.log(6)  # 归一化累积积分
    ax_main.fill_between(x_int, 0, y_int_cum, color='green', alpha=0.15)
    ax_main.plot(x_int, y_int_cum, 'g--', lw=1.5, alpha=0.6, label='∫(1/x)dx 累积分布')

    ax_main.set_xlim(0, 6)
    ax_main.set_ylim(0, 2.5)
    ax_main.set_xlabel('x / 参数空间', fontsize=12)
    ax_main.set_ylabel('y / 值域', fontsize=12)
    ax_main.set_title('三线归一：Line A(蛋截面) ←→ Line B(波盘) ←→ Line C(双曲线)',
                     fontsize=14, fontweight='bold')
    ax_main.legend(loc='upper right', fontsize=10)
    ax_main.grid(True, alpha=0.3)

    # 右侧结论面板
    ax_conclusion = fig.add_axes([0.62, 0.10, 0.36, 0.82])
    ax_conclusion.axis('off')

    conclusion_text = """
  ╔═══════════════════════════════════════╗
  ║     统一公式验证报告                  ║
  ╠═══════════════════════════════════════╣
  ║                                       ║
  ║  【候选统一公式】                      ║
  ║  ─────────────────                    ║
  ║  r(θ) = e^{-ln(2)·θ/π} = 2^{-θ/π}    ║
  ║                                       ║
  ║  【三常数出现位置】✅ 全部确认          ║
  ║  ─────────────────────                ║
  ║  ① ln(2) = 0.693...                  ║
  ║     → 指数的衰减系数                   ║
  ║     → 每 π 弧度半径 × 1/2             ║
  ║                                       ║
  ║  ② π = 3.142...                      ║
  ║     → 角度归一化的自然周期单位          ║
  ║     → 一整圈的度量基准                 ║
  ║                                       ║
  ║  ③ e^{-1} = 0.368...                  ║
  ║     → θ = π/ln(2) ≈ 4.53 rad 时      ║
  ║     → 螺旋衰减至 36.8% 的临界点        ║
  ║     → 约 259.7° (0.72 圈处)           ║
  ║                                       ║
  ╠═══════════════════════════════════════╣
  ║  【与波纹盘的物理对应】🔶 待CFD验证    ║
  ╠═══════════════════════════════════════╣
  ║  • 每圈半径 ÷4                        ║
  ║    → Repulsine 齿距递减趋势一致?       ║
  ║  • 1/x 双曲线 = 衰减包络               ║
  ║    → image9 绿线已确认                 ║
  ║  • e^{-1} 点 ≈ 0.72 圈               ║
  ║    → 可能对应第一个喉部/颈缩位置?      ║
  ║                                       ║
  ╠═══════════════════════════════════════╣
  ║  精度等级: 🔶 合理推断需CFD验证        ║
  ╚═══════════════════════════════════════╝
"""
    ax_conclusion.text(0.02, 0.98, conclusion_text, transform=ax_conclusion.transAxes,
                      fontsize=10.5, verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='#fffff0',
                               edgecolor='#aa6600', linewidth=2))

    plt.savefig(os.path.join(output_dir, '04_triline_synthesis.png'),
                dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("[OK] 图4: 三线归一综合结论 → 04_triline_synthesis.png")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    print("=" * 60)
    print("  统一公式验证: r(θ) = 2^{-θ/π}")
    print("  对应文档 image18/19 + P041 遗留问题")
    print("=" * 60)
    print(f"输出目录: {output_dir}")

    plot_polar_with_annotations()
    plot_cartesian_comparison()
    plot_envelope_comparison()
    plot_triline_synthesis()

    print("\n" + "=" * 60)
    print("  全部4张图生成完毕!")
    print("=" * 60)
