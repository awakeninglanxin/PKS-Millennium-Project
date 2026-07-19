#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博 v8 — 对偶渲染：内部蓝调渐变 + 外部三角网扩散 + 金边

原理：
  内部(未逃逸) → |z| 渐变深蓝 → 聚光灯效果
  外部(逃逸)   → ray_divisions×256 高频 XOR → 自然三角网
  边缘          → pot<0.05 → 金色蕾丝边过渡
"""

import numpy as np
import matplotlib.pyplot as plt
import os

TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.5
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
WIDTH=2400; HEIGHT=int(WIDTH*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAX_ITER=250; BAILOUT_SQ=10000.0**2
RAY_DIV=256; POT_STEP=0.04

def generate_outline(n_pts=6000):
    eps=1e-10; t=np.linspace(eps,2*np.pi-eps,n_pts)
    c=0.5*np.exp(1j*t)-0.25*np.exp(2j*t); inv=1.0/c
    return -inv.imag,inv.real

def compute(x_min,x_max,y_min,y_max,w,h,max_iter,bailout_sq):
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
        d=(z.real**2+z.imag**2)>bailout_sq; e[d&a]=i; a&=~d
    interior=(e>=max_iter); interior|=(np.abs(c_orig)<0.03)
    ms=zf.real**2+zf.imag**2+1e-30
    pot=np.log(ms)/(2.0**e); pot[interior]=0
    ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
    er=(ang/np.power(2.0,e))%1.0; er[interior]=0
    return np.rot90(pot,k=3),np.rot90(er,k=3),np.rot90(interior,k=3),np.rot90(np.abs(zf),k=3)

if __name__=="__main__":
    out_dir=os.path.dirname(os.path.abspath(__file__))
    print(f"v8 对偶渲染·三角网扩散 计算中...")
    pot,er,interior,zmod=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,WIDTH,HEIGHT,MAX_ITER,BAILOUT_SQ)
    h,w=pot.shape; img=np.zeros((h,w,3)); ext=~interior

    # === 区域一: 水滴内部 → 深蓝渐变(聚光灯) ===
    im=interior&(zmod>0); glow=np.clip(zmod[im]/2.0,0,1)
    img[im,0]=0.05+0.75*(glow**3)       # R 暗→亮红
    img[im,1]=0.30+0.55*(glow**2)       # G 暗蓝→亮蓝
    img[im,2]=0.70+0.30*glow            # B 深蓝→浅蓝白

    # === 区域二: 水滴外部 → 高频三角网 ===
    rz=np.floor(er*RAY_DIV).astype(int); re=(rz%2==0)
    pz=np.floor(pot/POT_STEP).astype(int); pe=(pz%2==0)
    cb_ext=(re==pe)&ext
    bg=np.clip(0.25+0.45*cb_ext.astype(float)+0.08*(pz%6/6.0),0.05,1.0)
    img[ext,0]=bg[ext]*0.08+0.03*(1-np.clip(pot[ext],0,1))
    img[ext,1]=bg[ext]*0.35+0.15*np.sin(pz[ext].astype(float))
    img[ext,2]=0.35+bg[ext]*0.65

    # === 区域三: 金色蕾丝边 (pot<0.05) ===
    gold=ext&(pot<0.05)
    if gold.sum()>0:
        t=np.clip((0.05-pot[gold])/0.05,0,1); t3=np.column_stack([t]*3)
        gc=np.zeros((gold.sum(),3)); gc[:,0]=1.0; gc[:,1]=0.65+0.35*(1-t); gc[:,2]=0.08
        img[gold]=(1-t3)*img[gold]+t3*gc

    # 黑底 + 最终裁剪
    img[~interior&~ext]=[0.02,0.04,0.12]
    img=np.clip(img,0,1)

    # 解析轮廓
    ox,oy=generate_outline()

    out_path=os.path.join(out_dir,"逆M_v8_三角网扩散.png")
    fw=8; fh=fw*(HEIGHT/WIDTH)
    fig,ax=plt.subplots(figsize=(fw,fh),dpi=100)
    ax.set_facecolor('#020610'); fig.patch.set_facecolor('#020610')
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],aspect='equal',interpolation='bilinear',origin='lower')
    ax.plot(ox,oy,'-',color='#ffcc66',lw=0.5,alpha=0.5,zorder=10)
    ax.set_xlim(IM_MIN,IM_MAX); ax.set_ylim(RE_MIN,RE_MAX); ax.axis('off')
    plt.tight_layout(pad=0); plt.savefig(out_path,dpi=300,bbox_inches='tight',facecolor='#020610'); plt.close()
    print(f"内部:{interior.sum()}px 外部:{ext.sum()}px 金边:{gold.sum()}px")
    print(f"已保存: {out_path}")
