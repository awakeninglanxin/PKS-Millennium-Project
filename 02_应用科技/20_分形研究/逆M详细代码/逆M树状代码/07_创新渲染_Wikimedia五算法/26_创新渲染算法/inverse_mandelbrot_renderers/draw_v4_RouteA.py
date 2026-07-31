#!/usr/bin/env python3
"""v4: 路线A — 取模势能棋盘 × 金涟漪调制 (archive_v3)"""
import numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
CACHE = os.path.join(OUT_DIR, "_wave_cache_v4.npz")

# ═══ 波场计算 (同v3) ═══
if os.path.exists(CACHE):
    print("[0] 加载缓存...")
    d = np.load(CACHE); ws_big = d['ws']; rf_big = d['rf']; pot_big = d['pot']
    W, H = ws_big.shape
else:
    W, H = 2000, 2000; SCALE = 160; CX, CY = 0.0, 0.0
    def mset_center(p,q): th=2*math.pi*p/q; return 0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)

    # 蓝波场源
    bulbs=[]; MAX_ITER=400
    def add_bulb(cc,period,depth):
        if depth>9: return
        if abs(cc)<1e-12: return
        ci=1.0/cc; px=CX+ci.real*SCALE; py=CY+ci.imag*SCALE
        if depth==0: rm=1.0/(1.5+period*0.5)
        else: rm=0.15/(1.8**(period-1))*(0.4**depth)
        deriv=1.0/(cc*cc); ri=rm*abs(deriv); rr=ri*SCALE
        if rr<1: rr=1.0; wlen=8; amp=2; nr=3
        else:
            if depth<=1: wlen=rr*8
            elif depth<=3: wlen=rr*5
            else: wlen=rr*3
            amp=rr*3; nr=min(6+period,18)
        bulbs.append((px,py,rr,period,depth,wlen,amp,nr))
        ms=max(2,7-depth)
        for s in range(2,ms+1):
            for r in range(1,s):
                if math.gcd(r,s)!=1: continue
                cp=period*s
                if cp>64: continue
                th=2*math.pi*r/s; ccc=cc+rm*cmath.exp(1j*th)
                add_bulb(ccc,cp,depth+1)
    for q in range(2,37):
        for p in range(1,q):
            if math.gcd(p,q)!=1: continue
            add_bulb(mset_center(p,q),q,1)
    for s in range(2,7):
        for r in range(1,s):
            if math.gcd(r,s)!=1: continue
            add_bulb(-1+0.25*cmath.exp(1j*2*math.pi*r/s),2*s,2)
    print(f"  {len(bulbs)}个蓝波源")

    # 网格
    RW,RH=W//2,H//2
    xs=np.linspace(-W/2/SCALE,W/2/SCALE,RW,dtype=np.float64)
    ys=np.linspace(-H/2/SCALE,H/2/SCALE,RH,dtype=np.float64)
    X,Y=np.meshgrid(xs*SCALE,ys*SCALE)

    # 蓝波场
    print("  蓝波场...")
    wave_sum=np.zeros((RH,RW),dtype=np.float64)
    for idx,(bx,by,br,p,d,wlen,amp,nr) in enumerate(bulbs):
        dx=X-bx; dy=Y-by; dist=np.sqrt(dx*dx+dy*dy)
        cutoff=br+nr*wlen*1.5; mask=dist<=cutoff
        if not mask.any(): continue
        d2=dist[mask]
        w=np.sin(2*math.pi*d2/wlen)*(amp/(1+d2/max(br,1)))
        w*=np.exp(-d2/cutoff*2.0); wave_sum[mask]+=w
        if (idx+1)%800==0: print(f"    蓝波 {idx+1}/{len(bulbs)}...")
    ws=np.abs(wave_sum); ws=ws/(ws.max()+1e-30); ws=ws**0.35
    ws_big=zoom(ws,(W/RH,W/RW),order=1)

    # ── ★ 势能pot场 (新) ──
    print("  势能pot场...")
    # 在网格上跑标准M集迭代, 得到|z|和pot
    c_eff=X/SCALE+1j*Y/SCALE  # 像素坐标对应的复平面点
    rC=np.abs(c_eff); rC=np.maximum(rC,1e-13)
    thC=np.angle(c_eff)
    rp=np.power(rC,-1.0); aa=-thC
    cr=rp*np.cos(aa); ci=rp*np.sin(aa)
    zr=np.zeros_like(cr); zi=np.zeros_like(ci)
    alive=np.ones(c_eff.shape,dtype=bool)
    esc_iter=np.full(c_eff.shape,400,dtype=np.int32)
    pot=np.zeros(c_eff.shape,dtype=np.float64)
    for n in range(400):
        if not alive.any(): break
        nzr=zr[alive]**2-zi[alive]**2+cr[alive]
        nzi=2*zr[alive]*zi[alive]+ci[alive]
        zr[alive]=nzr; zi[alive]=nzi
        m2=nzr*nzr+nzi*nzi
        esc=m2>1024
        esc_iter[alive]=np.where(esc,n,esc_iter[alive])
        alive[alive]=~esc
    # 计算pot (仅逃逸区, 即水滴内部)
    ext_mask=esc_iter<400
    m2_final=zr*zr+zi*zi
    pot[ext_mask]=399-np.log2(np.maximum(np.log2(np.maximum(m2_final[ext_mask],1e-30))/2,1e-12))
    pot[~ext_mask]=0
    pot=np.clip(pot,0,None)
    pot_big=zoom(pot,(W/RH,W/RW),order=1)
    print(f"    pot范围: [{pot[ext_mask].min():.1f},{pot[ext_mask].max():.1f}]")

    # 金涟漪场
    print("  金涟漪场...")
    upper=[]
    DEPTH=[(1.12,0),(1.30,1),(1.55,2),(1.80,3),(2.10,4)]
    for i in range(91):
        th=math.pi*i/90
        ca=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)
        for expand,lvl in DEPTH:
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
    for level,cr2,ci2 in known:
        c=complex(cr2,ci2)
        if abs(c)<1e-12: continue
        cii2=1.0/c
        if abs(cii2.real)<6 and abs(cii2.imag)<5:
            upper.append((cii2.real,abs(cii2.imag),level))
    red_s=[]
    for cr3,ci3,level in upper:
        red_s.append((cr3,ci3,level))
        if abs(ci3)>1e-6: red_s.append((cr3,-ci3,level))
    print(f"    {len(red_s)}个金涟漪源")
    rf=np.zeros((RH,RW),dtype=np.float64)
    for cr3,ci3,level in red_s:
        bx=CX+cr3*SCALE; by=CY+ci3*SCALE
        dx=X-bx; dy=Y-by; dist=np.sqrt(dx*dx+dy*dy)
        cutoff=4000/(1.5**level); mask=dist<=cutoff
        if not mask.any(): continue
        d3=dist[mask]; wlen=max(12,200/(1.5**level)); amp=1.0/(1.45**level)
        rw=np.sin(2*math.pi*d3/wlen)*amp/(1+d3/(cutoff/3))
        rw*=np.exp(-d3/(cutoff*0.5)*1.8); rf[mask]+=rw
    rf=np.abs(rf); rf=rf/(rf.max()+1e-30); rf=rf**0.6
    rf_big=zoom(rf,(W/RH,W/RW),order=1)
    np.savez(CACHE, ws=ws_big, rf=rf_big, pot=pot_big)

