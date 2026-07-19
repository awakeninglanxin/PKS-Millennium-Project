#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M 算法创新渲染套件 v1.0

灵感来源: Wikimedia Commons 5种渲染算法
- XOR Texture          → 位运算纹理
- Square Tile Fractal  → 位运算分形
- Domain Coloring      → 域着色复分析
- Backtang2            → 沙堆自组织临界
- Poincare H7          → 双曲镶嵌

每种渲染到"逆M水滴"上,生成5种新风格。
"""
import numpy as np, os, sys
from scipy.ndimage import binary_dilation, gaussian_filter
from PIL import Image

# ═══════════════════════════════════════════════════════════
#  逆M集计算引擎 (共享)
# ═══════════════════════════════════════════════════════════
TIP=4.0; BOTTOM=-4.0/3.0; HSPAN=1.6242719100; MARGIN=0.50
RE_MIN, RE_MAX = BOTTOM-MARGIN, TIP+MARGIN
IM_MIN, IM_MAX = -HSPAN-MARGIN, HSPAN+MARGIN
MAX_ITER = 200; BAILOUT_SQ = 256**2

def compute_inverse_m(w, h):
    """计算逆M集: z_{n+1} = z_n^2 + 1/c"""
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

# ═══════════════════════════════════════════════════════════
#  1. XOR 位运算纹理
# ═══════════════════════════════════════════════════════════
def xor_texture_render(ic, interior, co, w, h):
    """参考: Wikimedia XOR_texture.png
    原始: f(i,j) = i ^ j (像素索引XOR)
    改编: 用实部/虚部整数索引做XOR
    """
    img = np.zeros((h, w, 3), dtype=np.float64)
    ii = np.floor((co.real - RE_MIN) / (RE_MAX - RE_MIN) * w).astype(int)
    jj = np.floor((co.imag - IM_MIN) / (IM_MAX - IM_MIN) * h).astype(int)
    ii = np.clip(ii, 0, w-1); jj = np.clip(jj, 0, h-1)
    xv = ii ^ jj  # XOR
    # 多字节XOR增加细节
    xv2 = (ii >> 4) ^ (jj >> 4)
    xv_total = xv + xv2 * 16
    norm = xv_total / 256.0
    # HSV映射
    hue = norm % 1.0
    sat = 0.7 + 0.3 * np.sin(hue * np.pi * 4)
    val = 0.3 + 0.7 * (0.5 + 0.5 * np.cos(hue * np.pi * 2))
    # RGB转换
    r = np.where(hue < 1/6, 1, np.where(hue < 1/2, 1-hue*2+1, 0))
    g = np.where(hue < 1/2, 1-(hue-1/6)*2, np.where(hue < 2/3, 0, 1-(2-hue)*2))
    b = np.where(hue < 2/3, np.where(hue >= 1/2, 1-(hue-1/2)*2, 1), 0)
    img[:,:,0] = r * val * sat * 0.9 + 0.05
    img[:,:,1] = g * val * sat * 0.9 + 0.05
    img[:,:,2] = b * val * sat * 0.9 + 0.05
    img[interior] = img[interior] * 1.8  # 内部更亮
    return np.clip(img, 0, 1)

# ═══════════════════════════════════════════════════════════
#  2. Square Tile 位运算分形
# ═══════════════════════════════════════════════════════════
def square_tile_render(ic, interior, co, w, h):
    """参考: Wikimedia Square_tile_fractal.png
    公式: g = (i & (j - 2*(i^j) + j) & i) % 255
    改编: 用复平面整数索引
    """
    img = np.zeros((h, w, 3), dtype=np.float64)
    ii = np.arange(w, dtype=np.int64)[np.newaxis, :]
    jj = np.arange(h, dtype=np.int64)[:, np.newaxis]
    expr = ii & (jj - 2*(ii ^ jj) + jj) & ii
    norm = (expr % 256).astype(np.float64) / 255.0
    # 彩虹调色
    hue = norm * 5  # 多周期
    hue = hue % 1.0
    sat = 0.8
    val = 0.4 + 0.6 * norm
    r = 0.5 + 0.5 * np.cos(2*np.pi*hue)
    g = 0.5 + 0.5 * np.cos(2*np.pi*(hue - 1/3))
    b = 0.5 + 0.5 * np.cos(2*np.pi*(hue + 1/3))
    img[:,:,0] = r * sat * val + 0.05
    img[:,:,1] = g * sat * val + 0.05
    img[:,:,2] = b * sat * val + 0.05
    img[interior] = img[interior] * 2.0
    return np.clip(img, 0, 1)

# ═══════════════════════════════════════════════════════════
#  3. Domain Coloring 域着色
# ═══════════════════════════════════════════════════════════
def domain_coloring_render(z, interior, w, h):
    """参考: Wikimedia Color_complex_plot.jpg
    域着色: hue=arg(f(c))/2pi, sat/val=log|f(c)|
    改编: 对逆M的最终z值做域着色
    """
    img = np.zeros((h, w, 3), dtype=np.float64)
    with np.errstate(invalid='ignore'):
        arg = np.angle(z)
        arg = (arg + np.pi) / (2*np.pi)  # [0,1]
        mag = np.sqrt(z.real**2 + z.imag**2 + 1e-30)
        log_mag = np.log(mag) / 10.0
        log_mag = np.clip(log_mag, 0, 1)
    # HSV→RGB
    hue = arg.copy()
    sat = 0.7 + 0.3 * (1 - log_mag)
    val = 0.3 + 0.7 * log_mag
    # 简化RGB转换
    hh = hue * 6
    c = val * sat
    x = c * (1 - np.abs(hh % 2 - 1))
    m = val - c
    r = np.where(hh < 1, c, np.where(hh < 2, x, m))
    g = np.where(hh < 3, c, np.where(hh < 4, x, m))
    b = np.where(hh < 5, c, np.where(hh < 6, x, m))
    img[:,:,0] = r; img[:,:,1] = g; img[:,:,2] = b
    img[interior] = img[interior] * 0.6  # 内部稍暗
    return np.clip(img, 0, 1)

# ═══════════════════════════════════════════════════════════
#  4. Backtang2 沙堆自组织临界
# ═══════════════════════════════════════════════════════════
def sandpile_render(ic, interior, w, h):
    """参考: Wikimedia Backtang2.png
    Bak-Tang-Wiesenfeld 沙堆模型: 临界值=4, 超量扩散
    改编: 用逃逸迭代次数作沙堆高度
    """
    height = np.zeros((h, w), dtype=np.float32)
    if interior.any():
        depth = ic[interior] / float(MAX_ITER)
        height[interior] = depth * 50
    else:
        height[:] = 0.5
    # 沙堆扩散模拟 (3次松弛迭代)
    kernel = np.array([[0, 0.25, 0], [0.25, -1, 0.25], [0, 0.25, 0]])
    for _ in range(10):
        from scipy.signal import convolve2d
        relaxed = convolve2d(height, kernel, mode='same', boundary='fill', fillvalue=0)
        relaxed = np.maximum(relaxed, 0)
        height = relaxed
    # 归一化
    h_max = height.max()
    if h_max > 0:
        height /= h_max
    # 四色系统 (白红绿蓝)
    img = np.zeros((h, w, 3), dtype=np.float64)
    co = height * 4
    i0 = np.floor(co).astype(int) % 4
    frac = co - np.floor(co)
    # 0=白, 1=红, 2=绿, 3=蓝, 4=黄(0+1混合)
    white = [1,1,1]; red = [1,0,0]; green = [0,1,0]; blue = [0,0,1]
    for ch in range(3):
        img[:,:,ch] = np.where(i0==0, white[ch],
                  np.where(i0==1, red[ch],
                  np.where(i0==2, green[ch],
                  blue[ch])))
        img[:,:,ch] = img[:,:,ch] * (1 - frac) + img[:,:,ch] * 0.5 * frac
    img = np.clip(img, 0, 1)
    return img

# ═══════════════════════════════════════════════════════════
#  统一输出
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    RES = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else '.'
    w = h = RES
    print(f"逆M算法创新渲染套件 (SSAA=1, {RES}x{RES})")
    
    print("[1/5] 计算逆M集...")
    ic, trap, z, dz, interior, co = compute_inverse_m(w, h)
    print(f"    内部={interior.sum()} ({100*interior.mean():.1f}%)")
    
    print("[2/5] XOR纹理...")
    img_xor = xor_texture_render(ic, interior, co, w, h)
    out = os.path.join(OUT_DIR, '逆M_XOR位运算纹理.png')
    Image.fromarray((np.clip(img_xor,0,1)*255).astype(np.uint8),'RGB').save(out, compress_level=1)
    print(f"    → {out}")
    
    print("[3/5] Square Tile...")
    img_sq = square_tile_render(ic, interior, co, w, h)
    out = os.path.join(OUT_DIR, '逆M_SquareTile分形.png')
    Image.fromarray((np.clip(img_sq,0,1)*255).astype(np.uint8),'RGB').save(out, compress_level=1)
    print(f"    → {out}")
    
    print("[4/5] Domain Coloring...")
    img_dc = domain_coloring_render(z, interior, w, h)
    out = os.path.join(OUT_DIR, '逆M_DomainColoring域着色.png')
    Image.fromarray((np.clip(img_dc,0,1)*255).astype(np.uint8),'RGB').save(out, compress_level=1)
    print(f"    → {out}")
    
    print("[5/5] Sandpile...")
    img_sp = sandpile_render(ic, interior, w, h)
    out = os.path.join(OUT_DIR, '逆M_Sandpile沙堆.png')
    Image.fromarray((np.clip(img_sp,0,1)*255).astype(np.uint8),'RGB').save(out, compress_level=1)
    print(f"    → {out}")
    
    print(f"\n✅ 完成! 全部 {RES}x{RES} 方块视图")
