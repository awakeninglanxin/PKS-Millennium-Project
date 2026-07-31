#!/usr/bin/env python
"""快速暴力测试3种Lévy龙形参数组合"""
import numpy as np, math, os, time
from collections import deque
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

od = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\22_图像映射'
SRC, DPI, BIG_N = 1200, 150, 2048

for label, depth, N_canvas, lw in [
    ('levy_dragon_S256_v15', 10, 256, 6),
    ('levy_dragon_S512_v15', 10, 512, 4),
    ('levy_dragon_D12_v15', 12, 512, 3),
]:
    t0 = time.time()
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
    sc = N_canvas * 0.40 / max(xmax-xmin, ymax-ymin, 1)
    cx, cy = (xmin+xmax)/2, (ymin+ymax)/2
    
    bnd = np.zeros((N_canvas, N_canvas), dtype=np.int16)
    for rot_deg in [0, 90, 180, 270]:
        cr = math.cos(-math.radians(rot_deg)); sr = math.sin(-math.radians(rot_deg))
        for i in range(len(pts)-1):
            x1=(pts[i,0]-cx)*sc;   y1=(pts[i,1]-cy)*sc
            x2=(pts[i+1,0]-cx)*sc; y2=(pts[i+1,1]-cy)*sc
            rx1 = x1*cr - y1*sr + N_canvas/2; ry1 = x1*sr + y1*cr + N_canvas/2
            rx2 = x2*cr - y2*sr + N_canvas/2; ry2 = x2*sr + y2*cr + N_canvas/2
            xi1, yi1 = int(rx1), int(ry1); xi2, yi2 = int(rx2), int(ry2)
            steps = max(abs(xi2-xi1), abs(yi2-yi1), 1)
            hw = lw // 2
            for t in range(steps+1):
                xi = xi1 + (xi2-xi1)*t//steps; yi = yi1 + (yi2-yi1)*t//steps
                for dx in range(-hw, hw+1):
                    for dy in range(-hw, hw+1):
                        nx, ny = xi+dx, yi+dy
                        if 0 <= nx < N_canvas and 0 <= ny < N_canvas:
                            bnd[ny, nx] = 1
    
    # Flood fill
    filled = bnd.copy(); visited = np.zeros((N_canvas,N_canvas), dtype=bool); rid = 0
    for y0 in range(N_canvas):
        for x0 in range(N_canvas):
            if filled[y0,x0] == 0 and not visited[y0,x0]:
                q = deque([(x0,y0)]); visited[y0,x0] = True; rp = []
                while q:
                    x,y = q.popleft(); rp.append((x,y))
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx,ny=x+dx,y+dy
                        if 0<=nx<N_canvas and 0<=ny<N_canvas and filled[ny,nx]==0 and not visited[ny,nx]:
                            visited[ny,nx] = True; q.append((nx,ny))
                if rid % 2 == 1:
                    for x,y in rp: filled[y,x] = 2
                rid += 1
    
    fill_native = (filled > 0).mean() * 100
    
    # Upsample
    big = np.zeros((BIG_N, BIG_N), dtype=np.int16)
    for y in range(N_canvas):
        for x in range(N_canvas):
            if filled[y, x] > 0:
                y0, y1 = y*BIG_N//N_canvas, (y+1)*BIG_N//N_canvas
                x0, x1 = x*BIG_N//N_canvas, (x+1)*BIG_N//N_canvas
                big[y0:y1, x0:x1] = filled[y, x]
    
    fill_big = (big > 0).mean() * 100
    off = (BIG_N - SRC) // 2
    src = big[off:off+SRC, off:off+SRC]
    rgb = np.ones((SRC, SRC, 3))
    rgb[src==1] = [0.12, 0.28, 0.42]
    rgb[src==2] = [0.92, 0.65, 0.10]
    rgb[src==0] = [0.96, 0.94, 0.88]
    
    out = os.path.join(od, f'UF22_{label}.png')
    fig, ax = plt.subplots(figsize=(SRC/DPI, SRC/DPI), dpi=DPI)
    ax.imshow(rgb, interpolation='bilinear'); ax.set_aspect('equal')
    ax.set_title(f'Levy N={N_canvas} d={depth} lw={lw} fill={fill_big:.1f}%', fontsize=11)
    ax.axis('off'); fig.tight_layout()
    fig.savefig(out, dpi=DPI, facecolor='white'); plt.close()
    print(f'{label}: canvas={N_canvas} fill_native={fill_native:.1f}% fill_big={fill_big:.1f}% {time.time()-t0:.1f}s')
