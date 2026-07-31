#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF21 v3 — 蓝白极坐标阴阳格(扇形×同心环 XOR + UF8三角网算法外置)

v2→v3 改进:
  v2: 纯角度扇形(像披萨切片) → 缺少环带纹理
  v3: 角度扇形 × 距离/势能环 二维XOR → 阴阳瓷砖(匹配参考图的分形格子)
  
核心 = 把UF8的三角网算法(er⊕pot)搬到interior(水滴外部):
  - er = 外部角场(随迭代深度细化, 边界附近更精细)
  - pot = 平滑势能(等高线=同心环)
  - XOR → 阴阳分形瓷砖 + 向外扩散的环

配色: 蓝白系(参考图风格)
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import binary_dilation

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=3600; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== v3 渲染参数 ======
ANG_DIV=32            # 外部角场量化(中等→参考图有较细的扇形分割)
POT_STEP=4.0          # 势能环步长(粗→减少环密度, 参考图环不太密)
BG_COLOR=[0.03,0.06,0.18]    # 深海军蓝背景
BLUE_LIGHT=[0.78,0.84,0.96]  # 阳格亮色(淡蓝白)
BLUE_DARK =[0.12,0.18,0.45]  # 阴格暗色(中深蓝, 比v2更深以增强对比)
INT_COLOR=[0.02,0.04,0.12]    # 水滴内部(深蓝近黑)
DEM_SCALE=15.0

# ====== 引擎: 逆M迭代 + DEM导数追踪 ======
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

interior=~alive
ext=alive

# ====== 全域场量 ======
abs_z=np.sqrt(z.real**2+z.imag**2+1e-30)
with np.errstate(invalid='ignore', divide='ignore'):
    loglog_z=np.log2(np.log2(abs_z+1e-30))
    pot_raw=MI+1-loglog_z
    pot=np.where(np.isfinite(pot_raw), pot_raw, 0.0)

# ★ 外部角场 (UF8同款: 角度随迭代深度2^n细化)
ang_z=np.arctan2(z.imag,z.real)/(2*np.pi)
denom=np.power(2.0,np.minimum(np.where(np.isfinite(pot_raw),pot_raw,0).astype(int),20).astype(float))
er=(ang_z/denom)%1.0
er[~ext]=0  # 非逃逸区清零

# ====== DEM ======
zm=abs_z
dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(zm*zm+1e-30)*zm/(dzm+1e-30)
d[~ext]=-1

# ====== 渲染层叠 ======
h,w=pot.shape
img=np.full((h,w,3), BG_COLOR)

# ---- 层1: 水滴外部 = UF8三角网XOR (er⊕pot) 但在interior ----
rz=np.floor(er*ANG_DIV).astype(int)       # 外部角(边界处更细)
pz=np.floor(pot/POT_STEP).astype(int)     # 势能环
chess=((rz%2==0)!=(pz%2==0))&interior     # ★ XOR在interior(水滴外部!)
img[chess]=BLUE_LIGHT                      # 阳(淡蓝白)
dark_chess=interior & ~chess
img[dark_chess]=BLUE_DARK                   # 阴(中深蓝)

# ---- 层2: 水滴内部 = 纯深蓝 ----
img[ext]=INT_COLOR

# ---- 层3: 金色DEM边界辉光 ----
bd_h=np.zeros((h,w),dtype=bool); bd_v=np.zeros((h,w),dtype=bool)
bd_h[:,:-1]=(interior[:,:-1]!=interior[:,1:])
bd_v[:-1,:]=(interior[:-1,:]!=interior[1:,:])
boundary_edge=bd_h|bd_v

dem_valid=d.copy(); dem_valid[dem_valid<0]=0
dem_log=np.log1p(dem_valid*DEM_SCALE)
if dem_log.max()>0:
    dem_norm=dem_log/(dem_log.max()+1e-12)
else:
    dem_norm=dem_log

glow_region=binary_dilation(boundary_edge, structure=np.ones((5,5)))
glow_mask=glow_region & ext

if glow_mask.any():
    dn=dem_norm[glow_mask]
    img[glow_mask]=np.stack([
        np.clip(0.90+0.10*dn,0,1),
        np.clip(0.65+0.35*dn,0,1),
        np.clip(0.08*dn,0,0.15),
    ],axis=-1)

# ---- 朝向修正 ----
img=np.rot90(img,k=3)

out=os.path.join(od,"UF21_v3_阴阳格三角网.png")
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_COLOR))
plt.close()
print(f"UF21 v3 YinYang-TriNet: int={interior.sum()}, ext={ext.sum()}, chess={chess.sum()}, glow={glow_mask.sum()} done -> {out}")
