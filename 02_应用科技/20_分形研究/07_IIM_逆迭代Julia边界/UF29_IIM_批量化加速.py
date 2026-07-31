#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF29 IIM 逆迭代 numpy批量化加速版 — z -> +/-sqrt(z-c)

与UF28对比: 用numpy批量处理替代Python纯循环, 8M点从3min->20s
"""
import numpy as np, matplotlib.pyplot as plt, os, time
od = os.path.dirname(os.path.abspath(__file__))

DPI, W, H, BATCH = 180, 2400, 2400, 200_000
R2 = 2500

def miim_batch(c, span=3.0, n_steps=200, batch=200_000, hit_limit=60, seed=42):
    """批量IIM修正版：每个粒子独立随机游走 n_steps 步，每步都画点，避免 collapse 到单像素。"""
    np.random.seed(seed)
    buf = np.zeros((H, W), dtype=np.int32)
    half = span / 2
    # 初始化 batch 个独立粒子在逃逸圆上
    z = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(batch))
    t0 = time.time()
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
        # 映射到画布
        re, im = z.real, z.imag
        valid = (np.abs(re) < half) & (np.abs(im) < half)
        if valid.any():
            px = ((im[valid] + half) / span * W).astype(int)
            py = ((half - re[valid]) / span * H).astype(int)
            px = np.clip(px, 0, W - 1); py = np.clip(py, 0, H - 1)
            np.add.at(buf, (py, px), 1)
            # 热门点所在粒子重置，避免局部过度堆积
            hot = buf[py, px] > hit_limit
            if hot.any():
                reset_idx = np.where(valid)[0][hot]
                z[reset_idx] = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(len(reset_idx)))
        # 越界粒子重置
        out = ~valid
        if out.any():
            z[out] = 2.0 * np.exp(1j * 2 * np.pi * np.random.random(out.sum()))
        if step % 50 == 0 or step == n_steps - 1:
            print(f'  step {step}, nonzero={np.count_nonzero(buf)}, max-hit={buf.max()}, {time.time()-t0:.0f}s', flush=True)
    return buf

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

cases = [
    ("c=0  unit-circle",  0.0+0.0j,  2.2, 4_000_000, 40, (1.0,1.0,0.85), (0.35,0.55,0.95)),
    ("c=-1  dragon",     -1.0+0.0j,  2.0, 8_000_000, 50, (1.0,0.85,0.30), (0.55,0.30,0.20)),
    ("c=i  spiral",       0.0+1.0j,  2.0, 8_000_000, 50, (0.55,0.90,1.0), (0.20,0.45,0.75)),
    ("c=-0.745+0.113i  seahorse", -0.74543+0.11301j, 2.5, 8_000_000, 200,
     (1.0,0.55,0.90), (0.60,0.20,0.55)),
]

fig, axes = plt.subplots(2, 2, figsize=(18, 18), facecolor='#08081E')
axes = axes.ravel()
print(f'UF29 IIM Batch (numpy vec, {BATCH//1000}K batch)\n')

for idx, (label, c_val, span, n_pts, hit, hi, lo) in enumerate(cases):
    print(f'IIM {label} ...', flush=True)
    buf = miim_batch(c_val, span=span, n_steps=200, hit_limit=hit)
    img = buf_to_img(buf, hi=hi, lo=lo)
    ax = axes[idx]
    ax.imshow(np.rot90(img, k=1), extent=[-span/2, span/2, -span/2, span/2])
    ax.set_xlim(-span/2, span/2); ax.set_ylim(-span/2, span/2)
    ax.set_facecolor('#08081E')
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f'IIM: z -> +/- sqrt(z-c)  |  {label}',
                 fontsize=11, color='#CCCCDD', pad=8)

fig.suptitle('IIM (Inverse Iteration Method) — Julia Set Boundary as Attractor  |  numpy batch 40M steps/case',
             fontsize=14, color='#AAAACC', y=0.98)

out = os.path.join(od, 'IIM_Julia边界_四经典_v2批量化.png')
plt.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='#08081E')
plt.close()
sz = os.path.getsize(out)
print(f'\n-> {os.path.basename(out)} ({sz//1024}KB)')
print('UF29 done.')
