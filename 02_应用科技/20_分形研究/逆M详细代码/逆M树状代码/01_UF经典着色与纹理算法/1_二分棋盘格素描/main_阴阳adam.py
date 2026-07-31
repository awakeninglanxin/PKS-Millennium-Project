#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF1 阴阳Adam — 基于逆M引擎的黑白棋盘+DEM辉光+蓝紫中心

参考: 逆M阴阳 adam.jpg

算法分析(从参考图反推):
  1. 背景反转: 非逃逸区=纯黑(外部空间), 逃逸区=水滴内部有内容
  2. 黑白棋盘格: 角度⊕势函数 XOR (旧版双维度, 但参数调粗)
  3. 中心区域: 连续colormap覆盖(蓝紫渐变 = "阴阳鱼眼")
  4. 边界辉光: DEM距离估计 (log|z|·|z|/|dz|) 橙黄色描边
  5. Mini-bulb: 内部点保持黑色空洞

与main.py差异:
  - main.py: 白底+角度边缘检测细线+蓝边界 → 树状连线风格
  - 本版:   黑底+XOR棋盘+DEM辉光+colormap中心 → 阴阳Adam风格
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0; B=-4/3; H=1.6242719100; M=0.5
RE_MIN,RE_MAX=B-M,TIP+M; IM_MIN,IM_MAX=-H-M,H+M
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1

# ====== 渲染参数 ======
RAY_DIV=16           # 角度量化(粗→大格子, 参考: 大块棋盘)
POT_STEP=8.0         # 势能步长(很粗→极少环)
DEM_SCALE=20.0       # DEM辉光强度(大幅提高)

class Engine:
    """UF5已验证的c^α引擎 + DEM距离估计"""
    @staticmethod
    def compute(x_mn,x_mx,y_mn,y_mx,w,h):
        x=np.linspace(x_mn,x_mx,w); y=np.linspace(y_mn,y_mx,h)
        X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
        eps=1e-12; safe=np.abs(c_orig)>eps
        ce=np.zeros_like(c_orig,dtype=np.complex128)
        ce[safe]=(np.abs(c_orig[safe])**ALPHA)*np.exp(1j*ALPHA*np.angle(c_orig[safe]))
        ce[~safe]=1e6+0j
        z=np.zeros_like(ce,dtype=np.complex128)
        dz=np.ones_like(ce,dtype=np.complex128)   # dz/dz₀ 用于DEM
        alive=np.ones(ce.shape,dtype=bool)
        zf=np.zeros_like(ce,dtype=np.complex128)
        esc_iter=np.zeros(ce.shape,dtype=np.int32)
        for n in range(MAXITER):
            if not alive.any(): break
            z[alive]=z[alive]**2+ce[alive]
            dz[alive]=2*z[alive]*dz[alive]+1       # dZ/dc 导数链式法则
            zf[alive]=z[alive].copy()
            escaped=np.abs(z)>BAILOUT
            esc_iter[escaped & alive]=n+1
            alive&=~escaped
        interior=alive
        az=np.abs(zf)+1e-12
        smooth_n=MAXITER-1-np.log2(np.maximum(np.log2(az),1e-12)); smooth_n[interior]=0
        ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
        denom=np.power(2.0,np.minimum(smooth_n,20))
        er=(ang/denom)%1.0; er[interior]=0
        # DEM: distance estimator
        dem=np.zeros_like(smooth_n)
        msk=~interior & (az>1)
        dem[msk]=0.5*np.log(az[msk])*az[msk]/np.abs(dz[msk])
        dem[interior]=0
        return (np.rot90(smooth_n,k=3),
                np.rot90(er,k=3),
                np.rot90(interior,k=3),
                np.rot90(esc_iter,k=3),
                np.rot90(dem,k=3))

pot,er,interior,esc_iter,dem=Engine.compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,W,H)
h,w=pot.shape; ext=~interior

# ====== 层1: 黑底 ======
img=np.zeros((h,w,3))

# ====== 层2: 灰阶XOR棋盘格(水滴内部) ======
rz=np.floor(er*RAY_DIV).astype(int)
pz=np.floor(pot/POT_STEP).astype(int)
chess=((rz%2==0)!=(pz%2==0))&ext
# 灰阶: 暖白 vs 深灰(非纯黑白, 匹配参考图的层次感)
img[chess]=[0.95,0.93,0.90]          # 暖白色格
dark=ext & ~chess
img[dark]=[0.18,0.16,0.14]           # 深灰格(接近参考图)

# ====== 层3: (已移除) 中心蓝紫colormap ======
# 用户要求: 保留右侧黑白棋盘格, 去掉左侧蓝区
# 原逻辑: center_mask=ext & (c_dist < CENTER_DIST) → PuBu 蓝紫覆盖
# 现移除, 左侧统一回落为黑白棋盘格

# ====== 层4: DEM橙黄辉光边(仅集合边界!) ======
# 找与interior相邻的ext像素 = 真正的集合边界
bnd_h=np.zeros((h,w),dtype=bool); bnd_v=np.zeros((h,w),dtype=bool)
bnd_h[:,1:]=ext[:,1:]&interior[:,:-1]
bnd_h[:,:-1]=ext[:,:-1]&interior[:,1:]
bnd_v[1:,:]=ext[1:,:]&interior[:-1,:]
bnd_v[:-1,:]=ext[:-1,:]&interior[1:,:]
boundary_edge=(bnd_h|bnd_v)&ext

# 边界像素用DEM值映射橙黄强度
if boundary_edge.any():
    dem_b=np.clip(dem[boundary_edge],0,None)
    dn=dem_b/(dem_b.max()+1e-12)
    img[boundary_edge]=np.stack([
        np.clip(0.90+0.10*dn,0,1),      # R: 橙~亮黄
        np.clip(0.40+0.50*dn,0,1),      # G: 暗~亮
        np.clip(0.05+0.03*dn,0,0.10),   # B: 微量
    ],axis=-1)
    # 膨胀2px让辉光有厚度(半透明橙)
    for _ in range(2):
        bdil=np.zeros((h,w),dtype=bool)
        bdil[:,1:]|=boundary_edge[:,:-1]; bdil[:,:-1]|=boundary_edge[:,1:]
        bdil[1:,:]|=boundary_edge[:-1,:]; bdil[:-1,:]|=boundary_edge[1:,:]
        extra=bdil & ~boundary_edge & dark  # 只在深灰区填充
        img[extra]=[0.72,0.33,0.06]
        boundary_edge|=bdil

# ====== 层5: 内部(Mini-bub)保持黑色 ======
# 已经是黑底, 无需操作

fig,ax=plt.subplots(figsize=(10,10*h/w),dpi=150)
ax.set_facecolor('black'); fig.patch.set_facecolor('black')
ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
ax.axis('off'); plt.tight_layout(pad=0)
out=os.path.join(od,"UF1_阴阳Adam.png")
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor='black'); plt.close()
print(f"UF1 YinYang Adam: ext={ext.sum()}, chess={chess.sum()}, boundary={boundary_edge.sum()} done -> {out}")
