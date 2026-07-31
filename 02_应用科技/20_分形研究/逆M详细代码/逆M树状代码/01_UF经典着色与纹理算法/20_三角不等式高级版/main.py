#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF20 三角不等式高级版 — 3种TIA平均模式"""
import numpy as np, matplotlib.pyplot as plt, os, matplotlib
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1
MODE=0  # 0=算术, 1=对数几何, 2=调和
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);z_prev=np.zeros_like(ce)
tia=np.zeros(ce.shape);cnt=np.zeros(ce.shape,int)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy()
    z_prev[idx]=za;za=za**2+ca;z[idx]=za
    d=np.abs(z-z_prev);az=np.abs(z)+1e-12;dz_idx=az[idx]
    if MODE==0: tia[idx]+=d[idx]/dz_idx
    elif MODE==1: tia[idx]+=np.log(1+d[idx]/dz_idx)
    else: tia[idx]+=dz_idx/(d[idx]+1e-12)
    cnt[idx]+=1;alive&=~(np.abs(z)>BL)
avg=np.where(cnt>0,tia/cnt,0);avg=np.rot90(avg,k=3)
sv=avg[avg>0];lo,hi=np.percentile(sv,[2,98]) if len(sv)>0 else (0,1)
norm=np.clip((avg-lo)/(hi-lo+1e-10),0,1)
cmap=matplotlib.colormaps['viridis'];img=cmap(norm)[...,:3]
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF20_三角不等式高级版.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print("UF20: TIA Advanced done")
