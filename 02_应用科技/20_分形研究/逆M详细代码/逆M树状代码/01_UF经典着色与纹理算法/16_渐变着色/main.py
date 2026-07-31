#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF16 渐变着色 (Gradient) — smooth势能→HSV渐变"""
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
    idx=np.where(alive);za=z[idx].copy();ca=ce[idx].copy();za=za**2+ca;z[idx]=za;zf[idx]=za
    alive&=~(np.abs(z)>BL)
az=np.abs(zf)+1e-12;sm=np.where(~alive,MI-1-np.log2(np.maximum(np.log2(az),1e-12)),0.0)
sm=np.rot90(sm,k=3);interior=np.rot90(alive,k=3)
sv=sm[~interior];lo,hi=np.percentile(sv,[2,98]) if len(sv)>0 else (0,1)
norm=np.clip((sm-lo)/(hi-lo+1e-10),0,1)
h=norm;s=np.ones_like(h);v=np.ones_like(h)
# HSV→RGB 自定义彩虹
r=np.abs(h*6-3)-1;g=2-np.abs(h*6-2);b=2-np.abs(h*6-4)
r=np.clip(r,0,1);g=np.clip(g,0,1);b=np.clip(b,0,1)
img=np.dstack([r,g,b])
img_flat=img.reshape(-1,3);img_flat[interior.ravel()]=[0,0,0];img=img_flat.reshape(*norm.shape,3)
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off');plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF16_渐变着色.png"),dpi=200,bbox_inches='tight',facecolor='black');plt.close()
print("UF16: Gradient done")
