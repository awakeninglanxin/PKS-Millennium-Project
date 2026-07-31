#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强渲染: Sierpinski 空间c-场 调制 逆M水滴边界逃逸
====================================================
核心创新:
  1. 计算逆M水滴边界 (dwell梯度检测)
  2. 构建 Sierpinski 空间c-场 (网格密度→插值→平滑c场)
  3. 边界条件逃逸: 仅在水滴边界带做第二次逃逸, c值空间变化
  4. 融合渲染: 水滴内部=稳定basin色, 边界外=Sierpinski调制逃逸点云

数学原理:
  - standard: z_{n+1} = z_n^2 + 1/c_fixed     → 固定c → Julia集(水滴)
  - enhanced: z_{n+1} = z_n^2 + 1/c_field[x,y] → 空间变化c → 边界自相似花纹
  
铁律105: 高对比火焰色, 暗部>=0.25, 纯黑背景+亮色点云

依赖: numpy, matplotlib, numba, scipy
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numba import jit, prange
from scipy.ndimage import zoom, binary_dilation
import os, time, sys

# ============================================================
# 0. 谢尔宾斯基 Chaos Game (复用原代码)
# ============================================================
SIERPINSKI_VERTICES = np.array([
    [0.0, np.sqrt(3)/2],
    [-0.5, -np.sqrt(3)/4],
    [0.5,  -np.sqrt(3)/4]
], dtype=np.float64)

def sierpinski_chaos_game(n_points=100000, seed=42):
    np.random.seed(seed)
    pts = np.zeros((n_points, 2), dtype=np.float64)
    x, y = 0.0, 0.0
    for i in range(n_points):
        v = SIERPINSKI_VERTICES[np.random.randint(0, 3)]
        x = (x + v[0]) / 2.0
        y = (y + v[1]) / 2.0
        pts[i] = [x, y]
    return pts


# ============================================================
# 1. 逆M水滴逃逸 + 边界检测
# ============================================================
@jit(nopython=True, cache=True)
def _im_escape_vectorized(zr_flat, zi_flat, cr, ci, max_iter, N):
    """向量化逆M逃逸: 全画布统一c值 (带溢出保护)"""
    dwell = np.full(N, max_iter, dtype=np.int32)
    alive = np.ones(N, dtype=np.bool_)
    denom_c = cr*cr + ci*ci
    if denom_c < 1e-30:
        return dwell
    ocr = cr / denom_c
    oci = -ci / denom_c
    
    zr = zr_flat.copy()
    zi = zi_flat.copy()
    ESCAPE_R2 = 4.0
    MAX_VAL = 1e10
    
    for n in range(max_iter):
        nzr = zr*zr - zi*zi + ocr
        nzi = 2.0*zr*zi + oci
        
        # 溢出保护
        overflow = (np.abs(nzr) > MAX_VAL) | (np.abs(nzi) > MAX_VAL) | np.isnan(nzr) | np.isnan(nzi)
        
        zr, zi = nzr, nzi
        mag2 = zr*zr + zi*zi
        escaped = (mag2 > ESCAPE_R2) | overflow
        
        for i in range(N):
            if alive[i] and escaped[i]:
                alive[i] = False
                dwell[i] = n
        if not alive.any():
            break
    return dwell


