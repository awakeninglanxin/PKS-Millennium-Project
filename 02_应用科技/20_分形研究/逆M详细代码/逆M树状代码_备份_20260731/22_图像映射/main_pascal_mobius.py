#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 帕斯卡三角 Mobius 映射 — 逆M逃逸区用 Sierpinski 分形纹理填充

核心链路 (元宝《维度数学漫步》5层拆解 → 实践):
  像素 w → Mobius变换 z=f_M(w) → 三角格 (n,k) → Lucas定理 (k&~n)==0 → 着色

Mobius 变换 f_M(z)=(az+b)/(cz+d) 是反演 1/z 的推广 (第3层),
帕斯卡三角 mod 2 = Sierpinski 分形, 通过 Mobius 弯曲成底层纹理。
"""
import numpy as np, matplotlib.pyplot as plt, os
from matplotlib.colors import hsv_to_rgb

od = os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 (逆M标准窗) ======
TIP = 4.0
B = -4/3
HSP = 1.6242719100
M = 0.5
R0, R1 = B-M, TIP+M
I0, I1 = -HSP-M, HSP+M
W = 2400
H = int(W * (R1-R0) / (I1-I0))
MI = 300          # 最大迭代
BL = 50           # bailout
A = -1            # 反演幂次

# ====== Mobius 变换参数 (可调! 不同参数=不同纹理弯曲效果) ======
# f_M(z) = (a*z + b) / (c*z + d)
# 方案A: 纯反演 f(z)=1/z
MOBIUS_a = 0 + 0j
MOBIUS_b = 1 + 0j
MOBIUS_c = 1 + 0j
MOBIUS_d = 0 + 0j

# 方案B: f(z)=z/(z-p)  — 将点p映射到无穷远,产生极向拉伸
# MOBIUS_a = 1+0j; MOBIUS_b = 0+0j; MOBIUS_c = 1+0j; MOBIUS_d = -2+0j

# 方案C: Cayley f(z)=(z-i)/(z+i)
# MOBIUS_a = 1+0j; MOBIUS_b = -1j; MOBIUS_c = 1+0j; MOBIUS_d = 1j

# ====== 帕斯卡三角参数 ======
SIERPINSKI_SCALE = 18.0   # 三角格缩放 (越大三角越小越密)
# 三角格偏移 (可调,改变纹理起始位置)
GRID_OFFSET_X = 0.0
GRID_OFFSET_Y = 0.0

print(f"视窗: {W}x{H}, 迭代{MI}, bailout{BL}")
print(f"Mobius: a={MOBIUS_a}, b={MOBIUS_b}, c={MOBIUS_c}, d={MOBIUS_d}")
print(f"帕斯卡三角 scale={SIERPINSKI_SCALE}")

# ====== 阶段0: 生成复数网格 (逆M: w参数) ======
x = np.linspace(R0, R1, W)
y = np.linspace(I0, I1, H)
X, Y = np.meshgrid(x, y)
w_grid = X + 1j*Y  # 参数平面 w

# 逆M有效参数: c_eff = w^(-1) = 1/w (反演)
eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = (abs(w_grid[sf])**A) * np.exp(1j * A * np.angle(w_grid[sf]))
ce[~sf] = 1e6  # 原点附近设为大值

# ====== 阶段1: 临界轨道迭代 + 逃逸检测 ======
z = np.zeros_like(ce)
dz = np.ones_like(ce)
alive = np.ones(ce.shape, bool)
esc_iter = np.zeros(ce.shape, int)

for i in range(MI):
    if not alive.any():
        break
    idx = np.where(alive)
    za = z[idx].copy()
    ca = ce[idx].copy()
    dza = dz[idx].copy()

    # 导数: dz ← 2*z*dz + 1  (对参数c的导数, 但这里是逆M用c_eff)
    dza = 2 * za * dza + 1
    # 迭代: z ← z² + c_eff
    za = za * za + ca

    z[idx] = za
    dz[idx] = dza

    # 逃逸检测
    escaped_full = np.zeros(ce.shape, bool)
    escaped_full[idx] = (za.real**2 + za.imag**2 > BL**2)
    esc_iter[escaped_full] = i + 1
    alive &= ~escaped_full

interior = ~alive   # 水滴内部 = 未逃逸
ext = alive          # 逃逸区

print(f"逃逸像素: {ext.sum()}/{W*H} ({ext.sum()/(W*H)*100:.1f}%)")
print(f"内部像素: {interior.sum()}/{W*H}")

# ====== 阶段2: Mobius变换作用于逃逸像素的w坐标 ======
def mobius(z, a, b, c, d):
    """Mobius变换 f(z) = (az+b)/(cz+d)"""
    num = a * z + b
    den = c * z + d
    # 处理除零 (den=0 → 无穷远)
    safe = np.abs(den) > 1e-12
    result = np.full_like(z, np.nan, dtype=np.complex128)
    result[safe] = num[safe] / den[safe]
    return result

# 对逃逸像素应用Mobius变换
w_ext = w_grid[ext]
z_mobius = mobius(w_ext, MOBIUS_a, MOBIUS_b, MOBIUS_c, MOBIUS_d)

# ====== 阶段3: 帕斯卡三角 mod 2 — Lucas定理判定 ======
def pascal_sierpinski(z_re, z_im, scale=18.0, offset_x=0.0, offset_y=0.0):
    """
    帕斯卡三角 mod 2 (Sierpinski分形) 纹理判定

    Lucas定理: C(n,k) mod 2 = 1 ⟺ (k & ~n) == 0

    三角格坐标映射 (等边三角形平铺):
      b = 2*y / (s*sqrt(3))
      a = (x - s*b/2) / s
      n = round(a+b), k = round(b)
    """
    s = scale
    # 三角格坐标
    b_coord = 2 * (z_im + offset_y) / (s * np.sqrt(3))
    a_coord = ((z_re + offset_x) - s * b_coord / 2) / s

    n = np.round(a_coord + b_coord).astype(np.int64)
    k = np.round(b_coord).astype(np.int64)

    # Lucas定理: C(n,k) mod 2 = 1 ⟺ (k & ~n) == 0
    valid = (n >= 0) & (k >= 0) & (k <= n)
    pascal_fill = valid & ((k & ~n) == 0)

    return pascal_fill

# 对Mobius变换后的z坐标做帕斯卡判定
pascal_mask = pascal_sierpinski(
    z_mobius.real, z_mobius.imag,
    scale=SIERPINSKI_SCALE,
    offset_x=GRID_OFFSET_X,
    offset_y=GRID_OFFSET_Y
)

# ====== 阶段4: 着色 ======
img = np.zeros((H, W, 3))

# 水滴内部: 深蓝 → 青渐变 (体现层次)
if interior.any():
    # 用迭代次数做内部渐变
    interior_depth = np.zeros((H, W))
    # 未逃逸点用迭代次数做微弱的亮度变化
    for ii in range(H):
        for jj in range(W):
            if interior[ii, jj]:
                interior_depth[ii, jj] = 0.3 + 0.2 * np.sin(ii/H*5 + jj/W*8)
    img[interior] = np.stack([
        np.full(interior.sum(), 0.02),
        np.full(interior.sum(), 0.05),
        0.15 + 0.15 * interior_depth[interior]
    ], axis=-1)

# 逃逸区: 帕斯卡三角纹理
if ext.any():
    # 帕斯卡填充 → 金色/琥珀色
    # 帕斯卡空白 → 深藏青色
    fill_color = np.array([1.0, 0.75, 0.15])    # 金色
    empty_color = np.array([0.05, 0.08, 0.25])   # 深藏青

    ext_fill = np.zeros((ext.sum(), 3))
    ext_fill[pascal_mask] = fill_color
    ext_fill[~pascal_mask] = empty_color
    img[ext] = ext_fill

# ====== 阶段5: DEM 距离估计勾边 ======
dem = np.zeros_like(w_grid, dtype=np.float64)
abs_z = np.abs(z)
abs_dz = np.abs(dz) + 1e-12
dem[ext] = abs_z[ext] * np.log(abs_z[ext] + 1e-12) / abs_dz[ext]

# 归一化
dem_max = np.percentile(dem[ext], 95) if ext.any() else 1.0
dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)

# 暗边: |d| 小的区域 (靠近边界) 变暗
edge_dark = np.clip(1.0 - np.exp(-dem_norm * 2.5), 0, 1)
# 光晕: 最靠近边界的细线发亮
edge_glow = np.exp(-dem_norm * 8)

img = img * edge_dark[..., None]
img = img + edge_glow[..., None] * 0.4  # 金色光晕

# ====== 阶段6: 逃逸势能微调 (让深区有层次) ======
# 用平滑迭代次数在帕斯卡纹理上叠加微弱的亮度变化
if ext.any():
    nu = esc_iter.astype(np.float64)
    nu_max = nu[ext].max() if ext.any() else 1.0
    nu_norm = np.clip(nu / max(nu_max, 1), 0, 1)
    # 越靠近边界(nu小) → 稍亮
    brightness = 0.85 + 0.15 * (1.0 - nu_norm[ext])
    img[ext] = img[ext] * brightness[:, None]

img = np.clip(img, 0, 1)

# ====== 输出 ======
out_png = os.path.join(od, 'UF22_帕斯卡Mobius映射.png')

# 旋转: k=1 (90°CCW) → Re轴朝上
img_rot = np.rot90(img, k=1)
aspect = img_rot.shape[1] / img_rot.shape[0]

fig, ax = plt.subplots(1, 1, figsize=(14, 14/aspect))
ax.imshow(img_rot, origin='upper')
ax.set_title(
    f'UF22 Pascal-Sierpinski + Moebius Map\n'
    f'f(z)=({MOBIUS_a}z+{MOBIUS_b})/({MOBIUS_c}z+{MOBIUS_d})  '
    f'scale={SIERPINSKI_SCALE}',
    color='white', fontsize=10
)
ax.axis('off')
fig.patch.set_facecolor('black')
fig.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='black')
plt.close()
print(f'\nDone: {out_png}')
print(f'  Sierpinski fill: {pascal_mask.sum()}/{len(pascal_mask)} triangles')
