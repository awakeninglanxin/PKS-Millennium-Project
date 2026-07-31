#!/usr/bin/env python3
"""v6: 每泡独立同心圆涟漪(不干涉), 用ImageDraw画线"""
import cupy as cp, numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom, label, maximum_filter
from matplotlib.path import Path

OUT_DIR = "/root/invM_v6"
os.makedirs(OUT_DIR, exist_ok=True)
W, H = 3000, 3000
SCALE = 160
CX, CY = 0.0, 0.0
MAX_ITER, BL = 200, 50

# ═══ 1. GPU TIA ═══
print(f"[1] GPU TIA: bailout={BL}, iter={MAX_ITER}...")
t0 = time.time()
R2 = BL**2
xs = cp.linspace(-W/2/SCALE, W/2/SCALE, W//2, dtype=cp.float64)
ys = cp.linspace(-H/2/SCALE, H/2/SCALE, H//2, dtype=cp.float64)
X, Y = cp.meshgrid(xs, ys); C = X + 1j*Y
rC = cp.abs(C); rC = cp.maximum(rC, 1e-13); thC = cp.angle(C)
ce = (rC**(-1.0)) * cp.exp(1j*(-1.0)*thC)
zr = cp.zeros_like(ce); zi = cp.zeros_like(ce)
alive = cp.ones(ce.shape, dtype=bool)
tia_sum = cp.zeros(ce.shape, dtype=cp.float64)
tia_cnt = cp.zeros(ce.shape, dtype=cp.int32)
for n in range(MAX_ITER):
    if not cp.any(alive): break
    za = zr[alive]+1j*zi[alive]; ca = ce[alive]; zn = za*za+ca
    rn = cp.abs(zn-za)/(cp.abs(zn)+1e-30)
    tia_sum[alive] += rn; tia_cnt[alive] += 1
    zr[alive]=cp.real(zn); zi[alive]=cp.imag(zn)
    m2=cp.real(zn)**2+cp.imag(zn)**2; esc=m2>R2
    alive[alive]=~esc
ext_mask_cpu=cp.asnumpy(alive); tia_sum_cpu=cp.asnumpy(tia_sum); tia_cnt_cpu=cp.asnumpy(tia_cnt)
del C,ce,zr,zi,X,Y,tia_sum,tia_cnt,alive; cp.get_default_memory_pool().free_all_blocks()
print(f"  GPU: {time.time()-t0:.1f}s")

# ═══ 2. TIA中心检测 ═══
print("[2] 中心检测...")
tia = np.where(tia_cnt_cpu>0, tia_sum_cpu/np.maximum(tia_cnt_cpu,1), 0.0)
tia_full = zoom(tia, (W//tia.shape[0], W//tia.shape[1]), order=1)
ext_full = zoom(ext_mask_cpu.astype(np.float64), (W//ext_mask_cpu.shape[0], W//ext_mask_cpu.shape[1]), order=0)>0.5
XS,YS=np.meshgrid(np.linspace(-W/2/SCALE,W/2/SCALE,W),np.linspace(-H/2/SCALE,H/2/SCALE,H))
in_box=(XS>-1.5)&(XS<4.2)&(np.abs(YS)<1.8); search_mask=ext_full&in_box

nhood_m5=maximum_filter(tia_full,size=5); nhood_m3=maximum_filter(tia_full,size=3)
local_max=(((tia_full>=nhood_m5*0.999)|(tia_full>=nhood_m3*0.999))&search_mask)
labeled,n=label(local_max)
centers_raw=[]
for i in range(1,n+1):
    yx,xx=np.where(labeled==i)
    if len(yx)>=1:
        cx2,cy2=xx.mean(),yx.mean()
        centers_raw.append((cx2,cy2,tia_full[int(cy2),int(cx2)]))

dp=[]; 
for i in range(2001):
    th=2*math.pi*i/2000
    c2=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv=1.0/c2
    dp.append((W/2+cv.real*SCALE,H/2-cv.imag*SCALE))
droplet_path=Path(dp)
ci=[c for c in centers_raw if droplet_path.contains_point((c[0],c[1]))]
print(f"  水滴内:{len(ci)}个")

cs=sorted(ci,key=lambda x:x[2],reverse=True)[:360]
centers=[]
for rank,(cx,cy,tval) in enumerate(cs):
    r_scale=1200*(0.993**rank)
    centers.append((cx,cy,tval,r_scale))
print(f"  保留{len(centers)}个 半径{centers[0][3]:.0f}→{centers[-1][3]:.0f}px")

# ═══ 3. 每泡独立同心圆绘制(无干涉) ═══
print("[3] 独立同心圆涟漪...")
t0=time.time()
img=np.zeros((W,H,4),dtype=np.uint8); img[:,:,:3]=255; img[:,:,3]=255
ip=Image.fromarray(img,'RGBA'); dr=ImageDraw.Draw(ip)

for idx,(cx,cy,tval,r_scale) in enumerate(centers):
    if cx<0 or cx>W or cy<0 or cy>H: continue
    # 颜色: 金色, 透明度随距离衰减
    n_ripples = max(3, int(15/(1+(360-idx)/360*5)))
    wavelength = r_scale / n_ripples
    for ri in range(1, n_ripples+1):
        r = ri * wavelength
        if r<3: continue
        # 透明度衰减: 越远越淡, 越靠后越淡
        alpha = max(10, int(200*math.exp(-ri*0.15)))
        col = (218, 165, 32, alpha)
        dr.ellipse([cx-r,cy-r,cx+r,cy+r], outline=col, width=1)
    if (idx+1)%60==0: print(f"  泡 {idx+1}/{len(centers)}...")

# 轮廓
pts_c=[]; pts2=[]
for i in range(2001):
    th=2*math.pi*i/2000
    c2=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv=1.0/c2
    pts_c.append((int(W/2+cv.real*SCALE),int(H/2-cv.imag*SCALE)))
for i in range(801):
    th=2*math.pi*i/800
    c2=math.cos(th)/4+1j*math.sin(th)/4-1; cv=1.0/c2
    pts2.append((int(W/2+cv.real*SCALE),int(H/2-cv.imag*SCALE)))
dr.line(pts_c,fill=(120,40,150,220),width=5)
dr.line(pts2,fill=(180,120,40,200),width=4)
for cx,cy,tval,r_scale in centers:
    px,py=int(cx),int(cy)
    if 0<=px<W and 0<=py<H: dr.ellipse([px-2,py-2,px+2,py+2],fill=(255,80,80,220))
dr.text((10,10),f"v6 独立同心圆 {len(centers)}泡 无干涉",fill=(40,40,60,200))

ip=ip.rotate(90,expand=True,resample=Image.BILINEAR,fillcolor=(255,255,255,255))
out=os.path.join(OUT_DIR,"invM_v6_independent.png")
ip.save(out)
print(f"→ {out}  ({time.time()-t0:.0f}s)")
