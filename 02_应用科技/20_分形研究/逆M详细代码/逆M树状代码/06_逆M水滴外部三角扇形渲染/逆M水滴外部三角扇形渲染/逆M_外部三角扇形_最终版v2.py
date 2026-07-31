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
from PIL import Image, ImageDraw

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
# 多乘数对比: 0.1, 0.3, 0.5, 1.0
# ================================================================
print("[2/3] 4种乘数对比着色...")
t0 = time.time()

interior = ic >= MAX_ITER
exterior = ~interior

# 内部 (乘数不影响内部)
v_int = np.zeros(C.shape, dtype=np.float64)
with np.errstate(invalid='ignore', divide='ignore'):
    v_int_tmp = (np.log(trap + 1e-9) * 0.55) % 1.0
    v_int[interior] = 0.3 + 0.7 * v_int_tmp[interior]

# 外部基础数据
Z_re_e = Z_re[exterior]; Z_im_e = Z_im[exterior]
ic_e = ic[exterior]
nu = np.log2(np.log(np.maximum(Z_re_e*Z_re_e+Z_im_e*Z_im_e, 1e-30)) / 2 / math.log(2)) / math.log(2)

multipliers = [0.1, 0.3, 0.5, 1.0]
labels = ["×0.1", "×0.3", "×0.5", "×1.0"]
sub_imgs = []

for m in multipliers:
    v_arr = np.zeros(C.shape, dtype=np.float64)
    v_arr[interior] = v_int[interior]
    v_arr[exterior] = ((ic_e + 1 - nu) * m) % 1.0
    
    img = np.zeros((RES, RES, 3), dtype=np.uint8)
    vi = (v_arr * 255).astype(np.int32) % 256
    for c in range(3):
        img[:,:,c] = LUT[vi, c]
    # 实轴朝下
    img = img[::-1, :, :]
    sub_imgs.append(img)

# 保存各子图
sub_paths = []
for idx, (m, img) in enumerate(zip(multipliers, sub_imgs)):
    sp = os.path.join(OUT_DIR, f"_tmp_{m:.1f}.png")
    Image.fromarray(img).save(sp)
    sub_paths.append(sp)

# 拼成2×2 + 标签
HALF = RES // 2
full = np.zeros((RES, RES, 3), dtype=np.uint8)
for idx, (m, label, img) in enumerate(zip(multipliers, labels, sub_imgs)):
    sm = np.array(Image.fromarray(img).resize((HALF, HALF), Image.LANCZOS))
    r, c = idx // 2, idx % 2
    # 加白色半透明底标签
    sm_pil = Image.fromarray(sm).convert('RGBA')
    overlay = Image.new('RGBA', sm_pil.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    # 白色半透明底的矩形
    draw.rectangle([4, 4, 4 + len(label)*12, 28], fill=(20,30,60,200))
    draw.text((8, 6), label, fill=(255,255,255))
    sm_pil = Image.alpha_composite(sm_pil, overlay).convert('RGB')
    full[r*HALF:(r+1)*HALF, c*HALF:(c+1)*HALF] = np.array(sm_pil)

# 清理临时文件
for sp in sub_paths:
    try: os.remove(sp)
    except: pass

print(f"  {time.time()-t0:.1f}s")

# ================================================================
# 保存拼图
# ================================================================
print("[3/3] 保存拼图...")
out = os.path.join(OUT_DIR, "逆M_平滑乘数对比.png")
Image.fromarray(full, 'RGB').save(out)
sz = os.path.getsize(out) / 1024
print(f"  → {out}  ({sz:.0f}KB)")
print(f"  Done!")
