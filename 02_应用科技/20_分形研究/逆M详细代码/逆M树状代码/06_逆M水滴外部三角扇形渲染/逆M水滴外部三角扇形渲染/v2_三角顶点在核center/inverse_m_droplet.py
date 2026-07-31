#!/usr/bin/env python3
"""
inverse_m_droplet.py
=====================
逆M水滴形状必须保留。方法：

  1. 正M迭代数据（Mobius翻转后）定义了水滴的"形状边界"
  2. 迭代次数 = 水滴的生长深度 = 帕斯卡三角的行号 n
  3. 帕斯卡三角 mod P 提供分形纹理
  4. 在水滴形状内部，用帕斯卡三角填充 → 水滴形状保留 + 分形纹理

关键：不用距离 r 做映射（那会丢掉水滴形状），
      而是直接用 iter_count 做行号 n（iter_count 本身就定义了水滴轮廓）

v2 修改 (2026-07-27):
  1. ★ 360°全方向映射原点改为 (0,0)，不用核中心 (cx,cy)
  2. ★ 全360°无张角限制: k = (θ+π)/(2π)·n
  3. ★ 保存路径改为 OUT_DIR（本地目录）
"""

import numpy as np
import matplotlib.pyplot as plt
import time, math, os
from math import comb
from scipy.signal import find_peaks

# ============================================================
# 参数
# ============================================================
P = 2
N_ROWS = 512
WIDTH, HEIGHT = 2400, 2400
MAX_ITER = 500
ESCAPE_RADIUS = 16.0
X_MIN, X_MAX = -3.0, 3.0
Y_MIN, Y_MAX = -1.5, 4.5

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

D = math.log(P*(P+1)/2) / math.log(P)
print(f"p={P}: D={D:.6f}  N_ROWS={N_ROWS}")

# ============================================================
# 1. 帕斯卡三角 mod P
# ============================================================
print("[1/5] 帕斯卡三角 mod P ...")
pascal = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
pascal[0, 0] = 1 % P
for n in range(1, N_ROWS):
    pascal[n, 0] = pascal[n, n] = 1 % P
    for k in range(1, n):
        pascal[n, k] = (pascal[n-1, k] + pascal[n-1, k-1]) % P
mask = (pascal != 0).astype(np.float64)
row_density = np.array([mask[n,:n+1].mean() for n in range(N_ROWS)])
print(f"  行密度: [{row_density.min():.4f}, {row_density.max():.4f}]")

# ============================================================
# 2. 复平面 + Mobius + 正M迭代
# ============================================================
print("[2/5] Mobius + 正M ...")
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

# 核
um = iter_count >= np.percentile(iter_count, 92)
cy = np.nanmean(np.where(um, Y, np.nan))
cx = np.nanmean(np.where(um, X, np.nan))
if math.isnan(cx): cx, cy = 0.0, 1.5
print(f"  核: ({cx:.2f}, {cy:.2f})")

# 水滴形状 = iter_count 的等高线
# 水滴内部 = iter_count 高的区域
# 水滴边界 = iter_count 快速下降的区域

# 水滴主轴方向
gy, gx = np.gradient(iter_count.astype(np.float64))
out_angle = math.atan2(np.nanmean(np.where(um, gy, np.nan)),
                       np.nanmean(np.where(um, gx, np.nan)))
print(f"  主轴: {math.degrees(out_angle):.0f}°")

# ============================================================
# 3. ★ 核心：用 iter_count 直接做帕斯卡行号 ★
#    360°全方向映射，原点在 (0,0)
# ============================================================
print("[3/5] iter_count → Pascal row ...")

# iter_count 本身 = 正M的逃逸时间 = 水滴的生长深度
# 高 iter_count = 水滴核（生长最慢 = 最稳定 = 三角顶部）
# 低 iter_count = 水滴边缘（逃逸快 = 三角底部）

# 归一化 iter_count → 行号 n
iter_valid = iter_count[iter_count > 0]
iter_min = np.percentile(iter_valid, 2)
iter_max = np.percentile(iter_valid, 98)
print(f"  iter范围: [{iter_min:.0f}, {iter_max:.0f}]")

