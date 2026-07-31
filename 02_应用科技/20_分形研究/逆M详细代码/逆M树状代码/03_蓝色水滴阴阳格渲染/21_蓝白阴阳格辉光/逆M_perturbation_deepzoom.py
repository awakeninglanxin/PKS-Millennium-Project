#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逆M 深度缩放扰动法渲染器 (Perturbation Renderer for Inverse Mandelbrot)

算法: Divetoxx/Mandelbrot (main.cpp + README) 
  扰动公式 δ_{n+1} = 2·Z_n·δ_n + δ_n² - Δc/C₀²  
  复反演  w = 1/c ── 正M seahorse valley 坐标对应到逆M主体内深度缩放

用法:
  python 逆M_perturbation_deepzoom.py [center_re] [center_im] [width] [res] [max_iter]
  
示例 (Image 93 的逆M等效视图):
  python 逆M_perturbation_deepzoom.py -0.5714462691840562 2.147953450824901e-10 4.2452e-14 1080 20000

许可: CC0 (与 Commons 系列图像一致)
"""
import numpy as np, sys, os, time
from PIL import Image
from scipy.ndimage import binary_dilation, gaussian_filter
import mpmath as mp

# ─── 默认参数 (Image 93 → 逆M等效) ──────────────────────────
DEF_CENTER_RE = -0.5714462691840562
DEF_CENTER_IM = 2.147953450824901e-10
DEF_WIDTH     = 4.2452e-14
DEF_RES       = 1080       # 方图宽度像素
DEF_MAX_ITER  = 20000
BAILOUT_SQ    = 40000.0    # (=200², 与大缩放视图匹配)
MARGIN_FACTOR = 0.0        # 视图无 margin (精准取景)
MP_DPS        = 100        # mpmath 精度位数

# ─── 配色参数 (继承 v10 蓝白阴阳格风格) ────────────────────
BG_BLACK     = [0.00,0.00,0.02]
EXT_FAR      = [0.03,0.08,0.22]
EXT_MID      = [0.10,0.18,0.42]
EXT_NEAR     = [0.20,0.33,0.60]
EXT_NEAR2    = [0.30,0.40,0.68]       # 接内部边缘亮区
TILE_BRIGHT  = [0.38,0.52,0.82]
TILE_SHADOW  = [0.01,0.04,0.14]
INT_HOT      = [0.94,0.97,1.0]
INT_CORE     = [0.76,0.87,0.98]
INT_MID      = [0.52,0.70,0.92]
INT_EDGE     = [0.28,0.46,0.78]
GOLD_WHITE   = [1.0,1.0,0.70]
GOLD_HOT     = [1.0,0.88,0.25]
GOLD_WARM    = [0.95,0.55,0.06]
GOLD_EMBER   = [0.75,0.28,0.02]

N_ANGLE      = 120    # 棋盘角度分区数 (深度缩放下减少, 纹理够密)
LOG_R_STEP   = 0.022  # 棋盘径向间距
CHESS_ALPHA  = 0.15   # 棋盘混合透明度
CHESS_BLUR   = 0.6    # 棋盘模糊 Sigma

# ─── 外部电势 LUT ────────────────────────────────────────────
def ext_lut(v):
    """4段蓝色 LUT (同 v10)"""
    r = np.select([v<0.25,v<0.55,v<0.82,True],
        [EXT_FAR[0]+(EXT_MID[0]-EXT_FAR[0])*(v/0.25),
         EXT_MID[0]+(EXT_NEAR[0]-EXT_MID[0])*((v-0.25)/0.30),
         EXT_NEAR[0]+(EXT_NEAR2[0]-EXT_NEAR[0])*((v-0.55)/0.27),
         EXT_NEAR2[0]])
    g = np.select([v<0.25,v<0.55,v<0.82,True],
        [EXT_FAR[1]+(EXT_MID[1]-EXT_FAR[1])*(v/0.25),
         EXT_MID[1]+(EXT_NEAR[1]-EXT_MID[1])*((v-0.25)/0.30),
         EXT_NEAR[1]+(EXT_NEAR2[1]-EXT_NEAR[1])*((v-0.55)/0.27),
         EXT_NEAR2[1]])
    b = np.select([v<0.25,v<0.55,v<0.82,True],
        [EXT_FAR[2]+(EXT_MID[2]-EXT_FAR[2])*(v/0.25),
         EXT_MID[2]+(EXT_NEAR[2]-EXT_MID[2])*((v-0.25)/0.30),
         EXT_NEAR[2]+(EXT_NEAR2[2]-EXT_NEAR[2])*((v-0.55)/0.27),
         EXT_NEAR2[2]])
    return np.stack([r,g,b],axis=-1)

# ─── 内部轨道陷阱 LUT ────────────────────────────────────────
def int_lut(v):
    """5段内部渐变 (同 v10)"""
    r = np.select([v<0.12,v<0.30,v<0.55,v<0.80,True],
        [INT_HOT[0]+(INT_CORE[0]-INT_HOT[0])*(v/0.12),
         INT_CORE[0]+(INT_MID[0]-INT_CORE[0])*((v-0.12)/0.18),
         INT_MID[0]+(INT_EDGE[0]-INT_MID[0])*((v-0.30)/0.25),
         INT_EDGE[0]+(INT_EDGE[0]*0.65-INT_EDGE[0])*((v-0.55)/0.25),
         INT_EDGE[0]*0.65*(1-(v-0.80)/0.20)])
    g = np.select([v<0.12,v<0.30,v<0.55,v<0.80,True],
        [INT_HOT[1]+(INT_CORE[1]-INT_HOT[1])*(v/0.12),
         INT_CORE[1]+(INT_MID[1]-INT_CORE[1])*((v-0.12)/0.18),
         INT_MID[1]+(INT_EDGE[1]-INT_MID[1])*((v-0.30)/0.25),
         INT_EDGE[1]+(INT_EDGE[1]*0.68-INT_EDGE[1])*((v-0.55)/0.25),
         INT_EDGE[1]*0.68*(1-(v-0.80)/0.20)])
    b = np.select([v<0.12,v<0.30,v<0.55,v<0.80,True],
        [INT_HOT[2]+(INT_CORE[2]-INT_HOT[2])*(v/0.12),
         INT_CORE[2]+(INT_MID[2]-INT_CORE[2])*((v-0.12)/0.18),
         INT_MID[2]+(INT_EDGE[2]-INT_MID[2])*((v-0.30)/0.25),
         INT_EDGE[2]+(INT_EDGE[2]*0.75-INT_EDGE[2])*((v-0.55)/0.25),
         INT_EDGE[2]*0.75*(1-(v-0.80)/0.20)])
    return np.stack([r,g,b],axis=-1)

# ═══════════════════════════════════════════════════════════
#  核心: 参考轨道 (mpmath 高精度)
# ═══════════════════════════════════════════════════════════
def compute_reference(cx, cy, max_iter, bailout_sq, dps=MP_DPS):
    """在中心 C₀ 上用 mpmath 高精度计算参考轨道 Z_n
    
    返回:
        Z_list: float64 complex 列表 (共 ref_iters + 1 项)
        escaped: bool 参考是否逃逸
        ref_iters: 实际计算到的迭代次数 (Z 仍有限且 < bailout)
        inv_C0_sq: 1/C₀² 复数 (高精度转 double)
    """
    mp.mp.dps = dps
    C0 = mp.mpc(cx, cy)
    inv_C0 = 1 / C0
    inv_C0_sq = 1 / (C0 * C0)
    
    Z = mp.mpc(0)
    Z_list = [complex(0.0, 0.0)]  # Z₀ = 0
    ref_escaped = False
    
    t0 = time.time()
    report_interval = max(1, max_iter // 10)
    
    for n in range(max_iter):
        Z = Z * Z + inv_C0
        abs_sq = float(Z.real**2 + Z.imag**2)
        
        # 转 double 存
        Z_list.append(complex(float(Z.real), float(Z.imag)))
        
        if abs_sq > bailout_sq:
            ref_escaped = True
            if (n + 1) % report_interval == 0:
                print(f"  参考轨道: iter={n+1} 逃逸 |Z|²={abs_sq:.1e}")
            break
        
        if (n + 1) % report_interval == 0:
            print(f"  参考轨道: iter={n+1} |Z|={np.sqrt(abs_sq):.4f}")
    
    elapsed = time.time() - t0
    print(f"  参考轨道完成: {len(Z_list)-1} iter, {elapsed:.1f}s, 逃逸={ref_escaped}")
    
    return {
        'Z': Z_list,
        'escaped': ref_escaped,
        'iter_count': len(Z_list) - 1,
        'inv_C0_sq': complex(float(inv_C0_sq.real), float(inv_C0_sq.imag))
    }

# ═══════════════════════════════════════════════════════════
#  核心: 扰动法逐像素迭代
# ═══════════════════════════════════════════════════════════
def perturb_iterate(center_re, center_im, inv_width, w, h, ref, max_iter, bailout_sq):
    """用扰动法逆M迭代: δ_{n+1} = 2·Z_n·δ_n + δ_n² - Δc/C₀²
    
    返回:
        ic: int32 escape iteration (h×w)
        trap: float64 min|z|² (h×w)
        interior: bool mask (h×w)
        z_esc: complex128 final z for escaped pixels
    """
    step = inv_width / w
    c_re_min = center_re - inv_width / 2
    c_im_min = center_im - inv_width / 2
    
    # 每像素精确 c 值 (float64 可表示, 因为 Δc / center ~ 4e-14 << eps)
    xs = c_re_min + (np.arange(w, dtype=np.float64) + 0.5) * step
    ys = c_im_min + (np.arange(h, dtype=np.float64) + 0.5) * step
    X, Y = np.meshgrid(xs, ys)
    c_pixel = X + 1j * Y          # 每像素的 c 值
    
    # Δc = c_pixel - C₀  (用于扰动项)
    C0 = complex(center_re, center_im)
    dC = c_pixel - C0
    
    inv_C0_sq = ref['inv_C0_sq']
    ref_Z = ref['Z']               # float64 complex list
    ref_iters = ref['iter_count']
    
    # 状态数组
    ic = np.full((h, w), max_iter, dtype=np.int32)
    trap = np.full((h, w), 1e30, dtype=np.float64)
    z_esc = np.zeros((h, w), dtype=np.complex128)
    alive = np.ones((h, w), dtype=bool)
    delta = np.zeros((h, w), dtype=np.complex128)
    
    total_pixels = h * w
    report_interval = max(1, max_iter // 20)
    t0 = time.time()
    
    max_n = min(max_iter, ref_iters + 1)
    for n in range(max_n):
        if not alive.any():
            break
        
        Zn = ref_Z[n]  # 标量, numpy 自动广播
        
        # 只对 alive 的像素操作
        idx_alive = alive
        d_alive = delta[idx_alive]
        dc_alive = dC[idx_alive]
        
        # ── δ 更新 ──
        d_new = 2.0 * Zn * d_alive + d_alive * d_alive - dc_alive * inv_C0_sq
        delta[idx_alive] = d_new
        
        # ── z = Z_n + δ ──
        z_alive = Zn + d_new
        z_abs_sq = z_alive.real**2 + z_alive.imag**2
        
        # ── 逃逸判定 ──
        esc = z_abs_sq > bailout_sq
        ic[idx_alive] = np.where(esc, n, ic[idx_alive])
        z_esc[idx_alive] = np.where(esc, z_alive, z_esc[idx_alive])
        
        # ── 轨道陷阱 ──
        trap[idx_alive] = np.minimum(trap[idx_alive], z_abs_sq)
        
        # ── 重定基准 (Rebasing): |z| < |δ| → δ = z ──
        d_abs_sq = d_new.real**2 + d_new.imag**2
        rebase = (z_abs_sq < d_abs_sq)
        if rebase.any():
            delta_alive = delta[idx_alive]
            delta_alive[rebase] = z_alive[rebase]
            delta[idx_alive] = delta_alive
        
        # ── 更新 alive ──
        alive[idx_alive] = ~esc
        
        # ── 进度报告 ──
        if (n + 1) % report_interval == 0:
            alive_pct = 100 * alive.sum() / total_pixels
            elapsed = time.time() - t0
            rate = (n + 1) / elapsed if elapsed > 0 else 0
            eta = (max_n - n - 1) / rate if rate > 0 else 0
            print(f"  iter {n+1}/{max_n}: alive={alive.sum()}({alive_pct:.2f}%)  {elapsed:.0f}s  ETA={eta:.0f}s")
    
    elapsed = time.time() - t0
    interior = (ic == max_iter)
    print(f"  扰动迭代完成: {elapsed:.1f}s  interior={interior.sum()}({100*interior.mean():.1f}%)")
    
    return ic, trap, interior, z_esc, dC

# ═══════════════════════════════════════════════════════════
#  着色渲染 (继承 v10 蓝白阴阳格风格)
# ═══════════════════════════════════════════════════════════
def render_result(ic, trap, interior, z_esc, dC, w, h, inv_width, center_re, center_im):
    """基于 perturbation 迭代结果, 生成 v10 风格着色"""
    img = np.full((h, w, 3), BG_BLACK, dtype=np.float64)
    ext = ~interior
    
    # ── 外部着色: 平滑电势 + 4段蓝色 LUT ──
    if ext.any():
        with np.errstate(invalid='ignore', divide='ignore'):
            ms = z_esc[ext].real**2 + z_esc[ext].imag**2 + 1e-30
            nc_f = np.minimum(ic[ext].astype(np.float64), 32.0)
            pot_raw = np.log(ms) / np.power(2.0, nc_f)
            p99 = np.percentile(pot_raw, 99) if pot_raw.size > 0 else 1.0
            t = np.clip(pot_raw / max(float(p99), 0.5), 0, 1)
            ts = np.power(t, 0.52)
            img[ext] = ext_lut(ts)
    
    # ── 内部着色: 轨道陷阱渐变 ──
    if interior.any():
        with np.errstate(invalid='ignore'):
            trap_s = np.maximum(trap[interior], 1e-30)
            v_raw = (np.log(trap_s) * 0.43) % 1.0
            v_adj = np.power(v_raw, 0.48)
            img[interior] = int_lut(v_adj)
    
    # ── 棋盘格: c 空间极坐标 XOR (仅外部) ──
    c_r = np.sqrt(dC.real**2 + dC.imag**2 + 1e-30)  # 从中心点的径向距离
    # 注意: 深度缩放下 dC 接近 0 但可分辨; log|c| 趋向 -∞
    # 改用绝对坐标 c = C₀ + dC
    c_abs = np.sqrt((dC.real + complex(center_re,0).real)**2 + 
                    (dC.imag + complex(0,center_im).imag)**2)
    c_theta = (np.arctan2(dC.imag + center_im, dC.real + center_re) + np.pi) / (2*np.pi)
    c_log_r = np.log(c_abs + 0.01)
    
    qi = np.floor(c_theta * N_ANGLE).astype(int)
    qj = np.floor(c_log_r / LOG_R_STEP).astype(int)
    chess_raw = ((qi % 2 == 0) != (qj % 2 == 0)).astype(np.float64)
    
    if CHESS_BLUR > 0:
        cs = gaussian_filter(chess_raw, sigma=CHESS_BLUR)
    else:
        cs = chess_raw
    
    ca = cs * CHESS_ALPHA
    ca[interior] = 0  # 内部不放棋盘格
    
    tex = np.zeros((h, w, 3), dtype=np.float64)
    ml = chess_raw > 0.5
    for ch in range(3):
        tex[:, :, ch] = np.where(ml, TILE_BRIGHT[ch], TILE_SHADOW[ch])
    for ch in range(3):
        img[:, :, ch] = np.clip(img[:, :, ch] * (1 - ca) + tex[:, :, ch] * ca, 0, 1)
    
    # ── 金边: 内部/外部边界膨胀 (替代 DEM, 精度足够) ──
    bd_h = interior[:, :-1] != interior[:, 1:]
    bd_v = interior[:-1, :] != interior[1:, :]
    edge = np.zeros((h, w), dtype=bool)
    edge[:, :-1] |= bd_h
    edge[:-1, :] |= bd_v
    
    g_ember = binary_dilation(edge, np.ones((14, 14)))
    g_warm  = binary_dilation(edge, np.ones((8, 8)))
    g_gold  = binary_dilation(edge, np.ones((5, 5)))
    g_hot   = binary_dilation(edge, np.ones((3, 3)))
    g_core  = binary_dilation(edge, np.ones((2, 2)))
    
    # (深度缩放下可用简单的距离估计替代 DEM)
    # 每层辉光厚度按概率稀释
    if ext.any():
        dv = np.zeros((h, w), dtype=np.float64)
        dv[ext] = 1.0  # 替代 DEM: 等厚辉光
        
        ge = g_ember & ext & ~g_warm
        if ge.any():
            img[ge, 0] = np.clip(img[ge, 0] + 0.08, 0, 1)
            img[ge, 1] = np.clip(img[ge, 1] + 0.04, 0, 1)
        
        gw = g_warm & ext & ~g_gold
        if gw.any():
            img[gw] = np.stack([
                np.clip(GOLD_EMBER[0] * 0.35 + GOLD_WARM[0] * 0.50, 0, 1),
                np.clip(GOLD_EMBER[1] * 0.25 + GOLD_WARM[1] * 0.55, 0, 1),
                np.clip(GOLD_EMBER[2] * 0.08 + GOLD_WARM[2] * 0.70, 0, 0.32)
            ], axis=-1)
        
        gg = g_gold & ext & ~g_hot
        if gg.any():
            img[gg] = np.stack([
                np.clip(GOLD_WARM[0] * 0.40 + GOLD_HOT[0] * 0.50, 0, 1),
                np.clip(GOLD_WARM[1] * 0.32 + GOLD_HOT[1] * 0.55, 0, 1),
                np.clip(GOLD_WARM[2] * 0.12 + GOLD_HOT[2] * 0.70, 0, 0.40)
            ], axis=-1)
        
        gh = g_hot & ext & ~g_core
        if gh.any():
            img[gh] = np.stack([
                np.clip(GOLD_HOT[0] * 0.55 + GOLD_WHITE[0] * 0.38, 0, 1),
                np.clip(GOLD_HOT[1] * 0.48 + GOLD_WHITE[1] * 0.42, 0, 1),
                np.clip(GOLD_HOT[2] * 0.18 + GOLD_WHITE[2] * 0.65, 0, 0.50)
            ], axis=-1)
        
        gc = g_core & interior
        if gc.any():
            img[gc] = np.stack([
                np.clip(GOLD_WHITE[0] * 0.55 + 0.40, 0, 1),
                np.clip(GOLD_WHITE[1] * 0.50 + 0.42, 0, 1),
                np.clip(GOLD_WHITE[2] * 0.30 + 0.55, 0, 0.58)
            ], axis=-1)
    
    return img


# ═══════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    # 解析命令行参数
    cx = float(sys.argv[1]) if len(sys.argv) > 1 else DEF_CENTER_RE
    cy = float(sys.argv[2]) if len(sys.argv) > 2 else DEF_CENTER_IM
    inv_w = float(sys.argv[3]) if len(sys.argv) > 3 else DEF_WIDTH
    res = int(sys.argv[4]) if len(sys.argv) > 4 else DEF_RES
    max_iter = int(sys.argv[5]) if len(sys.argv) > 5 else DEF_MAX_ITER
    
    out_dir = sys.argv[6] if len(sys.argv) > 6 else os.path.dirname(os.path.abspath(__file__))
    
    w = h = res  # 方块视图
    
    print("=" * 55)
    print("逆M 深度缩放扰动法渲染器")
    print("=" * 55)
    print(f"  中心: ({cx:.16f}, {cy:.6e})")
    print(f"  宽度: {inv_w:.4e}")
    print(f"  分辨率: {w}×{h}")
    print(f"  最大迭代: {max_iter}")
    print(f"  bailout: {BAILOUT_SQ:.0f} ({np.sqrt(BAILOUT_SQ):.0f}²)")
    
    # Step 1: 参考轨道
    print("\n[Step 1] 计算 mpmath 参考轨道...")
    ref = compute_reference(cx, cy, max_iter, BAILOUT_SQ)
    
    # Step 2: 扰动法迭代
    print("\n[Step 2] 扰动法逐像素迭代...")
    ic, trap, interior, z_esc, dC = perturb_iterate(
        cx, cy, inv_w, w, h, ref, max_iter, BAILOUT_SQ
    )
    
    # Step 3: 着色渲染
    print("\n[Step 3] 着色渲染...")
    img = render_result(ic, trap, interior, z_esc, dC, w, h, inv_w, cx, cy)
    
    # Step 4: 保存
    out_name = f'逆M_perturbation_{res}px.png'
    out_path = os.path.join(out_dir, out_name)
    img_uint8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img_uint8, mode='RGB').save(out_path, compress_level=2)
    
    sz = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n✅ 完成! {out_path}")
    print(f"   尺寸: {img.shape[1]}×{img.shape[0]}px ({sz:.1f}MB)")
    print(f"   内部像素: {interior.sum()} ({100*interior.mean():.1f}%)")
