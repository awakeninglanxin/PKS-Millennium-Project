# -*- coding: utf-8 -*-
"""
双曲线与3条不同斜度线 — matplotlib 独立可视化
原版：Rhino脚本 29_双曲线与3条斜度线.py / 双曲线与3条不同斜度线.py
转换：Rhino → matplotlib PNG 输出

核心内容：
- 双曲线 y = 1/x，用 x=e^t 参数化（对数均匀采样）
- 3条斜切线：(k,b) = {(2/3,5/3), (8/3,10/3), (32/3,20/3)}
  这些 (k,b) 来自蛋形斜切公式的放大序列：每档 ×4
- 圆（半径9，在ZX平面）→ 转换为XY平面
"""

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import os

# === 铁律57: 三步初始化中文字体 ===
cache_dir = matplotlib.get_cachedir()
try:
    for f in os.listdir(cache_dir):
        if f.endswith('.json'):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass
except:
    pass
fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

import numpy as np

# ============================================================
# 1. 双曲线 y = 1/x（与原Rhino脚本一致的参数化）
# ============================================================
# 原脚本: t_start = ln(1/9), t_end = ln(9), x = e^t, y = e^{-t} = 1/x
t_start = math.log(1/9)  # x = 1/9
t_end   = math.log(9)    # x = 9
steps   = 200            # 比原版增加10倍插值点数（更平滑的曲线）

t_vals = np.linspace(t_start, t_end, steps)
x_hyper = np.exp(t_vals)
y_hyper = np.exp(-t_vals)  # = 1/x

# ============================================================
# 2. 三条线（与原Rhino脚本一致）
# ============================================================
lines = [
    {"k": 2/3,  "b": 5/3,   "color": "#0066CC", "label": r"线1: $k=\frac{2}{3}$, $b=\frac{5}{3}$"},
    {"k": 8/3,  "b": 10/3,  "color": "#CC0000", "label": r"线2: $k=\frac{8}{3}$, $b=\frac{10}{3}$"},
    {"k": 32/3, "b": 20/3,  "color": "#CC9900", "label": r"线3: $k=\frac{32}{3}$, $b=\frac{20}{3}$"},
]

# 每条线从 y=0 交点画到 x=1
line_segments = []
for ln in lines:
    kk, bb = ln["k"], ln["b"]
    x_start = -bb / kk     # y=0 → x = -b/k
    x_end = 1.0            # x=1 → y = k + b
    y_end = kk * x_end + bb
    line_segments.append({
        "x": [x_start, x_end],
        "y": [0, y_end],
        "color": ln["color"],
        "label": ln["label"],
        "k": kk,
        "b": bb,
    })

# ============================================================
# 3. 圆（半径9，原版在ZX平面 → 我们画在XY平面）
# ============================================================
theta_circle = np.linspace(0, 2*math.pi, 500)
circle_x = 9 * np.cos(theta_circle)
circle_y = 9 * np.sin(theta_circle)

# ============================================================
# 图1：主图 — 双曲线 + 3条线 + 交点分析
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(18, 9))
fig.suptitle(
    r'双曲线 $y=1/x$ 与3条不同斜度线的几何关系' + '\n'
    r'$(k,b) \in \left\{\left(\frac{2}{3},\frac{5}{3}\right), '
    r'\left(\frac{8}{3},\frac{10}{3}\right), '
    r'\left(\frac{32}{3},\frac{20}{3}\right)\right\}$ — 每档×4递进',
    fontsize=15, fontweight='bold')

# --- 左图：大范围视图（含圆） ---
ax1 = axes[0]
ax1.plot(x_hyper, y_hyper, 'b-', lw=2.5, alpha=0.9, label=r'$y=1/x$ (双曲线)')
ax1.plot(circle_x, circle_y, 'gray', lw=1.5, alpha=0.5, label='r=9 参考圆')

