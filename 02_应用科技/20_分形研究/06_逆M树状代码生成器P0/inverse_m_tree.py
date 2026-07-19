# -*- coding: utf-8 -*-
"""
逆M树状代码生成器  (Inverse-Julia Tree Generator)
=================================================
对应两篇 PDF 的核心算法:

  [Eq12] 逆 Julia 二值分叉:  z_{n+1} = +/- sqrt(z_n - c)
          -> 每个节点分出 2 个子节点 => 二叉树

  [Eq13] 规模倍增:           M_2 = M_1 * 2^N
          -> 从 M_1 个根出发, 每迭代一层点数翻倍, 深度 N 时共 M_1*2^N 个叶

  [去重 ] McClure pointsSoFar 访问集剪枝:
          -> 已访问过的点不再重复绘制, 使 Julia 边界被均匀覆盖 (modified IIM)

输出:
  1) tree_*.json / tree_*.npz  精确的满二叉树 (节点+父边) = 字面意义的"逆M树状代码"
  2) tree_*.png                小深度树状结构可视化 (画线 parent->child)
  3) iim_*.npz                 大规模逆迭代点云 (GPU CuPy 向量化)
  4) iim_*.png                 高对比 Julia 边界渲染 (吸取上次黑底看不清教训: 亮前景+深底+gamma)
"""
import argparse, json, time, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ============================================================
# Eq12 + Eq13 : 精确满二叉树 (CPU, 结构化)
#   根 = 临界点 z=0  (z^2+c 的临界点 f'(z)=2z=0 => z=0)
#   每层应用 Eq12 的 +/- 两分支; 总节点数随深度按 Eq13 翻倍
# ============================================================
def build_exact_tree(c, depth, root=None, max_nodes=600000):
    c = complex(c)
    t0 = time.time()
    if root is None:
        root = 0.0 + 0.0j                    # 默认 = 临界点 (z^2+c 的临界点 f'(z)=2z=0 => z=0)
    r0 = complex(root)
    re = [r0.real]; im = [r0.imag]; parent = [-1]; dlev = [0]; br = [0]
    frontier = [(0, r0)]                     # (node_id, z)
    for d in range(1, depth + 1):
        nxt = []
        for (pid, z) in frontier:
            w = z - c                         # Eq12: 求逆的被开方式
            sr = np.sqrt(abs(w)); ang = np.angle(w) / 2.0
            p = sr * np.exp(1j * ang)
            for b, zb in ((1, p), (-1, -p)):  # Eq12: +/- 两分支
                nid = len(re)
                re.append(zb.real); im.append(zb.imag)
                parent.append(pid); dlev.append(d); br.append(b)
                nxt.append((nid, zb))
        frontier = nxt                        # Eq13: 下一层节点数 = 上层 *2
        if len(re) > max_nodes:
            print(f"  [tree] 在 depth={d} 达到 max_nodes={max_nodes}, 截断")
            break
    print(f"  [tree] 深度={depth} 节点={len(re)} 用时={time.time()-t0:.2f}s")
    return (np.array(re), np.array(im), np.array(parent),
            np.array(dlev), np.array(br))


