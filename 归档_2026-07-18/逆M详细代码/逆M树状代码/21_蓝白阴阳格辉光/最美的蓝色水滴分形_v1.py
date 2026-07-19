#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v6 — 蓝白阴阳格水滴分形（目标：复刻逆M蓝色.png效果）

算法融合：
  1. UF1b_壳线描边.py 的 XOR 棋盘格算法 → 仅作用于水滴外部(ext)
  2. 原理3_逆M水滴渲染算法 的轨道陷阱内部着色 → 水滴内部(interior)
  3. DEM距离估计金色边界辉光 → 水滴边界层

核心设计决策：
  - 棋盘格放在水滴外部（!interior），不在内部
  - 内部用 orbit-trap 同心圆纹理（白→浅蓝渐变）
  - 外部棋盘格用低对比度蓝白阴阳色（不刺眼）
  - 边界用厚实金橙色辉光过渡
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import binary_dilation, sobel

# ============================================================
# 参数区
# ============================================================
TIP = 4.0                    # 水滴尖端 Re 值
BOTTOM = -4.0 / 3.0          # 水滴底部 Re 值
HSPAN = 1.6242719100         # Im 半宽
MARGIN = 0.5                 # 视窗边距

RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH = 2400                 # 图像宽度
HEIGHT = int(WIDTH * (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN))

MAX_ITER = 256               # 最大迭代次数
BAILOUT = 128                # 逃逸半径（模长）
BAILOUT_SQ = BAILOUT ** 2

# ---- 棋盘格参数 ----
RAY_DIVISIONS = 64           # 外部射线角度分区数（UF1b原值）
POT_STEP = 0.12              # 连续势能环步长（UF1b原值）

# ---- 颜色参数 ----
BG_DEEP = [0.02, 0.05, 0.16]        # 最深海军蓝（远场背景）
BLUE_LIGHT_TILE = [0.45, 0.58, 0.85]   # 阳：中亮蓝（棋盘亮格）
BLUE_DARK_TILE = [0.12, 0.20, 0.50]    # 阴：中深蓝（棋盘暗格）
INT_CORE_WHITE = [0.95, 0.97, 1.0]     # 内部核心：近白色
INT_EDGE_BLUE = [0.35, 0.55, 0.82]     # 内部边缘：浅蓝
GLOW_GOLD_INNER = [1.0, 0.92, 0.35]    # 金辉内侧（靠近内部）
GLOW_GOLD_OUTER = [0.95, 0.55, 0.05]   # 金辉外侧（靠近外部）

DEM_SCALE = 12.0             # DEM辉光强度系数


# ============================================================
# 引擎：逆M水滴迭代 z² + 1/c
# ============================================================
def compute_inverse_m(x_min, x_max, y_min, y_max, w, h, max_iter, bailout_sq):
    """计算逆M集，返回完整场量用于分层着色"""
    x = np.linspace(x_min, x_max, w)
    y = np.linspace(y_min, y_max, h)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    # c_eff = 1/c （复反演），原点安全处理
    safe = np.abs(c_orig) > 1e-12
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = 1.0 / c_orig[safe]
    c_eff[~safe] = 1e6 + 0j

    z = np.zeros_like(c_eff, dtype=np.complex128)
    dz = np.zeros_like(c_eff, dtype=np.complex128)  # 导数（DEM用）

    # 场量初始化
    iter_count = np.full(c_eff.shape, max_iter, dtype=np.float64)
    trap = np.full(c_eff.shape, 1e30, dtype=np.float64)  # 轨道陷阱：min|z|²
    alive = np.ones(c_eff.shape, dtype=bool)

    for i in range(max_iter):
        if not alive.any():
            break
        idx = np.where(alive)
        za = z[idx].copy()
        ca = c_eff[idx].copy()
        dza = dz[idx].copy()

        # 迭代：z ← z² + c_eff
        dza = 2.0 * za * dza + 1.0  # dc/dz 的导数链式法则
        za = za * za + ca

        m2 = za.real * za.real + za.imag * za.imag
        trap[idx] = np.minimum(trap[idx], m2)

        z[idx] = za
        dz[idx] = dza

        escaped = m2 > bailout_sq
        iter_count[idx] = np.where(escaped, i, iter_count[idx])
        alive[idx] &= ~escaped

    interior = ~alive  # 未逃逸 = 水滴内部
    escaped_mask = alive  # 已逃逸 = 水滴外部

    # 最终 z 值（所有像素都有意义）
    final_z = z.copy()
    final_dz = dz.copy()

    return {
        'iter_count': iter_count,
        'trap': trap,
        'final_z': final_z,
        'final_dz': final_dz,
        'interior': interior,
        'c_orig': c_orig,
    }


