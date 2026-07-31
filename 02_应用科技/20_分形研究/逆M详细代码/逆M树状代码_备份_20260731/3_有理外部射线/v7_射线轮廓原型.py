#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v7 — 射线分叉线条 + 轮廓 (无葫芦残影版)

v5 的问题: c_eff[~safe]=1e6 使 c≈0 处强制逃逸 → 产生黑色葫芦状残影
修复: 将 c≈0 的逃逸点明确标记为 interior(白色), 消除残影
"""

import numpy as np
import matplotlib.pyplot as plt
import os

TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.5
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
WIDTH=2400; HEIGHT=int(WIDTH*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAX_ITER=300; BAILOUT=100000.0; BAILOUT_SQ=BAILOUT*BAILOUT
POT_SPACING=0.12; RAY_COUNT=64; LINE_THICK=0.025

def generate_outline(n_pts=6000):
    eps=1e-10; theta=np.linspace(eps,2*np.pi-eps,n_pts)
    c=0.5*np.exp(1j*theta)-0.25*np.exp(2j*theta); inv_c=1.0/c
    return -inv_c.imag,inv_c.real

def compute_fields(x_min,x_max,y_min,y_max,w,h,max_iter,bailout_sq):
    x=np.linspace(x_min,x_max,w); y=np.linspace(y_min,y_max,h)
    X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
    eps=1e-12; safe=np.abs(c_orig)>eps
    c_eff=np.zeros_like(c_orig,dtype=np.complex128)
    c_eff[safe]=1.0/c_orig[safe]; c_eff[~safe]=1e10
    z=np.zeros_like(c_eff,dtype=np.complex128)
    e=np.full(c_eff.shape,max_iter,dtype=np.float64)
    a=np.ones(c_eff.shape,dtype=bool); zf=np.zeros_like(c_eff,dtype=np.complex128)
    c_mod_sq=c_eff.real**2+c_eff.imag**2
    for i in range(max_iter):
        if not a.any(): break
        z[a]=z[a]**2+c_eff[a]; zf[a]=z[a].copy()
        # 动态逃逸: |z|² > max(bailout_sq, 4×|c_eff|²) → 防止核心大数值假逃逸
        d=(z.real**2+z.imag**2)>np.maximum(bailout_sq,4.0*c_mod_sq)
        e[d&a]=i; a&=~d
    interior=(e>=max_iter)
    # 反演核心安全半径: 标准M葫芦(半径≈2) → 1/2=0.5, 用0.25安全覆盖
    interior|=(np.abs(c_orig)<0.25)
    ms=zf.real**2+zf.imag**2+1e-30
    pot=np.log(ms)/(2.0**e); pot[interior]=0
    ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
    nc=np.minimum(e,20).astype(np.float64)
    er=(ang/np.power(2.0,nc))%1.0; er[interior]=0
    return np.rot90(pot,k=3),np.rot90(er,k=3),np.rot90(interior,k=3)

if __name__=="__main__":
    from scipy.ndimage import sobel,binary_dilation,binary_opening
    out_dir=os.path.dirname(os.path.abspath(__file__))
    print(f"v7 无葫芦残影 计算中...")
    pot,er,interior=compute_fields(RE_MIN,RE_MAX,IM_MIN,IM_MAX,WIDTH,HEIGHT,MAX_ITER,BAILOUT_SQ)
    h,w=pot.shape; ext=~interior
    # 射线
    rm=np.abs((er*RAY_COUNT)%1.0-0.5); is_ray=ext&(rm<LINE_THICK)
    # 等势
    pm=np.abs((pot%POT_SPACING)-POT_SPACING/2.0); is_pot=ext&(pm<LINE_THICK)
    # 外壳
    sf=pot.astype(np.float64); sf[interior]=0
    gx=sobel(sf,axis=1); gy=sobel(sf,axis=0); gm=np.sqrt(gx**2+gy**2)
    th=np.percentile(gm[ext],98.5) if ext.sum() else 0
    shell=(gm>th)&ext; shell=binary_opening(shell,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    shell=binary_dilation(shell,structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))
    # 渲染
    img=np.ones((h,w,3))
    img[is_ray]=[0,0,0]; img[is_pot]=[0.35,0.35,0.35]
    img[is_ray&is_pot]=[0,0,0]; img[shell]=[0,0,0]; img[interior]=[1,1,1]
    print(f"射线:{is_ray.sum()} 等势:{is_pot.sum()} 外壳:{shell.sum()}")
    out_path=os.path.join(out_dir,"逆M_v7_无葫芦残影.png")
    fw=8; fh=fw*(HEIGHT/WIDTH)
    fig,ax=plt.subplots(figsize=(fw,fh),dpi=100)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],aspect='equal',interpolation='nearest',origin='lower')
    ox,oy=generate_outline(); ax.plot(ox,oy,'-',color='#1a1a1a',lw=0.6,alpha=0.8,zorder=10)
    ax.set_xlim(IM_MIN,IM_MAX); ax.set_ylim(RE_MIN,RE_MAX); ax.axis('off')
    plt.tight_layout(pad=0); plt.savefig(out_path,dpi=300,bbox_inches='tight',facecolor='white'); plt.close()
    print(f"已保存: {out_path}")
