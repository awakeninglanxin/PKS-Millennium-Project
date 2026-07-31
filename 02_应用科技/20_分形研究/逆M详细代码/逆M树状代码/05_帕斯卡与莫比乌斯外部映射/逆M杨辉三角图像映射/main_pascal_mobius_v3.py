#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 帕斯卡三角 Mobius映射 v3 — 精细调参 + CJK字体修复

算法链路 (来自元宝5层拆解 → 实践):
  像素w → Mobius f_M(w) → 三角格(n,k) → Lucas (k&~n)==0 → 金/藏青双色
  DEM金边 + 逃逸势能层次叠加

Mobius 主方案: f(z)=z/(z-2)  — 将点2映射到∞, 产生极向拉伸
  使复平面在z=2附近区域展开, 帕斯卡三角纹理随之弯曲变形
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# CJK字体 (铁律24)
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

od = os.path.dirname(os.path.abspath(__file__))

# ==================== 视窗 ====================
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B - MARGIN, TIP + MARGIN
I0, I1 = -HSP - MARGIN, HSP + MARGIN
W = 2400
H = int(W * (R1 - R0) / (I1 - I0))
MI = 300; BL = 50
print(f"视窗: {W}x{H}  MI={MI}  BL={BL}")

# ==================== 复数网格 ====================
x = np.linspace(R0, R1, W)
y = np.linspace(I0, I1, H)
X, Y = np.meshgrid(x, y)
w_grid = X + 1j * Y

eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0 / w_grid[sf]
ce[~sf] = 1e6

# ==================== 迭代 ====================
z = np.zeros_like(ce); dz = np.ones_like(ce)
alive = np.ones(ce.shape, bool)
esc_iter = np.zeros(ce.shape, int)

for i in range(MI):
    if not alive.any(): break
    idx = np.where(alive)
    za = z[idx].copy(); ca = ce[idx].copy(); dza = dz[idx].copy()
    dza = 2 * za * dza + 1
    za = za * za + ca
    z[idx] = za; dz[idx] = dza
    esc = np.zeros(ce.shape, bool)
    esc[idx] = (za.real**2 + za.imag**2 > BL**2)
    esc_iter[esc] = i + 1
    alive &= ~esc

interior = ~alive; ext = alive
print(f"逃逸: {ext.sum()}/{W*H}  ({ext.sum()/(W*H)*100:.1f}%)")

# ==================== Mobius 与 帕斯卡 ====================
def mobius(z, a, b, c, d):
    num = a*z + b; den = c*z + d
    safe = np.abs(den) > 1e-12
    r = np.full(z.shape, np.nan + 1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe] / den[safe]
    return r

def pascal_fill(re_vals, im_vals, scale, ox=0, oy=0):
    """帕斯卡三角 mod 2 填充判定 → bool array"""
    sr3 = np.sqrt(3)
    b = 2*(im_vals + oy) / (scale * sr3)
    a = (re_vals + ox) / scale - b/2
    n = np.round(a + b).astype(np.int64)
    k = np.round(b).astype(np.int64)
    valid = (n >= 0) & (k >= 0) & (k <= n)
    fill = valid & ((k & ~n) == 0)
    return fill, n, k

# --- 方案: z/(z-2), 调参让三角更密集 ---
A, B_M, C_M, D_M = 1+0j, 0+0j, 1+0j, -2+0j   # f(z)=z/(z-2)
SCALE = 0.12      # 更小的scale=更大的三角=更多填充
OX, OY = 0.3, 0.2  # 偏移使有效区域居中

w_ext = w_grid[ext]
zm = mobius(w_ext, A, B_M, C_M, D_M)
valid_m = ~np.isnan(zm.real)
zm_v = zm[valid_m]

pascal, nvals, kvals = pascal_fill(zm_v.real, zm_v.imag, SCALE, OX, OY)
n_range = (int(nvals.min()), int(nvals.max()))
k_range = (int(kvals.min()), int(kvals.max()))
pct = pascal.sum()/len(pascal)*100 if len(pascal)>0 else 0
print(f"Mobius z/(z-2): scale={SCALE}  n{n_range} k{k_range}  "
      f"fill={pascal.sum()}/{len(pascal)} ({pct:.1f}%)")

# ==================== 着色 ====================
img = np.zeros((H, W, 3))

# 水滴内部: 深蓝 (带微弱渐变拉开层次)
int_mask = interior
int_grad = (np.arange(H)[:, None] / H * 0.08 +
            np.arange(W)[None, :] / W * 0.05)
img[int_mask] = np.stack([
    np.full(int_mask.sum(), 0.02),
    np.full(int_mask.sum(), 0.06),
    0.15 + int_grad[int_mask]
], axis=-1)

# 逃逸区: 帕斯卡纹理
fill_color = np.array([0.92, 0.68, 0.10])   # 暖金
empty_color = np.array([0.04, 0.06, 0.20])   # 深藏青

ext_idx = np.where(ext)
# 构建填充标记
pascal_full = np.zeros(ext.sum(), dtype=bool)
pascal_full[valid_m] = pascal
pascal_full[~valid_m] = False  # Mobius奇点→空白

for i, (py, px) in enumerate(zip(ext_idx[0], ext_idx[1])):
    img[py, px] = fill_color if pascal_full[i] else empty_color

# ==================== DEM金边 ====================
abs_z = np.abs(z); abs_dz = np.abs(dz) + 1e-12
dem = np.zeros_like(w_grid, dtype=np.float64)
dem[ext] = abs_z[ext] * np.log(abs_z[ext] + 1e-12) / abs_dz[ext]
dem_max = np.percentile(dem[ext], 95) if ext.any() else 1.0
dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)
edge_dark = np.clip(1.0 - np.exp(-dem_norm * 2.8), 0, 1)
edge_glow = np.exp(-dem_norm * 12)
img *= edge_dark[..., None]
img += edge_glow[..., None] * 0.38

# ==================== 逃逸势能层次 ====================
nu = esc_iter.astype(np.float64)
nu_max = nu[ext].max() or 1.0
nu_norm = np.clip(nu / nu_max, 0, 1)
# 靠近边界(nu小)微亮, 远端稍暗
brightness = 0.80 + 0.20 * (1.0 - nu_norm[ext])
img[ext] *= brightness[:, None]
img = np.clip(img, 0, 1)

# ==================== 输出 ====================
out_png = os.path.join(od, 'UF22_帕斯卡Mobius_最终版.png')

img_rot = np.rot90(img, k=1)
aspect = img_rot.shape[1] / img_rot.shape[0]
fig, ax = plt.subplots(1, 1, figsize=(14, 14/aspect))
ax.imshow(img_rot, origin='upper')
title = (
    f'UF22 Pascal-Sierpinski + Moebius Mapping\n'
    f'f(z) = z/(z-2)  |  Pascal scale={SCALE}  |  '
    f'n{n_range} k{k_range}  |  fill {pct:.1f}%'
)
ax.set_title(title, color='white', fontsize=11)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='black')
plt.close()
print(f"\nDone: {out_png}")
print(f"  帕斯卡三角填充率: {pct:.1f}%  (Sierpinski gasket density)")
