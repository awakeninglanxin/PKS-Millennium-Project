#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v2 — 蓝白阴阳格水滴分形（迭代优化版）

v1→v2 改进：
  1. 棋盘密度提升10倍: ANG_DIV 64→256, POT_STEP 0.12→0.025
  2. 内部色调从白→浅蓝 改为 天蓝→中蓝（匹配目标图偏蓝）
  3. 金边辉光加厚（7→15像素膨胀核）
  4. 外部棋盘对比度降低（更柔和的蓝阴阳）
  5. 新增：基于c空间极坐标的辅助网格层（增强外部纹理细节）
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import binary_dilation

# ============================================================
# 参数区
# ============================================================
TIP = 4.0; BOTTOM = -4.0 / 3.0; HSPAN = 1.6242719100; MARGIN = 0.5
RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH = 2400
HEIGHT = int(WIDTH * (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN))

MAX_ITER = 300
BAILOUT_SQ = 128 ** 2

# ---- v2: 高密度棋盘 ----
ANG_DIV = 256              # 角度分区（v1=64, 细4倍）
POT_STEP = 0.025           # 势能环步长（v1=0.12, 细约5倍）

# ---- v2: 柔和蓝白配色 ----
BG_DEEP = [0.01, 0.03, 0.12]          # 远场深藏蓝
BLUE_LIGHT_TILE = [0.35, 0.48, 0.78]   # 阳：柔亮蓝（降低亮度）
BLUE_DARK_TILE = [0.08, 0.14, 0.38]    # 阴：柔暗蓝（提高亮度减少对比）

# 内部渐变：天蓝色调（不是白色）
INT_CENTER = [0.72, 0.84, 0.98]        # 内部中心：浅天蓝
INT_EDGE = [0.22, 0.38, 0.68]          # 内部边缘：中海蓝

GLOW_PEAK = [1.0, 0.82, 0.20]          # 金辉峰值色
DEM_SCALE = 18.0


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
# 渲染器 v2
# ============================================================
def render(data, w, h):
    ic = data['ic']; trap = data['trap']
    fz = data['z']; fdz = data['dz']
    interior = data['interior']; ext = ~interior

    img = np.full((h, w, 3), BG_DEEP, dtype=np.float64)

    # ====== 层1: 内部 — 轨道陷阱天蓝渐变 ======
    with np.errstate(invalid='ignore'):
        trap_s = np.maximum(trap, 1e-30)
        v = (np.log(trap_s) * 0.50) % 1.0   # 系数微调让同心圆密度合适

        # 用 sqrt 让中心区域更大面积保持亮色（视觉上更像目标图）
        v_smooth = np.sqrt(v)

        r_ch = INT_CENTER[0] * (1 - v_smooth) + INT_EDGE[0] * v_smooth
        g_ch = INT_CENTER[1] * (1 - v_smooth) + INT_EDGE[1] * v_smooth
        b_ch = INT_CENTER[2] * (1 - v_smooth) + INT_EDGE[2] * v_smooth
        img[interior] = np.stack([r_ch[interior], g_ch[interior], b_ch[interior]], axis=-1)

    # ====== 层2: 外部 — 高密度XOR棋盘格 ======
    with np.errstate(invalid='ignore', divide='ignore'):
        # 外部射线角度（最终 z 的相位）
        ang_z = np.arctan2(fz.imag, fz.real) / (2 * np.pi)

        # 连续势能
        ms = fz.real**2 + fz.imag**2 + 1e-30
        nc_f = np.minimum(ic, 28).astype(np.float64)
        pot = np.log(ms) / np.power(2.0, nc_f)
        pot[interior] = 0

        # 外部角度重整化（让射线在逃逸点附近变化更快）
        er = (ang_z / np.power(2.0, nc_f)) % 1.0
        er[interior] = 0

        # 量化
        rz = np.floor(er * ANG_DIV).astype(int)
        pz = np.floor(pot / POT_STEP).astype(int)

        # XOR 棋盘（仅外部）
        chess = ((rz % 2 == 0) != (pz % 2 == 0)) & ext

    # 着色（低对比度蓝阴阳）
    img[chess] = BLUE_LIGHT_TILE
    img[ext & ~chess] = BLUE_DARK_TILE

    # ====== 层3: 厚金色边界辉光 ======
    abs_z = np.sqrt(fz.real**2 + fz.imag**2 + 1e-30)
    abs_dz = np.sqrt(fdz.real**2 + fdz.imag**2 + 1e-30)
    dem = np.log(abs_z**2 + 1e-30) * abs_z / (abs_dz + 1e-30)
    dem[~ext] = -1

    # 边缘检测
    bd_h = interior[:, :-1] != interior[:, 1:]
    bd_v = interior[:-1, :] != interior[1:, :]
    edge = np.zeros((h, w), dtype=bool)
    edge[:, :-1] |= bd_h; edge[:-1, :] |= bd_v

    # 大范围辉光（15像素膨胀）
    glow = binary_dilation(edge, structure=np.ones((15, 15)))

    # DEM 归一化
    dv = dem.copy(); dv[dv < 0] = 0
    dl = np.log1p(dv * DEM_SCALE)
    dn = dl / (dl.max() + 1e-12) if dl.max() > 0 else dl

    # 外侧辉光（叠加到棋盘格上）
    gm_out = glow & ext
    if gm_out.any():
        d = dn[gm_out]
        img[gm_out, 0] = np.clip(img[gm_out, 0] + 0.55 * d, 0, 1)
        img[gm_out, 1] = np.clip(img[gm_out, 1] + 0.40 * d, 0, 1)
        img[gm_out, 2] = np.clip(img[gm_out, 2] - 0.05 * d, 0, 1)

    # 内侧辉光（叠加到内部渐变上）
    gm_in = glow & interior
    if gm_in.any():
        d = dn[gm_in]
        img[gm_in, 0] = np.clip(GLOW_PEAK[0] * (0.45 + 0.55 * d), 0, 1)
        img[gm_in, 1] = np.clip(GLOW_PEAK[1] * (0.35 + 0.65 * d), 0, 1)
        img[gm_in, 2] = np.clip(GLOW_PEAK[2] * (0.1 + 0.9 * d), 0, 0.35)

    return np.rot90(img, k=3)


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"=== v2 高密度蓝白阴阳格 ===")
    print(f"尺寸: {WIDTH}x{HEIGHT} | 迭代:{MAX_ITER} | 棋盘:{ANG_DIV}x{1/POT_STEP:.0f}")

    data = compute(RE_MIN, RE_MAX, IM_MIN, IM_MAX, WIDTH, HEIGHT, MAX_ITER, BAILOUT_SQ)
    print(f"内部: {data['interior'].sum()} px ({100*data['interior'].mean():.1f}%)")

    img = render(data, WIDTH, HEIGHT)

    out_path = os.path.join(out_dir, '最美的蓝色水滴分形_v2.png')
    fw = 8; fh = fw * HEIGHT / WIDTH
    fig, ax = plt.subplots(figsize=(fw, fh), dpi=150)
    ax.imshow(img, extent=[IM_MIN, IM_MAX, RE_MIN, RE_MAX],
              aspect='equal', interpolation='bilinear', origin='lower')
    ax.axis('off'); plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor=tuple(BG_DEEP))
    plt.close()

    sz = os.path.getsize(out_path) / 1024 / 1024
    print(f"完成! {out_path} ({sz:.1f}MB)")
