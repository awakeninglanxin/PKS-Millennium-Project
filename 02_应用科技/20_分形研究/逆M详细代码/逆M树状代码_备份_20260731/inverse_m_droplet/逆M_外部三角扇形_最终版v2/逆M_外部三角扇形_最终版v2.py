#!/usr/bin/env python3
"""
逆M_外部三角扇形_最终版v2.py
===========================
基于DNA_M集音乐探索器的算法精髓:
  外部: 平滑彩虹 + 二进制分解(arg(z)符号)→ 二分棋盘格
  内部: orbit trap 同心圆
  cmap: 蓝→白→金渐变
  实轴朝下 (flipud)
"""
import numpy as np, os, sys, math, time
from PIL import Image

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RES = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
MAX_ITER = 400
R2 = 2500
ALPHA = -1.0  # s=1 → 逆M

def make_lut_blue_gold():
    """蓝→白→金 256色LUT — 增强对比度"""
    stops = [
        [5, 10, 50],     # 0: 深蓝黑
        [15, 45, 140],   # 1: 蓝
        [40, 100, 220],  # 2: 亮蓝
        [130, 180, 250], # 3: 蓝白
        [220, 230, 245], # 4: 近白
        [255, 248, 220], # 5: 米白
        [255, 220, 140], # 6: 浅金
        [255, 180, 60],  # 7: 金
        [200, 110, 20],  # 8: 深金
        [120, 55, 8],    # 9: 棕
    ]
    lut = np.zeros((256, 3), dtype=np.uint8)
    seg_n = len(stops) - 1
    for i in range(256):
        t = i / 255 * seg_n
        k = min(int(t), seg_n - 1)
        f = t - k
        for c in range(3):
            lut[i, c] = int(stops[k][c] * (1 - f) + stops[k+1][c] * f)
    return lut

LUT = make_lut_blue_gold()

print(f"[1/3] 逆M迭代 {RES}x{RES}  MAX_ITER={MAX_ITER}")
t0 = time.time()

xs = np.linspace(-3.0, 3.0, RES, dtype=np.float64)  # 虚数轴Im, 对称中心0, 跨度=6.0 (axis_equal)
ys = np.linspace(-1.5, 4.5, RES, dtype=np.float64)  # 实数轴Re, 跨度=6.0 (axis_equal)
X, Y = np.meshgrid(xs, ys)
C = Y + 1j * X

# c_eff = c^alpha (alpha=-1 → 1/c)
r = np.abs(C)
r = np.maximum(r, 1e-13)
theta = np.angle(C)
rp = np.power(r, ALPHA)
aa = ALPHA * theta
ce_re = rp * np.cos(aa)
ce_im = rp * np.sin(aa)

Z_re = np.zeros_like(ce_re)
Z_im = np.zeros_like(ce_im)
ic = np.full(C.shape, MAX_ITER, dtype=np.int32)
trap = np.full(C.shape, 1e30, dtype=np.float64)
alive = np.ones(C.shape, dtype=bool)

for n in range(MAX_ITER):
    if not alive.any(): break
    zr = Z_re[alive]; zi = Z_im[alive]
    er = ce_re[alive]; ei = ce_im[alive]
    nzr = zr*zr - zi*zi + er
    nzi = 2*zr*zi + ei
    Z_re[alive] = nzr; Z_im[alive] = nzi
    m2 = nzr*nzr + nzi*nzi
    trap[alive] = np.minimum(trap[alive], m2)
    esc = m2 > R2
    ic[alive] = np.where(esc, n, ic[alive])
    alive[alive] = ~esc

print(f"  iter: [{ic.min()}, {ic.max()}]  {time.time()-t0:.1f}s")

# ================================================================
# 着色: 内部trap同心圆 + 外部smooth+二进制分解
# ================================================================
print("[2/3] 着色...")
t0 = time.time()

v_arr = np.zeros(C.shape, dtype=np.float64)
interior = ic >= MAX_ITER
exterior = ~interior

# 内部: orbit trap 同心圆 + 提升亮度
with np.errstate(invalid='ignore', divide='ignore'):
    v_int = (np.log(trap[interior] + 1e-9) * 0.55) % 1.0
    # 提升内部亮度: trap值小的区域(近核) = 亮, trap大的区域 = 暗金
    v_arr[interior] = 0.3 + 0.7 * v_int

# 外部: 平滑彩虹 + 二进制分解 (从水滴边缘向外outward)
Z_re_e = Z_re[exterior]; Z_im_e = Z_im[exterior]
ic_e = ic[exterior]

# 平滑重整化
nu = np.log2(np.log(np.maximum(Z_re_e*Z_re_e+Z_im_e*Z_im_e, 1e-30)) / 2 / math.log(2)) / math.log(2)
v_smooth = (ic_e + 1 - nu) * 0.132

# ★ 二进制分解: arg(C) 从全局原点(0,0)向外辐射 ★
# arg(C) = atan2(Im, Re) = atan2(X, Y)  因为 C = Y + jX
# X=Im轴(水平), Y=Re轴(垂直)
arg_out = np.arctan2(X[exterior], Y[exterior])
N_RAYS = 16  # 16条射线 → 8对交替棋盘向外辐射
ray_idx = np.floor((arg_out + np.pi) / (2 * np.pi) * N_RAYS).astype(int) % N_RAYS
ray_parity = (ray_idx % 2) == 0
# XOR with iter奇偶: 相邻环带棋盘交替
iter_parity = (ic_e % 2) == 1
checker = np.where(iter_parity, ~ray_parity, ray_parity)

# 外部: 平滑色带 + 二进制棋盘(蓝←→金强对比)
# 状态0: 映射到LUT蓝白端 [0, 0.5)
# 状态1: 映射到LUT金端 [0.5, 1.0)
# => 棋盘格=蓝白交替vs金 → 视觉上极其清晰
v_base = v_smooth % 1.0
v_arr[exterior] = np.where(checker, 0.5 + 0.5 * v_base, 0.5 * v_base)

# 映射到 LUT
img = np.zeros((RES, RES, 3), dtype=np.uint8)
vi = (v_arr * 255).astype(np.int32) % 256
for c in range(3):
    img[:,:,c] = LUT[vi, c]

# 实轴朝下 (flip vertical)
img = img[::-1, :, :]

print(f"  {time.time()-t0:.1f}s")

# ================================================================
# 保存
# ================================================================
print("[3/3] 保存...")
out = os.path.join(OUT_DIR, "逆M_外部三角扇形_最终版v2.png")
Image.fromarray(img, 'RGB').save(out)
sz = os.path.getsize(out) / 1024
print(f"  → {out}  ({sz:.0f}KB)")
print(f"  Done!")
