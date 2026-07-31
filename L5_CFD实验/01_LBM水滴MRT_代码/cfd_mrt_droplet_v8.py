#!/usr/bin/env python3
"""逆M水滴 LBM v8Lite — 小网格快速出片, RdBu_r涡量伪彩色"""
import numpy as np, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path

plt.rcParams['font.sans-serif'] = ['SimHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

THIS_DIR = r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验'
CSV = np.loadtxt(os.path.join(THIS_DIR,'droplet_invM_analytic.csv'),delimiter=',',skiprows=1)

# D2Q9
w=np.array([4/9,1/9,1/9,1/9,1/9,1/36,1/36,1/36,1/36])
cx=np.array([0,1,0,-1,0,1,-1,-1,1],np.int32); cy=np.array([0,0,1,0,-1,1,1,-1,-1],np.int32)
opp=np.array([0,3,4,1,2,7,8,5,6],np.int32)

def load_mask(NX,NY,scale,cx0,cy0):
    px=(CSV[:,0]*scale+cx0).astype(np.float64); py=(CSV[:,1]*scale+cy0).astype(np.float64)
    xx,yy=np.meshgrid(np.arange(NX+2),np.arange(NY+2),indexing='ij')
    return Path(np.column_stack((px,py))).contains_points(
        np.column_stack((xx.ravel(),yy.ravel()))).reshape(NX+2,NY+2)

NX,NY=350,175; u0=0.04; tau=0.60; omega=1.0/tau
scale=125.0/5.333; cx0=int(NX*0.22); cy0=NY//2; D_est=125
Re_est=3*u0*D_est/(tau-0.5)
STEPS=4000; SAVE_EVERY=25

OUT_DIR=os.path.join(THIS_DIR,'cfd_Greedy_BaseToTip_v2'); os.makedirs(OUT_DIR,exist_ok=True)
print(f'N={NX}×{NY} u0={u0} τ={tau} Re≈{Re_est:.0f} frames={STEPS//SAVE_EVERY}')

mask=load_mask(NX,NY,scale,cx0,cy0); mask1=mask[1:-1,1:-1]
f=np.zeros((NX+2,NY+2,9))
for k in range(9): f[:,:,k]=w[k]
rho=np.ones((NX+2,NY+2)); ux=np.zeros((NX+2,NY+2)); uy=np.zeros((NX+2,NY+2))
frames=[]

for t in range(STEPS):
    rho=np.sum(f,2); de=rho+1e-10
    ux=(f[:,:,1]+f[:,:,5]+f[:,:,8]-f[:,:,3]-f[:,:,6]-f[:,:,7])/de
    uy=(f[:,:,2]+f[:,:,5]+f[:,:,6]-f[:,:,4]-f[:,:,7]-f[:,:,8])/de
    ux[mask]=0; uy[mask]=0

    ux2=ux**2; uy2=uy**2; u2=ux2+uy2
    for k in range(9):
        cu=3*(cx[k]*ux+cy[k]*uy)
        f[:,:,k]-=omega*(f[:,:,k]-w[k]*rho*(1+cu+0.5*cu*cu-1.5*u2))

    fb=np.zeros_like(f)
    for k in range(9): fb[:,:,k]=np.roll(np.roll(f[:,:,k],-cx[k],0),-cy[k],1)
    for k in range(9): f[:,:,k]=np.roll(np.roll(f[:,:,k],cx[k],0),cy[k],1)
    for k in range(9): f[mask,k]=fb[mask,opp[k]]

    jy=np.arange(2,NY)
    rho[1,jy]=(f[1,jy,0]+f[1,jy,2]+f[1,jy,4]+2*(f[1,jy,3]+f[1,jy,6]+f[1,jy,7]))/(1-u0)
    f[1,jy,1]=f[1,jy,3]+2*w[1]*rho[1,jy]*u0
    f[1,jy,5]=f[1,jy,7]-0.5*(f[1,jy,2]-f[1,jy,4])+0.5*(f[1,jy,1]+f[1,jy,3])
    f[1,jy,8]=f[1,jy,6]+0.5*(f[1,jy,2]-f[1,jy,4])+0.5*(f[1,jy,1]+f[1,jy,3])
    f[NX,jy,:]=f[NX-1,jy,:]

    if t%SAVE_EVERY==0 or t==STEPS-1:
        vort=(np.roll(uy,-1,0)-np.roll(uy,1,0)-np.roll(ux,-1,1)+np.roll(ux,1,1))*0.5
        vort[mask]=0; frames.append(vort[1:-1,1:-1].copy())
        if t%1000==0:
            vel=np.sqrt(ux**2+uy**2); vel[mask]=0
            print(f'  t={t:>4d} frames={len(frames)} max|v|={vel.max():.4f}')

# 渲染
print(f'渲染 {len(frames)} 帧…')
fig,ax=plt.subplots(figsize=(10,5))
vmax=abs(frames[-1]).max()*0.3
def anim(i):
    ax.clear()
    bg=np.zeros((NY,NX,4)); bg[mask1.T,:]=[0.15,0.18,0.22,1.0]
    ax.imshow(bg,extent=[0,NX,0,NY],origin='lower')
    ax.imshow(frames[i].T,cmap='RdBu_r',origin='lower',extent=[0,NX,0,NY],vmin=-vmax,vmax=vmax,alpha=0.88)
    ax.contour(mask1.T,levels=[0.5],colors='white',linewidths=1.2,extent=[0,NX,0,NY])
    ax.arrow(8,NY*0.5,18,0,head_width=4,head_length=6,fc='cyan',ec='cyan',lw=2,zorder=10)
    ax.set_title(f'逆M水滴绕流 Re≈{Re_est:.0f} t={i*SAVE_EVERY}',fontsize=12,fontweight='bold')
    ax.set_xlim(0,NX); ax.set_ylim(0,NY)

ani=animation.FuncAnimation(fig,anim,frames=len(frames),interval=80)
gif=os.path.join(OUT_DIR,'droplet_MRT_v8_vorticity.gif')
ani.save(gif,writer='pillow',fps=12,dpi=80); plt.close(fig)
print(f'✅ {gif} ({os.path.getsize(gif)//1024}KB)')

# vortex版
fig2,ax2=plt.subplots(figsize=(10,5))
vmax2=abs(frames[-1]).max()*0.2
def anim2(i):
    ax2.clear()
    bg=np.zeros((NY,NX,4)); bg[mask1.T,:]=[0.12,0.15,0.20,1.0]
    ax2.imshow(bg,extent=[0,NX,0,NY],origin='lower')
    ax2.imshow(frames[i].T,cmap='coolwarm',origin='lower',extent=[0,NX,0,NY],vmin=-vmax2,vmax=vmax2,alpha=0.90)
    ax2.contour(mask1.T,levels=[0.5],colors='#ffcc44',linewidths=1,extent=[0,NX,0,NY])
    ax2.arrow(8,NY*0.5,18,0,head_width=4,head_length=6,fc='#ff44aa',ec='#ff44aa',lw=2,zorder=10)
    ax2.set_title(f'逆M水滴涡街 Re≈{Re_est:.0f} frame={i}',fontsize=12)
    ax2.set_xlim(0,NX); ax2.set_ylim(0,NY)
ani2=animation.FuncAnimation(fig2,anim2,frames=len(frames),interval=80)
gif2=os.path.join(OUT_DIR,'droplet_MRT_v8_vortex.gif')
ani2.save(gif2,writer='pillow',fps=12,dpi=80); plt.close(fig2)
print(f'✅ {gif2} ({os.path.getsize(gif2)//1024}KB)')
print('Done!')
