#!/usr/bin/env python3
"""
逆M_Farey泡向外棋盘渲染
========================
基于×0.1平滑 + 16射线Farey泡对齐二分棋盘
"""
import numpy as np, os, sys, math, time
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RES = 1200
MAX_ITER = 400
R2 = 2500
ALPHA = -1.0

# ── 蓝→白→金 LUT (保留，但棋盘用浅蓝/深蓝) ──
LUT_BW = np.zeros((256,3), dtype=np.uint8)
stops = [[5,10,50],[15,45,140],[40,100,220],[130,180,250],[220,230,245],
         [255,248,220],[255,220,140],[255,180,60],[200,110,20],[120,55,8]]
sn = len(stops)-1
for i in range(256):
    t=i/255*sn; k=min(int(t),sn-1); f=t-k
    for c in range(3): LUT_BW[i,c]=int(stops[k][c]*(1-f)+stops[k+1][c]*f)

# ── 1. 生成Farey泡 ──
def gen_farey_bulbs(max_q):
    """生成所有Farey分数p/q(q≤max_q)在主心形上泡的中心"""
    bulbs = []
    for q in range(1, max_q+1):
        for p in range(1, q):
            if math.gcd(p,q)!=1: continue  # 只取最简分数
            # 泡中心: c = e^(2πi p/q)/2 - e^(4πi p/q)/4
            th = 2*math.pi*p/q
            cx = math.cos(th)/2 - math.cos(2*th)/4
            cy = math.sin(th)/2 - math.sin(2*th)/4
            # 反演: 1/c
            if cx*cx+cy*cy<1e-12: continue
            inv_norm = 1/(cx*cx+cy*cy)
            ix = cx*inv_norm  # Re
            iy = -cy*inv_norm  # Im
            arg = math.atan2(iy, ix)  # 从原点的角度
            bulbs.append((p,q,cx,cy,ix,iy,arg))
    # 按角度排序
    bulbs.sort(key=lambda b: b[6])
    return bulbs

print("[0/4] 生成Farey泡...")
BULBS = gen_farey_bulbs(8)
print(f"  {len(BULBS)}个泡 (q≤8)")
for p,q,_,_,ix,iy,arg in BULBS[:10]:
    print(f"    p/q={p}/{q} → inv=({ix:.3f},{iy:.3f}) arg={math.degrees(arg):.0f}°")

# ── 2. 逆M迭代 ──
print(f"\n[1/4] 逆M迭代 {RES}x{RES}")
t0=time.time()
xs=np.linspace(-3.0,3.0,RES,dtype=np.float64)
ys=np.linspace(-1.5,4.5,RES,dtype=np.float64)
X,Y=np.meshgrid(xs,ys);C=Y+1j*X
rC=np.abs(C);rC=np.maximum(rC,1e-13)
thC=np.angle(C);rp=np.power(rC,ALPHA);aa=ALPHA*thC
cr=rp*np.cos(aa);ci=rp*np.sin(aa)
Zr=np.zeros_like(cr);Zi=np.zeros_like(ci)
ic=np.full(C.shape,MAX_ITER,dtype=np.int32)
trap=np.full(C.shape,1e30,dtype=np.float64)
al=np.ones(C.shape,dtype=bool)
for n in range(MAX_ITER):
    if not al.any():break
    zr=Zr[al];zi=Zi[al];er=cr[al];ei=ci[al]
    nzr=zr*zr-zi*zi+er;nzi=2*zr*zi+ei
    Zr[al]=nzr;Zi[al]=nzi
    m2=nzr*nzr+nzi*nzi
    trap[al]=np.minimum(trap[al],m2)
    esc=m2>R2;ic[al]=np.where(esc,n,ic[al]);al[al]=~esc
print(f"  iter: [{ic.min()},{ic.max()}]  {time.time()-t0:.1f}s")

# ── 3. 着色 ──
print("[2/4] 着色...")
t0=time.time()

v_arr=np.zeros(C.shape,dtype=np.float64)
interior=ic>=MAX_ITER;exterior=~interior
Zr_e=Zr[exterior];Zi_e=Zi[exterior];ic_e=ic[exterior]

# 内部: orbit trap (保持不变)
with np.errstate(invalid='ignore',divide='ignore'):
    v_int=(np.log(trap[interior]+1e-9)*0.55)%1.0
    v_arr[interior]=0.3+0.7*v_int

# 外部平滑 (×0.1)
nu=np.log2(np.log(np.maximum(Zr_e*Zr_e+Zi_e*Zi_e,1e-30))/2/math.log(2))/math.log(2)
v_smooth=((ic_e+1-nu)*0.1)%1.0

