#!/usr/bin/env python3
"""逆M递归泡芽 + 泡外涟漪同心圆 (P1~P20, 透明背景)"""
import numpy as np, math, cmath, os
from PIL import Image, ImageDraw

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 3000, 3000
SCALE = 280

def c_to_px(cx, cy):
    return (int(W/2 + cx*SCALE), int(H/2 - cy*SCALE))

img = Image.new('RGBA', (W, H), (0,0,0,0))
draw = ImageDraw.Draw(img)

def per_color(period, alpha=200):
    pal = [(0,80,220),(0,180,200),(60,220,120),(160,240,40),
           (240,200,0),(240,120,0),(220,40,80),(180,0,160),
           (120,40,220),(60,80,240),(0,160,200),(0,200,120),
           (100,100,200),(200,100,100),(100,200,100),(200,200,100),
           (200,100,200),(100,200,200),(200,200,200),(150,150,255)]
    return pal[(period-1)%len(pal)] + (alpha,)

# ── 1. 主心形 ──
print("[1] 主心形 (P1)...")
pts = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    c_i = 1.0/c
    pts.append(c_to_px(c_i.real, c_i.imag))
draw.line(pts, fill=per_color(1,220), width=4)

# ── 2. 周期2泡 ──
print("[2] 周期2泡...")
pts = []
for i in range(801):
    th = 2*math.pi*i/800
    c = math.cos(th)/4 + 1j*math.sin(th)/4 - 1
    c_i = 1.0/c
    pts.append(c_to_px(c_i.real, c_i.imag))
draw.line(pts, fill=per_color(2,220), width=4)

# ── 3. 画泡 + 涟漪 ──
MAX_PERIOD = 24  # 最高周期
MAX_DEPTH = 2    # 递归深度

def mset_center(p, q):
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

def draw_bulb_with_ripples(c_center, period, depth, max_depth):
    """递归画泡 + 本地的涟漪同心圆"""
    if depth > max_depth: return
    if abs(c_center) < 1e-12: return
    
    c_inv = 1.0/c_center
    px, py = c_to_px(c_inv.real, c_inv.imag)
    
    # 泡半径 (指数衰减)
    if depth == 0:
        r_m = 1.0 / (1.5 + period*0.5)
    else:
        r_m = 0.15 / (1.8 ** (period-1)) * (0.4 ** depth)
    
    deriv = 1.0/(c_center*c_center)
    r_inv = r_m * abs(deriv)
    rr = max(int(r_inv*SCALE), 2)
    if rr < 1: return
    
    # 画泡本身
    col = per_color(period, max(100, 220-depth*50))
    draw.ellipse([px-rr, py-rr, px+rr, py+rr], outline=col, width=max(1,2-depth))
    
    # ── ★ 泡外涟漪同心圆 (本地水波) ★ ──
    # 从泡边界向外画 n_ripples 个同心圆
    if rr >= 3:
        n_ripples = min(6 + period, 18)          # 涟漪数量随周期增加
        ripple_gap = max(2, rr // 2)              # 涟漪间距 = 泡半径的一半
        max_ripple_r = rr + n_ripples * ripple_gap
        
        for ri in range(1, n_ripples+1):
            r_ripple = rr + ri * ripple_gap
            if r_ripple > 500: break  # 不要画到图像外面
            
            # 涟漪透明度随距离衰减
            fade = max(30, 180 - ri * 15)
            ripple_col = col[:3] + (fade,)
            draw.ellipse([px-r_ripple, py-r_ripple, 
                         px+r_ripple, py+r_ripple], 
                        outline=ripple_col, width=max(1, 2 - ri//6))
    
    # 递归画子芽
    max_q_child = max(3, 8 - depth*2)
    for s in range(2, max_q_child+1):
        for r in range(1, s):
            if math.gcd(r,s) != 1: continue
            child_period = period * s
            if child_period > MAX_PERIOD: continue
            
            theta = 2*math.pi*r/s
            c_child = c_center + r_m * cmath.exp(1j*theta)
            draw_bulb_with_ripples(c_child, child_period, depth+1, max_depth)

# ── 第一阶段: 主心形上2~MAX_PERIOD周期泡 ──
print("[3] 主心形上的泡 (P2~P24)...")
count = 0
for q in range(2, MAX_PERIOD+1):
    for p in range(1, q):
        if math.gcd(p,q)!=1: continue
        c = mset_center(p, q)
        draw_bulb_with_ripples(c, q, 1, MAX_DEPTH)
        count += 1
        if count % 20 == 0:
            print(f"  已处理 {count} 个泡...")

# ── 第二阶段: 周期2泡上的子芽 ──
print("[4] 周期2泡上的子芽...")
for s in range(2, 6):
    for r in range(1, s):
        if math.gcd(r,s)!=1: continue
        theta = 2*math.pi*r/s
        c_child = -1 + 0.25*cmath.exp(1j*theta)
        child_period = 2*s
        if child_period <= MAX_PERIOD:
            draw_bulb_with_ripples(c_child, child_period, 2, MAX_DEPTH)

print(f"\n  总计: ~{count}个泡 + 涟漪")

# ── 坐标轴 ──
draw.line([(0,H//2),(W-1,H//2)], fill=(128,128,128,30), width=1)
draw.line([(W//2,0),(W//2,H-1)], fill=(128,128,128,30), width=1)

draw.text((10,10),f"逆M P1~P{MAX_PERIOD} 泡芽+本地涟漪 (~{count}泡)", fill=(255,255,255,180))
draw.text((10,30),"每个泡向外发射同心圆涟漪 (透明度随距离衰减)", fill=(200,200,200,120))

out = os.path.join(OUT_DIR, "逆M_泡芽涟漪全图.png")
img.save(out)
print(f"\n→ {out}")