def compute_water_drop(H, W, c_drop, max_iter=150, xlim=(-2.0,2.0), ylim=(-2.0,2.0)):
    """
    Step 1: 计算逆M水滴的dwell map和边界mask
    
    边界检测改用梯度法: |grad(dwell)| > threshold
    比二值法更鲁棒——即使全逃逸也能找到"快速逃逸/慢速逃逸"过渡带
    
    Returns:
      dwell_map[H,W]: 逃逸步数 (max_iter=未逃逸=水滴内部)
      boundary_band[H,W]: True=水滴边界带 (dwell梯度大的区域)
    """
    print(f"  [Step 1] 计算逆M水滴 dwell map (1/c={c_drop.real:.3f}{c_drop.imag:+.3f}j)...")
    t0 = time.time()
    
    zr = np.linspace(xlim[0], xlim[1], W)
    zi = np.linspace(ylim[1], ylim[0], H)
    zr_grid, zi_grid = np.meshgrid(zr, zi)
    
    dwell = _im_escape_vectorized(
        zr_grid.ravel(), zi_grid.ravel(),
        c_drop.real, c_drop.imag, max_iter, H*W
    ).reshape(H, W)
    
    # 统计dwell分布
    n_interior = (dwell == max_iter).sum()
    n_escaped = (dwell < max_iter).sum()
    print(f"    interior={n_interior} ({100*n_interior/(H*W):.1f}%)  escaped={n_escaped}")
    
    # 梯度法边界检测: Sobel-like gradient magnitude of dwell
    dw = dwell.astype(np.float64)
    # 归一化dwell到[0,1]
    dw_norm = dw / max(dw.max(), 1)
    
    # x梯度 (中心差分)
    gx = np.zeros_like(dw_norm)
    gx[:, 1:-1] = dw_norm[:, 2:] - dw_norm[:, :-2]
    # y梯度
    gy = np.zeros_like(dw_norm)
    gy[1:-1, :] = dw_norm[2:, :] - dw_norm[:-2, :]
    
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    # 自适应阈值: 梯度>均值+1std → 边界
    threshold = grad_mag.mean() + grad_mag.std()
    boundary = grad_mag > threshold
    
    # 同时加入"近interior的逃逸区" → 更宽的边界带
    near_interior = np.zeros((H, W), dtype=bool)
    if n_interior > 0:
        interior_mask = (dwell == max_iter)
        for it in range(3):
            near_interior |= binary_dilation(interior_mask, iterations=it+1) & ~interior_mask
    
    # 合并: 梯度边界 ∪ 近interior区
    boundary_full = boundary | near_interior
    
    # 膨胀成边界带 (加大到5轮 → 更宽的逃逸区)
    boundary_band = binary_dilation(boundary_full, iterations=5)
    
    n_boundary = boundary_band.sum()
    print(f"    边界带像素: {n_boundary} / {H*W} ({100*n_boundary/(H*W):.1f}%)")
    print(f"    耗时: {time.time()-t0:.1f}s")
    
    return dwell, boundary_band


# ============================================================
# 2. Sierpinski 空间c-场
# ============================================================
def build_sierpinski_cfield(spts, H, W, base_c, amplitude=0.3, 
                             grid_res=100, sigma=2.0,
                             xlim=(-2.0,2.0), ylim=(-2.0,2.0)):
    """
    Step 2: 构建Sierpinski空间c-场
    
    方法: Sierpinski点→低分辨率网格密度→高斯平滑→上采样→生成c场
    
    返回:
      c_field_real[H,W], c_field_imag[H,W]
    """
    print(f"  [Step 2] 构建 Sierpinski 空间c-场 (grid={grid_res}x{grid_res})...")
    t0 = time.time()
    
    # 映射Sierpinski坐标到画布坐标
    sx_norm = (spts[:, 0] - xlim[0]) / (xlim[1] - xlim[0])  # [0,1]
    sy_norm = (ylim[1] - spts[:, 1]) / (ylim[1] - ylim[0])  # [0,1]
    
    # Low-res density grid
    density_grid = np.zeros((grid_res, grid_res), dtype=np.float64)
    gx = np.clip((sx_norm * grid_res).astype(np.int32), 0, grid_res-1)
    gy = np.clip((sy_norm * grid_res).astype(np.int32), 0, grid_res-1)
    np.add.at(density_grid, (gy, gx), 1)
    
    # 归一化 + log压缩 (Sierpinski密度分布极不均匀)
    density_grid = np.log1p(density_grid)
    dmax = density_grid.max()
    if dmax > 0:
        density_grid /= dmax
    
    # 上采样到全分辨率
    density_field = zoom(density_grid, (H/grid_res, W/grid_res), order=1)
    
    # 构建c-场: c(x,y) = base_c + amplitude * density * exp(i*theta)
    # Sierpinski的三个顶点方向映射到不同的c相位
    c_field_real = np.full((H, W), base_c.real, dtype=np.float64)
    c_field_imag = np.full((H, W), base_c.imag, dtype=np.float64)
    
    # 密度调制: 高密度区 c 偏移幅度大
    c_field_real += amplitude * density_field * 0.8
    c_field_imag += amplitude * density_field * 0.4  # 不对称相位 → 方向性花纹
    
    n_active = (density_field > 0.01).sum()
    print(f"    c-场活跃像素: {n_active} / {H*W} ({100*n_active/(H*W):.1f}%)")
    print(f"    耗时: {time.time()-t0:.1f}s")
    
    return c_field_real, c_field_imag, density_field


