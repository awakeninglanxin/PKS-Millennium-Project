#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF1 二分棋盘格素描 — 旧版(同心辐射环) — 已归档保留

此版本使用 pot/POT_STEP 双维度棋盘，会产生大量同心辐射环(bullseye)。
新版 main.py 已去掉同心环，改用角度场阴阳分界线(树状分岔线)。
本文件仅供对照/回溯使用，不要覆盖 main.py。
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0; B=-4/3; H=1.6242719100; M=0.5
RE_MIN,RE_MAX=B-M,TIP+M; IM_MIN,IM_MAX=-H-M,H+M
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1; RAY_DIV=64; POT_STEP=0.12

class Engine:
    """UF5已验证的c^α引擎"""
    @staticmethod
    def compute(x_mn,x_mx,y_mn,y_mx,w,h):
        x=np.linspace(x_mn,x_mx,w); y=np.linspace(y_mn,y_mx,h)
        X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
        eps=1e-12; safe=np.abs(c_orig)>eps
        ce=np.zeros_like(c_orig,dtype=np.complex128)
        ce[safe]=(np.abs(c_orig[safe])**ALPHA)*np.exp(1j*ALPHA*np.angle(c_orig[safe]))
        ce[~safe]=1e6+0j
        z=np.zeros_like(ce,dtype=np.complex128)
        alive=np.ones(ce.shape,dtype=bool)
        zf=np.zeros_like(ce,dtype=np.complex128)
        for n in range(MAXITER):
            if not alive.any(): break
            z[alive]=z[alive]**2+ce[alive]; zf[alive]=z[alive].copy()
            alive&=~(np.abs(z)>BAILOUT)
        interior=alive
        az=np.abs(zf)+1e-12; sm=MAXITER-1-np.log2(np.maximum(np.log2(az),1e-12)); sm[interior]=0
        ang=np.arctan2(zf.imag,zf.real)/(2*np.pi); er=(ang/np.power(2.0,np.minimum(MAXITER-1-np.log2(np.maximum(np.log2(az),1e-12)),20)))%1.0
        e2=np.where(~interior,sm,0.0)
        sm2=np.where(~interior,sm,0.0)
        ang2=np.where(~interior,ang,0.0)
        er2=(ang2/np.power(2.0,np.minimum(np.where(~interior,MAXITER-1,0).astype(float),20)))%1.0
        er2[interior]=0; sm2[interior]=0
        return np.rot90(sm2,k=3),np.rot90(er2,k=3),np.rot90(interior,k=3)

pot,er,interior=Engine.compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,W,H)
h,w=pot.shape; ext=~interior
rz=np.floor(er*RAY_DIV).astype(int); pz=np.floor(pot/POT_STEP).astype(int)
cb=((rz%2==0)==(pz%2==0))&ext
img=np.ones((h,w,3)); img[cb]=0; img[interior]=1
fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=150)
ax.set_facecolor('white'); fig.patch.set_facecolor('white')
ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF1_二分棋盘格素描_旧版_同心环.png"),dpi=200,bbox_inches='tight',facecolor='white'); plt.close()
print(f"UF1(old, rings): ext={ext.sum()} done")
