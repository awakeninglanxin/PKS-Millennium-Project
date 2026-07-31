#!/usr/bin/env python
"""v16: 4色Lévy龙形 × 逆M — 归一化共形映射"""
import numpy as np, math, os, time
from collections import deque
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb as h2r

plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False
od=os.path.dirname(os.path.abspath(__file__))

DEPTH=14; N_ROWS=2048; W,H=2400,2025
MAX_ITER=300; ESCAPE_RADIUS=50.0
TIP=4.0; BOTTOM=-4/3; HSP=1.6242719100; EXPAND=4.0
R0,R1=BOTTOM-EXPAND,TIP+EXPAND; I0,I1=-HSP-EXPAND,HSP+EXPAND

t0=time.time()
print(f"=== Lévy 8-dragon ±mirror D={DEPTH} × 逆M v16 ===")

# ====== LUT: 8条龙, 每边正反双旋 ======
def levy_path(sx,sy,angle_deg,depth,mirror=False):
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

S=10
configs=[
    ( S, 0, 180, False),( S, 0, 180, True),
    ( 0, S, 270, False),( 0, S, 270, True),
    (-S, 0, 0, False),  (-S, 0, 0, True),
    ( 0,-S, 90, False), ( 0,-S, 90, True),
]
paths=[levy_path(x,y,a,DEPTH,m) for x,y,a,m in configs]
all_pts=np.vstack(paths)
xmin,xmax=all_pts[:,0].min(),all_pts[:,0].max()
ymin,ymax=all_pts[:,1].min(),all_pts[:,1].max()
sc=N_ROWS*0.47/max(xmax-xmin,ymax-ymin,1)
cx,cy=(xmin+xmax)/2,(ymin+ymax)/2

# 8色 LUT: mod 1-8
pascal=np.zeros((N_ROWS,N_ROWS),dtype=np.int16)
for pi,pts in enumerate(paths):
    mod_val=pi+1
    for i in range(len(pts)-1):
        x1=(pts[i,0]-cx)*sc+N_ROWS/2; y1=(pts[i,1]-cy)*sc+N_ROWS/2
        x2=(pts[i+1,0]-cx)*sc+N_ROWS/2; y2=(pts[i+1,1]-cy)*sc+N_ROWS/2
        xi1,yi1=int(x1),int(y1); xi2,yi2=int(x2),int(y2)
        steps=max(abs(xi2-xi1),abs(yi2-yi1),1)
        for s in range(steps+1):
            xi=xi1+(xi2-xi1)*s//steps; yi=yi1+(yi2-yi1)*s//steps
            for dx in range(-1,2):
                for dy in range(-1,2):
                    nx,ny=xi+dx,yi+dy
                    if 0<=nx<N_ROWS and 0<=ny<N_ROWS:
                        pascal[ny,nx]=mod_val

lut_fill=(pascal>0).mean()*100
print(f"LUT fill={lut_fill:.1f}% ({time.time()-t0:.1f}s)")

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

def mob(z,a,b,c,d):
    num=a*z+b; den=c*z+d; sf=np.abs(den)>1e-12
    r=np.full(z.shape,np.nan+1j*np.nan,dtype=np.complex128)
    r[sf]=num[sf]/den[sf]; return r

w_int=w_grid[interior]
# 映射: f = ±1/w — 正负双分支
zm = np.zeros_like(w_int, dtype=np.complex128)
den_ok = np.abs(w_int) > 1e-12
zm[den_ok] = 1.0/w_int[den_ok]
vm = np.isfinite(zm.real) & np.isfinite(zm.imag)
zmv=zm[vm]
nuc_px=N_ROWS//2  # 核点对应LUT中心

# 归一化映射 + C4 query
M=2; ANGLES=np.array([m*np.pi/2 for m in range(M)])
RC=np.cos(-ANGLES); RS=np.sin(-ANGLES)

zr_min,zr_max=zmv.real.min(),zmv.real.max()
zi_min,zi_max=zmv.imag.min(),zmv.imag.max()
zr_span=max(zr_max-zr_min,1e-12); zi_span=max(zi_max-zi_min,1e-12)
print(f"  zmv range: re[{zr_min:.1f},{zr_max:.1f}] im[{zi_min:.1f},{zi_max:.1f}]")

N_v=len(zmv)
best_mod=np.zeros(N_v,dtype=np.int16); best_n=np.full(N_v,-1,dtype=np.int64)
best_pri=np.full(N_v,N_ROWS,dtype=np.float64)

for m in range(M):
    zr=zmv.real*RC[m]-zmv.imag*RS[m]; zi=zmv.real*RS[m]+zmv.imag*RC[m]
    for sgn in (1.0, -1.0):  # ± 双分支
        zrs=sgn*zr; zis=sgn*zi
        nr=(np.round((zis-zi_min)/zi_span*(N_ROWS-1)).astype(np.int64))%N_ROWS
        kr=(np.round((zrs-zr_min)/zr_span*(N_ROWS-1)).astype(np.int64))%N_ROWS
        ne=nr%N_ROWS; ke=kr%N_ROWS
        v=(ne>=0)&(ne<N_ROWS)&(ke>=0)&(ke<N_ROWS)
        if v.any():
            vi=np.where(v)[0]; mv=pascal[ne[vi],ke[vi]]; nz=mv>0
            if nz.any():
                ui=vi[nz]; pr=ne[ui].astype(np.float64); bt=pr<best_pri[ui]
                if bt.any():
                    bi=ui[bt]; best_mod[bi]=mv[nz][bt]; best_n[bi]=ne[bi]; best_pri[bi]=pr[bt]

fill_pct=(best_mod>0).mean()*100
print(f"fill={fill_pct:.1f}% interior={interior.sum()/(W*H)*100:.1f}%")

# ====== 着色: 统一金白cmap (8龙无差别, 中心金→边缘白) ======
GOLD=np.array([0.95,0.72,0.10]); WHITE=np.array([1.0,1.0,1.0])
img=np.zeros((H,W,3))
img[escaped]=[0.45,0.75,0.92]

mf=np.zeros(interior.sum(),dtype=np.int8); nf=np.full(interior.sum(),-1,dtype=np.int64)
mf[vm]=best_mod; nf[vm]=best_n
ii=np.where(interior)
for i,(py,px) in enumerate(zip(ii[0],ii[1])):
    mv=mf[i]; nv=nf[i]
    if mv>0:
        t=nv/N_ROWS  # 0=中心, 1=边缘
        img[py,px]=GOLD*(1-t)+WHITE*t
    else:
        img[py,px]=[0.30,0.20,0.08]

img=np.clip(img,0,1)

# ====== 输出 ======
DPI=150; out=os.path.join(od,f'UF22_levy_4color_D{DEPTH}_v16.png')
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
print(f"Done: {out} ({os.path.getsize(out)//1024}KB) {time.time()-t0:.0f}s fill={fill_pct:.1f}%")
