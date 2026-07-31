#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF12 高斯整数 (Gaussian Integer) — 按Re(z)/Im(z)整数部分着色

正M: 外部逃逸z → floor(Re(z)) mod N 着色
逆M: 水滴内部逃逸z → 同理
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);zf=np.zeros_like(ce)
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca
    z[idx]=za;zf[idx]=za;alive&=~(np.abs(z)>BL)
# 高斯整数: floor(Re(z)) 和 floor(Im(z)) 的奇偶组合
gi=(np.floor(zf.real).astype(int)%2+(np.floor(zf.imag).astype(int)%2)*2)
gi[alive]=0
gi=np.rot90(gi,k=3)
cmap=[[1,1,1],[0.2,0.2,0.8],[0.8,0.2,0.2],[0.2,0.8,0.2]]
img=np.array([cmap[min(g,3)] for g in gi.ravel()]).reshape(gi.shape[0],gi.shape[1],3)
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF12_高斯整数.png"),dpi=200,bbox_inches='tight',facecolor='white');plt.close()
print(f"UF12: Gaussian Integer done")