# 反转：高iter→低n（核=三角顶部），低iter→高n（边缘=三角底部）
iter_norm = np.clip((iter_count - iter_min) / (iter_max - iter_min + 1e-12), 0, 1)
n_float = ((1 - iter_norm) ** D) * (N_ROWS - 1)
n_idx = np.clip(n_float.astype(np.int64), 0, N_ROWS - 1)

# 只对 iter_count > 0 的像素（水滴内部）做映射
inside_droplet = iter_count > 0

# ════════════════════════════════════════════════════════════
# ★ v2 修改：360°全方向映射，原点在 (0,0) ★
# ════════════════════════════════════════════════════════════
# 旧版：theta = arctan2(Y-cy, X-cx)  → 以核中心为原点
# 新版：theta = angle(C)             → 以 (0,0) 为原点
# 旧版：k = (θ_rel+SPREAD)/(2*SPREAD) * n  → 张角限制
# 新版：k = (θ+π)/(2π) * n                → 全360°无限制
# ════════════════════════════════════════════════════════════

# 角度直接用C的辐角（原点在0,0）
theta = np.angle(C)  # 范围 [-π, π]

# 全360°映射：k = (θ+π)/(2π) * n
# (θ+π)/(2π) 将 [-π, π] 映射到 [0, 1]，覆盖整行
k_frac = (theta + math.pi) / (2 * math.pi)
k_frac = np.clip(k_frac, 0, 1)
k_val = (k_frac * n_idx.astype(np.float64)).astype(np.int64)
k_val = np.clip(k_val, 0, n_idx)

# 查帕斯卡三角
valid = inside_droplet & (n_idx < N_ROWS) & (k_val <= n_idx)
brightness = np.zeros_like(iter_count, dtype=np.float64)
brightness[valid] = mask[n_idx[valid], k_val[valid]]

# 水滴外部 = 0（黑色背景）
brightness[~inside_droplet] = 0

# 核区强制亮
core_mask = (iter_count >= np.percentile(iter_count[iter_count>0], 97))
brightness[core_mask] = 1.0

print(f"  亮度: [{brightness.min():.3f}, {brightness.max():.3f}]")
print(f"  水滴内非零: {brightness[inside_droplet].mean()*100:.1f}%")

# ============================================================
# 4. 验证水滴形状 + 涟漪
# ============================================================
print("[4/5] 验证 ...")

# 水滴形状验证
print(f"  水滴范围:")
print(f"    x: [{X[inside_droplet].min():.2f}, {X[inside_droplet].max():.2f}]")
print(f"    y: [{Y[inside_droplet].min():.2f}, {Y[inside_droplet].max():.2f}]")
print(f"    核: ({cx:.2f}, {cy:.2f})")

# 涟漪层次（沿主轴方向）
print(f"\n  沿主轴涟漪:")
# 主轴方向向量
dx = math.cos(out_angle)
dy = math.sin(out_angle)
proj = (X-cx)*dx + (Y-cy)*dy  # 沿主轴投影
proj_valid = proj[inside_droplet]
p_min = np.percentile(proj_valid, 5)
p_max = np.percentile(proj_valid, 95)
for i in range(8):
    p_lo = p_min + (p_max - p_min) * i / 8
    p_hi = p_min + (p_max - p_min) * (i + 1) / 8
    band = inside_droplet & (proj >= p_lo) & (proj < p_hi)
    if band.any():
        b = brightness[band].mean()
        n_avg = int(n_float[band].mean())
        n_avg = min(n_avg, N_ROWS-1)
        d = row_density[n_avg]
        bar = '█' * int(b * 40)
        print(f"    p={p_lo:.2f}-{p_hi:.2f}  n≈{n_avg:>3d}  ρ={d*100:>5.1f}%  "
              f"b={b:.3f}  {bar}")

# ============================================================
# 5. 保存（每个功能/公式独立出图）
# ============================================================
print("\n[5/5] 保存 ...")

