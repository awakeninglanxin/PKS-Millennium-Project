#!/usr/bin/env python3
"""v7: 轨道密度法 (Orbit Density) — z-plane直方图 + log压缩"""
import numpy as np, math, cmath, time, os
from PIL import Image
from scipy.ndimage import zoom

OUT_DIR = "/root/invM_v7"; os.makedirs(OUT_DIR, exist_ok=True)
W, H = 2400, 2400; SCALE = 160; Z_BOUND = 5.0
N_ITER = 8000   # 高迭代
BL = 50

# ═══ 1. 找水滴内部C点 ═══
print("[1] 找水滴内部(有界)采样点...")
t0 = time.time()
STEP = 5  # 每5×5采样1个C点
RW, RH = W//STEP//2, H//STEP//2
xs = np.linspace(-W/2/SCALE, W/2/SCALE, RW)
ys = np.linspace(-H/2/SCALE, H/2/SCALE, RH)
CX, CY = np.meshgrid(xs, ys); C = CX+1j*CY
rC = np.abs(C); rC = rC.clip(1e-13); thC = np.angle(C)
ce = (rC**(-1.0)) * np.exp(1j*(-1.0)*thC)

zr, zi = np.zeros_like(ce), np.zeros_like(ce)
alive = np.ones(ce.shape, dtype=bool)
for n in range(200):
    if not alive.any(): break
    z = zr[alive]+1j*zi[alive]; ca = ce[alive]; zn = z*z+ca
    zr[alive], zi[alive] = zn.real, zn.imag
    m2 = zn.real**2+zn.imag**2; alive[alive]=~(m2>BL**2)
bounded = alive
bounded_ce = ce[bounded]; n_b = len(bounded_ce)
# 采样最多5000个C点
n_sample = min(n_b, 5000)
idx = np.random.choice(n_b, n_sample, replace=False)
samples = bounded_ce[idx]
print(f"  {n_b}有界点 → 采样{n_sample}个, {time.time()-t0:.1f}s")

# ═══ 2. 轨道直方图 ═══
print(f"[2] 轨道直方图 (iter={N_ITER}, z∈[±{Z_BOUND}])...")
t0 = time.time()
hist = np.zeros((W, H), dtype=np.float64)
Z_SC = W/(2*Z_BOUND)  # z→像素映射

for ci, ce_val in enumerate(samples):
    z = 0+0j
    for n in range(N_ITER):
        z = z*z + ce_val; m2 = z.real**2+z.imag**2
        if m2 > BL**2: break
        if abs(z.real)<Z_BOUND and abs(z.imag)<Z_BOUND:
            hx = int((z.real+Z_BOUND)*Z_SC)
            hy = int((z.imag+Z_BOUND)*Z_SC)
            if 0<=hx<W and 0<=hy<H: hist[hy,hx]+=1
    if (ci+1)%1000==0: print(f"  {ci+1}/{n_sample}...")
print(f"  直方图: {time.time()-t0:.0f}s")

# ═══ 3. 对数压缩 ═══
print("[3] 对数压缩 + 渲染...")
rho = hist + 1; log_h = np.log(rho)
vm = log_h[log_h>0].min(); vx = log_h.max()
norm = 1 - (log_h - vm)/(vx - vm + 1e-12)  # 1=低密度白, 0=高密度黑

# plasma色板渲染高密度区
from matplotlib import colormaps as cms
colors = cms['plasma'](norm)[:,:,:3]
img_arr = (colors * 255).astype(np.uint8)

# 叠加水滴轮廓
from PIL import Image, ImageDraw
from matplotlib.path import Path
dp = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c2 = 0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv = 1.0/c2
    dp.append((W/2+cv.real*SCALE*W/H, H/2-cv.imag*SCALE*H/W))
droplet_path = Path(dp)

img_pil = Image.fromarray(img_arr, 'RGB').convert('RGBA')
dr = ImageDraw.Draw(img_pil)
dr.line([(int(x), int(y)) for x,y in dp], fill=(180,180,255,200), width=4)
dr.text((10,10), f"v7 轨道密度 {n_sample}C点×{N_ITER}iter log压缩", fill=(255,255,255,220))
img_pil = img_pil.rotate(90, expand=True, resample=Image.BILINEAR)

out = os.path.join(OUT_DIR, "invM_v7_orbit_density.png")
img_pil.resize((2000,2000), Image.LANCZOS).save(out)
print(f"→ {out}")
