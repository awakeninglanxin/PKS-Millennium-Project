#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF9 光照效果 (Lighting) — 由距离场计算法线, 3D漫反射

正M: 集合外部逃逸 → 法线朝外 → 3D光照
逆M: 水滴内部逃逸 → 法线朝内壁 → 3D光照

原理: 用 DEM 距离场梯度做法线, 定向光源产生浮雕感
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import sobel
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=200;BL=50;A=-1
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);dz=np.zeros_like(ce);alive=np.ones(ce.shape,bool)
for i in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy()
    dza=dz[idx].copy();dza=2*za*dza+1;za=za**2+ca
    z[idx]=za;dz[idx]=dza;alive&=~(z.real**2+z.imag**2>BL**2)
zm=np.sqrt(z.real**2+z.imag**2+1e-30);dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(zm*zm+1e-30)*zm/(dzm+1e-30);d[alive]=1e10
# Sobel梯度 → 法线 → 光源 (从左上角打光)
gx=sobel(d,axis=1);gy=sobel(d,axis=0)
gm=np.sqrt(gx**2+gy**2+1e-10);nx=-gx/gm;ny=-gy/gm
lx,ly=0.5,-1.0;ln=np.sqrt(lx*lx+ly*ly);lx/=ln;ly/=ln
shade=np.clip(nx*lx+ny*ly,0,1)
shade[alive]=0
shade=np.rot90(shade,k=3)
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(shade,extent=[I0,I1,R0,R1],origin='lower',cmap='gray')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF9_光照效果.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print(f"UF9: lighting done")
