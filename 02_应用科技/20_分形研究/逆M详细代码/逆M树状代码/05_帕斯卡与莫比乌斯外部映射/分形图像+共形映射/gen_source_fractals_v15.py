#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速生成 Koch-8 / Lévy钻石 平铺源图 (类似 UF22_六向帕斯卡源图_v12_p15.png)"""
import numpy as np, math, os, time
from collections import deque
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

od = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\22_图像映射'
SRC, N, DPI = 1200, 2048, 150

# ==================== Koch-8 LUT ====================
def make_koch8(depth=4):
    t0 = time.time()
    def subdivide(p1, p2, dp):
        if dp == 0: return [(p1, p2)]
        x1,y1=p1; x2,y2=p2; dx,dy=(x2-x1)/4,(y2-y1)/4
        px,py=-dy*4,dx*4
        s1=(x1+dx,y1+dy); s2=(x1+2*dx,y1+2*dy); s3=(x1+3*dx,y1+3*dy)
        a=(s1[0]+px/4,s1[1]+py/4); b=(s2[0]+px/4,s2[1]+py/4)
        c=(s2[0]-px/4,s2[1]-py/4); dd=(s3[0]-px/4,s3[1]-py/4)
        return (subdivide(p1,s1,dp-1) + subdivide(s1,a,dp-1) + subdivide(a,b,dp-1) +
                subdivide(b,s2,dp-1) + subdivide(s2,c,dp-1) + subdivide(c,dd,dp-1) +
                subdivide(dd,s3,dp-1) + subdivide(s3,p2,dp-1))
    segs = subdivide((0.0,0.0),(1.0,0.0), depth)
    # Draw boundary
    bnd = np.zeros((N,N), dtype=np.int16)
    for (x1,y1),(x2,y2) in segs:
        xi1,yi1=int(x1*N),int(y1*N+N/2); xi2,yi2=int(x2*N),int(y2*N+N/2)
        steps=max(abs(xi2-xi1),abs(yi2-yi1),1)
        for t in range(steps+1):
            xi=xi1+(xi2-xi1)*t//steps; yi=yi1+(yi2-yi1)*t//steps
            for dx in range(-2,3):
                for dy in range(-2,3):
                    nx,ny=xi+dx,yi+dy
                    if 0<=nx<N and 0<=ny<N: bnd[ny,nx]=1
    # Flood fill alternating
    filled=bnd.copy(); visited=np.zeros((N,N),dtype=bool); rid=0
    for y0 in range(N):
        for x0 in range(N):
            if filled[y0,x0]==0 and not visited[y0,x0]:
                q=deque([(x0,y0)]); visited[y0,x0]=True; rp=[]
                while q:
                    x,y=q.popleft(); rp.append((x,y))
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx,ny=x+dx,y+dy
                        if 0<=nx<N and 0<=ny<N and filled[ny,nx]==0 and not visited[ny,nx]:
                            visited[ny,nx]=True; q.append((nx,ny))
                if rid%2==1:
                    for x,y in rp: filled[y,x]=2
                rid+=1
    print(f'  Koch-8 LUT: fill={(filled>0).mean()*100:.1f}% ({time.time()-t0:.1f}s)')
    return filled

