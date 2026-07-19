#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IIM 逆迭代法 — z -> +/-sqrt(z-c) 绘制 Julia 集边界

关键词: IIM/MIIM + preimages of repelling fixed point
        + binary tree + Julia boundary as attractor
"""
import numpy as np, matplotlib.pyplot as plt, os
od = os.path.dirname(os.path.abspath(__file__))

# ============== 画布配置 ==============
DPI, W, H = 180, 3200, 3200
R2 = 2500; MI = 80

# ============== IIM 逆迭代核心 ==============
def csqrt(z):
    """复数开根号: z -> +/- sqrt(z), 返回两个分支"""
    r = np.abs(z); th = np.angle(z)
    sr = np.sqrt(r); st = th / 2
    p = sr * np.exp(1j * st)
    return p, -p

def miim_render(c, span=3.5, n_steps=400, batch=300_000, hit_limit=80, seed=42):
    """MIIM: 向量化随机游走逆迭代, hit-limit 防止冷段饿死。"""
    np.random.seed(seed)
    buf = np.zeros((H, W), dtype=np.int32)
    half = span / 2
    # 初始化 batch 个独立粒子在逃逸圆上
    z = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(batch))
    for step in range(n_steps):
        w = z - c
        # 避免 w=0 导致 stuck
        bad = np.abs(w) < 1e-14
        if bad.any():
            z[bad] = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(bad.sum()))
            w = z - c
        r = np.sqrt(np.abs(w))
        th = np.angle(w) / 2.0
        p = r * np.exp(1j * th)
        branch = np.random.random(batch) < 0.5
        z = np.where(branch, p, -p)
        # 像素映射 (Re轴朝上)
        re, im = z.real, z.imag
        valid = (np.abs(re) < half) & (np.abs(im) < half)
        if valid.any():
            px = ((im[valid] + half) / span * W).astype(int)
            py = ((half - re[valid]) / span * H).astype(int)
            px = np.clip(px, 0, W - 1); py = np.clip(py, 0, H - 1)
            np.add.at(buf, (py, px), 1)
            # hit-limit: 热门像素所在粒子跳回外区
            hot = buf[py, px] > hit_limit
            if hot.any():
                reset_idx = np.where(valid)[0][hot]
                z[reset_idx] = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(len(reset_idx)))
        # 越界粒子重置
        out = ~valid
        if out.any():
            z[out] = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(out.sum()))
    return buf

# ============== 着色 ==============
def buf_to_img(buf, bg=(0.0,0.0,0.05), hi=(1.0,0.95,0.55), lo=(0.25,0.75,1.0), gamma=0.45):
    alive = buf > 0
    img = np.full((H, W, 3), bg)
    if not alive.any(): return img

    v = np.log1p(buf[alive].astype(np.float64))
    vn = np.clip((v - v.min()) / (v.max() - v.min() + 1e-12), 0, 1)
    vn = vn ** gamma  # 提亮低 hit 区域，让浅灰点变成可见亮线
    for ch in range(3):
        img[alive, ch] = lo[ch] + vn * (hi[ch] - lo[ch])
    return img

# ============== 四种经典 Julia 集 ==============
cases = [
    ("c=0  unit circle",     0.0+0.0j,        2.5, 4_000_000, 40),
    ("c=-1  dragon",         -1.0+0.0j,        2.0, 8_000_000, 50),
    ("c=i  spiral",           0.0+1.0j,        2.0, 6_000_000, 50),
    ("c=-0.745+0.113i  seahorse", -0.74543+0.11301j, 2.5, 6_000_000, 200),
]

fig, axes = plt.subplots(2, 2, figsize=(18, 18), facecolor='#08081E')
axes = axes.ravel()

for idx, (label, c_val, span, n_pts, hit) in enumerate(cases):
    print(f'IIM {label} ...', end=' ', flush=True)
    buf = miim_render(c_val, span=span, n_steps=800, hit_limit=hit)
    img = buf_to_img(buf)
    ax = axes[idx]
    ax.imshow(np.rot90(img, k=1), extent=[-span/2, span/2, -span/2, span/2])
    ax.set_xlim(-span/2, span/2); ax.set_ylim(-span/2, span/2)
    ax.set_facecolor('#08081E')
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f'IIM: z -> +/- sqrt(z - c)  |  {label}',
                 fontsize=11, color='#CCCCDD', pad=8)
    print(f'nonzero={np.count_nonzero(buf)} max-hit={buf.max()}', flush=True)

fig.suptitle('IIM (Inverse Iteration Method) — Julia Set Boundary as Attractor',
             fontsize=14, color='#AAAACC', y=0.98)

out = os.path.join(od, 'IIM_Julia边界_四经典.png')
plt.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='#08081E')
plt.close()
print(f'-> {os.path.getsize(out)//1024}KB')

# ============== 单张大图: seahorse 高精度 ==============
print('IIM seahorse HD ...', end=' ', flush=True)
buf_hd = miim_render(-0.74543+0.11301j, span=2.2, n_steps=800, batch=600_000, hit_limit=80)
img_hd = buf_to_img(buf_hd, hi=(1.0,0.70,0.95), lo=(0.55,0.15,0.60))

fig2, ax2 = plt.subplots(1, 1, figsize=(16, 16), facecolor='#08081E')
ax2.imshow(np.rot90(img_hd, k=1), extent=[-1.1, 1.1, -1.1, 1.1])
ax2.set_xlim(-1.1, 1.1); ax2.set_ylim(-1.1, 1.1)
ax2.set_facecolor('#08081E')
ax2.set_xticks([]); ax2.set_yticks([])
ax2.set_title('IIM Seahorse Julia  |  c = -0.74543 + 0.11301i  |  20M pts',
              fontsize=13, color='#CCCCDD', pad=10)

out_hd = os.path.join(od, 'IIM_Seahorse_Julia_高清.png')
plt.savefig(out_hd, dpi=220, bbox_inches='tight', facecolor='#08081E')
plt.close()
print(f'-> {os.path.getsize(out_hd)//1024}KB')
print('IIM done.')