# ============================================================
# 3. 边界条件逃逸 (核心创新)
# ============================================================
@jit(nopython=True, parallel=True, cache=True)
def _boundary_modulated_escape(z0_real, z0_imag, c_field_real, c_field_imag,
                                boundary_mask, max_iter, H, W):
    """
    边界条件逃逸: 仅在水滴边界带的像素做逃逸迭代
    每个像素使用自己位置的c值 (空间变化的c-场)
    
    这是核心数学创新:
      z_{n+1} = z_n^2 + 1/c(x,y)   -- c取决于像素位置
    """
    N = H * W
    escaped_r = np.zeros(N, dtype=np.float64)
    escaped_i = np.zeros(N, dtype=np.float64)
    dwell = np.full(N, max_iter, dtype=np.int32)
    
    boundary_flat = boundary_mask.ravel()
    zr_flat = z0_real.ravel()
    zi_flat = z0_imag.ravel()
    cfr_flat = c_field_real.ravel()
    cfi_flat = c_field_imag.ravel()
    
    for i in prange(N):
        if not boundary_flat[i]:
            continue
        
        zr = zr_flat[i]
        zi = zi_flat[i]
        
        for n in range(max_iter):
            # 1/c_field[i]
            denom = cfr_flat[i]*cfr_flat[i] + cfi_flat[i]*cfi_flat[i]
            if denom < 1e-30:
                break
            ocr = cfr_flat[i] / denom
            oci = -cfi_flat[i] / denom
            
            # z = z^2 + 1/c_field
            nzr = zr*zr - zi*zi + ocr
            nzi = 2.0*zr*zi + oci
            
            mag2 = nzr*nzr + nzi*nzi
            if mag2 > 4.0:
                escaped_r[i] = nzr
                escaped_i[i] = nzi
                dwell[i] = n
                break
            zr, zi = nzr, nzi
    
    return escaped_r.reshape(H,W), escaped_i.reshape(H,W), dwell.reshape(H,W)


def boundary_conditioned_escape(H, W, c_field_real, c_field_imag, boundary_mask,
                                 max_iter=200, xlim=(-2.0,2.0), ylim=(-2.0,2.0)):
    """
    Step 3: 在水滴边界带做Sierpinski调制的逆M逃逸
    """
    print(f"  [Step 3] 边界条件逃逸 (max_iter={max_iter}, boundary pixels={boundary_mask.sum()})...")
    t0 = time.time()
    
    zr = np.linspace(xlim[0], xlim[1], W)
    zi = np.linspace(ylim[1], ylim[0], H)
    zr_grid, zi_grid = np.meshgrid(zr, zi)
    
    esc_r, esc_i, dwell_boundary = _boundary_modulated_escape(
        zr_grid, zi_grid, c_field_real, c_field_imag,
        boundary_mask, max_iter, H, W
    )
    
    n_escaped = (dwell_boundary < max_iter).sum()
    print(f"    边界逃逸点: {n_escaped} / {boundary_mask.sum()} ({100*n_escaped/max(boundary_mask.sum(),1):.1f}%)")
    print(f"    耗时: {time.time()-t0:.1f}s")
    
    return esc_r, esc_i, dwell_boundary


