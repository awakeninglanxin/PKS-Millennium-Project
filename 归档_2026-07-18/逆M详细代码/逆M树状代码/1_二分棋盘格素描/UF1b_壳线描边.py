#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v6 — 二分棋盘格黑白素描版

基于 v4，去掉所有色阶渐变和火焰过渡，纯黑白 XOR 棋盘格。
"""

import numpy as np
import matplotlib.pyplot as plt
import os

TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.5
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
WIDTH=2400; HEIGHT=int(WIDTH*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
RAY_DIVISIONS=64; POT_STEP=0.12; MAX_ITER=300; BAILOUT=128

def generate_outline(n_pts=6000):
    eps=1e-10; theta=np.linspace(eps,2*np.pi-eps,n_pts)
    c=0.5*np.exp(1j*theta)-0.25*np.exp(2j*theta); inv_c=1.0/c
    return -inv_c.imag,inv_c.real

def compute(x_min,x_max,y_min,y_max,w,h,max_iter,bailout):
    x=np.linspace(x_min,x_max,w); y=np.linspace(y_min,y_max,h)
    X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
    safe=np.abs(c_orig)>1e-12
    c_eff=np.zeros_like(c_orig,dtype=np.complex128)
    c_eff[safe]=1.0/c_orig[safe]; c_eff[~safe]=1e6
    z=np.zeros_like(c_eff,dtype=np.complex128)
    e=np.full(c_eff.shape,max_iter,dtype=np.float64)
    a=np.ones(c_eff.shape,dtype=bool); zf=np.zeros_like(c_eff,dtype=np.complex128)
    for i in range(max_iter):
        if not a.any(): break
        z[a]=z[a]**2+c_eff[a]; zf[a]=z[a].copy()
        d=np.abs(z)>bailout; e[d&a]=i; a&=~d
    interior=e>=max_iter
    interior|=(np.abs(c_orig)<0.03)  # 去除原点葫芦残影
    ms=zf.real**2+zf.imag**2+1e-30
    pot=np.log(ms)/(2.0**e); pot[interior]=0
    ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
    nc=np.minimum(e,25).astype(np.float64)
    er=(ang/np.power(2.0,nc))%1.0; er[interior]=0
    return np.rot90(pot,k=3),np.rot90(er,k=3),np.rot90(interior,k=3)

if __name__=="__main__":
    from scipy.ndimage import sobel,binary_dilation,binary_opening
    out_dir=os.path.dirname(os.path.abspath(__file__))
    print(f"v6 黑白素描版 计算中...")
    pot,er,interior=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,WIDTH,HEIGHT,MAX_ITER,BAILOUT)
    h,w=pot.shape; ext=~interior
    rz=np.floor(er*RAY_DIVISIONS).astype(int); re=(rz%2==0)
    pz=np.floor(pot/POT_STEP).astype(int); pe=(pz%2==0)
    cb=(re==pe)&ext

    img=np.ones((h,w,3))
    img[cb]=[0,0,0]; img[interior]=[1,1,1]
    # Sobel 外壳
    sf=pot.astype(np.float64); sf[interior]=0
    gx=sobel(sf,axis=1); gy=sobel(sf,axis=0); gm=np.sqrt(gx**2+gy**2)
    th=np.percentile(gm[ext],98.5) if ext.sum() else 0
    shell=(gm>th)&ext; shell=binary_opening(shell,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    shell=binary_dilation(shell,structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))
    img[shell]=[0,0,0]

    out_path=os.path.join(out_dir,"逆M_v6_黑白素描.png")
    fw=8; fh=fw*(HEIGHT/WIDTH)
    fig,ax=plt.subplots(figsize=(fw,fh),dpi=100)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],aspect='equal',interpolation='nearest',origin='lower')
    ax.set_xlim(IM_MIN,IM_MAX); ax.set_ylim(RE_MIN,RE_MAX); ax.axis('off')
    ox,oy=generate_outline(); ax.plot(ox,oy,'-',color='#1a1a1a',lw=0.5,alpha=0.7,zorder=10)
    plt.tight_layout(pad=0); plt.savefig(out_path,dpi=300,bbox_inches='tight',facecolor='white'); plt.close()
    print(f"深色: {cb.sum()} px | 外壳: {shell.sum()} px | 已保存: {out_path}")
    print(f"纯黑白 XOR 棋盘格，无渐变无火焰")
