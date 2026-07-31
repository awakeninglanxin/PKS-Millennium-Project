#!/usr/bin/env python3
"""
inverse_m_outward_mobius.py
============================
逆 M 水滴朝外渲染 — Möbius 翻转法

核心思路（一句话）：
  正 M 标准 inward 渲染 → 对每个像素做 c → 1/c 翻转 → 自然得到逆 M outward

数学原理：
  标准 Mandelbrot: z_{n+1} = z_n² + c,  z₀ = 0
  逆 Mandelbrot:   z_{n+1} = z_n² + 1/c, z₀ = 0
  → 等价于先算 c' = 1/c，再代入标准 Mandelbrot 迭代
  → 所以"逆 M 的 outward 渲染" = 把正 M 的 inward 图做 Möbius 翻转

步骤：
  1. 建立复平面网格
  2. 坐标旋转 C = Y + 1j*X
  3. Möbius 翻转：C_inv = 1 / C        ← 关键一步
  4. 标准正 M 迭代：z = z² + C_inv
  5. 标准 inward 着色（不用任何反转）
  6. 输出即为逆 M outward 渲染

可选叠加：用 Reiter 帕斯卡维数公式做 Lucas 蒙版纹理（不改方向，只改纹理）
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from scipy.ndimage import gaussian_filter
import time, math

# ============================================================
# 0. 参数
# ============================================================
WIDTH, HEIGHT   = 1800, 1350
MAX_ITER        = 400
ESCAPE_RADIUS   = 16.0
PRIMES          = [2, 3, 5]
K_DIM           = 2
GLOW_SIGMA      = 3.0

# 复平面范围
X_MIN, X_MAX    = -3.0, 3.0
Y_MIN, Y_MAX    = -1.5, 4.5

# ============================================================
# 1. Reiter 公式（仅用于可选 Lucas 蒙版纹理）
# ============================================================
def reiter_dimension(p):
    return math.log(p * (p + 1) / 2) / math.log(p)

def lucas_mask_vectorized(N, K, p):
    max_bits = int(np.log(max(N.max(), K.max(), 1)) / np.log(p)) + 1
    m = np.ones(N.shape, dtype=bool)
    for j in range(max_bits):
        m &= ((N // (p**j)) % p >= (K // (p**j)) % p)
    return m

D_vals = {p: reiter_dimension(p) for p in PRIMES}
print("=" * 60)
print("Reiter D(p)（仅用于 Lucas 纹理蒙版）")
for p in PRIMES:
    print(f"  p={p}: D={D_vals[p]:.6f}")
print("=" * 60)

# ============================================================
# 2. 复平面网格 + 坐标旋转
# ============================================================
print("\n[1/6] 复平面网格 ...")
t0 = time.time()
xs = np.linspace(X_MIN, X_MAX, WIDTH, dtype=np.float64)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT, dtype=np.float64)
X, Y = np.meshgrid(xs, ys)
C = Y + 1j * X
C = np.where(np.abs(C) < 1e-15, 1e-15 + 0j, C)
print(f"      {time.time()-t0:.2f}s")

# ============================================================
# ★ 3. Möbius 翻转 C → 1/C ★
# ============================================================
print("[2/6] Möbius 翻转 C → 1/C ...")
C_inv = 1.0 / C
# C_inv 就是逆 M 对应的参数
# 接下来用 C_inv 做标准正 M 迭代 → 等价于逆 M
print(f"      C_inv 范围: Re[{C_inv.real.min():.2f},{C_inv.real.max():.2f}]"
      f" Im[{C_inv.imag.min():.2f},{C_inv.imag.max():.2f}]")

# ============================================================
# 4. 标准正 M 迭代（inward 着色）
# ============================================================
print("[3/6] 标准正 M 迭代 z₀=0, z←z²+C_inv ...")
Z = np.zeros_like(C_inv, dtype=np.complex128)
iter_count = np.full(C_inv.shape, -1, dtype=np.int32)

t0 = time.time()
for n in range(MAX_ITER):
    active = iter_count == -1
    if not np.any(active):
        print(f"      ✓ 全部逃逸于 {n} 步")
        break
    Z[active] = Z[active]**2 + C_inv[active]
    escaped = active & (np.abs(Z) > ESCAPE_RADIUS)
    iter_count[escaped] = n
    if (n + 1) % 100 == 0:
        frac = np.sum(iter_count != -1) / iter_count.size * 100
        print(f"      步 {n+1:>3d}: 逃逸 {frac:.1f}%")

iter_count[iter_count == -1] = MAX_ITER
n_esc = np.sum(iter_count < MAX_ITER)
print(f"      耗时 {time.time()-t0:.2f}s | 逃逸 {n_esc/iter_count.size*100:.2f}%")

# ============================================================
# 5. 连续逃逸时间（Büldt 标准 inward）
# ============================================================
print("[4/6] 连续逃逸时间（标准 inward 着色）...")

absZ = np.abs(Z)
absZ_safe = np.clip(absZ, ESCAPE_RADIUS + 1e-12, None)
log_esc = math.log(ESCAPE_RADIUS)

n_int = iter_count.astype(np.float64)
ratio = np.clip(np.log(absZ_safe) / log_esc, 1.0 + 1e-12, None)
log_term = np.log(np.log(ratio)) / math.log(2) + math.log(log_esc) / math.log(2)
nu = n_int - log_term
nu = np.clip(nu, 0, None)

# 标准 inward 归一化（不做任何反转）
nu_norm = np.clip(nu / (MAX_ITER * 0.5), 0, 1)

print(f"      nu_norm: min={nu_norm.min():.3f} max={nu_norm.max():.3f}")

# ============================================================
# 6. 标准 inward 着色（log + coolwarm 风格）
# ============================================================
print("[5/6] 标准 inward 着色 + 输出 ...")

# --- 方法 A：对数灰度 inward（正 M 经典）---
# iter 越深（M集内部）→ 值大 → 亮（或黑，看偏好）
# 经典 inward：内部黑，边缘彩色辐射 → 翻转后内部亮、边缘暗 → outward
log_iter = np.log1p(nu_norm * MAX_ITER) / math.log(MAX_ITER + 1)
# 平滑周期化用于 cmap
smoothed = nu_norm  # 直接用连续逃逸时间

# --- 方法 B：Reiter 三通道（帕斯卡维数驱动色相周期）---
rgb_pascal = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float64)
for idx, p in enumerate(PRIMES):
    Dp = D_vals[p]
    # 用 D(p) 控制颜色周期密度
    # iter 越高 → 相位越密 → 更多彩色条纹
    phase = nu_norm * Dp * 2.0
    # 用 sin 做周期性色彩映射
    if idx == 0:
        rgb_pascal[:,:,0] = 0.5 + 0.5 * np.sin(phase * math.pi)
    elif idx == 1:
        rgb_pascal[:,:,1] = 0.5 + 0.5 * np.sin(phase * math.pi + 2.094)
    else:
        rgb_pascal[:,:,2] = 0.5 + 0.5 * np.sin(phase * math.pi + 4.189)

# --- 方法 C：经典 inward colormap（coolwarm 方向）---
# 正 M 经典：低 iter（外部刚逃逸）→ 蓝/黑，高 iter（靠近边界）→ 红/白
# 翻转后：高 iter 区域（原 M 集边界）→ 翻转到中心 → 中心红亮 = outward 辐射核

# 用 nu_norm 做 HSV
hue = np.clip(0.66 * (1 - nu_norm), 0, 0.95)  # 高iter→红(0), 低iter→蓝(0.66)
sat = np.clip(0.3 + 0.7 * nu_norm, 0, 1)
val = np.clip(0.1 + 0.9 * nu_norm, 0, 1)        # 高iter→亮, 低iter→暗
hsv = np.stack([hue, sat, val], axis=2)
img_hsv = hsv_to_rgb(hsv)

# --- 方法 D：纯 inward 灰度（最经典的"黑洞"效果）---
# 正 M 内部(iter大)→白, 外部(iter小)→黑
# 翻转后 → 中心白(辐射核), 外圈黑 → 完美 outward
img_inward = np.clip(nu_norm, 0, 1)

# --- 方法 E：Lucas / 帕斯卡蒙版叠加（可选纹理）---
print("      生成 Lucas 蒙版纹理 ...")
mask = np.ones(C_inv.shape, dtype=np.float64)
for pi, p in enumerate(PRIMES):
    k_shift = 7 + pi * 5
    N = iter_count.astype(np.int64)
    K = (iter_count // k_shift).astype(np.int64)
    m = lucas_mask_vectorized(N, K, p).astype(np.float64)
    mask *= m

# 把 Lucas 蒙版作为纹理叠加到 inward 图上
# 蒙版非零区保持原色，零区压暗 → Sierpinski 镂空纹理
img_lucas = np.clip(img_inward * (0.3 + 0.7 * mask), 0, 1)

# ============================================================
# 7. 保存所有图
# ============================================================
print("[6/6] 保存输出 ...")

outputs = {
    "mobius_01_inward_gray.png": (
        plt.cm.gray(img_inward),
        "正 M Inward 灰度（翻转后 = 逆 M Outward 灰度）"
    ),
    "mobius_02_hsv_coolwarm.png": (
        img_hsv,
        "HSV Inward（翻转后 = 逆 M Outward 彩色）"
    ),
    "mobius_03_pascal_rgb.png": (
        np.clip(rgb_pascal, 0, 1),
        "Reiter D(p) 三通道色相周期"
    ),
    "mobius_04_lucas_texture.png": (
        plt.cm.magma(img_lucas),
        "Lucas / Pascal 蒙版纹理叠加"
    ),
}

for fname, (img, title) in outputs.items():
    fig, ax = plt.subplots(figsize=(16, 12), dpi=130)
    ax.imshow(img, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
              origin='lower', interpolation='bilinear')
    ax.set_title(
        f"Inverse M · TRUE Outward (via Möbius Flip)\n"
        f"{title}",
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

# ---------- 对比图：正 M 原图 vs 逆 M 翻转图 ----------
# 正 M 在同一网格上直接渲染（不做 Möbius 翻转）
print("\n  附：渲染正 M 原图作对比 ...")
Z2 = np.zeros_like(C, dtype=np.complex128)
iter2 = np.full(C.shape, -1, dtype=np.int32)
for n in range(MAX_ITER):
    active = iter2 == -1
    if not np.any(active):
        break
    Z2[active] = Z2[active]**2 + C[active]
    escaped = active & (np.abs(Z2) > ESCAPE_RADIUS)
    iter2[escaped] = n
iter2[iter2 == -1] = MAX_ITER

absZ2 = np.abs(Z2)
absZ2_safe = np.clip(absZ2, ESCAPE_RADIUS + 1e-12, None)
ratio2 = np.clip(np.log(absZ2_safe) / log_esc, 1.0 + 1e-12, None)
log_term2 = np.log(np.log(ratio2)) / math.log(2) + math.log(log_esc) / math.log(2)
nu2 = iter2.astype(np.float64) - log_term2
nu2 = np.clip(nu2, 0, None)
nu2_norm = np.clip(nu2 / (MAX_ITER * 0.5), 0, 1)

# 正 M inward：高 iter → 亮
img_positive = plt.cm.hot(np.clip(nu2_norm, 0, 1))

fig, axes = plt.subplots(1, 2, figsize=(24, 10), dpi=120)

axes[0].imshow(img_positive, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
               origin='lower', interpolation='bilinear')
axes[0].set_title("正 M · Inward 渲染（标准 Mandelbrot）",
                  fontsize=14, color='white')
axes[0].set_xlabel("Re", fontsize=11, color='white')
axes[0].set_ylabel("Im", fontsize=11, color='white')
axes[0].tick_params(colors='white')

axes[1].imshow(img_inward, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
               origin='lower', cmap='hot', interpolation='bilinear')
axes[1].set_title("逆 M · Outward 渲染（Möbius 翻转后）",
                  fontsize=14, color='white')
axes[1].set_xlabel("Re (rotated)", fontsize=11, color='white')
axes[1].set_ylabel("Im (rotated)", fontsize=11, color='white')
axes[1].tick_params(colors='white')

fig.patch.set_facecolor('black')
fig.suptitle("正 M Inward  →  Möbius 翻转  →  逆 M Outward",
             fontsize=16, color='white', y=1.01)
plt.tight_layout()
fig.savefig("/data/workspace/mobius_05_comparison.png", dpi=120,
            facecolor='black', bbox_inches='tight')
plt.close(fig)
print("  ✓ mobius_05_comparison.png (正M vs 逆M 对比)")

print("\n🎉 全部完成！")
print("\n" + "=" * 60)
print("核心公式（写在制图说明里）")
print("-" * 60)
print(r"  Möbius 翻转: c' = 1/c")
print(r"  正 M 迭代:   z ← z² + c'    (标准 inward 着色)")
print(r"  翻转后自然 outward，无需任何方向反转")
print(r"")
print(r"  可选叠加（不改方向，只加纹理）:")
print(r"  Reiter D(p) = ln[p(p+1)/2] / ln(p)")
print(r"  Lucas 蒙版: C(n,k) mod p ≠ 0 ⟺ 无进位")
print("=" * 60)
