#!/usr/bin/env python3
"""逆M水滴涡街动画 v3 — Re≈150~300, 大网格+保守参数"""
import numpy as np, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

this_dir = r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验'
csv = np.loadtxt(os.path.join(this_dir, 'droplet_invM_analytic.csv'), delimiter=',', skiprows=1)

def load_mask(NX, NY, scale, cx0, cy0):
    px=(csv[:,0]*scale+cx0).astype(np.float64); py=(csv[:,1]*scale+cy0).astype(np.float64)
    xx,yy=np.meshgrid(np.arange(NX+2),np.arange(NY+2),indexing='ij')
    return Path(np.column_stack((px,py))).contains_points(
        np.column_stack((xx.ravel(),yy.ravel()))).reshape(NX+2,NY+2)

# D2Q9
Q=9; w=np.array([4/9,1/9,1/9,1/9,1/9,1/36,1/36,1/36,1/36])
cx=np.array([0,1,0,-1,0,1,-1,-1,1],np.int32); cy=np.array([0,0,1,0,-1,1,1,-1,-1],np.int32)
opp=np.array([0,3,4,1,2,7,8,5,6],np.int32)

# 参数: u0=0.04, tau=0.60 (稳定!), D≈250, Re≈300
NX,NY=700,350; u0=0.04; tau=0.60; omega=1.0/tau
scale=250.0/5.333; cx0=int(NX*0.22); cy0=NY//2; D_est=250
Re=3*u0*D_est/(tau-0.5)
steps=10000; save_every=50
print(f'N={NX}×{NY} u0={u0} τ={tau} D≈{D_est} Re≈{Re:.0f} frames={steps//save_every}')

mask=load_mask(NX,NY,scale,cx0,cy0); mask1=mask[1:-1,1:-1]
out_dir=os.path.join(this_dir,'cfd_Greedy_BaseToTip_v2')
os.makedirs(out_dir,exist_ok=True)

f=np.zeros((NX+2,NY+2,Q))
for k in range(Q): f[:,:,k]=w[k]
rho=np.ones((NX+2,NY+2)); ux_f=np.zeros((NX+2,NY+2)); uy_f=np.zeros((NX+2,NY+2))
frames=[]

for t in range(steps):
    rho=np.sum(f,2); de=rho+1e-10
    ux_f=(f[:,:,1]+f[:,:,5]+f[:,:,8]-f[:,:,3]-f[:,:,6]-f[:,:,7])/de
    uy_f=(f[:,:,2]+f[:,:,5]+f[:,:,6]-f[:,:,4]-f[:,:,7]-f[:,:,8])/de
    ux_f[mask]=0; uy_f[mask]=0

    for k in range(Q):
        cu=3*(cx[k]*ux_f+cy[k]*uy_f)
        f[:,:,k]-=omega*(f[:,:,k]-w[k]*rho*(1+cu+0.5*cu*cu-1.5*(ux_f**2+uy_f**2)))

    fb=np.zeros_like(f)
    for k in range(Q): fb[:,:,k]=np.roll(np.roll(f[:,:,k],-cx[k],0),-cy[k],1)
    for k in range(Q): f[:,:,k]=np.roll(np.roll(f[:,:,k],cx[k],0),cy[k],1)
    for k in range(Q): f[mask,k]=fb[mask,opp[k]]

    jy=np.arange(2,NY)
    rho[1,jy]=(f[1,jy,0]+f[1,jy,2]+f[1,jy,4]+2*(f[1,jy,3]+f[1,jy,6]+f[1,jy,7]))/(1-u0)
    f[1,jy,1]=f[1,jy,3]+2*w[1]*rho[1,jy]*u0
    f[1,jy,5]=f[1,jy,7]-0.5*(f[1,jy,2]-f[1,jy,4])+0.5*(f[1,jy,1]+f[1,jy,3])
    f[1,jy,8]=f[1,jy,6]+0.5*(f[1,jy,2]-f[1,jy,4])+0.5*(f[1,jy,1]+f[1,jy,3])
    f[NX,jy,:]=f[NX-1,jy,:]

    if t%save_every==0 or t==steps-1:
        vort=(np.roll(uy_f,-1,0)-np.roll(uy_f,1,0)-np.roll(ux_f,-1,1)+np.roll(ux_f,1,1))*0.5
        vort[mask]=0; frames.append(vort[1:-1,1:-1].copy())
        if t%2000==0:
            vel=np.sqrt(ux_f**2+uy_f**2); vel[mask]=0
            print(f"  t={t:>5d} frames={len(frames)} max|v|={vel.max():.4f} |vort|max={abs(vort[1:-1,1:-1]).max():.4f}")

print(f'渲染 {len(frames)} 帧 GIF...')
fig,ax=plt.subplots(figsize=(12,6))
vmax=abs(frames[-1]).max()*0.3

def animate(i):
    ax.clear()
    bg=np.zeros((NY,NX,4)); bg[mask1.T,:]=[0.15,0.18,0.22,1.0]
    ax.imshow(bg,extent=[0,NX,0,NY],origin='lower')
    ax.imshow(frames[i].T,cmap='RdBu_r',origin='lower',extent=[0,NX,0,NY],vmin=-vmax,vmax=vmax,alpha=0.85)
    ax.contour(mask1.T,levels=[0.5],colors='white',linewidths=1.5,extent=[0,NX,0,NY])
    ax.arrow(15,NY*0.5,30,0,head_width=8,head_length=12,fc='cyan',ec='cyan',lw=3,zorder=10)
    ax.set_title(f'逆M水滴绕流 钝面迎流 Re≈{Re:.0f} t={i*save_every}',fontsize=13,fontweight='bold')
    ax.set_xlim(0,NX); ax.set_ylim(0,NY); ax.set_xlabel('X→'); ax.set_ylabel('Y')

anim=animation.FuncAnimation(fig,animate,frames=len(frames),interval=100)
gif_path=os.path.join(out_dir,'droplet_BaseToTip_vorticity_v3.gif')
anim.save(gif_path,writer='pillow',fps=10,dpi=90); plt.close(fig)
print(f'✅ {gif_path} ({os.path.getsize(gif_path)//1024}KB)')
