"""
Mandelbrot Fractal Structure Clustering
========================================
核心思路：
  1. 在多个放大级别(缩放深度)渲染 Mandelbrot 集合
  2. 对每个深度提取"可见区域内的结构特征"——
     将复平面切片编码为一维时间序列(轮廓线/边��密度/周期轨道)
  3. 用 DTW + k-medoids / K-Shape 对结构做聚类
  4. 每多一种封闭结构(新簇)就往 dict 里加一项，统计每个放大级别
     视角内出现的不同类型结构数量

用法：python mandelbrot_fractal_clustering.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score
import json, os, time
from collections import defaultdict, OrderedDict

# ── 全局参数 ──────────────────────────────────────────────
W, H = 480, 480          # 渲染分辨率
MAX_ITER = 350           # 逃逸迭代上限
ZOOM_LEVELS = [          # 多个放大深度，每个 (cx, cy, half_width)
    # (中心x, 中心y, 半宽)  → 半宽越小放大越大
    (-0.5,  0.0,  1.6),    # L0 全局
    (-0.75, 0.1,  0.4),    # L1 M神主体
    (-1.250, 0.38, 0.1),   # L2 左上方小芽苞
    (-0.101, 0.956, 0.05), # L3 顶部旋涡
    (-0.7436, 0.1318, 0.01),  # L4 海马谷
    (-0.749, 0.107, 0.0025),  # L5 更深海马
    (-0.7453, 0.1127, 0.0006),# L6 螺旋芽
    (-0.7436, 0.1318, 0.00015),# L7 超深螺旋
]

OUT_DIR = "/data/workspace/mandelbrot_output"
os.makedirs(OUT_DIR, exist_ok=True)

rng = np.random.default_rng(42)

# ═════════════════════════════════════════════════════════
# 1. Mandelbrot 渲染
# ═════════════════════════════════════════════════════════
def render_mandelbrot(cx, cy, half_w, w=W, h=H, max_iter=MAX_ITER):
    """返回 (w,h) 的逃逸时间矩阵 + 复平面坐标网格"""
    x = np.linspace(cx - half_w, cx + half_w, w)
    y = np.linspace(cy - half_w * h / w, cy + half_w * h / w, h)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.zeros_like(C, dtype=np.complex128)
    escape = np.full(C.shape, max_iter, dtype=np.int32)
    mask = np.full(C.shape, True, dtype=bool)
    for i in range(max_iter):
        Z[mask] = Z[mask]**2 + C[mask]
        escaped = mask & (np.abs(Z) > 2.0)
        escape[escaped] = i
        mask &= ~escaped
        if not mask.any():
            break
    return escape, C

# ═════════════════════════════════════════════════════════
# 2. 结构特征编码 → 一维"时间序列"
# ═════════════════════════════════════════════════════════
def extract_structural_signatures(escape, C, n_rays=128, n_rings=128,
                                   max_iter=MAX_ITER):
    """
    把 2D 分形图像编码成几条 1D 序列(形态签名)：
      a) 径向轮廓 ray_profile   : 从中心向外的逃逸时间均值
      b) 角向轮廓 angular_profile: 沿圆周的逃逸时间
      c) 边界密度 boundary_density: 不同半径上的边界像素数
      d) 周期轨道 period_orbit  : 沿等势线的迭代周期采样
    返回 dict {name: 1D-array}
    """
    sigs = {}
    h, w = escape.shape
    cy_px, cx_px = h // 2, w // 2

    # 像素坐标距图像中心的距离(用于径向/角向采样索引)
    Y, X = np.ogrid[:h, :w]
    R_px = np.sqrt((X - cx_px) ** 2 + (Y - cy_px) ** 2)
    r_max_px = R_px.max()

    # (a) 径向轮廓 —— 用像素距离分箱
    r_bins = np.linspace(0, r_max_px, n_rays + 1)
    radial = np.zeros(n_rays)
    for k in range(n_rays):
        ring_mask = (R_px >= r_bins[k]) & (R_px < r_bins[k + 1])
        vals = escape[ring_mask]
        radial[k] = vals.mean() if vals.size else 0
    sigs['radial'] = radial

    # (b) 角向轮廓 —— 沿 80% 最大像素半径的圆周采样
    theta = np.linspace(0, 2 * np.pi, n_rings, endpoint=False)
    r_sample_px = 0.8 * r_max_px
    ang_vals = np.zeros(n_rings)
    for k, t in enumerate(theta):
        ix = int(cx_px + r_sample_px * np.cos(t))
        iy = int(cy_px + r_sample_px * np.sin(t))
        ix = np.clip(ix, 0, w - 1)
        iy = np.clip(iy, 0, h - 1)
        ang_vals[k] = escape[iy, ix]
    sigs['angular'] = ang_vals

    # (c) 边界密度 —— 用像素距离环带
    bd = np.zeros(16)
    r_lin = np.linspace(r_max_px * 0.1, r_max_px * 0.95, 16)
    for r_idx, r_th in enumerate(r_lin):
        ring_mask = (np.abs(R_px - r_th) < 2.0)
        if ring_mask.sum() == 0:
            continue
        boundary = (escape[ring_mask] < max_iter - 1).sum()
        bd[r_idx] = boundary / max(ring_mask.sum(), 1)
    sigs['boundary_density'] = bd

    # (d) 周期轨道 —— 沿 50% 半径圆周采样
    period = np.zeros(n_rings)
    r_period_px = 0.5 * r_max_px
    for k, t in enumerate(theta):
        ix = int(cx_px + r_period_px * np.cos(t))
        iy = int(cy_px + r_period_px * np.sin(t))
        ix = np.clip(ix, 0, w - 1)
        iy = np.clip(iy, 0, h - 1)
        period[k] = escape[iy, ix]
    sigs['period_orbit'] = period

    return sigs

# ═════════════════════════════════════════════════════════
# 3. DTW 距离
# ═════════════════════════════════════════════════════════
def dtw_distance(a, b):
    """经典 DTW, O(n*m), 带 sqrt 变换让数值稳定"""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n, m = len(a), len(b)
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (a[i - 1] - b[j - 1]) ** 2
            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return np.sqrt(D[n, m])

# ═════════════════════════════════════════════════════════
# 4. k-medoids 聚类(用 DTW 距离)
# ═════════════════════════════════════════════════════════
def kmedoids_dtw(signatures, k, max_iter=50):
    """对一组 1D 序列做 k-medoids, 返回 labels"""
    n = len(signatures)
    # 预计算距离矩阵
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = dtw_distance(signatures[i], signatures[j])
            dist[i, j] = dist[j, i] = d
    # 初始化 medoids
    medoids = rng.choice(n, size=k, replace=False)
    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        # assign
        new_labels = np.argmin(dist[:, medoids], axis=1)
        # update medoids
        new_medoids = medoids.copy()
        for c in range(k):
            members = np.where(new_labels == c)[0]
            if len(members) == 0:
                continue
            intra = dist[np.ix_(members, members)].sum(axis=1)
            new_medoids[c] = members[np.argmin(intra)]
        if np.array_equal(new_medoids, medoids):
            break
        medoids = new_medoids
        labels = new_labels
    return labels, medoids, dist

# ═════════════════════════════════════════════════════════
# 5. 主流程
# ═════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    print("=" * 60)
    print("Mandelbrot Fractal Structure Clustering")
    print("=" * 60)

    # ── 5.1 渲染每个缩放级别 ──────────────────────────────
    renders = []
    for i, (cx, cy, hw) in enumerate(ZOOM_LEVELS):
        esc, C = render_mandelbrot(cx, cy, hw)
        renders.append({
            'level': i, 'cx': cx, 'cy': cy, 'half_w': hw,
            'escape': esc, 'C': C,
            'label': f"L{i} zoom={1/(2*hw):.0f}x"
        })
        print(f"  [L{i}] center=({cx:+.4f},{cy:+.4f})  half_w={hw:.5f}  done")

    # ── 5.2 提取多视角签名 ────────────────────────────────
    # 技巧: 每个级别不只取中心, 还取 4 个偏移子窗口 → 更多样本
    all_signatures = []   # list of dicts
    all_meta = []         # 对应元信息
    sig_names = ['radial', 'angular', 'boundary_density', 'period_orbit']

    for rend in renders:
        esc = rend['escape']
        C = rend['C']
        h, w = esc.shape
        # 中心窗口
        sigs = extract_structural_signatures(esc, C)
        all_signatures.append(sigs)
        all_meta.append({'level': rend['level'], 'label': rend['label'],
                        'sub': 'center', 'cx': rend['cx'], 'cy': rend['cy']})
        # 4 个象限子窗口(缩小视野看局部涡旋)
        for qx, qy, tag in [(0.25, 0.25, 'TL'), (-0.25, 0.25, 'TR'),
                             (-0.25, -0.25, 'BR'), (0.25, -0.25, 'BL')]:
            half = rend['half_w'] * 0.5
            cx0 = rend['cx'] + qx * rend['half_w']
            cy0 = rend['cy'] + qy * rend['half_w']
            esc_sub, C_sub = render_mandelbrot(cx0, cy0, half, w=W // 2, h=H // 2)
            sigs_sub = extract_structural_signatures(esc_sub, C_sub)
            all_signatures.append(sigs_sub)
            all_meta.append({'level': rend['level'], 'label': rend['label'],
                            'sub': tag, 'cx': cx0, 'cy': cy0})

    n_samples = len(all_signatures)
    print(f"\n  总样本数(多缩放×多子窗口): {n_samples}")

    # ── 5.3 对每种签名分别聚类, 再融合 ────────────────────
    # 先单独对 'radial' 签名做聚类(最稳定, 代表整体封闭结构)
    radial_seqs = [s['radial'] for s in all_signatures]
    # 用层次聚类决定 k: 看树状图切断位置
    # 这里用 silhouette 选最优 k
    best_k = 2
    best_sil = -1
    dist_radial = np.zeros((n_samples, n_samples))
    for i in range(n_samples):
        for j in range(i + 1, n_samples):
            d = dtw_distance(radial_seqs[i], radial_seqs[j])
            dist_radial[i, j] = dist_radial[j, i] = d
    for k_try in range(2, min(8, n_samples)):
        labels_try, _, _ = kmedoids_dtw(radial_seqs, k_try)
        if len(set(labels_try)) < 2:
            continue
        sil = silhouette_score(dist_radial, labels_try, metric='precomputed')
        print(f"    k={k_try}  silhouette={sil:.3f}")
        if sil > best_sil:
            best_sil = sil
            best_k = k_try
    print(f"  ✅ 最优簇数 k={best_k} (silhouette={best_sil:.3f})")

    labels_radial, medoids, _ = kmedoids_dtw(radial_seqs, best_k)

    # 同样对 angular 做一遍
    angular_seqs = [s['angular'] for s in all_signatures]
    labels_angular, _, _ = kmedoids_dtw(angular_seqs,
                                         k=min(best_k + 1, 7))

    # ── 5.4 融合双签名标签 → 最终结构类型 ────────────────
    # 组合 (label_radial, label_angular) 作为复合结构 ID
    composite = [f"R{r:02d}_A{a:02d}"
                 for r, a in zip(labels_radial, labels_angular)]
    # 给复合标签编成连续整数
    uniq = OrderedDict()
    for c in composite:
        uniq.setdefault(c, len(uniq))
    final_labels = [uniq[c] for c in composite]
    n_structure_types = len(uniq)
    print(f"  ✅ 复合结构类型数: {n_structure_types}")
    for code, idx in uniq.items():
        print(f"     类型 {idx}: {code}")

    # ── 5.5 统计每个缩放级别的 dict ────────────────────────
    level_stats = defaultdict(dict)
    for meta, fl in zip(all_meta, final_labels):
        lv = meta['level']
        key = f"type_{fl:02d}"
        level_stats[lv].setdefault(key, 0)
        level_stats[lv][key] += 1
    # 补充"该级别共出现几种结构"
    for lv in sorted(level_stats.keys()):
        d = level_stats[lv]
        d['__total_samples__'] = sum(v for k, v in d.items() if not k.startswith('_'))
        d['__n_structure_types__'] = sum(1 for k in d if not k.startswith('_'))
        print(f"  L{lv}: {d}")

    # ── 5.6 可视化 ────────────────────────────────────────
    # (a) 渲染图拼贴
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()
    for i, rend in enumerate(renders[:8]):
        ax = axes[i]
        esc = rend['escape']
        img = np.log1p(esc)
        ax.imshow(img, cmap='hot', extent=[-1, 1, -1, 1])
        ax.set_title(rend['label'], fontsize=10)
        ax.axis('off')
    plt.suptitle("Mandelbrot at Multiple Zoom Levels", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/zoom_grid.png", dpi=130)
    plt.close()

    # (b) 径向签名曲线(按最终标签着色)
    fig, ax = plt.subplots(figsize=(12, 6))
    cmap = cm.get_cmap('tab10', n_structure_types)
    for i, sig in enumerate(radial_seqs):
        ax.plot(sig / sig.max(), color=cmap(final_labels[i]),
                alpha=0.55, lw=1.2)
    ax.set_title("Radial Signatures Colored by Cluster Label")
    ax.set_xlabel("Radial bin"); ax.set_ylabel("Normalized escape time")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/radial_signatures.png", dpi=130)
    plt.close()

    # (c) 角向签名
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, sig in enumerate(angular_seqs):
        ax.plot(sig / max(sig.max(), 1), color=cmap(final_labels[i]),
                alpha=0.55, lw=1.2)
    ax.set_title("Angular Signatures (sampled around 80% radius)")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/angular_signatures.png", dpi=130)
    plt.close()

    # (d) 每级别结构类型数柱状图
    lvs = sorted(level_stats.keys())
    type_counts = [level_stats[lv]['__n_structure_types__'] for lv in lvs]
    sample_counts = [level_stats[lv]['__total_samples__'] for lv in lvs]
    fig, ax1 = plt.subplots(figsize=(10, 5))
    x = np.arange(len(lvs))
    bars = ax1.bar(x, sample_counts, color='#4C9AFF', alpha=0.7,
                   label='samples per level')
    ax1.set_xlabel('Zoom level'); ax1.set_ylabel('Samples', color='#4C9AFF')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"L{lv}" for lv in lvs])
    ax2 = ax1.twinx()
    ax2.plot(x, type_counts, 'o-', color='#FF6B6B', lw=2.5,
             label='structure types')
    ax2.set_ylabel('Distinct structure types', color='#FF6B6B')
    ax1.set_title("Structure-Type Count vs Zoom Level")
    fig.legend(loc='upper left', bbox_to_anchor=(0.12, 0.88))
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/structure_type_vs_zoom.png", dpi=130)
    plt.close()

    # ── 5.7 输出 JSON 统计字典 ────────────────────────────
    result = {
        'n_total_samples': n_samples,
        'n_structure_types': n_structure_types,
        'best_k_radial': best_k,
        'silhouette': round(float(best_sil), 3),
        'composite_code_map': dict(uniq),
        'level_stats': {f"L{k}": v for k, v in level_stats.items()},
        'sample_meta': [
            {'idx': i, **m, 'final_label': int(fl)}
            for i, (m, fl) in enumerate(zip(all_meta, final_labels))
        ]
    }
    with open(f"{OUT_DIR}/fractal_cluster_report.json", 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - t0
    print(f"\n✅ 完成! 耗时 {elapsed:.1f}s")
    print(f"📁 输出目录: {OUT_DIR}/")
    print(f"   - zoom_grid.png             各缩放级别渲染")
    print(f"   - radial_signatures.png     径向签名聚类曲线")
    print(f"   - angular_signatures.png    角向签名聚类曲线")
    print(f"   - structure_type_vs_zoom.png 每级结构类型数统计")
    print(f"   - fractal_cluster_report.json 完整统计字典")

if __name__ == '__main__':
    main()
