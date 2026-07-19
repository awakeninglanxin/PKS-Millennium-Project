#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF8 对偶三角网扩散 — c^α引擎 + 金边 + 高频XOR

原理 (逆M):
  内部(逃逸) = 水滴内部 → RAY_DIV=256 高频XOR → 三角网
  外部(未逃逸) = 水滴外部 → |z|渐变深蓝聚光灯
  边缘 → pot<0.05 → 金色蕾丝边
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1
RAY_DIV=256;POT_STEP=0.04

x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);zf=np.zeros_like(ce)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca
    z[idx]=za;zf[idx]=za;alive&=~(np.abs(z)>BL)
interior=alive;ext=~interior;h,w=ext.shape
az=np.abs(zf)+1e-12;sm=np.where(ext,MI-1-np.log2(np.maximum(np.log2(az),1e-12)),0.0)
ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
er=(ang/np.power(2.0,np.where(ext,(MI-1-np.log2(np.maximum(np.log2(az),1e-12))).astype(int),0).astype(float)))%1.0
er[interior]=0;sm[interior]=0
sm=np.rot90(sm,k=3);er=np.rot90(er,k=3);interior=np.rot90(interior,k=3);ext=~interior
h,w=sm.shape;img=np.zeros((h,w,3))

# 区域一: 外部(水滴外) → 深蓝渐变聚光灯
gl=np.clip(np.abs(np.where(~ext,sm,0))/1.5,0,1)
img[~ext,0]=0.02+0.10*(gl[~ext]**2);img[~ext,1]=0.35+0.45*gl[~ext];img[~ext,2]=0.75+0.25*gl[~ext]

# 区域二: 内部(水滴内) → 高频XOR三角网
rz=np.floor(er*RAY_DIV).astype(int);re=(rz%2==0)
pz=np.floor(sm/POT_STEP).astype(int);pe=(pz%2==0)
cb_int=(re==pe)&ext
bg=np.clip(0.25+0.45*cb_int.astype(float)+0.08*(pz%6/6.0),0.05,1.0)
img[ext,0]=bg[ext]*0.08+0.03*(1-np.clip(sm[ext],0,1))
img[ext,1]=bg[ext]*0.35+0.15*np.sin(pz[ext].astype(float))
img[ext,2]=0.35+bg[ext]*0.65

# 区域三: 金边
gold=ext&(sm<0.05)
if gold.sum()>0:
    t=np.clip((0.05-sm[gold])/0.05,0,1);t3=np.column_stack([t]*3)
    gc=np.zeros((gold.sum(),3));gc[:,0]=1.0;gc[:,1]=0.65+0.35*(1-t);gc[:,2]=0.08
    img[gold]=(1-t3)*img[gold]+t3*gc

img=np.clip(img,0,1)
fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower',interpolation='bilinear')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF8_对偶三角网扩散.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print(f"UF8: ext={ext.sum()}px done")
