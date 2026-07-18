# -*- coding: utf-8 -*-
"""
Glynn 分形 f(z) = z^1.5 - 0.2 渲染器（仿参考图配色版）
流程:
  1. 读取参考图 hfgjhgj.webp -> 提取尺寸/长宽比/背景色/中心色/主色集合
  2. 由主色构建色板 (背景色=快逃逸端, 中心色=内部填充, 其余色按最近邻链排序)
  3. 修正版逃逸时间算法: 活跃索引压缩 + 吸引子捕获(内部早停) + 平滑 mu
  4. 直方图均衡化上色 + 2x 超采样抗锯齿
  5. 输出 PNG + 数值比对输出图与参考图的主色距离
"""
import numpy as np
from PIL import Image
from pathlib import Path
import time

TARGET_DIR = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关")
REF_PATH = TARGET_DIR / "hfgjhgj.webp"
OUT_PATH = TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_2026-07-18.png"

POWER = 1.5
C = -0.2

# ---------- 1. 参考图分析 ----------
def analyze_reference(path, n_colors=10):
    info = {}
    img = Image.open(path).convert("RGB")
    info["size"] = img.size                      # (W, H)
    info["aspect"] = img.size[0] / img.size[1]
    # 分析用缩略图
    small = img.copy()
    small.thumbnail((512, 512))
    arr = np.asarray(small).astype(np.float64) / 255.0
    h, w = arr.shape[:2]
    # 背景色 = 四角均值
    k = max(4, min(h, w) // 20)
    corners = np.concatenate([
        arr[:k, :k].reshape(-1, 3), arr[:k, -k:].reshape(-1, 3),
        arr[-k:, :k].reshape(-1, 3), arr[-k:, -k:].reshape(-1, 3)])
    info["bg"] = corners.mean(axis=0)
    # 主色: 自适应量化
    q = small.convert("P", palette=Image.ADAPTIVE, colors=n_colors)
    pal = np.array(q.getpalette()).reshape(-1, 3)[:n_colors] / 255.0
    counts = np.bincount(np.asarray(q).ravel(), minlength=n_colors).astype(float)
    counts /= counts.sum()
    order = np.argsort(-counts)
    info["dom_colors"] = pal[order]
    info["dom_weights"] = counts[order]
    # 中心色 = 中央 30% 区域出现最多的量化色 (通常是填充 Julia 集内部)
    qa = np.asarray(q)
    cy0, cy1 = int(h * 0.35), int(h * 0.65)
    cx0, cx1 = int(w * 0.35), int(w * 0.65)
    center_idx = np.bincount(qa[cy0:cy1, cx0:cx1].ravel(), minlength=n_colors).argmax()
    info["interior"] = pal[center_idx]
    # 亮度直方图 (验证用)
    lum = arr @ np.array([0.299, 0.587, 0.114])
    info["lum_hist"] = np.histogram(lum, bins=10, range=(0, 1))[0] / lum.size
    return info


def build_palette(info):
    """背景色 -> (最近邻链排序的中间主色) -> 边界色; 内部色单独填充"""
    bg = info["bg"]; interior = info["interior"]
    cand = []
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        if w_ < 0.02:
            continue
        if np.linalg.norm(c_ - bg) < 0.10 or np.linalg.norm(c_ - interior) < 0.10:
            continue
        cand.append(c_)
    # 最近邻贪心链: 从背景色出发, 保证渐变平滑
    chain = [bg]
    rest = list(cand)
    while rest:
        last = chain[-1]
        d = [np.linalg.norm(r - last) for r in rest]
        j = int(np.argmin(d))
        chain.append(rest.pop(j))
    anchors = np.array(chain)
    pos = np.linspace(0, 1, len(anchors))
    return pos, anchors


def apply_palette(norm, pos, anchors):
    out = np.empty(norm.shape + (3,))
    for ch in range(3):
        out[..., ch] = np.interp(norm, pos, anchors[:, ch])
    return out


# ---------- 2. 分形计算 (修正版) ----------
def find_attractor(power, c, warm=600, tail=8):
    z = 0.0 + 0.0j
    with np.errstate(all="ignore"):
        for _ in range(warm):
            z = z ** power + c
        orbit = []
        for _ in range(tail):
            z = z ** power + c
            orbit.append(z)
    cands = []
    for o in orbit:
        cands.append(o); cands.append(np.conj(o))
    return np.array(cands)


def glynn_field(power, c, xlim, ylim, W, H, max_iter=400, R=8.0, attractors=None):
    xs = np.linspace(xlim[0], xlim[1], W)
    ys = np.linspace(ylim[1], ylim[0], H)          # 顶行 = ymax
    X, Y = np.meshgrid(xs, ys)
    z = (X + 1j * Y).ravel()
    N = z.size
    mu = np.full(N, np.nan)
    interior = np.zeros(N, dtype=bool)
    active = np.arange(N)
    logR = np.log(R); logd = np.log(power)
    t0 = time.time()
    with np.errstate(all="ignore"):
        for i in range(max_iter):
            za = z[active] ** power + c            # numpy 主分支幂
            z[active] = za
            r = np.abs(za)
            esc = r > R
            if esc.any():
                idx = active[esc]
                mu[idx] = (i + 1) - np.log(np.log(r[esc]) / logR) / logd
            conv = np.zeros(za.shape, dtype=bool)
            if attractors is not None and i > 10:
                dmin = np.full(za.shape, np.inf)
                for a in attractors:
                    d = np.abs(za - a)
                    np.minimum(dmin, d, out=dmin)
                conv = dmin < 1e-7
                if conv.any():
                    interior[active[conv]] = True
            done = esc | conv
            if done.any():
                active = active[~done]
            if active.size == 0:
                break
    interior[active] = True                        # 未判定 -> 视作内部/边界
    print(f"  field {W}x{H}: {time.time()-t0:.1f}s, interior={interior.sum()/N*100:.1f}%")
    return mu.reshape(H, W), interior.reshape(H, W)


def auto_window(power, c, aspect, attractors):
    """粗渲染找结构 bbox, 再按参考图长宽比扩展"""
    mu, inter = glynn_field(power, c, (-1.6, 1.6), (-1.6, 1.6), 420, 420,
                            max_iter=150, attractors=attractors)
    esc_vals = mu[~np.isnan(mu)]
    thr = np.quantile(esc_vals, 0.97)
    structure = inter | (np.nan_to_num(mu, nan=np.inf) >= thr)
    rows = np.where(structure.any(axis=1))[0]
    cols = np.where(structure.any(axis=0))[0]
    xs = np.linspace(-1.6, 1.6, 420); ys = np.linspace(1.6, -1.6, 420)
    x0, x1 = xs[cols[0]], xs[cols[-1]]
    y1, y0 = ys[rows[0]], ys[rows[-1]]
    # padding 12%
    pw = (x1 - x0) * 0.12; ph = (y1 - y0) * 0.12
    x0 -= pw; x1 += pw; y0 -= ph; y1 += ph
    # 扩展到目标长宽比
    w, h = x1 - x0, y1 - y0
    if w / h < aspect:
        extra = (aspect * h - w) / 2; x0 -= extra; x1 += extra
    else:
        extra = (w / aspect - h) / 2; y0 -= extra; y1 += extra
    print(f"  window: x[{x0:.3f},{x1:.3f}] y[{y0:.3f},{y1:.3f}] aspect={(x1-x0)/(y1-y0):.3f}")
    return (x0, x1), (y0, y1)


# ---------- 3. 主流程 ----------
def main():
    print("=== 1. 分析参考图 ===")
    info = analyze_reference(REF_PATH)
    print(f"  参考图: {info['size'][0]}x{info['size'][1]} aspect={info['aspect']:.3f}")
    print(f"  背景色 RGB: {np.round(info['bg']*255).astype(int)}")
    print(f"  中心(内部)色 RGB: {np.round(info['interior']*255).astype(int)}")
    print("  主色(按占比):")
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        print(f"    {np.round(c_*255).astype(int)}  {w_*100:.1f}%")

    pos, anchors = build_palette(info)
    print(f"  色板锚点数: {len(anchors)}")

    print("=== 2. 吸引子 ===")
    att = find_attractor(POWER, C)
    print(f"  吸引子候选: {np.round(att[:4], 4)}")

    print("=== 3. 自动取景 ===")
    xlim, ylim = auto_window(POWER, C, info["aspect"], att)

    print("=== 4. 最终渲染 (2x 超采样) ===")
    W_out = min(info["size"][0], 1920)
    H_out = int(round(W_out / info["aspect"]))
    ss = 2
    mu, inter = glynn_field(POWER, C, xlim, ylim, W_out * ss, H_out * ss,
                            max_iter=400, attractors=att)

    # 直方图均衡化: 逃逸像素按秩归一化
    esc = ~inter & ~np.isnan(mu)
    norm = np.zeros_like(mu)
    vals = mu[esc]
    ranks = np.argsort(np.argsort(vals)).astype(np.float64)
    norm[esc] = ranks / max(len(vals) - 1, 1)

    rgb = apply_palette(norm, pos, anchors)
    rgb[inter] = info["interior"]

    # 降采样抗锯齿
    rgb = rgb.reshape(H_out, ss, W_out, ss, 3).mean(axis=(1, 3))
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    img.save(OUT_PATH)
    print(f"  已保存: {OUT_PATH} ({W_out}x{H_out})")

    print("=== 5. 与参考图数值比对 ===")
    out_info = analyze_reference(OUT_PATH)
    # 主色最小距离 (加权)
    dsum = wsum = 0.0
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        if w_ < 0.02:
            continue
        d = min(np.linalg.norm(c_ - oc) for oc in out_info["dom_colors"])
        dsum += d * w_; wsum += w_
    print(f"  参考主色 -> 输出最近主色 加权平均距离: {dsum/wsum:.4f} (0=完全一致, <0.15 视为同风格)")
    l1 = np.abs(info["lum_hist"] - out_info["lum_hist"]).sum()
    print(f"  亮度直方图 L1 距离: {l1:.4f} (0=完全一致)")


if __name__ == "__main__":
    main()
