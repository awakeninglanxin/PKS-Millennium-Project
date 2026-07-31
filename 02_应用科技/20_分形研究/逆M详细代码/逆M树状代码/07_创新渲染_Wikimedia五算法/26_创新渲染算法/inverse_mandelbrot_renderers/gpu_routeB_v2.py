#!/usr/bin/env python3
"""路线B GPU简化: 已知32泡中心 × 每泡独立棋盘 × 金涟漪 (RTX 4090)"""
import numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom

OUT_DIR = "/root/invM_v4"
W, H = 3200, 3200
SCALE = 260
CX, CY = 0.0, 0.0
RING_BY_PER = 8  # 每泡基础环数

# ═══ 1. 金涟漪场 (同v3) ═══
print("[1] 金涟漪场...")
t0 = time.time()
RH, RW = H//4, W//4  # 800×800
XX, YY = np.meshgrid(np.linspace(-W/2, W/2, RW), np.linspace(-H/2, H/2, RH))

# 涟漪源
upper=[]
for i in range(91):
    th=math.pi*i/90
    ca=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)
    for expand,lvl in [(1.12,0),(1.30,1),(1.55,2),(1.80,3),(2.10,4)]:
        co=ca*expand
        if abs(co)<1e-12: continue
        cii=1.0/co
        if abs(cii.real)<6 and abs(cii.imag)<5:
            upper.append((cii.real,abs(cii.imag),lvl))
known=[(1,-1.0,0),(2,-1.754878,0),(2,-0.122561,0.744862),
       (3,-1.310703,0),(3,-0.156520,1.032247),(3,0.282000,0.530000),
       (4,-1.625413,0),(4,-0.504340,0.562765),(4,0.379280,0.334020),(4,-1.860783,0),
       (5,-1.476000,0),(5,0.374400,0.367200),(5,-0.163423,0.577597),(5,-0.044987,1.050261),
       (6,-1.600357,0),(6,0.365640,0.291010),(6,-1.738350,0),(6,-1.424870,0),
       (6,-0.229542,0.561508),(6,0.220328,0.465829),
       (7,-1.566838,0),(7,-1.420594,0),(7,0.366218,0.250745),
       (7,0.389000,0.216000),(8,-1.520000,0),(8,0.373000,0.225000),
       (8,-0.080000,0.692000),(8,-0.325000,0.700000),
       (9,-1.500000,0),(9,0.382000,0.201000),(9,-0.138000,0.802000),(9,-0.220000,0.605000)]
for level,cr,ci in known:
    c=complex(cr,ci)
    if abs(c)<1e-12: continue
    cii=1.0/c
    if abs(cii.real)<6 and abs(cii.imag)<5:
        upper.append((cii.real,abs(cii.imag),level))
red_s=[]
for cr,ci,level in upper:
    red_s.append((cr,ci,level))
    if abs(ci)>1e-6: red_s.append((cr,-ci,level))
print(f"  {len(red_s)}个涟漪源")

rf=np.zeros((RH,RW),dtype=np.float64)
for cr,ci,level in red_s:
    bx=CX+cr*SCALE; by=CY+ci*SCALE
    dx=XX-bx; dy=YY-by; dist=np.sqrt(dx*dx+dy*dy)
    cutoff=3000/(1.5**level); mask=dist<=cutoff
    if not mask.any(): continue
    d=dist[mask]; wlen=max(12,200/(1.5**level)); amp=1.0/(1.45**level)
    rw=np.sin(2*math.pi*d/wlen)*amp/(1+d/(cutoff/3))
    rw*=np.exp(-d/(cutoff*0.5)*1.8); rf[mask]+=rw
rf=np.abs(rf); rf=rf/(rf.max()+1e-30); rf=rf**0.6
rf_big=zoom(rf,(W/RH,W/RW),order=1)
print(f"  金涟漪: {time.time()-t0:.1f}s")

# ═══ 2. 每泡独立棋盘调制 ═══
print("[2] 每泡独立棋盘(路线B核心)...")
t0=time.time()

