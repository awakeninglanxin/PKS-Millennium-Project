#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M变换 #4 (修复版): c = -2.0 + 1/p — 标准M左端点平移反演

修复: 原版视窗太大(R=5)导致ext太少, 改用GitHub参数+加大迭代次数.
GitHub实测: "Mandelbrot Set (in the 1/(mu-2) plane): x∈[-2.33,-0.17], y∈[-0.94,0.94]"
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

# 缩小视窗至GitHub实测范围
R0=-2.5; R1=0.0; I0=-1.2; I1=1.2
W=1200; H=int(W*(I1-I0)/(R1-R0)); MI=500; BL=50

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y

sf=np.abs(co)>1e-12; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=-2.0 + 1.0/co[sf]; ce[~sf]=1e6-2.0

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
if ext.any():
    norm=np.clip(pot[ext]/max(vmax,1e-6),0,1)
    img[ext]=plt.cm.inferno(norm)[...,:3]
img[~ext]=[0.02,0.02,0.08]

out=os.path.join(od,'逆M_kneg2_反天线_v2.png')
plt.imsave(out,np.rot90(img,k=3),dpi=150)
print(f'k=-2 v2: ext={ext.sum()}, interior={interior.sum()} -> {out}')
