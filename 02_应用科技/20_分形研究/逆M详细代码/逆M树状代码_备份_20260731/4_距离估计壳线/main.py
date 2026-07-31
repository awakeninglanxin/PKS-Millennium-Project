#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF4 距离估计壳线 — 真实 DEM 连续发光映射

Mu-Ency DEM/M 算法:
  d = log(|z|²) * |z| / |dz|   (无 0.5 因子)
  映射: shade = -k * log(d)    → 连续渐变光晕
  
效果: 不是硬边界线, 而是边界发光→衰减的丝滑光晕
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M
W=3600;H=int(W*(R1-R0)/(I1-I0));MI=200;BL=50;A=-1

x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);dz=np.zeros_like(ce);alive=np.ones(ce.shape,bool)
for i in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy()
    dza=dz[idx].copy();dza=2*za*dza+1;za=za**2+ca
    z[idx]=za;dz[idx]=dza;alive&=~(z.real**2+z.imag**2>BL**2)

interior=alive
zm=np.sqrt(z.real**2+z.imag**2+1e-30);dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
# ★ Mu-Ency 真实 DEM 公式: d = log(|z|²) * |z| / |dz|
d=np.log(zm*zm+1e-30)*zm/(dzm+1e-30)
d[interior]=1e10
# 映射: shade = -log(d) → 边界处最小d→最大shade→发光
shade=np.clip(-np.log(d+1e-100)/3,0,1)
shade[interior]=0
img=np.zeros((H,W,3));s=shade
img[:,:,0]=s*0.15+0.02
img[:,:,1]=s*0.60+0.10
img[:,:,2]=s*0.20+0.02
# 增强边界: d < pixel_width → 亮白色细线
px_w=(I1-I0)/W;stroke=d<px_w
from scipy.ndimage import binary_dilation
stroke=binary_dilation(stroke,structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))
img[stroke]=[0.8,1.0,0.8]
img=np.rot90(img,k=3)
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.set_facecolor('black');fig.patch.set_facecolor('black')
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF4_距离估计壳线.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print(f"UF4: DEM光晕 stroke={stroke.sum()}px done")