# ── Farey泡对齐的16射线二分棋盘 ──
# 对每个外部像素, 找最近Farey泡, 用相对角度做16扇区
n_bulbs=len(BULBS)
b_args=np.array([b[6] for b in BULBS])  # 各泡角度

# 每个外部像素的角度
pix_arg=np.arctan2(X[exterior],Y[exterior])  # arg(C)

# 找最近泡: 用二分搜索(bulbs已按角度排序)
# 对每个像素的arg, 找最近的两个泡, 取角度差最小的
sorted_args = b_args.copy()
# 处理wrap-around: 复制[-π,π]到两侧
ext_args = np.concatenate([sorted_args - 2*math.pi, sorted_args, sorted_args + 2*math.pi])
ext_idx = np.arange(-n_bulbs, 2*n_bulbs)

# 对每个像素角度, 找最近泡
# 用searchsorted在ext_args中找插入位置
pos = np.searchsorted(ext_args, pix_arg)
# 检查pos和pos-1两个候选
candidates = []
for offset in [-1, 0]:
    ci = np.clip(pos + offset, 0, len(ext_args)-1)
    ca = ext_args[ci]
    cd = np.abs(pix_arg - ca)
    cd = np.minimum(cd, 2*math.pi - cd)
    candidates.append((ext_idx[ci], ca, cd))

nearest_idx = np.where(candidates[0][2] <= candidates[1][2],
                       candidates[0][0], candidates[1][0]) % n_bulbs
# 用sorted_args取实际泡角度(不是扩展数组的)
nearest_arg = sorted_args[nearest_idx.astype(int)]

# 相对角度: 像素角 - 泡角 (归一化到[-π,π])
rel_arg=np.arctan2(np.sin(pix_arg-nearest_arg),np.cos(pix_arg-nearest_arg))

# 16扇区: 每个泡的扇区 = floor((rel_arg+π) / (2π) * 16)
N_RAYS=16
ray_idx=np.floor((rel_arg+math.pi)/(2*math.pi)*N_RAYS).astype(int)%N_RAYS
ray_parity=(ray_idx%2)==0

# XOR迭代奇偶
iter_parity=(ic_e%2)==1
checker=np.where(iter_parity,~ray_parity,ray_parity)

# ── 颜色: 棋盘状态0→浅蓝, 状态1→深蓝 ──
# 用平滑值作为v_base, 然后映射到浅蓝或深蓝范围
v_base=v_smooth

# 构建浅蓝-深蓝LUT子集
# 浅蓝: LUT_BW[40:148], 深蓝: LUT_BW[0:108]
light_blue_lut=LUT_BW[40:148]  # 108色: 亮蓝到蓝白
dark_blue_lut=LUT_BW[0:108]    # 108色: 深蓝到蓝

v_arr[exterior]=np.where(checker,
    # 深蓝: 映射到LUT蓝黑端
    0.2+0.6*v_base,
    # 浅蓝: 映射到LUT白蓝端
    0.4+0.6*v_base)

# 映射到LUT
img=np.zeros((RES,RES,3),dtype=np.uint8)
vi=(v_arr*255).astype(np.int32)%256
for c in range(3): img[:,:,c]=LUT_BW[vi,c]
img=img[::-1,:,:]  # 实轴朝下

print(f"  {time.time()-t0:.1f}s")

# ── 保存 ──
print("[3/4] 保存...")
out=os.path.join(OUT_DIR,"逆M_Farey棋盘_最终版.png")
Image.fromarray(img,'RGB').save(out)
sz=os.path.getsize(out)/1024
print(f"  → {out}  ({sz:.0f}KB)")

# ── 附: 泡位置标记图(调试) ──
print("[4/4] 生成泡位置标记图...")
mark=np.ones((RES,RES,3),dtype=np.uint8)*20
# 映射泡位置到像素
h_half,w_half=RES//2,RES//2
for p,q,_,_,ix,iy,arg in BULBS:
    # 坐标: Re=Y[-1.5,4.5]→row, Im=X[-3,3]→col
    # 但已经flipud过了, 所以:
    px=int((ix+3)/6*RES)  # Im→col
    py=int((iy+1.5)/6*RES)  # Re→row (未flip前)
    if 0<=px<RES and 0<=py<RES:
        # 画小圆
        for dy in range(-4,5):
            for dx in range(-4,5):
                if dx*dx+dy*dy<=16:
                    yy=RES-1-py if True else py  # flipud
                    # 标记用彩色
                    if 0<=yy<RES and 0<=px+dx<RES and 0<=yy+dy<RES:
                        yy2=yy+dy
                        if 0<=yy2<RES and 0<=px+dx<RES:
                            mark[yy2,px+dx]=[255,200,80]

Image.fromarray(mark,'RGB').save(os.path.join(OUT_DIR,"_泡位置标记.png"))
print(f"  Done!")
