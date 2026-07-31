#!/usr/bin/env python3
"""Glynn f(z)=z^1.5 - 0.5 — 创新对比渲染"""
import numpy as np
from PIL import Image
from pathlib import Path

TARGET_DIR = Path(r"D:\AAA我的文件\PKS_千禧难题_GitHub版\02_应用科技\20_分形研究\05_julia-set分形相关")
POWER = 1.5
C = -0.5
MAX_ITER = 400

def glynn_field(power, c, xlim, ylim, W, H, max_iter=400):
    xs = np.linspace(xlim[0], xlim[1], W)
    ys = np.linspace(ylim[1], ylim[0], H)
    xv, yv = np.meshgrid(xs, ys)
    z = xv + 1j*yv
    escaped = np.full(z.shape, False)
    mu = np.full(z.shape, np.nan)
    for n in range(max_iter):
        mask = ~escaped & (np.abs(z) < 2.0)
        if not mask.any(): break
        # z^1.5 — 主分支
        r = np.abs(z[mask])
        theta = np.angle(z[mask])
        z[mask] = r**power * np.exp(1j*theta*power) + c
        newly = np.abs(z[mask]) >= 2.0
        if newly.any():
            idx = np.where(mask)[0][newly] if mask.ndim==1 else np.argwhere(mask)[newly]
            if mask.ndim == 1:
                escaped[idx] = True
                r2 = np.abs(z[idx])
                mu[idx] = n + 1 - np.log(np.log(r2)/np.log(2))/np.log(power)
            else:
                escaped[tuple(idx.T)] = True
                r2 = np.abs(z[tuple(idx.T)])
                mu[tuple(idx.T)] = n + 1 - np.log(np.log(r2)/np.log(2))/np.log(power)
    return mu, ~escaped

def auto_window(power, c, aspect=1.0):
    span = 2.6
    return [-span*aspect, span*aspect], [-span, span]

def render(mu, inner):
    mu_f = mu.copy()
    mu_f[np.isnan(mu_f)] = -1
    img = np.zeros((*mu.shape, 3), dtype=np.uint8)
    # 内点 (true Julia set) — 深色
    img[inner] = [10, 5, 20]
    # 逃逸点 — 橙红到绿棕
    esc = ~np.isnan(mu)
    v = mu[esc]; vn = (v - v.min()) / (v.max() - v.min() + 1e-12)
    # 参考图色系：橙红(57.5%)→绿棕(36.5%)→暗红(6%)
    r = np.zeros_like(vn); g = np.zeros_like(vn); b = np.zeros_like(vn)
    lo = vn < 0.575
    r[lo] = 210 + 30*vn[lo]/0.575; g[lo] = 53 + 140*vn[lo]/0.575; b[lo] = 0 + 23*vn[lo]/0.575
    mid = (vn >= 0.575) & (vn < 0.94)
    t2 = (vn[mid]-0.575)/0.365
    r[mid] = 227 - 60*t2; g[mid] = 150 + 40*t2; b[mid] = 13 + 10*t2
    hi = vn >= 0.94
    t3 = (vn[hi]-0.94)/0.06
    r[hi] = 167 - 90*t3; g[hi] = 188 - 100*t3; b[hi] = 22 + 5*t3
    img[esc, 0] = np.clip(r, 0, 255).astype(np.uint8)
    img[esc, 1] = np.clip(g, 0, 255).astype(np.uint8)
    img[esc, 2] = np.clip(b, 0, 255).astype(np.uint8)
    return img

print(f"Glynn f(z)=z^{POWER} {C:+}", flush=True)
xlim, ylim = auto_window(POWER, C, 0.633)
W, H, ss = 1024, 608, 2
mu, inner = glynn_field(POWER, C, xlim, ylim, W*ss, H*ss, MAX_ITER)
print(f"  inner: {inner.sum()/inner.size*100:.2f}%")
img = render(mu, inner)
img = np.array(Image.fromarray(img).resize((W, H), Image.LANCZOS))
out = TARGET_DIR / f"Glynn_z1p5_c-0p5_创新_2026-07-20.png"
Image.fromarray(img).save(out, optimize=True)
print(f"  saved: {out.name} ({out.stat().st_size//1024}KB)")

# 对比图：左侧 -0.2 参考，右侧 -0.5 创新
ref = Image.open(TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_2026-07-18.png")
gap = 16
cmp_w = ref.size[0] + gap + img.shape[1]
cmp_h = max(ref.size[1], img.shape[0])
cmp = Image.new('RGB', (cmp_w, cmp_h), (20, 20, 30))
cmp.paste(ref, (0, 0))
label_img = Image.fromarray(img)
cmp.paste(label_img, (ref.size[0] + gap, 0))
from PIL import ImageDraw
d = ImageDraw.Draw(cmp)
d.text((8, 8), "参考: f(z)=z^1.5-0.2", fill=(200, 200, 200))
d.text((ref.size[0]+gap+8, 8), "创新: f(z)=z^1.5-0.5", fill=(200, 200, 200))
cmp_out = TARGET_DIR / "Glynn_z1p5_c-0p2_vs_c-0p5_对比_2026-07-20.png"
cmp.save(cmp_out, optimize=True)
print(f"  comparison: {cmp_out.name} ({cmp_out.stat().st_size//1024}KB)")