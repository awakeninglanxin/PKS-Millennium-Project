#!/usr/bin/env python3
"""v8: DEM ±log(d) — 有界区+log, 逃逸区−log, 内外全纹理"""
import cupy as cp, numpy as np, math, cmath, time, os
from PIL import Image, ImageDraw
from scipy.ndimage import zoom

OUT_DIR = "/root/invM_v8"; os.makedirs(OUT_DIR, exist_ok=True)
W, H = 6000, 6000; SCALE = 320; MI = 400; BL = 50

# ═══ GPU DEM迭代 ═══
print(f"[1] GPU DEM iter={MI}...")
t0 = time.time()
RW, RH = W//2, H//2
xs = cp.linspace(-W/2/SCALE, W/2/SCALE, RW, dtype=cp.float64)
ys = cp.linspace(-H/2/SCALE, H/2/SCALE, RH, dtype=cp.float64)
X, Y = cp.meshgrid(xs, ys); C = X+1j*Y
rC = cp.abs(C); rC = cp.maximum(rC, 1e-13)
ce = (rC**(-1.0))*cp.exp(1j*(-1.0)*cp.angle(C))
R2 = BL**2

zr = cp.zeros_like(ce); zi = cp.zeros_like(ce)
dzr = cp.zeros_like(ce); dzi = cp.zeros_like(ce)
alive = cp.ones(ce.shape, dtype=bool)

for n in range(MI):
    if not cp.any(alive): break
    za = zr[alive]+1j*zi[alive]; ca = ce[alive]
    dza = dzr[alive]+1j*dzi[alive]
    # 导数更新: dz' = 2*z*dz + 1
    dzn = 2*za*dza + 1
    zn = za*za + ca
    zr[alive]=cp.real(zn); zi[alive]=cp.imag(zn)
    dzr[alive]=cp.real(dzn); dzi[alive]=cp.imag(dzn)
    m2=cp.real(zn)**2+cp.imag(zn)**2
    alive[alive]=~(m2>R2)

bounded = cp.asnumpy(alive)
zr_cpu=cp.asnumpy(cp.real(zr)); zi_cpu=cp.asnumpy(cp.real(zi))
# DEM公式
zm = np.sqrt(zr_cpu**2+zi_cpu**2+1e-30)
dzr_cpu=cp.asnumpy(cp.real(dzr)); dzi_cpu=cp.asnumpy(cp.real(dzi)); dzm=np.sqrt(dzr_cpu**2+dzi_cpu**2+1e-30)
d = np.log(zm*zm+1e-30) * zm / (dzm+1e-30)

# 二分棋盘格 (UF1): 角度 × 势能 XOR
pot = np.zeros_like(zm); pot[~bounded] = MI-1 - np.log2(np.maximum(np.log2(zm[~bounded]**2)/2, 1e-12))
pot = np.clip(pot, 0, None)
ang=np.arctan2(zi_cpu,zr_cpu+1e-30)/(2*np.pi)+0.5
nc = np.minimum(pot, 20).astype(int)
er = np.where(nc>0, ang / (2.0**nc), 0)
del X,Y,C,ce,zr,zi,dzr,dzi,alive; cp.get_default_memory_pool().free_all_blocks()
print(f"  GPU: {time.time()-t0:.1f}s")

# ═══ ±log(d) 双面纹理 ═══
print("[2] ±log(d) 渲染...")
t0 = time.time()
d_safe = d + 1e-100
log_d = np.log(d_safe)

# ★ v9: 朝内DEM / 朝外几何XOR梯度 ★
# 像素坐标网格
Y_px_g, X_px_g = np.ogrid[:zm.shape[0], :zm.shape[1]]
Y_px = Y_px_g.astype(float) / zm.shape[0] * (H/SCALE) - H/(2*SCALE)
X_px = X_px_g.astype(float) / zm.shape[1] * (W/SCALE) - W/(2*SCALE)
d_safe = d + 1e-100
shade = np.zeros_like(log_d)

# 朝内(逃逸区): DEM -log(d) 边界发光
shade[~bounded] = np.clip(-np.log(d_safe[~bounded])/5, 0, 1)

# 朝外(有界区): 几何XOR, 密度梯度(边界密→远处疏)
c_ang = (np.arctan2(Y_px, X_px) + np.pi)/(2*np.pi)
c_dist_log = np.log(np.sqrt(X_px**2 + Y_px**2) + 0.01)
d_norm = np.clip(d_safe / 10, 0, 1)
step_grad = 0.003 * np.exp(8.37 * d_norm)  # Δ=0.003×e^{8.37d}
rz_geo = np.floor(c_ang * 360).astype(int)
dr_geo = np.floor(c_dist_log / step_grad).astype(int)
chess_geo = ((rz_geo%2==0)!=(dr_geo%2==0)).astype(float)
from scipy.ndimage import gaussian_filter
chess_soft = gaussian_filter(chess_geo.astype(float), sigma=0.8)
weight = np.exp(-d_norm * 4)
shade[bounded] = np.clip(chess_soft[bounded] * weight[bounded], 0, 1)

# 4种Δ公式对比
from matplotlib import colormaps as cms; cm = cms['plasma']
variants = [
    ("v8_A_0.003e8.37d", lambda dn: 0.003*np.exp(8.37*dn)),
    ("v8_B_0.001e9.5d", lambda dn: 0.001*np.exp(9.5*dn)),
    ("v8_C_0.01e7.0d", lambda dn: 0.01*np.exp(7.0*dn)),
    ("v8_D_0.003e6.0d", lambda dn: 0.003*np.exp(6.0*dn)),
    ("v8_E_0.1e7.0d", lambda dn: 0.1*np.exp(7.0*dn)),
]
for fname, step_fn in variants:
    # 重新计算几何XOR
    step_grad=step_fn(d_norm)
    dr_geo=np.floor(c_dist_log/step_grad).astype(int)
    chess_geo=((rz_geo%2==0)!=(dr_geo%2==0)).astype(float)
    chess_soft=gaussian_filter(chess_geo.astype(float),sigma=0.8)
    s=np.zeros_like(log_d)
    s[~bounded]=shade[~bounded]
    s[bounded]=np.clip(chess_soft[bounded]*weight[bounded],0,1)
    sb=zoom(s,(W/s.shape[0],W/s.shape[1]),order=1)
    cs=cm(sb)[:,:,:3]; im=(cs*255).astype(np.uint8)
    ip=Image.fromarray(im).convert('RGBA'); dr=ImageDraw.Draw(ip)
    dr.text((20,20),fname,fill=(255,255,255,200))
    ip=ip.rotate(90,expand=True,resample=Image.BILINEAR)

    fout=os.path.join(OUT_DIR,fname+".png")
    ip.resize((1500,1500),Image.LANCZOS).save(fout)
    print(f"  -> {fout}")