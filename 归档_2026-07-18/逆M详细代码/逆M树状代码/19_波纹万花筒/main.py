#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF19 波纹万花筒 (Ripples/Kaleidoscope) — sin/polar 波纹扭曲"""
import numpy as np, matplotlib.pyplot as plt, os, matplotlib
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);zf=np.zeros_like(ce)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca;z[idx]=za;zf[idx]=za
    alive&=~(np.abs(z)>BL)
# 波纹: sin(|z|*freq) + sin(arg(z)*freq2)
az=np.abs(zf)+1e-12;ag=np.angle(zf)
ripple=np.sin(az*5)*np.cos(ag*8)
ripple[alive]=0;ripple=np.rot90(ripple,k=3)
sv=ripple[~np.isnan(ripple)&(rip>0)] if 'rip' in dir() else np.abs(ripple[~np.isnan(ripple)])
# 简化: 用 ripples 绝对值
rip=np.abs(ripple)
cmap=matplotlib.colormaps['twilight_shifted'];img=cmap(rip)[...,:3]
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF19_波纹万花筒.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print("UF19: Ripples done")
