#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v16: 直接从 莱维龙形曲线.png 抠图做纹理, 集成逆M渲染"""
import numpy as np, math, os, time
from collections import deque
from PIL import Image
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb as h2r

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
od = os.path.dirname(os.path.abspath(__file__))

print("=== v16: 莱维龙形曲线 图片抠图 → 纹理 LUT → 逆M渲染 ===")

# ==================== 参数 ====================
N_ROWS = 2048
HEX_SCALE = 0.003
W, H = 2400, 2025
MAX_ITER = 300; ESCAPE_RADIUS = 50.0
TIP = 4.0; BOTTOM = -4/3; HSP = 1.6242719100; EXPAND = 4.0
R0, R1 = BOTTOM - EXPAND, TIP + EXPAND
I0, I1 = -HSP - EXPAND, HSP + EXPAND
A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j

t0 = time.time()

# ==================== 阶段0: 从图片抠图生成LUT ====================
print("[0/5] 图片抠图 → LUT...")
img_file = os.path.join(od, '莱维龙形曲线.png')
src_img = np.array(Image.open(img_file))  # RGBA 751×751

# 二值化: 深色=曲线=1, 浅色=背景=0
gray = 0.299*src_img[:,:,0] + 0.587*src_img[:,:,1] + 0.114*src_img[:,:,2]
curve = (gray < 120).astype(np.int16)  # 751×751

# 膨曲线 (让曲线更粗→容易闭合→洪水填充有效)
from scipy.ndimage import binary_dilation
curve_dilated = binary_dilation(curve, structure=np.ones((3,3)), iterations=1).astype(np.int16)

# Resize to N_ROWS
from PIL import Image as PILImage
curve_big = np.array(PILImage.fromarray((curve_dilated*255).astype(np.uint8)).resize(
    (N_ROWS, N_ROWS), PILImage.LANCZOS)) > 128
curve_big = curve_big.astype(np.int16)

# Flood fill: 标记交替区域
print("  洪水填充...")
filled = curve_big.copy()
visited = np.zeros((N_ROWS, N_ROWS), dtype=bool)
rid = 0
for y0 in range(0, N_ROWS, 4):  # stride加速
    for x0 in range(0, N_ROWS, 4):
        if filled[y0, x0] == 0 and not visited[y0, x0]:
            q = deque([(x0, y0)]); visited[y0, x0] = True; rp = []
            while q:
                x, y = q.popleft(); rp.append((x, y))
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < N_ROWS and 0 <= ny < N_ROWS:
                        if filled[ny, nx] == 0 and not visited[ny, nx]:
                            visited[ny, nx] = True; q.append((nx, ny))
            if rid % 2 == 1:
                for x, y in rp:
                    filled[y, x] = 2
            rid += 1

pascal = filled
fill_lut = (pascal > 0).mean() * 100
print(f"  LUT fill={fill_lut:.1f}% ({time.time()-t0:.1f}s)")

# ==================== 阶段1: 逆M迭代 ====================
print("[1/5] 逆M迭代...")
xs, ys = np.linspace(R0, R1, W), np.linspace(I0, I1, H)
X, Y = np.meshgrid(xs, ys); w_grid = X + 1j*Y
eps = 1e-12; sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0/w_grid[sf]; ce[~sf] = 1e6
Z_iter = np.zeros_like(ce)
it = np.full(ce.shape, -1, dtype=np.int32)
for i in range(MAX_ITER):
    act = it == -1
    if not np.any(act): break
    Z_iter[act] = Z_iter[act]**2 + ce[act]
    esc = act & (np.abs(Z_iter) > ESCAPE_RADIUS)
    it[esc] = i
it[it == -1] = MAX_ITER
interior = it == MAX_ITER; escaped = ~interior
print(f"  interior: {interior.sum()/(W*H)*100:.1f}%")

cx, cy = 0.0, 0.0
dist_nuc = np.sqrt((X-cx)**2 + (Y-cy)**2)
r_valid_d = dist_nuc[escaped]
r_min = np.percentile(r_valid_d, 3); r_max = np.percentile(r_valid_d, 95)

# ==================== 阶段2: Möbius ====================
def mobius(z, a, b, c, d):
    num = a*z+b; den = c*z+d
    safe = np.abs(den)>1e-12
    r = np.full(z.shape, np.nan+1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe]/den[safe]; return r

print("[2/5] Mobius...")
nuc_z = mobius(np.array([0+0j]), A, B_MOB, C_MOB, D_MOB)[0]
if np.isnan(nuc_z.real): nuc_z = 0+0j
w_int = w_grid[interior]; zm = mobius(w_int, A,B_MOB,C_MOB,D_MOB)
vm = ~np.isnan(zm.real); zmv = zm[vm] - nuc_z

