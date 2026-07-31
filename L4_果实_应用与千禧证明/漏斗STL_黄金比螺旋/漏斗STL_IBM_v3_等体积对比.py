"""
PKS 漏斗对比 v3 — 等内体积对比
Smooth缩放至与16bands同体积(114.6x) | 8bands/16bands不变
IBM沉浸边界法 CFD
"""
import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import struct, os
from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
def extract_profile(path, scale=1.0, n_z=60):
    raw=np.fromfile(path,dtype=np.uint8,offset=84)
    n_avail=len(raw)//50
    v_all=[]
    for i in range(0,min(n_avail,200000),120):
        off=i*50
        for j in range(3):
            v_all.append(np.frombuffer(raw[off+12+j*12:off+24+j*12].tobytes(),np.float32)*scale)
    v=np.array(v_all); xs,ys,zs=v[:,0],v[:,1],v[:,2]
    r=np.sqrt(xs**2+ys**2)
    z_edges=np.linspace(zs.min(),zs.max(),n_z+1)
    zc=(z_edges[:-1]+z_edges[1:])/2
    rm=np.array([r[(zs>=z_edges[i])&(zs<z_edges[i+1])].max()
                  if ((zs>=z_edges[i])&(zs<z_edges[i+1])).any() else np.nan
                  for i in range(n_z)])
    valid=np.isfinite(rm)
    rm=np.interp(zc,zc[valid],rm[valid])
    dz=(zc.max()-zc.min())/(n_z-1)
    vol=np.pi*np.trapz(rm**2,zc) if len(rm)>1 else 0
    return zc,rm,vol

def build_sdf(zp,rp,nx,L):
    x=np.linspace(-L/2,L/2,nx)
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    R=np.sqrt(X**2+Y**2)
    rw=np.interp(Z.flatten(),zp,rp).reshape(nx,nx,nx)
    return R-rw

