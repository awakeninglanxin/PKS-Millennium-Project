#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v3 — 蓝白阴阳格水滴分形（c空间极坐标网格版）

v2→v3 核心改进：
  1. ★ 棋盘格改用 c 空间极坐标 (|c|, arg(c)) 而非最终z相位 → 产生真正的极坐标瓷砖
  2. 棋盘密度: 角度 360 分区 + 对数半径 80 环带 → 细密瓷砖
  3. 内部渐变增强: 用幂函数让中心更亮更广
  4. 金边辉光: 双层结构(内金+外橙过渡)
  5. 整体色调统一为冷蓝系
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import binary_dilation, binary_erosion

# ============================================================
# 参数
# ============================================================
TIP = 4.0; BOTTOM = -4.0 / 3.0; HSPAN = 1.6242719100; MARGIN = 0.50
RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH = 2400
HEIGHT = int(WIDTH * (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN))

MAX_ITER = 280
BAILOUT_SQ = 128 ** 2

# ---- 极坐标棋盘参数 ----
N_ANGLE = 360              # 角度分区数（每度一格）
LOG_R_STEP = 0.038         # 对数半径环步长（控制径向瓷砖大小）

# ---- 配色方案（冷蓝色系）----
BG_DEEP       = [0.008, 0.025, 0.10]     # 最深藏青（远场）
TILE_LIGHT    = [0.32, 0.46, 0.76]        # 阳：柔亮蓝
TILE_DARK     = [0.06, 0.13, 0.36]        # 阴：柔暗蓝
INT_CORE      = [0.82, 0.90, 0.99]        # 内核：近白浅蓝
INT_MID       = [0.48, 0.68, 0.90]        # 中层：天蓝
INT_EDGE      = [0.18, 0.35, 0.65]        # 边缘：中海蓝
GOLD_INNER    = [1.0, 0.88, 0.28]         # 金辉内侧峰值
GOLD_OUTER    = [0.92, 0.52, 0.06]         # 橙辉外侧峰值
DEM_SCALE     = 20.0


# ============================================================
# 引擎
# ============================================================
def compute(x_min, x_max, y_min, y_max, w, h, max_iter, bail_sq):
    x = np.linspace(x_min, x_max, w)
    y = np.linspace(y_min, y_max, h)
    X, Y = np.meshgrid(x, y)
    co = X + 1j * Y

    safe = np.abs(co) > 1e-12
    ce = np.zeros_like(co, dtype=np.complex128)
    ce[safe] = 1.0 / co[safe]
    ce[~safe] = 1e6 + 0j

    z = np.zeros_like(ce, dtype=np.complex128)
    dz = np.zeros_like(ce, dtype=np.complex128)

    ic = np.full(ce.shape, max_iter, dtype=np.float64)
    trap = np.full(ce.shape, 1e30, dtype=np.float64)
    alive = np.ones(ce.shape, dtype=bool)

    for i in range(max_iter):
        if not alive.any():
            break
        idx = np.where(alive)
        za = z[idx]; ca = ce[idx]; dza = dz[idx]
        dza = 2.0 * za * dza + 1.0
        za = za * za + ca
        m2 = za.real**2 + za.imag**2
        trap[idx] = np.minimum(trap[idx], m2)
        z[idx] = za; dz[idx] = dza
        esc = m2 > bail_sq
        ic[idx] = np.where(esc, i, ic[idx])
        alive[idx] &= ~esc

    return {
        'ic': ic, 'trap': trap,
        'z': z.copy(), 'dz': dz.copy(),
        'interior': ~alive, 'co': co,
    }


