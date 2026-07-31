"""
cop_formula_figures.py — 暗能量COP公式配套图表生成
===================================================
基于 周治平《暗能量转换成为附加磁能的论证》2014

生成图表（匹配原PDF风格）：
  图3：铁磁材料的 B-H-μ 曲线（灰度风格，传统学术论文样式）
  图4：铁磁材料的饱和磁能 W_Hs 和附加磁能 W_Hf（品红B-H曲线+粉底W_Hf区域）
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_统一解\打通暗能量与磁场与cop公式"

# 参考原图品红色
PINK_CURVE = '#E684B6'      # B-H曲线品红 ~(230,132,182)
PINK_FILL = '#E684B6'       # W_Hf矩形填充
PINK_EDGE = '#D472A0'       # W_Hf矩形边框
W_HF_ALPHA = 0.48           # W_Hf矩形透明度


def figure3_bh_mu_curve():
    """图3：铁磁材料的 B-H-μ 曲线

    灰度风格，匹配传统学术论文样式：
    - 浅灰色背景
    - B-H曲线：黑色实线
    - μ曲线：黑色虚线
    - 标注 H_S, H_X, B_S
    - 不填充彩色区域
    """
    H = np.linspace(0, 10, 500)
    H_s = 1.5    # 匹配参考图：B-H饱和拐点在x≈15%处
    H_x = 10.0
    B_s = 1.5

    # B-H 曲线：线性段(0→H_s) + 早饱和段(H_s→H_x)
    B = np.zeros_like(H)
    mask_linear = H <= H_s
    mask_sat = H > H_s
    B[mask_linear] = (B_s / H_s) * H[mask_linear]
    # 饱和段：较早快速平坦化
    B[mask_sat] = B_s * (1 - 0.15 * np.exp(-(H[mask_sat] - H_s) / 1.0))

    # μ 曲线：线性段常数，非线性段快速下降
    mu_linear = B_s / H_s
    mu = np.zeros_like(H)
    mu[mask_linear] = mu_linear
    mu[mask_sat] = B_s / (H[mask_sat] + 0.3)

    fig, ax1 = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor('#ECECEC')
    ax1.set_facecolor('#ECECEC')

    # B-H 曲线 — 黑色实线
    ax1.plot(H, B, color='#000000', linewidth=2.0, zorder=4,
             label=r'$B$$-$$H$ 曲线')

    ax1.set_xlabel(r'$H$', fontsize=13)
    ax1.set_ylabel(r'$B$', fontsize=13)
    ax1.set_xlim(0, H_x * 1.02)
    ax1.set_ylim(0, B_s * 1.35)
    ax1.tick_params(labelsize=10)

    # μ 曲线 — 黑色虚线（右轴）
    ax2 = ax1.twinx()
    ax2.plot(H, mu, color='#000000', linewidth=1.8, linestyle='--',
             zorder=3, dashes=(5, 3), label=r'$\mu$ 曲线')
    ax2.set_ylabel(r'$\mu$', fontsize=13)
    ax2.set_ylim(0, mu_linear * 1.5)
    ax2.tick_params(labelsize=10)

    # 标注线 H_S, H_X, B_S
    ax1.axvline(x=H_s, color='#666666', linestyle=':', linewidth=1.0, alpha=0.7)
    ax1.axvline(x=H_x, color='#666666', linestyle=':', linewidth=1.0, alpha=0.7)
    ax1.axhline(y=B_s, color='#888888', linestyle='-.', linewidth=1.0, alpha=0.6)

    # 简洁标注
    ax1.annotate(r'$H_S$', xy=(H_s, 0.05), fontsize=12, fontweight='bold',
                 ha='center', color='#333333',
                 xytext=(H_s - 0.3, 0.42),
                 arrowprops=dict(arrowstyle='->', color='#555555', lw=1.0))

    ax1.annotate(r'$H_X$', xy=(H_x, 0.05), fontsize=12, fontweight='bold',
                 ha='center', color='#333333',
                 xytext=(H_x + 0.3, 0.30),
                 arrowprops=dict(arrowstyle='->', color='#555555', lw=1.0))

    ax1.annotate(r'$B_S$', xy=(0.3, B_s), fontsize=12, fontweight='bold',
                 color='#333333',
                 xytext=(0.3, B_s + 0.15),
                 arrowprops=dict(arrowstyle='->', color='#888888', lw=1.0))

    # 图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right',
               fontsize=11, framealpha=0.85, edgecolor='#999999')

    # 标题
    ax1.set_title('图3  铁磁材料的 B-H-μ 曲线', fontsize=14, fontweight='bold',
                  pad=12)

    # 底部说明
    fig.text(0.5, 0.01,
             r'$0 \rightarrow H_S$: $\mu$ 线性域，$\Phi_L \propto i$，楞次定律有效'
             r'    |    $H_S \rightarrow H_X$: $\mu$ 非线性域，$\Phi_L$=const，楞次定律失效',
             ha='center', fontsize=9, color='#555555')

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    outpath = f"{OUTPUT_DIR}/图3 铁磁材料的B-H-μ曲线.png"
    plt.savefig(outpath, dpi=150, bbox_inches='tight', facecolor='#ECECEC')
    plt.close()
    print(f"[OK] 图3 已保存: {outpath}")
    return outpath


def figure4_saturation_additional_energy():
    """图4：铁磁材料的饱和磁能 W_Hs 和附加磁能 W_Hf

    匹配原PDF风格：
    - 品红色 B-H 曲线
    - 仅 W_Hf（附加磁能）区域用粉色填充
    - W_Hs（饱和磁能）区域不填充
    - 无网格线、无公式框
    """
    H = np.linspace(0, 10, 500)
    H_s = 1.5    # 匹配参考图：饱和拐点在x≈15%
    H_x = 10.0
    B_s = 1.5

    # B-H 曲线
    B = np.zeros_like(H)
    mask_linear = H <= H_s
    mask_sat = H > H_s
    B[mask_linear] = (B_s / H_s) * H[mask_linear]
    B[mask_sat] = B_s * (1 - 0.12 * np.exp(-(H[mask_sat] - H_s) / 1.0))

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # === W_Hf 矩形（Rectangle patch，保证从B=0到B=B_s）===
    rect = Rectangle((H_s, 0), H_x - H_s, B_s,
                      linewidth=1.5, edgecolor=PINK_EDGE,
                      facecolor=PINK_FILL, alpha=W_HF_ALPHA, zorder=1)
    ax.add_patch(rect)

    # 图例手动构建
    legend_elements = [
        Patch(facecolor=PINK_FILL, alpha=W_HF_ALPHA, edgecolor=PINK_EDGE,
              label=r'$W_{Hf}$ (附加磁能)'),
        plt.Line2D([0], [0], color=PINK_CURVE, lw=2.5, label=r'$B-H$ 曲线')
    ]

    # W_Hs 不填充，只用虚线标注边界
    ax.axvline(x=H_s, color='#888888', linestyle='--', linewidth=1.2, alpha=0.7)

    # === B-H 曲线 — 品红色 ===
    ax.plot(H, B, color=PINK_CURVE, linewidth=2.5, zorder=5)

    # 饱和水平虚线
    ax.axhline(y=B_s, color='#999999', linestyle='--', linewidth=1.0, alpha=0.5)

    # 关键点标注
    ax.plot(H_s, B_s, 'o', color='#C2185B', markersize=8, zorder=6)
    ax.annotate(r'$(H_S, B_S)$', xy=(H_s, B_s), fontsize=11, fontweight='bold',
                xytext=(H_s + 0.6, B_s - 0.18), color='#C2185B',
                arrowprops=dict(arrowstyle='->', color='#C2185B', lw=1.2))

    ax.plot(H_x, B_s, 'o', color='#C2185B', markersize=8, zorder=6)
    ax.annotate(r'$(H_X, B_S)$', xy=(H_x, B_s), fontsize=11, fontweight='bold',
                xytext=(H_x + 0.2, B_s + 0.12), color='#C2185B',
                arrowprops=dict(arrowstyle='->', color='#C2185B', lw=1.2))

    # 轴上标注
    ax.annotate(r'$H_S$', xy=(H_s, -0.04), fontsize=12, fontweight='bold',
                ha='center', va='top', color='#555555')
    ax.annotate(r'$H_X$', xy=(H_x, -0.04), fontsize=12, fontweight='bold',
                ha='center', va='top', color='#555555')
    ax.annotate(r'$B_S$', xy=(-0.12, B_s), fontsize=12, fontweight='bold',
                va='center', color='#555555')

    # 区域标签
    ax.text(H_s / 2, B_s * 0.55, r'$W_{Hs}$' + '\n(饱和磁能=输入电能)',
            fontsize=10, ha='center', va='center', color='#555555')

    ax.text((H_s + H_x) / 2, B_s * 0.55,
            r'$W_{Hf}$' + '\n(附加磁能=暗能量转换)',
            fontsize=10, ha='center', va='center',
            color='#C2185B', fontweight='bold')

    ax.set_xlabel(r'$H$', fontsize=13)
    ax.set_ylabel(r'$B$', fontsize=13)
    ax.set_xlim(0, H_x * 1.06)
    ax.set_ylim(0, B_s * 1.25)
    ax.tick_params(labelsize=10)

    ax.set_title('图4  铁磁材料的饱和磁能 $W_{Hs}$ 和附加磁能 $W_{Hf}$',
                 fontsize=14, fontweight='bold', pad=12)

    ax.legend(handles=legend_elements, loc='upper left', fontsize=10,
              framealpha=0.85, edgecolor='#CCCCCC')

    plt.tight_layout()
    outpath = f"{OUTPUT_DIR}/图4 铁磁材料的饱和磁能WHs和附加磁能WHf.png"
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] 图4 已保存: {outpath}")
    return outpath


if __name__ == '__main__':
    print("=" * 60)
    print("暗能量COP公式 · 配套图表生成（匹配原PDF风格）")
    print("周治平《暗能量转换成为附加磁能的论证》2014")
    print("=" * 60)
    figure3_bh_mu_curve()
    figure4_saturation_additional_energy()
    print("\n[OK] 全部图表生成完毕")
