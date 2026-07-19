#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v4 — 蓝白阴阳格水滴分形（柔光混合版）

v3→v4 核心改进：
  1. ★ 棋盘格从硬覆盖改为柔光混合（alpha=0.35）— 关键！目标图是朦胧感
  2. 外部基底层：连续势能平滑着色（非纯色）→ 深蓝到中蓝的径向渐变
  3. 棋盘格作为纹理层以低alpha叠加在基底上
  4. 内部更蓝（降低白度），中心小亮点
  5. 金边增强：加宽+内白外橙双层+辉光扩散
  6. 新增：微弱环境光均匀提亮（模拟大气散射）
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import binary_dilation, gaussian_filter

# ============================================================
# 参数
# ============================================================
TIP = 4.0; BOTTOM = -4.0 / 3.0; HSPAN = 1.6242719100; MARGIN = 0.50
RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH = 2400
HEIGHT = int(WIDTH * (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN))

MAX_ITER = 300
BAILOUT_SQ = 128 ** 2

# ---- 极坐标棋盘参数 ----
N_ANGLE = 400              # 更密的角度分区
LOG_R_STEP = 0.032         # 更密的径向环带
CHESS_ALPHA = 0.35         # ★ 棋盘格混合透明度（低=更朦胧）

# ---- 配色（整体冷蓝系）----
BG_DEEP       = [0.010, 0.028, 0.11]      # 远场深藏青
EXT_BASE_FAR  = [0.04, 0.10, 0.28]         # 外部远场基底
EXT_BASE_NEAR = [0.12, 0.24, 0.52]         # 外部近场基底（靠近水滴）
TILE_LIGHT    = [0.52, 0.64, 0.88]         # 阳纹亮色（混合后变柔和）
TILE_DARK     = [0.00, 0.04, 0.18]         # 阴纹暗色

INT_CORE      = [0.70, 0.82, 0.96]         # 内核亮区（偏蓝白）
INT_MID       = [0.40, 0.58, 0.84]         # 中层天蓝
INT_EDGE      = [0.15, 0.30, 0.62]         # 边缘海蓝
GOLD_HOT      = [1.0, 0.90, 0.35]          # 金辉核心峰值
GOLD_WARM     = [0.95, 0.60, 0.10]          # 暖橙外侧
DEM_SCALE     = 22.0
AMBIENT_BOOST = 0.06                        # 全局环境光提升


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

    return {'ic': ic, 'trap': trap, 'z': z.copy(), 'dz': dz.copy(),
            'interior': ~alive, 'co': co}


