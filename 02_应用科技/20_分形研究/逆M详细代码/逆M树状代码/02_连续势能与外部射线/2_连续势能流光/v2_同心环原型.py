#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v2 — 同心环 + 解析轮廓线叠加

完全自包含，不依赖任何外部 CSV 文件。
轮廓由 c(θ)=½e^(iθ)-¼e^(2iθ) → 1/c → rot90 直接解析生成。
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ===== 水滴边框精确值 =====
TIP      =  4.0
BOTTOM   = -4.0 / 3.0
HSPAN    =  1.6242719100
MARGIN   =  0.5

RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH  = 2400
ASPECT = (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN)
HEIGHT = int(WIDTH * ASPECT)
SUB_FACTOR = 12

def generate_outline(n_pts=6000):
    """解析生成轮廓: c(θ)=½e^(iθ)-¼e^(2iθ) → 1/c → rot90 → 封闭曲线"""
    eps = 1e-10
    theta = np.linspace(eps, 2*np.pi - eps, n_pts)
    c = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    inv_c = 1.0 / c
    # rot90: x' = -Im(c), y' = Re(c)
    ox, oy = -inv_c.imag, inv_c.real
    return ox, oy

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

    print(f"逆M水滴 v2 — 同心环 + 解析轮廓 (自包含)")
    print(f"  视口: Re[{RE_MIN:.3f},{RE_MAX:.3f}] Im[{IM_MIN:.3f},{IM_MAX:.3f}]")
    print(f"  网格: {WIDTH}×{HEIGHT}, factor={SUB_FACTOR}")
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

    # ===== 4. 外围枝杈 =====
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
    out_path = os.path.join(out_dir, "逆M_v2_同心环+解析轮廓.png")
    fig_w = 8
    fig_h = fig_w * (HEIGHT / WIDTH)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='nearest', origin='lower')

    # ===== 叠加解析轮廓线 (自包含, 不需要 CSV) =====
    ox, oy = generate_outline()
    ax.plot(ox, oy, '-', color='#1a1a1a', linewidth=0.6, alpha=0.85, zorder=10)

    ax.set_xlim(IM_MIN, IM_MAX)
    ax.set_ylim(RE_MIN, RE_MAX)
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    total_rings = ET_on_jumps.max() - ET_on_jumps.min()
    print(f"  跳边: {jump_edges.sum()} px, ~{total_rings}层")
    print(f"  轮廓: {len(ox)} 顶点 (解析生成, 无外部文件依赖)")
    print(f"已保存: {out_path}")
