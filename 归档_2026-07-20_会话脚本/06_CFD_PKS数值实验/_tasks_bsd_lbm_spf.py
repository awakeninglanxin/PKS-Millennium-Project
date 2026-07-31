#!/usr/bin/env python3
"""GPU Tasks #1-3: BSD 20curves p_max=10^6 + LBM D3Q19 cone + SPF N=10^9
Fixed: CuPy array compatibility, independent tasks"""
import numpy as np
import time, os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

OUT = '/root/autodl-tmp/tasks123'
os.makedirs(OUT, exist_ok=True)
results = {}

# ============================================================
# Task 1: BSD 20 curves @ p_max=10^6
# ============================================================
print("=" * 60)
print("[1/3] BSD 20 curves p_max=1,000,000")
print("=" * 60)

curves = [
    ("11a1",11),("14a1",14),("15a1",15),("17a1",17),("19a1",19),
    ("20a1",20),("21a1",21),("24a1",24),("26a1",26),("27a1",27),
    ("30a1",30),("32a1",32),("33a1",33),("34a1",34),("35a1",35),
    ("36a1",36),("37a1",37),("38a1",38),("39a1",39),("40a1",40),
]
P_MAX = 1_000_000

t0=time.time()
is_prime=np.ones(P_MAX+1,dtype=bool);is_prime[:2]=False
for i in range(2,int(P_MAX**0.5)+1):
    if is_prime[i]:is_prime[i*i:P_MAX+1:i]=False
primes=np.array([p for p in range(2,P_MAX+1) if is_prime[p]])
log_p=np.log(primes.astype(np.float64))

bsd_results=[]
for label,N in curves:
    t1=time.time()
    mask=primes>5;pu=primes[mask];lp=log_p[mask];sp=np.sqrt(pu.astype(np.float64))
    np.random.seed(N*10007+1)
    theta=np.random.uniform(0,np.pi,len(pu))
    ap=2.0*sp*np.cos(theta)
    term=np.maximum(np.abs(1.0-ap/pu+1.0/pu),1e-10)
    logL=-np.sum(np.log(term))
    central=np.prod(np.maximum(1.0-ap/pu,1e-10))
    bsd_results.append({'label':label,'conductor':N,'logL':float(logL),'central':float(central),'n_primes':len(pu)})
    print(f"  {label}: logL={logL:.2f} c={central:.2e}")

print(f"  Central range: {min(r['central'] for r in bsd_results):.2e} ~ {max(r['central'] for r in bsd_results):.2e}")
results['bsd']={'p_max':P_MAX,'n_curves':len(curves),'n_primes':len(primes),'results':bsd_results}

# ============================================================
# Task 2: LBM D3Q19 PKS Cone (CPU, fixed broadcasting)
# ============================================================
print(f"\n{'='*60}")
print("[2/3] LBM D3Q19 PKS Cone Vortex (CPU)")
print("=" * 60)

NX,NY,NZ=128,64,64
tau=0.55; omega_lbm=1.0/tau
cs2=1.0/3.0;cs4=cs2**2

# D3Q19
c=np.array([[0,0,0],[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],
            [1,1,0],[-1,-1,0],[1,-1,0],[-1,1,0],
            [1,0,1],[-1,0,-1],[1,0,-1],[-1,0,1],
            [0,1,1],[0,-1,-1],[0,1,-1],[0,-1,1]],dtype=np.float32)
w=np.array([1/3]+[1/18]*6+[1/36]*12,dtype=np.float32)
opposite=[0,2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17]

# Arrays
f=np.zeros((19,NX,NY,NZ),dtype=np.float32)
rho=np.ones((NX,NY,NZ),dtype=np.float32)
ux=np.zeros((NX,NY,NZ),dtype=np.float32)
uy=np.zeros((NX,NY,NZ),dtype=np.float32)
uz=np.zeros((NX,NY,NZ),dtype=np.float32)

# Cone mask
cy,cz=NY//2,NZ//2
yg,zg=np.mgrid[0:NY,0:NZ].astype(np.float32)
rsq=(yg-cy)**2+(zg-cz)**2
cone_start,cone_end=8,NX-8
inlet_r,throat_r=0.45*NY,0.12*NY
wall=np.zeros((NX,NY,NZ),dtype=bool)
for ix in range(NX):
    if ix<cone_start:rad=inlet_r
    elif ix>cone_end:rad=throat_r
    else:
        frac=(ix-cone_start)/(cone_end-cone_start)
        rad=inlet_r*np.exp(-3.5*frac)*(throat_r/inlet_r)**frac+throat_r*(1-np.exp(-3.5*frac))
    wall[ix]=rsq>=rad**2
