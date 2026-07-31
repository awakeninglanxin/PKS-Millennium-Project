"""
超参数搜索对比实验 (clean version)
==========================================
Random Search vs Bayesian Optimization vs Fractal-Guided Search

搜索空间: lr in [1e-4, 0.1], dropout in [0, 0.5]
预算: 60 次评估, 50 次独立重复
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json, time, warnings
warnings.filterwarnings('ignore')

np.random.seed(0)
print("=" * 70)
print("  Hyperparameter Search: Random vs Bayesian vs Fractal-Guided")
print("=" * 70)

# ============================================================
# 1. 质量函数 + 全局最优
# ============================================================
def quality(lr, dropout):
    q1 = 0.88*np.exp(-0.5*((lr-0.01)/0.025)**2 - 0.5*((dropout-0.2)/0.12)**2)
    q2 = 0.85*np.exp(-0.5*((lr-0.04)/0.015)**2 - 0.5*((dropout-0.35)/0.08)**2)
    div = 1.0/(1.0+np.exp(18*(lr-0.055)))
    slow = 1.0-0.25*np.exp(-0.5*((lr-0.002)/0.003)**2)
    return np.clip(0.45+(q1+q2)*div*slow, 0, 1)

from scipy.optimize import minimize
res = minimize(lambda x: -quality(x[0],x[1]), [0.01,0.2],
               bounds=[(1e-4,0.1),(0,0.5)], method='L-BFGS-B')
OPT_VAL = quality(res.x[0], res.x[1])
OPT_LR, OPT_DO = res.x
print(f"\nGlobal optimum: acc={OPT_VAL:.4f} @ lr={OPT_LR:.5f}, do={OPT_DO:.3f}")

lr_min, lr_max = 1e-4, 0.1
do_min, do_max = 0.0, 0.5

# ============================================================
# 2. 逆 M 逃逸时间场 (Fractal 先验)
# ============================================================
print("\n▶ Computing inverse M escape field...")
W=H=300
re_g = np.linspace(-2.0, 4.0, W)
im_g = np.linspace(-3.0, 3.0, H)
C = re_g[None,:]+1j*im_g[:,None]

t0=time.time()
Z=np.zeros_like(C,dtype=np.complex128)
ns=np.full(C.shape,300,dtype=np.float64)
act=np.ones(C.shape,dtype=bool)
Cs=np.where(np.abs(C)<1e-12,1e-12+0j,C)
P=1.0/Cs
np.seterr(over='ignore',invalid='ignore')
for n in range(300):
    Z=np.where(act,Z*Z+P,Z)
    aZ=np.abs(Z); esc=aZ>1e4; ne=esc&act
    if np.any(ne):
        with np.errstate(invalid='ignore',divide='ignore'):
            ns[ne]=n+1.0-np.log(np.log(aZ[ne]+1e-300))/np.log(2.0)
        act=act&~esc
    if not np.any(act): break

ns_n=np.log1p(np.clip(ns,0,300))/np.log1p(300)
ns_n[ns>=300]=0.5
print(f"  Done in {time.time()-t0:.1f}s, escape rate={100*np.mean(ns<300):.1f}%")

from scipy.interpolate import RectBivariateSpline
interp_esc = RectBivariateSpline(im_g, re_g, ns_n)

def fractal_score(lr, do):
    re=np.clip(-2.0+(lr-lr_min)/(lr_max-lr_min)*6.0,-1.99,3.99)
    im=np.clip(-3.0+(do-do_min)/(do_max-do_min)*6.0,-2.99,2.99)
    return float(interp_esc.ev(do,lr))

# Fractal 先验图
lr_m=np.linspace(lr_min,lr_max,200)
do_m=np.linspace(do_min,do_max,200)
LRm, DOm=np.meshgrid(lr_m,do_m)
Qm=quality(LRm,DOm)
ESCm=np.array([[fractal_score(l,d) for l in lr_m] for d in do_m])

fig0,ax0=plt.subplots(figsize=(10,8),facecolor='black')
ax0.imshow(ESCm,extent=[lr_min,lr_max,do_min,do_max],cmap='viridis',origin='lower',aspect='auto')
cs=ax0.contour(LRm,DOm,Qm,levels=[0.6,0.7,0.8,0.85],colors=['cyan','yellow','orange','red'],linewidths=1.5)
ax0.clabel(cs,inline=True,fontsize=10,colors='white')
ax0.plot(OPT_LR,OPT_DO,'*',color='white',markersize=20,markeredgecolor='red',markeredgewidth=2,zorder=5)
ax0.set_xlabel('Learning Rate');ax0.set_ylabel('Dropout')
ax0.set_title('Fractal Prior (escape time) + Quality Contours\nWhite star = global optimum',fontsize=13,color='white')
ax0.tick_params(colors='white');ax0.set_facecolor('black')
plt.tight_layout()
plt.savefig('/data/workspace/fractal_prior.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ fractal_prior.png")

# ============================================================
# 3. 三种搜索策略
# ============================================================
BUDGET=60; N_REP=50

# --- RBF Kernel ---
def kernel(A,B,ls=0.15,sigma=1.0):
    D=np.sum(A**2,1)[:,None]+np.sum(B**2,1)[None,:]-2*A@B.T
    return sigma**2*np.exp(-D/(2*ls**2))

# --- 1. Random ---
def random_search(budget,seed):
    rng=np.random.RandomState(seed)
    best=0;hist=[]
    for i in range(budget):
        lr=rng.uniform(lr_min,lr_max);do=rng.uniform(do_min,do_max)
        v=quality(lr,do)
        best=max(best,v);hist.append(best)
    return np.array(hist)

# --- 2. Bayesian (GP-UCB) ---
def bayesian_search(budget,seed,init=5,kappa=2.0):
    rng=np.random.RandomState(seed)
    X=rng.uniform([lr_min,do_min],[lr_max,do_max],(init,2))
    y=np.array([quality(x[0],x[1]) for x in X])
    best=y.max();hist=[best]
    from scipy.linalg import cho_factor,cho_solve
    for i in range(budget-init):
        K=kernel(X,X)+1e-6*np.eye(len(X))
        L=cho_factor(K)
        cand=rng.uniform([lr_min,do_min],[lr_max,do_max],(2000,2))
        Ks=kernel(cand,X)
        mu=Ks@cho_solve(L,y-0.5)
        std=np.sqrt(np.maximum(1.0-np.einsum('ij,jk,ik->i',Ks,cho_solve(L,np.eye(len(X))),Ks),1e-10))
        idx=np.argmax(mu+kappa*std)
        x_new=cand[idx]
        tries=0
        while np.any(np.all(np.abs(X-x_new)<1e-8,axis=1)) and tries<50:
            x_new=rng.uniform([lr_min,do_min],[lr_max,do_max])
            tries+=1
        y_new=quality(x_new[0],x_new[1])
        X=np.vstack([X,x_new]);y=np.append(y,y_new)
        best=max(best,y_new);hist.append(best)
    while len(hist)<budget:hist.append(hist[-1])
    return np.array(hist[:budget])

# --- 3. Fractal-Guided ---
def fractal_guided(budget,seed,init=5):
    rng=np.random.RandomState(seed)
    # Phase 1: fractal-weighted init
    n_g=200
    lrs_g=np.linspace(lr_min,lr_max,n_g)
    dos_g=np.linspace(do_min,do_max,n_g)
    LG,DG=np.meshgrid(lrs_g,dos_g)
    F=np.array([[fractal_score(l,d) for l in lrs_g] for d in dos_g])
    prob=F**2;prob/=prob.sum()
    flat_idx=rng.choice(n_g**2,size=init,p=prob.ravel())
    X=np.column_stack([LG.ravel()[flat_idx],DG.ravel()[flat_idx]])
    y=np.array([quality(x[0],x[1]) for x in X])
    best=y.max();hist=[best]
    from scipy.linalg import cho_factor,cho_solve
    remain=budget-init
    for i in range(remain):
        K=kernel(X,X)+1e-6*np.eye(len(X))
        L=cho_factor(K)
        cand=rng.uniform([lr_min,do_min],[lr_max,do_max],(2000,2))
        Ks=kernel(cand,X)
        mu=Ks@cho_solve(L,y-0.5)
        std=np.sqrt(np.maximum(1.0-np.einsum('ij,jk,ik->i',Ks,cho_solve(L,np.eye(len(X))),Ks),1e-10))
        fc=np.array([fractal_score(c[0],c[1]) for c in cand])
        acq=mu+2.0*std+1.5*fc
        idx=np.argmax(acq)
        x_new=cand[idx]
        tries=0
        while np.any(np.all(np.abs(X-x_new)<1e-8,axis=1)) and tries<50:
            x_new=rng.uniform([lr_min,do_min],[lr_max,do_max])
            tries+=1
        y_new=quality(x_new[0],x_new[1])
        X=np.vstack([X,x_new]);y=np.append(y,y_new)
        best=max(best,y_new);hist.append(best)
    while len(hist)<budget:hist.append(hist[-1])
    return np.array(hist[:budget])

# ============================================================
# 4. 运行实验
# ============================================================
print(f"\n▶ Running experiments (3 methods x {N_REP} reps x {BUDGET} budget)...")
methods={'Random Search':random_search,'Bayesian Opt':bayesian_search,'Fractal-Guided':fractal_guided}
all_h={}
for name,func in methods.items():
    t0=time.time()
    hists=[func(BUDGET,1000+s) for s in range(N_REP)]
    all_h[name]=np.array(hists)
    print(f"  {name:20s}: {time.time()-t0:5.1f}s | final_mean={all_h[name][:,-1].mean():.4f}")

# Simple regret
regrets={n:OPT_VAL-all_h[n] for n in methods}

# ============================================================
# 5. 指标
# ============================================================
print("\n▶ Metrics:")
metrics={}
for n in methods:
    h=all_h[n];r=regrets[n]
    metrics[n]={'final_mean':float(h[:,-1].mean()),
                'final_median':float(np.median(h[:,-1])),
                'final_std':float(h[:,-1].std()),
                'regret_mean':float(r[:,-1].mean()),
                'regret_median':float(np.median(r[:,-1])),
                'sr_85':float(np.mean(h[:,-1]>=0.85)),
                'sr_80':float(np.mean(h[:,-1]>=0.80))}
    b80=[]
    for hh in h:
        idx=np.where(hh>=0.80)[0]
        b80.append(idx[0]+1 if len(idx)>0 else BUDGET)
    metrics[n]['budget_to_80']=float(np.mean(b80))

print(f"\n  {'Method':<20s} {'FinalMean':>10s} {'Regret':>10s} {'SR@0.85':>10s} {'SR@0.80':>10s} {'Bgt2@0.80':>10s}")
print(f"  {'-'*72}")
for n in methods:
    m=metrics[n]
    print(f"  {n:<20s} {m['final_mean']:>10.4f} {m['regret_mean']:>10.4f} {m['sr_85']:>10.0%} {m['sr_80']:>10.0%} {m['budget_to_80']:>10.1f}")

# ============================================================
# 6. 可视化
# ============================================================
print("\n▶ Plotting...")
colors={'Random Search':'#888888','Bayesian Opt':'#2196F3','Fractal-Guided':'#FF5722'}

# 图1: 收敛曲线
fig1,ax1=plt.subplots(figsize=(12,8),facecolor='black')
for n in methods:
    h=all_h[n];m=h.mean(0);s=h.std(0)
    ax1.plot(range(1,BUDGET+1),m,color=colors[n],lw=2.5,label=n)
    ax1.fill_between(range(1,BUDGET+1),m-s,m+s,color=colors[n],alpha=0.15)
ax1.axhline(OPT_VAL,color='white',ls='--',lw=1,alpha=0.5,label=f'Opt={OPT_VAL:.4f}')
ax1.set_xlabel('Evaluations');ax1.set_ylabel('Best val_accuracy')
ax1.set_title('Convergence: Who finds the best hyperparameters faster?',fontsize=15,color='white')
ax1.legend(fontsize=12,facecolor='black',edgecolor='white',labelcolor='white')
ax1.tick_params(colors='white');ax1.set_facecolor('#0a0a0a')
ax1.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/conv_curves.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ conv_curves.png")

# 图2: Regret
fig2,ax2=plt.subplots(figsize=(12,8),facecolor='black')
for n in methods:
    r=regrets[n]
    ax2.plot(range(1,BUDGET+1),r.mean(0),color=colors[n],lw=2.5,label=n)
    ax2.fill_between(range(1,BUDGET+1),r.mean(0)-r.std(0),r.mean(0)+r.std(0),color=colors[n],alpha=0.15)
ax2.set_xlabel('Evaluations');ax2.set_ylabel('Simple Regret')
ax2.set_title('Simple Regret: Lower = Better',fontsize=15,color='white')
ax2.legend(fontsize=12,facecolor='black',edgecolor='white',labelcolor='white')
ax2.tick_params(colors='white');ax2.set_facecolor('#0a0a0a')
ax2.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/regret_curves.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ regret_curves.png")

# 图3: 箱线图
fig3,ax3=plt.subplots(figsize=(10,8),facecolor='black')
bp=ax3.boxplot([all_h[n][:,-1] for n in methods],labels=list(methods.keys()),patch_artist=True)
for p,n in zip(bp['boxes'],methods):p.set_facecolor(colors[n]);p.set_alpha(0.7)
ax3.axhline(OPT_VAL,color='white',ls='--',lw=1,alpha=0.5)
ax3.set_ylabel('Final best val_accuracy')
ax3.set_title('Final Performance Distribution (50 repeats)',fontsize=15,color='white')
ax3.tick_params(colors='white');ax3.set_facecolor('#0a0a0a')
plt.tight_layout()
plt.savefig('/data/workspace/boxplot.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ boxplot.png")

# 图4: 综合海报
fig4,axes4=plt.subplots(2,2,figsize=(20,16),facecolor='black')
ax=axes4[0][0]
for n in methods:
    ax.plot(range(1,BUDGET+1),all_h[n].mean(0),color=colors[n],lw=2,label=n)
ax.set_title('Convergence');ax.legend();ax.tick_params(colors='white');ax.set_facecolor('#0a0a0a')

ax=axes4[0][1]
for n in methods:
    ax.plot(range(1,BUDGET+1),regrets[n].mean(0),color=colors[n],lw=2,label=n)
ax.set_title('Simple Regret');ax.legend();ax.tick_params(colors='white');ax.set_facecolor('#0a0a0a')

ax=axes4[1][0]
bp=ax.boxplot([all_h[n][:,-1] for n in methods],labels=list(methods.keys()),patch_artist=True)
for p,n in zip(bp['boxes'],methods):p.set_facecolor(colors[n]);p.set_alpha(0.7)
ax.set_title('Final Distribution');ax.tick_params(colors='white');ax.set_facecolor('#0a0a0a')

ax=axes4[1][1];ax.axis('off')
lines=[f"{'Method':<20s} | {'Mean':>8s} | {'Regret':>8s} | {'SR@.85':>8s}"]
lines.append(f"{'-'*52}")
for n in methods:
    m=metrics[n]
    lines.append(f"{n:<20s} | {m['final_mean']:>8.4f} | {m['regret_mean']:>8.4f} | {m['sr_85']:>8.0%}")
ax.text(0.05,0.95,'\n'.join(lines),transform=ax.transAxes,color='white',fontsize=13,
         verticalalignment='top',family='monospace')
ax.set_title('Summary Table',color='white')

fig4.suptitle('Hyperparameter Search: Random vs Bayesian vs Fractal-Guided\n'+
              f'lr∈[1e-4,0.1], dropout∈[0,0.5]  |  Budget={BUDGET}  |  {N_REP} repeats',
              fontsize=16,color='white',y=1.005)
plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig('/data/workspace/final_poster_search.png',dpi=130,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ final_poster_search.png")

# ============================================================
# 7. 保存
# ============================================================
results={'optimal':{'value':float(OPT_VAL),'lr':float(OPT_LR),'dropout':float(OPT_DO)},
          'metrics':metrics,
          'config':{'budget':BUDGET,'repeats':N_REP,'search_space':{'lr':[lr_min,lr_max],'dropout':[do_min,do_max]}}}
with open('/data/workspace/search_results.json','w') as f:json.dump(results,f,indent=2)

import subprocess
subprocess.run(['zip','-j','/data/workspace/search_exp.zip',
                '/data/workspace/fractal_prior.png',
                '/data/workspace/conv_curves.png',
                '/data/workspace/regret_curves.png',
                '/data/workspace/boxplot.png',
                '/data/workspace/final_poster_search.png',
                '/data/workspace/search_results.json',
                '/data/workspace/exp_search2.py'],check=True)

print(f"\n{'='*70}")
print("  RESULTS")
print(f"{'='*70}")
best_m=min(methods,key=lambda n:metrics[n]['regret_mean'])
print(f"\n  Best method (by mean regret): {best_m}")
print(f"\n  {'Method':<20s} {'FinalMean':>10s} {'Regret':>10s} {'SR@.85':>10s}")
print(f"  {'-'*52}")
for n in methods:
    m=metrics[n]
    flag="  <-- BEST" if n==best_m else ""
    print(f"  {n:<20s} {m['final_mean']:>10.4f} {m['regret_mean']:>10.4f} {m['sr_85']:>10.0%}{flag}")

print(f"\n  Files: search_exp.zip")
print("  ALL DONE!")
