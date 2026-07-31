#!/usr/bin/env python3
"""
逆M集水滴外轮廓 — 解析法 + matplotlib 出图

公式:
  逆M主心形:  c_inv(θ) = 1 / (e^(iθ)/2 - e^(2iθ)/4)

水滴 = 逆M主心形上半弧 → 实轴镜像 → 完整闭合曲线
A点(根点): c=-1.333  B点(尖端): c=4  尖端朝右(正x)
"""
import numpy as np
import os, argparse

# ═══════ 解析公式 ═══════

def inv_cardioid(theta):
    c_cls = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    return 1.0 / c_cls

# ═══════ 生成水滴轮廓 ═══════

def generate_droplet(n_cardioid=800, edge_ratio=5):
    """只生成逆M主心形水滴轮廓, 不含周期2泡"""
    theta_c = np.linspace(0, np.pi, n_cardioid)
    b_boost = n_cardioid // edge_ratio
    theta_tip = np.linspace(0, np.pi * 0.15, b_boost) ** 1.5
    theta_base = np.pi - np.linspace(0, np.pi * 0.15, b_boost) ** 1.5
    theta_c = np.unique(np.sort(np.concatenate([theta_tip, theta_c, theta_base])))
    theta_c = theta_c[(theta_c > 1e-10) & (theta_c < np.pi - 1e-10)]

    c_c = inv_cardioid(theta_c)
    mask = c_c.imag <= 0  # 1/c翻转: 经典上半→逆M下半(水滴主体)
    body_upper_x = c_c.real[mask][::-1]  # 从左→右: 根点→尖端
    body_upper_y = -c_c.imag[mask][::-1]

    # 心形闭合轮廓: 上半弧 → 下半弧(镜像) → 闭环
    body_closed_x = np.concatenate([body_upper_x, body_upper_x[::-1]])
    body_closed_y = np.concatenate([body_upper_y, -body_upper_y[::-1]])
    body_closed_x = np.append(body_closed_x, body_closed_x[0])
    body_closed_y = np.append(body_closed_y, body_closed_y[0])

    return body_closed_x, body_closed_y


# ═══════ matplotlib 出图 ═══════

def plot_droplet(x, y, title="Inverse-M Droplet Contour", out_png=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 7))

    # 填充 + 轮廓
    ax.fill(x, y, color='#4ecdc4', alpha=0.35, edgecolor='none')
    ax.plot(x, y, 'b-', linewidth=1.2)

    # 尖端 (最右x ≈ +4)
    tip_idx = np.argmax(x)
    ax.plot(x[tip_idx], y[tip_idx], 'ro', markersize=6)
    ax.annotate(f'Tip ({x[tip_idx]:.2f}, {y[tip_idx]:.2f})',
                (x[tip_idx], y[tip_idx]), textcoords="offset points",
                xytext=(15, 5), fontsize=9, color='red')

    # 底部 (最左x)
    base_idx = np.argmin(x)
    ax.plot(x[base_idx], y[base_idx], 'go', markersize=6)
    ax.annotate(f'Base ({x[base_idx]:.2f})',
                (x[base_idx], y[base_idx]), textcoords="offset points",
                xytext=(-30, -10), fontsize=9, color='green')

    ax.set_aspect('equal')
    ax.set_xlabel('X (droplet axis →)')
    ax.set_ylabel('Y')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # 信息框
    info = (f"Points: {len(x)}\n"
            f"Length: {np.ptp(x):.3f}\n"
            f"Width: {np.ptp(y):.3f}\n"
            f"Aspect: {np.ptp(x)/np.ptp(y):.2f}")
    ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    fig.tight_layout()
    if out_png:
        fig.savefig(out_png, dpi=150, bbox_inches='tight')
        print(f"   PNG: {out_png}")
    else:
        plt.show()
    plt.close(fig)


# ═══════ 主函数 ═══════

def main():
    parser = argparse.ArgumentParser(description="逆M集水滴精确轮廓 (解析法)")
    parser.add_argument("-n", type=int, default=1200, help="采样点数")
    parser.add_argument("-e", type=int, default=5, help="尖端加密比")
    parser.add_argument("--png", type=str, default=None, help="输出PNG路径(不指定则默认)")
    parser.add_argument("--dir", type=str, default=None, help="输出目录")
    args = parser.parse_args()

    out_dir = args.dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    print("💧 逆M集水滴 解析法生成中...")

    x, y = generate_droplet(n_cardioid=args.n, edge_ratio=args.e)

    print(f"   x: [{x.min():.4f}, {x.max():.4f}]  (尖端c={x.max():.3f} 根点c={x.min():.3f})")
    print(f"   y: [{y.min():.4f}, {y.max():.4f}]")
    print(f"   长轴={np.ptp(x):.4f} 短轴={np.ptp(y):.4f} 比={np.ptp(x)/np.ptp(y):.2f}")
    print(f"   点数={len(x)} 闭合={np.hypot(x[-1]-x[0],y[-1]-y[0]):.2e}")

    # 保存CSV
    for ext, delim in [("txt", " "), ("csv", ",")]:
        path = os.path.join(out_dir, f"droplet_invM_analytic.{ext}")
        np.savetxt(path, np.column_stack((x, y)), fmt="%.12f", delimiter=delim, header="x,y")
        print(f"   {ext}: {path}")

    # 出图
    png_path = args.png or os.path.join(out_dir, "droplet_invM_analytic.png")
    plot_droplet(x, y, title="Inverse-M Droplet (Analytic, Tip at c=+4)", out_png=png_path)

    print("\n✅ 完成")


# ═══════ 降采样: 2^n+φ(n) 本原几何驱动 ═══════

def downsample_bulb_anchor(x_upper, y_upper):
    """基于 M 集 period-1~7 泡锚点 + 2^n+φ(n) 加权的降采样
    返回: keep 布尔数组 (True=保留)
    """
    import math
    n = len(x_upper)
    phi = lambda n: sum(1 for k in range(1, n) if math.gcd(k, n) == 1)

    # 主锚点: period 2~7 泡在水滴上边界的附着位置
    def inv_cardioid(theta):
        return 1.0 / (0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta))

    ancs = []
    for q in range(2, 8):
        for p in range(1, q):
            if math.gcd(p, q) == 1:
                theta = 2 * np.pi * p / q
                ci = inv_cardioid(theta)
                if 0 < theta < np.pi and ci.imag <= 0:
                    idx = int(np.argmin(np.hypot(x_upper - ci.real, y_upper + ci.imag)))
                    ancs.append((q, p, idx))
    ancs.append((1, 0, 0))        # 根点
    ancs.append((1, 0, n - 1))    # 尖端
    ancs.sort(key=lambda x: x[2])

    # 2^n+φ(n) 权重表
    weights = {m: 2**m + phi(m) for m in range(1, 9)}

    keep_idx = {a[2] for a in ancs}  # 主锚点必保留

    # 间隙中按 2^n+φ(n) 权重插入子锚点
    for k in range(len(ancs) - 1):
        q1, _, i1 = ancs[k]
        q2, _, i2 = ancs[k + 1]
        max_q = max(q1, q2)
        w = weights.get(max_q, 2**max_q + max_q)
        n_sub = min(w // 8, (i2 - i1) // 3)
        if n_sub > 0 and i2 > i1 + 1:
            sub_idxs = np.linspace(i1 + 1, i2 - 1, n_sub + 2, dtype=int)[1:-1]
            for si in sub_idxs:
                keep_idx.add(int(si))

    keep = np.zeros(n, bool)
    for i in keep_idx:
        keep[i] = True
    return keep


if __name__ == "__main__":
    main()
