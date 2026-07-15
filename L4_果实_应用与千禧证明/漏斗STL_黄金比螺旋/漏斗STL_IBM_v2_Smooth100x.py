"""
PKS 漏斗对比 v2 — Smooth x100 vs 8bands x1 vs 16bands x1
IBM 沉浸边界法, 归一化到同域对比形状差异对涡量的影响
"""
import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import struct, os
from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# STL -> r(z) profile, with optional vertex scaling
# ============================================================
def extract_profile(path, scale=1.0, n_z=50):
    raw = np.fromfile(path, dtype=np.uint8, offset=84)
    n_avail = len(raw) // 50
    v_all = []
    for i in range(0, min(n_avail, 200000), 150):
        off = i * 50
        for j in range(3):
            v_all.append(np.frombuffer(raw[off+12+j*12:off+24+j*12].tobytes(), np.float32) * scale)
    v = np.array(v_all); xs, ys, zs = v[:,0], v[:,1], v[:,2]
    r = np.sqrt(xs**2 + ys**2)
    z_edges = np.linspace(zs.min(), zs.max(), n_z+1)
    zc = (z_edges[:-1]+z_edges[1:])/2
    rm = np.array([r[(zs>=z_edges[i])&(zs<z_edges[i+1])].max()
                    if ((zs>=z_edges[i])&(zs<z_edges[i+1])).any() else np.nan
                    for i in range(n_z)])
    valid = np.isfinite(rm)
    rm = np.interp(zc, zc[valid], rm[valid])
    return zc, rm

# ============================================================
# Build axisymmetric SDF from r(z)
# ============================================================
def build_sdf(z_prof, r_prof, nx, ny, nz, L):
    x = np.linspace(-L/2, L/2, nx)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R = np.sqrt(X**2 + Y**2)
    r_wall = np.interp(Z.flatten(), z_prof, r_prof).reshape(nx, ny, nz)
    sdf = R - r_wall
    return sdf

