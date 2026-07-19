#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M变换 #7: c = cf + e^p — 指数映射 (Exponential Map)

围绕Feigenbaum点做指数映射.
将倍周期级联(period 1,2,4,8,16,32,64)拉平成等间距分布.
GitHub: "one can see 7 hyperbolic components, each has the same size"
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

CF=-1.401155
# 视窗 (GitHub: xMin=-8.9, xMax=0.7, yMin=-2.4, yMax=2.4)
R0=-8.9; R1=0.7; I0=-2.4; I1=2.4
W=1800; H=int(W*(I1-I0)/(R1-R0)); MI=500; BL=50

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y

# c = cf + e^p
ce=CF + np.exp(co)

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
img[ext]=plt.cm.magma(norm)[...,:3]
img[~ext]=[0.02,0.02,0.08]

out=os.path.join(od,'逆M_指数映射_Feigenbaum.png')
plt.imsave(out,img,dpi=150)
print(f'Exponential Map: ext={ext.sum()} -> {out}')
