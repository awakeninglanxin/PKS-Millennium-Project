#!/usr/bin/env python3
"""逆M泡涟漪干涉衍射: 递归泡+子芽涟漪全叠加, 自然干涉波"""
import numpy as np, math, cmath, os, time
from PIL import Image

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 2400, 2400
SCALE = 200
CX, CY = 0.0, 0.0

def complex_to_pixel(c):
    return (CX + c.real*SCALE, CY + c.imag*SCALE)

# ── 收集所有泡中心和半径 ──
print("[1] 收集泡中心数据...")
bulbs = []  # [(cx_px, cy_px, radius_px, period), ...]

def mset_center(p, q):
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

def collect_bulbs(c_center, period, depth, max_depth):
    if depth > max_depth: return
    if abs(c_center) < 1e-12: return
    c_inv = 1.0/c_center
    px = CX + c_inv.real*SCALE
    py = CY + c_inv.imag*SCALE
    
    if depth == 0:
        r_m = 1.0 / (1.5 + period*0.5)
    else:
        r_m = 0.15 / (1.8**(period-1)) * (0.4**depth)
    deriv = 1.0/(c_center*c_center)
    r_inv = r_m * abs(deriv)
    rr = r_inv*SCALE
    if rr < 1:
        rr = 1.0
        wavelength = 5.0
        amplitude = 2.0
        n_ripples = 3
    else:
        wavelength = max(10, rr * 3)
        amplitude = rr * 3
        n_ripples = min(6 + period, 18)
    
    bulbs.append((px, py, rr, period, wavelength, amplitude, n_ripples))
    
    # 递归子芽
    max_qc = max(3, 7 - depth*2)
    for s in range(2, max_qc+1):
        for r in range(1, s):
            if math.gcd(r,s)!=1: continue
            cp = period * s
            if cp > 28: continue
            theta = 2*math.pi*r/s
            cc = c_center + r_m * cmath.exp(1j*theta)
            collect_bulbs(cc, cp, depth+1, max_depth)

# 主心形上的泡
for q in range(2, 26):
    for p in range(1, q):
        if math.gcd(p,q)!=1: continue
        collect_bulbs(mset_center(p,q), q, 1, 3)  # 递归3层

# 周期2泡上的子芽
for s in range(2, 6):
    for r in range(1, s):
        if math.gcd(r,s)!=1: continue
        c_child = -1 + 0.25*cmath.exp(1j*2*math.pi*r/s)
        collect_bulbs(c_child, 2*s, 2, 2)

print(f"  共{len(bulbs)}个泡源")

# ── 干涉波场计算 ──
print("[2] 干涉衍射波场计算...")
t0 = time.time()

# 输出分辨率
RW, RH = 1200, 1200
xs = np.linspace(-W/2/SCALE, W/2/SCALE, RW, dtype=np.float64)
ys = np.linspace(-H/2/SCALE, H/2/SCALE, RH, dtype=np.float64)
X, Y = np.meshgrid(xs*SCALE, ys*SCALE)  # 像素坐标

wave_sum = np.zeros((RH, RW), dtype=np.float64)

for idx, (bx, by, br, period, wlen, amp, n_ripples) in enumerate(bulbs):
    # 距离场
    dx = X - bx
    dy = Y - by
    dist = np.sqrt(dx*dx + dy*dy)
    
    # 截止半径: 只算有限范围
    cutoff = br + n_ripples * wlen
    
    # 掩码: 在截止半径内的像素
    mask = dist <= cutoff
    if not mask.any(): continue
    
    d = dist[mask]
    
    # 波: sin(2π × 距离/波长) × 振幅 × 衰减
    # 振幅衰减: exp(-距离/截止半径)
    wave = np.sin(2*math.pi * d / wlen) * (amp / (1 + d/br))
    wave *= np.exp(-d / cutoff * 3)  # 指数衰减
    
    wave_sum[mask] += wave
    
    if (idx+1) % 40 == 0:
        print(f"  泡 {idx+1}/{len(bulbs)}...")

print(f"  波场计算完成: {time.time()-t0:.1f}s")

# ── 渲染 ──
print("[3] 渲染...")
# 归一化波场强度
ws = wave_sum.copy()
# 取模量 + 加基线
ws = np.abs(ws)
ws = ws / (ws.max() + 1e-30)
# gamma 拉伸增强对比度
ws = ws ** 0.5

# 主心形边界 (作为遮罩)
print("  渲染主心形...")
N1 = 2000
mask_pts = []
for i in range(N1+1):
    th = 2*math.pi*i/N1
    c = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    c_i = 1.0/c
    mask_pts.append((c_i.real, c_i.imag))

# 画心形叠加
img_arr = np.zeros((RH, RW, 4), dtype=np.uint8)
# 波场背景: 蓝白渐变
for c in range(3):
    img_arr[:,:,c] = (ws * 200 + 55).astype(np.uint8)
img_arr[:,:,3] = 255

# 心形边界白色高亮
from PIL import ImageDraw, Image
img_pil = Image.fromarray(img_arr, 'RGBA')
draw = ImageDraw.Draw(img_pil)

# 心形白色粗边
pts_px = []
for rx, ry in mask_pts:
    px = int(RW/2 + rx*SCALE * RW/W)
    py = int(RH/2 - ry*SCALE * RH/H)
    pts_px.append((px, py))
draw.line(pts_px, fill=(255,255,255,200), width=4)

# 周期2泡
pts2 = []
for i in range(801):
    th = 2*math.pi*i/800
    c = math.cos(th)/4 + 1j*math.sin(th)/4 - 1
    c_i = 1.0/c
    px = int(RW/2 + c_i.real*SCALE * RW/W)
    py = int(RH/2 - c_i.imag*SCALE * RH/H)
    pts2.append((px, py))
draw.line(pts2, fill=(255,200,100,180), width=3)

# 泡位置标记
for bx, by, br, period, wlen, amp, nr in bulbs:
    px = int(RW/2 + (bx-CX)/SCALE * SCALE * RW/W)
    py = int(RH/2 - (by-CY)/SCALE * SCALE * RH/H)
    rr = max(int(br * RW/W), 1)
    if rr >= 1:
        draw.ellipse([px-rr, py-rr, px+rr, py+rr], outline=(255,255,255,80), width=1)

out = os.path.join(OUT_DIR, "逆M_涟漪干涉衍射.png")
img_pil.save(out)
print(f"→ {out}")
print(f"总耗时: {time.time()-t0:.1f}s")