# 32泡中心逆M位置
centers=[]
for level,cr,ci in known:
    c=complex(cr,ci)
    if abs(c)<1e-12: continue
    cii=1.0/c
    px=CX+cii.real*SCALE; py=CY+cii.imag*SCALE
    if abs(cii)<5:
        centers.append((px,py,level))
for px,py,level in list(centers):
    if abs(py)>1: centers.append((px,-py,level))
print(f"  共{len(centers)}个泡中心锚点")

# 每泡本地棋盘
modulation=np.ones((W,H),dtype=np.float64)
XX2,YY2=np.meshgrid(np.arange(W),np.arange(H))

for idx,(cx,cy,period) in enumerate(centers):
    if abs(cx)<0 or abs(cx)>W or abs(cy)<0 or abs(cy)>H: continue
    dx=XX2-cx; dy=YY2-cy
    dist=np.sqrt(dx*dx+dy*dy)
    # 截止半径随周期递减 (高周期泡半径小)
    max_radius=120/(1+period*0.5)  # P1:80px, P3:48px, P5:34px, P9:22px
    n_rings=int(max(RING_BY_PER/(1+period*0.3),2))  # 最少2环
    wlen=max_radius/n_rings
    mask=dist<=max_radius
    if not mask.any(): continue
    d=dist[mask]
    p_local=(d/wlen)%1.0
    binary=np.floor(p_local/0.5).astype(int)
    modulation[mask]=np.where(binary==1,
        np.minimum(modulation[mask],0.25),  # 暗格: 25%强度
        modulation[mask])                     # 亮格: 保持
    if (idx+1)%15==0: print(f"  泡 {idx+1}/{len(centers)}...")
print(f"  棋盘调制: {time.time()-t0:.1f}s")

# ═══ 3. 双场混合渲染 ═══
print("[3] 渲染...")
ripple=np.clip(rf_big,0,1)*modulation
gold_r,gold_g,gold_b=218,165,32
rr2=gold_r+(255-gold_r)*(1-ripple)
gg2=gold_g+(255-gold_g)*(1-ripple)
rb2=gold_b+(255-gold_b)*(1-ripple)
alpha_g=ripple*0.6

img=np.zeros((W,H,4),dtype=np.uint8)
for c in range(3): img[:,:,c]=255
img[:,:,0]=(img[:,:,0]*(1-alpha_g)+rr2*alpha_g).astype(np.uint8)
img[:,:,1]=(img[:,:,1]*(1-alpha_g)+gg2*alpha_g).astype(np.uint8)
img[:,:,2]=(img[:,:,2]*(1-alpha_g)+rb2*alpha_g).astype(np.uint8)
img[:,:,3]=255

# 轮廓
pts_c=[]; pts2=[]
SC=SCALE*W/W
for i in range(2001):
    th=2*math.pi*i/2000
    c2=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cvi=1.0/c2
    pts_c.append((int(W/2+cvi.real*SC),int(H/2-cvi.imag*SC)))
for i in range(801):
    th=2*math.pi*i/800
    c2=math.cos(th)/4+1j*math.sin(th)/4-1; cvi=1.0/c2
    pts2.append((int(W/2+cvi.real*SC),int(H/2-cvi.imag*SC)))

img_pil=Image.fromarray(img,'RGBA')
draw=ImageDraw.Draw(img_pil)
draw.line(pts_c,fill=(60,60,100,180),width=5)
draw.line(pts2,fill=(180,120,40,150),width=4)

# 泡中心红点标记
for cx,cy,period in centers:
    px,py=int(cx),int(cy)
    if 0<=px<W and 0<=py<H:
        draw.ellipse([px-3,py-3,px+3,py+3],fill=(255,80,80,200))

draw.text((10,10),f"路线B: {len(centers)}泡×独立棋盘 × 金涟漪 (GPU综合)",fill=(60,60,80,200))
img_pil=img_pil.rotate(90,expand=True,resample=Image.BILINEAR,fillcolor=(255,255,255,255))

out=os.path.join(OUT_DIR,"invM_RouteB_棋盘金涟漪.png")
img_pil.save(out)
print(f"→ {out}  ({os.path.getsize(out)//1024}KB)")
