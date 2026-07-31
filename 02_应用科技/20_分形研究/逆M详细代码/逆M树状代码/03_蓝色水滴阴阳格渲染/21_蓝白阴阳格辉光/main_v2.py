#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF21 v2 — 蓝白极坐标辐射格(参考 逆M蓝色.jpg + UF8三角网算法)

v2 核心思路 (对比v1的修正):
  v1问题: 用矩形XOR棋盘(er⊕pot)画外部 → 细密格子, 不像参考图
  v2方案: 用**极坐标系**的 角度扇形 ⊕ 距离环 XOR → 粗蓝白辐射条纹
        = UF8三角网算法搬到 水滴外部(interior), 配色改为蓝白

参考图特征分析:
  1. 背景/远处: 深海军蓝
  2. 水滴外部: 粗扇形蓝白辐射纹 (角度~8-16区 × 同心环向外扩散)
  3. 水滴内部: 近纯深蓝(平滑无纹理)
  4. 边界:     金色DEM细线辉光
  5. Mini-bub: 深色空洞

与UF8的关系:
  UF8: 三角网在 ext(水滴内) + 渐变在 interior(水滴外)
  v2:  三角网在 interior(水滴外) + 纯色在 ext(水滴内)  ← 内外反转!
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import binary_dilation

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=3600; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== v2 渲染参数 ======
ANG_SECT=10           # 极坐标角度分区数(越小→越宽的扇形, 参考~8-12粗条纹)
RING_STEP=8.0         # 距离环步长(越大→越少的环, 参考图环较稀)
BG_COLOR=[0.03,0.06,0.18]    # 深海军蓝背景
BLUE_LIGHT=[0.78,0.84,0.96]  # 辐射纹亮色(淡蓝白)
BLUE_DARK =[0.15,0.22,0.52]  # 辐射纹暗色(中深蓝)
INT_COLOR=[0.02,0.04,0.14]   # 水滴内部颜色(近纯深蓝)
DEM_SCALE=15.0         # DEM金边强度

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

interior=~alive  # 非逃逸 = 水滴外部
ext=alive        # 逃逸   = 水滴内部

# ====== 全域场量 ======
abs_z=np.sqrt(z.real**2+z.imag**2+1e-30)
with np.errstate(invalid='ignore', divide='ignore'):
    loglog_z=np.log2(np.log2(abs_z+1e-30))
    pot_raw=MI+1-loglog_z
    pot=np.where(np.isfinite(pot_raw), pot_raw, 0.0)
er=(np.angle(z)+np.pi)/(2*np.pi)  # 外部角 [0,1]

# ====== DEM 距离估计 ======
zm=abs_z
dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(zm*zm+1e-30)*zm/(dzm+1e-30)
d[~ext]=-1

# ====== 像素到原点的极坐标 (用于水滴外部辐射纹) ======
yy,xx=np.ogrid[:H,:W]
re_px=R0+(xx/W)*(R1-R0)
im_px=I0+(yy/H)*(I1-I0)
c_dist=np.sqrt(re_px**2+im_px**2)       # 到原点距离
c_ang =(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi)  # 到原点角度 [0,1]

# ====== 渲染层叠 ======
h,w=pot.shape
img=np.full((h,w,3), BG_COLOR)

# ---- 层1: 水滴外部 = 极坐标辐射纹 (角度扇形 ⊕ 距离环 XOR) ----
# 这是UF8三角网算法的核心逻辑, 但应用在interior区域
ang_bin=np.floor(c_ang*ANG_SECT).astype(int)          # 粗角度分区
ring_bin=np.floor(c_dist/RING_STEP).astype(int)       # 粗距离环
radial_chess=((ang_bin%2==0)!=(ring_bin%2==0))&interior  # ★ XOR在interior!
img[radial_chess]=BLUE_LIGHT   # 亮纹(淡蓝白)
dark_radial=interior & ~radial_chess
img[dark_radial]=BLUE_DARK      # 暗纹(中深蓝)

# ---- 层2: 水滴内部 = 纯深蓝 (无纹理, 匹配参考图) ----
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
glow_mask=glow_region & ext  # 金边在水滴内侧边缘

if glow_mask.any():
    dn=dem_norm[glow_mask]
    img[glow_mask]=np.stack([
        np.clip(0.90+0.10*dn,0,1),
        np.clip(0.65+0.35*dn,0,1),
        np.clip(0.08*dn,0,0.15),
    ],axis=-1)

# ---- 朝向修正 ----
img=np.rot90(img,k=3)

# ====== 存盘 ======
out=os.path.join(od,"UF21_v2_极坐标辐射格.png")
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_COLOR))
plt.close()
print(f"UF21 v2 PolarRadial: int={interior.sum()}, ext={ext.sum()}, radial={radial_chess.sum()}, glow={glow_mask.sum()} done -> {out}")
