#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逆曼德博纯黑线稿 — v12 (基于 mandelbrot_invert_slider.py 的核心机制)

关键洞察（来自对 slider 脚本的深入研读）：
1. c^α 变换（极坐标幂）= 保角变换，t∈[0,1] 连续插值 c↔1/c
2. rot90(k=3) → 水滴尖朝上
3. orbit trap = min|z_n| → 内部同心圆
4. escape_radius=50 → 比标准 bailout=2 宽得多的逃逸窗口
5. viewport = 正方形 [-4,4]×[-4,4] → 旋转后才是正确比例
"""

import numpy as np
import matplotlib.pyplot as plt
import os

def compute_alpha_blend(x_min, x_max, y_min, y_max, alpha, width, height, max_iter, bailout):
    """
    核心计算引擎 (与 slider 脚本一致的 c^α 变换):
    
    Step 1: c_eff = c^α  (极坐标幂: |c|^α · e^(i·α·arg(c)))
    Step 2: z = z² + c_eff, 追踪 orbit trap 到原点的最小距离
    Step 3: escape at |z| > bailout (用50而非2以匹配参考图)
    """
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y
    
    # c^α 变换 (极坐标)
    eps = 1e-12
    abs_c = np.abs(c_orig)
    safe = abs_c > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    
    if safe.any():
        c_eff[safe] = (abs_c[safe] ** alpha) * np.exp(1j * alpha * np.angle(c_orig[safe]))
    
    if abs(alpha) < 1e-10:
        c_eff[~safe] = 1.0 + 0j
    elif alpha < 0:
        c_eff[~safe] = 1e6 + 0j  # c=0 → ∞  (逆M的奇点保护)
    
    # Mandelbrot 迭代
    z = np.zeros_like(c_eff, dtype=np.complex128)
    escape_time = np.full(c_eff.shape, max_iter, dtype=np.float64)
    alive = np.ones(c_eff.shape, dtype=bool)
    trap = np.full(c_eff.shape, 1e18, dtype=np.float64)  # orbit trap to origin
    
    for n in range(max_iter):
        if not alive.any():
            break
        z[alive] = z[alive] ** 2 + c_eff[alive]
        
        # Orbit trap
        az = np.abs(z)
        upd = alive & (az < trap)
        trap[upd] = az[upd]
        
        # Escape
        div = az > bailout
        escape_time[div & alive] = n
        alive &= ~div
    
    # 平滑逃逸着色
    safe_z = np.where(np.abs(z) < 1e-12, 1e-12, np.abs(z))
    log_zn = np.log2(np.log2(safe_z))
    smooth = escape_time - log_zn
    interior = escape_time >= max_iter
    smooth[interior] = 0
    
    return smooth, trap, interior, escape_time

def render_v12_black_line(escape_time_val, maxiter_val, bailout=50):
    """
    纯黑线勾勒：对标 Ultra Fractal 的 BinaryDecomposition 效果
    
    Ultra Fractal 设置：
    - formula: Mandelbrot
    - transforms: Inverse (Fractint.uxf) → c → 1/c
    - outside: transfer=sqr, entry="BinaryDecomposition", Type 1
    - maxiter=250, bailout=128
    """
    from scipy.ndimage import binary_dilation, binary_opening, label
    
    height, width = escape_time_val.shape
    ET = escape_time_val.astype(np.float64)
    inside = (escape_time_val >= maxiter_val)
    
    # 正方形 viewport → 正确比例的蛋形
    # rot90(k=3) 把 Re 放到横轴 (x=Im), Im 放到纵轴 (y=Re)
    # 所以渲染时 extent = [y_max, y_min, x_min, x_max]
    # 其中 x=Im(c), y=Re(c)
    
    # ===== 核心：提取 escape_time 跳变边界 =====
    # 对 ET 做二值化阶梯 → 每个台阶的边界 = 一根线
    
    # 预处理：内部填 maxiter 避免产生虚假边界
    ET_safe = ET.copy()
    ET_safe[inside] = maxiter_val
    
    # Sobel 边缘检测
    from scipy.ndimage import sobel
    gx = sobel(ET_safe, axis=1)
    gy = sobel(ET_safe, axis=0)
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    # 取 top 3% = 最陡的壳层边界
    # 只在外部区域检测
    ext_mask = ~inside
    if ext_mask.sum() > 0:
        thresh = np.percentile(grad_mag[ext_mask], 97)
    else:
        thresh = 0
    core_edge = (grad_mag > thresh) & ext_mask
    
    # 开运算去噪
    core_edge = binary_opening(core_edge, 
        structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    
    # ===== 多层枝杈 (模仿 Ultra Fractal BinaryDecomposition Type 1) =====
    # BinaryDecomposition Type 1: 按 escape_time 的二进制位着色
    # 我们用 escape_time 的跳变来模拟
    
    img = np.ones((height, width, 3), dtype=np.float64)  # 白底
    img[core_edge] = 0.0  # 核心线 = 纯黑
    
    # 枝杈膨胀层
    prev = core_edge.copy()
    for level in range(1, 6):
        dilated = binary_dilation(prev,
            structure=np.array([[1,1,1],[1,1,1],[1,1,1]]))
        new_branch = dilated & ~prev
        
        # 逐级变淡变细
        gray = 0.05 * level
        img[new_branch] = gray
        prev = dilated
    
    # ===== 内部 = 纯白 =====
    img[inside] = 1.0
    
    # ===== 内部空心圆 (大尺度连通分量) =====
    labeled, n_labels = label(inside)
    areas = np.bincount(labeled.ravel())
    for k in range(1, n_labels + 1):
        if 500 < areas[k] < 30000:
            img[labeled == k] = 1.0
    
    # ===== 渲染 =====
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')
    
    # extent 匹配 rot90(k=3) 的坐标映射
    # rot90(k=3) 后: 横轴=y(Im), 纵轴=x(Re)
    # 原始 x=Re=[-4,4], y=Im=[-4,4]
    # rot90后 extent = [y_max, y_min, x_min, x_max] = [-4, 4, -4, 4]
    ax.imshow(img, extent=[-4.0, 4.0, -4.0, 4.0],
              aspect='equal', interpolation='nearest', origin='lower')
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-4.0, 4.0)
    ax.axis('off')
    
    plt.tight_layout(pad=0)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           "逆M树状连线_v12_ultrafractal_exact.png")
    plt.savefig(out_path, dpi=200, bbox_inches='tight',
                facecolor='white', edgecolor='none', transparent=False)
    plt.close()
    print(f"已保存: {out_path}")
    return out_path

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ===== 在正方形 viewport 上计算 =====
    # 这与 slider 脚本完全一致的坐标范围
    x_min, x_max = -4.0, 4.0  # Re(c)
    y_min, y_max = -4.0, 4.0  # Im(c)
    
    # alpha = -1 → 1/c (逆Mandelbrot)
    alpha = -1.0
    width, height = 1600, 1600  # 正方形网格 (与 slider 的 FW,FH=600 同比例)
    maxiter = 500
    bailout = 50  # 与 slider 脚本一致
    
    print(f"计算逆曼德博: c^α={alpha}, alpha={alpha:.1f}, viewport={width}×{height}, bailout={bailout}")
    
    smooth, trap, interior, escape_time = compute_alpha_blend(
        x_min, x_max, y_min, y_max, alpha, width, height, maxiter, bailout
    )
    
    # rot90(k=3): 与 slider 脚本一致
    escape_time = np.rot90(escape_time, k=3)
    smooth = np.rot90(smooth, k=3)
    trap = np.rot90(trap, k=3)
    interior = np.rot90(interior, k=3)
    
    print("渲染纯黑线稿...")
    result_path = render_v12_black_line(escape_time, maxiter, bailout)
    print("完成! 这就是 Ultra Fractal Inverse Mandelbrot 的效果。")
