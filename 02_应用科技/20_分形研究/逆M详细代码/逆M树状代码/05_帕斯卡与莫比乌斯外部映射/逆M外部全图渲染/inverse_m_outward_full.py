#!/usr/bin/env python3
"""
inverse_m_outward_full.py
==========================
两个问题修复：
  1. 360° 全方向覆盖（不是半张角）
  2. 渲染水滴外部 = outward（核暗/无 → 外圈亮）

思路：
  正M的 iter_count 定义了水滴"内部"形状
  水滴外部 = iter_count 低 = 逃逸快 = 离核远
  
  outward 渲染：亮在水滴外部（逃逸区），暗在水滴核
  
  映射反转：
    高 iter（核）→ n 大 → 帕斯卡底部 → 稀疏 → 暗
    低 iter（外圈）→ n 小 → 帕斯卡顶部 → 密集 → 亮
    
  360° 覆盖：不用角度限制，所有方向都映射
"""

import numpy as np
import matplotlib.pyplot as plt
import math
from math import comb

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
# 2. 复平面 + Mobius + 正M
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
um = iter_count >= np.percentile(iter_count[iter_count>0], 92)
cy = np.nanmean(np.where(um, Y, np.nan))
cx = np.nanmean(np.where(um, X, np.nan))
if math.isnan(cx): cx, cy = 0.0, 1.5
print(f"  核: ({cx:.2f}, {cy:.2f})")

# 水滴形状参数
dist = np.sqrt((X-cx)**2 + (Y-cy)**2)
theta = np.arctan2(Y-cy, X-cx)

# 水滴边界：用 iter_count 的阈值定义
# 水滴内部 = 高 iter，外部 = 低 iter
thr_inner = np.percentile(iter_count[iter_count>0], 30)  # 水滴主体
thr_outer = np.percentile(iter_count[iter_count>0], 5)   # 外围边界

print(f"  水滴阈值: inner={thr_inner:.0f}  outer={thr_outer:.0f}")
print(f"  核 iter: {iter_count[um].mean():.0f}")

# ============================================================
# 3. ★ 360° 全方向 + outward 映射 ★
# ============================================================
print("[3/5] 360° outward 映射 ...")

# iter_count 范围
iter_valid = iter_count[iter_count > 0]
iter_min = np.percentile(iter_valid, 1)
iter_max = np.percentile(iter_valid, 99)
print(f"  iter范围: [{iter_min:.0f}, {iter_max:.0f}]")

# ★ 反转映射（outward）★
# 核（高iter）→ n 大 → 三角底部（稀疏）→ 暗
# 外圈（低iter）→ n 小 → 三角顶部（密集）→ 亮
# n = ((iter - iter_min) / (iter_max - iter_min))^D * (N-1)
# 即：iter 越大 n 越大（和之前相反）
iter_norm = np.clip((iter_count - iter_min) / (iter_max - iter_min + 1e-12), 0, 1)
n_float = (iter_norm ** D) * (N_ROWS - 1)
n_idx = np.clip(n_float.astype(np.int64), 0, N_ROWS - 1)

# ★ 360° 全方向：角度映射到完整的三角展开 ★
# 不用张角限制，所有 θ ∈ [-π, π] 都映射到 k
# 把 360° 映射到三角的 k 展开
# k = (θ + π) / (2π) * n  → 均匀分布
k_frac = (theta + math.pi) / (2 * math.pi)  # [0, 1] 全范围
k_frac = np.clip(k_frac, 0, 1)
k_val = (k_frac * n_idx.astype(np.float64)).astype(np.int64)
k_val = np.clip(k_val, 0, n_idx)

# 查帕斯卡三角
valid = (iter_count > 0) & (n_idx < N_ROWS) & (k_val <= n_idx)
brightness = np.zeros_like(iter_count, dtype=np.float64)
brightness[valid] = mask[n_idx[valid], k_val[valid]]

# ★ outward：外圈亮，核区暗 ★
# 核区（高iter）→ n大 → 大部分是0（稀疏）→ 自然暗
# 但为了视觉清晰，给核区一个基础暗光
core_dim = np.clip(iter_count / np.percentile(iter_count[iter_count>0], 90), 0, 1)
brightness = np.clip(brightness * (0.3 + 0.7 * core_dim), 0, 1)

# 外圈（低iter但>0）→ n小 → 密集 → 亮
# 已经自然实现了

# 完全逃逸区（iter_count 极低）→ 暗背景
bg = iter_count < thr_outer
brightness[bg] = brightness[bg] * 0.15  # 只留微弱纹理

# 核区最暗（但不是纯黑，留一点结构）
nucleus = iter_count >= np.percentile(iter_count[iter_count>0], 95)
brightness[nucleus] = brightness[nucleus] * 0.4