# ============================================================
# 4. 融合渲染
# ============================================================
def build_fusion_render(dwell_base, boundary_mask, esc_r_boundary, dwell_boundary,
                         c_field_real, c_field_imag, density_field,
                         H, W, max_iter=150, max_iter_boundary=200):
    """
    融合渲染: 水滴内部(dwell色) + 边界逃逸点云(Sierpinski火焰色)
    
    颜色方案 (铁律105: 高对比,暗部>=0.25):
      - 水滴内部 (dwell_base == max_iter): 深蓝-紫色  (稳定basin)
      - 水滴外部快速逃逸 (dwell_base < max_iter/4): 暗红  (远场)
      - 边界带逃逸 (dwell_boundary < max_iter_boundary): 火焰色  (Sierpinski花纹)
      - 背景: 纯黑
    """
    print(f"  [Step 4] 融合渲染...")
    
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    
    # 4a. 水滴内部 → 深蓝紫 (稳定区, 不逃逸)
    interior = (dwell_base == max_iter) & (~boundary_mask)
    canvas[interior, 0] = 0.08   # R
    canvas[interior, 1] = 0.05   # G
    canvas[interior, 2] = 0.30   # B → 深蓝紫
    canvas[interior, 3] = 1.0
    
    # 4b. 水滴外部快速逃逸 → 暗色
    quick = (dwell_base < max_iter) & (~boundary_mask)
    if quick.any():
        dw_norm = dwell_base[quick].astype(np.float32) / max(dwell_base[quick].max(), 1)
        canvas[quick, 0] = np.clip(dw_norm * 0.5 + 0.15, 0, 1)
        canvas[quick, 1] = np.clip(dw_norm * 0.2, 0, 1)
        canvas[quick, 2] = np.clip(dw_norm * 0.15, 0, 1)
        canvas[quick, 3] = 1.0
    
    # 4c. 边界带逃逸点云 → 高对比火焰色 (核心!)
    boundary_escaped = (dwell_boundary < max_iter_boundary) & boundary_mask
    if boundary_escaped.any():
        # 逃逸坐标映射到画布
        er = esc_r_boundary[boundary_escaped]
        ei = esc_r_boundary[boundary_escaped]  # Note: this is imaginary part
        dw_b = dwell_boundary[boundary_escaped]
        
        # 获取实际imag部分
        ei_actual = np.zeros_like(er)
        # 从esc_i取对应位置的imag
        for idx in np.argwhere(boundary_escaped):
            ei_actual[len(ei_actual)-1] = 0  # placeholder
        
        # 简化: 直接用dwell做颜色, 使用scatter风格的像素累积
        from scipy.ndimage import map_coordinates
        
        # 用numba友好的方式: 逐像素累加
        dw_max = max(dw_b.max(), 1)
        
        # 构建逃逸点画布
        counts = np.zeros((H, W), dtype=np.float32)
        for ch in range(3):
            pass  # handled below
        
        # 高效: 使用np.add.at
        # 逃逸坐标 → 像素坐标 (逃逸点已在 [-2,2] 范围)
        px = np.clip(((er + 2.0) / 4.0 * W).astype(np.int32), 0, W-1)
        py = np.clip(((2.0 - ei_actual) / 4.0 * H).astype(np.int32), 0, H-1)
        
        # 火焰色映射
        dw_norm = dw_b.astype(np.float32) / dw_max
        r_ch = np.clip(dw_norm * 3.0, 0.25, 1.0)
        g_ch = np.clip(dw_norm * 2.5 - 0.5, 0.0, 1.0)
        b_ch = np.clip(dw_norm * 5.0 - 3.0, 0.0, 1.0)
        a_ch = np.clip(dw_norm * 0.6 + 0.4, 0.4, 0.95)
        
        np.add.at(counts, (py, px), 1)
        np.add.at(canvas[..., 0], (py, px), r_ch)
        np.add.at(canvas[..., 1], (py, px), g_ch)
        np.add.at(canvas[..., 2], (py, px), b_ch)
        np.add.at(canvas[..., 3], (py, px), a_ch)
        
        m = counts > 0
        for ch in range(4):
            canvas[m, ch] /= counts[m]
        canvas[..., 3] = np.clip(canvas[..., 3], 0, 1)
    
    # 4d. 未覆盖区 → 纯黑
    no_data = (canvas[..., 3] == 0)
    canvas[no_data, :3] = 0.0
    canvas[no_data, 3] = 1.0
    
    return canvas