for seg in line_segments:
    ax1.plot(seg["x"], seg["y"], '-', color=seg["color"], lw=2.0, label=seg["label"])
    # 标注参数
    mid_x = (seg["x"][0] + seg["x"][1]) / 2
    mid_y = (seg["y"][0] + seg["y"][1]) / 2
    ax1.annotate(f'k={seg["k"]:.2f}\nb={seg["b"]:.2f}',
                 xy=(mid_x, mid_y), fontsize=7, color=seg["color"],
                 ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

# 特殊标注：(k,b)=(2/3,5/3) 的交点
k0, b0 = 2/3, 5/3
# 解 y=1/x 与 y=kx+b 的交点: kx+b = 1/x → kx^2 + bx - 1 = 0
disc = b0**2 + 4*k0
if disc > 0:
    xs = [(-b0 - math.sqrt(disc))/(2*k0), (-b0 + math.sqrt(disc))/(2*k0)]
    for xs_i in xs:
        if 0 < xs_i < 9:
            ys_i = 1/xs_i
            ax1.plot(xs_i, ys_i, 'ro', markersize=10, zorder=10)
            ax1.annotate(f'交点\n({xs_i:.2f}, {ys_i:.2f})',
                         xy=(xs_i, ys_i), fontsize=9, color='darkred',
                         xytext=(xs_i-1.2, ys_i+0.5),
                         arrowprops=dict(arrowstyle='->', color='darkred'))

ax1.axhline(y=0, color='black', lw=0.5, alpha=0.3)
ax1.axvline(x=0, color='black', lw=0.5, alpha=0.3)
ax1.set_xlabel('X', fontsize=12)
ax1.set_ylabel('Y', fontsize=12)
ax1.set_title('大范围视图：双曲线+3条线+参考圆 (r=9)', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', fontsize=8, ncol=2)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(-5, 9.5)
ax1.set_ylim(-0.5, 12)
ax1.set_aspect('equal')

# --- 右图：放大视图（靠近原点区域，展示双曲线渐近行为） ---
ax2 = axes[1]
# 更精细的双曲线（x∈[0.1, 9] 对数采样）
x_fine = np.logspace(-1, 1, 400)
y_fine = 1/x_fine
ax2.plot(x_fine, y_fine, 'b-', lw=2.5, alpha=0.9, label=r'$y=1/x$ (log尺度)')

for seg in line_segments:
    ax2.plot(seg["x"], seg["y"], '-', color=seg["color"], lw=2.0, label=seg["label"])
    # 计算与y=1/x的交点
    kk, bb = seg["k"], seg["b"]
    disc2 = bb**2 + 4*kk
    if disc2 > 0:
        x_inter = (-bb + math.sqrt(disc2)) / (2*kk)
        if 0 < x_inter < 9:
            y_inter = 1/x_inter
            ax2.plot(x_inter, y_inter, 'o', color=seg["color"], markersize=8, zorder=10)
            ax2.annotate(f'({x_inter:.2f}, {y_inter:.2f})',
                         xy=(x_inter, y_inter), fontsize=7, color=seg["color"],
                         xytext=(x_inter+0.2, y_inter+0.2),
                         arrowprops=dict(arrowstyle='->', color=seg["color"], lw=0.6))

# 渐近线标注
ax2.axvline(x=0, color='red', ls=':', lw=1.0, alpha=0.4, label='渐近线 x=0')
ax2.axhline(y=0, color='red', ls=':', lw=1.0, alpha=0.4, label='渐近线 y=0')

ax2.set_xlabel('X', fontsize=12)
ax2.set_ylabel('Y', fontsize=12)
ax2.set_title('放大视图：交点与渐近行为', fontsize=13, fontweight='bold')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(-1.5, 6.5)
ax2.set_ylim(-0.5, 12)

plt.tight_layout(rect=[0, 0, 1, 0.93])
out1 = '12_双曲线与3条斜度线.png'
fig.savefig(out1, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out1}")
plt.close()

# ============================================================
# 图2：交点分析 — 3条线的斜率-截距放大序列
# ============================================================
fig2, axes2 = plt.subplots(1, 3, figsize=(18, 6))
fig2.suptitle(
    r'3条斜度线与双曲线 $y=1/x$ 的接触分析 | '
    r'$\alpha_1=\arctan(2/3)\approx 33.7°$, '
    r'$\alpha_2=\arctan(8/3)\approx 69.4°$, '
    r'$\alpha_3=\arctan(32/3)\approx 84.6°$',
    fontsize=13, fontweight='bold')

for idx, seg in enumerate(line_segments):
    ax = axes2[idx]
    kk, bb = seg["k"], seg["b"]

    # 双曲线
    ax.plot(x_hyper, y_hyper, 'b-', lw=2.0, alpha=0.85, label=r'$y=1/x$')
    # 线
    ax.plot(seg["x"], seg["y"], '-', color=seg["color"], lw=2.5,
            label=rf'$y={kk:.2f}x+{bb:.2f}$')
    # 交点
    disc3 = bb**2 + 4*kk
    if disc3 > 0:
        xs3 = [(-bb - math.sqrt(disc3))/(2*kk), (-bb + math.sqrt(disc3))/(2*kk)]
        for xi in xs3:
            if 0 < xi < 9:
                yi = 1/xi
                ax.plot(xi, yi, 'o', color=seg["color"], markersize=10, zorder=10)

    # 标注斜率角
    angle_rad = math.atan(kk)
    angle_deg = math.degrees(angle_rad)
    ax.annotate(rf'$\alpha={angle_deg:.1f}°$',
                xy=(0.5, bb + kk*0.5), fontsize=11,
                color=seg["color"], fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    ax.axhline(y=0, color='black', lw=0.5, alpha=0.3)
    ax.axvline(x=0, color='black', lw=0.5, alpha=0.3)
    ax.set_xlabel('X', fontsize=10)
    ax.set_ylabel('Y', fontsize=10)
    ax.set_title(
        rf'线{idx+1}: $(k,b)=(\frac{{{int(kk*3) if idx==0 else int(kk*3)}}}{{3}},\frac{{{int(bb*3)}}}{{3}})$'
        f'\nα={angle_deg:.1f}°',
        fontsize=11, fontweight='bold', color=seg["color"])
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1, 4.5)
    ax.set_ylim(-0.5, 6)

plt.tight_layout(rect=[0, 0, 1, 0.9])
out2 = '13_双曲线与3条线逐条分析.png'
fig2.savefig(out2, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out2}")
plt.close()

# ============================================================
# 图3：几何意义 — 超双曲锥斜切的"切片角度族"
# ============================================================
fig3, ax3 = plt.subplots(1, 1, figsize=(12, 9))
fig3.suptitle(
    r'几何溯源：超双曲锥 $z=\frac{1}{\sqrt{x^2+y^2}}$ 在不同斜度 $(k,b)$ 下的截线族' + '\n'
    r'$(k,b)=(\frac{2}{3},\frac{5}{3})$ 来自3-4-5勾股三角 $\rightarrow$ 每档×4递进 $\rightarrow$ '
    r'$xy=1$ 双曲线上的五点',
    fontsize=13, fontweight='bold')

# 画 xy=1 双曲线
x_log = np.logspace(-1.5, 1.2, 500)
y_log = 1/x_log
ax3.plot(x_log, y_log, 'navy', lw=2.8, alpha=0.85, label=r'$xy=1$ 双曲线 (宇宙反比律)')

# 3条线
for seg in line_segments:
    ax3.plot(seg["x"], seg["y"], '-', color=seg["color"], lw=2.2, label=seg["label"])

# 标注 Schauberger 1970 图的五大反比律来源
ax3.annotate(r'$xy=1$ Schauberger 1970',
             xy=(1, 1), fontsize=12, color='navy', fontweight='bold',
             xytext=(2.5, 0.3),
             arrowprops=dict(arrowstyle='->', color='navy', lw=1.2),
             bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.9))

# 物理反比律标注
laws = [
    r'数量$\times$质量 = 1',
    r'波长$\times$频率 = 1',
    r'半径$\times$角速度 = 1',
    r'$\tan\times\cot = 1$',
    r'距离$\times$信息 = 1',
]
for i, law in enumerate(laws):
    y_pos = 7.5 - i*0.8
    ax3.annotate(law, xy=(0.15, y_pos), fontsize=9,
                 color='navy', style='italic',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='lightcyan', alpha=0.6))

