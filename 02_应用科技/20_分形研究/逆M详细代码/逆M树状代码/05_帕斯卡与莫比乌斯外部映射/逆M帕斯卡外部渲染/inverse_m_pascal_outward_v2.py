#!/usr/bin/env python3
"""
inverse_m_pascal_outward_v2.py
=================================
逆 M 水滴 · 朝外渲染  v2（修复数值稳定性 + 增强水滴结构）

改进点 v2
---------
1. 初始值 z=0，迭代 z←z²+1/c（标准逆M定义，水滴更标准）
2. 逃逸半径 100.0（足够大，保证 log(log(|z|)) 始终有定义）
3. 对数平滑做安全裁剪，消除 RuntimeWarning
4. Reiter D(p) 朝外映射保留，新增"反向归一化"模式开关
   outward_mode:
     'power'  - val^(1/D)    高维向外喷射（默认）
     'linear' - val * D       线性加权
     'exp'    - exp(val*D)/e  指数辐射
5. 新增内晕染（glow）通道：在水滴边缘叠加高斯模糊的光晕
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from scipy.ndimage import gaussian_filter
import time, math

# ============================================================
# 0. 参数区
# ============================================================
WIDTH, HEIGHT   = 1800, 1350
MAX_ITER        = 500
ESCAPE_RADIUS   = 100.0        # |z| > 100 才判定逃逸
PRIMES          = [2, 3, 5]
K_DIM           = 2
OUTWARD_MODE    = 'power'      # 'power' | 'linear' | 'exp'
GLOW_SIGMA      = 4.0          # 光晕模糊半径（像素）

X_MIN, X_MAX    = -3.0, 3.0
Y_MIN, Y_MAX    = -1.5, 4.5

# ============================================================
# 1. Reiter 公式
# ============================================================
def reiter_dimension(p):
    return math.log(p * (p + 1) / 2) / math.log(p)

def reiter_multinomial_dimension(p, k):
    from math import comb
    return math.log(comb(p - 1 + k, k)) / math.log(p)

def lucas_nonzero(n, k, p):
    """Lucas 定理：C(n,k) mod p != 0 的充要条件"""
    while n > 0 or k > 0:
        if (k % p) > (n % p):
            return False
        n //= p
        k //= p
    return True

D_vals = {p: reiter_dimension(p) for p in PRIMES}
Dk_vals = {p: reiter_multinomial_dimension(p, K_DIM) for p in PRIMES}

print("=" * 60)
print("Reiter 分形维数表")
print("-" * 60)
for p in PRIMES:
    print(f"  p={p}: D={D_vals[p]:.6f}  D_k(k={K_DIM})={Dk_vals[p]:.6f}")
print(f"  朝外模式 = {OUTWARD_MODE}")
print("=" * 60)

# ============================================================
# 2. 复平面 + 坐标旋转
# ============================================================
print("\n[1/6] 复平面网格 ...")
t0 = time.time()
xs = np.linspace(X_MIN, X_MAX, WIDTH, dtype=np.float64)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT, dtype=np.float64)
X, Y = np.meshgrid(xs, ys)
C = Y + 1j * X                 # 坐标旋转：C = Y + 1j*X
C = np.where(np.abs(C) < 1e-15, 1e-15 + 0j, C)
invC = 1.0 / C
print(f"      {time.time()-t0:.2f}s")

# ============================================================
# 3. 逆 M 迭代  z ← z² + 1/c   (z₀ = 0)
# ============================================================
print("[2/6] 逆 M 迭代 z₀=0, z←z²+1/c ...")
Z = np.zeros_like(C, dtype=np.complex128)
iter_count = np.full(C.shape, -1, dtype=np.int32)

t0 = time.time()
for n in range(MAX_ITER):
    active = iter_count == -1
    if not np.any(active):
        print(f"      ✓ 全部逃逸于 {n} 步")
        break
    Z[active] = Z[active]**2 + invC[active]
    escaped = active & (np.abs(Z) > ESCAPE_RADIUS)
    iter_count[escaped] = n
    if (n + 1) % 100 == 0:
        frac = np.sum(iter_count != -1) / iter_count.size * 100
        print(f"      步 {n+1:>3d}: 逃逸 {frac:.1f}%")

iter_count[iter_count == -1] = MAX_ITER
n_esc = np.sum(iter_count < MAX_ITER)
print(f"      耗时 {time.time()-t0:.2f}s | 逃逸 {n_esc/iter_count.size*100:.2f}%")

# ============================================================
# 4. 连续逃逸时间（安全对数平滑）
# ============================================================
print("[3/6] 连续逃逸时间 + Reiter 朝外映射 ...")

absZ = np.abs(Z)
# 安全下界：保证 log(absZ) > 0 且 log(log(absZ)) 有定义
absZ_safe = np.clip(absZ, ESCAPE_RADIUS + 1e-12, None)
log_esc = math.log(ESCAPE_RADIUS)

n_int = iter_count.astype(np.float64)
# Büldt 公式：nu = n - log2(log2(|z|/R))，这里 R=ESCAPE_RADIUS
# 安全公式：nu = n - log2( log(|z|)/log(R) )
# 写成 log2(1 + (log(|z|)-log(R))/log(R)) 避免 log(0)
ratio = np.log(absZ_safe) / log_esc           # log(|z|)/log(R) ≥ 1
ratio = np.clip(ratio, 1.0 + 1e-12, None)     # 严格 > 1
log_term = np.log(np.log(ratio)) / math.log(2) + math.log(log_esc) / math.log(2)
nu = n_int - log_term
nu = np.clip(nu, 0, None)

# 归一化到 [0,1]
nu_norm = nu / (MAX_ITER * 0.6)        # *0.6 拉伸对比度
nu_norm = np.clip(nu_norm, 0, 1)

# ============================================================
# 5. Reiter 朝外辐射映射
# ============================================================
print("[4/6] Reiter D(p) 朝外辐射 ...")

rgb = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float64)

for idx, p in enumerate(PRIMES):
    Dp = D_vals[p]
    if OUTWARD_MODE == 'power':
        # val^(1/D)：D>1 时边缘更亮 → 朝外喷射
        ch = np.power(nu_norm, 1.0 / Dp)
    elif OUTWARD_MODE == 'linear':
        ch = np.clip(nu_norm * (Dp / D_vals[2]), 0, 1)
    elif OUTWARD_MODE == 'exp':
        ch = np.clip((np.exp(nu_norm * Dp * 0.6) - 1) / (math.e - 1), 0, 1)
    else:
        ch = nu_norm
    rgb[:, :, idx] = ch

# ============================================================
# 6. Lucas / Pascal 蒙版（Sierpinski 镂空纹理）— 向量化
# ============================================================
print("[5/6] Lucas 蒙版 (向量化) ...")

def lucas_mask_vectorized(N, K, p):
    """
    向量化 Lucas 判定：C(N,K) mod p != 0
    原理：在基 p 下逐位比较 N_i >= K_i
    用对数位提取法：对每一位 j，检查 (N mod p^(j+1))//p^j >= (K mod p^(j+1))//p^j
    """
    max_bits = int(np.log(max(N.max(), K.max(), 1)) / np.log(p)) + 1
    m = np.ones(N.shape, dtype=bool)
    for j in range(max_bits):
        pj = p ** j
        pj1 = pj * p
        ni = (N // pj) % p
        ki = (K // pj) % p
        m &= (ni >= ki)
    return m

mask = np.ones(C.shape, dtype=np.float64)
for pi, p in enumerate(PRIMES):
    k_shift = 5 + pi * 3
    N = iter_count.astype(np.int64)
    K = (iter_count // k_shift).astype(np.int64)
    m = lucas_mask_vectorized(N, K, p).astype(np.float64)
    mask *= m
    frac = m.mean() * 100
    print(f"      p={p}: Pascal 非零占比 {frac:.1f}%")

# 蒙版叠加：非零区增强，零区压暗
for c in range(3):
    rgb[:, :, c] = rgb[:, :, c] * (0.25 + 0.75 * mask)

# ============================================================
# 7. 光晕（glow）+ 色彩映射
# ============================================================
print("[6/6] 光晕 + 色彩映射 + 输出 ...")

# 亮度图做高斯模糊作为光晕
luminance = 0.299*rgb[:,:,0] + 0.587*rgb[:,:,1] + 0.114*rgb[:,:,2]
glow = gaussian_filter(luminance, sigma=GLOW_SIGMA)
glow = np.clip(glow * 1.5, 0, 1)

# 把光晕加回 RGB（朝外辐射感倍增）
for c in range(3):
    rgb[:, :, c] = np.clip(rgb[:, :, c] + 0.18 * glow, 0, 1)

# ---------- HSV 主图 ----------
hue = np.clip(0.66 - 0.66 * rgb[:, :, 2], 0, 0.95)  # 蓝→红 辐射
sat = np.clip(0.35 + 0.65 * (rgb[:,:,0]*0.5 + glow*0.5), 0, 1)
val = np.clip(0.15 + 0.85 * (0.5*rgb[:,:,1] + 0.5*glow), 0, 1)
hsv = np.stack([hue, sat, val], axis=2)
img_hsv = hsv_to_rgb(hsv)

# ---------- 纯 RGB Reiter ----------
img_rgb = np.clip(rgb, 0, 1)

# ---------- 保存 ----------
out = {
    "inverse_m_outward_MAIN.png":  (img_hsv,  "HSV + Glow 朝外辐射 (主图)"),
    "inverse_m_outward_RGB.png":   (img_rgb,  "纯 Reiter RGB 三通道"),
}

for fname, (img, title) in out.items():
    fig, ax = plt.subplots(figsize=(16,12), dpi=130)
    ax.imshow(img, extent=[X_MIN,X_MAX,Y_MIN,Y_MAX],
              origin='lower', interpolation='bilinear')
    D_str = "  |  ".join([f"p={p}: D={D_vals[p]:.4f}" for p in PRIMES])
    ax.set_title(f"Inverse M · Outward Pascal Rendering\n"
                 r"$D(p)=\frac{\ln[p(p+1)/2]}{\ln p}$  |  " + D_str,
                 fontsize=13, color='white')
    ax.set_xlabel("Re (rotated)", fontsize=11, color='white')
    ax.set_ylabel("Im (rotated)", fontsize=11, color='white')
    ax.tick_params(colors='white')
    fig.patch.set_facecolor('black')
    plt.tight_layout()
    fig.savefig(f"/data/workspace/{fname}", dpi=130,
                facecolor='black', bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {fname}")

# ---------- 通道分离图 ----------
fig, axes = plt.subplots(1, 3, figsize=(22, 7.5), dpi=120)
for idx, p in enumerate(PRIMES):
    ch = rgb[:, :, idx]
    im = axes[idx].imshow(ch, extent=[X_MIN,X_MAX,Y_MIN,Y_MAX],
                          origin='lower', cmap='magma',
                          interpolation='bilinear')
    axes[idx].set_title(
        f"p = {p}  |  D = {D_vals[p]:.4f}\n"
        r"$D_k($"f"p={p}, k={K_DIM}"r"$) = {:.4f}$".format(Dk_vals[p]),
        fontsize=13, color='white')
    axes[idx].set_xlabel("Re", fontsize=10, color='white')
    axes[idx].tick_params(colors='white')
    fig.colorbar(im, ax=axes[idx], shrink=0.8)
fig.patch.set_facecolor('black')
fig.suptitle("Reiter D(p) Channels · Outward Radiation Components",
             fontsize=15, color='white', y=1.02)
plt.tight_layout()
fig.savefig("/data/workspace/inverse_m_channels_v2.png", dpi=120,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ inverse_m_channels_v2.png")

print("\n🎉 全部完成！")
print("\n" + "=" * 60)
print("公式改编速查（写进制图说明）")
print("-" * 60)
print(r"  定理2: D(p) = ln[p(p+1)/2] / ln(p)")
print(r"  朝外映射: channel_p = normalize(iter)^ (1/D(p))")
print(r"  定理3: D_k(p) = ln[C(p-1+k,k)] / ln(p)  [k=维度参数]")
print(r"  Lucas: C(n,k) mod p ≠ 0 ⟺ 无进位（蒙版）")
print("=" * 60)
