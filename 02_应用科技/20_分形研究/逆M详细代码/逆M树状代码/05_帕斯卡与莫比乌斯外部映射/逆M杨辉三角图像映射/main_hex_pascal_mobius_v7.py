#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 六向帕斯卡三角 360°周期平铺 × Möbius v7

改进 (v6→v7):
  1. HEX_SCALE=0.015 → 纹理更密
  2. 中心 = mobius(w=-1) → 逆M实轴-1对应六边形中心
  3. 周期延拓: n_eff = n % N_ROWS → 六边形无限平铺, 保持前N行32%密度
  4. N_ROWS=512 → 更丰富的细节变化

算法:
  Z(n,k) = (n-k) + k*e^(iπ/3)  (帕斯卡三角→复数坐标)
  Z_360(n,k,m) = Z * e^(imπ/3)  (六向旋转)
  周期延拓: n↦n%N_ROWS, k↦wrap(k, 0, n_eff)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, math

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

od = os.path.dirname(os.path.abspath(__file__))

# ==================== 参数 ====================
P = 2
N_ROWS = 512
HEX_SCALE = 0.015          # 更密
D = math.log(P*(P+1)/2) / math.log(P)
W, H = 2400, 3577
MAX_ITER = 300; ESCAPE_RADIUS = 50.0
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B-MARGIN, TIP+MARGIN; I0, I1 = -HSP-MARGIN, HSP+MARGIN

# Möbius
A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j  # f(z)=z/(z-2)

# 中心: w=-1 (逆M实轴-1) → Möbius后
CENTER_W = -1.0 + 0j
CENTER_Z = CENTER_W / (CENTER_W - 2)  # ≈ 0.333

print(f"P={P} D={D:.3f} N_ROWS={N_ROWS} HEX_SCALE={HEX_SCALE}")
print(f"中心: w={CENTER_W} → z={CENTER_Z:.3f}")
print(f"Möbius: f(z)=z/(z-2)")

# ==================== 阶段1: 帕斯卡三角查找表 ====================
print(f"[1/5] 帕斯卡三角 mod {P} (N_ROWS={N_ROWS})...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
pascal[0, 0] = 1 % P
for n in range(1, N_ROWS):
    pascal[n, 0] = pascal[n, n] = 1 % P
    for k in range(1, n):
        pascal[n, k] = (pascal[n-1, k] + pascal[n-1, k-1]) % P
pascal_mask = (pascal != 0)
fill_ratio = pascal_mask[:N_ROWS, :N_ROWS].mean()
print(f"  整体填充率: {fill_ratio*100:.1f}%")

# ==================== 阶段2: 逆M迭代 ====================
print("[2/5] 逆M迭代...")
xs = np.linspace(R0, R1, W); ys = np.linspace(I0, I1, H)
X, Y = np.meshgrid(xs, ys); w_grid = X + 1j*Y

eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0 / w_grid[sf]; ce[~sf] = 1e6

Z_iter = np.zeros_like(ce)
iter_count = np.full(ce.shape, -1, dtype=np.int32)
for i in range(MAX_ITER):
    active = iter_count == -1
    if not np.any(active): break
    Z_iter[active] = Z_iter[active]**2 + ce[active]
    esc = active & (np.abs(Z_iter) > ESCAPE_RADIUS)
    iter_count[esc] = i
iter_count[iter_count == -1] = MAX_ITER

interior = iter_count == MAX_ITER
escaped = ~interior
print(f"  interior: {interior.sum()}/{W*H} ({interior.sum()/(W*H)*100:.1f}%)")

# ==================== 阶段3: Möbius 变换 ====================
print("[3/5] Möbius 变换 (中心=w=-1)...")
def mobius(z, a, b, c, d):
    num = a*z + b; den = c*z + d
    safe = np.abs(den) > 1e-12
    r = np.full(z.shape, np.nan + 1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe] / den[safe]
    return r

w_int = w_grid[interior]
z_mob = mobius(w_int, A, B_MOB, C_MOB, D_MOB)
valid_mob = ~np.isnan(z_mob.real)

# 中心移: w=-1 → z=CENTER_Z
zm_valid = z_mob[valid_mob] - CENTER_Z
N_int_valid = len(zm_valid)
print(f"  Mobius valid: {N_int_valid}/{interior.sum()}")

# ==================== 阶段4: 六向帕斯卡 + 周期延拓 ====================
print("[4/5] 六向帕斯卡 360° 周期平铺...")
SR3 = np.sqrt(3)
SIX_ANGLES = np.array([m * np.pi / 3 for m in range(6)])
ROT_COS = np.cos(-SIX_ANGLES); ROT_SIN = np.sin(-SIX_ANGLES)

brightness = np.zeros(N_int_valid, dtype=np.float64)

for m in range(6):
    # 反旋转
    z_re = zm_valid.real * ROT_COS[m] - zm_valid.imag * ROT_SIN[m]
    z_im = zm_valid.real * ROT_SIN[m] + zm_valid.imag * ROT_COS[m]

    # 缩放
    z_re_sc = z_re / HEX_SCALE
    z_im_sc = z_im / HEX_SCALE

    # 反算 (n,k)
    k_float = 2.0 * z_im_sc / SR3
    n_float = z_re_sc + z_im_sc / SR3

    n_round = np.round(n_float).astype(np.int64)
    k_round = np.round(k_float).astype(np.int64)

    # ★ 周期延拓: n → n%N_ROWS, k必须严格在 [0, n_eff] 内
    n_eff = n_round % N_ROWS
    valid = (k_round >= 0) & (k_round <= n_eff) & (n_eff < N_ROWS)

    if valid.any():
        brightness[valid] = np.maximum(
            brightness[valid],
            pascal_mask[n_eff[valid], k_round[valid]].astype(np.float64)
        )

fill_pct = brightness.mean() * 100
print(f"  亮度: [{brightness.min():.3f}, {brightness.max():.3f}]")
print(f"  填充率: {fill_pct:.1f}%")

# ==================== 阶段5: 着色 ====================
print("[5/5] 着色...")
img = np.zeros((H, W, 3))

# 逃逸背景: 深蓝
img[escaped] = [0.02, 0.04, 0.14]

# Interior: 六向帕斯卡纹理
brightness_full = np.zeros(interior.sum(), dtype=np.float64)
brightness_full[valid_mob] = brightness

fill_color = np.array([0.92, 0.62, 0.06])     # 暖金
empty_color = np.array([0.04, 0.08, 0.28])    # 钢蓝

int_idx = np.where(interior)
for i, (py, px) in enumerate(zip(int_idx[0], int_idx[1])):
    bv = brightness_full[i]
    if bv > 0.5:
        img[py, px] = fill_color * (0.5 + 0.5*bv)
    else:
        img[py, px] = empty_color

# --- DEM金边 ---
abs_Z = np.abs(Z_iter)
dem = np.zeros_like(w_grid, dtype=np.float64)
dem[escaped] = abs_Z[escaped] * np.log(abs_Z[escaped] + 1e-12) / (abs_Z[escaped] + 1e-12)
dem_max = np.percentile(dem[escaped], 95) if escaped.any() else 1.0
dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)
edge_glow = np.exp(-dem_norm * 15)
glow_mask = escaped & (dem_norm < 0.3)
img[glow_mask] += edge_glow[glow_mask, None] * 0.4
img = np.clip(img, 0, 1)