# ============================================================
# 着色器：多层合成
# ============================================================
def render_blue_drop(data, w, h):
    """渲染蓝白阴阳格水滴分形"""

    ic = data['iter_count']
    trap = data['trap']
    fz = data['final_z']
    fdz = data['final_dz']
    interior = data['interior']
    co = data['c_orig']
    ext = ~interior

    img = np.full((h, w, 3), BG_DEEP, dtype=np.float64)

    # ====== 层1：水滴内部 — 轨道陷阱同心圆渐变 ======
    # v = log(trap) * coef % 1 → 映射到 白→浅蓝 径向渐变
    with np.errstate(invalid='ignore', divide='ignore'):
        trap_safe = np.maximum(trap, 1e-30)
        v_int = np.log(trap_safe) * 0.55  # 原理3中的陷阱系数
        v_int = v_int - np.floor(v_int)    # 取小数部分 [0,1)

        # 径向渐变：中心(v≈0)→白色，边缘(v→1)→浅蓝
        # 但 trap 在内部的变化可能不单调，直接用 v 映射
        r_chan = INT_CORE_WHITE[0] * (1 - v_int) + INT_EDGE_BLUE[0] * v_int
        g_chan = INT_CORE_WHITE[1] * (1 - v_int) + INT_EDGE_BLUE[1] * v_int
        b_chan = INT_CORE_WHITE[2] * (1 - v_int) + INT_EDGE_BLUE[2] * v_int

        img[interior, 0] = r_chan[interior]
        img[interior, 1] = g_chan[interior]
        img[interior, 2] = b_chan[interior]

    # ====== 层2：水滴外部 — XOR 棋盘格（蓝白阴阳）======
    # 基于 UF1b 算法：角度射线 × 势能环带 XOR
    with np.errstate(invalid='ignore', divide='ignore'):
        # 外部最终 z 的相位角 → 射线分区
        ang = np.arctan2(fz.imag, fz.real) / (2.0 * np.pi)
        # 连续势能（逃逸速度度量）
        ms = fz.real ** 2 + fz.imag ** 2 + 1e-30
        pot = np.log(ms) / (np.power(2.0, np.minimum(ic, 25).astype(np.float64)))
        pot[interior] = 0  # 内部不用

        # 量化为棋盘坐标
        nc = np.minimum(ic, 25).astype(np.float64)
        er = (ang / np.power(2.0, nc)) % 1.0
        er[interior] = 0

        # XOR 棋盘判定
        rz = np.floor(er * RAY_DIVISIONS).astype(int)
        pz = np.floor(pot / POT_STEP).astype(int)
        chess = ((rz % 2 == 0) != (pz % 2 == 0)) & ext  # ★ XOR 且仅在外部

    # 棋盘格着色（低对比度蓝白）
    img[chess] = BLUE_LIGHT_TILE
    dark_chess = ext & ~chess
    img[dark_chess] = BLUE_DARK_TILE

    # ====== 层3：金色DEM边界辉光 ======
    abs_z = np.sqrt(fz.real ** 2 + fz.imag ** 2 + 1e-30)
    abs_dz = np.sqrt(fdz.real ** 2 + fdz.imag ** 2 + 1e-30)

    # 距离估计：d = ln|z|² · |z|/|dz|
    dem = np.log(abs_z ** 2 + 1e-30) * abs_z / (abs_dz + 1e-30)
    dem[~ext] = -1  # 仅外部有效

    # 边缘检测（内/外交界）
    bd_h = np.zeros((h, w), dtype=bool)
    bd_v = np.zeros((h, w), dtype=bool)
    bd_h[:, :-1] = (interior[:, :-1] != interior[:, 1:])
    bd_v[:-1, :] = (interior[:-1, :] != interior[1:, :])
    boundary_edge = bd_h | bd_v

    # 扩展辉光区域
    glow_region = binary_dilation(boundary_edge, structure=np.ones((7, 7)))

    # DEM 归一化 → 辉光强度
    dem_valid = dem.copy()
    dem_valid[dem_valid < 0] = 0
    dem_log = np.log1p(dem_valid * DEM_SCALE)
    if dem_log.max() > 0:
        dem_norm = dem_log / (dem_log.max() + 1e-12)
    else:
        dem_norm = dem_log

    # 在边界区域叠加金色辉光
    glow_mask = glow_region & ext  # 外侧辉光
    glow_inner = glow_region & interior  # 内侧辉光

    if glow_mask.any():
        dn = dem_norm[glow_mask]
        img[glow_mask] = np.stack([
            np.clip(img[glow_mask, 0] + 0.50 * dn, 0, 1),
            np.clip(img[glow_mask, 1] + 0.35 * dn, 0, 1),
            np.clip(img[glow_mask, 2] - 0.10 * dn, 0, 1),
        ], axis=-1)

    if glow_inner.any():
        dn = dem_norm[glow_inner]
        img[glow_inner] = np.stack([
            np.clip(GLOW_GOLD_INNER[0] * (0.5 + 0.5 * dn), 0, 1),
            np.clip(GLOW_GOLD_INNER[1] * (0.4 + 0.6 * dn), 0, 1),
            np.clip(GLOW_GOLD_INNER[2] * dn, 0, 0.3),
        ], axis=-1)

    # ====== 旋转修正（与 UF1b 一致）======
    img = np.rot90(img, k=3)

    return img, dem_norm, boundary_edge


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_name = '最美的蓝色水滴分形_v1'

    print(f"=== UF21 v6 蓝白阴阳格水滴 ===")
    print(f"分辨率: {WIDTH}x{HEIGHT}, MAX_ITER={MAX_ITER}, BAILOUT={BAILOUT}")
    print(f"棋盘: RAY_DIV={RAY_DIVISIONS}, POT_STEP={POT_STEP}")

    # --- 计算 ---
    print("[1/3] 计算逆M集...")
    data = compute_inverse_m(RE_MIN, RE_MAX, IM_MIN, IM_MAX,
                             WIDTH, HEIGHT, MAX_ITER, BAILOUT_SQ)
    print(f"  内部像素: {data['interior'].sum()} ({100*data['interior'].mean():.1f}%)")

    # --- 渲染 ---
    print("[2/3] 渲染着色...")
    img, dem_norm, boundary = render_blue_drop(data, WIDTH, HEIGHT)

    # --- 保存 ---
    print("[3/3] 保存图像...")
    out_path = os.path.join(out_dir, f'{out_name}.png')
    fig_h = 8
    fig_w = fig_h * (HEIGHT / WIDTH)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='bilinear', origin='lower')
    ax.set_xlim(IM_MIN, IM_MAX)
    ax.set_ylim(RE_MIN, RE_MAX)
    ax.axis('off')

    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=200, bbox_inches='tight',
                facecolor=tuple(BG_DEEP))
    plt.close()

    file_size = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n完成! → {out_path} ({file_size:.1f}MB)")
    print(f"  分辨率: {WIDTH}x{HEIGHT}")
    print(f"  算法: 逆M(z²+1/c) + 外部XOR棋盘 + 轨道陷阱内部 + DEM金边")
