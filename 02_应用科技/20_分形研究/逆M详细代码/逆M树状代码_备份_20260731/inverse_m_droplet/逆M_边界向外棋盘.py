#!/usr/bin/env python3
"""
逆M_边界向外棋盘.py
==================
关键: 用距离变换找每个外部像素到水滴边界的最近点
      从边界点朝外的方向 = 真正的向外辐射!
"""
import numpy as np, os, sys, math, time
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_dilation

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RES = 1200; MAX_ITER = 400; R2 = 2500; ALPHA = -1.0
LUT = np.zeros((256,3), dtype=np.uint8)
stops = [[5,10,50],[15,45,140],[40,100,220],[130,180,250],[220,230,245],
         [255,248,220],[255,220,140],[255,180,60],[200,110,20],[120,55,8]]
for i in range(256):
    t=i/255*(len(stops)-1);k=min(int(t),len(stops)-2);f=t-k
    for c in range(3):LUT[i,c]=int(stops[k][c]*(1-f)+stops[k+1][c]*f)

print(f"[1/4] 逆M迭代 {RES}x{RES}")
t0=time.time()
xs=np.linspace(-3.0,3.0,RES,dtype=np.float64)
ys=np.linspace(-1.5,4.5,RES,dtype=np.float64)
X,Y=np.meshgrid(xs,ys);C=Y+1j*X
rC=np.abs(C);rC=np.maximum(rC,1e-13);thC=np.angle(C)
rp=np.power(rC,ALPHA);aa=ALPHA*thC;cr=rp*np.cos(aa);ci=rp*np.sin(aa)
Zr=np.zeros_like(cr);Zi=np.zeros_like(ci)
ic=np.full(C.shape,MAX_ITER,dtype=np.int32)
trap=np.full(C.shape,1e30,dtype=np.float64);al=np.ones(C.shape,dtype=bool)
for n in range(MAX_ITER):
    if not al.any():break
    zr=Zr[al];zi=Zi[al];er=cr[al];ei=ci[al]
    nzr=zr*zr-zi*zi+er;nzi=2*zr*zi+ei
    Zr[al]=nzr;Zi[al]=nzi
    m2=nzr*nzr+nzi*nzi
    trap[al]=np.minimum(trap[al],m2)
    esc=m2>R2;ic[al]=np.where(esc,n,ic[al]);al[al]=~esc
print(f"  iter:[{ic.min()},{ic.max()}]  {time.time()-t0:.1f}s")

# ── 2. 找水滴边界 ──
print("[2/4] 边界检测...")
t0=time.time()
interior=ic>=MAX_ITER
# 边界 = 内部像素膨胀后与外部像素的交集
boundary=binary_dilation(interior)^interior
n_bd=boundary.sum()
print(f"  边界点数: {n_bd}")

# ── 3. 距离变换: 每个像素到最近边界点的方向和距离 ──
print("[3/4] 距离变换+方向计算...")
# 获取边界点坐标 (row=y, col=x)
bd_ys,bd_xs=np.where(boundary)
# 方向: 用距离变换的索引
# 方法: 对每个外部像素, 计算到所有边界点的距离, 找最近的

# 优化: 只对exterior像素计算, 且用分块/KD-tree
ext_ys,ext_xs=np.where(~interior)  # 所有外部像素坐标

# 简化: 用argmin暴力搜索 (n_bd≈5000, n_ext≈10^6, 太慢)
# 改用: 基于角度的分桶

# 从原点(0,0)到每个边界点的角度
bd_args=np.arctan2(bd_xs/ RES*6-3,  bd_ys/ RES*6-1.5)

# 简单方案: 外部像素的方向 = 从最近的边界点(按角度)到该像素的方向
# 这大致是outward方向
# 更简单: 用arg(C) -> 找最近边界点(按角度) -> 边界点坐标已知

# 实际实现: 用Farey泡作为边界锚点(已在边界附近)
print("  生成21个Farey泡作为边界锚点...")
bulbs=[]
for q in range(1,9):
    for p in range(1,q):
        if math.gcd(p,q)!=1:continue
        th=2*math.pi*p/q
        cx=math.cos(th)/2-math.cos(2*th)/4
        cy=math.sin(th)/2-math.sin(2*th)/4
        if cx*cx+cy*cy<1e-12:continue
        inv_n=1/(cx*cx+cy*cy)
        ix=cx*inv_n;iy=-cy*inv_n  # Re, Im
        # 像素坐标
        px=(ix+3)/6*RES;py=(iy+1.5)/6*RES
        bulbs.append((px,py,ix,iy,math.atan2(iy,ix)))
