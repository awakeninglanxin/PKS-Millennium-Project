#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF21 蓝白阴阳格辉光 — 逆M DEM + 蓝白棋盘格 + 金色边界

基于 逆M蓝色.jpg 分析:
  - 背景: 深海军蓝(不是黑)
  - 水滴外部(非逃逸区): 蓝白XOR阴阳棋盘格(er⊕pot), 精细分形瓷砖
  - 水滴内部(逃逸区):   平滑蓝渐变colormap(深蓝边→浅蓝/白尖端)
  - 边界:              金色DEM距离估计薄边辉光
  - Mini-bulb:         深蓝空洞

算法组合 = UF4(DEM距离估计) + UF1(XOR棋盘格) + 蓝色系着色
关键修正: 棋盘在interior(水滴外), 蓝渐变在ext(水滴内) — 与阴阳Adam相反!
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import binary_dilation

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 (固定, 与main.py一致) ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=3600; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== 渲染参数 ======
RAY_DIV=48           # 角度量化(越高→越细密的蓝白格)
POT_STEP=4.0         # 势能步长(小→更多环, 但用粗角度平衡)
BG_COLOR=[0.02,0.04,0.14]    # 深海军蓝背景
BLUE_LIGHT=[0.80,0.86,0.97]  # 棋盘亮色(近白淡蓝)
BLUE_DARK =[0.18,0.26,0.55]  # 棋盘暗色(中深蓝)
DEM_SCALE=15.0        # DEM辉光强度

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

interior=~alive  # 不逃逸 = 水滴**外部**(逆M中非逃逸在外)
ext=alive        # 逃逸   = 水滴**内部**(逆M中逃逸在内)

# ====== 全域场量计算 (interior和ext都需要!) ======
abs_z=np.sqrt(z.real**2+z.imag**2+1e-30)

# 平滑势能 — 全域计算(对数保护)
with np.errstate(invalid='ignore', divide='ignore'):
    loglog_z=np.log2(np.log2(abs_z+1e-30))
    pot_raw=MI+1-loglog_z
    pot=np.where(np.isfinite(pot_raw), pot_raw, 0.0)

# 外部角度场 — 全域计算(用最终z的角度)
er=(np.angle(z)+np.pi)/(2*np.pi)

# ====== DEM 距离估计 (Mu-Ency公式, 仅ext有效) ======
zm=abs_z
dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(zm*zm+1e-30)*zm/(dzm+1e-30)
d[~ext]=-1  # 非逃逸区标记无效

# ====== 渲染层叠 ======
h,w=pot.shape
img=np.full((h,w,3), BG_COLOR)  # 层0: 深蓝底

# ---- 层1: 蓝白XOR阴阳棋盘格(水滴EXTERNAL外部=非逃逸区) ----
rz=np.floor(er*RAY_DIV).astype(int)
pz=np.floor(pot/POT_STEP).astype(int)
chess=((rz%2==0)!=(pz%2==0))&interior  # ★ 棋盘在interior!
img[chess]=BLUE_LIGHT     # 亮格(淡蓝白)
dark_chess=interior & ~chess
img[dark_chess]=BLUE_DARK  # 暗格(中深蓝)

# ---- 层2: 水滴内部平滑蓝渐变(逃逸区=ext) ----
if ext.any():
    from matplotlib import colormaps as cms
    cmap=cms['Blues_r']  # 深蓝→浅蓝/白(尖端最亮)
    pot_ext=pot[ext]
    p_min,p_max=np.nanmin(pot_ext),np.nanmax(pot_ext)
    norm_pot=(pot_ext-p_min)/(p_max-p_min+1e-12) if p_max>p_min else np.zeros_like(pot_ext)
    img[ext]=cmap(norm_pot)[...,:3]

# ---- 层3: 金色DEM边界辉光(仅interior↔ext交界处) ----
bd_h=np.zeros((h,w),dtype=bool)
bd_v=np.zeros((h,w),dtype=bool)
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
glow_mask=glow_region & ext  # 辉光在水滴内侧边缘

if glow_mask.any():
    dn=dem_norm[glow_mask]
    r_val=np.clip(0.90+0.10*dn,0,1)
    g_val=np.clip(0.65+0.35*dn,0,1)
    b_val=np.clip(0.08*dn,0,0.15)
    img[glow_mask]=np.stack([r_val,g_val,b_val],axis=-1)

# ---- 层4: Mini-bulb(非逃逸的孤立区域)=保持背景深蓝(已设为BG_COLOR) ----

# ---- 朝向修正 ----
img=np.rot90(img,k=3)

# ====== 存盘 ======
out=os.path.join(od,"UF21_蓝白阴阳格辉光.png")
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_COLOR))
plt.close()
print(f"UF21 Blue YinYang Glow: int={interior.sum()}, ext={ext.sum()}, chess={chess.sum()}, glow={glow_mask.sum()} done -> {out}")
