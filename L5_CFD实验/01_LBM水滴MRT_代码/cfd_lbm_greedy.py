#!/usr/bin/env python3
"""逆M水滴 LBM CFD — Greedy 98点轮廓 + 双向来流"""
import numpy as np, math, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path

# ═══════ Greedy 轮廓 ═══════
def inv_cardioid(theta):
    return 1.0/(0.5*np.exp(1j*theta)-0.25*np.exp(2j*theta))

pts = np.loadtxt(os.path.join(os.path.dirname(__file__), 'droplet_invM_analytic.csv'),
                 delimiter=',', skiprows=1)
N_half = len(pts)//2; ux, uy = pts[:N_half,0], pts[:N_half,1]

def coprime(a,b): return math.gcd(a,b)==1
ancs=set()
for q in range(2,8):
    for p in range(1,q):
        if coprime(p,q):
            th=2*np.pi*p/q; ci=inv_cardioid(th)
            if 0<th<np.pi and ci.imag<=0:
                ancs.add(int(np.argmin(np.hypot(ux-ci.real,uy+ci.imag))))
ancs.add(0); ancs.add(N_half-1)

def seg_dev(a,b):
    md,mi=0.0,a; ax,ay=ux[a],uy[a]; bx,by=ux[b],uy[b]
    abx,aby=bx-ax,by-ay; ab2=abx**2+aby**2
    if ab2<1e-20: return 0.0,a
    for i in range(a,b+1):
        t=max(0,min(1,((ux[i]-ax)*abx+(uy[i]-ay)*aby)/ab2))
        d=np.hypot(ux[i]-(ax+t*abx),uy[i]-(ay+t*aby))
        if d>md: md,mi=d,i
    return md,mi

k4=list(ancs)
while True:
    ki=sorted(k4); wd,ws=0,0
    for s in range(len(ki)-1):
        d,_=seg_dev(ki[s],ki[s+1])
        if d>wd: wd,ws=d,s
    if wd<0.002: break
    a,b=ki[ws],ki[ws+1]; _,wi=seg_dev(a,b); k4.append(wi)
k4=sorted(set(k4))

gx=ux[k4]; gy=uy[k4]
gx_cl=np.concatenate([gx,gx[::-1],[gx[0]]])
gy_cl=np.concatenate([gy,-gy[::-1],[gy[0]]])
print(f'Greedy contour: {len(k4)*2} pts')

# ═══════ LBM D2Q9 ═══════
Q=9
w=np.array([4/9,1/9,1/9,1/9,1/9,1/36,1/36,1/36,1/36])
cx=np.array([0,1,0,-1,0,1,-1,-1,1],dtype=np.int32)
cy=np.array([0,0,1,0,-1,1,1,-1,-1],dtype=np.int32)
opp=np.array([0,3,4,1,2,7,8,5,6],dtype=np.int32)

NX,NY=350,180; scale=150.0/5.333; cx0=int(NX*0.4); cy0=NY//2

px=(gx_cl*scale+cx0).astype(int); py=(gy_cl*scale+cy0).astype(int)
path=Path(np.column_stack((px,py)))
xx,yy=np.meshgrid(np.arange(NX+2),np.arange(NY+2),indexing='ij')
mask=path.contains_points(np.column_stack((xx.ravel(),yy.ravel()))).reshape(NX+2,NY+2)
mask1=mask[1:-1,1:-1]
print(f'Obstacle: {mask.sum()} cells / {(NX+2)*(NY+2)}')

