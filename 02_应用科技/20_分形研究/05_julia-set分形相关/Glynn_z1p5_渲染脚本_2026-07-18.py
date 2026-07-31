# -*- coding: utf-8 -*-
"""
Glynn 分形 f(z) = z^1.5 - 0.2 渲染器 v4（按参考图色系占比精确分带）
关键修正 (相对 v3): 参考图中心是黄绿"Glynn树"主体(~36.5%色系占比),
v3 绿带只占 12% 导致树体偏橙黄。v4 按色系真实占比分带:
  逃逸秩 [0, 0.575)   -> 橙红背景族 (210,53,0)->(212,84,7)->(213,117,14)
  逃逸秩 [0.575,0.94) -> 黄绿树体族 (196,178,25)->(159,193,23)->(95,155,53)
  逃逸秩 [0.94, 1.0]  -> 暗红树脊 (158,41,51)
验证: 输出中心 30% 区域主色 vs 参考中心主色 + 绿系像素占比 + 并排对比图
"""
import numpy as np
from PIL import Image
from pathlib import Path
import time

TARGET_DIR = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关")
REF_PATH = TARGET_DIR / "hfgjhgj.webp"
OUT_PATH = TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_2026-07-18.png"
OUT_HI_PATH = TARGET_DIR / "Glynn_z1p5_c-0p2_仿参考渲染_高清2048_2026-07-18.png"
CMP_PATH = TARGET_DIR / "Glynn_渲染对比_参考vs输出_2026-07-18.png"

POWER = 1.5
C = -0.2

# 参考图分析结果 (v3 实测): 主色与占比
REF_BG = np.array([210, 53, 0]) / 255.0          # 背景橙红
REF_INTERIOR = np.array([159, 193, 23]) / 255.0  # 树体黄绿


def analyze_reference(path, n_colors=10):
    info = {}
    img = Image.open(path).convert("RGB")
    info["size"] = img.size
    info["aspect"] = img.size[0] / img.size[1]
    small = img.copy(); small.thumbnail((512, 512))
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
    info["dom_colors"] = pal[order]; info["dom_weights"] = counts[order]
    qa = np.asarray(q)
    cy0, cy1 = int(h*0.35), int(h*0.65); cx0, cx1 = int(w*0.35), int(w*0.65)
    center_idx = np.bincount(qa[cy0:cy1, cx0:cx1].ravel(), minlength=n_colors).argmax()
    info["interior"] = pal[center_idx]
    info["arr_small"] = arr
    return info


def green_fraction(arr):
    """绿系像素占比: G 通道显著大于 R 或 (G>R*0.8 且 B 低) 的黄绿系"""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    green = (g > r * 0.82) & (b < 0.45)
    return green.mean()


def glynn_field(power, c, xlim, ylim, W, H, max_iter=400, R=8.0):
    xs = np.linspace(xlim[0], xlim[1], W)
    ys = np.linspace(ylim[1], ylim[0], H)
    X, Y = np.meshgrid(xs, ys)
    z = (X + 1j * Y).ravel()
    N = z.size
    mu = np.full(N, np.nan)
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
                active = active[~esc]
            if active.size == 0:
                break
    inner = np.zeros(N, dtype=bool)
    inner[active] = True                    # 未逃逸 (≈0%, Glynn 树是慢逃逸结构)
    print(f"  field {W}x{H}: {time.time()-t0:.1f}s, non-escaped={inner.mean()*100:.2f}%",
          flush=True)
    return mu.reshape(H, W), inner.reshape(H, W)


def auto_window(power, c, aspect):
    mu, inner = glynn_field(power, c, (-1.6, 1.6), (-1.6, 1.6), 420, 420, max_iter=150)
    esc_vals = mu[~np.isnan(mu)]
    thr = np.quantile(esc_vals, 0.97)
    structure = inner | (np.nan_to_num(mu, nan=-np.inf) >= thr)
    rows = np.where(structure.any(axis=1))[0]
    cols = np.where(structure.any(axis=0))[0]
    xs = np.linspace(-1.6, 1.6, 420); ys = np.linspace(1.6, -1.6, 420)
    x0, x1 = xs[cols[0]], xs[cols[-1]]
    y1, y0 = ys[rows[0]], ys[rows[-1]]
    pw = (x1-x0)*0.12; ph = (y1-y0)*0.12
    x0 -= pw; x1 += pw; y0 -= ph; y1 += ph
    w, h = x1-x0, y1-y0
    if w/h < aspect:
        e = (aspect*h - w)/2; x0 -= e; x1 += e
    else:
        e = (w/aspect - h)/2; y0 -= e; y1 += e
    print(f"  window: x[{x0:.3f},{x1:.3f}] y[{y0:.3f},{y1:.3f}]")
    return (x0, x1), (y0, y1)


