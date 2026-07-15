"""
PKS漏斗 v6: 4种曲面全等体积统一对决
Golden Ratio / Super-Hyper / H+Straight30 / H+Straight45
全部缩放至 V=100, IBM CFD逐对对比
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
    return zc,rm,zc.max()-zc.min(),rm.max(),rm[0],np.pi*np.trapz(rm**2,zc)

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

# ========= MAIN =========
bp=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件'
configs=[
    ('Golden Ratio', os.path.join(bp,'黄金比螺旋漏斗光滑墙壁.stl'), 'dodgerblue'),
    ('Super-Hyper',  os.path.join(bp,'超双曲锥漏斗.stl'), 'darkorange'),
    ('H+Straight30', os.path.join(bp,'双曲直锥漏斗30°.stl'), 'forestgreen'),
    ('H+Straight45', os.path.join(bp,'双曲直锥漏斗45°.stl'), 'crimson'),
]

# Step 1: Compute all volumes, scale factors to V_target
V_target = 100.0
print(f'Target volume: {V_target:.0f}')
print('='*70)
profiles={}
for label,path,color in configs:
    zc,rm,h,tr,br,vol=extract(path)
    sf=(V_target/vol)**(1/3)
    zc2,rm2,_,_,_,_=extract(path,sf)
    profiles[label]=(sf,zc2,rm2,color)
    print(f'{label:15s}: orig V={vol:.0f} H={h:.1f} ratio={tr/br:.1f}:1 → x{sf:.3f} → V={np.pi*np.trapz(rm2**2,zc2):.0f}')

# Step 2: CFD
nx=40; dt=0.001; st=200; nu=0.01; rt=0.7; L=2.0
results={}
for label,path,color in configs:
    sf,zc,rm,_=profiles[label]
    print(f'\n[{label}] scaled x{sf:.3f}: H={zc.max()-zc.min():.1f} aspect={((zc.max()-zc.min())/(2*rm.max())):.2f}')
    sf2=rt/rm.max(); zn=zc*sf2-zc.mean()*sf2; rn=rm*sf2
    s=sdf(zn,rn,nx,L)
    r=ibm(s,nx,dt,st,nu,label)
    results[label]=dict(r,color=color)

# Step 3: Plot
fig,axes=plt.subplots(2,3,figsize=(18,11))
colors={l:r['color'] for l,r in results.items()}

# Time series: max vorticity
ax=axes[0,0]
for l,r in results.items():
    ax.plot(r['t'],r['v'],color=colors[l],label=l,lw=2)
ax.set_title('Max Vorticity (all V=100)'); ax.legend(fontsize=7); ax.grid(True,alpha=0.3); ax.set_xlabel('Time')

# Time series: H3
ax=axes[0,1]
for l,r in results.items():
    ax.plot(r['t'],r['h3'],color=colors[l],lw=2)
ax.set_title('H3 Sobolev Norm'); ax.grid(True,alpha=0.3); ax.set_xlabel('Time')

# Enstrophy
ax=axes[0,2]
for l,r in results.items():
    ax.plot(r['t'],r['e'],color=colors[l],lw=2)
ax.set_title('Enstrophy'); ax.grid(True,alpha=0.3); ax.set_xlabel('Time')

# r(z) profiles (normalized)
ax=axes[1,0]
for l,(sf,zc,rm,color) in profiles.items():
    sf2=rt/rm.max(); zn=zc*sf2-zc.mean()*sf2; rn=rm*sf2
    ax.plot(zn,rn,color=color,label=l,lw=2)
ax.set_title('r(z) Profiles (norm)'); ax.legend(fontsize=7); ax.grid(True,alpha=0.3)
ax.set_xlabel('Z'); ax.set_ylabel('R')

# Bar chart: final growth
ax=axes[1,1]
labels=[l for l,_,_ in configs]; growths=[results[l]['v'][-1]/results[l]['v'][0] for l in labels]
bars=ax.bar(labels,growths,color=[colors[l] for l in labels])
ax.set_title('Vortex Growth (all V=100)'); ax.set_ylabel('Growth ratio')
for b,g in zip(bars,growths): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.03,f'{g:.2f}x',ha='center',fontsize=9)

# Summary table
ax=axes[1,2]; ax.axis('off')
tdata=[['Funnel','Ratio','Aspect','max|w|','Growth','H3']]
for l,r in results.items():
    sf,zc,rm,_=profiles[l]; h=zc.max()-zc.min()
    v=r['v']; h3=r['h3']
    tdata.append([l,f'{rm.max()/rm[0]:.1f}:1',f'{h/(2*rm.max()):.2f}',
                  f'{v.max():.2f}',f'{v[-1]/v[0]:.2f}x',f'{h3[-1]:.3f}'])
tab=ax.table(cellText=tdata,loc='center',cellLoc='center')
tab.auto_set_font_size(False); tab.set_fontsize(9); tab.scale(1,1.4)

fig.suptitle('PKS Funnel v6: All 4 Curves at Equal Volume (V=100)\n'
             'Golden Ratio vs Super-Hyper vs H+Straight30 vs H+Straight45',
             fontsize=14, fontweight='bold')
plt.tight_layout()

od=r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\漏斗STL_黄金比螺旋'
fn=os.path.join(od,'漏斗STL_v6_全等体积对决.png')
fig.savefig(fn,dpi=150,bbox_inches='tight')

print(f'\nSaved: {fn}')
print('\n=== FINAL RANKING (all V=100) ===')
ranked=sorted(results.items(),key=lambda x: x[1]['v'][-1]/x[1]['v'][0],reverse=True)
for i,(l,r) in enumerate(ranked):
    v=r['v']; h3=r['h3']
    print(f'  #{i+1} {l:15s}: growth={v[-1]/v[0]:.2f}x max|w|={v.max():.2f} H3={h3[-1]:.3f}')
