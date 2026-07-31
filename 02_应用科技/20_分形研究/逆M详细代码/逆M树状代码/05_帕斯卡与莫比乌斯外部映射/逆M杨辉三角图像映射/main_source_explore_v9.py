#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22+ 六向帕斯卡源图 — 参数探索 + 颜色分组渲染

四张源图对照:
  A. p=2 (经典Sierpinski) — 黑白
  B. p=3 (三色mod 3) — 余数分色
  C. p=2 方向分色 — 6个楔形各一种颜色
  D. p=2 行号彩虹 — n越深颜色越冷

调参:
  N_ROWS (行数) — 越大细节越丰富, fill率降低
  scale — 控制三角在画面中的大小
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, math
from matplotlib.colors import hsv_to_rgb

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

od = os.path.dirname(os.path.abspath(__file__))

# ==================== 帕斯卡三角生成 ====================
def make_pascal(N_ROWS, P):
    """生成帕斯卡三角 mod P"""
    p = np.zeros((N_ROWS, N_ROWS), dtype=np.int8)
    p[0, 0] = 1 % P
    for n in range(1, N_ROWS):
        p[n, 0] = p[n, n] = 1 % P
        for k in range(1, n):
            p[n, k] = (p[n-1, k] + p[n-1, k-1]) % P
    return p

# ==================== 六向帕斯卡查询 (多个返回) ====================
SR3 = np.sqrt(3)
ANGLES = np.array([m * np.pi / 3 for m in range(6)])
RC, RS = np.cos(-ANGLES), np.sin(-ANGLES)

def hex_pascal_query(z_re, z_im, pascal_mod, N_ROWS):
    """
    六向帕斯卡查询 (纯, 无周期延拓)
    返回: brightness, best_n, best_dir, best_mod
    """
    N = len(z_re)
    brightness = np.zeros(N, dtype=np.float64)
    best_n = np.full(N, -1, dtype=np.int64)
    best_dir = np.full(N, -1, dtype=np.int8)
    best_mod = np.zeros(N, dtype=np.int8)

    for m in range(6):
        zr = z_re * RC[m] - z_im * RS[m]
        zi = z_re * RS[m] + z_im * RC[m]
        kf = 2.0 * zi / SR3; nf = zr + zi / SR3
        nr = np.round(nf).astype(np.int64); kr = np.round(kf).astype(np.int64)
        v = (kr >= 0) & (kr <= nr) & (nr >= 0) & (nr < N_ROWS)
        if v.any():
            vi = np.where(v)[0]
            vals = pascal_mod[nr[vi], kr[vi]].astype(np.float64)
            better = vals > brightness[vi]
            if better.any():
                ui = vi[better]
                brightness[ui] = vals[better]
                best_n[ui] = nr[ui]
                best_dir[ui] = m
                best_mod[ui] = pascal_mod[nr[ui], kr[ui]]

    return brightness, best_n, best_dir, best_mod

# ==================== 生成源图 ====================
SRC = 1200
off = SRC // 2
DPI = 150
N_ROWS = 512

# 坐标网格: 三角占画面85%
src_scale = N_ROWS / (off * 0.85)
sx = np.arange(SRC); sy = np.arange(SRC)
SX, SY = np.meshgrid(sx, sy)
sz_re = (SX - off) / src_scale
sz_im = (SY - off) / src_scale  # Y轴正方向朝上
sz_re_flat = sz_re.ravel(); sz_im_flat = sz_im.ravel()

print(f"N_ROWS={N_ROWS}  src_scale={src_scale:.4f}  SRC={SRC}")
print(f"坐标范围: re=[{sz_re_flat.min():.0f},{sz_re_flat.max():.0f}]  im=[{sz_im_flat.min():.0f},{sz_im_flat.max():.0f}]")

# ==================== A. p=2 经典Sierpinski 黑白 ====================
print("[A] p=2 经典...")
p2 = make_pascal(N_ROWS, 2)
b2, n2, d2, m2 = hex_pascal_query(sz_re_flat, sz_im_flat, p2, N_ROWS)
b2_img = b2.reshape(SRC, SRC)
print(f"  fill={b2.mean()*100:.1f}%")

# ==================== B. p=3 三色分组 ====================
print("[B] p=3 三色...")
p3 = make_pascal(N_ROWS, 3)
b3, n3, d3, m3 = hex_pascal_query(sz_re_flat, sz_im_flat, p3, N_ROWS)
b3_img = b3.reshape(SRC, SRC)
m3_img = m3.reshape(SRC, SRC)

# p=3 的余数: 1=青, 2=品红 (0=黑底)
rgb3 = np.zeros((SRC, SRC, 3))
mask_1 = m3_img == 1; mask_2 = m3_img == 2
rgb3[mask_1] = [0.1, 0.8, 0.8]   # 青色 (余1)
rgb3[mask_2] = [0.9, 0.3, 0.7]   # 品红 (余2)
print(f"  fill={b3.mean()*100:.1f}%  mod=1:{m3_img[mask_1].size/1e3:.0f}k  mod=2:{m3_img[mask_2].size/1e3:.0f}k")

