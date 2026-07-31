#!/usr/bin/env python3
"""v7b: GPU轨迹密度 — C-plane标量场, 轨道空间填充率"""
import cupy as cp, numpy as np, math, cmath, time, os
from PIL import Image, ImageDraw

OUT_DIR = "/root/invM_v7"; os.makedirs(OUT_DIR, exist_ok=True)
W, H = 3000, 3000; SCALE = 160; N_ITER = 3000; BL = 50

# ═══ GPU C-plane密度 ═══
print(f"[1] GPU密度场 W={W//2}  iter={N_ITER}...")
t0 = time.time()
RW, RH = W//2, H//2
xs = cp.linspace(-W/2/SCALE, W/2/SCALE, RW, dtype=cp.float64)
ys = cp.linspace(-H/2/SCALE, H/2/SCALE, RH, dtype=cp.float64)
X, Y = cp.meshgrid(xs, ys); C = X + 1j*Y
rC = cp.abs(C); rC = cp.maximum(rC, 1e-13)
ce = (rC**(-1.0))*cp.exp(1j*(-1.0)*cp.angle(C))
R2 = BL**2

zr = cp.zeros_like(ce); zi = cp.zeros_like(ce)
alive = cp.ones(ce.shape, dtype=bool)
# 轨道密度: TIA (超吸引中心→极大)
sum_tia_re=cp.zeros(ce.shape); sum_tia_im=cp.zeros(ce.shape, dtype=cp.float64)
cnt=cp.zeros(ce.shape,dtype=cp.int32)

for n in range(N_ITER):
    if not cp.any(alive): break
    za = zr[alive]+1j*zi[alive]; ca = ce[alive]; zn = za*za+ca
    rn_re=(cp.real(zn)-cp.real(za))/(cp.abs(zn)+1e-30)
    rn_im=(cp.imag(zn)-cp.imag(za))/(cp.abs(zn)+1e-30)
    sum_tia_re[alive]+=rn_re; sum_tia_im[alive]+=rn_im
    cnt[alive]+=1
    zr[alive]=cp.real(zn); zi[alive]=cp.imag(zn)
    m2=cp.real(zn)**2+cp.imag(zn)**2; alive[alive]=~(m2>R2)

tia_re=cp.asnumpy(sum_tia_re/cp.maximum(cnt,1))
tia_im=cp.asnumpy(sum_tia_im/cp.maximum(cnt,1))
density=np.sqrt(tia_re**2+tia_im**2)
bounded=cp.asnumpy(alive)
density[bounded]=0  # 有界区(=水滴内)压0, 纹理放在逃逸区(=水滴外)
del X,Y,C,ce,zr,zi,sum_tia_re,sum_tia_im,cnt,alive; cp.get_default_memory_pool().free_all_blocks()
print(f"  GPU: {time.time()-t0:.1f}s")

# ═══ 渲染 ═══
print("[2] 渲染...")
t0 = time.time()
from scipy.ndimage import zoom, gaussian_filter
d_big = zoom(density, (W/density.shape[0], W/density.shape[1]), order=1)
d_big = gaussian_filter(d_big, sigma=0.8)

# log压缩
valid = d_big > 0
if valid.any():
    rho = d_big[valid] + 1; log_h = np.log(rho)
    vm, vx = log_h.min(), log_h.max()
    norm_raw = (log_h - vm)/(vx - vm + 1e-12)
    norm = np.zeros_like(d_big)
    norm[valid] = 1 - norm_raw  # 越小|z|→越亮

# plasma色板
from matplotlib import colormaps as cms
cm = cms['plasma']
colors = cm(norm)[:,:,:3] if valid.any() else np.ones((W,W,3))
img_arr = (colors*255).astype(np.uint8)

# 水滴轮廓
dp = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c2 = 0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv = 1.0/c2
    dp.append((int(W/2+cv.real*SCALE), int(H/2-cv.imag*SCALE)))

img_pil = Image.fromarray(img_arr).convert('RGBA')
dr = ImageDraw.Draw(img_pil)
dr.line(dp, fill=(255,255,255,220), width=4)
dr.text((10,10), f"v7b 平均|z|  C-space GPU {N_ITER}iter", fill=(255,255,255,200))
img_pil = img_pil.rotate(90, expand=True, resample=Image.BILINEAR)
img_pil = img_pil.resize((1500,1500), Image.LANCZOS)
out = os.path.join(OUT_DIR, "invM_v7b_density.png")
img_pil.save(out)
print(f"→ {out}  ({time.time()-t0:.0f}s)")
