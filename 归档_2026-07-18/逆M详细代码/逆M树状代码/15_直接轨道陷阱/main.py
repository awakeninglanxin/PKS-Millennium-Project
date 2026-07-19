#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF15 直接轨道陷阱 — 追踪min|z|"""
import numpy as np, matplotlib.pyplot as plt, os, matplotlib
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=120;BL=50;A=-1
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool)
trap=np.full(ce.shape,1e10)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca;z[idx]=za
    trap=np.minimum(trap,np.abs(z));alive&=~(np.abs(z)>BL)
trap[alive]=trap[alive].max() if alive.any() else 1
t=np.rot90(trap,k=3)
sv=t[t<10]
if len(sv)>10:
    lo,hi=np.percentile(sv,[5,95])
    norm=np.clip((t-lo)/(hi-lo+1e-10),0,1)
else:
    norm=np.clip(t/5,0,1)
cmap=matplotlib.colormaps['inferno'];img=cmap(norm)[...,:3]
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF15_直接轨道陷阱.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print(f"UF15: trap∈[{trap.min():.3f},{trap.max():.3f}] done")