# ==================== C. p=2 方向分色 (6楔形) ====================
print("[C] p=2 方向分色...")
d2_img = d2.reshape(SRC, SRC)
# 6个方向各一种颜色
dir_colors = [
    [1.0, 0.2, 0.1],  # m=0: 红
    [1.0, 0.6, 0.0],  # m=1: 橙
    [0.2, 0.8, 0.1],  # m=2: 绿
    [0.1, 0.6, 0.9],  # m=3: 蓝
    [0.3, 0.2, 0.9],  # m=4: 紫
    [0.8, 0.2, 0.9],  # m=5: 洋红
]
rgb_dir = np.zeros((SRC, SRC, 3))
for m in range(6):
    mask = d2_img == m
    rgb_dir[mask] = dir_colors[m]
print(f"  各方向像素: {[(d2_img==m).sum() for m in range(6)]}")

# ==================== D. p=2 行号彩虹 ====================
print("[D] p=2 行号彩虹...")
n2_img = n2.reshape(SRC, SRC)
n2_norm = np.clip(n2_img.astype(np.float64) / N_ROWS, 0, 1)
# 暖色(n小)→冷色(n大)
hue_d = 0.15 - n2_norm * 0.6  # 红橙(n≈0) → 蓝紫(n≈512)
hue_d[hue_d < 0] += 1.0
sat_d = np.ones_like(hue_d) * 0.85
val_d = np.clip(0.3 + 0.7 * b2_img, 0, 1)
hsv_d = np.stack([hue_d, sat_d, val_d], axis=-1)
rgb_rainbow = hsv_to_rgb(hsv_d)
# 未命中→黑色
rgb_rainbow[b2_img < 0.5] = [0.02, 0.02, 0.06]
print(f"  n范围: [{n2_img.min()}, {n2_img.max()}]")

# ==================== 输出四宫格 ====================
fig, axes = plt.subplots(2, 2, figsize=(16, 16), dpi=DPI)
ext = [-off/src_scale, off/src_scale, -off/src_scale, off/src_scale]

# A
axes[0,0].imshow(b2_img, cmap='gray_r', extent=ext, interpolation='bilinear')
axes[0,0].set_title(f'A. p=2 Classic Sierpinski\n'
                     f'fill={b2.mean()*100:.1f}%  N_ROWS={N_ROWS}', fontsize=12)
axes[0,0].set_aspect('equal')

# B
axes[0,1].imshow(rgb3, extent=ext, interpolation='bilinear')
axes[0,1].set_title(f'B. p=3 Trinomial mod 3\n'
                     f'Cyan=mod1  Magenta=mod2  fill={b3.mean()*100:.1f}%', fontsize=12)
axes[0,1].set_aspect('equal')

# C
axes[1,0].imshow(rgb_dir, extent=ext, interpolation='bilinear')
axes[1,0].set_title(f'C. p=2 Direction-Colored (6 wedges)\n'
                     f'Red/Orange/Green/Blue/Purple/Magenta', fontsize=12)
axes[1,0].set_aspect('equal')

# D
axes[1,1].imshow(rgb_rainbow, extent=ext, interpolation='bilinear')
axes[1,1].set_title(f'D. p=2 Row Rainbow\n'
                     f'Red(n≈0)→Blue(n≈{N_ROWS})  n warmer→colder', fontsize=12)
axes[1,1].set_aspect('equal')

for ax in axes.flat:
    ax.set_xlabel('Re'); ax.set_ylabel('Im')

fig.suptitle(f'6-Way Pascal Triangle — Parameter & Color Exploration\n'
             f'Z(n,k)=(n-k)+k·e^(iπ/3)  Z_360=Z·e^(imπ/3)  m=0..5',
             fontsize=15, y=1.01)
plt.tight_layout()
out = os.path.join(od, 'UF22_六向帕斯卡_参数探索v9.png')
fig.savefig(out, dpi=DPI, facecolor='white', bbox_inches='tight')
plt.close()
print(f"\nDone: {out} ({os.path.getsize(out)//1024}KB)")

# 单项单独保存
for name, data, is_rgb in [
    ('A_p2_classic', b2_img, False),
    ('B_p3_trinomial', rgb3, True),
    ('C_p2_dircolor', rgb_dir, True),
    ('D_p2_rainbow', rgb_rainbow, True),
]:
    fn = os.path.join(od, f'UF22_六向帕斯卡_{name}_v9.png')
    if is_rgb:
        plt.imsave(fn, np.clip(data, 0, 1))
    else:
        plt.imsave(fn, data, cmap='gray_r')
    print(f"  {fn} ({os.path.getsize(fn)//1024}KB)")