# ═══ 路线A: 取模势能棋盘调制 ═══
print("[1] 取模势能棋盘调制...")
base=np.clip(ws_big,0,1)
pot_raw=np.clip(pot_big,0,None)
# pot集中[395.7,396.7] → 需要先归一化再拉宽
pmn,pmx=395.7,396.7  # 逆M水滴内部pot几乎恒定于396附近
RING_COUNT=24  # 水滴内部棋盘环数
print(f"  pot范围归一化: [{pmn:.1f},{pmx:.1f}] → 拉宽至0~{RING_COUNT}")
pot_norm=np.clip((pot_raw-pmn)/(pmx-pmn+1e-12)*RING_COUNT,0,None)
# ★ 核心公式: P = floor((pot_norm % 1.0) / 0.5) ★
P=(pot_norm%1.0)//0.5
modulation=np.where(P==1,0.35,1.0)

# 金涟漪调制
ripple=np.clip(rf_big,0,1)
ripple_mod = ripple * modulation  # ★ 棋盘×涟漪

# 藏青色底图
img_arr=np.zeros((H,W,4),dtype=np.uint8)
for c,wv in enumerate([0.22,0.16,0.06]):
    img_arr[:,:,c]=(255-base*140*3*wv).astype(np.uint8)

# 金涟漪(调制后)
gold_r,gold_g,gold_b=218,165,32
rr=gold_r+(255-gold_r)*(1-ripple_mod)
gg=gold_g+(255-gold_g)*(1-ripple_mod)
rb=gold_b+(255-gold_b)*(1-ripple_mod)
alpha=ripple_mod*0.6
img_arr[:,:,0]=(img_arr[:,:,0]*(1-alpha)+rr*alpha).astype(np.uint8)
img_arr[:,:,1]=(img_arr[:,:,1]*(1-alpha)+gg*alpha).astype(np.uint8)
img_arr[:,:,2]=(img_arr[:,:,2]*(1-alpha)+rb*alpha).astype(np.uint8)
img_arr[:,:,3]=255

