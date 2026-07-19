#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF6 拓扑交错瓦片 — c^α引擎 + v1 精确视窗 + rot90 尖朝上

着色: u=floor(θ·N) + v=floor(pot/Δ) → (u+v)%4 → 4级灰度镶嵌
视口: Re[-1.833,4.500] Im[-2.124,2.124] → rot90 → 尖朝上
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.5
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1.0
RAY_DIV=32; POT_STEP=0.08; K=4

def compute(x_mn,x_mx,y_mn,y_mx,w,h):
    x=np.linspace(x_mn,x_mx,w); y=np.linspace(y_mn,y_mx,h)
    X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
    eps=1e-12; abs_c=np.abs(c_orig); safe=abs_c>eps
    c_eff=np.zeros_like(c_orig,dtype=np.complex128)
    c_eff[safe]=(abs_c[safe]**ALPHA)*np.exp(1j*ALPHA*np.angle(c_orig[safe]))
    c_eff[~safe]=1e6+0j
    z=np.zeros_like(c_eff,dtype=np.complex128)
    escape=np.full(c_eff.shape,MAXITER,dtype=np.float64)
    alive=np.ones(c_eff.shape,dtype=bool); zf=np.zeros_like(c_eff,dtype=np.complex128)
    for n in range(MAXITER):
        if not alive.any(): break
        z[alive]=z[alive]**2+c_eff[alive]; zf[alive]=z[alive].copy()
        div=np.abs(z)>BAILOUT; escape[div&alive]=n; alive&=~div
    interior=escape>=MAXITER
    az=np.abs(zf)+1e-12; smooth=escape-np.log2(np.maximum(np.log2(az),1e-12))
    smooth[interior]=0
    ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
    nc=np.minimum(escape,20).astype(np.float64); er=(ang/np.power(2.0,nc))%1.0; er[interior]=0
    return np.rot90(smooth,k=3),np.rot90(er,k=3),np.rot90(interior,k=3)

if __name__=="__main__":
    pot,er,interior=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,W,H)
    h,w=pot.shape; ext=~interior
    ui=np.floor(er*RAY_DIV).astype(int)
    vi=np.floor(np.where(ext,pot,0)/POT_STEP).astype(int)
    cg=(ui+vi)%K
    g=[0.0,0.30,0.55,0.80]
    img=np.ones((h,w,3))
    for ci,gv in enumerate(g): img[ext&(cg==ci)]=gv
    img[interior]=1.0
    fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=100)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
    ax.axis('off'); plt.tight_layout(pad=0)
    plt.savefig(os.path.join(od,"UF6_拓扑交错瓦片.png"),dpi=200,bbox_inches='tight',facecolor='white'); plt.close()
    print(f"UF6: ext={ext.sum()}px done")
