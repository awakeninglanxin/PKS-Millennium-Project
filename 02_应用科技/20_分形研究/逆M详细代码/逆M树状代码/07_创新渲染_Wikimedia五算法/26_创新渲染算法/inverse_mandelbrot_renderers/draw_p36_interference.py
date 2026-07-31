#!/usr/bin/env python3
"""逆M P1~P36递归泡芽涟漪衍射(大分辨率+全波干涉)"""
import numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 4000, 4000
SCALE = 320
CX, CY = 0.0, 0.0

def mset_center(p, q):
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

# ── 第1阶段: 收集全部泡 ──
print("[1] 收集泡 (P1~P36, 递归3层)...")
bulbs = []  # (px, py, rr, period, wavelength, amplitude, n_ripples)

MAX_Q = 36  # Farey分母最大36
MAX_DEPTH = 3  # 递归深度

def add_bulb(c_center, period, depth):
    if depth > MAX_DEPTH: return
    if abs(c_center) < 1e-12: return
    c_inv = 1.0/c_center
    px = CX + c_inv.real*SCALE
    py = CY + c_inv.imag*SCALE
    
    # 可见尺寸: 无视物理半径, 确保每个泡可见
    if depth == 0:
        rr = 6.0  # 心形用不同画法
    else:
        # 按深度衰减尺寸但保证可见
        rr = max(2.0, 8.0 / (1.5**depth) * (0.7**max(0,period-2)))
    
    wavelength = max(6, rr * 4)
    amplitude = rr * 2
    n_ripples = min(8 + period, 24)
    
    bulbs.append((px, py, rr, period, wavelength, amplitude, n_ripples))
    
    # 递归子芽
    max_s = max(2, 6 - depth)
    for s in range(2, max_s+1):
        for r in range(1, s):
            if math.gcd(r,s)!=1: continue
            child_p = period * s
            if child_p > MAX_Q * 2: continue
            theta = 2*math.pi*r/s
            r_parent = 0.15 / (1.5**(period-1)) * (0.5**depth)
            cc = c_center + r_parent * cmath.exp(1j*theta)
            add_bulb(cc, child_p, depth+1)

# 主心形上的泡 (P2~P36)
for q in range(2, MAX_Q+1):
    for p in range(1, q):
        if math.gcd(p,q)!=1: continue
        add_bulb(mset_center(p,q), q, 1)
    if q % 6 == 0:
        print(f"  q={q}/36...")

# P2泡上的子芽
for s in range(2, 8):
    for r in range(1, s):
        if math.gcd(r,s)!=1: continue
        c_child = -1 + 0.25*cmath.exp(1j*2*math.pi*r/s)
        add_bulb(c_child, 2*s, 2)

print(f"  总计: {len(bulbs)}个泡源")

# ── 第2阶段: 波干涉场 ──
print("[2] 干涉衍射波场计算...")
t0 = time.time()
RW, RH = 1500, 1500  # 波场计算分辨率(直接全分辨率3层太慢,中等分辨率取波场再放大)
xs = np.linspace(-W/2/SCALE, W/2/SCALE, RW, dtype=np.float64)
ys = np.linspace(-H/2/SCALE, H/2/SCALE, RH, dtype=np.float64)
X, Y = np.meshgrid(xs*SCALE, ys*SCALE)

wave_sum = np.zeros((RH, RW), dtype=np.float64)

for idx, (bx, by, br, period, wlen, amp, nr) in enumerate(bulbs):
    dx = X - bx; dy = Y - by
    dist = np.sqrt(dx*dx + dy*dy)
    cutoff = br + nr * wlen
    mask = dist <= cutoff
    if not mask.any(): continue
    d = dist[mask]
    wave = np.sin(2*math.pi * d / wlen) * (amp / (1 + d/max(br,1)))
    wave *= np.exp(-d / max(cutoff,1) * 2.5)
    wave_sum[mask] += wave
    if (idx+1)%100==0: print(f"  泡 {idx+1}/{len(bulbs)}...")

print(f"  波场计算: {time.time()-t0:.1f}s")

# ── 第3阶段: 渲染输出 ──
print("[3] 渲染...")
# 波场归一化
ws = np.abs(wave_sum)
ws = ws / (ws.max() + 1e-30)
ws = ws ** 0.6  # gamma

# 放大到最终分辨率
from scipy.ndimage import zoom
ws_big = zoom(ws, (W/RH, W/RW), order=1)

# 主心形
pts_c = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    c_i = 1.0/c
    pts_c.append((int(W/2 + c_i.real*SCALE), int(H/2 - c_i.imag*SCALE)))

# 周期2泡
pts2 = []
for i in range(801):
    th = 2*math.pi*i/800
    c = math.cos(th)/4 + 1j*math.sin(th)/4 - 1
    c_i = 1.0/c
    pts2.append((int(W/2 + c_i.real*SCALE), int(H/2 - c_i.imag*SCALE)))

# 拼图
img_arr = np.zeros((W, H, 4), dtype=np.uint8)
# 蓝白渐变背景
for c in range(3):
    img_arr[:,:,c] = (np.clip(ws_big, 0, 1) * 200 + 55).astype(np.uint8)
img_arr[:,:,3] = 255

img_pil = Image.fromarray(img_arr, 'RGBA')
draw = ImageDraw.Draw(img_pil)
draw.line(pts_c, fill=(255,255,255,220), width=5)
draw.line(pts2, fill=(255,200,100,180), width=4)

# 泡标记
for bx, by, br, period, wlen, amp, nr in bulbs:
    px = int(W/2 + (bx-CX)/SCALE * SCALE)
    py = int(H/2 - (by-CY)/SCALE * SCALE)
    rv = max(int(br), 1)
    col = (min(200+period*2,255), min(180+period,255), 100, 100)
    draw.ellipse([px-rv, py-rv, px+rv, py+rv], outline=col, width=1)

draw.text((10,10), f"逆M P1~P36 递归3层 | {len(bulbs)}个泡源 | 波干涉衍射", fill=(255,255,255,200))

out = os.path.join(OUT_DIR, "逆M_P36_涟漪干涉.png")
img_pil.save(out)
print(f"→ {out}")
print(f"总耗时: {time.time()-t0:.1f}s")
