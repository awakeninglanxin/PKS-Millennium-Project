"""
PKS漏斗 v5: 两组等体积对比
A: 黄金比螺旋(Golden) vs 超双曲锥(SuperH) — SuperH缩放至等体积
B: 双曲直锥30° vs 双曲直锥45° — 45°缩放至等体积
"""
import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import struct, os
from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False

def extract(path, scale=1.0, n_z=50):
    raw=np.fromfile(path,dtype=np.uint8,offset=84)
    v_all=[]
    for i in range(0,min(len(raw)//50,200000),60):
        off=i*50
        for j in range(3):
            v_all.append(np.frombuffer(raw[off+12+j*12:off+24+j*12].tobytes(),np.float32)*scale)
    v=np.array(v_all); xs,ys,zs=v[:,0],v[:,1],v[:,2]
    r=np.sqrt(xs**2+ys**2)
    ze=np.linspace(zs.min(),zs.max(),n_z+1); zc=(ze[:-1]+ze[1:])/2
    rm=np.array([r[(zs>=ze[i])&(zs<ze[i+1])].max()
                  if ((zs>=ze[i])&(zs<ze[i+1])).any() else np.nan for i in range(n_z)])
    valid=np.isfinite(rm); rm=np.interp(zc,zc[valid],rm[valid])
    return zc,rm

def sdf(zp,rp,nx,L):
    x=np.linspace(-L/2,L/2,nx); X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    R=np.sqrt(X**2+Y**2); rw=np.interp(Z.flatten(),zp,rp).reshape(nx,nx,nx)
    return R-rw

def ibm(sdf,nx,dt,st,nu,label):
    L=2.0; dx=L/nx; k=2j*np.pi*fftfreq(nx,dx)
    KX,KY,KZ=np.meshgrid(k,k,k,indexing='ij'); k2=KX**2+KY**2+KZ**2; k2[0,0,0]=1.0
    d3=(np.abs(KX.imag*dx)<np.pi*2/3)&(np.abs(KY.imag*dx)<np.pi*2/3)&(np.abs(KZ.imag*dx)<np.pi*2/3)
    x=np.linspace(-L/2,L/2,nx); X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    u=np.sin(2*np.pi*X/L)*np.cos(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    v=-np.cos(2*np.pi*X/L)*np.sin(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    w=np.zeros_like(u); w[Z>0.75*L/2]=-0.25
    h={'t':[],'v':[],'e':[],'h3':[]}
    for s in range(st):
        uk,vk,wk=fftn(u),fftn(v),fftn(w)
        om=np.sqrt(ifftn(KY*wk-KZ*vk).real**2+ifftn(KZ*uk-KX*wk).real**2+ifftn(KX*vk-KY*uk).real**2)
        ux,uy,uz=ifftn(KX*uk).real,ifftn(KY*uk).real,ifftn(KZ*uk).real
        vx,vy,vz=ifftn(KX*vk).real,ifftn(KY*vk).real,ifftn(KZ*vk).real
        wx,wy,wz=ifftn(KX*wk).real,ifftn(KY*wk).real,ifftn(KZ*wk).real
        Nx=-(u*ux+v*uy+w*uz); Ny=-(u*vx+v*vy+w*vz); Nz=-(u*wx+v*wy+w*wz)
        Nx=np.clip(Nx,-50,50); Ny=np.clip(Ny,-50,50); Nz=np.clip(Nz,-50,50)
        wall=np.clip(sdf,0,None)/(sdf.max()+1e-8)
        Nx+=-6*wall*u; Ny+=-6*wall*v; Nz+=-6*wall*w
        Nxk,Nyk,Nzk=fftn(Nx),fftn(Ny),fftn(Nz); dv=KX*Nxk+KY*Nyk+KZ*Nzk
        Nxk-=KX*dv/k2; Nyk-=KY*dv/k2; Nzk-=KZ*dv/k2
        vs=np.exp(-nu*k2.real*dt)
        uk=vs*d3*(uk+dt*Nxk); vk=vs*d3*(vk+dt*Nyk); wk=vs*d3*(wk+dt*Nzk)
        u=ifftn(uk).real; v=ifftn(vk).real; w=ifftn(wk).real
        w[Z>0.75*L/2]=np.clip(w[Z>0.75*L/2],-0.4,0.4)
        if s%10==0:
            h['t'].append(s*dt); h['v'].append(om.max())
            h['e'].append(0.5*np.mean(om**2)); h['h3'].append(np.mean(om**6)**(1/6))
    return {k:np.array(v) for k,v in h.items()}

# ========== MAIN ==========
bp=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件'
nx=40; dt=0.001; st=200; nu=0.01; rt=0.7; L=2.0

# Experiment A: Golden Ratio vs Super-Hyper (Super scaled to match Golden volume)
f_sg=(12/35)**(1/3)  # 0.7079
experiments = [
    ('A: Golden vs SuperH(等体积)', [
        ('Golden Ratio', os.path.join(bp,'黄金比螺旋漏斗光滑墙壁.stl'), 1.0, 'dodgerblue'),
        ('SuperH x0.708', os.path.join(bp,'超双曲锥漏斗.stl'), f_sg, 'darkorange'),
    ]),
    ('B: H30 vs H45(等体积)', [
        ('H+Straight30',  os.path.join(bp,'双曲直锥漏斗30°.stl'), 1.0, 'forestgreen'),
        ('H+Straight45 x1.524', os.path.join(bp,'双曲直锥漏斗45°.stl'), 1.5244, 'crimson'),
    ]),
]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
colors = {}

for ei, (title, configs) in enumerate(experiments):
    profs={}; results={}
    print(f'\n=== {title} ===')
    for label,path,scale,color in configs:
        zc,rm=extract(path,scale)
        profs[label]=(zc,rm)
        vol=np.pi*np.trapz(rm**2,zc)
        print(f'{label}: H={zc.max()-zc.min():.1f} V={vol:.0f} ratio={rm.max()/rm[0]:.1f}:1')
        colors[label]=color
    
    for label,path,scale,color in configs:
        zc,rm=profs[label]
        sf=rt/rm.max(); zn=zc*sf-zc.mean()*sf; rn=rm*sf
        s=sdf(zn,rn,nx,L)
        r=ibm(s,nx,dt,st,nu,label)
        results[label]=dict(r,color=color)
    
    # Plot: time series
    ax=axes[ei,0]
    for l,r in results.items():
        ax.plot(r['t'],r['v'],color=colors[l],label=l,lw=2)
    ax.set_title(f'{title} — Max Vorticity'); ax.legend(fontsize=7); ax.grid(True,alpha=0.3); ax.set_xlabel('Time')
    
    # Plot: r(z) profiles
    ax=axes[ei,1]
    for l,(zc,rm) in profs.items():
        sf=rt/rm.max(); zn=zc*sf-zc.mean()*sf
        ax.plot(zn,rm*sf,color=colors[l],label=l,lw=2)
    ax.set_title(f'{title} — r(z) Profiles'); ax.legend(fontsize=7); ax.grid(True,alpha=0.3)
    ax.set_xlabel('Z (norm)'); ax.set_ylabel('R (norm)')
    
    # Print summary
    for l,r in results.items():
        v=r['v']; h3=r['h3']
        print(f'  {l}: max|w|={v.max():.3f} growth={v[-1]/v[0]:.2f}x H3={h3[-1]:.3f}')

fig.suptitle('PKS Funnel v5: Equal-Volume Pairwise Comparison\n'
             'A: Golden Ratio vs Super-Hyperbolic  |  B: H+Straight30 vs H+Straight45',
             fontsize=14, fontweight='bold')
plt.tight_layout()

od=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\漏斗STL_黄金比螺旋'
fn=os.path.join(od,'漏斗STL_v5_两组等体积对比.png')
fig.savefig(fn,dpi=150,bbox_inches='tight')
print(f'\nSaved: {fn}')
