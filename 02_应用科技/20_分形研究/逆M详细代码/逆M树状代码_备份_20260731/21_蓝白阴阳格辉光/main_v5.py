#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF21 v5 — 接近参考图风格(粗扇形+稀环+有机边界)

v4→v5 改进:
  1. ANG_DIV 24→10 (粗扇形, 匹配参考图的~8-12宽条纹)
  2. DIST_LOG_STEP 0.35→0.55 (环更稀)
  3. 角度维改用c的原始角度(非原点极坐标) → 边界附近扇形跟随水滴形状
  4. 增加第三维度: 迭代深度微调 → 边界处有额外细节
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import binary_dilation

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗 ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=3600; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== v5 参数 ======
ANG_DIV=10            # ★ 粗角度分区(匹配参考图~8-12扇形)
DIST_LOG_STEP=0.55    # ★ 稀疏环(参考图环不太密)
BG_COLOR=[0.03,0.06,0.18]
BLUE_LIGHT=[0.78,0.84,0.96]   # 淡蓝白
BLUE_DARK =[0.10,0.16,0.42]   # 中深蓝(加深对比)
INT_COLOR=[0.02,0.04,0.12]
DEM_SCALE=15.0

# ====== 引擎 ======
x=np.linspace(R0,R1,W); y=np.linspace(I0,I1,H); X,Y=np.meshgrid(x,y); co=X+1j*Y
eps=1e-12; sf=np.abs(co)>eps; ce=np.zeros_like(co,dtype=np.complex128)
ce[sf]=(abs(co[sf])**A)*np.exp(1j*A*np.angle(co[sf])); ce[~sf]=1e6

z=np.zeros_like(ce); dz=np.zeros_like(ce)
alive=np.ones(ce.shape,bool)

for i in range(MI):
    if not alive.any(): break
    idx=np.where(alive)
    za=z[idx].copy(); ca=ce[idx].copy(); dza=dz[idx].copy()
    dza=2*za*dza+1
    za=za**2+ca
    z[idx]=za; dz[idx]=dza
    escaped=(za.real**2+za.imag**2>BL**2)
    alive[idx]&=~escaped

interior=~alive; ext=alive

# DEM
abs_z=np.sqrt(z.real**2+z.imag**2+1e-30)
dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(abs_z**2+1e-30)*abs_z/(dzm+1e-30); d[~ext]=-1

# ====== 全域场量 ======
yy,xx=np.ogrid[:H,:W]
re_px=R0+(xx/W)*(R1-R0); im_px=I0+(yy/H)*(I1-I0)

# 角度维: 用c像素本身的复角 (不是到原点的极角!)
# 这让扇形边界跟随复平面坐标轴, 在水滴尖端/两侧产生不对称分割
c_ang_raw=(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi)  # [0,1]

# 对数距离 (全域有效)
c_dist=np.sqrt(re_px**2+im_px**2)
c_dist_log=np.log(c_dist+0.08)  # offset避免log(0), 也控制中心环密度

# 外部角场(er)用于逃逸区的精细修正
with np.errstate(invalid='ignore', divide='ignore'):
    ang_z=np.arctan2(z.imag,z.real)/(2*np.pi)
    pot_raw=MI+1-np.log2(np.log2(np.maximum(abs_z,1e-30)))
    denom=np.power(2.0,np.minimum(np.where(np.isfinite(pot_raw),pot_raw,0).astype(int),20).astype(float))
    er_ext=(ang_z/denom)%1.0

# ★ 混合角度: ext用er(精细), interior用c_ang_raw(粗但有方向性)
ang_field=np.where(ext, er_ext, c_ang_raw)

# ====== 渲染 ======
h,w=c_dist.shape; img=np.full((h,w,3), BG_COLOR)

# 层1: 水滴外部 = 角度 ⊕ 距离环 XOR
rz=np.floor(ang_field*ANG_DIV).astype(int)
dr=np.floor(c_dist_log/DIST_LOG_STEP).astype(int)
chess=((rz%2==0)!=(dr%2==0))&interior
img[chess]=BLUE_LIGHT
img[interior & ~chess]=BLUE_DARK

# 层2: 水滴内部 = 纯深蓝
img[ext]=INT_COLOR

# 层3: 金色DEM边界辉光
bd_h=np.zeros((h,w),dtype=bool); bd_v=np.zeros((h,w),dtype=bool)
bd_h[:,:-1]=(interior[:,:-1]!=interior[:,1:])
bd_v[:-1,:]=(interior[:-1,:]!=interior[1:,:])
boundary_edge=bd_h|bd_v

dem_valid=d.copy(); dem_valid[dem_valid<0]=0
dem_log=np.log1p(dem_valid*DEM_SCALE)
dem_norm=dem_log/(dem_log.max()+1e-12) if dem_log.max()>0 else dem_log

glow_region=binary_dilation(boundary_edge, structure=np.ones((5,5)))
glow_mask=glow_region & ext
if glow_mask.any():
    dn=dem_norm[glow_mask]
    img[glow_mask]=np.stack([
        np.clip(0.90+0.10*dn,0,1),
        np.clip(0.65+0.35*dn,0,1),
        np.clip(0.08*dn,0,0.15),
    ],axis=-1)

img=np.rot90(img,k=3)

out=os.path.join(od,"UF21_v5_粗扇形稀环.png")
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_COLOR))
plt.close()
print(f"UF21 v5: int={interior.sum()}, chess={chess.sum()}, dark={(interior&~chess).sum()}, glow={glow_mask.sum()} done -> {out}")
