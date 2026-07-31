#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v15: 莱维钻石 / Koch-8段 平替六角帕斯卡 × 逆M渲染

用法: python main_fractal_replace_v15.py levy_diamond
      python main_fractal_replace_v15.py koch8
"""
import numpy as np, math, os, sys, time
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb as h2r

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
od = os.path.dirname(os.path.abspath(__file__))

FRACTAL = sys.argv[1] if len(sys.argv) > 1 else 'levy_diamond'
if FRACTAL not in ('levy_diamond', 'koch8'):
    print(f"Usage: {sys.argv[0]} levy_diamond|koch8")
    sys.exit(1)

# ==================== 参数 ====================
N_ROWS = 2048
HEX_SCALE = 0.003
W, H = 2400, 2025
MAX_ITER = 300; ESCAPE_RADIUS = 50.0
TIP = 4.0; BOTTOM = -4/3; HSP = 1.6242719100; EXPAND = 4.0
R0, R1 = BOTTOM - EXPAND, TIP + EXPAND
I0, I1 = -HSP - EXPAND, HSP + EXPAND

A, B_MOB, C_MOB, D_MOB = 1+0j, 0+0j, 1+0j, -2+0j
nuc_w = 0.0 + 0j

if FRACTAL == 'levy_diamond':
    DEPTH = 5; D_VAL = math.log(3)/math.log(2)
    print(f"=== v15a: 莱维钻石 D={D_VAL:.3f} depth={DEPTH} ===")
else:
    DEPTH = 4; D_VAL = math.log(8)/math.log(4)
    print(f"=== v15b: Koch-8段 D={D_VAL:.3f} depth={DEPTH} ===")

# ==================== 阶段0: LUT 生成 ====================
t0 = time.time()

if FRACTAL == 'levy_diamond':
    # Lévy Diamond: L-system F→F+F--F+F, angle=60°, 3^n segments
    # Step 1: generate curve coordinates
    def levy_diamond_lut(depth, N):
        """Lévy diamond: 生成曲线→填充内部区域"""
        # Generate turn sequence
        turns = []
        for _ in range(depth):
            new = []
            for t in turns: new.append(t)
            new.append(1)
            for t in reversed(turns): new.append(-t)
            turns = new
        
        sx, sy = 0, 0
        points = [(0.0, 0.0)]
        angle = 0
        for t in turns:
            angle = (angle + t) % 6
            dx = math.cos(angle * math.pi / 3.0)
            dy = math.sin(angle * math.pi / 3.0)
            sx += dx; sy += dy
            points.append((sx, sy))
        pts = np.array(points)
        
        xmin, xmax = pts[:,0].min(), pts[:,0].max()
        ymin, ymax = pts[:,1].min(), pts[:,1].max()
        scale = (N - 4) / max(xmax-xmin, ymax-ymin, 1)
        cx = (xmin + xmax) / 2; cy = (ymin + ymax) / 2
        
        # Draw curve as boundary (line_width=3)
        boundary = np.zeros((N, N), dtype=np.int16)
        for i in range(len(pts)-1):
            x1 = int((pts[i,0] - cx) * scale + N/2)
            y1 = int((pts[i,1] - cy) * scale + N/2)
            x2 = int((pts[i+1,0] - cx) * scale + N/2)
            y2 = int((pts[i+1,1] - cy) * scale + N/2)
            steps = max(abs(x2-x1), abs(y2-y1), 1)
            for t in range(steps+1):
                xi = x1 + (x2-x1)*t//steps
                yi = y1 + (y2-y1)*t//steps
                for dx in range(-2, 3):
                    for dy2 in range(-2, 3):
                        nx, ny = xi+dx, yi+dy2
                        if 0 <= nx < N and 0 <= ny < N:
                            boundary[ny, nx] = 1
        
        # Flood fill: fill half of interior regions
        from collections import deque
        filled = boundary.copy()
        visited = np.zeros((N, N), dtype=bool)
        
        # Scanline: find regions and fill every other one
        region_id = 0
        for y0 in range(N):
            for x0 in range(N):
                if filled[y0, x0] == 0 and not visited[y0, x0]:
                    # BFS flood fill this region
                    q = deque([(x0, y0)])
                    visited[y0, x0] = True
                    region_pixels = []
                    while q:
                        x, y = q.popleft()
                        region_pixels.append((x, y))
                        for dx, dy2 in [(1,0),(-1,0),(0,1),(0,-1)]:
                            nx, ny = x+dx, y+dy2
                            if 0 <= nx < N and 0 <= ny < N:
                                if filled[ny, nx] == 0 and not visited[ny, nx]:
                                    visited[ny, nx] = True
                                    q.append((nx, ny))
                    # Fill odd-numbered regions
                    if region_id % 2 == 1:
                        for x, y in region_pixels:
                            filled[y, x] = 2
                    region_id += 1
        
        return filled
    
    pascal = levy_diamond_lut(DEPTH, N_ROWS)

else:  # koch8
    # Koch 8-segment: 1 segment → 8 segments, scale 1/4, D=1.5
    # Pattern: 4 equal parts, middle two → outward square + inward square
    # Line: ___ ___ ___ ___  (4 parts)
    # → keep 1st, 2nd→outward square(3 segments), 3rd→inward square(3 segments), keep 4th
    def koch8_lut(depth, N):
        """Koch-8: 生成曲线→填充内部区域"""
        def koch8_segments(p1, p2, d):
            if d == 0: return [(p1, p2)]
            x1, y1 = p1; x2, y2 = p2
            dx, dy = (x2-x1)/4.0, (y2-y1)/4.0
            px, py = -dy*4, dx*4
            
            s1 = (x1+dx, y1+dy); s2 = (x1+2*dx, y1+2*dy)
            s3 = (x1+3*dx, y1+3*dy)
            
            r1 = koch8_segments(p1, s1, d-1)
            r2a= koch8_segments(s1, (s1[0]+px/4, s1[1]+py/4), d-1)
            r2b= koch8_segments((s1[0]+px/4,s1[1]+py/4),(s2[0]+px/4,s2[1]+py/4), d-1)
            r2c= koch8_segments((s2[0]+px/4,s2[1]+py/4), s2, d-1)
            r3a= koch8_segments(s2, (s2[0]-px/4, s2[1]-py/4), d-1)
            r3b= koch8_segments((s2[0]-px/4,s2[1]-py/4),(s3[0]-px/4,s3[1]-py/4), d-1)
            r3c= koch8_segments((s3[0]-px/4,s3[1]-py/4), s3, d-1)
            r4 = koch8_segments(s3, p2, d-1)
            return r1+r2a+r2b+r2c+r3a+r3b+r3c+r4
        
        segs = koch8_segments((0.0,0.0), (1.0,0.0), depth)
        
        # Draw boundary
        boundary = np.zeros((N, N), dtype=np.int16)
        for (x1,y1),(x2,y2) in segs:
            xi1, yi1 = int(x1*N), int(y1*N+N/2)
            xi2, yi2 = int(x2*N), int(y2*N+N/2)
            steps = max(abs(xi2-xi1), abs(yi2-yi1), 1)
            for t in range(steps+1):
                xi = xi1+(xi2-xi1)*t//steps
                yi = yi1+(yi2-yi1)*t//steps
                for dx in range(-1,2):
                    for dy2 in range(-1,2):
                        nx, ny = xi+dx, yi+dy2
                        if 0 <= nx < N and 0 <= ny < N:
                            boundary[ny, nx] = 1
        
        # Flood fill
        from collections import deque
        filled = boundary.copy()
        visited = np.zeros((N,N), dtype=bool)
        rid = 0
        for y0 in range(N):
            for x0 in range(N):
                if filled[y0,x0]==0 and not visited[y0,x0]:
                    q=deque([(x0,y0)]); visited[y0,x0]=True
                    rp=[]
                    while q:
                        x,y=q.popleft(); rp.append((x,y))
                        for dx,dy2 in [(1,0),(-1,0),(0,1),(0,-1)]:
                            nx,ny=x+dx,y+dy2
                            if 0<=nx<N and 0<=ny<N and filled[ny,nx]==0 and not visited[ny,nx]:
                                visited[ny,nx]=True; q.append((nx,ny))
                    if rid%2==1:
                        for x,y in rp: filled[y,x]=2
                    rid+=1
        return filled
    
    pascal = koch8_lut(DEPTH, N_ROWS)

fill_lut = (pascal > 0).mean() * 100
print(f"[0/5] LUT生成: fill={fill_lut:.1f}% ({time.time()-t0:.1f}s)")

# ==================== 阶段1: 逆M迭代 ====================
print("[1/5] 逆M迭代...")
xs, ys = np.linspace(R0, R1, W), np.linspace(I0, I1, H)
X, Y = np.meshgrid(xs, ys); w_grid = X + 1j*Y
eps = 1e-12; sf = np.abs(w_grid) > eps
ce = np.zeros_like(w_grid, dtype=np.complex128)
ce[sf] = 1.0/w_grid[sf]; ce[~sf] = 1e6
Z_iter = np.zeros_like(ce)
it = np.full(ce.shape, -1, dtype=np.int32)
for i in range(MAX_ITER):
    act = it == -1
    if not np.any(act): break
    Z_iter[act] = Z_iter[act]**2 + ce[act]
    esc = act & (np.abs(Z_iter) > ESCAPE_RADIUS)
    it[esc] = i
it[it == -1] = MAX_ITER
interior = it == MAX_ITER; escaped = ~interior
print(f"  interior: {interior.sum()/(W*H)*100:.1f}%")

# 核点
cx, cy = 0.0, 0.0
dist_nuc = np.sqrt((X-cx)**2 + (Y-cy)**2)
r_valid_d = dist_nuc[escaped]
r_min = np.percentile(r_valid_d, 3); r_max = np.percentile(r_valid_d, 95)

# ==================== 阶段2: Möbius ====================
def mobius(z, a, b, c, d):
    num = a*z+b; den = c*z+d
    safe = np.abs(den)>1e-12
    r = np.full(z.shape, np.nan+1j*np.nan, dtype=np.complex128)
    r[safe] = num[safe]/den[safe]; return r

print("[2/5] Möbius...")
nuc_z = mobius(np.array([nuc_w]), A, B_MOB, C_MOB, D_MOB)[0]
if np.isnan(nuc_z.real): nuc_z = 0+0j
w_int = w_grid[interior]; zm = mobius(w_int, A,B_MOB,C_MOB,D_MOB)
vm = ~np.isnan(zm.real); zmv = zm[vm] - nuc_z
print(f"  valid: {vm.sum()}/{interior.sum()}")

# ==================== 阶段3: 六向 / 四向 判定 ====================
SR3 = np.sqrt(3)
if FRACTAL == 'levy_diamond':
    # C6 hex tiling (same as Pascal)
    M = 6
    ANGLES = np.array([m*np.pi/3 - np.pi/6 for m in range(M)])
    coord_type = 'hex'
else:
    # C4 square tiling
    M = 4
    ANGLES = np.array([m*np.pi/2 for m in range(M)])
    coord_type = 'square'

RC = np.cos(-ANGLES); RS = np.sin(-ANGLES)
print(f"[3/5] {M}向判定 (coord={coord_type})...")

N_v = len(zmv)
best_mod = np.zeros(N_v, dtype=np.int16)
best_n = np.full(N_v, -1, dtype=np.int64)
best_pri = np.full(N_v, N_ROWS, dtype=np.float64)

for m in range(M):
    zr = zmv.real*RC[m] - zmv.imag*RS[m]
    zi = zmv.real*RS[m] + zmv.imag*RC[m]
    if coord_type == 'hex':
        zrs = zr/HEX_SCALE; zis = zi/HEX_SCALE
        nr = np.round(zrs + zis/SR3).astype(np.int64)
        kr = np.round(2*zis/SR3).astype(np.int64)
    else:  # square
        nr = np.round(zi/HEX_SCALE).astype(np.int64)
        kr = np.round(zr/HEX_SCALE).astype(np.int64)
    ne = nr % N_ROWS
    ke = kr % N_ROWS
    v = (ne >= 0) & (ne < N_ROWS) & (ke >= 0) & (ke < N_ROWS)
    if v.any():
        vi = np.where(v)[0]
        mv = pascal[ne[vi], ke[vi]]
        nz = mv > 0
        if nz.any():
            ui = vi[nz]; pr = ne[ui].astype(np.float64)
            bt = pr < best_pri[ui]
            if bt.any():
                bi = ui[bt]; best_mod[bi] = mv[nz][bt]
                best_n[bi] = ne[bi]; best_pri[bi] = pr[bt]

fill_pct = (best_mod > 0).mean() * 100
print(f"  fill={fill_pct:.1f}%")

# ==================== 阶段4: 着色 ====================
print("[4/5] 着色...")
img = np.zeros((H, W, 3))
SKY_BG = np.array([0.45, 0.75, 0.92])
img[escaped] = SKY_BG

mod_full = np.zeros(interior.sum(), dtype=np.int8)
n_full = np.full(interior.sum(), -1, dtype=np.int64)
mod_full[vm] = best_mod; n_full[vm] = best_n

ii = np.where(interior)
for i, (py, px) in enumerate(zip(ii[0], ii[1])):
    if mod_full[i] > 0:
        nv = n_full[i]
        hue = 0.12 - (nv / N_ROWS) * 0.65
        if hue < 0: hue += 1.0
        sat = 0.7 + 0.3 * (nv / N_ROWS)
        val = 0.5 + 0.5 * (1 - nv / N_ROWS)
        img[py, px] = h2r([[[hue, sat, val]]])[0, 0]
    else:
        img[py, px] = [0.30, 0.20, 0.08]

# 核点辉光
core_r = r_min + (r_max - r_min) * 0.05
cmask = dist_nuc < core_r
if cmask.any():
    fade = np.clip(1.0 - dist_nuc[cmask]/core_r, 0, 1)
    img[cmask] = img[cmask]*(1-fade[:,None]*0.6) + fade[:,None]*[0.98,0.96,0.88]

img = np.clip(img, 0, 1)

# ==================== 输出 ====================
DPI = 150
tag = 'levy_diamond' if FRACTAL == 'levy_diamond' else 'koch8'
out_png = os.path.join(od, f'UF22_{tag}_v15.png')
img_disp = np.transpose(img, (1, 0, 2))

fig, ax = plt.subplots(figsize=(10, 8), dpi=DPI)
ax.imshow(img_disp, origin='lower', interpolation='bilinear',
          extent=[I0, I1, R0, R1])
ax.set_aspect('equal')

CSV_PATH = os.path.join(
    r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M水滴CFD流体实验',
    'droplet_invM_analytic.csv')
csv_data = np.loadtxt(CSV_PATH, delimiter=',', skiprows=1)
ax.plot(csv_data[:,1], csv_data[:,0], color=[0.95, 0.72, 0.10],
        linewidth=1.0, alpha=0.85)

GOLD = '#D4A017'
for spine in ax.spines.values():
    spine.set_color(GOLD); spine.set_linewidth(2.5)
ax.set_xticks([]); ax.set_yticks([])
fig.patch.set_facecolor('black'); ax.set_facecolor('black')
plt.tight_layout(pad=0.5)
fig.savefig(out_png, dpi=DPI, facecolor='black', bbox_inches='tight')
plt.close()

elapsed = time.time() - t0
print(f"Done: {out_png} ({os.path.getsize(out_png)//1024}KB) {elapsed:.0f}s")
print(f"  D={D_VAL:.3f}  fill={fill_pct:.1f}%")
