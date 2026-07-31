#!/usr/bin/env python
"""v16: Heighway Dragon 4-copy × 逆M — 八边形花毯纹理"""
import numpy as np, math, os, time
from collections import deque
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb as h2r

plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False
od=os.path.dirname(os.path.abspath(__file__))

N_ROWS=2048; HEX_SCALE=0.002; W,H=2400,2025
MAX_ITER=300; ESCAPE_RADIUS=50.0
TIP=4.0; BOTTOM=-4/3; HSP=1.6242719100; EXPAND=4.0
R0,R1=BOTTOM-EXPAND,TIP+EXPAND; I0,I1=-HSP-EXPAND,HSP+EXPAND

t0=time.time()
print("=== Heighway Dragon 4色 × 逆M v16 ===")

# ====== LUT: Heighway Dragon 4 copies from center, 90° ======
DEPTH=10; D_VAL=math.log(2)/math.log(math.sqrt(2))
N_ROWS=2048; HEX_SCALE=0.004  # D=2
print(f"Depth={DEPTH} D={D_VAL:.3f}")

# 1. Generate Heighway dragon turns
# sequence[0]=1=left(90°), 0=right(90°)
seq = [1]
for _ in range(DEPTH-1):
    rev_comp = [1-x for x in reversed(seq)]
    seq = seq + [1] + rev_comp

# 2. Follow turns from origin → path coordinates
sx, sy = 0.0, 0.0
pts_one = [(0.0, 0.0)]
angle = 0  # 0=east, 1=north, 2=west, 3=south (90° steps)
for turn in seq:
    if turn == 1: angle = (angle + 1) % 4  # left 90°
    else:         angle = (angle - 1) % 4  # right 90°
    dx, dy = [(1,0),(0,1),(-1,0),(0,-1)][angle]
    sx += dx; sy += dy
    pts_one.append((sx, sy))
pts_one = np.array(pts_one)

# 3. Scale to canvas
xmin,xmax=pts_one[:,0].min(),pts_one[:,0].max()
ymin,ymax=pts_one[:,1].min(),pts_one[:,1].max()
span=max(xmax-xmin, ymax-ymin, 1)
sc = N_ROWS * 0.48 / span
cx,cy=(xmin+xmax)/2,(ymin+ymax)/2

# 4. Draw 4 copies in different mod values (1,2,3,4 = colors)
bnd = np.zeros((N_ROWS, N_ROWS), dtype=np.int16)
for copy_idx, rot_deg in enumerate([0, 90, 180, 270]):
    mod_val = copy_idx + 1  # 1=blue,2=green,3=red,4=orange
    cr = math.cos(-math.radians(rot_deg))
    sr = math.sin(-math.radians(rot_deg))
    for i in range(len(pts_one)-1):
        x1=(pts_one[i,0]-cx)*sc;   y1=(pts_one[i,1]-cy)*sc
        x2=(pts_one[i+1,0]-cx)*sc; y2=(pts_one[i+1,1]-cy)*sc
        rx1=x1*cr-y1*sr+N_ROWS/2; ry1=x1*sr+y1*cr+N_ROWS/2
        rx2=x2*cr-y2*sr+N_ROWS/2; ry2=x2*sr+y2*cr+N_ROWS/2
        xi1,yi1=int(rx1),int(ry1); xi2,yi2=int(rx2),int(ry2)
        steps=max(abs(xi2-xi1),abs(yi2-yi1),1)
        for t in range(steps+1):
            xi=xi1+(xi2-xi1)*t//steps; yi=yi1+(yi2-yi1)*t//steps
            for dx in range(-4,5):
                for dy in range(-4,5):
                    nx,ny=xi+dx,yi+dy
                    if 0<=nx<N_ROWS and 0<=ny<N_ROWS:
                        bnd[ny,nx]=mod_val

# Flood fill: regions between curves
filled=bnd.copy()
visited=np.zeros((N_ROWS,N_ROWS),dtype=bool); rid=0
for y0 in range(0,N_ROWS,2):
    for x0 in range(0,N_ROWS,2):
        if filled[y0,x0]==0 and not visited[y0,x0]:
            q=deque([(x0,y0)]); visited[y0,x0]=True; rp=[]
            while q:
                x,y=q.popleft(); rp.append((x,y))
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<N_ROWS and 0<=ny<N_ROWS and filled[ny,nx]==0 and not visited[ny,nx]:
                        visited[ny,nx]=True; q.append((nx,ny))
            if rid%2==1:
                for x,y in rp: filled[y,x]=2
            rid+=1
pascal=filled
lut_fill=(pascal>0).mean()*100
print(f"LUT fill={lut_fill:.1f}% (mods 1-4=curve, mod2=fill) time={time.time()-t0:.1f}s")