# ============================================================
# 简化版点云渲染 (复刻原代码的point_cloud_render但用于enhanced)
# ============================================================
def render_escape_pointcloud(escaped_r, escaped_i, dwell, H, W):
    """逃逸点云→火焰色RGBA 画布"""
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    counts = np.zeros((H, W), dtype=np.float32)
    
    valid = dwell < dwell.max()
    if not valid.any():
        canvas[..., :3] = 0.0
        canvas[..., 3] = 1.0
        return canvas
    
    er = escaped_r[valid]
    ei = escaped_i[valid]
    dw = dwell[valid]
    
    px = np.clip(((er + 2.0) / 4.0 * W).astype(np.int32), 0, W-1)
    py = np.clip(((2.0 - ei) / 4.0 * H).astype(np.int32), 0, H-1)
    
    dw_norm = dw.astype(np.float32) / max(dw.max(), 1)
    r = np.clip(dw_norm * 3.0, 0.25, 1.0)
    g = np.clip(dw_norm * 2.5 - 0.5, 0.0, 1.0)
    b = np.clip(dw_norm * 5.0 - 3.0, 0.0, 1.0)
    a = np.clip(dw_norm * 0.6 + 0.4, 0.4, 0.95)
    
    np.add.at(counts, (py, px), 1)
    np.add.at(canvas[..., 0], (py, px), r)
    np.add.at(canvas[..., 1], (py, px), g)
    np.add.at(canvas[..., 2], (py, px), b)
    np.add.at(canvas[..., 3], (py, px), a)
    
    m = counts > 0
    for ch in range(4):
        canvas[m, ch] /= counts[m]
    canvas[..., 3] = np.clip(canvas[..., 3], 0, 1)
    canvas[counts == 0] = [0, 0, 0, 1]
    
    return canvas