def run_ibm(sdf,nx,dt,steps,nu,label):
    L=2.0; dx=L/nx
    k=2j*np.pi*fftfreq(nx,dx)
    KX,KY,KZ=np.meshgrid(k,k,k,indexing='ij')
    k2=KX**2+KY**2+KZ**2; k2[0,0,0]=1.0
    d3=(np.abs(KX.imag*dx)<np.pi*2/3)&(np.abs(KY.imag*dx)<np.pi*2/3)&(np.abs(KZ.imag*dx)<np.pi*2/3)

    x=np.linspace(-L/2,L/2,nx)
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    u=np.sin(2*np.pi*X/L)*np.cos(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    v=-np.cos(2*np.pi*X/L)*np.sin(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    w=np.zeros_like(u); w[Z>0.75*L/2]=-0.25

    hist={'t':[],'vort':[],'ens':[],'h3':[]}
    for step in range(steps):
        uk,vk,wk=fftn(u),fftn(v),fftn(w)
        wx_k,wy_k,wz_k=KY*wk-KZ*vk,KZ*uk-KX*wk,KX*vk-KY*uk
        om=np.sqrt(ifftn(wx_k).real**2+ifftn(wy_k).real**2+ifftn(wz_k).real**2)

        ux,uy,uz=ifftn(KX*uk).real,ifftn(KY*uk).real,ifftn(KZ*uk).real
        vx,vy,vz=ifftn(KX*vk).real,ifftn(KY*vk).real,ifftn(KZ*vk).real
        wx,wy,wz=ifftn(KX*wk).real,ifftn(KY*wk).real,ifftn(KZ*wk).real
        Nx=-(u*ux+v*uy+w*uz); Ny=-(u*vx+v*vy+w*vz); Nz=-(u*wx+v*wy+w*wz)
        # Clamp to prevent overflow from steep walls
        Nx=np.clip(Nx,-50,50); Ny=np.clip(Ny,-50,50); Nz=np.clip(Nz,-50,50)

        wall=np.clip(sdf,0,None)/(sdf.max()+1e-8); pen=6.0
        Nx+=-pen*wall*u; Ny+=-pen*wall*v; Nz+=-pen*wall*w

        Nxk,Nyk,Nzk=fftn(Nx),fftn(Ny),fftn(Nz)
        dv=KX*Nxk+KY*Nyk+KZ*Nzk
        Nxk-=KX*dv/k2; Nyk-=KY*dv/k2; Nzk-=KZ*dv/k2

        vs=np.exp(-nu*k2.real*dt)
        uk=vs*d3*(uk+dt*Nxk); vk=vs*d3*(vk+dt*Nyk); wk=vs*d3*(wk+dt*Nzk)
        u=ifftn(uk).real; v=ifftn(vk).real; w=ifftn(wk).real
        w[Z>0.75*L/2]=np.clip(w[Z>0.75*L/2],-0.4,0.4)

        if step%12==0:
            hist['t'].append(step*dt); hist['vort'].append(om.max())
            hist['ens'].append(0.5*np.mean(om**2)); hist['h3'].append(np.mean(om**6)**(1/6))
        if step%100==0:
            print(f"  [{label}] step {step}: max|w|={om.max():.4f} H3={hist['h3'][-1]:.4f}")

    return {'label':label,'t':np.array(hist['t']),'vort':np.array(hist['vort']),
            'ens':np.array(hist['ens']),'h3':np.array(hist['h3']),
            'u':u,'v':v,'w':w}

# ============================================================
# MAIN
# ============================================================
bp=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件'
stl_paths={
    'Smooth': os.path.join(bp,'黄金比螺旋漏斗光滑墙壁.stl'),
    '8bands': os.path.join(bp,'黄金比螺旋漏斗8bands.stl'),
    '16bands':os.path.join(bp,'黄金比螺旋漏斗16bands.stl'),
}

# Step 1: 计算体积 → 缩放比
print('Volume calculation...')
print('='*65)
zc_s,rm_s,V_smooth = extract_profile(stl_paths['Smooth'],1.0)
zc_8,rm_8,V_8 = extract_profile(stl_paths['8bands'],1.0)
zc_16,rm_16,V_16 = extract_profile(stl_paths['16bands'],1.0)
print(f'Smooth  V={V_smooth:,.0f} m³  H={zc_s.max()-zc_s.min():.0f}m')
print(f'8bands  V={V_8:,.0f} m³  H={zc_8.max()-zc_8.min():.0f}m')
print(f'16bands V={V_16:,.0f} m³  H={zc_16.max()-zc_16.min():.0f}m')

scale_smooth = (V_16/V_smooth)**(1/3)
print(f'\nScale Smooth by {scale_smooth:.4f}x  →  V ≈ V_16bands')

# Verify
zc_sv,rm_sv,V_sv = extract_profile(stl_paths['Smooth'],scale_smooth)
print(f'Smooth x{scale_smooth:.1f}  V={V_sv:,.0f}  vs 16bands V={V_16:,.0f}  err={abs(V_sv-V_16)/V_16*100:.2f}%')

# Step 2: 归一化 + CFD
nx=40; dt=0.001; steps=200; nu=0.012; L=2.0
print(f'\nCFD: {nx}³ | dt={dt} | steps={steps}')
print('='*65)

configs=[('Smooth(等体积)',zc_sv,rm_sv,'dodgerblue'),
         ('8bands',zc_8,rm_8,'forestgreen'),
         ('16bands',zc_16,rm_16,'crimson')]

# Normalize: same top radius=0.7, preserve aspect
rt=0.7
results={}
for label,zc,rm,color in configs:
    sf=rt/rm.max()
    zn=zc*sf-zc.mean()*sf; rn=rm*sf
    h=zn.max()-zn.min(); tr=rn.max(); br=rn[0]
    print(f'{label}: H_norm={h:.3f} topR={tr:.3f} botR={br:.3f} aspect={h/(2*tr):.2f}')
    sdf=build_sdf(zn,rn,nx,L)
    res=run_ibm(sdf,nx,dt,steps,nu,label)
    results[label]=res

# Step 3: Plot
fig,axes=plt.subplots(2,3,figsize=(18,10))
colors={'Smooth(等体积)':'dodgerblue','8bands':'forestgreen','16bands':'crimson'}

for ci,m in enumerate(['vort','ens','h3']):
    ax=axes[0,ci]
    tl={'vort':'Max Vorticity','ens':'Enstrophy 0.5<|w|^2>','h3':'H3 Sobolev Norm'}
    ax.set_title(tl[m])
    for l,r in results.items():
        ax.plot(r['t'],r[m],color=colors[l],label=l,lw=2)
    ax.legend(fontsize=7); ax.grid(True,alpha=0.3); ax.set_xlabel('时间')

km=nx//2
for ci,(l,r) in enumerate(results.items()):
    ax=axes[1,ci]; uu,vv,ww=r['u'],r['v'],r['w']
    o2=np.sqrt(np.gradient(ww,axis=1)**2+np.gradient(ww,axis=0)**2)[:,:,km]
    o2=np.clip(o2,0,np.percentile(o2,98))
    im=ax.imshow(o2.T,origin='lower',cmap='hot',extent=[-L/2,L/2,-L/2,L/2])
        ax.set_title(f'{l}\n|w| Z=0 final'); plt.colorbar(im,ax=ax,shrink=0.7)
    # wall
    for ll,zz,rr,cc in configs:
        if ll==l:
            sf=rt/rr.max(); zm=zz*sf-zz.mean()*sf; rm_r=rr*sf
            rmid=np.interp(0,zm,rm_r)
            th=np.linspace(0,2*np.pi,100)
            ax.plot(rmid*np.cos(th),rmid*np.sin(th),'c--',lw=1,alpha=0.6)

fig.suptitle(f'PKS漏斗 v3对比: Smooth等体积(×{scale_smooth:.1f}) vs 8bands/16bands\n'
             'IBM沉浸边界法 (归一化同顶半径=0.7, 保留各自长径比)',
             fontsize=13,fontweight='bold')
plt.tight_layout()

od=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\漏斗STL_黄金比螺旋'
fn=os.path.join(od,'漏斗STL_v3_等体积对比.png')
fig.savefig(fn,dpi=150,bbox_inches='tight')

print('\n'+'='*65)
print('v3 Summary (Smooth等体积=16bands)')
print('='*65)
for l,r in results.items():
    v=r['vort']; e=r['ens']; h3=r['h3']
    print(f'  {l:20s}: max|w|={v.max():.4f}  growth={v[-1]/v[0]:.2f}x  H3={h3[-1]:.4f}')
print(f'\nSaved: {fn}')
