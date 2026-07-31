#!/usr/bin/env python3
"""
inverse_m_pascal_ripple.py
============================
帕斯卡三角从中心向外生长，涟漪层次感。

核心改变：
  行号 n 本身就是亮度，不额外衰减。
  n 小（核区）→ 亮
  n 大（外圈）→ 暗
  但中间各层的"涟漪"由帕斯卡三角模 p 的自然结构产生——
  某些行特别密（亮涟漪），某些行特别疏（暗涟漪），
  形成由内而外的波纹层次感。

公式：
  brightness = pascal[n(r)][k(theta)]
  其中 n(r) 把距离映射到行号，不做亮度衰减
"""

import numpy as np
import matplotlib.pyplot as plt
import time, math
from math import comb

# ============================================================
# 参数
# ============================================================
P = 2
N_ROWS = 512
WIDTH, HEIGHT = 2400, 2400
MAX_ITER = 400
ESCAPE_RADIUS = 16.0
X_MIN, X_MAX = -3.0, 3.0
Y_MIN, Y_MAX = -1.5, 4.5

D = math.log(P*(P+1)/2) / math.log(P)
print(f"p={P}: D={D:.6f}  N_ROWS={N_ROWS}")

# ============================================================
# 1. 帕斯卡三角 mod P
# ============================================================
print("[1/4] 帕斯卡三角 mod P ...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
pascal[0, 0] = 1 % P
for n in range(1, N_ROWS):
    pascal[n, 0] = pascal[n, n] = 1 % P
    for k in range(1, n):
        pascal[n, k] = (pascal[n-1, k] + pascal[n-1, k-1]) % P

mask = (pascal != 0).astype(np.float64)

# 每行密度
row_density = np.array([mask[n,:n+1].mean() for n in range(N_ROWS)])
print(f"  密度范围: [{row_density.min():.4f}, {row_density.max():.4f}]")
print(f"  顶行(n=0): {row_density[0]*100:.0f}%")
print(f"  末行(n={N_ROWS-1}): {row_density[-1]*100:.0f}%")

# ============================================================
# 2. 复平面 + Mobius + 正M
# ============================================================
print("[2/4] Mobius + 正M ...")
xs = np.linspace(X_MIN, X_MAX, WIDTH, dtype=np.float64)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT, dtype=np.float64)
X, Y = np.meshgrid(xs, ys)
C = Y + 1j * X
C = np.where(np.abs(C) < 1e-15, 1e-15 + 0j, C)
C_inv = 1.0 / C

Z = np.zeros_like(C_inv, dtype=np.complex128)
iter_count = np.full(C_inv.shape, -1, dtype=np.int32)
for n in range(MAX_ITER):
    active = iter_count == -1
    if not np.any(active): break
    Z[active] = Z[active]**2 + C_inv[active]
    escaped = active & (np.abs(Z) > ESCAPE_RADIUS)
    iter_count[escaped] = n
iter_count[iter_count == -1] = MAX_ITER

um = iter_count >= np.percentile(iter_count, 92)
cy = np.nanmean(np.where(um, Y, np.nan))
cx = np.nanmean(np.where(um, X, np.nan))
if math.isnan(cx): cx, cy = 0.0, 1.5
print(f"  核: ({cx:.2f}, {cy:.2f})")

# 朝外方向
gy, gx = np.gradient(iter_count.astype(np.float64))
out_angle = math.atan2(np.nanmean(np.where(um, gy, np.nan)),
                       np.nanmean(np.where(um, gx, np.nan)))
print(f"  朝外角度: {math.degrees(out_angle):.0f}°")

# 张角
thr_80 = np.percentile(iter_count[iter_count>0], 80)
high = iter_count >= thr_80
angles = np.arctan2(Y[high]-cy, X[high]-cx)
spread = np.percentile(np.abs(angles), 90)
SPREAD = min(spread * 1.5, math.radians(65))
print(f"  张角: ±{math.degrees(SPREAD):.0f}°")

# ============================================================
# 3. 映射 + 渲染
# ============================================================
print("[3/4] 映射 ...")

dist = np.sqrt((X-cx)**2 + (Y-cy)**2)
theta = np.arctan2(Y-cy, X-cx)
theta_rel = np.arctan2(np.sin(theta-out_angle), np.cos(theta-out_angle))

inside = np.abs(theta_rel) <= SPREAD

# r 范围
r_valid = dist[inside & (iter_count > 0)]
r_min = np.percentile(r_valid, 3)
r_max = np.percentile(r_valid, 95)
print(f"  r: [{r_min:.2f}, {r_max:.2f}]")

