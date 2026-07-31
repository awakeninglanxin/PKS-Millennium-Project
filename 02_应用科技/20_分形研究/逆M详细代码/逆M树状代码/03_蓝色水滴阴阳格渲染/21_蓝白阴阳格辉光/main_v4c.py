#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF21 v4c — 外部网格版 (瓷砖细 100x)

基于 main_v4b.py (模式A XOR棋盘), 仅把格密度放大 100 倍:
  原 v4b: ANG_DIV=24,  DIST_LOG_STEP=0.35   → 整图外圈仅 ~17 圈环
  本 v4c: ANG_DIV=240, DIST_LOG_STEP=0.035  → 各细 10x, 面积细 100x
  
其余渲染逻辑(深蓝底/金边/内部平滑)完全不变。
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.ndimage import binary_dilation

od=os.path.dirname(os.path.abspath(__file__))

# ====== 视窗参数 ======
TIP=4.0; B=-4/3; HSP=1.6242719100; M=0.5
R0,R1=B-M,TIP+M; I0,I1=-HSP-M,HSP+M
W=3600; H=int(W*(R1-R0)/(I1-I0)); MI=200; BL=50; A=-1

# ====== v4c 渲染参数 (瓷砖细 100x) ======
ANG_DIV=240            # 角度量化 (v4b=24, 细10x)
DIST_LOG_STEP=0.035   # 对数距离环步长 (v4b=0.35, 细10x)
BG_COLOR=[0.03,0.06,0.18]     # 深海军蓝背景(用于水滴内部)
BLUE_LIGHT=[0.78,0.84,0.96]   # 阳(淡蓝白)
BLUE_DARK =[0.12,0.18,0.45]   # 阴(中深蓝)
INT_COLOR=[0.02,0.04,0.12]     # 水滴内部颜色
DEM_SCALE=15.0
CHESS_MODE='A'        # 'A'=XOR棋盘, 'B'=扇形, 'C'=环带

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

interior=~alive
ext=alive

# ====== DEM ======
abs_z=np.sqrt(z.real**2+z.imag**2+1e-30)
dzm=np.sqrt(dz.real**2+dz.imag**2+1e-30)
d=np.log(abs_z**2+1e-30)*abs_z/(dzm+1e-30)
d[~ext]=-1

# ====== 全域有效的场量 ======
yy,xx=np.ogrid[:H,:W]
re_px=R0+(xx/W)*(R1-R0)
im_px=I0+(yy/H)*(I1-I0)
c_dist=np.sqrt(re_px**2+im_px**2)
c_ang =(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi)
c_dist_log=np.log(c_dist+0.01)

with np.errstate(invalid='ignore', divide='ignore'):
    ang_z=np.arctan2(z.imag,z.real)/(2*np.pi)
    abs_z_safe=np.maximum(abs_z,1e-30)
    pot_raw=MI+1-np.log2(np.log2(abs_z_safe))
    denom=np.power(2.0,np.minimum(np.where(np.isfinite(pot_raw),pot_raw,0).astype(int),20).astype(float))
    er_ext=(ang_z/denom)%1.0

ang_field=np.where(ext, er_ext, c_ang)

# ====== 渲染层叠: 棋盘格放在 ext(水滴外部!) ======
h,w=c_dist.shape
img=np.full((h,w,3), BG_COLOR)

if CHESS_MODE == 'A':
    rz=np.floor(ang_field*ANG_DIV).astype(int)
    dr=np.floor(c_dist_log/DIST_LOG_STEP).astype(int)
    chess=((rz%2==0)!=(dr%2==0))&ext           # ★ XOR on ext!
    img[chess]=BLUE_LIGHT                         # 阳
    dark_chess=ext & ~chess
    img[dark_chess]=BLUE_DARK                      # 阴
    
elif CHESS_MODE == 'B':
    rz=np.floor(ang_field*ANG_DIV).astype(int)
    chess=(rz%2==0)&ext
    img[chess]=BLUE_LIGHT
    dark_chess=ext & ~chess
    img[dark_chess]=BLUE_DARK
    
elif CHESS_MODE == 'C':
    dr=np.floor(c_dist_log/DIST_LOG_STEP).astype(int)
    chess=(dr%2==0)&ext
    img[chess]=BLUE_LIGHT
    dark_chess=ext & ~chess
    img[dark_chess]=BLUE_DARK

# ---- 层2: 水滴内部(interior) = 平滑深蓝底 ----
img[interior]=INT_COLOR

# ---- 层3: 金色DEM边界辉光(在边界处叠加) ----
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
glow_mask=glow_region & interior

if glow_mask.any():
    dn=dem_norm[glow_mask]
    img[glow_mask]=np.stack([
        np.clip(0.90+0.10*dn,0,1),
        np.clip(0.65+0.35*dn,0,1),
        np.clip(0.08*dn,0,0.15),
    ],axis=-1)

# ---- 朝向修正 ----
img=np.rot90(img,k=3)

out=os.path.join(od,f"UF21_v4c_{'XOR' if CHESS_MODE=='A' else ('扇形' if CHESS_MODE=='B' else '环带')}_外部网格_细100x.png")
fig,ax=plt.subplots(figsize=(8,8*H/W),dpi=150)
ax.imshow(img,extent=[I0,I1,R0,R1],origin='lower')
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_COLOR))
plt.close()

mode_name={'A':'XOR棋盘','B':'扇形','C':'环带'}[CHESS_MODE]
print(f"UF21 v4c ({mode_name} 外部网格 细100x): int={interior.sum()}, ext={ext.sum()}, chess={chess.sum()}, dark={dark_chess.sum()}, glow={glow_mask.sum()} done -> {out}")