# ============================================================
# 渲染器 v3 — c空间极坐标网格
# ============================================================
def render(data, w, h):
    ic = data['ic']; trap = data['trap']
    fz = data['z']; fdz = data['dz']
    interior = data['interior']; ext = ~interior
    co = data['co']

    img = np.full((h, w, 3), BG_DEEP, dtype=np.float64)

    # ====== 层1: 内部 — 平滑轨道陷阱渐变 ======
    with np.errstate(invalid='ignore'):
        trap_s = np.maximum(trap, 1e-30)

        # v ∈ [0,1): 0=中心(最亮), 1=边缘(较暗)
        v_raw = (np.log(trap_s) * 0.48) % 1.0

        # 幂函数调整分布：让中心大面积保持亮色
        v_adj = np.power(v_raw, 0.65)

        # 三段线性插值: core→mid→edge
        r_ch = np.select(
            [v_adj < 0.5, v_adj >= 0.5],
            [
                INT_CORE[0] + (INT_MID[0] - INT_CORE[0]) * (v_adj / 0.5),
                INT_MID[0] + (INT_EDGE[0] - INT_MID[0]) * ((v_adj - 0.5) / 0.5),
            ]
        )
        g_ch = np.select(
            [v_adj < 0.5, v_adj >= 0.5],
            [
                INT_CORE[1] + (INT_MID[1] - INT_CORE[1]) * (v_adj / 0.5),
                INT_MID[1] + (INT_EDGE[1] - INT_MID[1]) * ((v_adj - 0.5) / 0.5),
            ]
        )
        b_ch = np.select(
            [v_adj < 0.5, v_adj >= 0.5],
            [
                INT_CORE[2] + (INT_MID[2] - INT_CORE[2]) * (v_adj / 0.5),
                INT_MID[2] + (INT_EDGE[2] - INT_MID[2]) * ((v_adj - 0.5) / 0.5),
            ]
        )
        img[interior] = np.stack([r_ch[interior], g_ch[interior], b_ch[interior]], axis=-1)

    # ====== 层2: 外部 — c空间极坐标XOR棋盘格 ======
    # 使用像素的 c 值本身计算极坐标（非最终 z）
    yy, xx = np.ogrid[:h, :w]

    # c 在复平面上的坐标
    re_px = RE_MIN + (xx / (w - 1)) * (RE_MAX - RE_MIN)
    im_px = IM_MIN + (yy / (h - 1)) * (IM_MAX - IM_MIN)

    # c 的极坐标
    c_r = np.sqrt(re_px**2 + im_px**2)           # |c|
    c_theta = (np.arctan2(im_px, re_px) + np.pi) / (2 * np.pi)  # θ ∈ [0,1)
    c_log_r = np.log(c_r + 0.01)                   # log(|c|)

    # 量化为棋盘索引
    qi = np.floor(c_theta * N_ANGLE).astype(int)   # 角度索引
    qj = np.floor(c_log_r / LOG_R_STEP).astype(int)  # 径向索引

    # ★ XOR 棋盘：仅在外部区域生效
    chess = ((qi % 2 == 0) != (qj % 2 == 0)) & ext

    # 着色
    img[chess] = TILE_LIGHT
    img[ext & ~chess] = TILE_DARK

    # ====== 层3: 双层金色边界辉光 ======
    abs_z = np.sqrt(fz.real**2 + fz.imag**2 + 1e-30)
    abs_dz = np.sqrt(fdz.real**2 + fdz.imag**2 + 1e-30)
    dem = np.log(abs_z**2 + 1e-30) * abs_z / (abs_dz + 1e-30)
    dem[~ext] = -1

    # 边界
    bd_h = interior[:, :-1] != interior[:, 1:]
    bd_v = interior[:-1, :] != interior[1:, :]
    edge = np.zeros((h, w), dtype=bool)
    edge[:, :-1] |= bd_h; edge[:-1, :] |= bd_v

    # 辉光区域：外宽内窄
    glow_out = binary_dilation(edge, structure=np.ones((12, 12)))
    glow_in  = binary_dilation(edge, structure=np.ones((8, 8)))

    # DEM 归一化
    dv = dem.copy(); dv[dv < 0] = 0
    dl = np.log1p(dv * DEM_SCALE)
    dn = dl / (dl.max() + 1e-12) if dl.max() > 0 else dl

    # 外侧辉光（暖金色叠加到棋盘上）
    go = glow_out & ext & ~glow_in  # 仅外部远端辉光区
    if go.any():
        d = dn[go]; falloff = d ** 0.7
        img[go, 0] = np.clip(img[go, 0] + 0.55 * falloff, 0, 1)
        img[go, 1] = np.clip(img[go, 1] + 0.38 * falloff, 0, 1)
        img[go, 2] = np.clip(img[go, 2] - 0.02 * falloff, 0, 1)

    # 近边界的强金橙色（内外两侧）
    near_edge = glow_in
    ne_ext = near_edge & ext
    ne_int = near_edge & interior

    if ne_ext.any():
        d = dn[ne_ext]
        img[ne_ext] = np.stack([
            np.clip(GOLD_OUTER[0] * (0.40 + 0.60 * d), 0, 1),
            np.clip(GOLD_OUTER[1] * (0.30 + 0.70 * d), 0, 1),
            np.clip(GOLD_OUTER[2] * d, 0, 0.30),
        ], axis=-1)

    if ne_int.any():
        d = dn[ne_int]
        img[ne_int] = np.stack([
            np.clip(GOLD_INNER[0] * (0.50 + 0.50 * d), 0, 1),
            np.clip(GOLD_INNER[1] * (0.40 + 0.60 * d), 0, 1),
            np.clip(GOLD_INNER[2] * (0.08 + 0.92 * d), 0, 0.35),
        ], axis=-1)

    return np.rot90(img, k=3)


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"=== v3 c空间极坐标网格版 ===")
    print(f"尺寸: {WIDTH}x{HEIGHT} | 迭代:{MAX_ITER}")
    print(f"棋盘: {N_ANGLE}角度×{1/LOG_R_STEP:.0f}径向")

    data = compute(RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, MAX_ITER, BAILOUT_SQ)
    print(f"内部: {data['interior'].sum()} px ({100*data['interior'].mean():.1f}%)")

    img = render(data, WIDTH, HEIGHT)

    out_path = os.path.join(out_dir, '最美的蓝色水滴分形_v3.png')
    fw = 8; fh = fw * HEIGHT / WIDTH
    fig, ax = plt.subplots(figsize=(fw, fh), dpi=150)
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='bilinear', origin='lower')
    ax.axis('off'); plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor=tuple(BG_DEEP))
    plt.close()

    sz = os.path.getsize(out_path) / 1024 / 1024
    print(f"完成! {out_path} ({sz:.1f}MB)")
