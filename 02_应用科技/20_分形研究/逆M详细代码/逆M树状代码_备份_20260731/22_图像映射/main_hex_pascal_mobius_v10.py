#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 六向帕斯卡 × Möbius v12 — p=16, HEX微调 → fill≈1/φ

参数: P=16, N_ROWS=2048, HEX_SCALE=0.003, D=1.772
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, math, time
from matplotlib.colors import hsv_to_rgb as h2r

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

od = os.path.dirname(os.path.abspath(__file__))

# ==================== 参数 ====================
P = 16
N_ROWS = 2048
HEX_SCALE = 0.003
D = math.log(P*(P+1)/2) / math.log(P)
# 视窗: 水滴边界精确值外扩+4 (来自逆M水滴边框精确求解.md)
TIP = 4.0; BOTTOM = -4/3; HSP = 1.6242719100; EXPAND = 4.0
R0, R1 = BOTTOM - EXPAND, TIP + EXPAND    # [-5.333, 8.0]
I0, I1 = -HSP - EXPAND, HSP + EXPAND      # [-5.624, 5.624]
ASPECT_RATIO = (R1-R0) / (I1-I0)
W = 2400; H = int(W / ASPECT_RATIO)
MAX_ITER = 300; ESCAPE_RADIUS = 50.0

A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j
CENTER_W = 0.0 + 0j; CENTER_Z = CENTER_W / (CENTER_W - 2)  # w=0 → Möbius→0

# 7色: mod 0=白, mod 1-6 各一色
MOD_COLORS = np.array([
    [1.00, 1.00, 1.00],  # mod 0: 白色 (空白)
    [0.90, 0.22, 0.20],  # mod 1: 红
    [0.96, 0.55, 0.15],  # mod 2: 橙
    [0.85, 0.75, 0.10],  # mod 3: 金
    [0.15, 0.62, 0.55],  # mod 4: 青绿
    [0.20, 0.45, 0.70],  # mod 5: 蓝
    [0.55, 0.15, 0.75],  # mod 6: 紫
])

print(f"P={P} N_ROWS={N_ROWS} HEX_SCALE={HEX_SCALE} D={D:.3f}")

