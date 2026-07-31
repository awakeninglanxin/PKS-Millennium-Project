#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 帕斯卡三角 Mobius映射 v5 — 正确方案

核心算法 (来自 inverse_m_pascal_ripple.py):
  1. 生成帕斯卡三角 mod P 查找表 (N_ROWS × N_ROWS)
  2. 逆M迭代 → 找到核点 (最高迭代区中心)
  3. 对每个逃逸像素:
     a. w → Mobius f_M(w) → z
     b. z → (r, θ) 相对核点
     c. r → n = (r_norm^D) × N_ROWS  (Reiter Theorem 2)
     d. θ → k = θ_frac × n
     e. 查表 pascal[n][k] → 亮度 → 着色

Reiter Theorem 2: D(p) = log(p(p+1)/2) / log(p)
  p=2 → D=log(3)/log(2) ≈ 1.585

关键: c=0 (M集中心) 对应帕斯卡三角尖角 n=0
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
P = 2                           # 模数
N_ROWS = 512                    # 帕斯卡三角行数
D = math.log(P*(P+1)/2) / math.log(P)  # Reiter Thm 2
W, H = 2400, 3577               # 输出尺寸
MAX_ITER = 300
ESCAPE_RADIUS = 50.0
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B-MARGIN, TIP+MARGIN
I0, I1 = -HSP-MARGIN, HSP+MARGIN

# Mobius: f(z) = (az+b)/(cz+d)
A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j  # f(z)=z/(z-2)
print(f"P={P}  D={D:.3f}  N_ROWS={N_ROWS}")
print(f"Mobius: f(z)=({A}z+{B_MOB})/({C_MOB}z+{D_MOB})")

# ==================== 阶段1: 生成帕斯卡三角查找表 ====================
print("[1/5] 生成帕斯卡三角 mod P 查找表...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
pascal[0, 0] = 1 % P
for n in range(1, N_ROWS):
    pascal[n, 0] = pascal[n, n] = 1 % P
    for k in range(1, n):
        pascal[n, k] = (pascal[n-1, k] + pascal[n-1, k-1]) % P
mask = (pascal != 0).astype(np.float64)

# 行密度统计
row_density = np.array([mask[n, :n+1].mean() for n in range(N_ROWS)])
print(f"  行密度: [{row_density[0]:.3f}, {row_density[N_ROWS-1]:.3f}]")
print(f"  末行密度: {row_density[-1]*100:.1f}%")

# ==================== 阶段2: 逆M 迭代 + 找核点 ====================
print("[2/5] 逆M 迭代...")
xs = np.linspace(R0, R1, W); ys = np.linspace(I0, I1, H)
X, Y = np.meshgrid(xs, ys)
w_grid = X + 1j*Y

# 逆M: c_eff = 1/w
eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0 / w_grid[sf]
ce[~sf] = 1e6

Z = np.zeros_like(ce)
iter_count = np.full(ce.shape, -1, dtype=np.int32)
for i in range(MAX_ITER):
    active = iter_count == -1
    if not np.any(active): break
    Z[active] = Z[active]**2 + ce[active]
    escaped = active & (np.abs(Z) > ESCAPE_RADIUS)
    iter_count[escaped] = i
iter_count[iter_count == -1] = MAX_ITER

interior = iter_count == MAX_ITER
escaped = ~interior
print(f"  逃逸: {escaped.sum()}/{W*H} ({escaped.sum()/(W*H)*100:.1f}%)")

# --- 找核点 (最高迭代区 = 水滴尖) ---
top_pct = np.percentile(iter_count[escaped], 92) if escaped.any() else MAX_ITER
um = iter_count >= top_pct
cy = np.nanmean(np.where(um, Y, np.nan))
cx = np.nanmean(np.where(um, X, np.nan))
if math.isnan(cx):
    cx, cy = 0.0, 1.5
print(f"  核点: ({cx:.3f}, {cy:.3f})")

# --- 朝外方向 ---
gy, gx = np.gradient(iter_count.astype(np.float64))
out_angle = math.atan2(
    np.nanmean(np.where(um, gy, np.nan)),
    np.nanmean(np.where(um, gx, np.nan)))
print(f"  朝外角度: {math.degrees(out_angle):.0f}°")

# --- 张角 ---
thr_80 = np.percentile(iter_count[escaped], 80)
high = iter_count >= thr_80
angles = np.arctan2(Y[high]-cy, X[high]-cx)
spread = np.percentile(np.abs(angles), 90)
SPREAD = min(spread * 1.5, math.radians(65))
print(f"  张角: ±{math.degrees(SPREAD):.0f}°")

# --- r范围 ---
dist = np.sqrt((X-cx)**2 + (Y-cy)**2)
r_valid = dist[escaped]
r_min = np.percentile(r_valid, 3)
r_max = np.percentile(r_valid, 95)
print(f"  r范围: [{r_min:.2f}, {r_max:.2f}]")

# ==================== 阶段3: Mobius 变换 (作用于 interior = 水滴内部) ====================
print("[3/5] Mobius 变换 (on interior)...")
def mobius(z, a, b, c, d):
    num = a*z + b; den = c*z + d
    safe = np.abs(den) > 1e-12
    r = np.full(z.shape, np.nan + 1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe] / den[safe]
    return r

# 对 interior (水滴内部) 像素的 w 坐标做 Mobius
w_int = w_grid[interior]
z_mob = mobius(w_int, A, B_MOB, C_MOB, D_MOB)
valid_mob = ~np.isnan(z_mob.real)

# Mobius 后重新计算相对核点的 (r, θ)
zm_valid = z_mob[valid_mob]
nuc_mob = mobius(np.array([cx + 1j*cy]), A, B_MOB, C_MOB, D_MOB)[0]
if np.isnan(nuc_mob.real):
    nuc_mob = 0+0j

dist_mob = np.abs(zm_valid - nuc_mob)
theta_mob = np.angle(zm_valid - nuc_mob)
theta_mob[theta_mob < 0] += 2*np.pi

# ==================== 阶段4: 映射 r→n, θ→k → 查表 ====================
print("[4/5] r→n, θ→k 映射...")
r_mob_min = np.percentile(dist_mob, 3)
r_mob_max = np.percentile(dist_mob, 95)
print(f"  Mobius r范围: [{r_mob_min:.3f}, {r_mob_max:.3f}]")

# r_norm → n (Reiter D(p) 非线性)
r_norm = np.clip((dist_mob - r_mob_min) / (r_mob_max - r_mob_min + 1e-12), 0, 1)
n_float = (r_norm ** D) * (N_ROWS - 1)
n_idx = np.clip(n_float.astype(np.int64), 0, N_ROWS - 1)

# θ → k
k_frac = theta_mob / (2 * np.pi)
k_val = (k_frac * n_idx.astype(np.float64)).astype(np.int64)
k_val = np.clip(k_val, 0, n_idx)

# 查表
brightness_valid = mask[n_idx, k_val]
print(f"  亮度: [{brightness_valid.min():.3f}, {brightness_valid.max():.3f}]")
print(f"  非零比例: {brightness_valid.mean()*100:.1f}%")
print(f"  n范围: [{n_idx.min()}, {n_idx.max()}]")

# 涟漪层验证
print("  涟漪层次:")
for i in range(6):
    r_lo = r_mob_min + (r_mob_max - r_mob_min) * i / 6
    r_hi = r_mob_min + (r_mob_max - r_mob_min) * (i + 1) / 6
    band = (dist_mob >= r_lo) & (dist_mob < r_hi)
    if band.any():
        b = brightness_valid[band].mean()
        nn = int(n_float[band].mean())
        nn = min(nn, N_ROWS-1)
        dd = row_density[nn]
        print(f"    r=[{r_lo:.2f},{r_hi:.2f}): b={b:.4f}  n≈{nn:>3d}  ρ={dd*100:.1f}%")

# ==================== 阶段5: 着色 (exterior=帕斯卡, interior=纯色) ====================
print("[5/5] 着色...")
img = np.zeros((H, W, 3))

# --- 逃逸区(exterior): 纯深蓝背景 ---
img[escaped] = [0.02, 0.05, 0.16]

# --- 水滴内部(interior): 帕斯卡纹理! ---
brightness_full = np.zeros(interior.sum(), dtype=np.float64)
brightness_full[valid_mob] = brightness_valid

fill_color = np.array([0.92, 0.65, 0.08])    # 暖金(帕斯卡填充)
empty_color = np.array([0.05, 0.10, 0.30])   # 钢蓝(帕斯卡空白)

int_idx = np.where(interior)
for i, (py, px) in enumerate(zip(int_idx[0], int_idx[1])):
    bv = brightness_full[i]
    if bv > 0.5:
        img[py, px] = fill_color * (0.7 + 0.3*bv)
    else:
        img[py, px] = empty_color * (0.3 + 0.7*(1-bv)) + bv * 0.15

# --- 核点辉光 (水滴尖) ---
core_r = r_min + (r_max - r_min) * 0.04
cmask = dist < core_r
if cmask.any():
    img[cmask] += [0.25, 0.20, 0.10]

# --- DEM金边 ---
abs_Z = np.abs(Z)
dem = np.zeros_like(w_grid, dtype=np.float64)
dem[escaped] = abs_Z[escaped] * np.log(abs_Z[escaped] + 1e-12) / (abs_Z[escaped] + 1e-12)
dem_max = np.percentile(dem[escaped], 95) if escaped.any() else 1.0
dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)

