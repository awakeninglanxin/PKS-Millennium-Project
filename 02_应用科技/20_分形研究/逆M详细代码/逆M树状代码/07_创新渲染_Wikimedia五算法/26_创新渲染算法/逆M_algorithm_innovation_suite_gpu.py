#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M算法创新渲染套件 v7 - GPU等轴比版 ★ axis_equal修复

v7修复的核心问题:
- v6虽然用了RES×RES方块，但实轴跨度≠虚轴跨度 → 像素的物理"尺"不一样 → 非等轴比
- axis_equal正确方案: 让实轴和虚轴在每个像素上的物理长度相等
  即: (RE_MAX-RE_MIN)/w == (IM_MAX-IM_MIN)/h → 必须同比例缩放
- 由于水滴是"纵向拉伸"的(高>宽)，要达到等轴比需:
  方案A: 缩放宽→用较小的轴跨度作为统一尺度
  方案B: 拉伸高→让虚轴范围等于实轴范围  
  ✅ 采用方案A: 统一用较小跨度，保持原始视野
  
旋转: np.rot90(k=2) → 水滴朝上 ✓
"""
import numpy as np, os, sys, time
from scipy.signal import convolve2d
from PIL import Image

RES = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════
# v7 修复: 等轴比 (aspect_ratio=1)
# ═══════════════════════════════════════════════════════════
# 原始取景
TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.50
RE_RAW_MIN, RE_RAW_MAX = BOTTOM-MARGIN, TIP+MARGIN
IM_RAW_MIN, IM_RAW_MAX = -HSPAN-MARGIN, HSPAN+MARGIN

# 计算原始跨度
re_span = RE_RAW_MAX - RE_RAW_MIN  # ≈ 9.0
im_span = IM_RAW_MAX - IM_RAW_MIN  # ≈ 4.24

# 取较小跨度作为统一尺度 → 确保每个像素的实/虚轴物理长度相等
uni_span = min(re_span, im_span)

# 以中心为基准等比例缩放
RE_CENTER = (RE_RAW_MIN + RE_RAW_MAX) / 2
IM_CENTER = (IM_RAW_MIN + IM_RAW_MAX) / 2

RE_MIN = RE_CENTER - uni_span/2
RE_MAX = RE_CENTER + uni_span/2
IM_MIN = IM_CENTER - uni_span/2
IM_MAX = IM_CENTER + uni_span/2

# 验证: 现在 re_span == im_span == uni_span → axis_equal ✓
MAX_ITER = 250; BAILOUT_SQ = 256**2

def compute_inverse_m(w, h):
    """逆M集迭代: z² + 1/c — 等轴比版"""
    x = np.linspace(RE_MIN, RE_MAX, w)
    y = np.linspace(IM_MIN, IM_MAX, h)
    X, Y = np.meshgrid(x, y)
    co = X + 1j*Y
    safe = np.abs(co) > 1e-12
    ce = np.zeros_like(co, dtype=np.complex128)
    ce[safe] = 1.0/co[safe]; ce[~safe] = 1e6+0j
    z = np.zeros_like(ce, dtype=np.complex128)
    dz = np.zeros_like(ce, dtype=np.complex128)
    ic = np.full(ce.shape, MAX_ITER, dtype=np.float64)
    trap = np.full(ce.shape, 1e30, dtype=np.float64)
    alive = np.ones(ce.shape, dtype=bool)
    for i in range(MAX_ITER):
        if not alive.any(): break
        idx = np.where(alive)
        za, ca, dza = z[idx], ce[idx], dz[idx]
        dza = 2*za*dza + 1; za = za*za + ca
        m2 = za.real**2 + za.imag**2
        trap[idx] = np.minimum(trap[idx], m2)
        z[idx] = za; dz[idx] = dza
        esc = m2 > BAILOUT_SQ
        ic[idx] = np.where(esc, i, ic[idx])
        alive[idx] &= ~esc
    interior = ~alive
    return ic, trap, z, dz, interior, co

def hsv_to_rgb(hue, sat=None, val=None):
    c = val * sat; x = c * (1 - np.abs((hue * 6) % 2 - 1)); m = val - c
    hh = (hue * 6) % 6
    r = m + np.where(hh < 1, c, np.where(hh < 2, x, 0))
    g = m + np.where(hh < 3, c, np.where(hh < 4, x, 0))
    b = m + np.where(hh < 5, c, np.where(hh < 6, x, 0))
    return np.stack([r,g,b], axis=-1)

def apply_interior_mask(img, interior):
    """只保留interior区域, exterior设为黑色"""
    img[~interior] = 0
    return img

# ═══════════════════════════════════════════════════════════
#  渲染器 1: XOR 位运算纹理 — 用逆M逃逸迭代数驱动
# ═══════════════════════════════════════════════════════════
def render_xor(ic, co, w, h, interior):
    """XOR位运算纹理 — 用逆M ic 做XOR位运算, 只着色interior"""
    img = np.zeros((h, w, 3), dtype=np.float64)
    # 只在 interior 上计算
    ic_int = (ic[interior] / MAX_ITER * 127).astype(np.int32)
    hi = (ic_int >> 4) & 0xF
    lo = ic_int & 0xF
    xor_val = (hi ^ lo).astype(np.float64) / 15.0  # [0, 1]
    hue = xor_val * 6; sat = 0.7 + 0.3 * xor_val; val = 0.2 + 0.8 * xor_val
    rgb = hsv_to_rgb(hue, sat, val)
    img[interior] = rgb
    img = apply_interior_mask(img, interior)
    return np.rot90(img, k=2)

# ═══════════════════════════════════════════════════════════
#  渲染器 2: Square Tile 分形 — 用逆M轨道陷阱驱动
# ═══════════════════════════════════════════════════════════
def render_square_tile(ic, co, w, h, interior):
    """Square Tile分形 — 用逆M轨道陷阱做位运算, 只着色interior"""
    img = np.zeros((h, w, 3), dtype=np.float64)
    safe_log = np.abs(np.log(trap[interior] + 1e-30))
    trap_norm = safe_log / safe_log.max()
    trap_int = (trap_norm * 255).astype(np.int32)
    # Square Tile: 高8位与低8位交互
    hi = (trap_int >> 8) & 0xFF
    lo = trap_int & 0xFF
    xor_hl = (hi ^ lo) / 255.0
    hue = xor_hl * 4; sat = 0.8; val = 0.1 + 0.9 * xor_hl
    rgb = hsv_to_rgb(hue, sat, val)
    img[interior] = rgb
    img = apply_interior_mask(img, interior)
    return np.rot90(img, k=2)

# ═══════════════════════════════════════════════════════════
#  渲染器 3: Domain Coloring 域着色
# ═══════════════════════════════════════════════════════════
def render_domain_coloring(z, w, h, interior):
    """Domain Coloring — 域着色复分析, 只着色interior"""
    img = np.zeros((h, w, 3), dtype=np.float64)
    with np.errstate(invalid='ignore'):
        zi = z[interior]
        arg = np.angle(zi)
        hue = (arg + np.pi) / (2*np.pi)
        mag = np.sqrt(zi.real**2 + zi.imag**2 + 1e-30)
        log_mag = np.log(mag) / 8.0
        sat = 0.6 + 0.4*(1 - np.clip(log_mag, 0, 1))
        val = 0.3 + 0.7*np.clip(log_mag, 0, 1)
    rgb = hsv_to_rgb(hue, sat, val)
    img[interior] = rgb
    img = apply_interior_mask(img, interior)
    return np.rot90(img, k=2)

# ═══════════════════════════════════════════════════════════
#  渲染器 4: Sandpile 沙堆自组织临界
# ═══════════════════════════════════════════════════════════
def render_sandpile(ic, w, h, interior):
    """Sandpile 沙堆 — 只用interior的ic值, exterior留黑"""
    img = np.zeros((h, w, 3), dtype=np.float64)
    # 只取interior
    height = np.zeros_like(ic, dtype=np.float32)
    height[interior] = ic[interior].astype(np.float32) / float(MAX_ITER) * 30
    kernel = np.array([[0,0.2,0],[0.2,-1,0.2],[0,0.2,0]], dtype=np.float32)
    for _ in range(15):
        relaxed = convolve2d(height, kernel, mode='same', boundary='symm')
        height = np.maximum(relaxed, 0)
    h_max = height.max()
    if h_max > 0: height /= h_max
    co = height * 4; i0 = np.floor(co).astype(int) % 4
    white=[1,1,1]; red=[1,0,0]; green=[0,1,0]; blue=[0,0,1]
    colors = np.array([white, red, green, blue], dtype=np.float64)
    img[:] = colors[i0]
    img = apply_interior_mask(img, interior)
    return np.rot90(img, k=2)

if __name__ == '__main__':
    t0 = time.time()
    print(f"逆M 创新渲染套件 v7 GPU版 ({RES}x{RES}) ★ 等轴比+只着色interior+水滴朝上")
    print(f"  RE轴=[{RE_MIN:.2f}, {RE_MAX:.2f}] 跨度={RE_MAX-RE_MIN:.2f}")
    print(f"  IM轴=[{IM_MIN:.2f}, {IM_MAX:.2f}] 跨度={IM_MAX-IM_MIN:.2f}")
    print(f"  ✓ axis_equal: 实虚轴物理尺度一致")
    print("计算逆M集...")
    ic, trap, z, dz, interior, co = compute_inverse_m(RES, RES)
    print(f"  内部={interior.sum()} ({100*interior.mean():.1f}%)")
    
    renderers = [
        ('逆M_XOR位运算纹理', render_xor, (ic, co, RES, RES, interior)),
        ('逆M_SquareTile分形', render_square_tile, (ic, co, RES, RES, interior)),
        ('逆M_DomainColoring域着色', render_domain_coloring, (z, RES, RES, interior)),
        ('逆M_Sandpile沙堆', render_sandpile, (ic, RES, RES, interior)),
    ]
    
    for name, renderer, args in renderers:
        print(f"渲染 {name}...")
        img = renderer(*args)
        out = os.path.join(OUT_DIR, f'{name}.png')
        Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8),'RGB').save(out, compress_level=1)
        sz = os.path.getsize(out)/1024/1024
        print(f"  → {out} ({sz:.1f}MB)")
    
    elapsed = time.time() - t0
    print(f"\n✅ 全部完成! 耗时{elapsed:.1f}s")
