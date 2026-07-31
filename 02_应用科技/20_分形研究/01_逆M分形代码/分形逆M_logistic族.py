#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M变换 #8-10: Logistic族 — m*z*(1-z) 及其反演

Logistic映射是Mandelbrot的等价族: z²+c ↔ mz(1-z), 其中 m=c+0.5.
三种变体:
  lambda标准:  m = p           (直接λ平面)
  lambda倒数:  m = 1/p         (λ平面反演)
  lambda_1+倒: m = 1 + 1/p     (平移1后反演)

参考: GitHub adammaj1, λ平面Mandelbrot集.
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

MODE='lambda_1inv'  # 'lambda_std' | 'lambda_inv' | 'lambda_1inv'

# 视窗
if MODE=='lambda_std':
    CENTER=1.0; R=3.2; ASP=2.0
else:
    CENTER=0.0; R=1.12; ASP=2.0
R0=CENTER-R*ASP; R1=CENTER+R*ASP; I0=-R; I1=R
W=1800; H=int(W*(I1-I0)/(R1-R0)); MI=200; BL=50

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y

# 计算参数 m
if MODE=='lambda_std':
    m=co  # m = p (直接)
elif MODE=='lambda_inv':
    m=np.zeros_like(co,dtype=np.complex128)
    sf=np.abs(co)>1e-12; m[sf]=1.0/co[sf]; m[~sf]=1e6
else:  # lambda_1inv
    m=np.zeros_like(co,dtype=np.complex128)
    sf=np.abs(co)>1e-12; m[sf]=1.0+1.0/co[sf]; m[~sf]=1e6+1.0

# Logistic迭代: z = m*z*(1-z), z0=0.5 (logistic的临界点)
z=np.full(co.shape,0.5+0j); dz=np.full(co.shape,1.0+0j)
alive=np.ones(co.shape,bool)

for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive)
    za=z[idx].copy(); ma=m[idx].copy(); dza=dz[idx].copy()
    # dz更新: d/dz[m*z*(1-z)] = m*(1-2z)
    dza=ma*(1-2*za)*dza
    za=ma*za*(1-za)
    z[idx]=za; dz[idx]=dza
    escaped_full=np.zeros(co.shape,bool)
    escaped_full[idx]=(za.real**2+za.imag**2>BL**2)
    alive&=~escaped_full

interior=~alive; ext=alive

pot=np.zeros(co.shape); pot[ext]=(np.log(np.abs(z[ext])**2)-np.log(2))/np.log(2)
vmax=np.percentile(pot[ext],98)
img=np.zeros((H,W,3))
norm=np.clip(pot[ext]/vmax,0,1)
img[ext]=plt.cm.plasma(norm)[...,:3]
img[~ext]=[0.02,0.02,0.08]

out=os.path.join(od,f'逆M_logistic_{MODE}.png')
plt.imsave(out,np.rot90(img,k=3),dpi=150)
print(f'Logistic {MODE}: ext={ext.sum()} -> {out}')