u0=0.05; tau=0.58; omega=1.0/tau; steps=20000; save_every=100
Re=u0*(NX//4)*(tau-0.5)/3.0

for direction, dir_name, flow_desc in [
    ('left','Greedy_BaseToTip','Base to Tip'),
    ('right','Greedy_TipToBase','Tip to Base')]:

    print(f'\n>>> {flow_desc}: u0={u0}, tau={tau}, Re~{Re:.0f}')
    out_dir=os.path.join(os.path.dirname(__file__),f'cfd_{dir_name}')
    os.makedirs(out_dir,exist_ok=True)

    # 初始化
    f=np.zeros((NX+2,NY+2,Q))
    for k in range(Q): f[:,:,k]=w[k]
    rho=np.ones((NX+2,NY+2)); ux_f=np.zeros((NX+2,NY+2)); uy_f=np.zeros((NX+2,NY+2))
    vort_snaps=[]; vel_snaps=[]

    for t in range(steps):
        # 宏观量
        rho=np.sum(f,axis=2); denom=rho+1e-10
        ux_f=(f[:,:,1]+f[:,:,5]+f[:,:,8]-f[:,:,3]-f[:,:,6]-f[:,:,7])/denom
        uy_f=(f[:,:,2]+f[:,:,5]+f[:,:,6]-f[:,:,4]-f[:,:,7]-f[:,:,8])/denom
        ux_f[mask]=0; uy_f[mask]=0

        # BGK 碰撞
        for k in range(Q):
            cu=3*(cx[k]*ux_f+cy[k]*uy_f)
            feq=w[k]*rho*(1+cu+0.5*cu*cu-1.5*(ux_f**2+uy_f**2))
            f[:,:,k]-=omega*(f[:,:,k]-feq)

        # 传播前保存障碍点
        f_bounce=np.zeros_like(f)
        for k in range(Q):
            f_bounce[:,:,k]=np.roll(np.roll(f[:,:,k],-cx[k],axis=0),-cy[k],axis=1)

        # 传播
        for k in range(Q):
            f[:,:,k]=np.roll(np.roll(f[:,:,k],cx[k],axis=0),cy[k],axis=1)

        # 障碍反弹
        for k in range(Q):
            f[mask,k]=f_bounce[mask,opp[k]]

        # Zou-He 入口
        jy=np.arange(2,NY)
        if direction=='left':
            rho[1,jy]=(f[1,jy,0]+f[1,jy,2]+f[1,jy,4]+2*(f[1,jy,3]+f[1,jy,6]+f[1,jy,7]))/(1-u0)
            f[1,jy,1]=f[1,jy,3]+2*w[1]*rho[1,jy]*u0
            f[1,jy,5]=f[1,jy,7]-0.5*(f[1,jy,2]-f[1,jy,4])+0.5*f[1,jy,1]+0.5*f[1,jy,3]
            f[1,jy,8]=f[1,jy,6]+0.5*(f[1,jy,2]-f[1,jy,4])+0.5*f[1,jy,1]+0.5*f[1,jy,3]
            f[NX,jy,:]=f[NX-1,jy,:]
        else:
            rho[NX,jy]=(f[NX,jy,0]+f[NX,jy,2]+f[NX,jy,4]+2*(f[NX,jy,1]+f[NX,jy,5]+f[NX,jy,8]))/(1+u0)
            f[NX,jy,3]=f[NX,jy,1]+2*w[3]*rho[NX,jy]*u0
            f[NX,jy,6]=f[NX,jy,8]-0.5*(f[NX,jy,4]-f[NX,jy,2])+0.5*f[NX,jy,3]+0.5*f[NX,jy,1]
            f[NX,jy,7]=f[NX,jy,5]+0.5*(f[NX,jy,4]-f[NX,jy,2])+0.5*f[NX,jy,3]+0.5*f[NX,jy,1]
            f[1,jy,:]=f[2,jy,:]

        # 快照
        if t%save_every==0 or t==steps-1:
            vort=(np.roll(uy_f,-1,0)-np.roll(uy_f,1,0)
                 -np.roll(ux_f,-1,1)+np.roll(ux_f,1,1))*0.5
            vort[mask]=0; vel=np.sqrt(ux_f**2+uy_f**2); vel[mask]=0
            vort_snaps.append(vort[1:-1,1:-1].copy())
            vel_snaps.append(vel[1:-1,1:-1].copy())
            if t%4000==0:
                print(f"  t={t:>6d}  max|u|={vel.max():.4f}  |vort|max={abs(vort[1:-1,1:-1]).max():.4f}")

    # ═══ 三栏可视化 ═══
    final_vort=vort_snaps[-1]; final_vel=vel_snaps[-1]
    fig,axes=plt.subplots(1,3,figsize=(18,5.5))
    ext=[0,NX,0,NY]

    ax=axes[0]; vm=abs(final_vort).max()*0.4
    im=ax.imshow(final_vort.T,cmap='RdBu_r',origin='lower',extent=ext,vmin=-vm,vmax=vm)
    ax.contour(mask1.T,levels=[0.5],colors='black',lw=1.5,extent=ext)
    ax.set_title(f'Vorticity - {flow_desc}'); plt.colorbar(im,ax=ax,shrink=0.8)

    ax=axes[1]; sk=5
    xs=np.arange(sk,NX,sk); ys=np.arange(sk,NY,sk); X,Y=np.meshgrid(xs,ys)
    qvx=ux_f[1:-1,1:-1][xs[:,None],ys[None,:]].T
    qvy=uy_f[1:-1,1:-1][xs[:,None],ys[None,:]].T
    ax.quiver(X,Y,qvx,qvy,scale=1.5,width=0.002,alpha=0.7)
    ax.contour(mask1.T,levels=[0.5],colors='black',lw=1.5,extent=ext)
    ax.set_title(f'Velocity - {flow_desc}'); ax.set_xlim(0,NX); ax.set_ylim(0,NY)

    ax=axes[2]
    im2=ax.imshow(final_vel.T,cmap='hot',origin='lower',extent=ext)
    ax.contour(mask1.T,levels=[0.5],colors='cyan',lw=1.2,extent=ext)
    arr_x=NX*0.08 if direction=='left' else NX*0.92
    arr_dx=35 if direction=='left' else -35
    ax.arrow(arr_x,NY*0.5,arr_dx,0,head_width=6,head_length=10,fc='cyan',ec='cyan',lw=2)
    ax.set_title(f'Speed - {flow_desc}'); ax.set_xlim(0,NX); ax.set_ylim(0,NY)
    plt.colorbar(im2,ax=ax,shrink=0.8)

    fig.suptitle(f'Inverse-M Droplet LBM CFD: {flow_desc} (Re~{Re:.0f}, 98-pt Greedy contour)',
                 fontsize=13,fontweight='bold')
    plt.tight_layout()
    png=os.path.join(out_dir,f'droplet_{dir_name}_cfd.png')
    fig.savefig(png,dpi=180,bbox_inches='tight'); plt.close(fig)
    print(f'   >> {png}')

    # 保存数据
    np.savez(os.path.join(out_dir,'cfd_data.npz'),
             vort=final_vort,vel=final_vel,mask=mask1,
             cx0=cx0,cy0=cy0,scale=scale,direction=direction)

print('\nCFD Done!')
