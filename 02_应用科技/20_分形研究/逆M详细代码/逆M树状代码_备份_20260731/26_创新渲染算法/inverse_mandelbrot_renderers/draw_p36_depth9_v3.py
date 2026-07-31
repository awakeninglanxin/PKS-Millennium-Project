#!/usr/bin/env python3
"""v3: 6种配色对比子图 (共用波场, 不同颜色映射)"""
import numpy as np, math, cmath, os, sys, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
CACHE = os.path.join(OUT_DIR, "_wave_cache.npz")

# ═══ 重用v2的波场计算 (如果缓存存在则跳过) ═══
if os.path.exists(CACHE):
    print("[0] 加载缓存波场...")
    d = np.load(CACHE)
    ws_big = d['ws']  # 蓝波场
    rf_big = d['rf']  # 金涟漪场
    W, H = ws_big.shape
else:
    print("[0] 计算波场...")
    W, H = 2000, 2000
    SCALE = 160
    CX, CY = 0.0, 0.0

    def mset_center(p, q):
        th=2*math.pi*p/q; return 0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)

    # 蓝波场源
    bulbs=[]
    def add_bulb(c_center, period, depth):
        if depth>9: return
        if abs(c_center)<1e-12: return
        c_inv=1.0/c_center; px=CX+c_inv.real*SCALE; py=CY+c_inv.imag*SCALE
        if depth==0: r_m=1.0/(1.5+period*0.5)
        else: r_m=0.15/(1.8**(period-1))*(0.4**depth)
        deriv=1.0/(c_center*c_center); r_inv=r_m*abs(deriv); rr=r_inv*SCALE
        if rr<1: rr=1.0; wlen=8; amp=2; nr=3
        else:
            # 波长按深度分层: 浅层宽间距->深层密集
            if depth<=1:    wlen=rr*8  # 第一层宽间距
            elif depth<=3:  wlen=rr*5  # 中层
            else:           wlen=rr*3  # 深层密集
            amp=rr*3; nr=min(6+period,18)
        bulbs.append((px,py,rr,period,depth,wlen,amp,nr))
        max_s=max(2,7-depth)
        for s in range(2,max_s+1):
            for r in range(1,s):
                if math.gcd(r,s)!=1: continue
                cp=period*s
                if cp>64: continue
                theta=2*math.pi*r/s
                cc=c_center+r_m*cmath.exp(1j*theta)
                add_bulb(cc,cp,depth+1)
    for q in range(2,37):
        for p in range(1,q):
            if math.gcd(p,q)!=1: continue
            add_bulb(mset_center(p,q),q,1)
    for s in range(2,7):
        for r in range(1,s):
            if math.gcd(r,s)!=1: continue
            add_bulb(-1+0.25*cmath.exp(1j*2*math.pi*r/s),2*s,2)
    print(f"  {len(bulbs)}个蓝波源")

    # 蓝波场计算
    xs=np.linspace(-W/2/SCALE,W/2/SCALE,W//2,dtype=np.float64)
    ys=np.linspace(-H/2/SCALE,H/2/SCALE,H//2,dtype=np.float64)
    X,Y=np.meshgrid(xs*SCALE,ys*SCALE); wave_sum=np.zeros((H//2,W//2),dtype=np.float64)
    for idx,(bx,by,br,period,depth,wlen,amp,nr) in enumerate(bulbs):
        dx=X-bx; dy=Y-by; dist=np.sqrt(dx*dx+dy*dy); cutoff=br+nr*wlen*1.5
        mask=dist<=cutoff
        if not mask.any(): continue
        d=dist[mask]
        w=np.sin(2*math.pi*d/wlen)*(amp/(1+d/max(br,1)))
        w*=np.exp(-d/cutoff*2.0)
        wave_sum[mask]+=w
        if (idx+1)%800==0: print(f"  蓝波 {idx+1}/{len(bulbs)}...")
    ws=np.abs(wave_sum); ws=ws/(ws.max()+1e-30); ws=ws**0.35
    ws_big=zoom(ws,(W/ws.shape[0],W/ws.shape[1]),order=1)

    # 金涟漪场源
    upper=[]
    DEPTH=[(1.12,0),(1.30,1),(1.55,2),(1.80,3),(2.10,4)]
    for i in range(91):
        th=math.pi*i/90
        c_att=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)
        for expand,lvl in DEPTH:
            c_out=c_att*expand
            if abs(c_out)<1e-12: continue
            ci=1.0/c_out
            if abs(ci.real)<6 and abs(ci.imag)<5:
                upper.append((ci.real,abs(ci.imag),lvl))
    known=[(1,-1.0,0.0),(2,-1.754878,0.0),(2,-0.122561,0.744862),
           (3,-1.310703,0.0),(3,-0.156520,1.032247),(3,0.282000,0.530000),
           (4,-1.625413,0.0),(4,-0.504340,0.562765),(4,0.379280,0.334020),(4,-1.860783,0.0),
           (5,-1.476000,0.0),(5,0.374400,0.367200),(5,-0.163423,0.577597),(5,-0.044987,1.050261),
           (6,-1.600357,0.0),(6,0.365640,0.291010),(6,-1.738350,0.0),(6,-1.424870,0.0),
           (6,-0.229542,0.561508),(6,0.220328,0.465829),
           (7,-1.566838,0.0),(7,-1.420594,0.0),(7,0.366218,0.250745),
           (7,0.389000,0.216000),(8,-1.520000,0.0),(8,0.373000,0.225000),
           (8,-0.080000,0.692000),(8,-0.325000,0.700000),
           (9,-1.500000,0.0),(9,0.382000,0.201000),(9,-0.138000,0.802000),(9,-0.220000,0.605000)]
    for level,cr,ci in known:
        c=complex(cr,ci)
        if abs(c)<1e-12: continue
        ci2=1.0/c
        if abs(ci2.real)<6 and abs(ci2.imag)<5:
            upper.append((ci2.real,abs(ci2.imag),level))
    red_s=[]
    for cr,ci,level in upper:
        red_s.append((cr,ci,level))
        if abs(ci)>1e-6: red_s.append((cr,-ci,level))
    print(f"  {len(red_s)}个金涟漪源")

    # 金涟漪场
    rf=np.zeros((H//2,W//2),dtype=np.float64)
    for cr,ci,level in red_s:
        bx=CX+cr*SCALE; by=CY+ci*SCALE
        dx=X-bx; dy=Y-by; dist=np.sqrt(dx*dx+dy*dy)
        cutoff=4000/(1.5**level)
        mask=dist<=cutoff
        if not mask.any(): continue
        d=dist[mask]; wlen=max(12,200/(1.5**level)); amp=1.0/(1.45**level)
        rw=np.sin(2*math.pi*d/wlen)*amp/(1+d/(cutoff/3))
        rw*=np.exp(-d/(cutoff*0.5)*1.8)
        rf[mask]+=rw
    rf=np.abs(rf); rf=rf/(rf.max()+1e-30); rf=rf**0.6
    rf_big=zoom(rf,(W/rf.shape[0],W/rf.shape[1]),order=1)

    np.savez(CACHE, ws=ws_big, rf=rf_big)
    print(f"  缓存已保存: {CACHE}")

# ═══ 6种配色方案对比 ═══
print("[1] 生成6种配色对比...")

variants = [
    ("深蓝波", (0.18,0.14,0.08)),     # 深蓝暗纹
    ("水绿波", (0.10,0.20,0.25)),     # 水绿
    ("淡紫波", (0.08,0.18,0.12)),     # 淡紫
    ("暖灰波", (0.15,0.13,0.10)),     # 暖灰
    ("藏青波", (0.22,0.16,0.06)),     # 藏青
    ("暗紫波", (0.20,0.10,0.18)),     # 暗紫
]

# 裁剪到正方形(取中心)
SZ = min(W, H)
base = np.clip(ws_big, 0, 1)
ripple = np.clip(rf_big, 0, 1)
# 金→白渐变
gold_r,gold_g,gold_b = 218,165,32
rr = gold_r+(255-gold_r)*(1-ripple)
gg = gold_g+(255-gold_g)*(1-ripple)
rb = gold_b+(255-gold_b)*(1-ripple)
alpha_g = ripple * 0.6

# 心形路径
SCALE = 160
pts_c = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    ci = 1.0/c
    pts_c.append((int(W/2+ci.real*SCALE*W/2000), int(H/2-ci.imag*SCALE*H/2000)))
pts2 = []
for i in range(801):
    th = 2*math.pi*i/800
    c = math.cos(th)/4+1j*math.sin(th)/4-1; ci=1.0/c
    pts2.append((int(W/2+ci.real*SCALE*W/2000), int(H/2-ci.imag*SCALE*H/2000)))

sub_images = []
for name, (wr, wg, wb) in variants:
    img_arr = np.zeros((H,W,4), dtype=np.uint8)
    for c, wv in enumerate([wr,wg,wb]):
        img_arr[:,:,c] = (255 - base*140*3*wv).astype(np.uint8)
    img_arr[:,:,0] = (img_arr[:,:,0]*(1-alpha_g) + rr*alpha_g).astype(np.uint8)
    img_arr[:,:,1] = (img_arr[:,:,1]*(1-alpha_g) + gg*alpha_g).astype(np.uint8)
    img_arr[:,:,2] = (img_arr[:,:,2]*(1-alpha_g) + rb*alpha_g).astype(np.uint8)
    img_arr[:,:,3] = 255

    img_pil = Image.fromarray(img_arr, 'RGBA')
    draw = ImageDraw.Draw(img_pil)
    draw.line(pts_c, fill=(60,60,100,180), width=4)
    draw.line(pts2, fill=(180,120,40,150), width=3)
    draw.text((10,10), name, fill=(60,60,80,255))
    # 旋转 水滴尖朝上
    img_pil = img_pil.rotate(90, expand=True, resample=Image.BILINEAR, fillcolor=(255,255,255,255))
    sub_images.append((name, img_pil))
    print(f"  {name} ✓")

# 单独保存藏青波大图
nq = sub_images[4][1]  # 藏青波是第5个(index 4)
nq.save(os.path.join(OUT_DIR, "逆M_藏青波_独立.png"))

# ═══ 拼成2×3网格 ═══
print("[2] 拼图...")
TW, TH = 1000, 1000  # 每格大小
grid = Image.new('RGBA', (TW*3, TH*2), (255,255,255,255))
for idx, (name, img) in enumerate(sub_images):
    r, c = idx // 3, idx % 3
    sm = img.resize((TW, TH), Image.LANCZOS)
    grid.paste(sm, (c*TW, r*TH))

out = os.path.join(OUT_DIR, "逆M_配色对比_v3.png")
grid.save(out)
print(f"→ {out}  ({os.path.getsize(out)//1024}KB)")
