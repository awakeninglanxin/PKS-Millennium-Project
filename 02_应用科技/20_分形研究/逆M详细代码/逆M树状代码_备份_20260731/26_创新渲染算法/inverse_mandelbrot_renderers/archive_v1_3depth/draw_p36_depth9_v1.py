#!/usr/bin/env python3
"""逆M P1~P36 递归9层选择性泡芽 + 涟漪干涉"""
import numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 4000, 4000
SCALE = 320
CX, CY = 0.0, 0.0

def mset_center(p, q):
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

# ── 选择性递归 ──
# 深度越深, q_max越小(控制分支因子), 保证总泡数可控
Q_MAX_BY_DEPTH = [0, 6, 5, 4, 3, 3, 2, 2, 2, 2]  # depth=1..9
MAX_DEPTH = 9
MIN_RADIUS = 1.5  # 最小可见泡半径(像素)

print("[1] 收集泡 (P1~P36, 递归9层·选择性)...")
bulbs = []

def add_bulb(c_center, period, depth):
    if depth > MAX_DEPTH: return
    if abs(c_center) < 1e-12: return
    c_inv = 1.0/c_center
    px = CX + c_inv.real*SCALE
    py = CY + c_inv.imag*SCALE
    
    # 泡的视觉尺寸 (深度越深越小, 但保证可见)
    rr = max(MIN_RADIUS, 6.0 / (1.6**depth))
    
    # 涟漪参数 (深层衰减)
    wlen = max(4, rr * 4 / (1.3**depth))
    amp = max(0.5, rr * 2 / (1.5**depth))
    n_ripples = max(2, 6 - depth//2)
    
    bulbs.append((px, py, rr, period, depth, wlen, amp, n_ripples))
    
    # 递归子芽: q_max随深度递减 → 控制分支
    max_q = Q_MAX_BY_DEPTH[depth] if depth < len(Q_MAX_BY_DEPTH) else 2
    for s in range(2, max_q+1):
        for r in range(1, s):
            if math.gcd(r,s)!=1: continue
            child_p = period * s
            if child_p > MAX_Q * 2: continue
            theta = 2*math.pi*r/s
            r_p = 0.15 / (1.5**max(0,period-1)) * (0.5**depth)
            cc = c_center + r_p * cmath.exp(1j*theta)
            add_bulb(cc, child_p, depth+1)

MAX_Q = 36
# 主心形上的泡 (P2~P36)
for q in range(2, MAX_Q+1):
    for p in range(1, q):
        if math.gcd(p,q)!=1: continue
        add_bulb(mset_center(p,q), q, 1)
    if q % 12 == 0: print(f"  q={q}/{MAX_Q}...")

# 周期2泡子芽
for s in range(2, 7):
    for r in range(1, s):
        if math.gcd(r,s)!=1: continue
        c_child = -1 + 0.25*cmath.exp(1j*2*math.pi*r/s)
        add_bulb(c_child, 2*s, 2)

print(f"  总计: {len(bulbs)}个泡源 (9层递归)")

# ── 波干涉场 ──
print("[2] 干涉衍射波场...")
t0 = time.time()
RW, RH = 1200, 1200  # 波场低分辨率计算
xs = np.linspace(-W/2/SCALE, W/2/SCALE, RW, dtype=np.float64)
ys = np.linspace(-H/2/SCALE, H/2/SCALE, RH, dtype=np.float64)
X, Y = np.meshgrid(xs*SCALE, ys*SCALE)

wave_sum = np.zeros((RH, RW), dtype=np.float64)

for idx, (bx, by, br, period, depth, wlen, amp, nr) in enumerate(bulbs):
    dx = X - bx; dy = Y - by
    dist = np.sqrt(dx*dx + dy*dy)
    cutoff = br + nr * wlen * 1.5
    mask = dist <= cutoff
    if not mask.any(): continue
    d = dist[mask]
    w = np.sin(2*math.pi * d / max(wlen,1)) * (amp / (1 + d/max(br,1)))
    w *= np.exp(-d / max(cutoff,1) * 2.0)
    wave_sum[mask] += w
    if (idx+1)%500==0: print(f"  泡 {idx+1}/{len(bulbs)}...")

print(f"  波场: {time.time()-t0:.1f}s")

# ── 金白涟漪: 上半+镜像, 多层次 ──
print("[2b] 金白涟漪...")
t0 = time.time()
red_field = np.zeros((RH, RW), dtype=np.float64)
upper_sources = []

# P0: 心形多层外扩 (每2°采样×3深度层)
for i in range(91):
    th = math.pi * i / 90
    c_att = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    for expand in [1.15, 1.45, 1.85]:  # 3层深度
        c_out = c_att * expand
        if abs(c_out) < 1e-12: continue
        c_inv = 1.0/c_out
        if abs(c_inv.real) < 6 and abs(c_inv.imag) < 5:
            upper_sources.append((c_inv.real, abs(c_inv.imag), 0))

# P1~P10 泡超吸引中心 (上半)
known_upper = [
    (1,-1.0,0.0),
    (2,-1.754878,0.0),(2,-0.122561,0.744862),
    (3,-1.310703,0.0),(3,-0.156520,1.032247),(3,0.282000,0.530000),
    (4,-1.625413,0.0),(4,-0.504340,0.562765),(4,0.379280,0.334020),(4,-1.860783,0.0),
    (5,-1.476000,0.0),(5,0.374400,0.367200),(5,-0.163423,0.577597),(5,-0.044987,1.050261),
    (6,-1.600357,0.0),(6,0.365640,0.291010),(6,-1.738350,0.0),(6,-1.424870,0.0),
    (6,-0.229542,0.561508),(6,0.220328,0.465829),
    (7,-1.566838,0.0),(7,-1.420594,0.0),(7,0.366218,0.250745),
    # P8+
    (7,0.389000,0.216000),
    (8,-1.520000,0.0),(8,0.373000,0.225000),
    (8,-0.080000,0.692000),(8,-0.325000,0.700000),
    (9,-1.500000,0.0),(9,0.382000,0.201000),
    (9,-0.138000,0.802000),(9,-0.220000,0.605000),
]

for level, cr, ci in known_upper:
    c=complex(cr,ci)
    if abs(c)<1e-12: continue
    c_inv=1.0/c
    if abs(c_inv.real)<6 and abs(c_inv.imag)<5:
        upper_sources.append((c_inv.real,abs(c_inv.imag),level))

# 镜像
red_sources=[]
for cr,ci,level in upper_sources:
    red_sources.append((cr,ci,level))
    if abs(ci)>1e-6: red_sources.append((cr,-ci,level))

n_up=len(upper_sources); n_total=len(red_sources)
print(f"  {n_up}个上半源({n_up-91*3+91*3}心形+泡) → {n_total}个(含镜像)")

# 级联
def level_amp(level): return 1.0/(1.45**level)
def level_cutoff(level): return 4000/(1.5**level)
def level_wavelength(level): return max(12, 200/(1.5**level))
for cr,ci,level in red_sources:
    bx=CX+cr*SCALE; by=CY+ci*SCALE
    dx=X-bx; dy=Y-by; dist=np.sqrt(dx*dx+dy*dy)
    cutoff=level_cutoff(level)
    mask=dist<=cutoff
    if not mask.any(): continue
    d=dist[mask]; wlen=level_wavelength(level); amp=level_amp(level)
    rw=np.sin(2*math.pi*d/wlen)*amp/(1+d/(cutoff/3))
    rw*=np.exp(-d/(cutoff*0.5)*1.8)
    red_field[mask]+=rw
print(f"  红色涟漪: {time.time()-t0:.1f}s")

# ── 渲染 ──
print("[3] 渲染(增强对比+红色涟漪)...")
t0 = time.time()
ws = np.abs(wave_sum)
ws = ws / (ws.max()+1e-30)
# 强对比度拉伸
ws = ws ** 0.35  # gamma 增强

# 红色涟漪层
rf = np.abs(red_field)
rf = rf / (rf.max()+1e-30)
rf = rf ** 0.6

from scipy.ndimage import zoom
ws_big = zoom(ws, (W/RH, W/RW), order=1)
rf_big = zoom(rf, (W/RH, W/RW), order=1)

# 主心形 + 周期2泡路径
pts_c = []
for i in range(2001):
    th=2*math.pi*i/2000
    c=0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th)
    ci=1.0/c; pts_c.append((int(W/2+ci.real*SCALE),int(H/2-ci.imag*SCALE)))
