#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v5 — 射线分叉线条 (Ray Tracing Binary Decomposition Lines)

核心修正：
  1. bailout=100000 → z 值充分发散 → arg(z) 方向稳定 → 2ⁿ 分叉正确
  2. 不做角度 cap → 全精度 external_ray = arg(z)/(2π·2ⁿ) % 1
  3. 射线检测 = 模运算线条 (不是棋盘格填色)
  4. 等势线检测 = 模运算线条
  5. 两线叠加 → 树状分叉网格
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ===== 水滴精确视窗 =====
TIP    =  4.0
BOTTOM = -4.0 / 3.0
HSPAN  =  1.6242719100
MARGIN =  0.5

RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH  = 2400
ASPECT = (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN)
HEIGHT = int(WIDTH * ASPECT)

# ===== 线条参数 =====
MAX_ITER   = 300
BAILOUT    = 100000.0       # 大逃逸半径 (关键!)
BAILOUT_SQ = BAILOUT * BAILOUT

POT_SPACING = 0.12          # 等势线间距
RAY_COUNT   = 64            # 射线密度
LINE_THICK  = 0.025         # 线宽

def generate_outline(n_pts=6000):
    """解析轮廓: c(θ)=½e^(iθ)-¼e^(2iθ) → 1/c → rot90"""
    eps = 1e-10
    theta = np.linspace(eps, 2*np.pi - eps, n_pts)
    c = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    inv_c = 1.0 / c
    return -inv_c.imag, inv_c.real

def compute_fields(x_min, x_max, y_min, y_max, width, height, max_iter, bailout_sq):
    """返回 pot, ext_ray, interior"""
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    eps = 1e-12
    safe = np.abs(c_orig) > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = 1.0 / c_orig[safe]
    c_eff[~safe] = 1e6

    z = np.zeros_like(c_eff, dtype=np.complex128)
    escape = np.full(c_eff.shape, max_iter, dtype=np.float64)
    alive = np.ones(c_eff.shape, dtype=bool)
    z_final = np.zeros_like(c_eff, dtype=np.complex128)

    for i in range(max_iter):
        if not alive.any():
            break
        z[alive] = z[alive] ** 2 + c_eff[alive]
        z_final[alive] = z[alive].copy()
        div = (z.real**2 + z.imag**2) > bailout_sq
        escape[div & alive] = i
        alive &= ~div

    interior = escape >= max_iter

    # pot = ln(|z|²) / 2^n (与参考伪代码完全一致)
    mod_sq = z_final.real**2 + z_final.imag**2 + 1e-30
    pot = np.log(mod_sq) / (2.0 ** escape)
    pot[interior] = 0

    # external_ray = arg(z) / (2π·2^n) % 1 (不做 cap)
    angle = np.arctan2(z_final.imag, z_final.real) / (2.0 * np.pi)
    ext_ray = (angle / np.power(2.0, escape)) % 1.0
    ext_ray[interior] = 0

    return (
        np.rot90(pot, k=3),
        np.rot90(ext_ray, k=3),
        np.rot90(interior, k=3),
    )

if __name__ == "__main__":
    from scipy.ndimage import sobel, binary_dilation, binary_opening
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"逆M水滴 v5 — 射线分叉线条")
    print(f"  bailout={BAILOUT:.0f}, maxiter={MAX_ITER}")
    print(f"  pot_spacing={POT_SPACING}, ray_count={RAY_COUNT}")
    print(f"  计算中...")

    pot, ext_ray, interior = compute_fields(
        RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, MAX_ITER, BAILOUT_SQ
    )

    height, width = pot.shape
    ext = ~interior

    # ===== 等势线 (横向) =====
    pot_mod = np.abs((pot % POT_SPACING) - POT_SPACING / 2.0)
    is_pot = ext & (pot_mod < LINE_THICK)

    # ===== 射线 (纵向分叉) =====
    ray_mod = np.abs((ext_ray * RAY_COUNT) % 1.0 - 0.5)
    is_ray = ext & (ray_mod < LINE_THICK)

    # ===== Sobel 外壳 =====
    smooth_f = pot.astype(np.float64)
    smooth_f[interior] = 0.0
    from scipy.ndimage import sobel
    gx = sobel(smooth_f, axis=1); gy = sobel(smooth_f, axis=0)
    gm = np.sqrt(gx**2 + gy**2)
    if ext.sum() > 0:
        th = np.percentile(gm[ext], 98.5)
    else:
        th = 0
    shell = (gm > th) & ext
    shell = binary_opening(shell, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    shell = binary_dilation(shell, structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))

    # ===== 渲染 =====
    img = np.ones((height, width, 3))
    img[is_ray] = [0.0, 0.0, 0.0]    # 射线 = 黑
    img[is_pot] = [0.35, 0.35, 0.35] # 等势线 = 深灰
    both = is_ray & is_pot
    img[both] = [0.0, 0.0, 0.0]      # 交汇 = 黑
    img[shell] = [0.0, 0.0, 0.0]     # 外壳 = 黑
    img[interior] = [1.0, 1.0, 1.0]  # 内部 = 白

    print(f"  射线: {is_ray.sum():>8} px")
    print(f"  等势: {is_pot.sum():>8} px")
    print(f"  外壳: {shell.sum():>8} px")

    # ===== 保存 =====
    out_path = os.path.join(out_dir, "逆M_v5_射线分叉线条.png")
    fw = 8; fh = fw * (HEIGHT / WIDTH)
    fig, ax = plt.subplots(figsize=(fw, fh), dpi=100)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='nearest', origin='lower')
    ax.set_xlim(IM_MIN, IM_MAX); ax.set_ylim(RE_MIN, RE_MAX)
    # 叠加解析轮廓
    ox, oy = generate_outline()
    ax.plot(ox, oy, '-', color='#1a1a1a', linewidth=0.6, alpha=0.8, zorder=10)
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"已保存: {out_path}")
    print(f"\n关键修正: bailout={BAILOUT:.0f} + 无角度cap → 射线自动二分分叉 + 解析轮廓叠加")
