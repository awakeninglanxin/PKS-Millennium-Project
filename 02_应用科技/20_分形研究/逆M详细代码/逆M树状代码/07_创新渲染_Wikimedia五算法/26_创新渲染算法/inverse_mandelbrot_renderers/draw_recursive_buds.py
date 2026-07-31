#!/usr/bin/env python3
"""逆M递归泡芽结构: 心形→泡→芽→子芽 递归渲染 (透明背景)"""
import numpy as np, math, cmath, os
from PIL import Image, ImageDraw

OUT_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\26_创新渲染算法\inverse_mandelbrot_renderers"
W, H = 2800, 2800
SCALE = 260

def c_to_px(cx, cy):
    return (int(W/2 + cx*SCALE), int(H/2 - cy*SCALE))

img = Image.new('RGBA', (W, H), (0,0,0,0))
draw = ImageDraw.Draw(img)

# ── 周期调色板 ──
def per_color(period, alpha=200):
    pal = [(0,80,220),(0,180,200),(60,220,120),(160,240,40),
           (240,200,0),(240,120,0),(220,40,80),(180,0,160),
           (120,40,220),(60,80,240),(0,160,200),(0,200,120)]
    return pal[(period-1)%len(pal)] + (alpha,)

# ── 1. 主心形 (period 1) ──
print("[1] 主心形 ...")
N1 = 2000
pts = []
for i in range(N1+1):
    th = 2*math.pi*i/N1
    c = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    c_i = 1.0/c
    pts.append(c_to_px(c_i.real, c_i.imag))
draw.line(pts, fill=per_color(1,220), width=4)

# ── 2. 周期2泡 (精确) ──
print("[2] 周期2泡 ...")
pts = []
for i in range(801):
    th = 2*math.pi*i/800
    c = math.cos(th)/4 + 1j*math.sin(th)/4 - 1
    c_i = 1.0/c
    pts.append(c_to_px(c_i.real, c_i.imag))
draw.line(pts, fill=per_color(2,220), width=4)

# ── 3. 递归画泡芽 ──
MAX_DEPTH = 3  # 递归深度

def farey_children(q):
    """返回q的所有Farey子分数 (r/s, s<q)"""
    kids = []
    for s in range(2, q):
        for r in range(1, s):
            if math.gcd(r,s)==1: kids.append((r,s))
    return kids

def mset_bulb_center(p, q):
    """标准M集上Farey p/q泡的中心"""
    th = 2*math.pi*p/q
    return 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)

def draw_bulb(c_center, period, depth, max_depth, i_angle=0.0):
    """
    递归画泡及其子芽
    c_center: 标准M集上的泡中心(复数)
    period: 泡周期
    depth: 当前递归深度
    i_angle: 内部附着角度(弧度)
    """
    if depth > max_depth: return
    if abs(c_center) < 1e-12: return
    
    # 反演到逆M空间
    c_inv = 1.0/c_center
    px, py = c_to_px(c_inv.real, c_inv.imag)
    
    # 泡的近似半径 (指数衰减)
    r_m = 0.15 / (1.8 ** (period-1)) * (0.4 ** depth)
    if depth == 0:
        # 第一层: 用更精确的半径
        r_m = 1.0 / (1.5 + period*0.5)
    
    # 反演后的半径 (从M集到逆M)
    deriv = 1.0/(c_center*c_center)
    r_inv = r_m * abs(deriv)
    
    rr = max(int(r_inv*SCALE), 1)
    if rr < 1: return
    
    # 画泡
    col = per_color(period, max(100, 220-depth*40))
    draw.ellipse([px-rr, py-rr, px+rr, py+rr], outline=col, width=max(1,3-depth))
    
    if rr > 3:
        # 标周期
        lbl = f"P{period}"
        draw.text((px+rr+2, py-5), lbl, fill=(255,255,255,120))
    
    # ── 递归画子芽 ──
    # 子芽的Farey分数: 附着在父边界上的内角 r/s
    # 对period-q的泡,子芽周期=q×s
    n_kids = 0
    max_q_child = max(3, 7 - depth*2)
    for s in range(2, max_q_child+1):
        for r in range(1, s):
            if math.gcd(r,s) != 1: continue
            child_period = period * s
            if child_period > 30: continue
            
            # 子芽中心 ≈ 父中心 + 父半径×exp(iθ) 在M集上
            theta = i_angle + 2*math.pi*r/s
            c_child = c_center + r_m * cmath.exp(1j*theta)
            
            # 递归画子芽
            draw_bulb(c_child, child_period, depth+1, max_depth, theta)
            n_kids += 1
    
    if n_kids > 0 and depth == 0:
        print(f"  深度{depth} 周期P{period}: {n_kids}个子芽")

print("[3] 第一层泡 (主心形上的子泡)...")
# 主心形(period=1)上的子泡: Farey分数p/q, child_period=q
for q in range(2, 10):
    for p in range(1, q):
        if math.gcd(p,q)!=1: continue
        c = mset_bulb_center(p, q)
        draw_bulb(c, q, 1, MAX_DEPTH, 2*math.pi*p/q)
        print(f"  P{q} (p/q={p}/{q}) 递归画子芽...")

# 周期2泡上的子芽
print("[4] 周期2泡上的子芽...")
for s in range(2, 6):
    for r in range(1, s):
        if math.gcd(r,s)!=1: continue
        # 周期2泡的中心c=-1, 半径0.25
        theta = 2*math.pi*r/s
        c_child = -1 + 0.25*cmath.exp(1j*theta)
        child_period = 2*s
        if child_period <= 20:
            draw_bulb(c_child, child_period, 2, MAX_DEPTH, theta)

# ── 坐标轴 ──
draw.line([(0,H//2),(W-1,H//2)], fill=(128,128,128,40), width=1)
draw.line([(W//2,0),(W//2,H-1)], fill=(128,128,128,40), width=1)
for val in range(-6, 9):
    if val==0: continue
    for coord, horiz in [((val,0),True),((0,val),False)]:
        px,py = c_to_px(*coord)
        if 0<=px<W and 0<=py<H:
            if horiz:
                draw.line([(px,py-3),(px,py+3)], fill=(128,128,128,60))
                draw.text((px-6,py+4), str(val), fill=(128,128,128,60))
            else:
                draw.line([(px-3,py),(px+3,py)], fill=(128,128,128,60))
                draw.text((px+4,py-5), str(val), fill=(128,128,128,60))

draw.text((10,10),"逆M递归泡芽: 心形→子泡→孙泡→曾孙泡 (~3层递归)", fill=(255,255,255,180))
draw.text((10,30),"颜色=周期  |  透明背景", fill=(200,200,200,120))

out = os.path.join(OUT_DIR, "逆M_递归泡芽全图.png")
img.save(out)
print(f"\n→ {out}")