# ============================================================
# 树状结构可视化 (画线 parent->child)
# ============================================================
def render_tree_png(re, im, parent, dlev, br, c, out_png, max_depth=12):
    mask = dlev <= max_depth
    idx = np.where(mask)[0]
    fig, ax = plt.subplots(figsize=(11, 11), dpi=140)
    fig.patch.set_facecolor("#06060F")
    ax.set_facecolor("#06060F")
    # 按深度上色 (亮青->品红渐变), 线条半透明
    for d in range(1, max_depth + 1):
        dm = dlev == d
        if not dm.any():
            continue
        ids = np.where(dm)[0]
        xs, ys = [], []
        for i in ids:
            p = parent[i]
            xs += [re[p], re[i], None]; ys += [im[p], im[i], None]
        t = d / max_depth
        col = (0.3 + 0.7 * t, 0.9 - 0.5 * t, 1.0 - 0.3 * t)
        ax.plot(xs, ys, color=col, linewidth=0.5, alpha=0.55)
    ax.set_title(f"Inverse-Julia Tree  (Eq12 +/- branch, Eq13 x2^N)\n"
                 f"c={c}  depth<={max_depth}  nodes={mask.sum()}",
                 color="#CFE", fontsize=12)
    ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    fig.savefig(out_png, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [png ] 树状图 -> {out_png}")


# ============================================================
# Eq12 + Eq13 + 去重 : GPU 向量化逆迭代采样 (IIM) -> 点云 + 渲染
#   每个 walker 独立做 n_steps 次逆迭代; 命中像素 +1;
#   去重: 命中数超 hit_limit 的像素, walker 重置到逃逸半径 (防冷段饿死/重叠)
# ============================================================
def iim_gpu(c, n_points, n_steps, W=2200, H=2200, span=3.2,
            hit_limit=40, burn_in=20, seed=42, out_npz=None, out_png=None):
    import cupy as cp
    c = complex(c)
    cp.random.seed(seed)
    buf = cp.zeros((H, W), dtype=cp.int32)
    half = span / 2.0
    t0 = time.time()

    # 起点: 逃逸半径 R=2 上随机 (Julia 集在 |z|<=2 内)
    ang0 = 2 * np.pi * cp.random.random(n_points)
    z = 2.0 * cp.exp(1j * ang0)
    burn_state = cp.zeros(n_points, dtype=cp.int32)  # >0 时不绘制, 先走 burn-in

    PERIODIC_RESET = 0.005  # 每步 0.5% 随机重投, 避免塌缩
    for s in range(n_steps + burn_in):             # burn_in 步 + 绘制步
        w = z - c                              # Eq12 被开方式
        aw = cp.abs(w)
        w = cp.where(aw < 1e-12, 1e-12 + 0j, w)  # 防 0 除
        sr = cp.sqrt(cp.abs(w)); ang = cp.angle(w) / 2.0
        p = sr * cp.exp(1j * ang)
        branch = cp.random.random(n_points) < 0.5
        z = cp.where(branch, p, -p)            # Eq12: +/- 二选一

        # 只有完成 burn-in 的 walker 才参与绘制 (避免 reset 瞬态伪影)
        plot_mask = burn_state == 0
        re = z.real; ima = z.imag
        valid = (cp.abs(re) < half) & (cp.abs(ima) < half) & plot_mask
        valid_idx = cp.where(valid)[0]           # 全局索引
        pv = re[valid]; iv = ima[valid]
        px = ((iv + half) / span * W).astype(cp.int32)
        py = ((half - pv) / span * H).astype(cp.int32)
        px = cp.clip(px, 0, W - 1); py = cp.clip(py, 0, H - 1)
        cp.add.at(buf, (py, px), 1)              # Eq13: 每层点数倍增地累积

        # 去重: 命中超 hit_limit 的像素 -> 对应 walker 重置到逃逸半径,
        #        并重新进入 burn-in (避免 reset 瞬态被绘制)
        if valid.size > 0:
            hot = buf[py, px] > hit_limit
            if bool(hot.any()):
                hot_global = valid_idx[hot]
                ra = 2 * np.pi * cp.random.random(hot_global.shape[0])
                z[hot_global] = 2.0 * cp.exp(1j * ra)
                burn_state[hot_global] = burn_in

        # 周期性随机重投 + 对应 burn-in
        if cp.random.random() < PERIODIC_RESET:
            rmask = cp.random.random(n_points) < 0.02
            ra2 = 2 * np.pi * cp.random.random(n_points)
            z = cp.where(rmask, 2.0 * cp.exp(1j * ra2), z)
            burn_state = cp.where(rmask, burn_in, burn_state)

        # 推进 burn-in 计数器
        burn_state = cp.where(burn_state > 0, burn_state - 1, burn_state)

        if (s + 1) % 20 == 0 or s == n_steps + burn_in - 1:
            print(f"  [iim ] step {s+1}/{n_steps+burn_in}  max-hit={int(buf.max())}  "
                  f"{time.time()-t0:.1f}s", flush=True)

    buf_np = cp.asnumpy(buf)
    print(f"  [iim ] 完成: 非零像素={int((buf_np>0).sum())} 总命中={int(buf_np.sum())}  "
          f"用时={time.time()-t0:.1f}s")

    if out_npz:
        np.savez_compressed(out_npz, buf=buf_np, c=np.array([c.real, c.imag]),
                            span=np.array([span]), W=np.array([W]), H=np.array([H]))
        print(f"  [npz ] 点云 -> {out_npz}")

    if out_png:
        render_hits_png(buf_np, out_png, title=f"Inverse Julia (IIM)  c={c}\n"
                                                f"{n_points} walkers x {n_steps} steps  [GPU CuPy]")
    return buf_np


# ============================================================
# 高对比渲染 (吸取教训: 亮前景 + 深底 + gamma 提亮暗部)
# ============================================================
def render_hits_png(buf, out_png, title="", bg=(0.02, 0.02, 0.07),
                    hi=(1.0, 0.85, 0.45), lo=(0.20, 0.35, 0.95), gamma=0.45):
    alive = buf > 0
    img = np.zeros((buf.shape[0], buf.shape[1], 3), dtype=np.float64)
    img[:] = bg
    if alive.any():
        v = np.log1p(buf[alive].astype(np.float64))
        vn = np.clip((v - v.min()) / (v.max() - v.min() + 1e-12), 0, 1)
        vn = vn ** gamma                       # 提亮暗部
        for ch in range(3):
            img[alive, ch] = lo[ch] + vn * (hi[ch] - lo[ch])
    fig, ax = plt.subplots(figsize=(11, 11), dpi=130)
    fig.patch.set_facecolor("#06060F")
    ax.imshow(np.rot90(img, k=1), extent=[-1.6, 1.6, -1.6, 1.6])
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, color="#CFE", fontsize=12, pad=8)
    plt.tight_layout()
    fig.savefig(out_png, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [png ] 渲染 -> {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", default="-0.74543+0.11301j", help="Julia 参数 c (复数)")
    ap.add_argument("--depth", type=int, default=16, help="精确树深度 (Eq13 叶数=2^depth)")
    ap.add_argument("--gpu", action="store_true", help="启用 CuPy GPU 采样")
    ap.add_argument("--npoints", type=int, default=4_000_000, help="IIM walker 数")
    ap.add_argument("--nsteps", type=int, default=120, help="每 walker 逆迭代步数")
    ap.add_argument("--outdir", default="/root/inverse_m_work", help="输出目录")
    ap.add_argument("--root", default=None,
                    help="树根 (复数, 默认=临界点0). c=0 时临界点是不动点会塌缩, 自动改取 Julia 集锚点")
    args = ap.parse_args()

    c = complex(args.c)
    os.makedirs(args.outdir, exist_ok=True)
    tag = f"c{c.real:.4f}_{c.imag:+.4f}".replace(".", "p").replace("+", "p").replace("-", "m")
    print(f"\n=== 逆M树状代码生成器 | c={c} ===")

    # 1) 精确满二叉树
    re, im, parent, dlev, br = build_exact_tree(c, args.depth, root=args.root)
    # 退化检测: c=0 时临界点 z=0 是超吸引不动点, 逆迭代全塌缩到原点
    #   -> 改用 Julia 集上的点 (单位圆取 z=1) 作根, 重新生成真正的单位圆树
    spread = np.hypot(np.array(re) - re[0], np.array(im) - im[0]).max()
    if spread < 1e-9:
        print(f"  [tree] 检测到塌缩 (c={c} 临界点为不动点), 改用 Julia 集锚点 z=1 重新生成")
        re, im, parent, dlev, br = build_exact_tree(c, args.depth, root=1.0 + 0.0j)
    json_path = os.path.join(args.outdir, f"tree_{tag}.json")
    npz_path = os.path.join(args.outdir, f"tree_{tag}.npz")
    # NPZ 紧凑存储 (大规模友好)
    np.savez_compressed(npz_path, re=re, im=im, parent=parent, dlev=dlev, br=br,
                        c=np.array([c.real, c.imag]), depth=np.array([args.depth]))
    # JSON 仅存小深度 (可读, 供前端/人工检查)
    small = dlev <= 12
    si = np.where(small)[0]
    nodes = [{"id": int(i), "parent": int(parent[i]), "depth": int(dlev[i]),
              "re": round(float(re[i]), 6), "im": round(float(im[i]), 6),
              "branch": int(br[i])} for i in si]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"c": [c.real, c.imag], "depth_max": int(dlev.max()),
                   "node_count": int(len(re)), "nodes": nodes}, f, ensure_ascii=False)
    print(f"  [json] 树(深度<=12, {len(nodes)}节点) -> {json_path}")
    print(f"  [npz ] 树(全 {len(re)}节点) -> {npz_path}")

    # 2) 树状结构图
    tree_png = os.path.join(args.outdir, f"tree_{tag}.png")
    render_tree_png(re, im, parent, dlev, br, c, tree_png, max_depth=12)

    # 3) GPU 逆迭代采样
    if args.gpu:
        try:
            import cupy  # noqa
            iim_npz = os.path.join(args.outdir, f"iim_{tag}.npz")
            iim_png = os.path.join(args.outdir, f"iim_{tag}.png")
            iim_gpu(c, args.npoints, args.nsteps, out_npz=iim_npz, out_png=iim_png)
        except Exception as e:
            print(f"  [gpu ] CuPy 不可用, 跳过: {e}")
    else:
        print("  [skip] 未加 --gpu, 跳过 IIM 采样")
    print("=== 完成 ===")


if __name__ == "__main__":
    main()
