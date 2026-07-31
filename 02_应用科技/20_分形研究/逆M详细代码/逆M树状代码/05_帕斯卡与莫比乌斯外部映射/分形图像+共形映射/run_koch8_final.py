#!/usr/bin/env python
"""Koch-8 × 逆M — 最终版"""
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
print("=== Koch-8 D=1.5 × 逆M v16 ===")

# LUT
def sub(p1,p2,dp):
    if dp==0: return [(p1,p2)]
    x1,y1=p1; x2,y2=p2; dx,dy=(x2-x1)/4,(y2-y1)/4
    px,py=-dy*4,dx*4
    s1=(x1+dx,y1+dy); s2=(x1+2*dx,y1+2*dy); s3=(x1+3*dx,y1+3*dy)
    a=(s1[0]+px/4,s1[1]+py/4); b=(s2[0]+px/4,s2[1]+py/4)
    c=(s2[0]-px/4,s2[1]-py/4); d=(s3[0]-px/4,s3[1]-py/4)
    return(sub(p1,s1,dp-1)+sub(s1,a,dp-1)+sub(a,b,dp-1)+sub(b,s2,dp-1)+
           sub(s2,c,dp-1)+sub(c,d,dp-1)+sub(d,s3,dp-1)+sub(s3,p2,dp-1))

segs=sub((0.0,0.0),(1.0,0.0),4)
bnd=np.zeros((N_ROWS,N_ROWS),dtype=np.int16)
for(x1,y1),(x2,y2) in segs:
    xi1,yi1=int(x1*N_ROWS),int(y1*N_ROWS+N_ROWS/2)
    xi2,yi2=int(x2*N_ROWS),int(y2*N_ROWS+N_ROWS/2)
    steps=max(abs(xi2-xi1),abs(yi2-yi1),1)
    for t in range(steps+1):
        xi=xi1+(xi2-xi1)*t//steps; yi=yi1+(yi2-yi1)*t//steps
        for dx in range(-2,3):
            for dy in range(-2,3):
                nx,ny=xi+dx,yi+dy
                if 0<=nx<N_ROWS and 0<=ny<N_ROWS: bnd[ny,nx]=1

filled=bnd.copy(); visited=np.zeros((N_ROWS,N_ROWS),dtype=bool); rid=0
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
print(f"LUT fill={(pascal>0).mean()*100:.1f}% ({time.time()-t0:.1f}s)")

# 逆M
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

M=4; ANGLES=np.array([m*np.pi/2 for m in range(M)])
RC=np.cos(-ANGLES); RS=np.sin(-ANGLES)
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

# 着色
img=np.zeros((H,W,3))
img[escaped]=[0.45,0.75,0.92]
mf=np.zeros(interior.sum(),dtype=np.int8); nf=np.full(interior.sum(),-1,dtype=np.int64)
mf[vm]=best_mod; nf[vm]=best_n
ii=np.where(interior)
for i,(py,px) in enumerate(zip(ii[0],ii[1])):
    if mf[i]>0:
        nv=nf[i]; hue=0.12-(nv/N_ROWS)*0.65
        if hue<0: hue+=1.0
        sat=0.7+0.3*(nv/N_ROWS); val=0.5+0.5*(1-nv/N_ROWS)
        img[py,px]=h2r([[[hue,sat,val]]])[0,0]
    else: img[py,px]=[0.30,0.20,0.08]
img=np.clip(img,0,1)

# 输出
DPI=150; out=os.path.join(od,'UF22_koch8_v16_final.png')
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
print(f"Done: {out} ({os.path.getsize(out)//1024}KB) {time.time()-t0:.0f}s D=1.5 fill={fill_pct:.1f}%")
