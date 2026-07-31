#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 六向帕斯卡 360°平铺 × Möbius v8

v7→v8 改进:
  1. 源图: 纯六向帕斯卡, 无周期延拓 → 清晰六角雪花
  2. 等轴显示: ax.set_aspect('equal')
  3. HEX_SCALE=0.02 → 纹理适度稀疏, 结构更清晰
  4. 渲染保留周期延拓 (n%N_ROWS)
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
P = 2; N_ROWS = 512
HEX_SCALE = 0.02           # 比0.015稍大 → 纹理更清晰
W, H = 2400, 3577
MAX_ITER = 300; ESCAPE_RADIUS = 50.0
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B-MARGIN, TIP+MARGIN; I0, I1 = -HSP-MARGIN, HSP+MARGIN
ASPECT = (R1-R0) / (I1-I0)

A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j
CENTER_W = -1.0 + 0j
CENTER_Z = CENTER_W / (CENTER_W - 2)

print(f"N_ROWS={N_ROWS} HEX_SCALE={HEX_SCALE} aspect={ASPECT:.3f}")
print(f"中心: w={CENTER_W} → z={CENTER_Z:.3f}")

# ==================== 帕斯卡三角 ====================
print(f"[1/4] 帕斯卡三角 mod {P} ({N_ROWS}行)...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8); pascal[0,0] = 1%P
for n in range(1,N_ROWS):
    pascal[n,0] = pascal[n,n] = 1%P
    for k in range(1,n): pascal[n,k] = (pascal[n-1,k]+pascal[n-1,k-1])%P
p_mask = (pascal != 0)

# ==================== 逆M迭代 ====================
print("[2/4] 逆M迭代...")
xs, ys = np.linspace(R0,R1,W), np.linspace(I0,I1,H)
X, Y = np.meshgrid(xs, ys); w_grid = X + 1j*Y
eps = 1e-12
sf = np.abs(w_grid) > eps
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

# ==================== Möbius ====================
def mobius(z, a, b, c, d):
    num = a*z+b; den = c*z+d
    safe = np.abs(den)>1e-12
    r = np.full(z.shape, np.nan+1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe]/den[safe]; return r

w_int = w_grid[interior]
zm = mobius(w_int, A,B_MOB,C_MOB,D_MOB)
vm = ~np.isnan(zm.real); zmv = zm[vm] - CENTER_Z

# ==================== 六向帕斯卡 (周期延拓 for 渲染) ====================
print("[3/4] 六向帕斯卡判定...")
SR3 = np.sqrt(3)
ANGLES = np.array([m*np.pi/3 for m in range(6)])
RC, RS = np.cos(-ANGLES), np.sin(-ANGLES)

def hex_pascal_lookup(z_re, z_im, hex_scale, n_rows, periodic=True):
    """六向帕斯卡判定。periodic=True→n%n_rows延拓"""
    brightness = np.zeros(z_re.shape, dtype=np.float64)
    for m in range(6):
        zr = z_re*RC[m] - z_im*RS[m]
        zi = z_re*RS[m] + z_im*RC[m]
        zrs = zr/hex_scale; zis = zi/hex_scale
        kf = 2.0*zis/SR3; nf = zrs + zis/SR3
        nr = np.round(nf).astype(np.int64); kr = np.round(kf).astype(np.int64)
        if periodic:
            ne = nr % n_rows
        else:
            ne = nr
        v = (kr>=0) & (kr<=ne) & (ne>=0) & (ne<n_rows)
        if v.any():
            brightness[v] = np.maximum(brightness[v],
                p_mask[ne[v], kr[v]].astype(np.float64))
    return brightness

b_right = hex_pascal_lookup(zmv.real, zmv.imag, HEX_SCALE, N_ROWS, periodic=True)
fill_pct = b_right.mean()*100
print(f"  渲染填充率: {fill_pct:.1f}%")

# ==================== 着色 ====================
print("[4/4] 着色+输出...")
img = np.zeros((H,W,3))
img[escaped] = [0.02, 0.04, 0.14]

bf = np.zeros(interior.sum(), dtype=np.float64); bf[vm] = b_right
fc = np.array([0.92,0.62,0.06]); ec = np.array([0.04,0.08,0.28])
ii = np.where(interior)
for i,(py,px) in enumerate(zip(ii[0],ii[1])):
    bv = bf[i]
    img[py,px] = fc*(0.5+0.5*bv) if bv>0.5 else ec

# DEM金边
absZ = np.abs(Z_iter)
dem = np.zeros((H,W), dtype=np.float64)
dem[escaped] = absZ[escaped]*np.log(absZ[escaped]+1e-12)/(absZ[escaped]+1e-12)
dmax = np.percentile(dem[escaped],95) if escaped.any() else 1
dn = np.clip(dem/max(dmax,1e-12),0,1)
eg = np.exp(-dn*15); gm = escaped & (dn<0.3)
img[gm] += eg[gm,None]*0.4
img = np.clip(img,0,1)

# ==== 等轴输出: 主渲染图 ====
out_png = os.path.join(od, 'UF22_六向帕斯卡Mobius_v8.png')
dpi = 150
fig_w = W/dpi; fig_h = H/dpi
fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
ax.imshow(np.rot90(img, k=1), origin='upper', interpolation='bilinear')
ax.set_aspect('equal')
ax.set_title(
    f'UF22 6-Way Pascal + Moebius (v8) | center=w=-1\n'
    f'HEX_SCALE={HEX_SCALE} N_ROWS={N_ROWS} fill={fill_pct:.1f}% (periodic)',
    color='white', fontsize=10)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.subplots_adjust(0,0,1,1)
fig.savefig(out_png, dpi=dpi, facecolor='black')
plt.close()

# ==== 等轴输出: 六向帕斯卡源图 (纯, 无周期延拓) ====
SRC = 1024
off = SRC//2
# 让三角直径占画面80%: N_ROWS行→物理半径N_ROWS→src_scale=N_ROWS/off*0.8
src_s = N_ROWS / (off * 0.9)
print(f"  源图 scale={src_s:.4f} (三角占画面90%)")

sx = np.arange(SRC); sy = np.arange(SRC)
SX, SY = np.meshgrid(sx, sy)
sz = (SX-off)/src_s + 1j*(SY-off)/src_s  # 注意: y轴正方向朝上
src_b = hex_pascal_lookup(sz.real, sz.imag, 1.0, N_ROWS, periodic=False)
print(f"  源图填充率: {src_b.mean()*100:.1f}%")

src_out = os.path.join(od, 'UF22_六向帕斯卡源图_v8.png')
fig, ax = plt.subplots(figsize=(SRC/dpi, SRC/dpi), dpi=dpi)
ax.imshow(1-src_b, cmap='gray', interpolation='bilinear',
          extent=[-off/src_s, off/src_s, -off/src_s, off/src_s])
ax.set_aspect('equal')
ax.set_title(f'6-Way Pascal Triangle (pure, no periodic)\n'
             f'N_ROWS={N_ROWS} fill={src_b.mean()*100:.1f}%', fontsize=13)
ax.set_xlabel('Re'); ax.set_ylabel('Im')
fig.tight_layout()
fig.savefig(src_out, dpi=dpi, facecolor='white')
plt.close()

print(f"\nDone: {out_png} ({os.path.getsize(out_png)//1024}KB)")
print(f"       {src_out} ({os.path.getsize(src_out)//1024}KB)")