# ==================== 阶段3: C4正方形判定 ====================
SR3 = np.sqrt(3)
M = 4  # C4 square tiling (Lévy carpet = square)
ANGLES = np.array([m*np.pi/2 for m in range(M)])
RC = np.cos(-ANGLES); RS = np.sin(-ANGLES)
print(f"[3/5] C4判定...")

N_v = len(zmv)
best_mod = np.zeros(N_v, dtype=np.int16)
best_n = np.full(N_v, -1, dtype=np.int64)
best_pri = np.full(N_v, N_ROWS, dtype=np.float64)

for m in range(M):
    zr = zmv.real*RC[m] - zmv.imag*RS[m]
    zi = zmv.real*RS[m] + zmv.imag*RC[m]
    nr = np.round(zi/HEX_SCALE).astype(np.int64)
    kr = np.round(zr/HEX_SCALE).astype(np.int64)
    ne = nr % N_ROWS; ke = kr % N_ROWS
    v = (ne >= 0) & (ne < N_ROWS) & (ke >= 0) & (ke < N_ROWS)
    if v.any():
        vi = np.where(v)[0]
        mv = pascal[ne[vi], ke[vi]]
        nz = mv > 0
        if nz.any():
            ui = vi[nz]; pr = ne[ui].astype(np.float64)
            bt = pr < best_pri[ui]
            if bt.any():
                bi = ui[bt]; best_mod[bi] = mv[nz][bt]
                best_n[bi] = ne[bi]; best_pri[bi] = pr[bt]

fill_pct = (best_mod > 0).mean() * 100
print(f"  fill={fill_pct:.1f}%")

# ==================== 阶段4: 着色 ====================
print("[4/5] 着色...")
img = np.zeros((H, W, 3))
SKY_BG = np.array([0.45, 0.75, 0.92])
img[escaped] = SKY_BG

mod_full = np.zeros(interior.sum(), dtype=np.int8)
n_full = np.full(interior.sum(), -1, dtype=np.int64)
mod_full[vm] = best_mod; n_full[vm] = best_n

ii = np.where(interior)
for i, (py, px) in enumerate(zip(ii[0], ii[1])):
    if mod_full[i] > 0:
        nv = n_full[i]
        hue = 0.12 - (nv / N_ROWS) * 0.65
        if hue < 0: hue += 1.0
        sat = 0.7 + 0.3 * (nv / N_ROWS)
        val = 0.5 + 0.5 * (1 - nv / N_ROWS)
        img[py, px] = h2r([[[hue, sat, val]]])[0, 0]
    else:
        img[py, px] = [0.30, 0.20, 0.08]

core_r = r_min + (r_max - r_min) * 0.05
cmask = dist_nuc < core_r
if cmask.any():
    fade = np.clip(1.0 - dist_nuc[cmask]/core_r, 0, 1)
    img[cmask] = img[cmask]*(1-fade[:,None]*0.6) + fade[:,None]*[0.98,0.96,0.88]

img = np.clip(img, 0, 1)

# ==================== 输出 ====================
DPI = 150
out_png = os.path.join(od, 'UF22_levy_real_v16.png')
img_disp = np.transpose(img, (1, 0, 2))

fig, ax = plt.subplots(figsize=(10, 8), dpi=DPI)
ax.imshow(img_disp, origin='lower', interpolation='bilinear',
          extent=[I0, I1, R0, R1])
ax.set_aspect('equal')

CSV_PATH = os.path.join(
    r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M水滴CFD流体实验',
    'droplet_invM_analytic.csv')
csv_data = np.loadtxt(CSV_PATH, delimiter=',', skiprows=1)
ax.plot(csv_data[:,1], csv_data[:,0], color=[0.95, 0.72, 0.10],
        linewidth=1.0, alpha=0.85)

GOLD = '#D4A017'
for spine in ax.spines.values():
    spine.set_color(GOLD); spine.set_linewidth(2.5)
ax.set_xticks([]); ax.set_yticks([])
fig.patch.set_facecolor('black'); ax.set_facecolor('black')
plt.tight_layout(pad=0.5)
fig.savefig(out_png, dpi=DPI, facecolor='black', bbox_inches='tight')
plt.close()

elapsed = time.time() - t0
print(f"Done: {out_png} ({os.path.getsize(out_png)//1024}KB) {elapsed:.0f}s")
print(f"  D=2  fill={fill_pct:.1f}%")
