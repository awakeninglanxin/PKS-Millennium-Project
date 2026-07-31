#!/usr/bin/env python3
"""
逆M_梯度向外棋盘渲染
====================
核心: 用迭代梯度方向做向外辐射
      梯度∇ic指向iter增加(=水滴内部)
      -∇ic指向水滴外部 → 正确的向外辐射方向!
"""
import numpy as np, os, sys, math, time
from PIL import Image
from scipy.ndimage import gaussian_filter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RES = 1200; MAX_ITER = 400; R2 = 2500; ALPHA = -1.0

# LUT: 蓝→白→金
def make_lut():
    stops=[[5,10,50],[15,45,140],[40,100,220],[130,180,250],[220,230,245],
           [255,248,220],[255,220,140],[255,180,60],[200,110,20],[120,55,8]]
    lut=np.zeros((256,3),dtype=np.uint8);sn=len(stops)-1
    for i in range(256):
        t=i/255*sn;k=min(int(t),sn-1);f=t-k
        for c in range(3):lut[i,c]=int(stops[k][c]*(1-f)+stops[k+1][c]*f)
    return lut
LUT=make_lut()

print(f"[1/3] 逆M迭代 {RES}x{RES}")
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

# ── 梯度: ic的梯度指向水滴内部, 反向=向外 ──
print("[2/3] 梯度方向+着色...")
t0=time.time()
ic_float=ic.astype(np.float64)
gy,gx=np.gradient(ic_float)     # gy=∂ic/∂Y(Re), gx=∂ic/∂X(Im)

interior=ic>=MAX_ITER;exterior=~interior

# 内部: orbit trap
v_arr=np.zeros(C.shape,dtype=np.float64)
with np.errstate(invalid='ignore',divide='ignore'):
    v_int=(np.log(trap[interior]+1e-9)*0.55)%1.0
    v_arr[interior]=0.3+0.7*v_int

# 外部: 平滑 ×0.1
Zr_e=Zr[exterior];Zi_e=Zi[exterior];ic_e=ic[exterior]
nu=np.log2(np.log(np.maximum(Zr_e*Zr_e+Zi_e*Zi_e,1e-30))/2/math.log(2))/math.log(2)
v_smooth=((ic_e+1-nu)*0.1)%1.0

# ★ 梯度向外方向 ★
# 梯度(-gy,-gx)指向水滴外部
gx_e=-gx[exterior];gy_e=-gy[exterior]

# 16扇区射线
N_RAYS=16
ray_arg=np.arctan2(gx_e,gy_e)     # 梯度方向角
ray_idx=np.floor((ray_arg+math.pi)/(2*math.pi)*N_RAYS).astype(int)%N_RAYS
ray_parity=(ray_idx%2)==0
iter_parity=(ic_e%2)==1
checker=np.where(iter_parity,~ray_parity,ray_parity)

# 深蓝↔浅蓝
v_base=v_smooth
v_arr[exterior]=np.where(checker,
    0.15+0.55*v_base,     # 深蓝端
    0.40+0.55*v_base)     # 浅蓝端

# 映射到LUT
img=np.zeros((RES,RES,3),dtype=np.uint8)
vi=(v_arr*255).astype(np.int32)%256
for c in range(3):img[:,:,c]=LUT[vi,c]
img=img[::-1,:,:]  # 实轴朝下
print(f"  {time.time()-t0:.1f}s")

# 保存
print("[3/3] 保存...")
out=os.path.join(OUT_DIR,"逆M_梯度向外棋盘.png")
Image.fromarray(img,'RGB').save(out)
print(f"  → {out}  ({os.path.getsize(out)/1024:.0f}KB)")