# ---- A: 帕斯卡三角本身 ----
tri = np.zeros((256, 256))
for n in range(256):
    for k in range(n+1):
        tri[n, k] = mask[n, k]

fig, ax = plt.subplots(figsize=(10, 14), dpi=130)
ax.imshow(tri, cmap='gray_r', interpolation='nearest',
          extent=[0, 256, 256, 0], aspect='auto')
ax.set_title(f"A. Pascal mod {P} (rows 0-255)\n"
             f"C(n,k) mod P | D={D:.3f}\n"
             f"Top row = nucleus", fontsize=13)
ax.set_xlabel("k", fontsize=11); ax.set_ylabel("n ↓", fontsize=11)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "A_pascal.png"), dpi=130); plt.close(fig)
print("  ✓ A_pascal.png")

# ---- B: iter_count 分布（水滴形状）----
fig, ax = plt.subplots(figsize=(14, 14), dpi=130)
im = ax.imshow(iter_count, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
               origin='lower', cmap='inferno', interpolation='bilinear')
ax.set_title("B. iter_count (defines droplet shape)\n"
             "High = nucleus | Low = edge",
             fontsize=13, color='white')
ax.set_xlabel("Re", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.colorbar(im, ax=ax, shrink=0.8)
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "B_iter_shape.png"), dpi=130, facecolor='black')
plt.close(fig)
print("  ✓ B_iter_shape.png")

# ---- C: iter → n 映射 ----
fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
# 采样沿主轴方向
proj_sample = np.linspace(p_min, p_max, 500)
iter_sample = np.clip(iter_max - (proj_sample - p_min)/(p_max-p_min)*(iter_max-iter_min), 0, MAX_ITER)
n_sample = ((1 - np.clip((iter_sample-iter_min)/(iter_max-iter_min+1e-12),0,1)) ** D) * (N_ROWS-1)
ax.plot(proj_sample, n_sample, 'y-', linewidth=2.5)
ax.set_title(f"C. iter → n mapping\n"
             f"n = (1 − (iter−imin)/(imax−imin))^{D:.3f} × {N_ROWS-1}\n"
             f"High iter (nucleus) → low n (triangle top)",
             fontsize=12)
ax.set_xlabel("position along droplet axis", fontsize=10)
ax.set_ylabel("n (Pascal row)", fontsize=10)
ax.set_ylabel("n (Pascal row)", fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "C_iter_to_n.png"), dpi=130); plt.close(fig)
print("  ✓ C_iter_to_n.png")

# ---- D: 水滴形状 + 帕斯卡纹理（灰度）----
fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(np.clip(brightness,0,1),
          extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', cmap='gray_r', interpolation='bilinear')
ax.set_title(
    f"D. Inverse M Droplet + Pascal Texture (gray)\n"
    f"Shape from iter_count | Texture from pascal[n][k] mod {P}\n"
    f"n = f(iter_count) | k = f(θ) | D={D:.3f}",
    fontsize=13, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "D_droplet_gray.png"), dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ D_droplet_gray.png")

# ---- E: 蓝色调（参考图风格）----
b = np.clip(brightness, 0, 1)

# 基础蓝色调
R = b * 0.08
G = b * 0.35
Bc = np.clip(b * 1.20, 0, 1)

# 核区暖白
cm = iter_count >= np.percentile(iter_count[iter_count>0], 96)
R = np.where(cm, np.clip(R+0.72,0,1), R)
G = np.where(cm, np.clip(G+0.62,0,1), G)
Bc = np.where(cm, np.clip(Bc+0.35,0,1), Bc)

# 暗涟漪（低密度行）→ 深蓝
dark_r = (b > 0.02) & (b < 0.25) & (~cm)
R = np.where(dark_r, R*0.2, R)
G = np.where(dark_r, G*0.6, G)
Bc = np.where(dark_r, np.clip(Bc*1.2,0,1), Bc)

# 亮涟漪（高密度行）→ 青蓝
bright_r = (b >= 0.5) & (~cm)
R = np.where(bright_r, R*0.3, R)
G = np.where(bright_r, np.clip(G*1.2,0,1), G)
Bc = np.where(bright_r, np.clip(Bc*0.9,0,1), Bc)

# 水滴边缘光晕（iter_count 快速下降处）
edge = (iter_count > 0) & (iter_count < np.percentile(iter_count[iter_count>0], 15))
R = np.where(edge, np.clip(R+0.15,0,1), R)
G = np.where(edge, np.clip(G+0.25,0,1), G)
Bc = np.where(edge, np.clip(Bc+0.45,0,1), Bc)

img_blue = np.clip(np.stack([R,G,Bc],2), 0, 1)

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_blue, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"E. Inverse M Droplet · Pascal Ripples (blue)\n"
    f"Mobius c'=1/c | Lucas mod {P} | D={D:.3f}\n"
    f"Droplet shape preserved | Pascal texture inside",
    fontsize=13, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "E_droplet_blue.png"), dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ E_droplet_blue.png  ← 主图")