# ==================== Lévy Dragon 4拼花毯 (canvas=512, 图6.4.6~7) ====================
def make_levy_dragon(depth=12):
    t0 = time.time()
    N_CANVAS = 512  # 小画布→粗纹理
    
    turns = []
    for _ in range(depth):
        turns = turns + [1] + [-t for t in reversed(turns)]
    
    sx, sy = 0.0, 0.0; pts = [(0.0, 0.0)]; angle = 0
    for t in turns:
        angle = (angle + t) % 8
        a_rad = angle * math.pi / 4.0
        sx += math.cos(a_rad); sy += math.sin(a_rad)
        pts.append((sx, sy))
    pts = np.array(pts)
    
    xmin, xmax = pts[:,0].min(), pts[:,0].max()
    ymin, ymax = pts[:,1].min(), pts[:,1].max()
    span = max(xmax-xmin, ymax-ymin, 1)
    sc = N_CANVAS * 0.38 / span
    cx, cy = (xmin+xmax)/2, (ymin+ymax)/2
    
    bnd = np.zeros((N_CANVAS, N_CANVAS), dtype=np.int16)
    for rot_deg in [0, 90, 180, 270]:
        cr = math.cos(-math.radians(rot_deg)); sr = math.sin(-math.radians(rot_deg))
        for i in range(len(pts)-1):
            x1=(pts[i,0]-cx)*sc;   y1=(pts[i,1]-cy)*sc
            x2=(pts[i+1,0]-cx)*sc; y2=(pts[i+1,1]-cy)*sc
            rx1 = x1*cr - y1*sr + N_CANVAS/2; ry1 = x1*sr + y1*cr + N_CANVAS/2
            rx2 = x2*cr - y2*sr + N_CANVAS/2; ry2 = x2*sr + y2*cr + N_CANVAS/2
            xi1, yi1 = int(rx1), int(ry1); xi2, yi2 = int(rx2), int(ry2)
            steps = max(abs(xi2-xi1), abs(yi2-yi1), 1)
            for t in range(steps+1):
                xi = xi1 + (xi2-xi1)*t//steps; yi = yi1 + (yi2-yi1)*t//steps
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nx, ny = xi+dx, yi+dy
                        if 0 <= nx < N_CANVAS and 0 <= ny < N_CANVAS:
                            bnd[ny, nx] = 1
    
    # Flood fill alternating
    filled = bnd.copy(); visited = np.zeros((N_CANVAS,N_CANVAS), dtype=bool); rid = 0
    for y0 in range(N_CANVAS):
        for x0 in range(N_CANVAS):
            if filled[y0,x0] == 0 and not visited[y0,x0]:
                q = deque([(x0,y0)]); visited[y0,x0] = True; rp = []
                while q:
                    x,y = q.popleft(); rp.append((x,y))
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx,ny=x+dx,y+dy
                        if 0<=nx<N_CANVAS and 0<=ny<N_CANVAS and filled[ny,nx]==0 and not visited[ny,nx]:
                            visited[ny,nx] = True; q.append((nx,ny))
                if rid % 2 == 1:
                    for x,y in rp: filled[y,x] = 2
                rid += 1
    
    # Upsample to N (2048) for compatibility
    big = np.zeros((N, N), dtype=np.int16)
    for y in range(N_CANVAS):
        for x in range(N_CANVAS):
            if filled[y, x] > 0:
                y0, y1 = y*N//N_CANVAS, (y+1)*N//N_CANVAS
                x0, x1 = x*N//N_CANVAS, (x+1)*N//N_CANVAS
                big[y0:y1, x0:x1] = filled[y, x]
    
    print(f'  Lévy Dragon 4拼: fill={(big>0).mean()*100:.1f}% ({time.time()-t0:.1f}s)')
    return big

# ==================== 生成 + 渲染源图 ====================
for name, lut_func, desc in [
    ('koch8_源图_v15', lambda: make_koch8(4), 'Koch-8段 D=1.5 depth=4'),
    ('levy_dragon_源图_v15', lambda: make_levy_dragon(12), 'Levy龙形4拼花毯 D=2 depth=12'),
]:
    print(f'\n=== {desc} ===')
    lut = lut_func()
    
    # Crop to SRC×SRC center
    off = (N - SRC) // 2
    src = lut[off:off+SRC, off:off+SRC]
    
    # Colorize
    rgb = np.ones((SRC, SRC, 3))
    rgb[src==1] = [0.12, 0.28, 0.42]  # boundary: dark blue
    rgb[src==2] = [0.92, 0.65, 0.10]  # filled: gold
    rgb[src==0] = [0.96, 0.94, 0.88]  # empty: cream
    
    out = os.path.join(od, f'UF22_{name}.png')
    fig, ax = plt.subplots(figsize=(SRC/DPI, SRC/DPI), dpi=DPI)
    ax.imshow(rgb, interpolation='bilinear')
    ax.set_aspect('equal')
    ax.set_title(f'{desc} | fill={(src>0).mean()*100:.1f}%', fontsize=11)
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, facecolor='white')
    plt.close()
    print(f'  → {out} ({os.path.getsize(out)//1024}KB)')
