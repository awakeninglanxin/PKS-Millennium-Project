#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF3 有理外部射线 — 正确追踪逃逸步数 n """
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0;B=-4/3;HSP=1.6242719100;M=0.5
R0,R1=B-M,TIP+M;I0,I1=-HSP-M,HSP+M;W=2400;H=int(W*(R1-R0)/(I1-I0));MI=250;BL=50;A=-1;RC=128;LTH=0.008
x=np.linspace(R0,R1,W);y=np.linspace(I0,I1,H);X,Y=np.meshgrid(x,y);co=X+1j*Y
eps=1e-12;sf=np.abs(co)>eps;ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf]));ce[~sf]=1e6
z=np.zeros_like(ce);alive=np.ones(ce.shape,bool);zf=np.zeros_like(ce)
esc_n=np.full(ce.shape,MI,dtype=int)  # 逃逸步数
for n in range(MI):
    if not alive.any():break
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca
    z[idx]=za;zf[idx]=za
    new_esc=alive&(np.abs(z)>BL)
    esc_n[new_esc]=n
    alive&=~new_esc
ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
# 用实际逃逸步数 n 而不是 MI-1
er=(ang/np.minimum(np.power(2.0,esc_n),4096))%1.0
er[alive]=0;er[esc_n>15]=0  # 大n的er≈0, 不画
er=np.rot90(er,k=3);interior=np.rot90(alive,k=3)
h,w=er.shape;ext=~interior;rg=np.abs((er*RC)-np.round(er*RC));rm=(rg<LTH)&ext
img=np.ones((h,w,3));img[ext]=[0.9,0.95,1.0];img[rm]=[0.1,0.2,0.5];img[interior]=[0.05,0.1,0.25]
fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF3_有理外部射线.png"),dpi=200,bbox_inches='tight',facecolor='white');plt.close()
print(f"UF3: ray={rm.sum()}px done")