edge_glow = np.exp(-dem_norm * 15)
glow_mask = escaped & (dem_norm < 0.3)
img[glow_mask] += edge_glow[glow_mask, None] * 0.4

img = np.clip(img, 0, 1)

# ==================== 输出 ====================
out_png = os.path.join(od, 'UF22_帕斯卡Mobius_v5.png')
img_rot = np.rot90(img, k=1)
aspect = img_rot.shape[1] / img_rot.shape[0]

fig, ax = plt.subplots(1, 1, figsize=(14, 14/aspect))
ax.imshow(img_rot, origin='upper', interpolation='bilinear')
ax.set_title(
    f'UF22 Pascal Triangle + Moebius (v5 — correct algorithm)\n'
    f'Mobius f(z)=z/(z-2) | p={P} | D={D:.3f} (Reiter Thm 2)\n'
    f'nucleus=({cx:.1f},{cy:.1f}) | r=[{r_mob_min:.1f},{r_mob_max:.1f}] | '
    f'fill {brightness_valid.mean()*100:.1f}%',
    color='white', fontsize=10)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='black')
plt.close()

# 同时保存帕斯卡源图像 (A_pascal 风格)
src_out = os.path.join(od, 'UF22_帕斯卡源图像_v5.png')
tri_show = np.zeros((256, 256))
for n in range(256):
    for k in range(n+1):
        tri_show[n, k] = mask[n, k]
fig, ax = plt.subplots(figsize=(8, 12), dpi=130)
ax.imshow(tri_show, cmap='gray_r', interpolation='nearest',
          extent=[0, 256, 256, 0], aspect='auto')
ax.set_title(f"Pascal Triangle mod {P} (source)\nD={D:.3f}", fontsize=12)
ax.set_xlabel("k"); ax.set_ylabel("n")
plt.tight_layout()
fig.savefig(src_out, dpi=130)
plt.close()

print(f"\nDone:\n  {out_png}\n  {src_out}")
print(f"  img mean: {img.mean():.4f}")