# 标注3-4-5三角
ax3.annotate(
    r'$(k,b)=(\frac{2}{3},\frac{5}{3})$'
    r'$\leftarrow$ 3-4-5 勾股三角'
    r'$\rightarrow$'
    r'$\tan\alpha = 2/3$'
    r'$\rightarrow$'
    r'$\alpha\approx 33.69°$',
    xy=(0.8, 2.0), fontsize=11, color='#0066CC', fontweight='bold',
    bbox=dict(boxstyle='round', facecolor='#f0f0ff', edgecolor='#0066CC', alpha=0.9))

ax3.axhline(y=0, color='black', lw=0.5, alpha=0.3)
ax3.axvline(x=0, color='black', lw=0.5, alpha=0.3)
ax3.set_xlabel('X', fontsize=12)
ax3.set_ylabel('Y', fontsize=12)
ax3.set_title(
    r'$xy=1$ 双曲线上的斜线族 — 超双曲锥 $z=\frac{1}{\sqrt{x^2+y^2}}$ 的斜切参数扫描',
    fontsize=13, fontweight='bold')
ax3.legend(loc='lower left', fontsize=8, ncol=2)
ax3.grid(True, alpha=0.3, which='both')
ax3.set_xlim(-1, 6.5)
ax3.set_ylim(-0.5, 9.5)

plt.tight_layout(rect=[0, 0, 1, 0.94])
out3 = '14_双曲线与3条线几何溯源.png'
fig3.savefig(out3, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out3}")
plt.close()

print("\n=== 全部完成 ===")
