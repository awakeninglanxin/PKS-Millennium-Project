import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
import time


def glynn_smooth(c=-0.2, power=1.5, width=2400, height=1440,
                 xlim=(-2.3, 2.3), ylim=(-1.4, 1.4),
                 max_iter=1200, escape=2.0):
    """
    Glynn 分形: z -> z^power + c
    使用平滑逃逸时间计数，避免非整数幂带来的分支切割带状伪影。
    """
    x = np.linspace(xlim[0], xlim[1], width)
    y = np.linspace(ylim[0], ylim[1], height)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    mask = np.ones((height, width), dtype=bool)
    iter_count = np.zeros((height, width), dtype=np.float64)

    t0 = time.time()
    for i in range(max_iter):
        # 只更新未逃逸点
        z = Z[mask]
        # 复数主分支幂: z^power = exp(power * log(z))
        z = np.exp(power * np.log(z)) + c
        Z[mask] = z
        escaped = np.abs(z) > escape

        # 记录平滑逃逸计数
        if escaped.any():
            z_esc = z[escaped]
            # mu = i - log(log|z| / log(R)) / log(power)
            mu = i - np.log(np.log(np.abs(z_esc)) / np.log(escape)) / np.log(power)
            idx = np.where(mask)[0][escaped]
            iter_count.flat[idx] = mu
            mask.flat[idx] = False

        if not mask.any():
            break

        if (i + 1) % 200 == 0:
            print(f"  iter {i+1}/{max_iter}, remaining {mask.sum()}, {time.time()-t0:.1f}s", flush=True)

    # 未逃逸点设为 max_iter
    iter_count[mask] = max_iter
    print(f"Glynn render done: {width}x{height}, max_iter={max_iter}, {time.time()-t0:.1f}s")
    return iter_count


def make_glynn_colormap():
    """
    复刻参考图配色：
    外层(快逃逸) -> 橙红；中间 -> 黄绿；内部(慢逃逸) -> 蓝紫/红。
    """
    colors = [
        (0.00, (0.20, 0.00, 0.35)),  # 深紫红 (最内不逃逸)
        (0.10, (0.85, 0.00, 0.15)),  # 红
        (0.22, (0.25, 0.35, 0.75)),  # 蓝紫
        (0.38, (0.00, 0.65, 0.70)),  # 青
        (0.55, (0.50, 0.90, 0.00)),  # 黄绿
        (0.75, (0.95, 0.55, 0.00)),  # 橙
        (0.90, (0.85, 0.15, 0.05)),  # 红橙
        (1.00, (0.70, 0.05, 0.00)),  # 深红橙 (最外)
    ]
    return LinearSegmentedColormap.from_list("glynn", colors)


def render_glynn(out_path, width=2400, height=1440, **kwargs):
    M = glynn_smooth(width=width, height=height, **kwargs)

    # 归一化到 [0,1] 用于 colormap
    m_min = M[M < kwargs.get('max_iter', 1200)].min() if (M < kwargs.get('max_iter', 1200)).any() else 0
    m_max = M.max()
    print(f"mu range: {m_min:.2f} .. {m_max:.2f}")

    # 归一化
    norm = (M - m_min) / (m_max - m_min + 1e-12)
    norm = np.clip(norm, 0, 1)

    cmap = make_glynn_colormap()
    img = cmap(norm)

    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    ax.imshow(img, origin='lower')
    ax.axis('off')
    plt.tight_layout(pad=0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=100, pad_inches=0)
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    out = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关\Glynn_z1p5_minus0p2_render_2400x1440.png")
    render_glynn(out, c=-0.2, power=1.5, width=2400, height=1440,
                 xlim=(-2.3, 2.3), ylim=(-1.4, 1.4), max_iter=1200, escape=2.0)