def banded_palette(norm):
    """按参考图色系占比的三段式分带 (输入=直方图均衡化后的逃逸秩)"""
    # 段 1: 背景橙红族 57.5%
    seg1_pos = np.array([0.00, 0.30, 0.575])
    seg1_col = np.array([[210, 53, 0], [212, 84, 7], [213, 117, 14]]) / 255.0
    # 段 2: 黄绿树体族 36.5%
    seg2_pos = np.array([0.575, 0.66, 0.80, 0.94])
    seg2_col = np.array([[196, 178, 25], [159, 193, 23], [128, 176, 36],
                         [95, 155, 53]]) / 255.0
    # 段 3: 暗红树脊 6%
    seg3_pos = np.array([0.94, 1.00])
    seg3_col = np.array([[120, 120, 45], [158, 41, 51]]) / 255.0
    pos = np.concatenate([seg1_pos, seg2_pos[1:-1], [seg2_pos[-1]], seg3_pos[1:]])
    cols = np.vstack([seg1_col, seg2_col[1:-1], seg2_col[-1:], seg3_col[1:]])
    # 段间硬过渡软化: 在 0.575 处插入双锚点做快速渐变
    pos_full = [0.0, 0.30, 0.555, 0.595, 0.66, 0.80, 0.93, 0.95, 1.0]
    col_full = np.array([
        [210, 53, 0], [212, 84, 7], [213, 117, 14],     # 橙红族
        [196, 178, 25],                                  # 快速过渡到黄
        [159, 193, 23], [128, 176, 36],                  # 黄绿主体
        [95, 155, 53],                                   # 深绿
        [120, 110, 48],                                  # 过渡
        [158, 41, 51],                                   # 暗红树脊
    ]) / 255.0
    out = np.empty(norm.shape + (3,))
    for ch in range(3):
        out[..., ch] = np.interp(norm, pos_full, col_full[:, ch])
    return out


def main():
    print("=== 1. 参考图分析 ===")
    info = analyze_reference(REF_PATH)
    ref_green = green_fraction(info["arr_small"])
    print(f"  参考图 {info['size'][0]}x{info['size'][1]}, 绿系占比 {ref_green*100:.1f}%")

    print("=== 2. 自动取景 ===")
    xlim, ylim = auto_window(POWER, C, info["aspect"])

    print("=== 3. 渲染 (2x 超采样) ===")
    W_out = info["size"][0]; H_out = info["size"][1]
    ss = 2
    mu, inner = glynn_field(POWER, C, xlim, ylim, W_out*ss, H_out*ss, max_iter=400)

    esc = ~np.isnan(mu)
    norm = np.zeros_like(mu)
    vals = mu[esc]
    ranks = np.argsort(np.argsort(vals)).astype(np.float64)
    norm[esc] = ranks / max(len(vals)-1, 1)
    norm[inner] = 1.0                       # 未逃逸点 -> 树脊色

    rgb = banded_palette(norm)
    rgb_hi = np.clip(rgb, 0, 1)
    Image.fromarray((rgb_hi*255).astype(np.uint8)).save(OUT_HI_PATH)
    rgb_lo = rgb_hi.reshape(H_out, ss, W_out, ss, 3).mean(axis=(1, 3))
    out_img = Image.fromarray((np.clip(rgb_lo, 0, 1)*255).astype(np.uint8))
    out_img.save(OUT_PATH)
    print(f"  已保存: {OUT_PATH.name} ({W_out}x{H_out}) + 高清 {W_out*ss}x{H_out*ss}")

    print("=== 4. 数值验证 ===")
    out_info = analyze_reference(OUT_PATH)
    out_green = green_fraction(out_info["arr_small"])
    print(f"  绿系占比: 输出 {out_green*100:.1f}% vs 参考 {ref_green*100:.1f}%")
    print(f"  中心主色: 输出 {np.round(out_info['interior']*255).astype(int)} "
          f"vs 参考 {np.round(info['interior']*255).astype(int)}")
    dc = np.linalg.norm(out_info["interior"] - info["interior"])
    print(f"  中心主色距离: {dc:.4f} (<0.20 视为同色系)")
    print(f"  背景色: 输出 {np.round(out_info['bg']*255).astype(int)} "
          f"vs 参考 {np.round(info['bg']*255).astype(int)}")
    dsum = wsum = 0.0
    for c_, w_ in zip(info["dom_colors"], info["dom_weights"]):
        if w_ < 0.02:
            continue
        d = min(np.linalg.norm(c_ - oc) for oc in out_info["dom_colors"])
        dsum += d*w_; wsum += w_
    print(f"  加权主色距离: {dsum/wsum:.4f} (<0.15 同风格)")

    print("=== 5. 并排对比图 ===")
    ref_img = Image.open(REF_PATH).convert("RGB")
    gap = 16
    W2 = ref_img.size[0]*2 + gap
    H2 = ref_img.size[1] + 40
    canvas = Image.new("RGB", (W2, H2), (24, 24, 24))
    canvas.paste(ref_img, (0, 40))
    canvas.paste(out_img.resize(ref_img.size), (ref_img.size[0]+gap, 40))
    try:
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("msyh.ttc", 22)
        except Exception:
            font = ImageFont.load_default()
        d.text((10, 8), "参考图 hfgjhgj.webp", fill=(230, 230, 230), font=font)
        d.text((ref_img.size[0]+gap+10, 8), "本次渲染 f(z)=z^1.5-0.2",
               fill=(230, 230, 230), font=font)
    except Exception:
        pass
    canvas.save(CMP_PATH)
    print(f"  对比图: {CMP_PATH.name}")


if __name__ == "__main__":
    main()