# ★ n(r)：用 D(p) 做非线性映射
# 不用亮度衰减，让行号本身的自然密度变化产生涟漪
r_norm = np.clip((dist - r_min) / (r_max - r_min + 1e-12), 0, 1)
n_float = (r_norm ** D) * (N_ROWS - 1)
n_idx = np.clip(n_float.astype(np.int64), 0, N_ROWS - 1)

# ★ k(theta)
k_frac = (theta_rel + SPREAD) / (2 * SPREAD)
k_frac = np.clip(k_frac, 0, 1)
k_val = (k_frac * n_idx.astype(np.float64)).astype(np.int64)
k_val = np.clip(k_val, 0, n_idx)

# 查表
valid = inside & (n_idx < N_ROWS) & (k_val <= n_idx) & (dist >= r_min)
brightness = np.zeros_like(dist, dtype=np.float64)
brightness[valid] = mask[n_idx[valid], k_val[valid]]

# 核点
brightness[dist < r_min * 0.9] = 1.0

print(f"  亮度: [{brightness.min():.3f}, {brightness.max():.3f}]")
print(f"  非零: {brightness.mean()*100:.1f}%")

# 验证各层
print("\n  涟漪层次（由内→外）:")
for i in range(6):
    r_lo = r_min + (r_max - r_min) * i / 6
    r_hi = r_min + (r_max - r_min) * (i + 1) / 6
    band = (dist >= r_lo) & (dist < r_hi)
    if band.any():
        b = brightness[band].mean()
        n_avg = int(n_float[band].mean())
        n_avg = min(n_avg, N_ROWS-1)
        d = row_density[n_avg]
        print(f"    r=[{r_lo:.2f},{r_hi:.2f}): 亮度={b:.4f}  n≈{n_avg:>3d}  "
              f"行密度={d*100:.1f}%")

# ============================================================
# 4. 着色 + 保存（每个图一个公式/功能）
# ============================================================
print("\n[4/4] 保存 ...")

# ---- A: 帕斯卡三角本身 ----
tri_show = np.zeros((N_ROWS, N_ROWS))
for n in range(min(N_ROWS, 256)):
    for k in range(n+1):
        tri_show[n, k] = mask[n, k]

fig, ax = plt.subplots(figsize=(10, 14), dpi=130)
ax.imshow(tri_show[:256], cmap='gray_r', interpolation='nearest',
          extent=[0, 256, 256, 0], aspect='auto')
ax.set_title(f"A. Pascal's Triangle mod {P}\n"
             f"Rows 0-255 | D={D:.3f}\n"
             f"C(n,k) mod P via Lucas theorem\n"
             f"Top=center → Bottom=outward",
             fontsize=13)
ax.set_xlabel("k (column)", fontsize=11)
ax.set_ylabel("n (row, growth ↓)", fontsize=11)
plt.tight_layout()
fig.savefig("/data/workspace/A_pascal.png", dpi=130)
plt.close(fig)
print("  ✓ A_pascal.png")

# ---- B: 行密度（涟漪来源）----
fig, ax = plt.subplots(figsize=(12, 6), dpi=130)
ax.semilogy(np.arange(N_ROWS), row_density, 'c-', linewidth=1)
# 标出"涟漪峰"（局部密度高）
from scipy.signal import find_peaks
peaks, _ = find_peaks(row_density, height=0.1, distance=8)
ax.scatter(peaks, row_density[peaks], color='yellow', zorder=5, s=20)
ax.set_title(f"B. Row Density (source of ripples)\n"
             f"mod {P} | peaks = bright ripple rings",
             fontsize=13)
