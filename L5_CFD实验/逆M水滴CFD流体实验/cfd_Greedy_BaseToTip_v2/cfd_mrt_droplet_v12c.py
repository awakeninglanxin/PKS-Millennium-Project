#!/usr/bin/env python3
"""逆M水滴 LBM v12 — fp32 + 粗网格 + 高对比
v10 base, fixes: 300x180 grid, fp32, in-place collision, vivid color
"""
import os, math, time as tmod
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt; import matplotlib.animation as animation
from matplotlib.path import Path
import cupy as cp; import numpy as np

plt.rcParams['font.family'] = 'DejaVu Sans'; plt.rcParams['axes.unicode_minus'] = False
OUT_DIR = 'cfd_out'; os.makedirs(OUT_DIR, exist_ok=True)
CSV = np.loadtxt('droplet_invM_analytic.csv', delimiter=',', skiprows=1)

# ===== Params =====
SWAY_A = 0.03; SWAY_T = 600
NX, NY = 300, 180; u0 = 0.06; tau = 0.65; omega = 1.0/tau
scale = 110.0/5.333; cx0 = int(NX*0.22); cy0 = NY//2
Re = int(3*u0*110/(tau-0.5))
STEPS = 40000; SE = 100; FPS = 12

# D2Q9 fp32
D = cp.float32
w = cp.array([4/9,1/9,1/9,1/9,1/9,1/36,1/36,1/36,1/36], D)
cx = cp.array([0,1,0,-1,0,1,-1,-1,1], cp.int32)
cy = cp.array([0,0,1,0,-1,1,1,-1,-1], cp.int32)
opp = cp.array([0,3,4,1,2,7,8,5,6], cp.int32)

# Broadcast shapes for in-place collision: (1,1,9)
w1 = w.reshape(1,1,9); cx1 = cx.reshape(1,1,9).astype(D); cy1 = cy.reshape(1,1,9).astype(D)

# Mask
px=(CSV[:,0]*scale+cx0).astype(np.float64); py=(CSV[:,1]*scale+cy0).astype(np.float64)
xx,yy=np.meshgrid(np.arange(NX+2),np.arange(NY+2),indexing='ij')
mask=cp.asarray(Path(np.column_stack((px,py))).contains_points(
    np.column_stack((xx.ravel(),yy.ravel()))).reshape(NX+2,NY+2))
m1=mask[1:-1,1:-1]

# Init
f=cp.zeros((NX+2,NY+2,9),D)
for k in range(9): f[:,:,k]=w[k]
fnew=cp.zeros_like(f)
rho=cp.ones((NX+2,NY+2),D); ux=cp.zeros((NX+2,NY+2),D); uy=cp.zeros((NX+2,NY+2),D)
frames=[]; t0=tmod.time()

print(f'LBM v12b fp32 coarse  N={NX}x{NY}  Re~{Re}')
print(f'sway={SWAY_A}(half) T={SWAY_T} steps={STEPS} fps={FPS}')

for t in range(STEPS):
    # Collision: in-place vectorized (1,1,9) broadcast
    rho=cp.sum(f,2); de=rho+1e-10
    ux=(f[:,:,1]+f[:,:,5]+f[:,:,8]-f[:,:,3]-f[:,:,6]-f[:,:,7])/de
    uy=(f[:,:,2]+f[:,:,5]+f[:,:,6]-f[:,:,4]-f[:,:,7]-f[:,:,8])/de
    ux[mask]=0; uy[mask]=0

    cu=3.0*(cx1*ux[:,:,None]+cy1*uy[:,:,None])
    u2=ux*ux+uy*uy
    feq=w1*rho[:,:,None]*(1.0+cu+0.5*cu*cu-1.5*u2[:,:,None])
    f-=omega*(f-feq)

    # Streaming
    for k in range(9):
        fnew[:,:,k]=cp.roll(cp.roll(f[:,:,k],cx[k],0),cy[k],1)
    for k in range(9):
        fnew[mask,k]=cp.roll(cp.roll(f[:,:,opp[k]],cx[k],0),cy[k],1)[mask]
    f=fnew

    # Zou-He inflow
    jy=slice(2,NY); sw=2.0*math.pi*t/SWAY_T; uys=SWAY_A*math.sin(sw)
    f0i,f2i,f3i=f[1,jy,0],f[1,jy,2],f[1,jy,3]
    f4i,f6i,f7i=f[1,jy,4],f[1,jy,6],f[1,jy,7]
    ri=(f0i+f2i+f4i+2.0*(f3i+f6i+f7i))/(1.0-u0)
    f[1,jy,1]=f3i+(2.0/3.0)*ri*u0
    f[1,jy,5]=f7i-0.5*(f2i-f4i)+0.5*ri*uys+(1.0/6.0)*ri*u0
    f[1,jy,8]=f6i+0.5*(f2i-f4i)+0.5*ri*uys+(1.0/6.0)*ri*u0
    f[NX,jy,:]=f[NX-1,jy,:]

    if t%SE==0 or t==STEPS-1:
        vort=(cp.roll(uy,-1,0)-cp.roll(uy,1,0)-cp.roll(ux,-1,1)+cp.roll(ux,1,1))*0.5
        vort[mask]=0; frames.append(cp.asnumpy(vort[1:-1,1:-1]))
        if t%2000==0:
            et=tmod.time()-t0
            print(f'  t={t:>5d}  f={len(frames):>3d}  '
                  f'|v|={float(cp.max(cp.sqrt(ux**2+uy**2)*~mask)):.3f}  '
                  f'uy={uys:+.3f}  {et:.0f}s')

