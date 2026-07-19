#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v4 — 二分辐角棋盘格 (Binary Decomposition XOR)

算法核心：
  1. ray_zone = floor(external_ray × ray_divisions)  → 奇偶 → 左右中分
  2. pot_zone = floor(pot / pot_step)                  → 奇偶 → 前后竹节
  3. XOR: is_ray_even == is_pot_even → 深色, 否则浅色
  4. pot < fire_thresh → 橙金火焰过渡 (仿逆M阴阳adam的金色边缘)
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

# ===== 棋盘格参数 =====
RAY_DIVISIONS = 64      # 纵向射线分区数 (越大越细密)
POT_STEP      = 0.12    # 横向等势区间距
FIRE_THRESH   = 0.06    # 火焰过渡阈值 (pot < 此值 → 橙金渐变)
MAX_ITER      = 300
BAILOUT       = 128

def compute_binary_decomp(x_min, x_max, y_min, y_max, width, height,
                           max_iter, bailout):
    """
    返回 pot(连续势能) + ext_ray(外部角度) + interior_mask
    """
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    eps = 1e-12
    abs_c = np.abs(c_orig)
    safe = abs_c > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = 1.0 / c_orig[safe]
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

    # --- 连续势能: pot = ln(|z|²) / 2^n ---
    mod_z_sq = z_final.real**2 + z_final.imag**2 + 1e-30
    pot = np.log(mod_z_sq) / (2.0 ** escape)
    pot[interior] = 0

    # --- 外部角度: θ = arg(z) / (2π·2^n) mod 1 ---
    n_cap = np.minimum(escape, 25).astype(np.float64)
    angle = np.arctan2(z_final.imag, z_final.real) / (2.0 * np.pi)
    ext_ray = (angle / np.power(2.0, n_cap)) % 1.0
    ext_ray[interior] = 0

    # rot90 → 尖朝上
    return (
        np.rot90(pot, k=3),
        np.rot90(ext_ray, k=3),
        np.rot90(interior, k=3),
    )

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"逆M水滴 v4 — 二分辐角棋盘格")
    print(f"  视口: Re[{RE_MIN:.3f},{RE_MAX:.3f}] Im[{IM_MIN:.3f},{IM_MAX:.3f}]")
    print(f"  网格: {WIDTH}×{HEIGHT}, maxiter={MAX_ITER}")
    print(f"  ray_divisions={RAY_DIVISIONS}, pot_step={POT_STEP}")
    print(f"  计算中...")

    pot, ext_ray, interior = compute_binary_decomp(
        RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, MAX_ITER, BAILOUT
    )

    height, width = pot.shape
    ext = ~interior

    # ===== 1. 射线分区 (左右中分) =====
    ray_zone = np.floor(ext_ray * RAY_DIVISIONS).astype(int)
    is_ray_even = (ray_zone % 2 == 0)

    # ===== 2. 等势线分区 (前后竹节) =====
    pot_zone = np.floor(pot / POT_STEP).astype(int)
    is_pot_even = (pot_zone % 2 == 0)

    # ===== 3. XOR 棋盘格 =====
    chessboard = (is_ray_even == is_pot_even) & ext  # True → 深色, False → 浅色

    # ===== 4. 渐变色 =====
    # 用 pot_zone 的深度产生层次感
    img = np.zeros((height, width, 3))

    # 深色区: 深蓝灰调
    depth_dark = np.clip(0.08 + 0.015 * (pot_zone[ext] % 12), 0.04, 0.35)
    img_dark_r = depth_dark * 0.6
    img_dark_g = depth_dark * 0.7
    img_dark_b = depth_dark * 0.95

    # 浅色区: 暖灰白
    depth_light = np.clip(0.45 + 0.02 * (pot_zone[ext] % 10), 0.30, 0.78)
    img_light_r = depth_light * 0.92
    img_light_g = depth_light * 0.88
    img_light_b = depth_light * 0.82

    # 写入外部像素
    cb = chessboard[ext]
    img_flat = img.reshape(-1, 3)
    ext_flat = ext.ravel()

    r = np.zeros(ext.sum()); g = np.zeros(ext.sum()); b = np.zeros(ext.sum())
    r[cb] = img_dark_r[cb];   g[cb] = img_dark_g[cb];   b[cb] = img_dark_b[cb]
    r[~cb] = img_light_r[~cb]; g[~cb] = img_light_g[~cb]; b[~cb] = img_light_b[~cb]

    img_flat[ext_flat, 0] = r
    img_flat[ext_flat, 1] = g
    img_flat[ext_flat, 2] = b

    # ===== 5. 火焰过渡 (pot < FIRE_THRESH → 橙金渐变) =====
    fire = ext & (pot < FIRE_THRESH)
    if fire.sum() > 0:
        t = (FIRE_THRESH - pot[fire]) / FIRE_THRESH  # 0→1 (越近边界越金)
        fire_r = 0.90 + 0.05 * t
        fire_g = 0.35 + 0.45 * t - 0.15 * (1-t)
        fire_b = 0.08 + 0.12 * (1-t)

        cur_r = img_flat[fire.ravel(), 0]
        cur_g = img_flat[fire.ravel(), 1]
        cur_b = img_flat[fire.ravel(), 2]

        blend = t
        img_flat[fire.ravel(), 0] = (1-blend)*cur_r + blend*fire_r
        img_flat[fire.ravel(), 1] = (1-blend)*cur_g + blend*fire_g
        img_flat[fire.ravel(), 2] = (1-blend)*cur_b + blend*fire_b

    img = img_flat.reshape(height, width, 3)

    # 内部 = 纯黑
    img[interior] = [0, 0, 0]

    # ===== 保存 =====
    n_cb = chessboard.sum()
    n_fire = fire.sum()
    print(f"  深色格: {n_cb} px ({100*n_cb/ext.sum():.1f}% of ext)")
    print(f"  火焰区: {n_fire} px")

    out_path = os.path.join(out_dir, "逆M_v4_二分棋盘格.png")
    fig_w = 8; fig_h = fig_w * (HEIGHT / WIDTH)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='bilinear', origin='lower')
    ax.set_xlim(IM_MIN, IM_MAX)
    ax.set_ylim(RE_MIN, RE_MAX)
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"已保存: {out_path}")
    print(f"\n算法: ray_zone⊕pot_zone XOR → 棋盘格 + pot<{FIRE_THRESH} → 橙金火焰")
