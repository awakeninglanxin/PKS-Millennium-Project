#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF25 Calabi-Yau指数浮雕 — 螺旋棋盘+Sobel浮雕+DEM金边, Re轴朝上

修复: 螺旋图案移到exterior(视觉外部), 浮雕在棋盘基础上叠加光照
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import sobel
od=os.path.dirname(os.path.abspath(__file__))

TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
ASP=(R1-R0)/(I1-I0); W=2000; H=max(int(W/ASP),1); MI=200; BL=50; A=-1

x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y
eps=1e-12; sf=np.abs(co)>eps; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf])); ce[~sf]=1e6
z=np.zeros_like(ce); dz=np.zeros_like(ce); alive=np.ones(ce.shape,bool)
for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive); za=z[idx].copy(); ca=ce[idx].copy(); dza=dz[idx].copy()
    dza=2*za*dza+1; za=za**2+ca; z[idx]=za; dz[idx]=dza
    escaped_full=np.zeros(ce.shape,bool)
    escaped_full[idx]=(za.real**2+za.imag**2>BL**2); alive&=~escaped_full
interior=~alive; ext=alive

# ==== 螺旋棋盘 (exterior) ====
SPIRAL_K=1.5; DECAY_SIGMA=12.0; N_Q=128; M_Q=64
r=np.abs(co); theta=np.angle(co)
z_cy=np.exp(1j*theta+np.log(r+1e-6)*SPIRAL_K); decay=1-np.exp(-r/DECAY_SIGMA); z_cy*=decay
z_max=np.max(np.abs(z_cy))+1e-6; u=np.real(z_cy)/z_max; v=np.imag(z_cy)/z_max
u_idx=np.floor(u*N_Q).astype(int); v_idx=np.floor(v*M_Q).astype(int)
chess=((u_idx%2==0)!=(v_idx%2==0))&interior  # interior=视觉外部

# 棋盘基础色
LIGHT=[0.78,0.84,0.96]; DARK=[0.12,0.18,0.45]; BG=[0.03,0.06,0.18]
img=np.full((H,W,3),BG); img[chess]=LIGHT; img[interior&~chess]=DARK

# ==== 高度场 (基于螺旋棋盘) ====
height=np.zeros((H,W)); height[chess]=0.6; height[interior&~chess]=0.15
# 叠加多层K值高度调制
for K in [0.7,2.5,4.0]:
    zl=np.exp(1j*theta+np.log(r+1e-6)*K)*decay*0.2
    height+=np.abs(np.real(zl))
height[~interior]=0

# ==== Sobel法线 + 光照 ====
gx=sobel(height,axis=1); gy=sobel(height,axis=0)
nx=-gx; ny=-gy; nz=np.ones_like(gx)
nlen=np.sqrt(nx**2+ny**2+nz**2)+1e-6; nx/=nlen; ny/=nlen; nz/=nlen
lx,ly,lz=0.5,0.5,0.707  # 左上45°
lambert=np.clip(nx*lx+ny*ly+nz*lz,0,1)

# 光照叠加 (亮度调制)
img_emboss=img.copy()
for c in range(3):
    img_emboss[interior,c]=np.clip(img[interior,c]*(0.5+0.7*lambert[interior]),0,1)

# ==== DEM金边 ====
dem=np.zeros_like(co); dem[ext]=(np.log(np.abs(z[ext])**2)*np.abs(z[ext])/(np.abs(dz[ext])+1e-12))
dem_norm=np.clip(dem/(dem.max()+1e-12),0,1); glow=ext&(dem_norm>0.25)
if glow.any():
    dn=dem_norm[glow]; img_emboss[glow]=np.stack([0.85*dn+0.1,0.55*dn+0.2,0.08*dn+0.02],axis=-1)

out=os.path.join(od,'UF25_CY指数浮雕_多层螺旋.png')
plt.imsave(out,np.rot90(img_emboss,k=1),dpi=150)
print(f'UF25 CY-Emboss: ext={ext.sum()} -> {out}')
