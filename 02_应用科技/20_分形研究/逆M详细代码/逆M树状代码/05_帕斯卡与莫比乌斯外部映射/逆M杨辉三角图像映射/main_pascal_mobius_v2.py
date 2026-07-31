#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 帕斯卡三角 Mobius映射 — 逆M逃逸区 Sierpinski 分形纹理

v2 修复: 坐标缩放 + 三套Mobius方案并行对比

算法链路:
  像素w → Mobius f_M(w) → 三角格(n,k) → Lucas (k&~n)==0 → 着色

基于元宝《维度数学漫步》5层拆解:
  第3层: 反演1/z + 平方z² = 非线性共形映射核心积木
  第4层: z²+c迭代 = Mandelbrot/Julia分形
  第5层: e^(iθ)欧拉公式 = 角向参数化

Mobius变换 f_M(z)=(az+b)/(cz+d) 将帕斯卡三角纹理"弯曲"到复平面,
产生的视觉效果类似于在逆水滴逃逸区铺了一层扭曲的谢尔宾斯基地毯。
"""
import numpy as np
import matplotlib.pyplot as plt
import os

od = os.path.dirname(os.path.abspath(__file__))

# ==================== 视窗参数 ====================
TIP = 4.0; B = -4/3; HSP = 1.6242719100; MARGIN = 0.5
R0, R1 = B - MARGIN, TIP + MARGIN
I0, I1 = -HSP - MARGIN, HSP + MARGIN
W = 2400
H = int(W * (R1 - R0) / (I1 - I0))
MI = 300; BL = 50

# ==================== Mobius 方案库 ====================
MOBIUS_SCHEMES = {
    'A_反演1_z': {
        'a': 0+0j, 'b': 1+0j, 'c': 1+0j, 'd': 0+0j,
        'label': 'f(z)=1/z  (纯反演)',
        'sierpinski_scale': 0.04,
        'offset_x': 0.0, 'offset_y': 0.0,
    },
    'B_z除以z减2': {
        'a': 1+0j, 'b': 0+0j, 'c': 1+0j, 'd': -2+0j,
        'label': 'f(z)=z/(z-2)  (极点拉伸)',
        'sierpinski_scale': 0.06,
        'offset_x': 0.5, 'offset_y': 0.5,
    },
    'C_Cayley': {
        'a': 1+0j, 'b': -1j, 'c': 1+0j, 'd': 1j,
        'label': 'f(z)=(z-i)/(z+i)  (Cayley)',
        'sierpinski_scale': 0.08,
        'offset_x': 0.2, 'offset_y': 0.3,
    },
}

print(f"视窗: {W}x{H}, 迭代{MI}, bailout{BL}")

# ==================== 阶段0: 复数网格 ====================
x = np.linspace(R0, R1, W)
y = np.linspace(I0, I1, H)
X, Y = np.meshgrid(x, y)
w_grid = X + 1j * Y

eps = 1e-12
sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0 / w_grid[sf]  # c_eff = 1/w (逆M反演)
ce[~sf] = 1e6

# ==================== 阶段1: 迭代 + 逃逸 ====================
z = np.zeros_like(ce)
dz = np.ones_like(ce)
alive = np.ones(ce.shape, bool)
esc_iter = np.zeros(ce.shape, int)

for i in range(MI):
    if not alive.any():
        break
    idx = np.where(alive)
    za = z[idx].copy(); ca = ce[idx].copy(); dza = dz[idx].copy()
    dza = 2 * za * dza + 1
    za = za * za + ca
    z[idx] = za; dz[idx] = dza
    esc = np.zeros(ce.shape, bool)
    esc[idx] = (za.real**2 + za.imag**2 > BL**2)
    esc_iter[esc] = i + 1
    alive &= ~esc

interior = ~alive
ext = alive
print(f"逃逸: {ext.sum()}/{W*H} ({ext.sum()/(W*H)*100:.1f}%)")

# ==================== 核心函数 ====================
def mobius(z, a, b, c, d):
    """Mobius: f(z) = (az+b)/(cz+d)"""
    num = a * z + b
    den = c * z + d
    safe = np.abs(den) > 1e-12
    result = np.full(z.shape, np.nan + 1j*np.nan, dtype=np.complex128)
    result[safe] = num[safe] / den[safe]
    return result

def pascal_sierpinski_fill(z_re, z_im, scale, ox=0, oy=0):
    """
    帕斯卡三角 mod 2 填充判定 (Lucas定理)

    三角格变换 (等边三角形平铺, 边长=scale):
      (x, y) → (n, k) 其中 n=行号, k=列号
      b = 2*(y+oy) / (scale * sqrt(3))
      a = (x+ox) / scale - b/2
      n = round(a+b), k = round(b)
    """
    sr3 = np.sqrt(3)
    b_coord = 2 * (z_im + oy) / (scale * sr3)
    a_coord = (z_re + ox) / scale - b_coord / 2

    n = np.round(a_coord + b_coord).astype(np.int64)
    k = np.round(b_coord).astype(np.int64)

    # Lucas: C(n,k) mod 2 = 1  ⇔  (k & ~n) == 0
    valid = (n >= 0) & (k >= 0) & (k <= n)
    fill = valid & ((k & ~n) == 0)
    return fill, valid, n, k

def render_one_scheme(w_grid, interior, ext, z, dz, esc_iter,
                      scheme, out_path):
    """用指定Mobius方案渲染一张图"""
    a = scheme['a']; b = scheme['b']
    c = scheme['c']; d = scheme['d']
    s_scale = scheme['sierpinski_scale']
    ox = scheme['offset_x']; oy = scheme['offset_y']

    # Mobius变换
    w_ext = w_grid[ext]
    z_m = mobius(w_ext, a, b, c, d)
    valid_mobius = ~np.isnan(z_m.real)

    # 帕斯卡填充
    zm_valid = z_m[valid_mobius]
    pascal, _, nvals, kvals = pascal_sierpinski_fill(
        zm_valid.real, zm_valid.imag, s_scale, ox, oy
    )

    n_range = (nvals.min(), nvals.max()) if len(nvals) > 0 else (0, 0)
    k_range = (kvals.min(), kvals.max()) if len(kvals) > 0 else (0, 0)

    # ===== 着色 =====
    img = np.zeros((H, W, 3))
    fill_color = np.array([0.95, 0.72, 0.12])   # 金色帕斯卡填充
    empty_color = np.array([0.04, 0.07, 0.22])   # 深藏青空白

    # 水滴内部: 深蓝渐变
    int_mask = np.where(interior)
    img[int_mask] = [0.02, 0.06, 0.18]

    # 逃逸区: 帕斯卡纹理
    ext_idx = np.where(ext)
    ext_flat = np.zeros(ext.sum(), dtype=int)
    ext_flat[valid_mobius] = pascal.astype(int)
    for i, (py, px) in enumerate(zip(ext_idx[0], ext_idx[1])):
        img[py, px] = fill_color if ext_flat[i] else empty_color

    # DEM 金边
    abs_z = np.abs(z); abs_dz = np.abs(dz) + 1e-12
    dem = np.zeros_like(w_grid, dtype=np.float64)
    dem[ext] = abs_z[ext] * np.log(abs_z[ext] + 1e-12) / abs_dz[ext]
    dem_max = np.percentile(dem[ext], 95) if ext.any() else 1.0
    dem_norm = np.clip(dem / max(dem_max, 1e-12), 0, 1)
    edge_dark = np.clip(1.0 - np.exp(-dem_norm * 3.0), 0, 1)
    edge_glow = np.exp(-dem_norm * 10)

    img *= edge_dark[..., None]
    img += edge_glow[..., None] * 0.35

    # 逃逸势能层次
    nu = esc_iter.astype(np.float64)
    nu_max = nu[ext].max() or 1.0
    nu_norm = np.clip(nu / nu_max, 0, 1)
    brightness = 0.82 + 0.18 * (1.0 - nu_norm[ext])
    img[ext] *= brightness[:, None]
    img = np.clip(img, 0, 1)

    # 输出
    img_rot = np.rot90(img, k=1)
    aspect = img_rot.shape[1] / img_rot.shape[0]
    fig, ax = plt.subplots(1, 1, figsize=(12, 12/aspect))
    ax.imshow(img_rot, origin='upper')
    ax.set_title(
        f'{scheme["label"]}\n'
        f'Pascal scale={s_scale}  n∈{n_range}  k∈{k_range}  '
        f'fill={pascal.sum()}/{len(pascal)}',
        color='white', fontsize=9
    )
    ax.axis('off')
    fig.patch.set_facecolor('black')
    fig.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"  → {os.path.basename(out_path)}  scale={s_scale}  "
          f"n{n_range} k{k_range}  fill={pascal.sum()}/{len(pascal)}")

# ==================== 渲染三套方案 ====================
for scheme_key, scheme in MOBIUS_SCHEMES.items():
    out_name = f'UF22_帕斯卡Mobius_{scheme_key}.png'
    out_path = os.path.join(od, out_name)
    print(f"\n渲染方案 {scheme_key}: {scheme['label']}")
    render_one_scheme(w_grid, interior, ext, z, dz, esc_iter, scheme, out_path)

print("\n===== All done =====")
