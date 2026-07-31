#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 帕斯卡三角 Mobius映射 v4 — 高对比度 + 快速验证

关键调参:
  - 非填充逃逸区: 中深蓝 (而非纯黑), 让帕斯卡三角纹理清晰可见
  - 帕斯卡填充: 暖金色 vs 冷钢蓝 → 强烈对比
  - DEM金边叠加
  - scale=0.08 让三角更密集
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

od = os.path.dirname(os.path.abspath(__file__))

# ====== 视窗 ======
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B - MARGIN, TIP + MARGIN
I0, I1 = -HSP - MARGIN, HSP + MARGIN
W, H = 2400, int(2400 * (R1-R0) / (I1-I0))
MI, BL = 300, 50
print(f"视窗: {W}x{H}  MI={MI}")

# ====== 复数网格 + 迭代 ======
x = np.linspace(R0, R1, W); y = np.linspace(I0, I1, H)
w_grid = np.add.outer(y*1j, x)  # HxW
eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0 / w_grid[sf]; ce[~sf] = 1e6

z = np.zeros_like(ce); dz = np.ones_like(ce)
alive = np.ones(ce.shape, bool); esc_iter = np.zeros(ce.shape, int)

for i in range(MI):
    if not alive.any(): break
    idx = np.where(alive)
    za, ca, dza = z[idx].copy(), ce[idx].copy(), dz[idx].copy()
    dza = 2*za*dza + 1; za = za*za + ca
    z[idx], dz[idx] = za, dza
    esc = np.zeros(ce.shape, bool)
    esc[idx] = (za.real**2 + za.imag**2 > BL**2)
    esc_iter[esc] = i + 1
    alive &= ~esc

interior, ext = ~alive, alive
print(f"逃逸: {ext.sum()}/{W*H} ({ext.sum()/(W*H)*100:.1f}%)")

# ====== Mobius & Pascal ======
def mobius(z, a, b, c, d):
    num, den = a*z + b, c*z + d
    safe = np.abs(den) > 1e-12
    r = np.full(z.shape, np.nan + 1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe] / den[safe]
    return r

def pascal_fill(re_vals, im_vals, scale, ox=0, oy=0):
    sr3 = np.sqrt(3)
    b_coord = 2*(im_vals + oy) / (scale * sr3)
    a_coord = (re_vals + ox) / scale - b_coord/2
    n = np.round(a_coord + b_coord).astype(np.int64)
    k = np.round(b_coord).astype(np.int64)
    valid = (n >= 0) & (k >= 0) & (k <= n)
    return valid & ((k & ~n) == 0), n, k

# f(z) = z/(z-2), scale=0.08 (更密集的三角)
A, B_M, C_M, D_M = 1+0j, 0+0j, 1+0j, -2+0j
SCALE = 0.08; OX, OY = 0.2, 0.15

w_ext = w_grid[ext]
zm = mobius(w_ext, A, B_M, C_M, D_M)
valid_m = ~np.isnan(zm.real)
zm_v = zm[valid_m]
pascal, nv, kv = pascal_fill(zm_v.real, zm_v.imag, SCALE, OX, OY)
pct = pascal.sum()/len(pascal)*100 if len(pascal) > 0 else 0
print(f"Pascal scale={SCALE} n[{nv.min()},{nv.max()}] k[{kv.min()},{kv.max()}] fill={pascal.sum()}/{len(pascal)} ({pct:.1f}%)")

# ====== 着色 (高对比度方案) ======
img = np.zeros((H, W, 3))

# --- 水滴内部: 深度蓝黑 ---
img[interior] = [0.02, 0.04, 0.14]

# --- 逃逸区 ---
fill_color = np.array([0.95, 0.70, 0.10])     # 暖金 (帕斯卡填充)
empty_color = np.array([0.06, 0.12, 0.35])     # 钢蓝 (非填充, 有可见度)
nan_color = np.array([0.03, 0.03, 0.10])       # Mobius奇点 → 极暗

pascal_full = np.zeros(ext.sum(), dtype=bool)
pascal_full[valid_m] = pascal

ext_idx = np.where(ext)
for i, (py, px) in enumerate(zip(ext_idx[0], ext_idx[1])):
    if not valid_m[i]:
        img[py, px] = nan_color
    elif pascal_full[i]:
        img[py, px] = fill_color
    else:
        img[py, px] = empty_color

# --- DEM金边 ---
abs_z, abs_dz = np.abs(z), np.abs(dz) + 1e-12
dem = np.zeros_like(w_grid, dtype=np.float64)
dem[ext] = abs_z[ext] * np.log(abs_z[ext] + 1e-12) / abs_dz[ext]
dem_max = np.percentile(dem[ext], 95) if ext.any() else 1.0
dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)
edge_dark = np.clip(1.0 - np.exp(-dem_norm * 3.5), 0, 1)
edge_glow = np.exp(-dem_norm * 14)
# DEM只作用于逃逸区
img[ext] *= edge_dark[ext, None]
# 光晕仅在真正边缘 (dem_norm小), 且只在逃逸区
glow_mask = ext & (dem_norm < 0.3)
img[glow_mask] += edge_glow[glow_mask, None] * 0.45

# --- 逃逸势能微调 ---
nu = esc_iter.astype(np.float64)
nu_max = nu[ext].max() or 1.0
nu_norm = np.clip(nu / nu_max, 0, 1)
brightness = 0.80 + 0.20 * (1.0 - nu_norm[ext])
img[ext] *= brightness[:, None]
img = np.clip(img, 0, 1)

# ====== 输出 ======
out_png = os.path.join(od, 'UF22_帕斯卡Mobius_v4.png')
img_rot = np.rot90(img, k=1)
aspect = img_rot.shape[1] / img_rot.shape[0]

fig, ax = plt.subplots(1, 1, figsize=(14, 14/aspect))
ax.imshow(img_rot, origin='upper')
ax.set_title(
    f'UF22 Pascal-Sierpinski + Moebius Mapping (v4 High Contrast)\n'
    f'f(z)=z/(z-2)  scale={SCALE}  '
    f'fill {pct:.1f}%  |  Gold=Fill  SteelBlue=Empty',
    color='white', fontsize=11)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='black')
plt.close()

# 同时生成纯帕斯卡纹理(仅逃逸区, 用于预览)
preview = img[ext].mean(axis=-1)
print(f"\nDone: {out_png}")
print(f"  img mean brightness: {img.mean():.4f}")
print(f"  escape mean: {img[ext].mean():.4f}, interior mean: {img[interior].mean():.4f}")
