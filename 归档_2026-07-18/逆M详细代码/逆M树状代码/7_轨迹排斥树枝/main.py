#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF7 轨迹排斥树枝 — v1坐标系修复: 在pre-rot90空间画轨迹, 再rot90

修复: 轨迹坐标映射到 pre-rot90 的(Re,Im)像素, 然后整体 rot90(k=3)
      与 v1 完全一致的坐标管线, 确保尖端在 y=4
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))

TIP=4.0; B=-4/3; HSPAN=1.6242719100; MARGIN=1.0  # +1外扩
RE_MIN,RE_MAX=B-M,TIP+M; IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
W=1200; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN)); BW,BA=250,50; STEP=8

print("UF7 轨迹排斥树枝 (v1坐标系) 计算中...")

# c^α引擎 (与v1一致)
x=np.linspace(RE_MIN,RE_MAX,W); y=np.linspace(IM_MIN,IM_MAX,H)
X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
eps=1e-12; safe=np.abs(c_orig)>eps
ce=np.zeros_like(c_orig,dtype=np.complex128)
ce[safe]=(np.abs(c_orig[safe])**-1)*np.exp(-1j*np.angle(c_orig[safe]))
ce[~safe]=1e6

# pre-rot90图像 (x=Re列, y=Im行)
img_pre=np.ones((H,W,3))
rows=np.arange(0,H,STEP); cols=np.arange(0,W,STEP)
RR,CC=np.meshgrid(rows,cols,indexing='ij')
sub_c=ce[RR.ravel(),CC.ravel()]; n_pts=len(sub_c)
print(f"  采样: {n_pts}点 step={STEP}")

z=np.zeros(n_pts,dtype=np.complex128); alive=np.ones(n_pts,bool)
for n in range(120):
    if not alive.any(): break
    z[alive]=z[alive]**2+sub_c[alive]
    sz=np.abs(z[alive])>1e-12
    idx=np.where(alive)[0][sz]
    wi=1.0/z[idx]
    px=np.clip(((wi.real-RE_MIN)/(RE_MAX-RE_MIN)*W).astype(int),0,W-1)
    py=np.clip(((wi.imag-IM_MIN)/(IM_MAX-IM_MIN)*H).astype(int),0,H-1)
    g=0.15+0.85*(n/120)
    img_pre[py,px]=g
    alive[idx[np.abs(z[idx])>BA]]=False

# rot90(k=3) 与 v1 一致
img=np.rot90(img_pre,k=3)
H2,W2=img.shape[:2]
# 解析轮廓
ox,oy=[],[]
for t in np.linspace(1e-10,2*np.pi-1e-10,6000):
    c=0.5*np.exp(1j*t)-0.25*np.exp(2j*t); inv=1.0/c
    ox.append(-inv.imag); oy.append(inv.real)

fig,ax=plt.subplots(figsize=(8,8*H2/W2),dpi=100)
ax.set_facecolor('white'); fig.patch.set_facecolor('white')
ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
ax.plot(ox,oy,'-',color='#cc0000',lw=0.3,alpha=0.4,zorder=10)
ax.set_xlim(IM_MIN,IM_MAX); ax.set_ylim(RE_MIN,RE_MAX); ax.axis('off')
plt.tight_layout(pad=0)
plt.savefig(os.path.join(od,"UF7_轨迹排斥树枝.png"),dpi=200,bbox_inches='tight',facecolor='white'); plt.close()
print(f"UF7 done")
