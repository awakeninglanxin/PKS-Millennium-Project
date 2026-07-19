#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF23 Calabi-Yau螺旋臂 — exp(iθ+ln(r)·K) 星系旋臂, Re轴朝上, XY等比

K=1.5标准双曲螺旋, K=3.0快速多臂, K=5.0极密星系旋臂
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
ASP=(R1-R0)/(I1-I0); W=2400; H=max(int(W/ASP),1); MI=200; BL=50; A=-1

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y
eps=1e-12; sf=np.abs(co)>eps; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf])); ce[~sf]=1e6
z=np.zeros_like(ce); dz=np.zeros_like(ce); alive=np.ones(ce.shape,bool)
for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive); za=z[idx].copy(); ca=ce[idx].copy(); dza=dz[idx].copy()
    dza=2*za*dza+1; za=za**2+ca; z[idx]=za; dz[idx]=dza
    escaped_full=np.zeros(ce.shape,bool)
    escaped_full[idx]=(za.real**2+za.imag**2>BL**2); alive&=~escaped_full
interior=~alive; ext=alive

# CY螺旋坐标
SPIRAL_K=1.5; DECAY_SIGMA=8.0; N_Q=128; M_Q=64
r=np.abs(co); theta=np.angle(co)
z_cy=np.exp(1j*theta+np.log(r+1e-6)*SPIRAL_K); decay=1-np.exp(-r/DECAY_SIGMA); z_cy*=decay
z_max=np.max(np.abs(z_cy))+1e-6; u=np.real(z_cy)/z_max; v=np.imag(z_cy)/z_max
u_idx=np.floor(u*N_Q).astype(int); v_idx=np.floor(v*M_Q).astype(int)
chess=((u_idx%2==0)!=(v_idx%2==0))&interior

BG=[0.03,0.06,0.18]; LIGHT=[0.78,0.84,0.96]; DARK=[0.12,0.18,0.45]
img=np.full((H,W,3),BG); img[chess]=LIGHT; img[interior&~chess]=DARK; img[ext]=BG

# DEM金边
dem=np.zeros_like(co); dem[ext]=(np.log(np.abs(z[ext])**2)*np.abs(z[ext])/(np.abs(dz[ext])+1e-12))
dem_norm=np.clip(dem/(dem.max()+1e-12),0,1); glow=ext&(dem_norm>0.3)
if glow.any():
    dn=dem_norm[glow]; img[glow]=np.stack([0.9*dn+0.1,0.6*dn+0.2,0.1*dn+0.02],axis=-1)

out=os.path.join(od,'UF23_CY螺旋臂_K1.5.png')
plt.imsave(out,np.rot90(img,k=1),dpi=150)
print(f'UF23 CY-Spiral K={SPIRAL_K}: ext={ext.sum()} -> {out}')
