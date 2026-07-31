#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M变换 #5: c = 0.25 + 1/p — 心形→抛物线 (k=0.25平移后反演)

Möbius反演 c→1/c 前先平移 k=0.25, 使心形尖点 c=0.25→0→∞.
结果: 心形变为抛物线外部, 尖点被推到无穷远.
Albert Chern: "心形是抛物线的Möbius反演."
"""
import numpy as np, matplotlib.pyplot as plt, os, sys
od=os.path.dirname(os.path.abspath(__file__))

# 视窗 (参照GitHub: center=4.0, radius=5.0, aspect=2.0)
CENTER=4.0; R=5.0; ASP=2.0
R0=CENTER-R*ASP; R1=CENTER+R*ASP; I0=-R; I1=R
W=1800; H=int(W*(I1-I0)/(R1-R0)); MI=200; BL=50

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y

# c = 0.25 + 1/p (平移0.25后反演)
sf=np.abs(co)>1e-12; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=0.25 + 1.0/co[sf]; ce[~sf]=1e6+0.25

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

# 势能着色
pot=np.zeros(ce.shape); pot[ext]=(np.log(np.abs(z[ext])**2)-np.log(2))/np.log(2)
vmax=np.percentile(pot[ext],98)
img=np.zeros((H,W,3))
norm=np.clip(pot[ext]/vmax,0,1)
cmap=plt.cm.plasma
img[ext]=cmap(norm)[...,:3]
img[~ext]=[0.02,0.02,0.08]

out=os.path.join(od,'逆M_抛物线_k025.png')
plt.imsave(out,np.rot90(img,k=3),dpi=150)
print(f'Parabola k=0.25: ext={ext.sum()}, interior={interior.sum()} -> {out}')
