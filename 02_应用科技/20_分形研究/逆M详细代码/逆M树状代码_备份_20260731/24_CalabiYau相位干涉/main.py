#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF24 Calabi-Yau满填螺旋 — 3层螺旋连续填充, 无黑格间隙, Re轴朝上, XY等比

使用 K值嵌套螺旋的虚部→色板映射, 每像素都有颜色, 无空隙
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

r=np.abs(co); theta=np.angle(co); DECAY_SIGMA=10.0
decay=1-np.exp(-r/DECAY_SIGMA)

# 3层螺旋叠加 → 合成纹理值(连续填充, 无间隙)
texture=np.zeros((H,W),dtype=np.float32)
for K,weight in [(0.6,0.5),(1.5,1.0),(3.0,0.3)]:
    z_cy=np.exp(1j*theta+np.log(r+1e-6)*K)*decay
    texture+=np.real(z_cy)*weight+np.imag(z_cy)*weight*0.5

# 归一化→连续色板(暖色螺旋)
t_min=texture[interior].min(); t_max=texture[interior].max()
tex_norm=np.zeros_like(texture)
if t_max>t_min: tex_norm[interior]=(texture[interior]-t_min)/(t_max-t_min)

# 暖色调映射: 蓝底→金→白
img=np.zeros((H,W,3))
R=np.clip(0.05+0.85*tex_norm,0,1)
G=np.clip(0.08+0.65*tex_norm+0.15*np.sin(np.pi*tex_norm*2),0,1)
B=np.clip(0.20-0.10*tex_norm+0.15*np.sin(np.pi*tex_norm*1.5),0,1)
img[interior]=np.stack([R[interior],G[interior],B[interior]],axis=-1)
img[ext]=[0.03,0.06,0.18]

# DEM金边
dem=np.zeros_like(co); dem[ext]=(np.log(np.abs(z[ext])**2)*np.abs(z[ext])/(np.abs(dz[ext])+1e-12))
dem_norm=np.clip(dem/(dem.max()+1e-12),0,1); glow=ext&(dem_norm>0.3)
if glow.any():
    dn=dem_norm[glow]; img[glow]=np.stack([0.9*dn+0.1,0.6*dn+0.2,0.1*dn+0.02],axis=-1)

out=os.path.join(od,'UF24_CY多层螺旋_3色叠加.png')
plt.imsave(out,np.rot90(img,k=1),dpi=150)
print(f'UF24 CY-Fill: ext={ext.sum()} -> {out}')