# ==================== 输出 ====================
out_png = os.path.join(od, 'UF22_六向帕斯卡Mobius_v7.png')
img_rot = np.rot90(img, k=1)
aspect = img_rot.shape[1] / img_rot.shape[0]

fig, ax = plt.subplots(1, 1, figsize=(14, 14/aspect))
ax.imshow(img_rot, origin='upper', interpolation='bilinear')
ax.set_title(
    f'UF22 6-Way Pascal Periodic Tiling + Moebius (v7)\n'
    f'center=w=-1 | HEX_SCALE={HEX_SCALE} | N_ROWS={N_ROWS} | '
    f'fill {fill_pct:.1f}% (periodic)',
    color='white', fontsize=11)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='black')
plt.close()

# 源图像 (六向帕斯卡 + 周期延拓)
SRC_SIZE = 1024; src_cx = SRC_SIZE//2; src_cy = SRC_SIZE//2
src_scale = SRC_SIZE / (N_ROWS * 2.0)
sx = np.arange(SRC_SIZE); sy = np.arange(SRC_SIZE)
SX, SY = np.meshgrid(sx, sy)
src_z = (SX - src_cx) / src_scale + 1j * (SY - src_cy) / src_scale
src_brightness = np.zeros((SRC_SIZE, SRC_SIZE), dtype=np.float64)

for m in range(6):
    z_re = src_z.real * ROT_COS[m] - src_z.imag * ROT_SIN[m]
    z_im = src_z.real * ROT_SIN[m] + src_z.imag * ROT_COS[m]
    kf = 2.0 * z_im / SR3; nf = z_re + z_im / SR3
    nr = np.round(nf).astype(np.int64); kr = np.round(kf).astype(np.int64)
    ne = nr % N_ROWS
    v = (kr >= 0) & (kr <= ne) & (ne >= 0) & (ne < N_ROWS)
    if v.any():
        src_brightness[v] = np.maximum(
            src_brightness[v], pascal_mask[ne[v], kr[v]].astype(np.float64))

src_out = os.path.join(od, 'UF22_六向帕斯卡源图_v7.png')
fig, ax = plt.subplots(figsize=(10, 10), dpi=130)
ax.imshow(src_brightness, cmap='gray_r', interpolation='bilinear')
ax.set_title(f"6-Way Pascal Periodic Tiling (v7)\n"
             f"N_ROWS={N_ROWS} | fill={src_brightness.mean()*100:.1f}%",
             fontsize=14)
ax.axis('off')
plt.tight_layout()
fig.savefig(src_out, dpi=130, facecolor='white')
plt.close()

print(f"\nDone: {out_png}")
print(f"  源图: {src_out}, fill={src_brightness.mean()*100:.1f}%")