# ---- F: 行号着色（看清涟漪层）----
# 用 n_idx 做色相
n_vis = np.clip(n_idx / N_ROWS, 0, 1)
# 核区黄白
hue = 0.12 * np.clip(iter_count / np.percentile(iter_count[iter_count>0], 95), 0, 1)
# 往外：红→橙→黄→绿→蓝→紫
hue += 0.7 * n_vis * np.clip(iter_count / iter_max, 0, 1)
hue = np.clip(hue, 0, 0.78)
sat = np.clip(0.2 + 0.8*b, 0, 1)
val = np.clip(0.02 + 0.98*b, 0, 1)
img_hsv = plt.cm.hsv(np.clip(n_vis * np.clip(b*2,0,1), 0, 1))[:,:,:3]

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_hsv, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"F. Row-Colored Ripples\n"
    f"Color = Pascal row n | Bright = pascal[n][k]\n"
    f"Each color band = one ripple",
    fontsize=13, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "F_color_ripples.png"), dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ F_color_ripples.png")

# ---- G: 不同素数对比 ----
fig, axes = plt.subplots(1, 3, figsize=(36, 12), dpi=110)
for ax, p_t in zip(axes, [2, 3, 5]):
    Dt = math.log(p_t*(p_t+1)/2) / math.log(p_t)
    NR = 300
    pt = np.zeros((NR, NR), dtype=np.int8)
    pt[0,0] = 1 % p_t
    for nn in range(1, NR):
        pt[nn,0] = pt[nn,nn] = 1 % p_t
        for kk in range(1, nn):
            pt[nn,kk] = (pt[nn-1,kk] + pt[nn-1,kk-1]) % p_t
    mt = (pt != 0).astype(np.float64)
    
    # ★ v2: iter_count → n
    it_n = np.clip((iter_count - iter_min) / (iter_max - iter_min + 1e-12), 0, 1)
    nf = ((1 - it_n) ** Dt) * (NR - 1)
    ni = np.clip(nf.astype(np.int64), 0, NR-1)
    
    # ★ v2: theta → k, 全360°映射, 原点(0,0)
    kf = (theta + math.pi) / (2 * math.pi)  # [0, 1], 无张角限制
    kv = np.clip((kf * ni.astype(np.float64)).astype(np.int64), 0, ni)
    
    vt = inside_droplet & (ni < NR) & (kv <= ni)
    bt = np.zeros_like(iter_count, dtype=np.float64)
    bt[vt] = mt[ni[vt], kv[vt]]
    bt[~inside_droplet] = 0
    bt[iter_count >= np.percentile(iter_count[iter_count>0], 97)] = 1.0
    
    # 蓝调
    Rt = bt*0.08; Gt = bt*0.35; Bt = np.clip(bt*1.2,0,1)
    cmt = iter_count >= np.percentile(iter_count[iter_count>0], 96)
    Rt = np.where(cmt, np.clip(Rt+0.72,0,1), Rt)
    Gt = np.where(cmt, np.clip(Gt+0.62,0,1), Gt)
    Bt = np.where(cmt, np.clip(Bt+0.35,0,1), Bt)
    imgt = np.clip(np.stack([Rt,Gt,Bt],2), 0, 1)
    
    ax.imshow(imgt, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
              origin='lower', interpolation='bilinear')
    ax.set_title(f"p={p_t}  D={Dt:.3f}\nLucas mod {p_t}",
                 fontsize=14, color='white')
    ax.set_xlabel("Re", fontsize=10, color='white')
    ax.tick_params(colors='white')

