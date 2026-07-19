#!/usr/bin/env python3
"""
逆M集水滴外轮廓生成器 — 只取光滑外廓, 消除内部芽/泡分形结构
z → z² + 1/c | 泡中心: c = e^(iθ)/2 - e^(2iθ)/4, θ=2π·p/q

输出: 闭合光滑轮廓点 → CSV/TXT → CFD网格生成
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import measure
import os, argparse

# ═══════ 逆M集逃逸时间 z²+1/c (纯mask, 不用np.nan) ═══════
def escape_time(C, max_iter=500, R=1e4):
    """逆M集: z←z²+1/c"""
    h, w = C.shape
    Z = np.zeros_like(C, dtype=np.complex128)
    iters = np.full((h, w), max_iter, dtype=np.int32)
    alive = np.ones((h, w), dtype=bool)

    for i in range(max_iter):
        if not alive.any():
            break
        Z[alive] = Z[alive] * Z[alive] + 1.0 / C[alive]
        escaped = alive & (np.abs(Z) >= R)
        iters[escaped] = i + 1
        alive[escaped] = False
    return iters


# ═══════ 泡中心公式 ═══════
def bulb_center(p, q):
    """Farey p/q → 逆M集泡中心: c = 1/(e^(iθ)/2 - e^(2iθ)/4)"""
    theta = 2 * np.pi * p / q
    c_cls = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    return 1.0 / c_cls  # c→1/c变换, 经典M→逆M


# ═══════ 光滑轮廓提取 ═══════
def extract_droplet_contour(p, q, resolution=2000, max_iter=600,
                            window=0.18, smooth_sigma=3.0, min_points=100):
    """
    提取逆M集 p/q 泡的光滑外轮廓(无内部芽结构)
    
    策略:
    1. 高分辨率逃逸时间 (resolution×resolution)
    2. 取 max_iter/2 等值线 → 这是集边界的主要轮廓
    3. 对轮廓做高斯平滑去除分形噪声
    4. 只取包围泡中心的闭合曲线
    """
    c0 = bulb_center(p, q)
    half = window / 2
    xs = np.linspace(c0.real - half, c0.real + half, resolution)
    ys = np.linspace(c0.imag - half, c0.imag + half, resolution)
    X, Y = np.meshgrid(xs, ys)
    C = X + 1j * Y

    print(f"  🔄 计算逃逸时间... ({resolution}×{resolution}, max_iter={max_iter})")
    iters = escape_time(C, max_iter)

    # 高斯平滑逃逸场 → 消除分形微结构
    print(f"  🧹 高斯平滑 σ={smooth_sigma}...")
    iters_smooth = gaussian_filter(iters.astype(np.float64), sigma=smooth_sigma)

    # 二值化：内部点 = 未逃逸 (iters==max_iter)
    interior = (iters_smooth > max_iter * 0.9)  # 平滑后阈值90%即内部
    print(f"  🔍 内部区域: {(interior).sum()} 点")
    contours = measure.find_contours(interior.astype(np.float64), level=0.5)

    # 选最靠近c0的最大闭合轮廓
    best, best_dist, best_len = None, float('inf'), 0
    for cnt in contours:
        if len(cnt) < min_points:
            continue
        # 像素→物理坐标 (注意: skimage contour 是 (row,col))
        cx = xs[0] + cnt[:, 1] * window / (resolution - 1)
        cy = ys[0] + cnt[:, 0] * window / (resolution - 1)
        centroid = complex(np.mean(cx), np.mean(cy))
        dist = abs(centroid - c0)
        # 优先: 离c0近 + 轮廓长
        if dist < best_dist or (abs(dist - best_dist) < 1e-4 and len(cnt) > best_len):
            best_dist = dist
            best_len = len(cnt)
            best = (cx, cy)

    if best is None:
        raise RuntimeError(f"未找到闭合轮廓 (p/q={p}/{q}), 尝试增大window或降低smooth_sigma")

    # 确保闭合
    x, y = best
    if np.hypot(x[-1]-x[0], y[-1]-y[0]) > 1e-8 * window:
        x = np.append(x, x[0])
        y = np.append(y, y[0])

    print(f"  ✅ 轮廓 {len(x)} 点, 质心距={best_dist:.6f}")
    return x, y, c0


# ═══════ 主函数 ═══════
def main():
    parser = argparse.ArgumentParser(description="生成逆M集水滴光滑外轮廓")
    parser.add_argument("-p", type=int, default=1, help="Farey分子 (默认1)")
    parser.add_argument("-q", type=int, default=3, help="Farey分母 (默认3)")
    parser.add_argument("-r", type=int, default=2000, help="分辨率 (默认2000)")
    parser.add_argument("--iter", type=int, default=600, help="最大迭代 (默认600)")
    parser.add_argument("-w", type=float, default=0.18, help="窗口大小 (默认0.18)")
    parser.add_argument("-s", type=float, default=3.0, help="高斯平滑σ (默认3)")
    parser.add_argument("--dir", type=str, default=None, help="输出目录")
    args = parser.parse_args()

    out_dir = args.dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    label = f"p{args.p}_q{args.q}"
    print(f"🎯 逆M水滴外轮廓: {label}")
    print(f"   泡中心: {bulb_center(args.p, args.q):.6f}")

    x, y, c0 = extract_droplet_contour(
        args.p, args.q,
        resolution=args.r,
        max_iter=args.iter,
        window=args.w,
        smooth_sigma=args.s,
    )

    # 保存
    txt_path = os.path.join(out_dir, f"droplet_{label}.txt")
    np.savetxt(txt_path, np.column_stack((x, y)), fmt="%.10f",
               header=f"逆M集水滴轮廓 {label} centroid≈{c0.real:.6f}+{c0.imag:.6f}j")

    csv_path = os.path.join(out_dir, f"droplet_{label}.csv")
    np.savetxt(csv_path, np.column_stack((x, y)), fmt="%.10f", delimiter=",",
               header="x,y")

    print(f"\n📦 输出:")
    print(f"   {txt_path}  ({len(x)} 点)")
    print(f"   {csv_path}  ({len(x)} 点)")
    print(f"\n💡 CFD导入: OpenFOAM → blockMesh/snappyHexMesh 直接用CSV")
    print(f"   对照椭圆: 长轴={np.ptp(x):.4f}, 短轴≈{np.ptp(y):.4f}")


if __name__ == "__main__":
    main()
