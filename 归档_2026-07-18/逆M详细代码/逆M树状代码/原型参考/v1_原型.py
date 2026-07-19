#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v1 — 精确视窗版（水滴边框 +0.5 外扩）

视窗（rot90后坐标系，尖朝上）：
  尖端 y = +4.000    底部 y = -4/3 ≈ -1.333
  右端 x = +1.624    左端 x = -1.624
  ↓ 各边外扩 +0.5 ↓
  Re(c) ∈ [-1.833, 4.500]    Im(c) ∈ [-2.124, 2.124]
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ===== 水滴边框精确值 =====
TIP      =  4.0          # 尖端
BOTTOM   = -4.0 / 3.0    # 底部 = -4/3
HSPAN    =  1.6242719100 # 水平半跨距
MARGIN   =  0.5          # 外扩留白

# 采样区间 (rot90前: x=Re, y=Im)
RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN    # 约 [-1.833, 4.500]
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN  # 约 [-2.124, 2.124]

# 网格: 宽度固定, 高度按比例
WIDTH  = 2400
ASPECT = (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN)    # ≈ 1.49
HEIGHT = int(WIDTH * ASPECT)
SUB_FACTOR = 12

def compute_fractal(alpha, x_min, x_max, y_min, y_max, width, height, max_iter, bailout):
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    eps = 1e-12
    abs_c = np.abs(c_orig)
    safe = abs_c > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = (abs_c[safe] ** alpha) * np.exp(1j * alpha * np.angle(c_orig[safe]))
    c_eff[~safe] = 1e6 + 0j

    z = np.zeros_like(c_eff, dtype=np.complex128)
    escape = np.full(c_eff.shape, max_iter, dtype=np.float64)
    alive = np.ones(c_eff.shape, dtype=bool)

    for i in range(max_iter):
        if not alive.any():
            break
        z[alive] = z[alive] ** 2 + c_eff[alive]
        div = np.abs(z) > bailout
        escape[div & alive] = i
        alive &= ~div

    az = np.abs(z) + 1e-12
    log_zn = np.log2(np.maximum(np.log2(az), 1e-12))
    smooth = escape - log_zn
    interior = escape >= max_iter
    smooth[interior] = 0

    return np.rot90(smooth, k=3), np.rot90(interior, k=3)

if __name__ == "__main__":
    from scipy.ndimage import sobel, binary_dilation, binary_opening

    out_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"逆M水滴精确视窗 (外扩+{MARGIN})")
    print(f"  Re(c) = [{RE_MIN:.3f}, {RE_MAX:.3f}]")
    print(f"  Im(c) = [{IM_MIN:.3f}, {IM_MAX:.3f}]")
    print(f"  网格: {WIDTH}×{HEIGHT}, 纵横比={ASPECT:.3f}")
    print(f"  子像素因子: {SUB_FACTOR}")
    print(f"  计算中...")
    
    smooth, interior = compute_fractal(-1.0, RE_MIN, RE_MAX, IM_MIN, IM_MAX,
                                        WIDTH, HEIGHT, 250, 128)

    height, width = smooth.shape
    img = np.ones((height, width, 3))
    ext = ~interior

    # ===== 1. Sobel 外壳主干 =====
    smooth_f = smooth.astype(np.float64)
    smooth_f[interior] = 0.0
    gx = sobel(smooth_f, axis=1)
    gy = sobel(smooth_f, axis=0)
    grad_mag = np.sqrt(gx**2 + gy**2)

    if ext.sum() > 0:
        thresh = np.percentile(grad_mag[ext], 98.5)
    else:
        thresh = 0
    shell_sobel = (grad_mag > thresh) & ext
    shell_sobel = binary_opening(shell_sobel, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    shell_thick = binary_dilation(shell_sobel, structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))

    # ===== 2. 子像素同心环 =====
    ET_scaled = np.round(smooth * SUB_FACTOR).astype(np.float64)
    dx = np.abs(np.diff(ET_scaled, axis=1, prepend=ET_scaled[:, 0:1]))
    dy = np.abs(np.diff(ET_scaled, axis=0, prepend=ET_scaled[0:1, :]))
    jump_edges = ((dx >= 0.5) | (dy >= 0.5)) & ext & ~shell_thick

    ET_on_jumps = ET_scaled[jump_edges].astype(int)
    phase = ET_on_jumps % 5
    grays = np.array([0.00, 0.20, 0.40, 0.60, 0.82])
    img[jump_edges] = np.column_stack([grays[phase]]*3)

    # ===== 3. 外壳 = 纯黑 =====
    img[shell_thick] = [0, 0, 0]

    # ===== 4. 统计 =====
    total_rings = ET_on_jumps.max() - ET_on_jumps.min()
    counts = [((ET_on_jumps % 5) == i).sum() for i in range(5)]
    print(f"  外壳: {shell_sobel.sum()} px")
    print(f"  跳边: {jump_edges.sum()} px, ~{total_rings}层")
    for i in range(5):
        print(f"    色{i}({grays[i]:.2f}): {counts[i]:>7} px")

    # ===== 5. 外围枝杈 =====
    prev = shell_sobel.copy()
    for level in range(1, 3):
        dilated = binary_dilation(prev, structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))
        new_br = dilated & ~shell_sobel & ~jump_edges
        gray = 0.07 * level
        if level >= 2:
            new_br = binary_opening(new_br, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
        img[new_br] = gray
        prev = dilated

    img[interior] = [1, 1, 1]

    # ===== 保存 =====
    out_path = os.path.join(out_dir, "逆M_v1_精确视窗_外扩0.5.png")
    fig_w = 8
    fig_h = fig_w * (HEIGHT / WIDTH)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    # rot90后: x=原Im轴, y=原Re轴
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='nearest', origin='lower')
    ax.set_xlim(IM_MIN, IM_MAX)
    ax.set_ylim(RE_MIN, RE_MAX)
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"\n已保存: {out_path}")
    print(f"视口: Re[{RE_MIN:.3f},{RE_MAX:.3f}] Im[{IM_MIN:.3f},{IM_MAX:.3f}]")
