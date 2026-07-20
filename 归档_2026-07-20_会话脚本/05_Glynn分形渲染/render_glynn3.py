# -*- coding: utf-8 -*-
"""
Glynn 分形 f(z) = z^1.5 - 0.2 渲染器 v3（仿参考图配色, 修复版）
- 参考图分析: 背景橙红(210,53,0) / 内部黄绿(159,193,23) —— 经典 Glynn 配色
- 修复: 临界轨道逃逸导致的 OverflowError -> numpy 标量 + isfinite 检测, 纯逃逸时间模式
- 色板: 最近邻链排序 + 按参考图色占比加权定位 -> 输出颜色比例贴近参考图
- 渲染: 活跃索引压缩逃逸时间 + 平滑 mu + 直方图均衡化 + 2x 超采样
"""
import numpy as np
from PIL import Image
from pathlib import Path
import time

TARGET_DIR = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关")
REF_PATH = TARGET_DIR / "hfgjhgj.webp"
OUT_PATH = TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_2026-07-18.png"
OUT_HI_PATH = TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_高清2048_2026-07-18.png"

POWER = 1.5
C = -0.2


# ---------- 1. 参考图分析 ----------
def analyze_reference(path, n_colors=10):
    info = {}
    img = Image.open(path).convert("RGB")
    info["size"] = img.size
    info["aspect"] = img.size[0] / img.size[1]
    small = img.copy()
    small.thumbnail((512, 512))
    arr = np.asarray(small).astype(np.float64) / 255.0
    h, w = arr.shape[:2]
    k = max(4, min(h, w) // 20)
    corners = np.concatenate([
        arr[:k, :k].reshape(-1, 3), arr[:k, -k:].reshape(-1, 3),
        arr[-k:, :k].reshape(-1, 3), arr[-k:, -k:].reshape(-1, 3)])
    info["bg"] = corners.mean(axis=0)
    q = small.convert("P", palette=Image.ADAPTIVE, colors=n_colors)
    pal = np.array(q.getpalette()).reshape(-1, 3)[:n_colors] / 255.0
    counts = np.bincount(np.asarray(q).ravel(), minlength=n_colors).astype(float)
    counts /= counts.sum()
    order = np.argsort(-counts)
    info["dom_colors"] = pal[order]
    info["dom_weights"] = counts[order]
    qa = np.asarray(q)
    cy0, cy1 = int(h * 0.35), int(h * 0.65)
    cx0, cx1 = int(w * 0.35), int(w * 0.65)
    center_idx = np.bincount(qa[cy0:cy1, cx0:cx1].ravel(), minlength=n_colors).argmax()
    info["interior"] = pal[center_idx]
    lum = arr @ np.array([0.299, 0.587, 0.114])
    info["lum_hist"] = np.histogram(lum, bins=10, range=(0, 1))[0] / lum.size
    return info


def build_palette(info):
    """最近邻链排序 + 色占比加权定位。返回 (pos, colors)。"""
    bg = info["bg"]; interior = info["interior"]
    cand = []
    bg_mass = 0.05                                     # 角落基础质量
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        if w_ < 0.02:
            continue
        if np.linalg.norm(c_ - interior) < 0.10:       # 内部色 -> 单独填充
            continue
        if np.linalg.norm(c_ - bg) < 0.10:             # 近背景色并入背景质量
            bg_mass += w_
            continue
        cand.append((c_, w_))
    chain = [(bg, bg_mass)]
    rest = list(cand)
    while rest:
        last = chain[-1][0]
        j = int(np.argmin([np.linalg.norm(r[0] - last) for r in rest]))
        chain.append(rest.pop(j))
    colors = np.array([c for c, _ in chain])
    masses = np.array([w for _, w in chain], dtype=float)
    total = masses.sum()
    starts = np.cumsum(masses) - masses
    pos = (starts + masses * 0.5) / total              # 每色带中点 = 锚点位置
    pos[0] = 0.0
    pos[-1] = max(pos[-1], 0.99)
    pos = np.maximum.accumulate(pos) + np.arange(len(pos)) * 1e-9
    return pos, colors


def apply_palette(norm, pos, colors):
    out = np.empty(norm.shape + (3,))
    for ch in range(3):
        out[..., ch] = np.interp(norm, pos, colors[:, ch])
    return out


# ---------- 2. 分形计算 ----------
def find_attractor(power, c, warm=600, tail=8):
    """临界点 z=0 轨道 -> 吸引子候选; 若逃逸返回 None (纯逃逸时间模式)"""
    z = np.complex128(0)
    with np.errstate(all="ignore"):
        for _ in range(warm):
            z = z ** power + c
            if not np.isfinite(z):
                return None
        orbit = []
        for _ in range(tail):
            z = z ** power + c
            if not np.isfinite(z):
                return None
            orbit.append(complex(z))
    cands = []
    for o in orbit:
        cands.append(o); cands.append(np.conj(o))
    return np.array(cands)


def glynn_field(power, c, xlim, ylim, W, H, max_iter=400, R=8.0, attractors=None):
    """活跃索引压缩的平滑逃逸时间场。R=8 保证逃逸时 |z|∈(8,23), mu 无溢出。"""
    xs = np.linspace(xlim[0], xlim[1], W)
    ys = np.linspace(ylim[1], ylim[0], H)
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
            za = z[active] ** power + c
            z[active] = za
            r = np.abs(za)
            esc = r > R
            if esc.any():
                idx = active[esc]
                mu[idx] = (i + 1) - np.log(np.log(r[esc]) / logR) / logd
            conv = np.zeros(za.shape, dtype=bool)
            if attractors is not None and len(attractors) and i > 10:
                dmin = np.full(za.shape, np.inf)
                for a in attractors:
                    np.minimum(dmin, np.abs(za - a), out=dmin)
                conv = dmin < 1e-7
                if conv.any():
                    interior[active[conv]] = True
            done = esc | conv
            if done.any():
                active = active[~done]
            if active.size == 0:
                break
    interior[active] = True
    print(f"  field {W}x{H}: {time.time()-t0:.1f}s, interior={interior.sum()/N*100:.1f}%",
          flush=True)
    return mu.reshape(H, W), interior.reshape(H, W)


def auto_window(power, c, aspect, attractors):
    mu, inter = glynn_field(power, c, (-1.6, 1.6), (-1.6, 1.6), 420, 420,
                            max_iter=150, attractors=attractors)
    esc_vals = mu[~np.isnan(mu)]
    thr = np.quantile(esc_vals, 0.97)
    structure = inter | (np.nan_to_num(mu, nan=-np.inf) >= thr)
    rows = np.where(structure.any(axis=1))[0]
    cols = np.where(structure.any(axis=0))[0]
    xs = np.linspace(-1.6, 1.6, 420); ys = np.linspace(1.6, -1.6, 420)
    x0, x1 = xs[cols[0]], xs[cols[-1]]
    y1, y0 = ys[rows[0]], ys[rows[-1]]
    pw = (x1 - x0) * 0.12; ph = (y1 - y0) * 0.12
    x0 -= pw; x1 += pw; y0 -= ph; y1 += ph
    w, h = x1 - x0, y1 - y0
    if w / h < aspect:
        extra = (aspect * h - w) / 2; x0 -= extra; x1 += extra
    else:
        extra = (w / aspect - h) / 2; y0 -= extra; y1 += extra
    print(f"  window: x[{x0:.3f},{x1:.3f}] y[{y0:.3f},{y1:.3f}] "
          f"aspect={(x1-x0)/(y1-y0):.3f}")
    return (x0, x1), (y0, y1)


# ---------- 3. 主流程 ----------
def main():
    print("=== 1. 分析参考图 ===")
    info = analyze_reference(REF_PATH)
    print(f"  参考图: {info['size'][0]}x{info['size'][1]} aspect={info['aspect']:.3f}")
    print(f"  背景色: {np.round(info['bg']*255).astype(int)}  "
          f"内部色: {np.round(info['interior']*255).astype(int)}")
    pos, colors = build_palette(info)
    print(f"  色板锚点: {len(colors)} 个, 位置 {np.round(pos, 3)}")

    print("=== 2. 吸引子探测 ===")
    att = find_attractor(POWER, C)
    if att is None:
        print("  临界轨道逃逸 -> 纯逃逸时间模式 (无内部早停)")
    else:
        print(f"  吸引子候选: {np.round(att[:4], 4)}")

    print("=== 3. 自动取景 ===")
    xlim, ylim = auto_window(POWER, C, info["aspect"], att)

    print("=== 4. 最终渲染 (2x 超采样) ===")
    W_out = min(info["size"][0], 1920)
    H_out = int(round(W_out / info["aspect"]))
    ss = 2
    mu, inter = glynn_field(POWER, C, xlim, ylim, W_out * ss, H_out * ss,
                            max_iter=400, attractors=att)

    esc = ~inter & ~np.isnan(mu)
    norm = np.zeros_like(mu)
    vals = mu[esc]
    ranks = np.argsort(np.argsort(vals)).astype(np.float64)
    norm[esc] = ranks / max(len(vals) - 1, 1)          # 直方图均衡化

    rgb = apply_palette(norm, pos, colors)
    rgb[inter] = info["interior"]

    rgb_hi = np.clip(rgb, 0, 1)
    Image.fromarray((rgb_hi * 255).astype(np.uint8)).save(OUT_HI_PATH)
    rgb_lo = rgb_hi.reshape(H_out, ss, W_out, ss, 3).mean(axis=(1, 3))
    Image.fromarray((np.clip(rgb_lo, 0, 1) * 255).astype(np.uint8)).save(OUT_PATH)
    print(f"  已保存: {OUT_PATH.name} ({W_out}x{H_out})")
    print(f"  已保存: {OUT_HI_PATH.name} ({W_out*ss}x{H_out*ss})")

    print("=== 5. 与参考图数值比对 ===")
    out_info = analyze_reference(OUT_PATH)
    dsum = wsum = 0.0
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        if w_ < 0.02:
            continue
        d = min(np.linalg.norm(c_ - oc) for oc in out_info["dom_colors"])
        dsum += d * w_; wsum += w_
    print(f"  参考主色->输出最近主色 加权平均距离: {dsum/wsum:.4f} "
          f"(0=一致, <0.15 同风格)")
    l1 = np.abs(info["lum_hist"] - out_info["lum_hist"]).sum()
    print(f"  亮度直方图 L1 距离: {l1:.4f} (0=一致, <0.6 分布接近)")
    print(f"  输出内部色: {np.round(out_info['interior']*255).astype(int)} "
          f"vs 参考 {np.round(info['interior']*255).astype(int)}")
    print(f"  输出背景色: {np.round(out_info['bg']*255).astype(int)} "
          f"vs 参考 {np.round(info['bg']*255).astype(int)}")


if __name__ == "__main__":
    main()