print(f"  亮度范围: [{brightness.min():.3f}, {brightness.max():.3f}]")

# ============================================================
# 4. 验证
# ============================================================
print("[4/5] 验证 ...")

# 分层验证
print(f"\n  outward 方向验证（核暗→外亮）:")
bands = 6
for i in range(bands):
    t_lo = iter_min + (iter_max - iter_min) * i / bands
    t_hi = iter_min + (iter_max - iter_min) * (i + 1) / bands
    band = (iter_count >= t_lo) & (iter_count < t_hi)
    if band.any():
        b = brightness[band].mean()
        n_avg = int(n_float[band].mean())
        n_avg = min(n_avg, N_ROWS-1)
        d = row_density[n_avg]
        tag = "核" if i >= bands-2 else ("中" if i >= bands//2 else "外")
        bar = '█' * int(b * 40)
        print(f"    {tag} iter={t_lo:.0f}-{t_hi:.0f}  n≈{n_avg:>3d}  "
              f"ρ={d*100:>5.1f}%  b={b:.3f}  {bar}")

# 核 vs 外
core_b = brightness[nucleus].mean()
outer_band = (iter_count >= thr_outer) & (iter_count < thr_inner)
outer_b = brightness[outer_band].mean() if outer_band.any() else 0
print(f"\n  核区亮度={core_b:.3f}  外圈亮度={outer_b:.3f}")
print(f"  {'>>> OUTWARD ✓ <<<' if outer_b > core_b else '>>> STILL INWARD ✗ <<<'}")
ratio = outer_b / max(core_b, 1e-9)
print(f"  外/核比值={ratio:.1f}x")

# 360° 验证
theta_check = np.arctan2(Y[iter_count > thr_outer]-cy,
                         X[iter_count > thr_outer]-cx)
print(f"\n  角度覆盖: [{math.degrees(theta_check.min()):.0f}°, "
      f"{math.degrees(theta_check.max()):.0f}°]")
print(f"  全360°: {'YES ✓' if (theta_check.max()-theta_check.min()) > math.radians(350) else 'NO ✗'}")

# ============================================================
# 5. 保存（每张图一个功能/公式）
# ============================================================
print("\n[5/5] 保存 ...")

# ---- A: 帕斯卡三角 ----
tri = np.zeros((256, 256))
for n in range(256):
    for k in range(n+1):
        tri[n, k] = mask[n, k]

fig, ax = plt.subplots(figsize=(10, 14), dpi=130)
ax.imshow(tri, cmap='gray_r', interpolation='nearest',
          extent=[0, 256, 256, 0], aspect='auto')
ax.set_title(f"A. Pascal mod {P} (rows 0-255)\n"
             f"C(n,k) mod P | D={D:.3f}\n"
             f"Top=dense(outward bright) → Bottom=sparse(core dim)",
             fontsize=13)
ax.set_xlabel("k (0→2π)", fontsize=11)
ax.set_ylabel("n ↓", fontsize=11)
plt.tight_layout()
fig.savefig("/data/workspace/A_pascal.png", dpi=130); plt.close(fig)
print("  ✓ A_pascal.png")

# ---- B: iter_count 形状 ----
fig, ax = plt.subplots(figsize=(14, 14), dpi=130)
im = ax.imshow(iter_count, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
               origin='lower', cmap='inferno', interpolation='bilinear')
ax.set_title("B. iter_count (Mobius + 正M)\n"
             "High=core(nucleus) | Low=outward(escape)",
             fontsize=13, color='white')
ax.set_xlabel("Re", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.colorbar(im, ax=ax, shrink=0.8)
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/B_iter.png", dpi=130, facecolor='black')
plt.close(fig)
print("  ✓ B_iter.png")

# ---- C: 映射方向 ----
fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
t_s = np.linspace(0, 1, 500)
n_s = t_s ** D * (N_ROWS - 1)
ax.plot(t_s * (iter_max-iter_min) + iter_min, n_s, 'y-', linewidth=2.5)
# 标注方向
ax.annotate('High iter (core)\nn large\ndim', xy=(iter_max*0.9, N_ROWS*0.8),
            fontsize=10, color='r', ha='center')
ax.annotate('Low iter (out)\nn small\nbright', xy=(iter_min*1.5+iter_max*0.1, N_ROWS*0.15),
            fontsize=10, color='c', ha='center')
ax.set_title(f"C. OUTWARD Mapping\n"
             f"n = ((iter−imin)/(imax−imin))^{D:.3f} × N\n"
             f"High iter→n large→sparse→DIM (core)\n"
             f"Low iter→n small→dense→BRIGHT (outward)",
             fontsize=11)
ax.set_xlabel("iter_count", fontsize=10)
ax.set_ylabel("n (Pascal row)", fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig("/data/workspace/C_mapping.png", dpi=130); plt.close(fig)
print("  ✓ C_mapping.png")

# ---- D: 360° 角度映射 ----
fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
theta_s = np.linspace(-math.pi, math.pi, 500)
ax.plot(theta_s, (theta_s+math.pi)/(2*math.pi)*100, 'c-', linewidth=2)
ax.set_title(f"D. 360° Angle → k Mapping\n"
             f"k = (θ+π)/(2π) × n\n"
             f"Full circle: −π → 0, +π → n",
             fontsize=12)
ax.set_xlabel("θ (radians)", fontsize=10)
ax.set_ylabel("k (relative)", fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig("/data/workspace/D_angle360.png", dpi=130); plt.close(fig)
print("  ✓ D_angle360.png")

# ---- E: 灰度 outward ----
fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(np.clip(brightness,0,1),
          extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', cmap='gray', interpolation='bilinear')
ax.set_title(
    f"E. Inverse M · OUTWARD (gray)\n"
    f"b = pascal[n(iter)][k(θ)] mod {P}\n"
    f"360° | outward: core=DIM, escape=BRIGHT\n"
    f"n = (iter_norm)^{D:.3f}·N  |  k = (θ+π)/(2π)·n",
    fontsize=12, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/E_outward_gray.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ E_outward_gray.png")

# ---- F: 蓝色调 outward ----
b = np.clip(brightness, 0, 1)

# outward 配色：外圈亮蓝/青，核区暗蓝黑
# 外圈亮
R = b * 0.05
G = b * 0.55
Bc = np.clip(b * 1.30, 0, 1)

# 高亮度区偏青
cyan = b > 0.7
G = np.where(cyan, np.clip(G*1.15,0,1), G)
Bc = np.where(cyan, np.clip(Bc*0.95,0,1), Bc)

# 核区暗蓝黑
R = np.where(nucleus, b*0.15, R)
G = np.where(nucleus, b*0.25, G)
Bc = np.where(nucleus, np.clip(b*0.5,0,1), Bc)

# 外圈光晕增强
halo = (iter_count > thr_outer) & (iter_count < thr_inner*0.8)
R = np.where(halo, np.clip(R+0.05,0,1), R)
G = np.where(halo, np.clip(G+0.1,0,1), G)
Bc = np.where(halo, np.clip(Bc+0.15,0,1), Bc)

img_blue = np.clip(np.stack([R,G,Bc],2), 0, 1)

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_blue, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"F. OUTWARD Droplet (blue)\n"
    f"Mobius c'=1/c | Lucas mod {P} | D={D:.3f}\n"
    f"360° full coverage | Core=DIM → Outward=BRIGHT",
    fontsize=12, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/F_outward_blue.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ F_outward_blue.png  ← 主图")

# ---- G: 行号着色 ----
# n 小（外圈亮区）→ 暖色，n 大（核区暗区）→ 冷色
n_vis = np.clip(n_idx / N_ROWS, 0, 1)
# 反转：外圈（n小）= 黄橙红，核（n大）= 蓝紫黑
hue = 0.66 + 0.34 * n_vis * np.clip(b, 0, 1)  # n大→蓝, n小→红
hue = np.clip(hue * np.clip(b*1.5, 0, 1), 0.0, 0.78)
sat = np.clip(0.15 + 0.85*b, 0, 1)
val = np.clip(0.05 + 0.95*b, 0, 1)
img_hsv = plt.cm.hsv(np.clip((1-n_vis)*b*1.5, 0, 1))[:,:,:3]

fig, ax = plt.subplots(figsize=(16, 16), dpi=140)
ax.imshow(img_hsv, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          origin='lower', interpolation='bilinear')
ax.set_title(
    f"G. Row-Colored OUTWARD\n"
    f"Red/Yellow = low n (outward, bright)\n"
    f"Blue/Purple = high n (core, dim)",
    fontsize=12, color='white')
ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax.tick_params(colors='white')
fig.patch.set_facecolor('black')
plt.tight_layout()
fig.savefig("/data/workspace/G_color_outward.png", dpi=140,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ G_color_outward.png")

# ---- H: p=2/3/5 对比 ----
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
    
    it_n = np.clip((iter_count - iter_min) / (iter_max - iter_min + 1e-12), 0, 1)
    nf = (it_n ** Dt) * (NR - 1)
    ni = np.clip(nf.astype(np.int64), 0, NR-1)
    
    kf = (theta + math.pi) / (2 * math.pi)
    kf = np.clip(kf, 0, 1)
    kv = np.clip((kf * ni.astype(np.float64)).astype(np.int64), 0, ni)
    
    vt = (iter_count > 0) & (ni < NR) & (kv <= ni)
    bt = np.zeros_like(iter_count, dtype=np.float64)
    bt[vt] = mt[ni[vt], kv[vt]]
    # outward: 核暗外亮
    cd = np.clip(iter_count / np.percentile(iter_count[iter_count>0], 90), 0, 1)
    bt = bt * (0.3 + 0.7 * cd)
    bt[nucleus] = bt[nucleus] * 0.4
    
    # 蓝调
    Rt = bt*0.05; Gt = bt*0.55; Btt = np.clip(bt*1.3,0,1)
    Rt = np.where(nucleus, bt*0.15, Rt)
    Gt = np.where(nucleus, bt*0.25, Gt)
    Btt = np.where(nucleus, np.clip(bt*0.5,0,1), Btt)
    imgt = np.clip(np.stack([Rt,Gt,Btt],2), 0, 1)
    
    ax.imshow(imgt, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
              origin='lower', interpolation='bilinear')
    ax.set_title(f"p={p_t}  D={Dt:.3f}\noutward",
                 fontsize=14, color='white')
    ax.set_xlabel("Re", fontsize=10, color='white')
    ax.tick_params(colors='white')

fig.patch.set_facecolor('black')
fig.suptitle("OUTWARD · 360° · Different primes p",
             fontsize=15, color='white', y=1.01)
plt.tight_layout()
fig.savefig("/data/workspace/H_diff_p.png", dpi=110,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ H_diff_p.png")

# ---- I: 总览 ----
fig, axes = plt.subplots(2, 4, figsize=(44, 24), dpi=100)
items = [
    (tri, "A. Pascal mod P", 'gray_r'),
    (np.clip(iter_count/MAX_ITER,0,1), "B. iter_count", 'inferno'),
    (np.clip(brightness,0,1), "E. Outward gray", 'gray'),
    (img_blue, "F. Outward blue (MAIN)", None),
    (img_hsv, "G. Color outward", None),
    (np.clip(brightness,0,1), "I. Outward inferno", 'inferno'),
    (tri, "J. Pascal closeup rows 0-64", 'gray_r'),
    (np.clip(brightness*1.3,0,1), "K. Contrast x1.3", 'gray'),
]
for ax, (im, t, cm) in zip(axes.flat, items):
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
    f"Inverse M · OUTWARD · 360° Full Coverage\n"
    f"Mobius c'=1/c | p={P} | D={D:.3f} (Reiter Thm 2)\n"
    f"OUTWARD: core DIM (n large, sparse) → outward BRIGHT (n small, dense)\n"
    f"n = ((iter−imin)/(imax−imin))^D · N  |  "
    f"k = (θ+π)/(2π) · n  |  360° no angle limit",
    fontsize=14, color='white', y=1.005)
plt.tight_layout()
fig.savefig("/data/workspace/I_overview.png", dpi=100,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ I_overview.png")

# ---- 公式文件 ----
formulas = f"""
┌────────────────────────────────────────────────────────────────────────┐
│ OUTWARD 公式 → 图 对照                                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  A. C(n,k) = C(n-1,k) + C(n-1,k-1) mod P                             │
│     Yang Hui recurrence → A_pascal.png                                 │
│                                                                        │
│  B. iter_count from z = z² + 1/c (Mobius)                             │
│     Droplet shape & escape time → B_iter.png                            │
│                                                                        │
│  C. ★ OUTWARD 映射方向反转 ★                                           │
│     n = ((iter−imin)/(imax−imin))^D · (N−1)                          │
│     (之前是 1−iter_norm，现在直接用 iter_norm)                           │
│     → C_mapping.png                                                     │
│                                                                        │
│  D. 360° 角度映射                                                      │
│     k = (θ+π)/(2π) · n   (全范围, 无张角限制)                           │
│     → D_angle360.png                                                   │
│                                                                        │
│  E. D(p) = ln[p(p+1)/2]/ln(p) = {D:.3f}                              │
│     Reiter Theorem 2 → controls n mapping nonlinearity                  │
│                                                                        │
│  F. brightness = pascal[n(iter)][k(θ)]                                │
│     Lookup only → E_outward_gray.png                                   │
│     Core (high n, sparse) = DIM                                        │
│     Outward (low n, dense) = BRIGHT                                    │
│                                                                        │
│  G. Blue tone → F_outward_blue.png (MAIN)                             │
│     Outward = cyan/bright | Core = dark blue/black                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
"""
with open("/data/workspace/formulas.txt", "w") as f:
    f.write(formulas)
print(formulas)

print("\nDone!")