# ============================================================
# Fast 3D pseudo-spectral NS + IBM
# ============================================================
def run_ibm(sdf, nx, dt, steps, nu, label):
    L = 2.0; dx = L/nx
    k = 2j*np.pi*fftfreq(nx, dx)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    k2 = KX**2+KY**2+KZ**2; k2[0,0,0] = 1.0
    dealias = (np.abs(KX.imag*dx)<np.pi*2/3)&(np.abs(KY.imag*dx)<np.pi*2/3)&(np.abs(KZ.imag*dx)<np.pi*2/3)

    # Taylor-Green vortex
    X, Y, Z = np.meshgrid(np.linspace(-L/2,L/2,nx), np.linspace(-L/2,L/2,nx), np.linspace(-L/2,L/2,nx), indexing='ij')
    u = np.sin(2*np.pi*X/L)*np.cos(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    v = -np.cos(2*np.pi*X/L)*np.sin(2*np.pi*Y/L)*np.cos(2*np.pi*Z/L)
    w = np.zeros_like(u)
    # Inlet flow at top
    w[Z>0.75*L/2] = -0.25

    hist = {'t':[],'vort':[],'ens':[],'h3':[]}
    for step in range(steps):
        u_k, v_k, w_k = fftn(u), fftn(v), fftn(w)
        wx_k, wy_k, wz_k = KY*w_k-KZ*v_k, KZ*u_k-KX*w_k, KX*v_k-KY*u_k
        omega = np.sqrt(ifftn(wx_k).real**2+ifftn(wy_k).real**2+ifftn(wz_k).real**2)

        # Nonlinear: physical space
        ux,uy,uz = ifftn(KX*u_k).real, ifftn(KY*u_k).real, ifftn(KZ*u_k).real
        vx,vy,vz = ifftn(KX*v_k).real, ifftn(KY*v_k).real, ifftn(KZ*v_k).real
        wx,wy,wz = ifftn(KX*w_k).real, ifftn(KY*w_k).real, ifftn(KZ*w_k).real
        Nx=-(u*ux+v*uy+w*uz); Ny=-(u*vx+v*vy+w*vz); Nz=-(u*wx+v*wy+w*wz)

        # IBM wall force (no velocity dependence)
        wall = np.clip(sdf,0,None)/(sdf.max()+1e-8)
        pen = 6.0
        Nx+=-pen*wall*u; Ny+=-pen*wall*v; Nz+=-pen*wall*w

        # Spectral projection
        Nx_k,Ny_k,Nz_k = fftn(Nx),fftn(Ny),fftn(Nz)
        div = KX*Nx_k+KY*Ny_k+KZ*Nz_k
        Nx_k-=KX*div/k2; Ny_k-=KY*div/k2; Nz_k-=KZ*div/k2

        visc=np.exp(-nu*k2.real*dt)
        u_k=visc*dealias*(u_k+dt*Nx_k); v_k=visc*dealias*(v_k+dt*Ny_k); w_k=visc*dealias*(w_k+dt*Nz_k)
        u=ifftn(u_k).real; v=ifftn(v_k).real; w=ifftn(w_k).real
        w[Z>0.75*L/2]=np.clip(w[Z>0.75*L/2],-0.4,0.4)

        if step%15==0:
            hist['t'].append(step*dt); hist['vort'].append(omega.max())
            hist['ens'].append(0.5*np.mean(omega**2)); hist['h3'].append(np.mean(omega**6)**(1/6))
        if step%100==0:
            print(f"  [{label}] step {step}: max|w|={omega.max():.4f}")

    return {'label':label,'t':np.array(hist['t']),'vort':np.array(hist['vort']),
            'ens':np.array(hist['ens']),'h3':np.array(hist['h3']),
            'u':u,'v':v,'w':w}

# ============================================================
# MAIN
# ============================================================
bp = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\漏斗STL_黄金比螺旋'
configs = [
    ('Smooth x100', os.path.join(bp,'黄金比螺旋漏斗光滑墙壁.stl'), 100.0, 'dodgerblue'),
    ('8 bands x1',  os.path.join(bp,'黄金比螺旋漏斗8bands.stl'),      1.0, 'forestgreen'),
    ('16 bands x1', os.path.join(bp,'黄金比螺旋漏斗16bands.stl'),     1.0, 'crimson'),
]

nx=40; dt=0.002; steps=250; nu=0.008; L=2.0
print(f'CFD: {nx}³ | dt={dt} | steps={steps} | nu={nu}')
print('='*60)

# ---- Step 1: Extract profiles ----
profiles={}
for label,path,scale,color in configs:
    zc,rm = extract_profile(path,scale)
    profiles[label]=(zc,rm)
    h=zc.max()-zc.min(); tr=rm.max(); br=rm[0]
    print(f'{label}: H={h:.0f} topR={tr:.0f} botR={br:.1f} ratio={tr/br:.0f}:1 aspect={h/(2*tr):.2f}')

# ---- Step 2: Normalize & run ----
# Normalize: all to same top radius=0.7, preserve aspect ratio
rtarget=0.7
results={}
for label,path,scale,color in configs:
    zc,rm=profiles[label]
    h=zc.max()-zc.min(); tr=rm.max()
    scale_factor = rtarget/tr
    z_norm = zc*scale_factor  # preserve aspect
    r_norm = rm*scale_factor
    z_norm = z_norm - z_norm.mean()  # center vertically
    
    sdf = build_sdf(z_norm,r_norm,nx,nx,nx,L)
    res = run_ibm(sdf,nx,dt,steps,nu,label)
    results[label]=res

# ---- Step 3: Plot ----
fig,axes=plt.subplots(2,3,figsize=(18,10))

for ci,metric in enumerate(['vort','ens','h3']):
    ax=axes[0,ci]
    titles={'vort':'Max Vorticity','ens':'Enstrophy','h3':'H3 Sobolev Norm'}
    ax.set_title(titles[metric])
    for label,res in results.items():
        c={'Smooth x100':'dodgerblue','8 bands x1':'forestgreen','16 bands x1':'crimson'}[label]
        ax.plot(res['t'],res[metric],color=c,label=label,lw=2)
    ax.legend(fontsize=7); ax.grid(True,alpha=0.3)
    ax.set_xlabel('Time')

# XY slices
km=nx//2
for ci,(label,res) in enumerate(results.items()):
    ax=axes[1,ci]
    u,v,w=res['u'],res['v'],res['w']
    omega_xy=np.sqrt(np.gradient(w,axis=1)**2+np.gradient(w,axis=0)**2)[:,:,km]
    omega_xy=np.clip(omega_xy,0,np.percentile(omega_xy,98))
    im=ax.imshow(omega_xy.T,origin='lower',cmap='hot',extent=[-L/2,L/2,-L/2,L/2])
    ax.set_title(f'{label}\n|w| Z=0 slice'); plt.colorbar(im,ax=ax,shrink=0.7)
    # wall outline
    zc,rm=profiles[label]; sf=rtarget/rm.max()
    rmid=np.interp(0,zc*sf-zc.mean()*sf,rm*sf)
    th=np.linspace(0,2*np.pi,100)
    ax.plot(rmid*np.cos(th),rmid*np.sin(th),'c--',lw=1,alpha=0.6)

fig.suptitle('PKS Funnel v2: Smooth x100 vs 8bands/16bands x1\n'
             'IBM Immersed Boundary (same top radius=0.7, preserved aspect ratios)',
             fontsize=14,fontweight='bold')
plt.tight_layout()

out_dir=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\漏斗STL_黄金比螺旋'
fig.savefig(os.path.join(out_dir,'漏斗STL_v2_Smooth100x对比.png'),dpi=150,bbox_inches='tight')

# ---- Step 4: Summary ----
print('\n'+'='*60)
print('v2 Comparison Summary (Smooth x100)')
print('='*60)
for label,res in results.items():
    v=res['vort']; e=res['ens']; h3=res['h3']
    print(f'  {label:15s}: max|w|={v.max():.4f}  final|w|={v[-1]:.4f}  '
          f'growth={v[-1]/v[0]:.2f}x  H3={h3[-1]:.4f}')

print(f'\n[Saved] {os.path.join(out_dir,"漏斗STL_v2_Smooth100x对比.png")}')