et=tmod.time()-t0
print(f'\nSim: {et:.0f}s  ~{et*1e6/STEPS:.0f}us/step  ~{et*1e3/STEPS:.1f}ms/step')

# Render - vivid color (lower vmax = higher saturation)
m1c=cp.asnumpy(m1)
print(f'Render {len(frames)} frames...')
fig,ax=plt.subplots(figsize=(10,5))
vm=abs(frames[-1]).max()*0.10
def av(i):
    ax.clear(); bg=np.zeros((NY,NX,4)); bg[m1c.T,:]=[0.15,0.18,0.22,1.0]
    ax.imshow(bg,extent=[0,NX,0,NY],origin='lower')
    ax.imshow(frames[i].T,cmap='RdBu_r',origin='lower',extent=[0,NX,0,NY],vmin=-vm,vmax=vm,alpha=0.95)
    ax.contour(m1c.T,levels=[0.5],colors='white',linewidths=1.5,extent=[0,NX,0,NY])
    tp=i*SE; sd=math.degrees(math.atan2(SWAY_A*math.sin(2*math.pi*tp/SWAY_T),u0))
    ax.arrow(7,NY/2,15*math.cos(math.radians(sd)),15*math.sin(math.radians(sd)),
             head_width=4,head_length=5,fc='cyan',ec='cyan',lw=2.5,zorder=10)
    ax.set_title(f'Inverse-M Droplet v12c Re~{Re} t={tp} [sway x1.8 12fps]',fontsize=12,fontweight='bold')
    ax.set_xlim(0,NX); ax.set_ylim(0,NY)
ani=animation.FuncAnimation(fig,av,frames=len(frames),interval=80)
g1=os.path.join(OUT_DIR,'droplet_v12c_vorticity.gif')
ani.save(g1,writer='pillow',fps=FPS,dpi=80); plt.close(fig)
print(f'OK {g1} ({os.path.getsize(g1)//1024}KB)')

fig2,ax2=plt.subplots(figsize=(10,5))
vm2=abs(frames[-1]).max()*0.08
def av2(i):
    ax2.clear(); bg=np.zeros((NY,NX,4)); bg[m1c.T,:]=[0.10,0.13,0.18,1.0]
    ax2.imshow(bg,extent=[0,NX,0,NY],origin='lower')
    ax2.imshow(frames[i].T,cmap='coolwarm',origin='lower',extent=[0,NX,0,NY],vmin=-vm2,vmax=vm2,alpha=0.95)
    ax2.contour(m1c.T,levels=[0.5],colors='#ffcc44',linewidths=1.2,extent=[0,NX,0,NY])
    tp=i*SE; sd2=math.degrees(math.atan2(SWAY_A*math.sin(2*math.pi*tp/SWAY_T),u0))
    ax2.arrow(7,NY/2,15*math.cos(math.radians(sd2)),15*math.sin(math.radians(sd2)),
              head_width=4,head_length=5,fc='#ff44aa',ec='#ff44aa',lw=2.5,zorder=10)
    ax2.set_title(f'Inverse-M Vortex v12c Re~{Re} f={i} [sway x1.8 12fps]',fontsize=12)
    ax2.set_xlim(0,NX); ax2.set_ylim(0,NY)
ani2=animation.FuncAnimation(fig2,av2,frames=len(frames),interval=80)
g2=os.path.join(OUT_DIR,'droplet_v12c_vortex.gif')
ani2.save(g2,writer='pillow',fps=FPS,dpi=80); plt.close(fig2)
print(f'OK {g2} ({os.path.getsize(g2)//1024}KB)')
print('\nDone v12!')
