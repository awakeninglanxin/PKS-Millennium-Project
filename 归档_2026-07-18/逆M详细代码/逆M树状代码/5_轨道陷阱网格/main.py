#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF5 轨道陷阱网格 — c^α引擎 + v1 精确视窗 + rot90 尖朝上

轨道陷阱: 追踪 min(|Re(z)|,|Im(z)|) → sin映射 → 灰度网格
视口: Re[-1.833,4.500] Im[-2.124,2.124] → rot90 → 尖朝上
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.5
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1.0

def compute(x_mn,x_mx,y_mn,y_mx,w,h):
    x=np.linspace(x_mn,x_mx,w); y=np.linspace(y_mn,y_mx,h)
    X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
    eps=1e-12; abs_c=np.abs(c_orig); safe=abs_c>eps
    c_eff=np.zeros_like(c_orig,dtype=np.complex128)
    c_eff[safe]=(abs_c[safe]**ALPHA)*np.exp(1j*ALPHA*np.angle(c_orig[safe]))
    c_eff[~safe]=1e6+0j
    z=np.zeros_like(c_eff,dtype=np.complex128)
    alive=np.ones(c_eff.shape,dtype=bool)
    mtd=np.full(c_eff.shape,1e10)
    for n in range(MAXITER):
        if not alive.any(): break
        z[alive]=z[alive]**2+c_eff[alive]
        gd=np.minimum(np.abs(z.real),np.abs(z.imag)); mtd=np.minimum(mtd,gd)
        alive&=~(np.abs(z)>BAILOUT)
    mtd[alive]=0.5  # interior→中灰
    # rot90(k=3)→尖朝上
    return np.rot90(mtd,k=3),np.rot90(~alive,k=3)

if __name__=="__main__":
    mtd,escaped=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,W,H)
    h,w=mtd.shape
    tg=1-np.clip(mtd*2.5,0,1)
    img=np.ones((h,w,3))
    for c in range(3): img[:,:,c]=tg
    fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=100)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
    ax.axis('off'); plt.tight_layout(pad=0)
    plt.savefig(os.path.join(od,"UF5_轨道陷阱网格.png"),dpi=200,bbox_inches='tight',facecolor='white'); plt.close()
    print(f"UF5: esc={escaped.sum()}px done")