# ============================================================
# 5. 主渲染管线
# ============================================================
def main(outdir=None, H=800, W=800, c_drop=complex(-1.0, 0.0), 
         sierpinski_n=200000, grid_res=150, c_amplitude=0.3):
    """
    增强渲染主流程
    
    参数:
      c_drop: 1/c 的实参 (NOT c本身!). 要产生连通Julia集(水滴),
              1/c_drop 必须在 Mandelbrot 集内部:
              -1.0+0.0j  → Basilica (经典连通 Julia, 8.7% interior)
              -1.25+0.0j → period-2 bulb (12% interior)
              -0.75+0.0j → period-2 boundary (碎形边界)
      sierpinski_n: Chaos Game点数 (越多→密度场越精细)
      grid_res: 密度场网格分辨率 (越高→c场越精细)
      c_amplitude: Sierpinski调制幅度 (越大→花纹越强)
    """
    if outdir is None:
        outdir = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(outdir, 'enhanced_output')
    os.makedirs(outdir, exist_ok=True)
    t_total = time.time()
    
    print("="*60)
    print("  Enhanced: Sierpinski c-Field x Inverse M Boundary Escape")
    print(f"  Resolution: {H}x{W}  |  c_drop={c_drop}  |  amplitude={c_amplitude}")
    print("="*60)
    
    # --- Step 1: 水滴边界 ---
    dwell_base, boundary_band = compute_water_drop(H, W, c_drop, max_iter=150)
    
    # --- Step 2: Sierpinski c-场 ---
    print(f"\n  [Pre] 生成 Sierpinski 点云 (n={sierpinski_n})...")
    spts = sierpinski_chaos_game(sierpinski_n)
    
    c_field_r, c_field_i, density_field = build_sierpinski_cfield(
        spts, H, W, c_drop, amplitude=c_amplitude, grid_res=grid_res
    )
    
    # --- Step 3: 边界条件逃逸 ---
    esc_r, esc_i, dwell_boundary = boundary_conditioned_escape(
        H, W, c_field_r, c_field_i, boundary_band, max_iter=180
    )
    
    # --- 渲染 ---
    print(f"\n  [Render] 生成输出图像...")
    
    # 图1: 水滴 dwell map (标准逆M)
    fig1, ax1 = plt.subplots(figsize=(8, 8))
    ax1.imshow(dwell_base, cmap='inferno', origin='upper')
    ax1.set_title('Water Drop: Inverse M Dwell Map\n'
                  f'c={c_drop.real:.2f}{c_drop.imag:+.2f}j, max_iter=150',
                  fontsize=12, color='white')
    ax1.set_xticks([]); ax1.set_yticks([])
    fig1.patch.set_facecolor('black')
    fig1.savefig(f'{outdir}/E1_water_drop_dwell.png', dpi=150, facecolor='black', 
                 bbox_inches='tight')
    plt.close(fig1)
    
    # 图2: 边界mask
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    ax2.imshow(boundary_band, cmap='hot', origin='upper')
    ax2.set_title('Boundary Band (dilation=2)', fontsize=12, color='white')
    ax2.set_xticks([]); ax2.set_yticks([])
    fig2.patch.set_facecolor('black')
    fig2.savefig(f'{outdir}/E2_boundary_mask.png', dpi=150, facecolor='black',
                 bbox_inches='tight')
    plt.close(fig2)
    
    # 图3: Sierpinski 密度场
    fig3, ax3 = plt.subplots(figsize=(8, 8))
    ax3.imshow(density_field, cmap='viridis', origin='upper')
    ax3.set_title(f'Sierpinski Density Field (grid={grid_res}x{grid_res})',
                  fontsize=12, color='white')
    ax3.set_xticks([]); ax3.set_yticks([])
    fig3.patch.set_facecolor('black')
    fig3.savefig(f'{outdir}/E3_sierpinski_density.png', dpi=150, facecolor='black',
                 bbox_inches='tight')
    plt.close(fig3)
    
    # 图4: c-场可视化 (幅值)
    c_magnitude = np.sqrt(c_field_r**2 + c_field_i**2)
    fig4, ax4 = plt.subplots(figsize=(8, 8))
    im4 = ax4.imshow(c_magnitude, cmap='plasma', origin='upper')
    ax4.set_title('c-Field Magnitude |c(x,y)|', fontsize=12, color='white')
    ax4.set_xticks([]); ax4.set_yticks([])
    fig4.patch.set_facecolor('black')
    plt.colorbar(im4, ax=ax4, fraction=0.046)
    fig4.savefig(f'{outdir}/E4_cfield_magnitude.png', dpi=150, facecolor='black',
                 bbox_inches='tight')
    plt.close(fig4)
    
    # 图5: 边界逃逸点云 — 低分辨率像素累积+大点散射
    # 策略: 在低分辨率(150x150)做像素累积 → 逃逸点密集 → 再上采样
    low_res = 150
    canvas_low = render_escape_pointcloud(esc_r, esc_i, dwell_boundary, low_res, low_res)
    # 上采样到显示分辨率
    from scipy.ndimage import zoom as ndzoom
    canvas_boundary = ndzoom(canvas_low, (2.67, 2.67, 1), order=1)  # 150→~400
    
    fig5, ax5 = plt.subplots(figsize=(8, 8))
    ax5.imshow(canvas_boundary)
    ax5.set_title('Boundary Escape Cloud (low-res accumulation + upscale)\n'
                  'Sierpinski-modulated c-field flame',
                  fontsize=11, color='white')
    ax5.set_xticks([]); ax5.set_yticks([])
    fig5.patch.set_facecolor('black')
    fig5.savefig(f'{outdir}/E5_boundary_escape_cloud.png', dpi=150, facecolor='black',
                 bbox_inches='tight')
    plt.close(fig5)
    
    # 图6: 融合渲染 (水滴+边界逃逸) — 增强版
    fig6, ax6 = plt.subplots(figsize=(12, 12))
    
    # 底层: 水滴dwell → 暗蓝基底
    dw_disp = dwell_base.astype(float)
    dw_disp[dwell_base == dwell_base.max()] = np.nan  # interior → transparent
    ax6.imshow(dw_disp, cmap='Blues', alpha=0.3, origin='upper', 
               extent=[-2, 2, -2, 2], vmax=150)
    
    # 中层: 水滴内部 → 深蓝色填充
    interior_mask = (dwell_base == dwell_base.max())
    if interior_mask.any():
        y_idx, x_idx = np.where(interior_mask)
        y_c = 2.0 - y_idx * 4.0 / H  # back to complex coords
        x_c = -2.0 + x_idx * 4.0 / W
        ax6.scatter(x_c[::5], y_c[::5], s=0.5, c='#1a1a6e', alpha=0.5, rasterized=True)
    
    # 顶层: 边界逃逸 → 火焰辉光 (三层叠加)
    boundary_valid = dwell_boundary < 180
    if boundary_valid.any():
        er = esc_r[boundary_valid]; ei_vals = esc_i[boundary_valid]
        dw = dwell_boundary[boundary_valid]
        ax6.scatter(er, ei_vals, s=4.0, c=dw, cmap='hot', alpha=0.12, rasterized=True)
        ax6.scatter(er, ei_vals, s=1.5, c=dw, cmap='inferno', alpha=0.35, rasterized=True)
        ax6.scatter(er[::2], ei_vals[::2], s=0.5, c=dw[::2], cmap='hot', alpha=0.85, rasterized=True)
    
    ax6.set_xlim(-2, 2); ax6.set_ylim(-2, 2)
    ax6.set_title('Fusion: Basilica Julia Set + Sierpinski Boundary Escape Halo\n'
                  f'1/c={c_drop}, amplitude={c_amplitude}',
                  fontsize=14, color='white')
    fig6.patch.set_facecolor('#08081E')
    ax6.set_facecolor('black')
    fig6.savefig(f'{outdir}/E6_fusion_drop_and_boundary.png', dpi=200, 
                 facecolor='#08081E', bbox_inches='tight')
    plt.close(fig6)
    
    # 图7: 综合看板 (2x3)
    fig7, axes = plt.subplots(2, 3, figsize=(18, 12))
    titles = [
        'Water Drop Dwell', 'Boundary Band', 'Sierpinski Density',
        'c-Field |c|', 'Boundary Escape Cloud', 'Pure Sierpinski Verify'
    ]
    images = [dwell_base, boundary_band.astype(float), density_field,
              c_magnitude, canvas_boundary, None]
    
    for idx, ax in enumerate(axes.flat):
        if idx == 5:
            # Sierpinski verify
            ax.scatter(spts[::20, 0], spts[::20, 1], s=0.15, c='#00ff44', 
                      alpha=0.6, rasterized=True)
            ax.set_xlim(-0.6, 0.6); ax.set_ylim(-0.5, 1.0)
        elif images[idx] is not None:
            cmap = 'inferno' if idx in [0] else ('hot' if idx==1 else 
                   'viridis' if idx==2 else 'plasma' if idx==3 else None)
            if idx == 4:
                ax.imshow(images[idx])
            else:
                ax.imshow(images[idx], cmap=cmap, origin='upper')
        
        ax.set_title(titles[idx], fontsize=11, color='white')
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_facecolor('black')
    
    fig7.suptitle('Sierpinski x Inverse M Boundary Escape: Full Pipeline\n'
                  f'H={H}x{W}, c_drop={c_drop}, amplitude={c_amplitude}, '
                  f'grid={grid_res}x{grid_res}',
                  fontsize=14, fontweight='bold', color='white')
    fig7.patch.set_facecolor('#08081E')
    plt.tight_layout()
    fig7.savefig(f'{outdir}/E7_composite_dashboard.png', dpi=180, 
                 facecolor='#08081E', bbox_inches='tight')
    plt.close(fig7)
    
    # 图8: 高对比融合 — 低分辨率像素累积确保点云可见
    low_res_fusion = 200
    canvas_fusion = render_escape_pointcloud(esc_r, esc_i, dwell_boundary, 
                                              low_res_fusion, low_res_fusion)
    
    # 构建水滴底色 (同分辨率)
    dw_small = ndzoom(dwell_base.astype(float), 
                       (low_res_fusion/H, low_res_fusion/W), order=1)
    dw_small[dw_small == dw_small.max()] = 0
    dw_n = dw_small / max(dw_small.max(), 1)
    
    # 融合: 水滴底色(冷蓝) + 逃逸点云(火焰) → 纯色叠加
    fusion_rgba = np.zeros((low_res_fusion, low_res_fusion, 4), dtype=np.float32)
    # 水滴底色
    fusion_rgba[..., 0] = np.clip(dw_n * 0.15, 0, 1)
    fusion_rgba[..., 1] = np.clip(dw_n * 0.08, 0, 1)
    fusion_rgba[..., 2] = np.clip(dw_n * 0.50, 0, 1)
    fusion_rgba[..., 3] = np.clip(dw_n * 0.6, 0, 1)
    # interior → 深蓝
    interior_small = (dw_small == 0) & (ndzoom((dwell_base == dwell_base.max()).astype(float),
                                                (low_res_fusion/H, low_res_fusion/W), order=0) > 0.5)
    fusion_rgba[interior_small] = [0.03, 0.03, 0.20, 0.7]
    
    # 逃逸点云叠加
    mask = canvas_fusion[..., 3] > 0.15
    fusion_rgba[mask, :3] = canvas_fusion[mask, :3]
    fusion_rgba[mask, 3] = np.maximum(canvas_fusion[mask, 3], fusion_rgba[mask, 3])
    # 纯黑背景
    empty = fusion_rgba[..., 3] < 0.03
    fusion_rgba[empty] = [0, 0, 0, 1]
    
    # 上采样到显示分辨率
    scale = 4
    fusion_hi = ndzoom(fusion_rgba, (scale, scale, 1), order=1)
    
    fig8, ax8 = plt.subplots(figsize=(14, 14))
    ax8.imshow(fusion_hi)
    ax8.set_title('Sierpinski Self-Similar Halo\n'
                  'Around Basilica Julia Set Boundary\n'
                  f'1/c={c_drop}, amplitude={c_amplitude}',
                  fontsize=15, color='white', fontweight='bold')
    ax8.set_xticks([]); ax8.set_yticks([])
    fig8.patch.set_facecolor('#08081E')
    fig8.savefig(f'{outdir}/E8_feature_halo_around_drop.png', dpi=200,
                 facecolor='#08081E', bbox_inches='tight')
    plt.close(fig8)
    
    elapsed = time.time() - t_total
    print(f"\n  [DONE] {elapsed:.0f}s total")
    print(f"  Output: {outdir}/")
    for f in sorted(os.listdir(outdir)):
        if f.endswith('.png'):
            sz = os.path.getsize(f'{outdir}/{f}') // 1024
            print(f'    {f} ({sz} KB)')
    
    return outdir


