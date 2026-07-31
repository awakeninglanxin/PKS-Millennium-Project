#!/usr/bin/env python3
"""路线B GPU修正: UF11参数(bailout=50, max_iter=200) + correct ext mask"""
import cupy as cp, numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom, label, maximum_filter

OUT_DIR = "/root/invM_v4"
W, H = 6000, 6000  # 2×像素 (GPU友好)
SCALE = 400         # 同比
CX, CY = 0.0, 0.0
MAX_ITER = 200  # UF11 参数
BL = 50          # UF11 bailout (不是1024!)

# ═══ 1. GPU TIA + ext/int mask 计算 (UF11标准参数) ═══
print(f"[1] GPU TIA: bailout={BL}, iter={MAX_ITER}...")
t0 = time.time()

R2 = BL**2  # 2500
xs = cp.linspace(-W/2/SCALE, W/2/SCALE, W//2, dtype=cp.float64)
ys = cp.linspace(-H/2/SCALE, H/2/SCALE, H//2, dtype=cp.float64)
X, Y = cp.meshgrid(xs, ys)
C = X + 1j * Y

rC = cp.abs(C); rC = cp.maximum(rC, 1e-13)
thC = cp.angle(C)
ce = (rC ** (-1.0)) * cp.exp(1j * (-1.0) * thC)

zr = cp.zeros_like(ce); zi = cp.zeros_like(ce)
alive = cp.ones(ce.shape, dtype=bool)
tia_sum = cp.zeros(ce.shape, dtype=cp.float64)
tia_cnt = cp.zeros(ce.shape, dtype=cp.int32)

for n in range(MAX_ITER):
    if not cp.any(alive): break
    za = zr[alive] + 1j * zi[alive]
    ca = ce[alive]
    zn = za * za + ca
    rn = cp.abs(zn - za) / (cp.abs(zn) + 1e-30)
    tia_sum[alive] += rn
    tia_cnt[alive] += 1
    zr[alive] = cp.real(zn); zi[alive] = cp.imag(zn)
    m2 = cp.real(zn)**2 + cp.imag(zn)**2
    esc = m2 > R2
    alive[alive] = ~esc

# UF11: ext = alive (有界区 = 水滴外部), interior = ~alive (逃逸区 = 水滴内部)
ext_mask_cpu = cp.asnumpy(alive)
tia_sum_cpu = cp.asnumpy(tia_sum)
tia_cnt_cpu = cp.asnumpy(tia_cnt)
del C, ce, zr, zi, X, Y, tia_sum, tia_cnt, alive
cp.get_default_memory_pool().free_all_blocks()
print(f"  GPU: {time.time()-t0:.1f}s, ext={ext_mask_cpu.sum()}")

# ═══ 2. TIA + 气泡中心检测 (在ext区域 = 水滴外部) ═══
print("[2] TIA极小值检测(ext=水滴外部)...")
t0 = time.time()
tia = np.where(tia_cnt_cpu > 0, tia_sum_cpu / np.maximum(tia_cnt_cpu, 1), 0.0)
tia_full = zoom(tia, (W/tia.shape[0], W/tia.shape[1]), order=1)
ext_full = zoom(ext_mask_cpu.astype(np.float64), (W/ext_mask_cpu.shape[0], W/ext_mask_cpu.shape[1]), order=0) > 0.5

# 水滴边界框裁剪ext区
XS, YS = np.meshgrid(np.linspace(-W/2/SCALE, W/2/SCALE, W), np.linspace(-H/2/SCALE, H/2/SCALE, H))
in_box = (XS > -1.5) & (XS < 4.2) & (np.abs(YS) < 1.8)
search_mask = ext_full & in_box
print(f"  搜索区: {search_mask.sum()} 像素")

# 统一极大值: 超吸引中心→z=0→TIA爆炸
nhood_m5 = maximum_filter(tia_full, size=5)
nhood_m3 = maximum_filter(tia_full, size=3)
local_max = (((tia_full >= nhood_m5*0.999) | (tia_full >= nhood_m3*0.999)) & search_mask)
labeled, n = label(local_max)
centers_raw = []
for i in range(1, n+1):
    yx, xx = np.where(labeled == i)
    if len(yx)>=1:
        cx2,cy2=xx.mean(),yx.mean()
        tval=tia_full[int(cy2),int(cx2)]
        centers_raw.append((cx2,cy2,tval))
print(f"  检测到 {len(centers_raw)} 个超吸引中心")

# 水滴多边形
from matplotlib.path import Path
dp=[]
for i in range(2001):
    th=2*math.pi*i/2000
    c2=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv=1.0/c2
    dp.append((W/2+cv.real*SCALE, H/2-cv.imag*SCALE))
droplet_path=Path(dp)

centers_in=[c for c in centers_raw if droplet_path.contains_point((c[0],c[1]))]
centers_out=[c for c in centers_raw if not droplet_path.contains_point((c[0],c[1]))]
print(f"  水滴内:{len(centers_in)} 水滴外:{len(centers_out)}")

# 按TIA降序取前360, 半径自然按TIA值缩放
centers_sorted=sorted(centers_in,key=lambda x:x[2],reverse=True)[:360]
centers=[]
for rank,(cx,cy,tval) in enumerate(centers_sorted):
    r_scale=1200*(0.993**rank)  # 第1:~1192px, 第360:~95px
    centers.append((cx,cy,tval,r_scale))
print(f"  保留{len(centers)}个 半径{centers[0][3]:.0f}→{centers[-1][3]:.0f}px")

# ═══ 3. …
print("[3] 棋盘调制...")
all_centers=[]
for cx,cy,tval,r_scale in centers:
    period=2+int(20*(1-r_scale/1200))
    all_centers.append((cx,cy,period,r_scale))

print(f"  共{len(all_centers)}个棋盘锚点(全部TIA检测)")

# ═══ 4. 金涟漪 + 棋盘涟漪(叠加干涉) ═══
print("[4] 双波场叠加干涉...")
RH2, RW2 = H//5, W//5
XX3, YY3 = np.meshgrid(np.linspace(-W/2,W/2,RW2), np.linspace(-H/2,H/2,RH2))

# 金涟漪波场
upper=[]
for i in range(91):
    th=math.pi*i/90; ca=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)
    for expand,lvl in [(1.12,0),(1.30,1),(1.55,2),(1.80,3),(2.10,4)]:
        co=ca*expand
        if abs(co)<1e-12: continue
        cv=1.0/co
        if abs(cv.real)<6 and abs(cv.imag)<5: upper.append((cv.real,abs(cv.imag),lvl))
gs=[]
for cr,ci,level in upper:
    gs.append((cr,ci,level))
    if abs(ci)>1e-6: gs.append((cr,-ci,level))

rf_g=np.zeros((RH2,RW2),dtype=np.float64)
for cr,ci,level in gs:
    bx=CX+cr*SCALE; by=CY+ci*SCALE
    dx=XX3-bx; dy=YY3-by; dist=np.sqrt(dx*dx+dy*dy)
    cutoff = (2500*W//3000) / (1.5**level); mask=dist<=cutoff
    if not mask.any(): continue
    d=dist[mask]; wlen=max(3,15/(1.5**level)); amp=1.0/(1.45**level)
    rw=np.sin(2*math.pi*d/wlen)*amp/(1+d/(cutoff/3))
    rw*=np.exp(-d/(cutoff*0.5)*1.8); rf_g[mask]+=rw

# ★ 棋盘涟漪 (独立归一化, 大幅提升可见度)
rf_c = np.zeros((RH2, RW2), dtype=np.float64)
NR=16
for cx,cy,period,r_scale in all_centers:
    bx=cx-W/2; by=cy-H/2
    bx_s=bx*(RW2/W); by_s=by*(RH2/H)
    dx=XX3-bx_s; dy=YY3-by_s; dist=np.sqrt(dx*dx+dy*dy)
    cutoff=r_scale*(RW2/W); wlen=max(15,cutoff/4); amp=1.2
    mask=dist<=cutoff
    if not mask.any(): continue
    d=dist[mask]
    wave = np.sin(2*math.pi*d/wlen) * amp/(1+d/(cutoff/3))
    wave *= np.exp(-d/(cutoff*0.5)*1.8)
    ang=np.arctan2(dy[mask],dx[mask])
    rz=np.floor((ang+math.pi)/(2*math.pi)*NR).astype(int)%NR
    wave *= np.where(rz%2==0, 1.0, 0.6)
    rf_c[mask] += wave

# 独立归一化棋盘场(不受金涟漪主导)
rf_c_norm = np.abs(rf_c)
rf_c_norm = rf_c_norm / (rf_c_norm.max()+1e-30)
rf_c_norm = rf_c_norm ** 0.6

# 独立归一化金涟漪
rf_g_norm = np.abs(rf_g)
rf_g_norm = rf_g_norm / (rf_g_norm.max()+1e-30)
rf_g_norm = rf_g_norm ** 0.6

# 叠加: 金涟漪70% + 棋盘涟漪30% (可观干涉)
rf = rf_g_norm * 0.7 + rf_c_norm * 0.3
rf_big = zoom(rf, (W/RH2, W/RW2), order=1)

# ═══ 5. 素描等高线 ═══
print("[5] 素描等高线...")

rf_c_norm=np.abs(rf_c); rf_c_norm=rf_c_norm/(rf_c_norm.max()+1e-30); rf_c_norm=rf_c_norm**0.6
rf_g_norm=np.abs(rf_g); rf_g_norm=rf_g_norm/(rf_g_norm.max()+1e-30); rf_g_norm=rf_g_norm**0.6
rf_B=rf_g_norm*0.5+rf_c_norm*0.5

rf_big=zoom(rf_B,(W/RH2,W/RW2),order=1)
# 波峰(正)深黑, 波谷(负)浅灰
peak=rf_big>0.01; valley=rf_big<-0.01  # 窄阈值→1px细线
img=np.zeros((W,H,4),dtype=np.uint8)
img[:,:,:3]=255; img[:,:,3]=255
img[np.where(peak)]= [20,20,30,255]
img[np.where(valley)]=[150,150,160,255]

pts_c=[]; pts2=[]
for i in range(2001):
    th=2*math.pi*i/2000; c2=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cv=1.0/c2
    pts_c.append((int(W/2+cv.real*SCALE),int(H/2-cv.imag*SCALE)))
for i in range(801):
    th=2*math.pi*i/800; c2=math.cos(th)/4+1j*math.sin(th)/4-1; cv=1.0/c2
    pts2.append((int(W/2+cv.real*SCALE),int(H/2-cv.imag*SCALE)))

ip=Image.fromarray(img,'RGBA'); dr=ImageDraw.Draw(ip)
dr.line(pts_c,fill=(120,40,150,220),width=5)
dr.line(pts2,fill=(180,120,40,200),width=4)
for cx,cy,p,r_s in all_centers:
    px,py=int(cx),int(cy)
    if 0<=px<W and 0<=py<H: dr.ellipse([px-2,py-2,px+2,py+2],fill=(255,80,80,220))
dr.text((10,10),"素描等高线 360泡 黑=波峰 灰=波谷",fill=(40,40,60,200))
ip=ip.rotate(90,expand=True,resample=Image.BILINEAR,fillcolor=(255,255,255,255))
OUT_DIR="/root/invM_v4"; os.makedirs(OUT_DIR,exist_ok=True)
out=os.path.join(OUT_DIR,"invM_RouteB_corrected.png")
ip.save(out); print(f"-> {out}")