ax.set_xlabel("n (row number, 0=center)", fontsize=11)
ax.set_ylabel("non-zero density (log)", fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig("/data/workspace/B_density.png", dpi=130)
plt.close(fig)
print("  ✓ B_density.png  (yellow dots = ripple peaks)")

# ---- C: n(r) 映射 ----
fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
r_s = np.linspace(0, 1, 500)
n_s = (r_s ** D) * (N_ROWS - 1)
ax.plot(r_s*(r_max-r_min)+r_min, n_s, 'y-', linewidth=2.5)
ax.fill_between(r_s*(r_max-r_min)+r_min, 0, n_s, alpha=0.15, color='yellow')
ax.set_title(f"C. n(r) mapping\n"
             f"n = ((r-r₀)/R)^{D:.3f} × {N_ROWS-1}\n"
             f"D(p) from Reiter Theorem 2",
             fontsize=13)
ax.set_xlabel("r (distance from nucleus)", fontsize=11)
ax.set_ylabel("n (Pascal row)", fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig("/data/workspace/C_mapping.png", dpi=130)
plt.close(fig)
print("  ✓ C_mapping.png")

# ---- D: 灰度渲染（纯 pascal 查表，无衰减）----
fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(np.clip(brightness,0,1),
          extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', cmap='gray_r', interpolation='bilinear')
ax.set_title(
    f"D. Pure Pascal Outward (gray)\n"
    f"brightness = pascal[n(r)][k(θ)]  (no attenuation)\n"
    f"p={P} | D={D:.3f} | {N_ROWS} rows",
    fontsize=14, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/D_gray.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ D_gray.png")

# ---- E: 蓝色调（参考图风格）----
b = np.clip(brightness, 0, 1)

# 核区：暖白
# 涟漪亮环：浅蓝
# 暗涟漪：深蓝
# 外圈：近黑深蓝

R = b * 0.10
G = b * 0.40
B = np.clip(b * 1.15, 0, 1)

# 核辉光
core_r = r_min + (r_max - r_min) * 0.06
cmask = dist < core_r
R = np.where(cmask, np.clip(R+0.7,0,1), R)
G = np.where(cmask, np.clip(G+0.6,0,1), G)
B = np.where(cmask, np.clip(B+0.3,0,1), B)

# 暗涟漪更蓝更饱和
dark_ripple = (b > 0.05) & (b < 0.3) & (~cmask)
R = np.where(dark_ripple, R*0.3, R)
G = np.where(dark_ripple, G*0.7, G)
B = np.where(dark_ripple, np.clip(B*1.15,0,1), B)

# 外圈压暗（只微微可见涟漪）
outer = dist > r_max * 0.85
fade = np.clip((dist[outer] - r_max*0.85) / (r_max*0.15 + 1e-9), 0, 1)
# 用广播
fade_map = np.clip((dist - r_max*0.85) / (r_max*0.15 + 1e-9), 0, 1)
R *= (1 - fade_map * 0.6)
G *= (1 - fade_map * 0.5)
B *= (1 - fade_map * 0.3)

img_blue = np.clip(np.stack([R,G,B],2), 0, 1)

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_blue, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"E. Pascal Ripple (blue tone)\n"
    f"b = pascal[n(r)][k(θ)] mod {P}\n"
    f"Ripples from row density variation | no artificial fade",
    fontsize=14, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/E_blue_ripple.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ E_blue_ripple.png")

# ---- F: 行号彩虹着色（看清涟漪层）----
# 每个 n 一个色相 → 不同颜色的涟漪环
hue_map = np.clip(n_idx / N_ROWS, 0, 1)

# 核黄
hue = 0.12 * np.clip(1 - dist/(r_min+(r_max-r_min)*0.04), 0, 1)
# 涟漪：红→橙→黄→绿→蓝→紫 随 n 增大
hue += (0.0 + 0.7 * hue_map) * np.clip(dist/(r_max*0.9), 0, 1)
hue = np.clip(hue, 0.0, 0.78)

sat = np.clip(0.2 + 0.8 * b, 0, 1)
val = np.clip(0.03 + 0.97 * b, 0, 1)
hsv = np.stack([hue, sat, val], 2)
img_rainbow = plt.cm.hsv(np.clip(hue_map, 0, 1))[:,:,:3]
# 乘上亮度
img_rainbow[:,:,0] *= b
img_rainbow[:,:,1] *= b
img_rainbow[:,:,2] *= b
img_rainbow = np.clip(img_rainbow, 0, 1)

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_rainbow, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"F. Row-Colored Ripples\n"
    f"Each color = one Pascal row n\n"
    f"Red=center rows → Violet=outer rows",
    fontsize=14, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/F_color_ripples.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ F_color_ripples.png")

# ---- G: 不同 p 对比 ----
# 快速生成 p=3,5 的小图
fig, axes = plt.subplots(1, 3, figsize=(36, 12), dpi=110)
for ax, p_test in zip(axes, [2, 3, 5]):
    Dt = math.log(p_test*(p_test+1)/2) / math.log(p_test)
    # 小三角
    NR = 256
    pt = np.zeros((NR, NR), dtype=np.int8)
    pt[0,0] = 1 % p_test
    for nn in range(1, NR):
        pt[nn,0] = pt[nn,nn] = 1 % p_test
        for kk in range(1, nn):
            pt[nn,kk] = (pt[nn-1,kk] + pt[nn-1,kk-1]) % p_test
    mt = (pt != 0).astype(np.float64)
    
    # 映射
    r_n = np.clip((dist - r_min) / (r_max - r_min + 1e-12), 0, 1)
    nf = (r_n ** Dt) * (NR - 1)
    ni = np.clip(nf.astype(np.int64), 0, NR-1)
    kf = np.clip((theta_rel + SPREAD)/(2*SPREAD), 0, 1)
    kv = np.clip((kf * ni.astype(np.float64)).astype(np.int64), 0, ni)
    v = inside & (ni < NR) & (kv <= ni) & (dist >= r_min)
    bt = np.zeros_like(dist, dtype=np.float64)
    bt[v] = mt[ni[v], kv[v]]
    bt[dist < r_min*0.9] = 1.0
    
    # 蓝调
    Rt = bt*0.1; Gt = bt*0.4; Bt = np.clip(bt*1.15,0,1)
    cm = dist < r_min+(r_max-r_min)*0.06
    Rt = np.where(cm, np.clip(Rt+0.7,0,1), Rt)
    Gt = np.where(cm, np.clip(Gt+0.6,0,1), Gt)
    Bt = np.where(cm, np.clip(Bt+0.3,0,1), Bt)
    imgt = np.clip(np.stack([Rt,Gt,Bt],2), 0, 1)
    
    ax.imshow(imgt, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
              origin='lower', interpolation='bilinear')
    ax.set_title(f"p={p_test}  D={Dt:.3f}\n"
                 f"Lucas mod {p_test} ripples",
                 fontsize=14, color='white')
    ax.set_xlabel("Re", fontsize=10, color='white')
    ax.tick_params(colors='white')

fig.patch.set_facecolor('black')
fig.suptitle("Pascal Ripples for different primes p",
             fontsize=16, color='white', y=1.01)
plt.tight_layout()
fig.savefig("/data/workspace/G_diff_p.png", dpi=110,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ G_diff_p.png  (p=2/3/5 对比)")

# ---- H: 总览 ----
fig, axes = plt.subplots(2, 4, figsize=(44, 24), dpi=100)
items = [
    (tri_show[:256], "A. Pascal mod P\ngrowth ↓", 'gray_r'),
    (None, "B. Density→Ripples\n(plot)", None),
    (np.clip(brightness,0,1), "D. Gray Outward\npure pascal lookup", 'gray_r'),
    (img_blue, "E. Blue Ripple\nreference style", None),
    (img_rainbow, "F. Color Ripples\nn=row number", None),
    (np.clip(brightness,0,1), "H. Inferno\nheat map", 'inferno'),
    (np.clip(brightness*1.3,0,1), "I. Contrast x1.3", 'gray_r'),
    (None, "G. p=2/3/5\n(see separate)", None),
]
for ax, (im, t, cm) in zip(axes.flat, items):
    if im is not None:
        if cm:
            ax.imshow(im, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
                      origin='lower', cmap=cm, interpolation='bilinear')
        else:
            ax.imshow(im, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
                      origin='lower', interpolation='bilinear')
    ax.set_title(t, fontsize=13, color='white')
    ax.set_xlabel("Re", fontsize=9, color='white')
    ax.tick_params(colors='white')

fig.patch.set_facecolor('black')
fig.suptitle(
    f"Inverse M · Pascal Triangle Outward Ripples\n"
    f"Mobius c'=1/c | p={P} | D={D:.3f} (Reiter Thm 2)\n"
    f"brightness = pascal[n(r)][k(θ)]  |  n = ((r-r₀)/R)^D·N  |  "
    f"k = (θ+φ)/(2φ)·n\n"
    f"No brightness attenuation — ripples come from row density variation",
    fontsize=14, color='white', y=1.005)
plt.tight_layout()
fig.savefig("/data/workspace/H_overview.png", dpi=100,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ H_overview.png")

# ---- 验证 ----
print("\n" + "=" * 60)
print("涟漪层次验证:")
for i in range(8):
    r_lo = r_min + (r_max - r_min) * i / 8
    r_hi = r_min + (r_max - r_min) * (i + 1) / 8
    band = (dist >= r_lo) & (dist < r_hi)
    if band.any():
        bb = brightness[band].mean()
        nn = min(int(n_float[band].mean()), N_ROWS-1)
        dd = row_density[nn]
        bar = '█' * int(bb * 40)
        print(f"  r={r_lo:.2f}-{r_hi:.2f}  n≈{nn:>3d}  ρ={dd*100:>5.1f}%  "
              f"b={bb:.3f}  {bar}")

c = brightness[dist < r_min+(r_max-r_min)*0.1].mean()
o = brightness[dist > r_max*0.7].mean()
print(f"\n  核={c:.3f}  外={o:.3f}  比值={c/max(o,1e-9):.1f}x")
print("=" * 60)

print("\nDone! Files:")
for f in ['A_pascal.png','B_density.png','C_mapping.png',
          'D_gray.png','E_blue_ripple.png','F_color_ripples.png',
          'G_diff_p.png','H_overview.png']:
    print(f"  {f}")