# ============================================================
# 6. 参数扫描: 探索c_drop对水滴形状的影响
# ============================================================
def parameter_scan(outdir=None, H=500, W=500):
    """扫描不同c_drop值, 展示水滴形状变化"""
    if outdir is None:
        outdir = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(outdir, 'enhanced_output', 'param_scan')
    os.makedirs(outdir, exist_ok=True)
    
    c_values = [
        complex(0.3, 0.5),   # 经典水滴
        complex(0.35, 0.4),  # 偏右
        complex(0.25, 0.6),  # 偏上
        complex(0.4, 0.3),   # 更圆
        complex(0.2, 0.7),   # 细长
        complex(0.5, 0.2),   # 扁平
    ]
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    for idx, (c_val, ax) in enumerate(zip(c_values, axes.flat)):
        zr = np.linspace(-2, 2, W)
        zi = np.linspace(2, -2, H)
        zr_grid, zi_grid = np.meshgrid(zr, zi)
        dwell = _im_escape_vectorized(
            zr_grid.ravel(), zi_grid.ravel(),
            c_val.real, c_val.imag, 150, H*W
        ).reshape(H, W)
        
        ax.imshow(dwell, cmap='inferno', origin='upper')
        ax.set_title(f'c={c_val.real:.2f}{c_val.imag:+.2f}j', 
                     fontsize=12, color='white')
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_facecolor('black')
    
    fig.suptitle('Inverse M Water Drop: Parameter Scan\nz = z^2 + 1/c',
                 fontsize=14, fontweight='bold', color='white')
    fig.patch.set_facecolor('#08081E')
    plt.tight_layout()
    fig.savefig(f'{outdir}/param_scan_drops.png', dpi=150, 
                facecolor='#08081E', bbox_inches='tight')
    plt.close(fig)
    print(f"  Param scan saved: {outdir}/param_scan_drops.png")