fig.patch.set_facecolor('black')
fig.suptitle("Droplet shape preserved | Different primes p",
             fontsize=15, color='white', y=1.01)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "G_diff_p.png"), dpi=110,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ G_diff_p.png")

# ---- H: 总览 ----
fig, axes = plt.subplots(2, 4, figsize=(44, 24), dpi=100)
all_imgs = [
    (tri, "A. Pascal mod P\ngrowth ↓", 'gray_r'),
    (np.clip(iter_count/MAX_ITER,0,1), "B. iter_count\ndroplet shape", 'inferno'),
    (np.clip(brightness,0,1), "D. Gray\npascal lookup", 'gray_r'),
    (img_blue, "E. Blue ripple\nMAIN", None),
    (img_hsv, "F. Color ripples\nn=row", None),
    (np.clip(brightness,0,1), "H. Inferno", 'inferno'),
    (tri, "I. Pascal closeup\ntop 64 rows", 'gray_r'),
    (np.clip(brightness*1.2,0,1), "J. Contrast x1.2", 'gray_r'),
]
for ax, (im, t, cm) in zip(axes.flat, all_imgs):
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
    f"Inverse M Droplet · Pascal Outward Ripples\n"
    f"Mobius c'=1/c | p={P} | D={D:.3f} (Reiter Thm 2)\n"
    f"Shape = iter_count (preserved) | Texture = pascal[n(iter)][k(θ)]\n"
    f"n = (1−(iter−imin)/(imax−imin))^D · N  |  k = (θ+π)/(2π)·n",
    fontsize=14, color='white', y=1.005)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "H_overview.png"), dpi=100,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ H_overview.png")

# ---- 公式文件 ----
formulas = f"""
┌────────────────────────────────────────────────────────────────────────┐
│ 公式 → 图 对照                                                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ① C(n,k) = C(n-1,k) + C(n-1,k-1) mod P                              │
│     Yang Hui recurrence → A_pascal.png                                 │
│                                                                        │
│  ② iter_count = 正M逃逸时间(z=z²+c', c'=1/c)                          │
│     Defines droplet shape → B_iter_shape.png                           │
│                                                                        │
│  ③ D(p) = ln[p(p+1)/2] / ln(p) = {D:.3f}                             │
│     Reiter Theorem 2 → used in mapping                                 │
│                                                                        │
│  ④ n(iter) = (1 − (iter−imin)/(imax−imin))^D · (N−1)                 │
│     Maps escape time → Pascal row → C_iter_to_n.png                    │
│     High iter (nucleus) → low n (triangle top, dense)                 │
│     Low iter (edge) → high n (triangle bottom, sparse)                 │
│                                                                        │
│  ⑤ ★ 360° 全方向映射, 原点 (0,0) ★                                    │
│     k = (θ+π)/(2π) · n   (无张角限制)                                  │
│     → D_droplet_gray.png (shape preserved, origin=0,0)                 │
│                                                                        │
│  ⑥ brightness = pascal[ n(iter) ][ k(θ) ]                            │
│     Lookup only, no multiplication                                    │
│     → D_droplet_gray.png (shape preserved)                            │
│     → E_droplet_blue.png (reference style)                            │
│                                                                        │
│  ⑦ Color = n mod colormap → F_color_ripples.png                       │
│     Each color band = one Pascal row = one ripple                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
"""
with open(os.path.join(OUT_DIR, "formulas.txt"), "w") as f:
    f.write(formulas)
print(formulas)

print("\nDone!")
