#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF1 二分棋盘格 — 取模势能去同心环

原: pz = floor(pot/0.12) → 全量程 → 密集同心环
现: pz = floor((pot%mod)/step) → 截断取模 → 保留树杈纹理, 无可见环
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0; B=-4/3; H=1.6242719100; M=0.5
RE_MIN,RE_MAX=B-M,TIP+M; IM_MIN,IM_MAX=-H-M,H+M
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1; RAY_DIV=64; POT_MOD=1.0; POT_STEP=0.5

x=np.linspace(RE_MIN,RE_MAX,W); y=np.linspace(IM_MIN,IM_MAX,H); X,Y=np.meshgrid(x,y); co=X+1j*Y
eps=1e-12; ce=np.where(np.abs(co)>eps,(np.abs(co)**ALPHA)*np.exp(1j*ALPHA*np.angle(co)),1e6+0j)
z=np.zeros_like(ce); alive=np.ones(ce.shape,bool); zf=np.zeros_like(ce)
for n in range(MAXITER):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca;z[idx]=za;zf[idx]=za
    alive&=~(np.abs(z)>BAILOUT)
interior=np.rot90(alive,k=3)
az=np.abs(zf)+1e-12;sm=np.where(~alive,MAXITER-1-np.log2(np.maximum(np.log2(az),1e-12)),0.0)
ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
er=(ang/np.power(2.0,np.where(~alive,MAXITER-1,0).astype(float)))%1.0;er[alive]=0
sm=np.rot90(sm,k=3);er=np.rot90(er,k=3);ext=~interior;h,w=er.shape
rz=np.floor(er*RAY_DIV).astype(int)
# ★ 取模势能: 只取 pot%MOD 范围, 消除远距离环累积
pz=np.floor((sm%POT_MOD)/POT_STEP).astype(int)
cb=((rz%2==0)==(pz%2==0))&ext
img=np.ones((h,w,3));img[cb]=0;img[interior]=1
fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=150)
ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF1_去环棋盘格.png"),dpi=200,bbox_inches='tight',facecolor='white');plt.close()
print("UF1 de-ring done")