# ============================================================
if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(
        description='Enhanced: Sierpinski c-Field x Inverse M Boundary Escape')
    ap.add_argument('--outdir', default=None)
    ap.add_argument('--H', type=int, default=800)
    ap.add_argument('--W', type=int, default=800)
    ap.add_argument('--c-real', type=float, default=-1.0,
                    help='Real part of 1/c (Mandelbrot set param, -1.0=Basilica)')
    ap.add_argument('--c-imag', type=float, default=0.0,
                    help='Imag part of 1/c')
    ap.add_argument('--amplitude', type=float, default=0.3)
    ap.add_argument('--sierpinski-n', type=int, default=200000)
    ap.add_argument('--grid-res', type=int, default=150)
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--scan', action='store_true')
    args = ap.parse_args()
    
    if args.quick:
        args.H = args.W = 400
        args.sierpinski_n = 50000
        args.grid_res = 80
    
    c_drop = complex(args.c_real, args.c_imag)
    outdir = main(args.outdir, args.H, args.W, c_drop,
                  sierpinski_n=args.sierpinski_n, 
                  grid_res=args.grid_res,
                  c_amplitude=args.amplitude)
    
    if args.scan:
        parameter_scan(args.outdir, min(args.H, 500), min(args.W, 500))
    
    print(f"\nAll outputs in: {outdir}")