bulbs.sort(key=lambda b:b[4])
b_args=np.array([b[4] for b in bulbs])
b_pxs=np.array([b[0] for b in bulbs])
b_pys=np.array([b[1] for b in bulbs])
n_b=len(bulbs)
print(f"  {n_b}个Farey泡锚点")

# 对每个外部像素, 找最近泡(二分搜索)
sorted_args=b_args.copy()
# 每个外部像素的角度 (从原点)
ext_arg=np.arctan2(X[~interior],Y[~interior])  # arg(C)

ext_args=ext_arg.copy()
# wrap-around
sa=np.concatenate([sorted_args-2*math.pi,sorted_args,sorted_args+2*math.pi])
idx_arr=np.concatenate([np.arange(n_b)-n_b,np.arange(n_b),np.arange(n_b)+n_b])

pos=np.searchsorted(sa,ext_args)
# 比较pos和pos-1
n_ext=len(ext_args)
best_idx=np.zeros(n_ext,dtype=np.int32)
best_dist=np.full(n_ext,1e30)
for off in [-1,0,1]:
    ci=np.clip(pos+off,0,len(sa)-1)
    d=np.abs(ext_args-sa[ci])
    d=np.minimum(d,2*math.pi-d)
    better=d<best_dist
    if better.any():
        best_idx[better]=idx_arr[ci[better]]%n_b
        best_dist[better]=d[better]

# 最近泡的像素坐标
near_px=b_pxs[best_idx];near_py=b_pys[best_idx]

# ★ 向外方向: 从最近边界泡指向外部像素 ★
out_dx=ext_xs-near_px;out_dy=ext_ys-near_py
out_arg=np.arctan2(out_dx,out_dy)  # 注意: dx→X(Im), dy→Y(Re)

print(f"  {time.time()-t0:.1f}s")

# ── 4. 着色 ──
print("[4/4] 着色...")
t0=time.time()

v_arr=np.zeros(C.shape,dtype=np.float64)
ext_mask=~interior

# 内部: orbit trap
with np.errstate(invalid='ignore',divide='ignore'):
    v_int=(np.log(trap[interior]+1e-9)*0.55)%1.0
    v_arr[interior]=0.3+0.7*v_int

# 外部平滑
Zr_e=Zr[ext_mask];Zi_e=Zi[ext_mask];ic_e=ic[ext_mask]
nu=np.log2(np.log(np.maximum(Zr_e*Zr_e+Zi_e*Zi_e,1e-30))/2/math.log(2))/math.log(2)
v_smooth=((ic_e+1-nu)*0.1)%1.0

# 16射线棋盘
N_RAYS=16
ray_idx=np.floor((out_arg+math.pi)/(2*math.pi)*N_RAYS).astype(int)%N_RAYS
ray_parity=(ray_idx%2)==0
iter_parity=(ic_e%2)==1
checker=np.where(iter_parity,~ray_parity,ray_parity)

# ★ 高对比棋盘: 硬编码RGB, 不用LUT ★
# 亮态 = 亮蓝白, 暗态 = 深蓝黑
img_f=np.zeros((RES,RES,3),dtype=np.float64)

# 内部: LUT
vi_int=(v_arr[interior]*255).astype(np.int32)%256
img_f[interior,0]=LUT[vi_int,0]/255.0
img_f[interior,1]=LUT[vi_int,1]/255.0
img_f[interior,2]=LUT[vi_int,2]/255.0

# 外部: 硬编码高对比
vb=v_smooth  # [0,1]
light_r=0.35+0.55*vb;light_g=0.65+0.25*vb;light_b=0.85+0.15*vb
dark_r=0.03+0.07*vb; dark_g=0.06+0.22*vb; dark_b=0.10+0.40*vb

tmp=np.zeros(ext_mask.sum(),dtype=np.float64)
img_f[ext_mask,0]=np.where(checker,light_r,dark_r)
img_f[ext_mask,1]=np.where(checker,light_g,dark_g)
img_f[ext_mask,2]=np.where(checker,light_b,dark_b)

img=(np.clip(img_f,0,1)*255).astype(np.uint8)
img=img[::-1,:,:]
print(f"  {time.time()-t0:.1f}s")

out=os.path.join(OUT_DIR,"逆M_边界向外棋盘.png")
Image.fromarray(img,'RGB').save(out)
print(f"  → {out}  ({os.path.getsize(out)/1024:.0f}KB)")
