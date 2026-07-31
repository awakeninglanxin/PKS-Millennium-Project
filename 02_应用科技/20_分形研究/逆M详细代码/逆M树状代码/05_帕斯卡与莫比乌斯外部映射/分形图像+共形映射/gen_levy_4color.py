#!/usr/bin/env python
"""Lévy 8-dragon 8向对称源图 — 每边正反双旋"""
import numpy as np, math, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

od = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\22_图像映射'
DEPTH=13; N=2048; SRC=1200; DPI=150

def levy_path(sx,sy,angle_deg,depth, mirror=False):
    rule={'F':'+F--F+'}; s='F'
    for _ in range(depth):
        ns=''
        for c in s: ns+=rule.get(c,c)
        s=ns
    if mirror: s=s.replace('+','T').replace('-','+').replace('T','-')
    angle=int(angle_deg/45)%8; pts=[(sx,sy)]
    for c in s:
        if c=='F':
            a=angle*math.pi/4; sx+=math.cos(a); sy+=math.sin(a)
            pts.append((sx,sy))
        elif c=='+': angle=(angle+1)%8
        elif c=='-': angle=(angle-1)%8
    return np.array(pts)

# 四边中点 × 正反双旋 = 8条龙
S=10
configs=[
    ( S, 0, 180, False),( S, 0, 180, True),
    ( 0, S, 270, False),( 0, S, 270, True),
    (-S, 0, 0, False),  (-S, 0, 0, True),
    ( 0,-S, 90, False), ( 0,-S, 90, True),
]
# 8色: 4对互补色 (正旋深, 反旋浅)
colors8=[
    (0.08,0.38,0.72),(0.30,0.58,0.85),  # 蓝
    (0.12,0.55,0.25),(0.35,0.72,0.45),  # 绿
    (0.78,0.20,0.15),(0.92,0.45,0.35),  # 红
    (0.88,0.52,0.08),(0.97,0.72,0.30),  # 橙
]

paths_raw=[levy_path(x,y,a,DEPTH,m) for x,y,a,m in configs]
all_pts=np.vstack(paths_raw)
xmin,xmax=all_pts[:,0].min(),all_pts[:,0].max()
ymin,ymax=all_pts[:,1].min(),all_pts[:,1].max()
sc=N*0.47/max(xmax-xmin,ymax-ymin,1)
cx,cy=(xmin+xmax)/2,(ymin+ymax)/2

canvas=np.ones((N,N,3))
for pi,pts in enumerate(paths_raw):
    base=np.array(colors8[pi]); dark=base*0.3
    total=len(pts)-1
    for i in range(total):
        t=i/total; bright=1.0-t*0.6
        col=base*bright+(1-bright)*dark
        x1=(pts[i,0]-cx)*sc+N/2; y1=(pts[i,1]-cy)*sc+N/2
        x2=(pts[i+1,0]-cx)*sc+N/2; y2=(pts[i+1,1]-cy)*sc+N/2
        xi1,yi1=int(x1),int(y1); xi2,yi2=int(x2),int(y2)
        steps=max(abs(xi2-xi1),abs(yi2-yi1),1)
        for s in range(steps+1):
            xi=xi1+(xi2-xi1)*s//steps; yi=yi1+(yi2-yi1)*s//steps
            for dx in range(-1,2):
                for dy in range(-1,2):
                    nx,ny=xi+dx,yi+dy
                    if 0<=nx<N and 0<=ny<N: canvas[ny,nx]=col

canvas=np.clip(canvas,0,1)
off=(N-SRC)//2; src=canvas[off:off+SRC,off:off+SRC]

out=os.path.join(od,f'UF22_levy_8dragon_D{DEPTH}_源图_v16.png')
fig,ax=plt.subplots(figsize=(SRC/DPI,SRC/DPI),dpi=DPI)
ax.imshow(src,interpolation='bilinear'); ax.set_aspect('equal')
ax.set_title(f'Levy 8-Dragon depth={DEPTH} ±mirror',fontsize=11)
ax.axis('off'); fig.tight_layout()
fig.savefig(out,dpi=DPI,facecolor='white'); plt.close()

dark=(src.max(axis=2)<0.95).mean()*100
print(f'Done: {out} fill={dark:.1f}% ({os.path.getsize(out)//1024}KB)')
