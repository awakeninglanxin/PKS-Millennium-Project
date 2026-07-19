#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF10 浮雕效果 (Emboss) — Sobel浮雕 + c^α引擎"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import sobel
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);zf=np.zeros_like(ce)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca
    z[idx]=za;zf[idx]=za;alive&=~(np.abs(z)>BL)
az=np.abs(zf)+1e-12;sm=np.where(~alive,MI-1-np.log2(np.maximum(np.log2(az),1e-12)),0.0)
sm[alive]=0
# Sobel浮雕
gx=sobel(sm,axis=1);gy=sobel(sm,axis=0)
emboss=np.clip(gx+gy,0,1)
emboss[alive]=0
emboss=np.rot90(emboss,k=3)
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(emboss,extent=[I0,I1,R0,R1],origin='lower',cmap='gray')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF10_浮雕效果.png"),dpi=200,bbox_inches='tight',facecolor='white');plt.close()
print(f"UF10: emboss done")
