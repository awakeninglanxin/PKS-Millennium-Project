#!/usr/bin/env python3
"""路线B: GPU加速 — TIA自动定位Farey中心 × 每泡独立棋盘 × 金涟漪
   RTX 4090 + CuPy 全GPU并行"""
import cupy as cp, numpy as np, math, cmath, os, time
from PIL import Image, ImageDraw
from scipy.ndimage import zoom, label, minimum_filter

OUT_DIR = "/root/invM_v4"
os.makedirs(OUT_DIR, exist_ok=True)
W, H = 2400, 2400
SCALE = 200
CX, CY = 0.0, 0.0
MAX_ITER = 400
R2 = 1024

# ═══ 1. GPU TIA + pot 全场计算 ═══
print("[1] GPU全场: TIA + pot 计算...")
t0 = time.time()

# 坐标网格 → GPU
xs = cp.linspace(-W/2/SCALE, W/2/SCALE, W//2, dtype=cp.float64)
ys = cp.linspace(-H/2/SCALE, H/2/SCALE, H//2, dtype=cp.float64)
X, Y = cp.meshgrid(xs, ys)
C = (X + 1j * Y)  # 像素坐标对应的复平面点, GPU上

# 逆M映射: c_eff = 1/c
rC = cp.abs(C); rC = cp.maximum(rC, 1e-13)
thC = cp.angle(C)
ce = (rC ** (-1.0)) * cp.exp(1j * (-1.0) * thC)

zr = cp.zeros_like(ce); zi = cp.zeros_like(ce)
alive = cp.ones(ce.shape, dtype=bool)
esc_iter = cp.full(ce.shape, MAX_ITER, dtype=cp.int32)
tia_sum = cp.zeros(ce.shape, dtype=cp.float64)
tia_cnt = cp.zeros(ce.shape, dtype=cp.int32)

for n in range(MAX_ITER):
    if not cp.any(alive): break
    # 取活像素
    za = zr[alive] + 1j * zi[alive]
    ca = ce[alive]
    zn = za * za + ca  # 标准迭代

    # TIA: r_n = |z_{n+1} - z_n| / |z_{n+1}|
    rn = cp.abs(zn - za) / (cp.abs(zn) + 1e-30)
    tia_sum[alive] += rn
    tia_cnt[alive] += 1

    zr[alive] = cp.real(zn); zi[alive] = cp.imag(zn)
    m2 = cp.real(zn)**2 + cp.imag(zn)**2
    esc = m2 > R2
    esc_iter[alive] = cp.where(esc, n, esc_iter[alive])
    alive[alive] = ~esc

# CPU转移
esc_iter_cpu = cp.asnumpy(esc_iter)
tia_sum_cpu = cp.asnumpy(tia_sum)
tia_cnt_cpu = cp.asnumpy(tia_cnt)
zr_cpu = cp.asnumpy(zr); zi_cpu = cp.asnumpy(zi)
del C, ce, zr, zi, X, Y, tia_sum, tia_cnt, alive; cp.get_default_memory_pool().free_all_blocks()

print(f"  GPU迭代: {time.time()-t0:.1f}s")

# ═══ 2. TIA平均 + 水滴内部分割 ═══
print("[2] TIA平均 + 水滴内部mask...")
ext_mask = esc_iter_cpu < MAX_ITER  # 逃逸 = 水滴外部
int_mask = esc_iter_cpu == MAX_ITER  # 从未逃逸 = 水滴内部 ← 正确!
tia = np.where(tia_cnt_cpu > 0, tia_sum_cpu / np.maximum(tia_cnt_cpu, 1), 0.0)
m2f = zr_cpu**2 + zi_cpu**2
pot = np.zeros_like(m2f)
pot[ext_mask] = MAX_ITER - 1 - np.log2(np.maximum(np.log2(np.maximum(m2f[ext_mask], 1e-30))/2, 1e-12))
pot = np.clip(pot, 0, None)
tia_full = zoom(tia, (W/tia.shape[0], W/tia.shape[1]), order=1)
int_full = zoom(int_mask.astype(np.float64), (W/tia.shape[0], W/tia.shape[1]), order=0) > 0.5

# 用水滴边界框过滤: 只在水滴内部找极小值
XS_big, YS_big = np.meshgrid(np.linspace(-W/2/SCALE,W/2/SCALE,W), np.linspace(-H/2/SCALE,H/2/SCALE,H))
in_droplet = (XS_big > -1.5) & (XS_big < 4.2) & (np.abs(YS_big) < 1.8) & int_full
tia_masked = np.where(in_droplet, tia_full, 1e30)
print(f"  水滴内部搜索区: {in_droplet.sum()}像素")
# 局部极小值 (size=5)
local_min = (tia_masked == minimum_filter(tia_masked, size=3)) & in_droplet
labeled, n_features = label(local_min)
centers = []
for i in range(1, n_features+1):
    ys_idx, xs_idx = np.where(labeled == i)
    if len(ys_idx) >= 3:
        cy = ys_idx.mean(); cx = xs_idx.mean()
        cr = CX + (cx - W/2) / SCALE
        ci = CY + (cy - H/2) / SCALE
        centers.append((cx, cy, cr, ci, tia_full[int(cy), int(cx)]))
print(f"  检测到{len(centers)}个Farey泡中心")

# ═══ 4. 每泡独立局部棋盘 ═══
print("[4] 每泡独立棋盘 + 波场叠加...")
RING_COUNT = 6  # 每泡周围6个棋盘环
modulation = np.ones((W, H), dtype=np.float64)
XX, YY = np.meshgrid(np.arange(W), np.arange(H))

# 从每个检测到的中心发出局部棋盘格
for idx, (cx, cy, cr, ci, tval) in enumerate(centers):
    # 距离场
    dx = XX - cx; dy = YY - cy
    dist = np.sqrt(dx*dx + dy*dy)
    # 截止半径: 随TIA值变化 (越小的TIA=越深的泡=半径越大)
    max_radius = 60 + 40 / (1 + tval*2)  # ~60-100px
    # 局部波长
    wlen = max(6, 30 / (1 + tval*5))  # TIA越小→波长越长
    # 棋盘
    mask = dist <= max_radius
    if not mask.any(): continue
    d = dist[mask]
    p_local = (d / wlen) % 1.0  # 局部势能(距离模)
    # 取模二值: 棋盘=1时衰减
    binary = np.floor(p_local / 0.5).astype(int)
    modulation[mask] = np.where(binary == 1, 
        np.minimum(modulation[mask], 0.35),
        modulation[mask])
    if (idx+1) % 20 == 0: print(f"  泡 {idx+1}/{len(centers)}...")

print(f"  {len(centers)}个泡中心棋盘完成")

# ═══ 5. 生成金涟漪(简化,用已知32泡中心) ═══
print("[5] 金涟漪场...")
upper = []
for i in range(91):
    th = math.pi*i/90
    ca = 0.5*cmath.exp(1j*th) - 0.25*cmath.exp(2j*th)
    for expand in [1.12, 1.30, 1.55, 1.80, 2.10]:
        co = ca * expand
        if abs(co) < 1e-12: continue
        ci_val = 1.0/co
        if abs(ci_val.real)<6 and abs(ci_val.imag)<5:
            upper.append((ci_val.real, abs(ci_val.imag)))
for ci in [(2,-1.0,0),(2,-0.122561,0.744862),(3,-0.156520,1.032247),
           (3,0.282000,0.530000),(4,-0.504340,0.562765),(4,0.379280,0.334020),
           (5,0.374400,0.367200),(5,-0.163423,0.577597),(5,-0.044987,1.050261),
           (6,0.365640,0.291010),(6,0.220328,0.465829),(7,0.366218,0.250745),
           (7,0.389000,0.216000),(8,0.373000,0.225000),(9,0.382000,0.201000)]:
    c = complex(ci[1], ci[2])
    if abs(c)<1e-12: continue
    cv = 1.0/c
    if abs(cv.real)<6 and abs(cv.imag)<5: upper.append((cv.real, abs(cv.imag)))

# 镜像
sources = []
for cr, ci_v in upper:
    sources.append((cr, ci_v))
    if abs(ci_v)>1e-6: sources.append((cr, -ci_v))

# 金涟漪波场
RH2, RW2 = H//4, W//4
XX2, YY2 = np.meshgrid(np.linspace(-W/2, W/2, RW2), np.linspace(-H/2, H/2, RH2))
rf = np.zeros((RH2, RW2), dtype=np.float64)
for cr, ci_v in sources:
    bx = cr*SCALE; by = ci_v*SCALE
    dx = XX2 - bx; dy = YY2 - by; dist = np.sqrt(dx*dx + dy*dy)
    cutoff = 2000; mask = dist <= cutoff
    if not mask.any(): continue
    d = dist[mask]
    rw = np.sin(2*math.pi*d/120)/(1+d/600)*np.exp(-d/500*1.5)
    rf[mask] += rw
rf = np.abs(rf); rf = rf/(rf.max()+1e-30); rf = rf**0.6
rf_big = zoom(rf, (W/RH2, W/RW2), order=1)

# 调制
ripple = np.clip(rf_big, 0, 1) * modulation
# 金的颜色
gold_r, gold_g, gold_b = 218, 165, 32
rr = gold_r + (255-gold_r)*(1-ripple)
gg = gold_g + (255-gold_g)*(1-ripple)
rb = gold_b + (255-gold_b)*(1-ripple)
alpha_g = ripple * 0.6

# ═══ 6. 渲染 ═══
print("[6] 渲染...")
img = np.zeros((W, H, 4), dtype=np.uint8)
for c, wv in enumerate([0.22, 0.16, 0.06]):
    img[:,:,c] = 255  # 白底
img[:,:,0] = (img[:,:,0]*(1-alpha_g) + rr*alpha_g).astype(np.uint8)
img[:,:,1] = (img[:,:,1]*(1-alpha_g) + gg*alpha_g).astype(np.uint8)
img[:,:,2] = (img[:,:,2]*(1-alpha_g) + rb*alpha_g).astype(np.uint8)
img[:,:,3] = 255

# 轮廓
pts_c = []; pts2 = []
for i in range(2001):
    th = 2*math.pi*i/2000
    c2 = 0.5*cmath.exp(1j*th)-0.25*cmath.exp(2j*th); cvi=1.0/c2
    pts_c.append((int(W/2+cvi.real*SCALE*W/W), int(H/2-cvi.imag*SCALE*H/H)))
for i in range(801):
    th = 2*math.pi*i/800
    c2 = math.cos(th)/4+1j*math.sin(th)/4-1; cvi=1.0/c2
    pts2.append((int(W/2+cvi.real*SCALE*W/W), int(H/2-cvi.imag*SCALE*H/H)))

img_pil = Image.fromarray(img, 'RGBA')
draw = ImageDraw.Draw(img_pil)
draw.line(pts_c, fill=(60,60,100,180), width=4)
draw.line(pts2, fill=(180,120,40,150), width=3)

# TIA检测到的泡中心标记
for cx, cy, cr, ci, tval in centers[:60]:
    px = int(cx); py = int(cy)
    if 0<=px<W and 0<=py<H:
        draw.ellipse([px-2,py-2,px+2,py+2], fill=(255,80,80,180))

draw.text((10,10), f"路线B: TIA自动检测{len(centers)}个Farey中心 + 独立棋盘 + 金涟漪", fill=(60,60,80,200))
img_pil = img_pil.rotate(90, expand=True, resample=Image.BILINEAR, fillcolor=(255,255,255,255))

out = os.path.join(OUT_DIR, "invM_RouteB_GPU.png")
img_pil.save(out)
print(f"\n→ {out}  ({os.path.getsize(out)//1024}KB)")
print(f"总耗时: {time.time()-t0:.0f}s")
