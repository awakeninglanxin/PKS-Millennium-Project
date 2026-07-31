#!/usr/bin/env python3
"""
inverse_m_pascal_outward.py
=================================
逆 M 水滴 · 朝外渲染（Pascal / Reiter 分形维数驱动）

核心思路
--------
1. 复平面网格 → 坐标旋转 → c = y + 1j*x          （逆 M 分形标准设置）
2. 迭代 z ← z² + 1/c，记录逃逸迭代次数 n
3. 用 Reiter (1993) 的 Pascal 模素数分形维数公式，
   将"朝内"的逃逸时间映射反转为"朝外"辐射：
       D(p) = ln[p(p+1)/2] / ln(p)
   把迭代深度 n 通过 D(p) 重新缩放，
   使得不同素数 p 对应不同的"辐射速度"层。
4. 朝外方向：中心（水滴核）颜色深，越往外越亮/越饱和，
   形成从内部向外辐射的水滴扩散感。
5. 多素数叠加：同时用 p=2,3,5 三层的 D(p) 分别驱动
   R / G / B 三个通道，实现彩色朝外渲染。

公式改编清单（来自 Reiter 论文）
---------------------------------
  定理2  D = ln[p(p+1)/2] / ln(p)        ← 驱动 RGB 三通道的辐射强度
  定理3  D_k = ln[C(p-1+k, k)] / ln(p)   ← 可选：多维度 k 控制颜色周期
  Long   e = [n - sum(base-p digits)]/(p-1) ← 可选：像素级素数筛选蒙版
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
import time

# ============================================================
# 0. 参数区
# ============================================================
WIDTH, HEIGHT = 1600, 1200      # 输出分辨率
MAX_ITER       = 300             # 最大迭代次数
ESCAPE_RADIUS  = 16.0           # 逃逸阈值 |z| > 16
PRIMES         = [2, 3, 5]      # 使用的素数（分别对应 R/G/B 通道）
K_DIM          = 2               # 多分项维数定理中的 k（这里取 2 = 三角形）

# 复平面范围（对应你给的图：x∈[-3,3], y∈[-1.5,4.5]）
X_MIN, X_MAX = -3.0, 3.0
Y_MIN, Y_MAX = -1.5, 4.5

# ============================================================
# 1. Reiter 公式实现
# ============================================================

def reiter_dimension(p):
    """
    定理2：Pascal 三角模素数 p 的分形维数
    D(p) = ln[p(p+1)/2] / ln(p)
    """
    return np.log(p * (p + 1) / 2) / np.log(p)


def reiter_multinomial_dimension(p, k):
    """
    定理3：k 维多分项金字塔模 p 的分形维数
    D_k = ln[ C(p-1+k, k) ] / ln(p)
    """
    from math import comb
    return np.log(comb(p - 1 + k, k)) / np.log(p)


def lucas_nonzero_mod_p(n, k, p):
    """
    用 Lucas 定理快速判断 C(n,k) mod p != 0
    等价于：n 与 k 的基 p 表示逐位满足 n_i >= k_i（无进位）
    返回 True 表示该二项式系数不被 p 整除（即"非零"像素）
    """
    nn, kk = n, k
    while nn > 0 or kk > 0:
        if (kk % p) > (nn % p):
            return False
        nn //= p
        kk //= p
    return True


# 预计算三个素数的 D(p) 与 D_k(p)
D_vals = {p: reiter_dimension(p) for p in PRIMES}
Dk_vals = {p: reiter_multinomial_dimension(p, K_DIM) for p in PRIMES}

print("=" * 55)
print("Reiter 分形维数（用于朝外辐射权重）")
print("-" * 55)
for p in PRIMES:
    print(f"  p={p}:  D({p}) = {D_vals[p]:.6f}"
          f"    D_k({p},k={K_DIM}) = {Dk_vals[p]:.6f}")
print("=" * 55)

# ============================================================
# 2. 复平面网格 + 坐标旋转
# ============================================================
print("\n[1/5] 建立复平面网格 ...")
t0 = time.time()

xs = np.linspace(X_MIN, X_MAX, WIDTH)
ys = np.linspace(Y_MIN, Y_MAX, HEIGHT)
X, Y = np.meshgrid(xs, ys)

# 坐标旋转：C = Y + 1j*X  （实轴竖直化，逆 M 标准操作）
C = Y + 1j * X

# 避免 c=0 导致 1/c 发散
mask_zero = (np.abs(C) < 1e-12)
C = np.where(mask_zero, 1e-12 + 0j, C)

print(f"      耗时 {time.time()-t0:.2f}s")

# ============================================================
# 3. 逆 M 迭代  z ← z² + 1/c
# ============================================================
print("[2/5] 逆 M 迭代 (z = z^2 + 1/c) ...")

# 初始值 z = c（逆 M 的关键：从 c 出发，而非 0）
Z = C.copy()
# 迭代公式中的常数 1/c
invC = 1.0 / C

# 记录逃逸迭代次数（-1 表示未逃逸）
iter_count = np.full(C.shape, -1, dtype=np.int32)

t0 = time.time()
for n in range(MAX_ITER):
    # 只对还没逃逸的点继续迭代
    active = (iter_count == -1)
    if not np.any(active):
        print(f"      所有像素已在 {n} 次迭代内逃逸")
        break
    Z[active] = Z[active] ** 2 + invC[active]
    # 逃逸判定
    escaped = active & (np.abs(Z) > ESCAPE_RADIUS)
    iter_count[escaped] = n
    if (n + 1) % 50 == 0:
        frac = np.sum(iter_count != -1) / iter_count.size * 100
        print(f"      迭代 {n+1:>3d}: 已逃逸 {frac:.1f}%")

# 未逃逸的设为 MAX_ITER
iter_count[iter_count == -1] = MAX_ITER
print(f"      耗时 {time.time()-t0:.2f}s")
print(f"      最大记录迭代 = {iter_count.max()}")

# ============================================================
# 4. 对数平滑（连续逃逸时间）
# ============================================================
print("[3/5] 对数平滑 + Reiter 朝外映射 ...")

# 标准连续逃逸时间（Büldt / Linas 公式）
# nu = n - log2(log2(|z|))，但这里我们做"朝外"反转
absZ = np.abs(Z)
# 防止 log(0)
absZ = np.clip(absZ, 1e-300, None)

# 整数迭代部分
n_int = iter_count.astype(np.float64)
# 小数部分（用 |z| 距逃逸阈值的"超出量"）
log_term = np.log(np.log(absZ) / np.log(ESCAPE_RADIUS)) / np.log(2)
nu_continuous = n_int - log_term
nu_continuous = np.clip(nu_continuous, 0, None)

# ---------- 关键改编：Reiter 朝外辐射映射 ----------
# 对每个素数 p，用 D(p) 作为"辐射速度"的指数缩放
# 朝外含义：中心（低迭代 = 水滴核）值小 → 暗
#           边缘（高迭代 = 辐射出去）值大 → 亮
# 映射公式：val_p = (nu / MAX_ITER) ^ (1/D(p))
#           → D(p)>1 时曲线更陡，辐射集中在外圈（向外喷射感）
#           → D(p)<1 时曲线平缓（这里 D(p) 都 >1）

rgb = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float64)
for idx, p in enumerate(PRIMES):
    Dp = D_vals[p]
    # 归一化到 [0,1]
    norm_val = nu_continuous / MAX_ITER
    # Reiter 朝外缩放：幂次 1/D(p) 使得高维通道更"向外辐射"
    channel = norm_val ** (1.0 / Dp)
    # 再做一次非线性拉伸增强水滴边缘的"喷射"感
    channel = np.clip(channel * (Dp / reiter_dimension(2)), 0, 1)
    rgb[:, :, idx] = channel

# ============================================================
# 5. Lucas 蒙版（可选：只在 Pascal 非零位置启用全彩）
# ============================================================
print("[4/5] 生成 Lucas / Pascal 非零蒙版 ...")

# 用迭代次数 n 作为 Lucas 定理的输入（n = 迭代深度）
# 对 p=2：只在 C(n,k) 不被 2 整除的位置保留高亮
# 这里 k 取迭代次数的低 8 位，制造类似 Sierpinski 的镂空
n_for_lucas = iter_count.astype(np.int64)
k_for_lucas = (iter_count // 7).astype(np.int64)  # 错开相位

mask_pascal = np.ones(C.shape, dtype=bool)
for p in PRIMES:
    # 逐素数判断；三个都满足时最亮（交集）
    m = np.zeros(C.shape, dtype=bool)
    flat_n = n_for_lucas.ravel()
    flat_k = k_for_lucas.ravel()
    flat_m = np.zeros(flat_n.shape, dtype=bool)
    for i in range(flat_n.size):
        flat_m[i] = lucas_nonzero_mod_p(int(flat_n[i]), int(flat_k[i]), p)
    m = flat_m.reshape(C.shape)
    mask_pascal &= m

# 蒙版可视化权重（0/1 二值）
mask_weight = mask_pascal.astype(np.float64)

# 将 Pascal 蒙版叠加到 RGB：在非零位置增强亮度，零位置压暗
# 这会在渲染图中产生 Sierpinski 风格的镂空纹理
for c in range(3):
    rgb[:, :, c] = rgb[:, :, c] * (0.35 + 0.65 * mask_weight)

# ============================================================
# 6. 色彩映射（朝外辐射感配色）
# ============================================================
print("[5/5] 色彩映射 + 输出 ...")

# 方案 A：HSV 朝外辐射
# hue 从中心（低值）到边缘（高值）顺时针旋转 → 水滴喷射色带
hue = np.clip(rgb[:, :, 1] * 0.7 + rgb[:, :, 0] * 0.3, 0, 1)
saturation = np.clip(0.4 + 0.6 * mask_weight, 0, 1)
value = np.clip(rgb[:, :, 2] ** 0.6, 0, 1)

hsv = np.stack([hue, saturation, value], axis=2)
img_hsv = hsv_to_rgb(hsv)

# 方案 B：直接 RGB（Reiter 三通道）
img_rgb = np.clip(rgb, 0, 1)

# ---------- 输出图 1：HSV 朝外辐射 ----------
fig1, ax1 = plt.subplots(figsize=(14, 10.5), dpi=150)
ax1.imshow(img_hsv, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
           origin='lower', interpolation='bilinear')
ax1.set_title(
    "Inverse Mandelbrot · Outward Pascal Rendering\n"
    r"$D(p)=\frac{\ln[p(p+1)/2]}{\ln p}$  driving R/G/B for $p=2,3,5$"
    "  |  Lucas mask overlay",
    fontsize=14, color='white')
ax1.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax1.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax1.tick_params(colors='white')
fig1.patch.set_facecolor('black')
plt.tight_layout()
fig1.savefig("/data/workspace/inverse_m_outward_hsv.png", dpi=150,
             facecolor='black', bbox_inches='tight')
plt.close(fig1)

# ---------- 输出图 2：纯 RGB Reiter 通道 ----------
fig2, ax2 = plt.subplots(figsize=(14, 10.5), dpi=150)
ax2.imshow(img_rgb, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
           origin='lower', interpolation='bilinear')
ax2.set_title(
    "Inverse Mandelbrot · Pure Reiter RGB Channels\n"
    r"$D_2=\ln3/\ln2\approx1.585$  "
    r"$D_3=\ln6/\ln3\approx1.631$  "
    r"$D_5=\ln15/\ln5\approx1.683$",
    fontsize=13, color='white')
ax2.set_xlabel("Re (rotated)", fontsize=11, color='white')
ax2.set_ylabel("Im (rotated)", fontsize=11, color='white')
ax2.tick_params(colors='white')
fig2.patch.set_facecolor('black')
plt.tight_layout()
fig2.savefig("/data/workspace/inverse_m_outward_rgb.png", dpi=150,
             facecolor='black', bbox_inches='tight')
plt.close(fig2)

# ---------- 输出图 3：各通道分离（便于制图分析）----------
fig3, axes = plt.subplots(1, 3, figsize=(21, 7), dpi=120)
for idx, p in enumerate(PRIMES):
    ch = rgb[:, :, idx]
    im = axes[idx].imshow(ch, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
                          origin='lower', cmap='inferno',
                          interpolation='bilinear')
    axes[idx].set_title(
        f"Channel p={p}\n"
        r"$D_{{{p}}}=$".format(p=p) + f"{D_vals[p]:.4f}",
        fontsize=13, color='white')
    axes[idx].set_xlabel("Re", fontsize=10, color='white')
    axes[idx].tick_params(colors='white')
    fig3.colorbar(im, ax=axes[idx], shrink=0.8)

fig3.patch.set_facecolor('black')
fig3.suptitle("Reiter D(p) Channels · Outward Radiation Components",
              fontsize=15, color='white', y=1.02)
plt.tight_layout()
fig3.savefig("/data/workspace/inverse_m_channels.png", dpi=120,
             facecolor='black', bbox_inches='tight')
plt.close(fig3)

print("\n✅ 渲染完成！输出文件：")
print("   1. inverse_m_outward_hsv.png  ← HSV 朝外辐射（主图）")
print("   2. inverse_m_outward_rgb.png  ← 纯 RGB Reiter 三通道")
print("   3. inverse_m_channels.png     ← 各素数通道分离图")

# 打印一张维数对照表，方便写进制图说明
print("\n" + "=" * 55)
print("维数对照表（制图注释用）")
print("-" * 55)
print(f"{'p':>3s}  {'D(p)':>10s}  {'D_k(p,2)':>10s}  {'用途'}")
print("-" * 55)
for p in PRIMES:
    print(f"{p:>3d}  {D_vals[p]:>10.6f}  {Dk_vals[p]:>10.6f}  "
          f"p={p} → {'R' if p==PRIMES[0] else 'G' if p==PRIMES[1] else 'B'} 通道")
print("=" * 55)