# ==================== 阶段1: 帕斯卡三角 mod P ====================
t0 = time.time()
print(f"[1/5] 帕斯卡三角 mod {P} ({N_ROWS}行)...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
pascal[0, 0] = 1 % P
for n in range(1, N_ROWS):
    pascal[n, 0] = pascal[n, n] = 1 % P
    for k in range(1, n):
        pascal[n, k] = (pascal[n-1, k] + pascal[n-1, k-1]) % P
p_mask = (pascal != 0)
print(f"  生成耗时: {time.time()-t0:.1f}s  fill={p_mask.mean()*100:.1f}%")

# 各余数统计
for mod_val in range(1, P):
    cnt = (pascal == mod_val).sum()
    print(f"  mod={mod_val}: {cnt:,} ({cnt/pascal.size*100:.2f}%)")

# ==================== 阶段2: 逆M迭代 ====================
print("[2/5] 逆M迭代...")
xs, ys = np.linspace(R0, R1, W), np.linspace(I0, I1, H)
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

# --- 核点: w=0 (逆M原点) ---
cx, cy = 0.0, 0.0
nuc_w = cx + 1j*cy
dist_from_nuc = np.sqrt((X-cx)**2 + (Y-cy)**2)
r_valid_d = dist_from_nuc[escaped]
r_min = np.percentile(r_valid_d, 3); r_max = np.percentile(r_valid_d, 95)
print(f"  核点: w=0  r范围: [{r_min:.3f}, {r_max:.3f}]")
CENTER_W_FIXED = CENTER_Z  # 暂存

# ==================== 阶段3: Möbius ====================
def mobius(z, a, b, c, d):
    num = a*z+b; den = c*z+d
    safe = np.abs(den)>1e-12
    r = np.full(z.shape, np.nan+1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe]/den[safe]; return r

# 核点Möbius
nuc_z = mobius(np.array([nuc_w]), A, B_MOB, C_MOB, D_MOB)[0]
if np.isnan(nuc_z.real): nuc_z = CENTER_W_FIXED
CENTER_Z = nuc_z
print(f"  核点Möbius后: {CENTER_Z:.3f}")

w_int = w_grid[interior]; zm = mobius(w_int, A,B_MOB,C_MOB,D_MOB)
vm = ~np.isnan(zm.real); zmv = zm[vm] - CENTER_Z
print(f"  Mobius valid (interior): {vm.sum()}/{interior.sum()}")

# ==================== 阶段4: 六向帕斯卡 (返回mod值) ====================
print("[4/5] 六向帕斯卡 p=7 分组判定...")
SR3 = np.sqrt(3)
ANGLES = np.array([m*np.pi/3 - np.pi/6 for m in range(6)])  # -30°起步: 六边形边对齐实轴
RC, RS = np.cos(-ANGLES), np.sin(-ANGLES)
print(f"  六向角度: {[f'{math.degrees(a):.0f}°' for a in ANGLES]}")

def hex_pascal_mod(z_re, z_im, pascal_arr, n_rows, hex_scale, periodic=True):
    """返回 best_mod (0=空白, 1-6=余数), best_n, best_dir"""
    N = len(z_re)
    best_mod = np.zeros(N, dtype=np.int8)
    best_n = np.full(N, -1, dtype=np.int64)
    best_dir = np.full(N, -1, dtype=np.int8)
    best_priority = np.full(N, n_rows, dtype=np.float64)  # 初始化为极大值

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
            vi = np.where(v)[0]
            mod_vals = pascal_arr[ne[vi], kr[vi]]
            nonzero = mod_vals > 0
            if nonzero.any():
                ui = vi[nonzero]
                # 优先级: n越小(接近中心) → 越优先
                priority = ne[ui].astype(np.float64)
                better = priority < best_priority[ui]
                if better.any():
                    bi = ui[better]
                    best_mod[bi] = mod_vals[nonzero][better]
                    best_n[bi] = ne[bi]
                    best_dir[bi] = m
                    best_priority[bi] = priority[better]

    return best_mod, best_n, best_dir

t1 = time.time()
b_mod, b_n, b_dir = hex_pascal_mod(zmv.real, zmv.imag, pascal, N_ROWS, HEX_SCALE, periodic=True)
fill_pct = (b_mod > 0).mean() * 100
print(f"  判定耗时: {time.time()-t1:.1f}s  fill={fill_pct:.1f}%")
for mod_val in range(1, P):
    cnt = (b_mod == mod_val).sum()
    print(f"  mod={mod_val}: {cnt:,} ({cnt/len(b_mod)*100:.2f}%)")

# ==================== 阶段5: 着色 ====================
print("[5/5] 着色...")
img = np.zeros((H, W, 3))

SKY_BG   = np.array([0.45, 0.75, 0.92])

# ===== Escaped(背景): 纯净天蓝 =====
img[escaped] = SKY_BG

# ===== Interior: 帕斯卡纹理 v12风格 (n彩虹 + 暗琥珀底) =====
mod_full = np.zeros(interior.sum(), dtype=np.int8)
n_full   = np.full(interior.sum(), -1, dtype=np.int64)
mod_full[vm] = b_mod; n_full[vm] = b_n

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

# --- 核点辉光 (水滴尖端暖白) ---
core_r = r_min + (r_max - r_min) * 0.05
cmask = dist_from_nuc < core_r
if cmask.any():
    fade = np.clip(1.0 - dist_from_nuc[cmask]/core_r, 0, 1)
    img[cmask] = img[cmask] * (1-fade[:,None]*0.6) + fade[:,None] * [0.98, 0.96, 0.88]

img = np.clip(img, 0, 1)

# ==================== 输出 ====================
DPI = 150
out_png = os.path.join(od, 'UF22_六向帕斯卡Mobius_v14.png')

# img原始: 行=Im(I0→I1), 列=Re(R0→R1)
# 转置→ 行=Re(R0→R1), 列=Im(I0→I1), origin='lower'→R0下R1上(尖端↑)
img_disp = np.transpose(img, (1, 0, 2))

fig, ax = plt.subplots(figsize=(10, 8), dpi=DPI)
ax.imshow(img_disp, origin='lower', interpolation='bilinear',
          extent=[I0, I1, R0, R1])
ax.set_aspect('equal')

# 水滴解析轮廓线
CSV_PATH = os.path.join(
    r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M水滴CFD流体实验',
    'droplet_invM_analytic.csv')
csv_data = np.loadtxt(CSV_PATH, delimiter=',', skiprows=1)
ax.plot(csv_data[:,1], csv_data[:,0], color=[0.95, 0.72, 0.10],
        linewidth=1.0, alpha=0.85)

# 金色画框 (无刻度/标签)
GOLD = '#D4A017'
for spine in ax.spines.values():
    spine.set_color(GOLD)
    spine.set_linewidth(2.5)
ax.set_xticks([]); ax.set_yticks([])
fig.patch.set_facecolor('black')
ax.set_facecolor('black')
plt.tight_layout(pad=0.5)
fig.savefig(out_png, dpi=DPI, facecolor='black', bbox_inches='tight')
plt.close()

# 源图 (p=16, 纯六向无延拓, n彩虹着色)
SRC = 1200; off = SRC//2
src_s = N_ROWS / (off * 0.85)
SX, SY = np.meshgrid(np.arange(SRC), np.arange(SRC))
sz_re = (SX - off) / src_s
sz_im = (SY - off) / src_s
sm, sn, sd = hex_pascal_mod(sz_re.ravel(), sz_im.ravel(), pascal, N_ROWS, 1.0, periodic=False)
# n彩虹着色
src_rgb = np.ones((SRC, SRC, 3))
sm_img = sm.reshape(SRC, SRC); sn_img = sn.reshape(SRC, SRC)
mask_s = sm_img > 0
if mask_s.any():
    nv_s = sn_img[mask_s].astype(np.float64)
    hue_s = 0.12 - (nv_s/N_ROWS)*0.65; hue_s[hue_s<0] += 1.0
    sat_s = 0.7 + 0.3*(nv_s/N_ROWS)
    val_s = 0.5 + 0.5*(1-nv_s/N_ROWS)
    hsv_s = np.stack([hue_s,sat_s,val_s], axis=-1)
    src_rgb[mask_s] = h2r(hsv_s)

src_out = os.path.join(od, 'UF22_六向帕斯卡源图_v12_p15.png')
fig, ax = plt.subplots(figsize=(SRC/DPI, SRC/DPI), dpi=DPI)
ax.imshow(src_rgb, interpolation='bilinear')
ax.set_aspect('equal')
ax.set_title(f'6-Way Pascal p={P} N_ROWS={N_ROWS}\n'
             f'fill={(sm>0).mean()*100:.1f}%', fontsize=13)
ax.axis('off')
fig.tight_layout()
fig.savefig(src_out, dpi=DPI, facecolor='white')
plt.close()

print(f"\nDone: {out_png} ({os.path.getsize(out_png)//1024}KB)")
print(f"       {src_out} ({os.path.getsize(src_out)//1024}KB)")
print(f"总耗时: {time.time()-t0:.1f}s")
