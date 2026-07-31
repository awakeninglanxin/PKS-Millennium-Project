#!/usr/bin/env python3
"""逆M集主心形+各周期泡边界曲线图 (透明背景PNG)"""
import numpy as np, math, cmath, os
from PIL import Image, ImageDraw

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 2400, 2400
CX, CY = 0.0, 0.0  # view center
SCALE = 220  # pixels per unit

def c_to_px(cx, cy):
    return (int(W/2 + cx*SCALE), int(H/2 - cy*SCALE))

img = Image.new('RGBA', (W, H), (0,0,0,0))
draw = ImageDraw.Draw(img)

# ── 逆M主心形 (period 1) ──
print("逆M主心形 (period 1)...")
pts1 = []
N1 = 2000
for i in range(N1+1):
    th = 2*math.pi*i/N1
    c_cls = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    c_inv = 1.0/c_cls
    pts1.append(c_to_px(c_inv.real, c_inv.imag))
draw.line(pts1, fill=(0,80,200,200), width=3)
print(f"  心形: {len(pts1)}点")

# ── 逆M周期2泡 ──
print("逆M周期2泡...")
pts2 = []
N2 = 800
for i in range(N2+1):
    th = 2*math.pi*i/N2
    c_cls = math.cos(th)/4 + 1j*math.sin(th)/4 - 1
    c_inv = 1.0/c_cls
    pts2.append(c_to_px(c_inv.real, c_inv.imag))
draw.line(pts2, fill=(200,80,0,200), width=3)
print(f"  周期2: {len(pts2)}点")

# ── 更高周期泡 ──
def farey_bulb_center(p, q):
    """Farey分数p/q对应的泡在标准M集上的中心"""
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

def bulb_radius(q):
    """泡的近似半径 (随周期指数衰减)"""
    return 0.5 / (2**q)

# 颜色从蓝到紫渐变
colors = [(0,160,255,180),(0,220,180,180),(100,255,100,180),
          (200,255,0,180),(255,200,0,180),(255,100,0,180),
          (255,0,100,180),(200,0,200,180),(150,0,255,180)]

print("各周期泡 (Farey fractions)...")
max_q = 8
n_total = 0
for q in range(3, max_q+1):
    for p in range(1, q):
        if math.gcd(p, q) != 1: continue
        # 标准M集上的泡中心
        c = farey_bulb_center(p, q)
        # 反演到逆M空间
        c_inv = 1.0 / c
        r_approx = abs(c_inv) * bulb_radius(q) / abs(c)  # 反演后的近似半径
        
        cx, cy = c_to_px(c_inv.real, c_inv.imag)
        rr = max(int(r_approx*SCALE), 3)
        
        # 画椭圆泡
        color = colors[(q-3)%len(colors)]
        draw.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=color, width=2)
        
        # 标Farey标签
        label = f"{p}/{q}"
        draw.text((cx+rr+3, cy-4), label, fill=(255,255,255,160))
        n_total += 1
print(f"  共{n_total}个高周期泡")

# ── 坐标轴 (淡灰) ──
draw.line([(0,H//2),(W-1,H//2)], fill=(128,128,128,60), width=1)
draw.line([(W//2,0),(W//2,H-1)], fill=(128,128,128,60), width=1)

# 标轴刻度
for val in range(-6, 8):
    if val == 0: continue
    px, py = c_to_px(val, 0)
    if 0<=px<W and 0<=py<H:
        draw.line([(px, py-4),(px, py+4)], fill=(128,128,128,80), width=1)
        draw.text((px-8, py+5), str(val), fill=(128,128,128,80))
    px, py = c_to_px(0, val)
    if 0<=px<W and 0<=py<H:
        draw.line([(px-4, py),(px+4, py)], fill=(128,128,128,80), width=1)
        draw.text((px+5, py-6), str(val), fill=(128,128,128,80))

draw.text((10,10), "逆M集周期边界: 蓝=心形(P1) 橙=P2 高期=彩色泡", fill=(255,255,255,180))
draw.text((10,30), "c_inv = 1 / (e^(iθ)/2 - e^(2iθ)/4)", fill=(200,200,200,150))

out = os.path.join(OUT_DIR, "逆M_周期边界全图.png")
img.save(out)
print(f"\n→ {out}")
