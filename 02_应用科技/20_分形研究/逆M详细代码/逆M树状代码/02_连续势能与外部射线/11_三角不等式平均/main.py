#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF11 三角不等式平均 (TIA) — 轨道比值累加

TIA 公式:  r_n = |z_{n+1} - z_n| / |z_{n+1}|,  TIA = (1/N) * Σ r_n

逆M 适配:
  - 映射 c_eff = 1/c  (A=-1 的幂映射)
  - 正M 着色于集合**外部**, 逆M 着色于水滴**内部**(ext=逃逸区)
  - 外部(interior, 非逃逸)统一深底, 不显示 TIA
  - 用 plasma 色板归一化 TIA
"""
import numpy as np, matplotlib.pyplot as plt, os

od = os.path.dirname(os.path.abspath(__file__))

# ====== 视窗 (与其他算法统一) ======
TIP = 4.0; B = -4/3; HSP = 1.6242719100; M = 0.5
R0, R1 = B - M, TIP + M
I0, I1 = -HSP - M, HSP + M
W = 3600
H = int(W * (R1 - R0) / (I1 - I0))
MI = 200; BL = 50; A = -1

# ====== 引擎: 逆M 映射 c_eff = 1/c ======
x = np.linspace(R0, R1, W)
y = np.linspace(I0, I1, H)
X, Y = np.meshgrid(x, y)
co = X + 1j * Y

eps = 1e-12
sf = np.abs(co) > eps
ce = np.zeros_like(co, dtype=np.complex128)
ce[sf] = (abs(co[sf]) ** A) * np.exp(1j * A * np.angle(co[sf]))
ce[~sf] = 1e6   # 原点保护

z = np.zeros_like(ce)
alive = np.ones(ce.shape, dtype=bool)
sum_r = np.zeros(ce.shape, dtype=np.float64)   # 累加 r_n
cnt = np.zeros(ce.shape, dtype=np.int32)        # 计数 N

for i in range(MI):
    if not alive.any():
        break
    idx = np.where(alive)
    za = z[idx].copy()
    ca = ce[idx].copy()
    z_new = za ** 2 + ca
    # r_n = |z_{n+1} - z_n| / |z_{n+1}|
    dz_step = np.abs(z_new - za)
    abs_new = np.abs(z_new) + 1e-30
    rn = dz_step / abs_new
    sum_r[idx] += rn
    cnt[idx] += 1
    z[idx] = z_new
    escaped = (z_new.real ** 2 + z_new.imag ** 2 > BL ** 2)
    alive[idx] &= ~escaped

interior = ~alive
ext = alive

# ====== TIA 平均 ======
tia = np.where(cnt > 0, sum_r / np.maximum(cnt, 1), 0.0)

# ====== 渲染 ======
img = np.full((H, W, 3), [0.04, 0.04, 0.09])   # 外部深底

if ext.any():
    tv = tia[ext]
    # 对数归一化: 避免极端值(最大值819)压暗整体
    tv_log = np.log1p(tv)
    tmin, tmax = tv_log.min(), tv_log.max()
    norm = (tv_log - tmin) / (tmax - tmin + 1e-12)
    from matplotlib import colormaps as cms
    cmap = cms['plasma']
    colors = cmap(norm)[..., :3]
    img[ext] = colors

# 内外边界黑色描边, 强化水滴轮廓
bd_h = np.zeros((H, W), dtype=bool)
bd_v = np.zeros((H, W), dtype=bool)
bd_h[:, :-1] = (interior[:, :-1] != interior[:, 1:])
bd_v[:-1, :] = (interior[:-1, :] != interior[1:, :])
boundary = bd_h | bd_v
img[boundary] = [0.0, 0.0, 0.0]

img = np.rot90(img, k=3)

out = os.path.join(od, "UF11_三角不等式平均.png")
fig, ax = plt.subplots(figsize=(8, 8 * H / W), dpi=150)
ax.imshow(img, extent=[I0, I1, R0, R1], origin='lower')
ax.axis('off')
plt.tight_layout(pad=0)
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='black')
plt.close()

print(f"UF11 TIA: ext={ext.sum()}, int={interior.sum()}, "
      f"tia_range=[{tia[ext].min():.4f},{tia[ext].max():.4f}] done -> {out}")