# 轮廓
SCALE=160
pts_c=[]; pts2=[]
for i in range(2001):
    th=2*math.pi*i/2000
    c=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); ci=1.0/c
    pts_c.append((int(W/2+ci.real*SCALE*W/2000),int(H/2-ci.imag*SCALE*H/2000)))
for i in range(801):
    th=2*math.pi*i/800
    c=math.cos(th)/4+1j*math.sin(th)/4-1; ci=1.0/c
    pts2.append((int(W/2+ci.real*SCALE*W/2000),int(H/2-ci.imag*SCALE*H/2000)))

img_pil=Image.fromarray(img_arr,'RGBA')
draw=ImageDraw.Draw(img_pil)
draw.line(pts_c,fill=(60,60,100,180),width=4)
draw.line(pts2,fill=(180,120,40,150),width=3)
draw.text((10,10),"v4: 取模势能棋盘×金涟漪 RouteA",fill=(60,60,80,200))
img_pil=img_pil.rotate(90,expand=True,resample=Image.BILINEAR,fillcolor=(255,255,255,255))

out=os.path.join(OUT_DIR,"逆M_v4_RouteA.png")
img_pil.save(out)
print(f"→ {out}  ({os.path.getsize(out)//1024}KB)")

# 6配色对比
variants=[("深蓝",(0.18,0.14,0.08)),("水绿",(0.10,0.20,0.25)),
           ("淡紫",(0.08,0.18,0.12)),("暖灰",(0.15,0.13,0.10)),
           ("藏青",(0.22,0.16,0.06)),("暗紫",(0.20,0.10,0.18))]
subs=[]
for nm,wv in variants:
    ia=np.zeros((H,W,4),dtype=np.uint8)
    for c,wvv in enumerate(wv): ia[:,:,c]=(255-base*140*3*wvv).astype(np.uint8)
    goto_r=gold_r+(255-gold_r)*(1-ripple_mod)
    goto_g=gold_g+(255-gold_g)*(1-ripple_mod)
    goto_b=gold_b+(255-gold_b)*(1-ripple_mod)
    alp=ripple_mod*0.6
    ia[:,:,0]=(ia[:,:,0]*(1-alp)+goto_r*alp).astype(np.uint8)
    ia[:,:,1]=(ia[:,:,1]*(1-alp)+goto_g*alp).astype(np.uint8)
    ia[:,:,2]=(ia[:,:,2]*(1-alp)+goto_b*alp).astype(np.uint8)
    ia[:,:,3]=255
    ip=Image.fromarray(ia,'RGBA'); dr=ImageDraw.Draw(ip)
    dr.line(pts_c,fill=(60,60,100,180),width=4)
    dr.line(pts2,fill=(180,120,40,150),width=3)
    dr.text((10,10),nm,fill=(60,60,80,255))
    ip=ip.rotate(90,expand=True,resample=Image.BILINEAR,fillcolor=(255,255,255,255))
    subs.append(ip.resize((900,900),Image.LANCZOS))

grid=Image.new('RGBA',(2700,1800),(255,255,255,255))
for i,sm in enumerate(subs): grid.paste(sm,(i%3*900,i//3*900))
out2=os.path.join(OUT_DIR,"逆M_v4_6配色对比.png")
grid.save(out2)
print(f"→ {out2}  ({os.path.getsize(out2)//1024}KB)")