# ============================================================
# 渲染器 v4 — 柔光混合
# ============================================================
def render(data, w, h):
    ic = data['ic']; trap = data['trap']
    fz = data['z']; fdz = data['dz']
    interior = data['interior']; ext = ~interior
    co = data['co']

    img = np.full((h, w, 3), BG_DEEP, dtype=np.float64)

    # ====== 层0: 外部基底 — 平滑连续势能着色 ======
    # 基于逃逸迭代次数的平滑梯度：远处暗→近处亮
    with np.errstate(invalid='ignore', divide='ignore'):
        ms = fz.real**2 + fz.imag**2 + 1e-30
        nc_f = np.minimum(ic, 30).astype(np.float64)
        # 连续势能 → 归一化到 [0,1]，远场=0，近场=1
        pot_raw = np.log(ms) / np.power(2.0, nc_f)
        pot_raw[interior] = 0
        pot_norm = pot_raw / (np.percentile(pot_raw[ext], 95) + 1e-12)
        pot_norm = np.clip(pot_norm, 0, 1)

        # 用幂函数让近处更亮
        ext_brightness = np.power(pot_norm, 0.5)

        for ch in range(3):
            base = EXT_BASE_FAR[ch] + (EXT_BASE_NEAR[ch] - EXT_BASE_FAR[ch]) * ext_brightness
            img[:, :, ch][ext] = np.clip(base[ext], 0, 1)

    # ====== 层1: 内部 — 轨道陷阱渐变 ======
    with np.errstate(invalid='ignore'):
        trap_s = np.maximum(trap, 1e-30)
        v_raw = (np.log(trap_s) * 0.45) % 1.0
        v_adj = np.power(v_raw, 0.55)  # 让核心亮点区域更大

        r_ch = np.select([v_adj < 0.45, v_adj >= 0.45],
            [INT_CORE[0] + (INT_MID[0]-INT_CORE[0])*(v_adj/0.45),
             INT_MID[0] + (INT_EDGE[0]-INT_MID[0])*((v_adj-0.45)/0.55)])
        g_ch = np.select([v_adj < 0.45, v_adj >= 0.45],
            [INT_CORE[1] + (INT_MID[1]-INT_CORE[1])*(v_adj/0.45),
             INT_MID[1] + (INT_EDGE[1]-INT_MID[1])*((v_adj-0.45)/0.55)])
        b_ch = np.select([v_adj < 0.45, v_adj >= 0.45],
            [INT_CORE[2] + (INT_MID[2]-INT_CORE[2])*(v_adj/0.45),
             INT_MID[2] + (INT_EDGE[2]-INT_MID[2])*((v_adj-0.45)/0.55)])
        img[interior] = np.stack([r_ch[interior], g_ch[interior], b_ch[interior]], axis=-1)

    # ====== 层2: 柔光棋盘格纹理叠加（仅外部）======
    yy, xx = np.ogrid[:h, :w]
    re_px = RE_MIN + (xx / (w - 1)) * (RE_MAX - RE_MIN)
    im_px = IM_MIN + (yy / (h - 1)) * (IM_MAX - IM_MIN)
    c_r = np.sqrt(re_px**2 + im_px**2)
    c_theta = (np.arctan2(im_px, re_px) + np.pi) / (2 * np.pi)
    c_log_r = np.log(c_r + 0.01)

    qi = np.floor(c_theta * N_ANGLE).astype(int)
    qj = np.floor(c_log_r / LOG_R_STEP).astype(int)
    chess_mask = ((qi % 2 == 0) != (qj % 2 == 0)) & ext

    # ★ 柔光混合：不是替换而是按 alpha 叠加
    alpha = CHESS_ALPHA
    for ch in range(3):
        tex = np.where(chess_mask, TILE_LIGHT[ch], TILE_DARK[ch])
        # img = img * (1-alpha) + tex * alpha
        blended = img[:, :, ch] * (1 - alpha) + tex * alpha
        img[:, :, ch][ext] = blended[ext]

    # ====== 层3: 增强金色边界辉光 ======
    abs_z = np.sqrt(fz.real**2 + fz.imag**2 + 1e-30)
    abs_dz = np.sqrt(fdz.real**2 + fdz.imag**2 + 1e-30)
    dem = np.log(abs_z**2 + 1e-30) * abs_z / (abs_dz + 1e-30)
    dem[~ext] = -1

    bd_h = interior[:, :-1] != interior[:, 1:]
    bd_v = interior[:-1, :] != interior[1:, :]
    edge = np.zeros((h, w), dtype=bool)
    edge[:, :-1] |= bd_h; edge[:-1, :] |= bd_v

    # 多层辉光
    glow_far = binary_dilation(edge, structure=np.ones((18, 18)))   # 远端扩散
    glow_mid = binary_dilation(edge, structure=np.ones((10, 10)))   # 中间层
    glow_near = binary_dilation(edge, structure=np.ones((4, 4)))    # 紧贴边缘

    dv = dem.copy(); dv[dv < 0] = 0
    dl = np.log1p(dv * DEM_SCALE)
    dn = dl / (dl.max() + 1e-12) if dl.max() > 0 else dl

    # 远端辉光（暖色调轻微提亮外部棋盘区）
    gf = glow_far & ext & ~glow_mid
    if gf.any():
        d = dn[gf]; falloff = np.power(d, 1.2)  # 快速衰减
        img[gf, 0] = np.clip(img[gf, 0] + 0.20 * falloff, 0, 1)
        img[gf, 1] = np.clip(img[gf, 1] + 0.12 * falloff, 0, 1)
        img[gf, 2] = np.clip(img[gf, 2] + 0.02 * falloff, 0, 1)

    # 中间层（暖橙色过渡带）
    gm_ext = glow_mid & ext & ~glow_near
    if gm_ext.any():
        d = dn[gm_ext]
        img[gm_ext] = np.stack([
            np.clip(GOLD_WARM[0] * (0.35 + 0.65 * d), 0, 1),
            np.clip(GOLD_WARM[1] * (0.25 + 0.75 * d), 0, 1),
            np.clip(GOLD_WARM[2] * (0.10 + 0.90 * d), 0, 0.35),
        ], axis=-1)

    # 紧贴边界的内侧（金色高亮）
    gn_int = glow_near & interior
    if gn_int.any():
        d = dn[gn_int]
        img[gn_int] = np.stack([
            np.clip(GOLD_HOT[0] * (0.55 + 0.45 * d), 0, 1),
            np.clip(GOLD_HOT[1] * (0.45 + 0.55 * d), 0, 1),
            np.clip(GOLD_HOT[2] * (0.15 + 0.85 * d), 0, 0.40),
        ], axis=-1)

    # ====== 层4: 全局环境光 ======
    img = np.clip(img + AMBIENT_BOOST, 0, 1)

    return np.rot90(img, k=3)


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"=== v4 柔光混合版 ===")
    print(f"尺寸: {WIDTH}x{HEIGHT} | 迭代:{MAX_ITER} | 棋盘alpha:{CHESS_ALPHA}")
    print(f"网格: {N_ANGLE}x{1/LOG_R_STEP:.0f}")

    data = compute(RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, MAX_ITER, BAILOUT_SQ)
    print(f"内部: {data['interior'].sum()} px ({100*data['interior'].mean():.1f}%)")

    img = render(data, WIDTH, HEIGHT)

    out_path = os.path.join(out_dir, '最美的蓝色水滴分形_v4.png')
    fw = 8; fh = fw * HEIGHT / WIDTH
    fig, ax = plt.subplots(figsize=(fw, fh), dpi=150)
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='bilinear', origin='lower')
    ax.axis('off'); plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor=tuple(BG_DEEP))
    plt.close()

    sz = os.path.getsize(out_path) / 1024 / 1024
    print(f"完成! {out_path} ({sz:.1f}MB)")
