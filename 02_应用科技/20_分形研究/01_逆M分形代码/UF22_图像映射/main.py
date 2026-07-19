#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF22 图像映射 (Image Mapping) — 将逃逸势能/角度映射到外部图像查色

算法: ν→图像列, arg(z)→图像行, 从源图像采样 RGB 作为输出颜色。
"""
import numpy as np, matplotlib.pyplot as plt, os
from matplotlib import colormaps as cms

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=1800; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== 引擎 ======
x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y
eps=1e-12; sf=np.abs(co)>eps; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf])); ce[~sf]=1e6

z=np.zeros_like(ce); dz=np.zeros_like(ce)
alive=np.ones(ce.shape,bool)
esc_iter=np.zeros(ce.shape,int)

for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive)
    za=z[idx].copy(); ca=ce[idx].copy(); dza=dz[idx].copy()
    dza=2*za*dza+1
    za=za**2+ca
    z[idx]=za; dz[idx]=dza
    escaped_full=np.zeros(ce.shape,bool)
    escaped_full[idx]=(za.real**2+za.imag**2>BL**2)
    esc_iter[escaped_full]=i+1
    alive&=~escaped_full

interior=~alive; ext=alive

# ====== 势能与角度 ======
# 直接用逃逸步数(避免 smooth pot 的 NaN)
nu=esc_iter.astype(np.float64)
arg_z=np.angle(z); arg_z[~ext]=0; arg_z[arg_z<0]+=2*np.pi

# ====== 创建源图像 (合成: 日落渐变 + 角度纹理) ======
SIW=256; SIH=256  # 源图像尺寸
src=np.zeros((SIH,SIW,3))
yg,xg=np.mgrid[0:SIH,0:SIW]
# col 0: 水平天空渐变 (蓝→橙→红)
hue=xg/SIW*0.66  # 0→赤, 0.66→蓝
sat=np.ones((SIH,SIW))*0.8
val=1.0-yg/SIH*0.3  # 顶部亮, 底部暗
# HSV→RGB
from matplotlib.colors import hsv_to_rgb
hsv=np.stack([hue,sat,val],axis=-1)
src=hsv_to_rgb(hsv)
# 叠加一些波纹纹理
src[:,:,0]*=0.85+0.15*np.sin(yg/8)*np.cos(xg/12)
src[:,:,1]*=0.90+0.10*np.sin(yg/6+1.2)*np.cos(xg/10+0.8)
src[:,:,2]*=0.85+0.15*np.sin(yg/7+2.4)*np.cos(xg/14+1.6)
src=np.clip(src,0,1)

# ====== 图像映射着色 (稳健版: 避免除零/NaN) ======
nu_copy=nu.copy().astype(np.float64); nu_copy[~ext]=0
nu_max=np.percentile(nu_copy[ext],95) if ext.any() else 1.0
nu_max=max(nu_max,1.0)  # 防止除零
u=np.clip(nu_copy/nu_max,0.0,1.0)
v=(arg_z/(2*np.pi))
v=np.clip(v,0.0,1.0)

sx=np.clip((u*(SIW-1)).astype(np.int32),0,SIW-1)
sy=np.clip((v*(SIH-1)).astype(np.int32),0,SIH-1)
img=np.zeros((H,W,3))
img[ext]=src[sy[ext],sx[ext]]
img[~ext]=[0.02,0.02,0.06]  # 水滴外部: 深蓝黑

# ====== 叠加 DEM 金边 ======
dem=np.zeros_like(co,dtype=np.float64)
dem[ext]=(np.log(np.abs(z[ext])**2)*np.abs(z[ext])/(np.abs(dz[ext])+1e-12))
dem_norm=np.clip(dem/(dem.max()+1e-12),0,1)
glow=ext&(dem_norm>0.4)
if glow.any():
    dn=dem_norm[glow]
    img[glow]=np.stack([0.9*dn+0.1,0.6*dn+0.2,0.1*dn+0.02],axis=-1)

# ====== 输出 (k=1转90°→实数轴正方向朝上) ======
out=os.path.join(od,'UF22_图像映射.png')
src_out=os.path.join(od,'UF22_源图像.png')
plt.imsave(src_out,src)

# 旋转: k=1(90°CCW)→Re轴朝上; k=3→Re朝下; k=2→180°
img_rot=np.rot90(img,k=1)
# xy等比: figsize严格按图像宽高比
aspect=img_rot.shape[1]/img_rot.shape[0]
fig,axes=plt.subplots(1,2,figsize=(12,12/aspect*0.5))
axes[0].imshow(src,origin='upper'); axes[0].set_title('Source (256x256)')
axes[0].axis('off')
axes[1].imshow(img_rot,origin='upper')
axes[1].set_title('UF22 Image Mapping')
axes[1].axis('off')
plt.tight_layout()
fig.savefig(out,dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print(f'UF22 Image Mapping: k=1(Re↑), aspect={aspect:.2f} -> {out}')