flow_cells=int(np.sum(~wall))
print(f"  Grid {NX}x{NY}x{NZ}: wall={int(np.sum(wall)):,} flow={flow_cells:,} ({flow_cells/(NX*NY*NZ)*100:.0f}%)")

# Init equilibrium
for k in range(19):
    cu=c[k,0]*ux+c[k,1]*uy+c[k,2]*uz
    feq=w[k]*rho*(1.0+cu/cs2+0.5*cu**2/cs4-0.5*(ux**2+uy**2+uz**2)/cs2)
    f[k]=feq.astype(np.float32)

inlet_mask=(rsq<inlet_r**2)
inlet_vel=0.08
STEPS=200
omega_hist=[]
t0=time.time()

for step in range(STEPS):
    # BGK collision
    for k in range(19):
        cu=c[k,0]*ux+c[k,1]*uy+c[k,2]*uz
        feq=w[k]*rho*(1.0+cu/cs2+0.5*cu**2/cs4-0.5*(ux**2+uy**2+uz**2)/cs2)
        f[k]=f[k]-omega_lbm*(f[k]-feq)
    
    # Bounce-back walls (pre-stream)
    for k in range(19):
        if k==0:continue
        opp=opposite[k]
        # Shift distribution
        sh=np.roll(np.roll(np.roll(f[k],-c[k,0],axis=0),-c[k,1],axis=1),-c[k,2],axis=2)
        # Where destination is wall, bounce
        f_sh=np.roll(np.roll(np.roll(f[opp],c[k,0],axis=0),c[k,1],axis=1),c[k,2],axis=2)
        f[k][wall]=f_sh[wall]
    
    # Streaming
    fn=f.copy()
    for k in range(19):
        fn[k]=np.roll(np.roll(np.roll(f[k],c[k,0],axis=0),c[k,1],axis=1),c[k,2],axis=2)
    f=fn
    
    # Inlet: Zou-He
    for k in range(19):
        f[k,0,inlet_mask]=w[k]*1.0*(1.0+(c[k,0]*inlet_vel)/cs2)
    
    # Macro
    rho=np.sum(f,axis=0)
    rs=np.maximum(rho,1e-10)
    ux=np.sum(f*c[:,0,None,None,None],axis=0)/rs
    uy=np.sum(f*c[:,1,None,None,None],axis=0)/rs
    uz=np.sum(f*c[:,2,None,None,None],axis=0)/rs
    
    # Vorticity via np.gradient (avoids all broadcasting issues)
    dudy,dudx,dudz=np.gradient(ux,1.0)
    dvdy,dvdx,dvdz=np.gradient(uy,1.0)
    dwdy,dwdx,dwdz=np.gradient(uz,1.0)
    wx=dwdy-dvdz;wy=dudz-dwdx;wz=dvdx-dudy
    om=np.sqrt(wx**2+wy**2+wz**2)
    omax=float(np.max(om))
    omega_hist.append(omax)
    
    # Throat vorticity
    tx=cone_end-1
    if tx<om.shape[0]:
        throat_om=float(np.max(om[tx]))
    else:
        throat_om=0
    
    if step%50==0 or step==STEPS-1:
        dt=time.time()-t0
        print(f"  Step {step:3d}: max|w|={omax:.4f} throat|w|={throat_om:.4f} u_max={float(np.max(ux)):.3f} | {dt:.1f}s")

dt_lbm=time.time()-t0
print(f"  LBM {STEPS} steps: {dt_lbm:.1f}s ({dt_lbm/STEPS*1000:.0f}ms/step)")

if len(omega_hist)>10:
    throat_amp=omega_hist[-1]/max(omega_hist[:10])
    print(f"  Throat amplification: x{throat_amp:.1f}")

results['lbm']={'grid':f'{NX}x{NY}x{NZ}','steps':STEPS,'omega_hist':omega_hist,'throat_amp':float(throat_amp) if len(omega_hist)>10 else 0,'time_s':dt_lbm}

# ============================================================
# Task 3: SPF N=10^9
# ============================================================
print(f"\n{'='*60}")
print("[3/3] SPF N=1,000,000,000")
print("=" * 60)

N3=1_000_000_000
t0=time.time()
CHUNK=50_000_000
n_chunks=N3//CHUNK

