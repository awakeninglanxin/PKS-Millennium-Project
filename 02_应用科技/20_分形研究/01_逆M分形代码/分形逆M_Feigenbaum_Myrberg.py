#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M变换 #6: c = cf - 1/p — Feigenbaum点(Myrberg点)反演

平移 cf=-1.401155 把倍周期累积点移到原点后反演.
结果: 原本缩到极小的周期泡链被放大成等大环, 7个双曲分支清晰可见.
GitHub参考: "one can see 7 hyperbolic components for periods 2^0..2^6, each has the same size"
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

CF=-1.401155  # Feigenbaum/Myrberg点
# 视窗 (GitHub: center=1.33, radius=400.7, aspect=2.0)
CENTER=1.33; R=400.7; ASP=2.0
R0=CENTER-R*ASP; R1=CENTER+R*ASP; I0=-R; I1=R
W=1800; H=int(W*(I1-I0)/(R1-R0)); MI=500; BL=50

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y

# c = cf - 1/p
sf=np.abs(co)>1e-12; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=CF - 1.0/co[sf]; ce[~sf]=1e6+CF

z=np.zeros_like(ce); dz=np.zeros_like(ce)
alive=np.ones(ce.shape,bool)

for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive)
    za=z[idx].copy(); ca=ce[idx].copy(); dza=dz[idx].copy()
    dza=2*za*dza+1; za=za**2+ca
    z[idx]=za; dz[idx]=dza
    escaped_full=np.zeros(ce.shape,bool)
    escaped_full[idx]=(za.real**2+za.imag**2>BL**2)
    alive&=~escaped_full

interior=~alive; ext=alive

pot=np.zeros(ce.shape); pot[ext]=(np.log(np.abs(z[ext])**2)-np.log(2))/np.log(2)
vmax=np.percentile(pot[ext],98)
img=np.zeros((H,W,3))
norm=np.clip(pot[ext]/vmax,0,1)
img[ext]=plt.cm.viridis(norm)[...,:3]
img[~ext]=[0.02,0.02,0.08]

out=os.path.join(od,'逆M_Feigenbaum.png')
plt.imsave(out,np.rot90(img,k=3),dpi=150)
print(f'Feigenbaum: ext={ext.sum()}, interior={interior.sum()} -> {out}')
