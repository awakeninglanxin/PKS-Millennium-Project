#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UF1 树状连线 — 去掉同心辐射环，保留外部角度场的阴阳分界线(三岔分形连线)

核心改动：
  旧: pz=floor(pot/0.12) → 数百个同心带 → bullseye环
  新: 角度场边缘检测 + 迭代奇偶二分 → 纯树状分岔线

参考图特征：从实数轴向水滴边缘的三岔分形连线，无同心环
算法原理：逆M集的外部角场在Mini-bulb处产生不连续性，
          检测相邻像素的角度跳变即可画出树状分支结构
"""
import numpy as np, matplotlib.pyplot as plt, os
od=os.path.dirname(os.path.abspath(__file__))
TIP=4.0; B=-4/3; H=1.6242719100; M=0.5
RE_MIN,RE_MAX=B-M,TIP+M; IM_MIN,IM_MAX=-H-M,H+M
W=2400; H=int(W*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAXITER=250; BAILOUT=50; ALPHA=-1
ANGLE_BINS=512       # 角度量化级数(更高=更密的分支线)
LINE_WIDTH=2          # 线条加粗(膨胀像素数)

class Engine:
    """UF5已验证的c^α引擎 (ALPHA=-1 → 逆M映射 1/c)"""
    @staticmethod
    def compute(x_mn,x_mx,y_mn,y_mx,w,h):
        x=np.linspace(x_mn,x_mx,w); y=np.linspace(y_mn,y_mx,h)
        X,Y=np.meshgrid(x,y); c_orig=X+1j*Y
        eps=1e-12; safe=np.abs(c_orig)>eps
        ce=np.zeros_like(c_orig,dtype=np.complex128)
        ce[safe]=(np.abs(c_orig[safe])**ALPHA)*np.exp(1j*ALPHA*np.angle(c_orig[safe]))
        ce[~safe]=1e6+0j
        z=np.zeros_like(ce,dtype=np.complex128)
        alive=np.ones(ce.shape,dtype=bool)
        zf=np.zeros_like(ce,dtype=np.complex128)
        # 同时记录逃逸迭代次数(原始整数，非平滑)
        esc_iter=np.zeros(ce.shape,dtype=np.int32)
        for n in range(MAXITER):
            if not alive.any(): break
            z[alive]=z[alive]**2+ce[alive]; zf[alive]=z[alive].copy()
            escaped=np.abs(z)>BAILOUT
            esc_iter[escaped & alive]=n+1
            alive&=~escaped
        interior=alive
        az=np.abs(zf)+1e-12
        smooth_n=MAXITER-1-np.log2(np.maximum(np.log2(az),1e-12)); smooth_n[interior]=0
        ang=np.arctan2(zf.imag,zf.real)/(2*np.pi)
        denom=np.power(2.0,np.minimum(smooth_n,20))
        er=(ang/denom)%1.0
        er[interior]=0
        return (np.rot90(smooth_n,k=3),
                np.rot90(er,k=3),
                np.rot90(interior,k=3),
                np.rot90(esc_iter,k=3))

pot,er,interior,esc_iter=Engine.compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,W,H)
h,w=pot.shape; ext=~interior

# ====== 核心：角度场阴阳分界线 ======
# 1) 高精度角度量化
rz=np.floor(er*ANGLE_BINS).astype(np.float64)

# 2) 检测角度跳变边缘 → 树状分岔线
edge_h=np.zeros((h,w),dtype=bool)
edge_v=np.zeros((h,w),dtype=bool)
edge_h[:,:-1]=(rz[:,1:]!=rz[:,:-1])&ext[:,:-1]&ext[:,1:]
edge_v[:-1,:]=(rz[1:,:]!=rz[:-1,:])&ext[:-1,:]&ext[1:,:]
tree_edge=edge_h|edge_v

# 3) 线条加粗(形态学膨胀)
if LINE_WIDTH > 1:
    dilated=tree_edge.copy()
    for _ in range(LINE_WIDTH-1):
        dilated[:,1:]|=dilated[:,:-1]
        dilated[:,:-1]|=dilated[:,1:]
        dilated[1:,:]|=dilated[:-1,:]
        dilated[:-1,:]|=dilated[1:,:]
    tree_edge=dilated

# ====== 构建图像 ======
img=np.full((h,w,3),1.0)  # 纯白底(参考图风格)

# 调试: pot值分布
pot_ext=pot[ext]
print(f"  pot stats: min={pot_ext.min():.1f}, max={pot_ext.max():.1f}, median={np.median(pot_ext):.1f}, <100={(pot_ext<100).sum()}, <50={(pot_ext<50).sum()}, <200={(pot_ext<200).sum()}")

# 层1: 树状分界线(深色细线，模拟参考图的连线)
img[tree_edge]=[0.15,0.12,0.28]

# 层2: 边界高密度区域(用逃逸迭代整数判断，低迭代=靠近集合边界)
bd_mask=~interior & (esc_iter < 80)
img[bd_mask & ~tree_edge]=[0.55,0.50,0.82]  # 淡蓝紫

# 层3: 内部纯白
img[interior]=1.0

fig,ax=plt.subplots(figsize=(8,8*h/w),dpi=150)
ax.set_facecolor('white'); fig.patch.set_facecolor('white')
ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],origin='lower',interpolation='nearest')
ax.axis('off'); plt.tight_layout(pad=0)
out=os.path.join(od,"UF1_二分棋盘格素描.png")
plt.savefig(out,dpi=200,bbox_inches='tight',facecolor='white'); plt.close()
print(f"UF1 tree-lines: ext={ext.sum()}, edges={tree_edge.sum()}, boundary={bd_mask.sum()} done -> {out}")
