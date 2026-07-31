"""vShape 2D heatmap: scan a∈[0.3,2.0], b∈[0.02,0.5] @ N=5e7"""
import cupy as cp, numpy as np, time, csv
N=50_000_000;tp=100  # fewer t-points for speed
t_arr=cp.linspace(10,80,tp,cp.float64)
print(f"vShape heatmap N=5e7 {tp}t-points",flush=True)
s=np.ones(N+1,bool);s[:2]=False
for i in range(2,int(N**0.5)+1):
    if s[i]:s[i*i::i]=False
tot=np.ones(N+1,bool)
for d in[2,3,5]:tot[d::d]=False
spf=np.zeros(N+1,np.int32);pr=[]
for i in range(2,N+1):
    if spf[i]==0:spf[i]=i;pr.append(i)
    for p in pr:
        if p>spf[i]or i*p>N:break;spf[i*p]=p
pc=np.zeros(N+1,bool);pc[pr]=True
def pp(n):
    if n<=1:return False
    p=spf[n]
    while n%p==0:n//=p
    return n==1
pm=np.zeros(N+1,bool);pkm=np.zeros(N+1,bool)
for n in range(2,N+1):
    if tot[n]:
        if pc[n]:pm[n]=True
        elif pp(n):pkm[n]=True
npi=pm.nonzero()[0].astype(np.float64)
npk=pkm.nonzero()[0].astype(np.float64)
ncp=cp.asarray(npi);ncpk=cp.asarray(npk);Nf=float(N)
lnp=cp.log(ncp);isq=1/cp.sqrt(ncp);lnpk=cp.log(ncpk);isqk=1/cp.sqrt(ncpk)
print(f"  primes={len(npi)} pk={len(npk)}",flush=True)

t_all=time.time();res=[]
for a in[0.3,0.5,0.8,1.0,1.2,1.5,1.8,2.0]:
 for b in[0.02,0.05,0.10,0.15,0.20,0.30,0.50]:
  rp=ncp/Nf;rpk=ncpk/Nf
  phi=cp.exp(-b*rp**a)*rp**a;phik=cp.exp(-b*rpk**a)*rpk**a
  Kp=cp.zeros(tp);Kpk=cp.zeros(tp);B=20000
  for i in range(0,len(npi),B):
   e=min(i+B,len(npi))
   for ti in range(tp):Kp[ti]+=float(cp.sum(cp.cos(t_arr[ti]*lnp[i:e])*isq[i:e]*phi[i:e]))
  for i in range(0,len(npk),B):
   e=min(i+B,len(npk))
   for ti in range(tp):Kpk[ti]+=float(cp.sum(cp.cos(t_arr[ti]*lnpk[i:e])*isqk[i:e]*phik[i:e]))
  vp=float(cp.var(Kp));vpk=float(cp.var(Kpk))
  r=vp/max(vpk,1e-15)
  res.append((a,b,r))
  print(f"  a={a:.1f} b={b:.2f} ratio={r:.0f}",flush=True)
t1=time.time()-t_all
best=max(res,key=lambda x:x[2])
print(f"Best: a={best[0]} b={best[1]} ratio={best[2]:.0f} ({t1:.0f}s)")

with open("/root/vshape_heatmap.csv","w") as f:
    w=csv.writer(f);w.writerow(["a","b","ratio"])
    for a,b,r in res:w.writerow([a,b,f"{r:.0f}"])