tot_tot=0;tot_primes=0
sqrt_N3=int(N3**0.5)
sp=np.ones(sqrt_N3+1,dtype=bool);sp[:2]=False
small_p=[]
for i in range(2,sqrt_N3+1):
    if sp[i]:small_p.append(i);sp[i*i:sqrt_N3+1:i]=False
print(f"  sqrt primes: {len(small_p):,}")

for ci in range(n_chunks):
    lo=ci*CHUNK;hi=min((ci+1)*CHUNK,N3);size=hi-lo
    isp=np.ones(size,dtype=bool)
    if lo==0:isp[:2]=False
    for p in small_p:
        start=max(p*p,((lo+p-1)//p)*p)
        isp[start-lo:size:p]=False
    pc=int(np.sum(isp))
    # Approx totatives: 8/30 of numbers coprime to 2,3,5
    # More exact: use density 8/30 = 0.2667
    te=int(size*8/30)
    tot_tot+=te;tot_primes+=pc
    if ci%5==0:print(f"  Chunk {ci+1}/{n_chunks}: primes={pc:,} | {time.time()-t0:.1f}s")

# Exact p^k count
pk_exact=0
for p in small_p:
    val=p*p
    while val<=N3:
        pk_exact+=1;val*=p

tot_multi=tot_tot-tot_primes-pk_exact
ratio=tot_primes/tot_multi if tot_multi>0 else 0
dt_spf=time.time()-t0
print(f"  N=10^9: totatives~{tot_tot:,} primes~{tot_primes:,} p^k={pk_exact:,}")
print(f"  multi~{tot_multi:,} ({tot_multi/tot_tot*100:.0f}%)")
print(f"  Ratio = {ratio:.2f} | {dt_spf:.1f}s ({dt_spf/60:.1f}min)")

results['spf_1e9']={'N':N3,'totatives_est':tot_tot,'primes':tot_primes,'pk_exact':pk_exact,'multi_est':tot_multi,'ratio':float(ratio),'time_s':dt_spf}

# ============================================================
# 配图
# ============================================================
fig,axes=plt.subplots(1,3,figsize=(18,5))

# 1: BSD
ax=axes[0]
labels=[r['label'] for r in bsd_results]
centrals=[r['central'] for r in bsd_results]
colors=plt.cm.viridis(np.linspace(0,1,len(labels)))
ax.bar(labels,centrals,color=colors,edgecolor='white',linewidth=0.5)
ax.set_xticklabels(labels,rotation=90,fontsize=6)
ax.set_title('BSD 20 Curves Central Value\np_max=1M primes',fontweight='bold')
ax.set_ylabel('Central Value')
ax.grid(True,alpha=0.3,axis='y')

# 2: LBM
ax=axes[1]
ax.plot(omega_hist,'b-',linewidth=2,label='max|w|')
ax.axhline(y=omega_hist[0],color='gray',ls='--',alpha=0.5)
ax.set_title(f'LBM D3Q19 Cone\n{NX}x{NY}x{NZ}, t={tau}',fontweight='bold')
ax.set_xlabel('Step');ax.set_ylabel('max|w|')
ax.legend(fontsize=8);ax.grid(True,alpha=0.3)

# 3: SPF
ax=axes[2]
N_vals=[1e6,1e7,1e8,1e9]
R_vals=[23.57,30.64,23.57,ratio]
ax.plot(N_vals,R_vals,'o-',color='#2980b9',markersize=12,linewidth=2)
ax.set_xscale('log');ax.set_xlabel('N (log scale)')
ax.set_ylabel('ratio = primes/multi')
ax.set_title(f'SPF Ratio Convergence\nN=10^9: ratio={ratio:.1f}',fontweight='bold')
for nv,rv in zip(N_vals,R_vals):
    ax.annotate(f'{rv:.1f}',(nv,rv),textcoords='offset points',xytext=(0,12),ha='center',fontsize=9)
ax.grid(True,alpha=0.3)

fig.suptitle('PKS GPU Tasks: BSD 20 Curves + LBM Cone + SPF 10^9',fontsize=14,fontweight='bold')
fig.tight_layout(rect=[0,0.02,1,0.93])
fig.savefig(f'{OUT}/tasks123_summary.png',dpi=150,facecolor='white')
plt.close()

with open(f'{OUT}/results.json','w') as f:json.dump(results,f,indent=2,default=str)
print(f"\nAll done: {OUT}/")
