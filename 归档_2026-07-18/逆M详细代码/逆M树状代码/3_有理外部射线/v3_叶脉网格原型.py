#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v3 — 树状连线 / 叶脉网格

基于外部射线(External Rays) + 等势线(Equipotential Lines)的双曲坐标网格。
原理：
  1. pot = smooth = n - log₂(log₂(|z|))   —— 连续等势场，modulo → 横向脉络
  2. ray = arg(z) / (2π·2^n)              —— 外部角度，modulo → 纵向经脉
  3. 1/c 反演 → 外部世界翻转进水滴内部 → 叶脉向心汇聚
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ===== 水滴边框 =====
TIP    =  4.0
BOTTOM = -4.0 / 3.0
HSPAN  =  1.6242719100
MARGIN =  0.5

RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH  = 2400
ASPECT = (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN)
HEIGHT = int(WIDTH * ASPECT)

# ===== 网格线参数 =====
POT_SPACING = 1.0       # 等势线间距 (单位 smooth 每格)
RAY_COUNT   = 128       # 射线总数 (越高越密)
LINE_THICK  = 0.025     # 线宽阈值 (越小线越细)
RAY_BIT_CAP = 20        # 射线角度计算中 n 的上限 (数值稳定)

def generate_outline(n_pts=6000):
    eps = 1e-10
    theta = np.linspace(eps, 2*np.pi - eps, n_pts)
    c = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    inv_c = 1.0 / c
    return -inv_c.imag, inv_c.real

def compute_fractal_with_rays(alpha, x_min, x_max, y_min, y_max,
                                width, height, max_iter, bailout):
    """返回 smooth(等势场) + ray_angle(射线角度场) + interior"""
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    eps = 1e-12; abs_c = np.abs(c_orig)
    safe = abs_c > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = (abs_c[safe] ** alpha) * np.exp(1j * alpha * np.angle(c_orig[safe]))
    c_eff[~safe] = 1e6 + 0j

    z = np.zeros_like(c_eff, dtype=np.complex128)
    escape = np.full(c_eff.shape, max_iter, dtype=np.float64)
    alive = np.ones(c_eff.shape, dtype=bool)
    z_final = np.zeros_like(c_eff, dtype=np.complex128)

    for i in range(max_iter):
        if not alive.any():
            break
        z[alive] = z[alive] ** 2 + c_eff[alive]
        z_final[alive] = z[alive].copy()
        div = np.abs(z) > bailout
        escape[div & alive] = i
        alive &= ~div

    interior = escape >= max_iter

    # --- 等势场 (连续势) ---
    az = np.abs(z_final) + 1e-12
    smooth = escape - np.log2(np.maximum(np.log2(az), 1e-12))
    smooth[interior] = 0

    # --- 射线角度场 ---
    n_safe = np.minimum(escape, RAY_BIT_CAP).astype(np.float64)
    arg_z = np.arctan2(z_final.imag, z_final.real)
    ray_angle = (arg_z / (2.0 * np.pi * np.power(2.0, n_safe) + 1e-30)) % 1.0
    ray_angle[interior] = 0

    # rot90 → 尖朝上
    return (
        np.rot90(smooth, k=3),
        np.rot90(ray_angle, k=3),
        np.rot90(interior, k=3),
    )

if __name__ == "__main__":
    from scipy.ndimage import sobel, binary_dilation, binary_opening
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"逆M水滴 v3 — 树状连线 / 叶脉网格")
    print(f"  视口: Re[{RE_MIN:.3f},{RE_MAX:.3f}] Im[{IM_MIN:.3f},{IM_MAX:.3f}]")
    print(f"  网格: {WIDTH}×{HEIGHT}")
    print(f"  pot_spacing={POT_SPACING}, ray_count={RAY_COUNT}")
    print(f"  计算中...")

    smooth, ray_angle, interior = compute_fractal_with_rays(
        -1.0, RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, 250, 128
    )

    height, width = smooth.shape
    ext = ~interior

    # ===== 等势线 grid 检测 =====
    pot_mod = np.abs((smooth % POT_SPACING) - POT_SPACING / 2.0)
    is_pot_line = ext & (pot_mod < LINE_THICK)

    # ===== 射线 grid 检测 =====
    ray_mod = np.abs((ray_angle * RAY_COUNT) % 1.0 - 0.5)
    is_ray_line = ext & (ray_mod < LINE_THICK)

    # ===== Sobel 壳层黑线（不参与叶脉，但保留外壳）=====
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

    # ===== 渲染 =====
    img = np.ones((height, width, 3))

    # 等势线：深灰
    img[is_pot_line] = [0.25, 0.25, 0.25]

    # 射线：黑
    img[is_ray_line] = [0.0, 0.0, 0.0]

    # 两线交汇处 → 纯黑加粗
    both = is_pot_line & is_ray_line
    img[both] = [0.0, 0.0, 0.0]

    # 外壳 Sobel 黑线覆盖
    img[shell_thick] = [0.0, 0.0, 0.0]

    # 内部纯白
    img[interior] = [1.0, 1.0, 1.0]

    # ===== 统计 =====
    n_pot = is_pot_line.sum()
    n_ray = is_ray_line.sum()
    print(f"  等势线: {n_pot} px ({100*n_pot/(height*width):.2f}%)")
    print(f"  射线:   {n_ray} px ({100*n_ray/(height*width):.2f}%)")
    print(f"  外壳:   {shell_sobel.sum()} px")

    # ===== 保存 =====
    out_path = os.path.join(out_dir, "逆M_v3_树状连线叶脉网格.png")
    fig_w = 8; fig_h = fig_w * (HEIGHT / WIDTH)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='nearest', origin='lower')

    ox, oy = generate_outline()
    ax.plot(ox, oy, '-', color='#111111', linewidth=0.5, alpha=0.7, zorder=10)

    ax.set_xlim(IM_MIN, IM_MAX)
    ax.set_ylim(RE_MIN, RE_MAX)
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"已保存: {out_path}")
    print(f"\n数学说明:")
    print(f"  等势: pot = n - log₂(log₂(|z|))  mod {POT_SPACING} → 横向脉络")
    print(f"  射线: θ = arg(z) / (2π·2^min(n,{RAY_BIT_CAP}))  mod 1/{RAY_COUNT} → 纵向经脉")
    print(f"  1/c反演 → 外部世界翻转进水滴 → 叶脉向心汇聚於中心线")