pts2 = []
for i in range(801):
    th=2*math.pi*i/800
    c=math.cos(th)/4+1j*math.sin(th)/4-1; ci=1.0/c
    pts2.append((int(W/2+ci.real*SCALE),int(H/2-ci.imag*SCALE)))

img_arr = np.zeros((W,H,4),dtype=np.uint8)
# 白底 + 波场暗纹
base = np.clip(ws_big, 0, 1)
for c in range(3):
    img_arr[:,:,c]= (255 - base*160).astype(np.uint8)  # 白底暗波

# 金色涟漪 (内金→外白, 金色更醇)
rf = np.abs(red_field)
rf = rf / (rf.max()+1e-30)
rf = rf ** 0.6
rf_big = zoom(rf, (W/RH, W/RW), order=1)

ripple = np.clip(rf_big, 0, 1)
# 醇金RGB(218,165,32) → 白(255,255,255)
gold_r,gold_g,gold_b = 218,165,32
r_r = gold_r + (255-gold_r)*(1-ripple)
r_g = gold_g + (255-gold_g)*(1-ripple)
r_b = gold_b + (255-gold_b)*(1-ripple)
alpha = ripple * 0.6
img_arr[:,:,0] = (img_arr[:,:,0]*(1-alpha) + r_r*alpha).astype(np.uint8)
img_arr[:,:,1] = (img_arr[:,:,1]*(1-alpha) + r_g*alpha).astype(np.uint8)
img_arr[:,:,2] = (img_arr[:,:,2]*(1-alpha) + r_b*alpha).astype(np.uint8)
img_arr[:,:,3] = 255

img_pil=Image.fromarray(img_arr,'RGBA')
draw=ImageDraw.Draw(img_pil)
draw.line(pts_c,fill=(60,60,100,220),width=5)
draw.line(pts2,fill=(180,120,40,180),width=4)

for bx,by,br,period,depth,wlen,amp,nr in bulbs:
    px=int(W/2+(bx-CX)/SCALE*SCALE)
    py=int(H/2-(by-CY)/SCALE*SCALE)
    draw.ellipse([px-1,py-1,px+1,py+1],fill=(80,80,100,40))

draw.text((10,10),f"逆M P1~P36 递归{MAX_DEPTH}层 | {len(bulbs)}泡 | 白底金涟漪",fill=(60,60,80,200))

# 旋转使实轴朝上 (水滴尖朝上)
img_pil = img_pil.rotate(90, expand=True, resample=Image.BILINEAR, fillcolor=(0,0,0,0))

out=os.path.join(OUT_DIR,"逆M_P36_递归9层.png")
img_pil.save(out)
print(f"→ {out}  ({time.time()-t0:.1f}s)")