# ====== 逆M ======
xs,ys=np.linspace(R0,R1,W),np.linspace(I0,I1,H)
X,Y=np.meshgrid(xs,ys); w_grid=X+1j*Y
ce=np.zeros_like(w_grid,dtype=np.complex128)
sf=np.abs(w_grid)>1e-12; ce[sf]=1.0/w_grid[sf]; ce[~sf]=1e6
Z_iter=np.zeros_like(ce); it=np.full(ce.shape,-1,dtype=np.int32)
for i in range(MAX_ITER):
    act=it==-1
    if not np.any(act): break
    Z_iter[act]=Z_iter[act]**2+ce[act]
    esc=act&(np.abs(Z_iter)>ESCAPE_RADIUS); it[esc]=i
it[it==-1]=MAX_ITER
interior=it==MAX_ITER; escaped=~interior
print(f"interior={interior.sum()/(W*H)*100:.1f}%")

def mob(z,a,b,c,d):
    num=a*z+b; den=c*z+d; sf=np.abs(den)>1e-12
    r=np.full(z.shape,np.nan+1j*np.nan,dtype=np.complex128)
    r[sf]=num[sf]/den[sf]; return r

w_int=w_grid[interior]; zm=mob(w_int,1+0j,0+0j,1+0j,-2+0j)
vm=~np.isnan(zm.real); zmv=zm[vm]

# C4 query
M=4; ANGLES=np.array([m*np.pi/2 for m in range(M)])
RC=np.cos(-ANGLES); RS=np.sin(-ANGLES)
# Debug: what range do nr/kr cover?
nr_test = np.round(zmv.real[:10000]/HEX_SCALE).astype(np.int64)
print(f"  zmv range: re=[{zmv.real.min():.1f},{zmv.real.max():.1f}] im=[{zmv.imag.min():.1f},{zmv.imag.max():.1f}]")
print(f"  nr range: [{nr_test.min()},{nr_test.max()}] unique={len(np.unique(nr_test%N_ROWS))}/{N_ROWS}")

N_v=len(zmv)
best_mod=np.zeros(N_v,dtype=np.int16); best_n=np.full(N_v,-1,dtype=np.int64)
best_pri=np.full(N_v,N_ROWS,dtype=np.float64)

for m in range(M):
    zr=zmv.real*RC[m]-zmv.imag*RS[m]; zi=zmv.real*RS[m]+zmv.imag*RC[m]
    nr=np.round(zi/HEX_SCALE).astype(np.int64); kr=np.round(zr/HEX_SCALE).astype(np.int64)
    ne=nr%N_ROWS; ke=kr%N_ROWS
    v=(ne>=0)&(ne<N_ROWS)&(ke>=0)&(ke<N_ROWS)
    if v.any():
        vi=np.where(v)[0]; mv=pascal[ne[vi],ke[vi]]; nz=mv>0
        if nz.any():
            ui=vi[nz]; pr=ne[ui].astype(np.float64); bt=pr<best_pri[ui]
            if bt.any():
                bi=ui[bt]; best_mod[bi]=mv[nz][bt]; best_n[bi]=ne[bi]; best_pri[bi]=pr[bt]

fill_pct=(best_mod>0).mean()*100
print(f"fill={fill_pct:.1f}%")

# ====== 着色 (多mod色 = 4色分块) ======
img=np.zeros((H,W,3))
img[escaped]=[0.45,0.75,0.92]

COLORS = {
    1: [0.10, 0.40, 0.75],  # blue
    2: [0.15, 0.65, 0.30],  # green
    3: [0.85, 0.25, 0.20],  # red
    4: [0.95, 0.60, 0.10],  # orange
}
mf=np.zeros(interior.sum(),dtype=np.int8)
mf[vm]=best_mod
ii=np.where(interior)
for i,(py,px) in enumerate(zip(ii[0],ii[1])):
    mv=mf[i]
    if 1<=mv<=4: img[py,px]=COLORS[mv]
    elif mv==2:  img[py,px]=[0.85,0.75,0.40]  # fill gold
    else:        img[py,px]=[0.30,0.20,0.08]

img=np.clip(img,0,1)

# ====== 输出 ======
DPI=150; out=os.path.join(od,'UF22_heighway_dragon_v16.png')
img_disp=np.transpose(img,(1,0,2))
fig,ax=plt.subplots(figsize=(10,8),dpi=DPI)
ax.imshow(img_disp,origin='lower',interpolation='bilinear',extent=[I0,I1,R0,R1])
ax.set_aspect('equal')
csv=np.loadtxt(r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M水滴CFD流体实验\droplet_invM_analytic.csv',delimiter=',',skiprows=1)
ax.plot(csv[:,1],csv[:,0],color=[0.95,0.72,0.10],linewidth=1.0,alpha=0.85)
for s in ax.spines.values(): s.set_color('#D4A017'); s.set_linewidth(2.5)
ax.set_xticks([]); ax.set_yticks([])
fig.patch.set_facecolor('black'); ax.set_facecolor('black')
plt.tight_layout(pad=0.5)
fig.savefig(out,dpi=DPI,facecolor='black',bbox_inches='tight'); plt.close()

elapsed=time.time()-t0
print(f"Done: {out} ({os.path.getsize(out)//1024}KB) {elapsed:.0f}s D=2 fill={fill_pct:.1f}%")
