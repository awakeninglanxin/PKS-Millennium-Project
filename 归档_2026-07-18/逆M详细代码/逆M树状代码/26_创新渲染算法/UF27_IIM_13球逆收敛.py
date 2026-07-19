#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF27 IIM逆收敛 — 13球角度折半 + 二叉预像树 + tzimtzum收缩

关键词: IIM / MIIM / angle halving / binary preimage tree
        Julia boundary as attractor / tzimtzum
"""
import numpy as np, matplotlib.pyplot as plt, os
od = os.path.dirname(os.path.abspath(__file__))

DPI, MI = 200, 60
R2 = 2500
W, H = 2400, 2400
x = np.linspace(-3.5, 3.5, W)
y = np.linspace(-3.5, 3.5, H)
X, Y = np.meshgrid(x, y)

co = X + 1j * Y

def mandel_iter(c):
    z = np.zeros_like(c)
    alive = np.ones(c.shape, bool)
    for i in range(MI):
        if not alive.any(): break
        z[alive] = z[alive]**2 + c[alive]
        alive &= (z.real**2 + z.imag**2 < R2)
    return alive, z

def inv_iter_single(z0, c=0+0j, depth=8):
    tree = {0: [z0]}
    for d in range(1, depth + 1):
        prev = tree[d - 1]
        cur = []
        for z in prev:
            w = np.sqrt(z - c)
            cur.extend([+w, -w])
        tree[d] = cur
    return tree

interior, _ = mandel_iter(co)

BG = np.array([0.03, 0.03, 0.12])
INNER = np.array([0.06, 0.08, 0.22])
L1 = np.array([0.95, 0.75, 0.28])
L2 = np.array([0.88, 0.45, 0.18])
L3 = np.array([0.75, 0.25, 0.55])
CNTR = np.array([0.99, 0.95, 0.85])

img = np.full((H, W, 3), BG)
img[interior] = INNER

c_val = 0.0 + 0.0j
N_SPHERES = 12
R_start = 2.6
seeds = [R_start * np.exp(1j * 2 * np.pi * k / N_SPHERES) for k in range(N_SPHERES)]

all_tree = {}
for seed in seeds:
    all_tree[seed] = inv_iter_single(seed, c_val, depth=6)

def to_pixel(z):
    px = int((z.real + 3.5) / 7.0 * W)
    py = int((3.5 - z.imag) / 7.0 * H)
    return np.clip(px, 0, W - 1), np.clip(py, 0, H - 1)

for depth in range(1, 5):
    sx, sy = 2.5 - depth * 0.5, 2.0 - depth * 0.4
    alpha = 0.3 + depth * 0.15
    color = [L1, L2, L3, CNTR][min(depth - 1, 3)]
    for seed in seeds:
        for z in all_tree[seed].get(depth, []):
            px, py = to_pixel(z)
            r_pt = int(max(1.5, 5 - depth * 0.8))
            for dx in range(-r_pt, r_pt + 1):
                for dy in range(-r_pt, r_pt + 1):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < W and 0 <= ny < H:
                        d2 = dx * dx + dy * dy
                        if d2 <= r_pt * r_pt:
                            fade = 1.0 - d2 / (r_pt * r_pt)
                            img[ny, nx] = (1 - fade * alpha) * img[ny, nx] + fade * alpha * np.array(color)

px_c, py_c = to_pixel(0)
R_c = 8
for dx in range(-R_c, R_c + 1):
    for dy in range(-R_c, R_c + 1):
        nx, ny = px_c + dx, py_c + dy
        if 0 <= nx < W and 0 <= ny < H:
            d2 = dx * dx + dy * dy
            if d2 <= R_c * R_c:
                f = 1.0 - d2 / (R_c * R_c)
                img[ny, nx] = (1 - f) * img[ny, nx] + f * CNTR

for seed in seeds:
    px, py = to_pixel(seed)
    R_s = 6
    for dx in range(-R_s, R_s + 1):
        for dy in range(-R_s, R_s + 1):
            nx, ny = px + dx, py + dy
            if 0 <= nx < W and 0 <= ny < H:
                d2 = dx * dx + dy * dy
                if d2 <= R_s * R_s:
                    f = 1.0 - d2 / (R_s * R_s)
                    img[ny, nx] = (1 - f) * img[ny, nx] + f * np.array([0.35, 0.55, 0.95])

img_rot = np.rot90(img, k=1)

fig, ax = plt.subplots(1, 1, figsize=(16, 16), facecolor='#08081E')
ax.imshow(img_rot, extent=[-3.5, 3.5, -3.5, 3.5])
ax.set_xlim(-3.5, 3.5)
ax.set_ylim(-3.5, 3.5)
ax.set_facecolor('#08081E')
ax.set_xticks([])
ax.set_yticks([])

# Annotations
ax.annotate('outer 12', xy=(0, 2.65), fontsize=11, color='#5588DD',
            ha='center', va='bottom')
ax.annotate('+/- sqrt(z-c)', xy=(2.0, 2.0), fontsize=10, color='#CC8844',
            ha='center', va='center')
ax.annotate('angle halving\n720->360 fold back', xy=(2.4, 0.5), fontsize=9,
            color='#BB66AA', ha='center', va='center')
ax.annotate('center 1\n(tzimtzum)', xy=(0, -0.45), fontsize=11, color='#FFDD88',
            ha='center', va='top')
ax.annotate('binary preimage tree 2^n', xy=(-2.3, -1.5), fontsize=10,
            color='#DD6644', ha='center', va='center', style='italic')

ax.set_title('IIM Inverse Convergence   |   Outer 12  ->  +/- sqrt(z-c)  ->  Center 1',
             fontsize=14, color='#CCCCDD', pad=12, fontweight='normal')

# Legend labels
for label, color, y_off in [
    ('depth=1  angle/2', L1, 0.12),
    ('depth=2  angle/4', L2, 0.24),
    ('depth=3  angle/8', L3, 0.36),
    ('depth>=4 -> unit circle', CNTR, 0.48),
]:
    ax.annotate(label, xy=(3.15, 3.0 - y_off), fontsize=8, color='#AAAAAA',
                ha='left', va='center')
    ax.add_patch(plt.Rectangle((3.35, 3.06 - y_off), 0.12, 0.06,
                facecolor=list(color) + [0.85], edgecolor='none', transform=ax.transData,
                clip_on=False))

out = os.path.join(od, 'UF27_IIM_13球逆收敛_角度折半.png')
plt.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='#08081E')
plt.close()
print(f'UF27 IIM: N_spheres=12 depth=6 -> {out}')
