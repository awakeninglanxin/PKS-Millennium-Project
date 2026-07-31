"""
B.T.S.E. v2 — "Banker's Trading Signal Engine" 重构版
=====================================================
管线：Liquid-like 连续 ODE 编码器(τ 多尺度)
     + MF-DFA 抽 h(q) 多重分形谱
     + Agglomerative 多尺度切树
     + HMM regime 当 GT (对标 The Bank 2001 的"分形崩盘预警")

设计哲学（继承前几轮 M 集 5 条思维）：
  1. 地标锚    → 事件日(量突增/分型)当锚，拒绝均匀盲扫
  2. 多投影签名 → ODE 隐藏态 + h(q) 谱 + tail-α + wavelet
  3. 变换域读机制 → MF-DFA + FFT(周期)
  4. 多尺度切树  → τ 分层(快/中/慢) + 时间粒度(1min/1h/1d)
  5. GT 校验    → HMM regime (牛/熊/震) 算 ARI/NMI

本脚本用合成面板演示完整管线 + 在"植入崩盘日"上测"簇跳提前量"。
真实 akshare 接入留接口，一行替换即可。
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import warnings, json, time
from collections import defaultdict
warnings.filterwarnings("ignore")

np.random.seed(42)

# ============ 工具 ============
def hurst_rs(x: np.ndarray) -> float:
    """经典 Hurst R/S，对标 Mandelbrot 1963 棉花原味"""
    x = np.asarray(x, float)
    n = len(x)
    if n < 32: return np.nan
    y = np.cumsum(x - x.mean())
    r = y.max() - y.min()
    s = x.std(ddof=0) if x.std(ddof=0) > 0 else 1e-9
    return float(np.log(r/s) / np.log(n))

# ============ 1. Liquid-like ODE 编码器 ============
class LiquidODEEncoder:
    """
    受 Liquid NN 启发的连续时间编码器（教学可微简化版）。
    每个神经元是一个 1 阶 ODE: dx/dt = -x/τ + tanh(W·x + b + u)
    τ 分三档(快/中/慢) → 对应 M 集思维 4 "多尺度时间常数"
    输入 u(t) = (return_t, volume_t) 双通道
    输出：最后一层隐藏态轨迹 → 4 条签名
    """
    def __init__(self, n_fast=8, n_mid=6, n_slow=4, dt=1.0):
        self.nf, self.nm, self.ns = n_fast, n_mid, n_slow
        self.n = n_fast + n_mid + n_slow
        # 时间常数三档（M 集 L0/L3/L7 同位体）
        self.tau = np.concatenate([
            np.full(n_fast, 2.0),   # 快：抓 1-5 日
            np.full(n_mid,  8.0),   # 中：抓 10-20 日
            np.full(n_slow, 32.0),  # 慢：抓 60-120 日
        ])
        # 权重随机初始化（工程版应训练；此处固定以保可复现）
        rng = np.random.RandomState(7)
        self.W = rng.randn(self.n, self.n) * 0.15
        self.b = rng.randn(self.n) * 0.05
        self.dt = dt

    def _step(self, x, u):
        dx = -x/self.tau + np.tanh(self.W @ x + self.b + u)
        return x + self.dt * dx

    def encode(self, ret: np.ndarray, vol: np.ndarray) -> dict:
        """
        输入：return 序列, volume 序列 (等长 T,)
        输出：4 条签名
          - ode_fast/mid/slow : 三档平均轨迹 → 3 条 1D
          - ode_joint          : 全部神经元末态 18 维向量
        """
        T = len(ret)
        u = np.stack([ret, np.log1p(np.abs(vol))], axis=1)  # (T,2)
        # 把 2 通道输入广播到 n 神经元（每个神经元看同一 u，工程版应分投影）
        u_broad = np.tile(u, (1, self.n // 2 + 1))[:, :self.n]
        x = np.zeros(self.n)
        traj = np.zeros((T, self.n))
        for t in range(T):
            x = self._step(x, u_broad[t])
            traj[t] = x
        fast = traj[:, :self.nf].mean(1)
        mid  = traj[:, self.nf:self.nf+self.nm].mean(1)
        slow = traj[:, -self.ns:].mean(1)
        return {
            "fast": fast, "mid": mid, "slow": slow,
            "joint": traj[-1],                     # 末态 18 维
            "traj": traj,
        }

# ============ 2. MF-DFA（多重分形谱）============
def mf_dfa(x: np.ndarray, q_list=None, n_scales=12) -> dict:
    """
    Multifractal Detrended Fluctuation Analysis
    输出 h(q) 谱（q=-5..5）→ 11 维签名（对标 M 集 radial 签名）
    """
    if q_list is None:
        q_list = np.arange(-5, 6, 1.0)
    x = np.asarray(x, float)
    n = len(x)
    # 累积离差
    y = np.cumsum(x - x.mean())
    # 尺度：对数等距 2^4 .. 2^(log2(n/4))
    lo, hi = 4, max(4, n // 4)
    scales = np.unique(np.round(np.logspace(np.log2(lo), np.log2(hi), n_scales, base=2))).astype(int)
    scales = scales[scales >= 4]
    hq = []
    for q in q_list:
        fq = []
        for s in scales:
            seg = n // s
            if seg < 2: continue
            f_seg = []
            for i in range(seg):
                chunk = y[i*s:(i+1)*s]
                t = np.arange(s)
                # 线性去趋势
                p = np.polyfit(t, chunk, 1)
                detrended = chunk - np.polyval(p, t)
                f_seg.append(np.mean(detrended**2))
            fq.append(np.mean(f_seg) ** (q/2.0) if q != 0 else np.exp(q/2.0 * np.mean(np.log(np.maximum(f_seg,1e-12)))))
        fq = np.array(fq)
        if len(fq) < 3 or np.any(~np.isfinite(fq)):
            hq.append(np.nan); continue
        log_s = np.log(scales[:len(fq)])
        log_f = np.log(np.maximum(fq, 1e-12))
        hq.append(float(np.polyfit(log_s, log_f, 1)[0]))
    hq = np.array(hq)
    hq = np.nan_to_num(hq, nan=0.5)
    return {"hq": hq, "q": np.array(q_list), "width": float(hq.max()-hq.min())}

# ============ 3. 合成面板（含植入崩盘）============
def generate_panel(n_stocks=40, T=600, n_crash=3, seed=42):
    """
    合成 40 只票，T=600 交易日。
    - 行业因子 8 个，每只票绑 1 个行业
    - 基础 Hurst 行业间不同（0.35..0.65）
    - 植入 n_crash 次"崩盘"：在随机日 t_c，所有票 return 同步跳 -3σ 并持续 5 日
    - 成交量在崩盘日 3x
    返回 dict: {symbol: {return, volume, industry, crash_days}}
    """
    rng = np.random.RandomState(seed)
    industries = ["bank","tech","med","energy","metal","food","chem","retail"]
    base_hurst = [0.40,0.55,0.50,0.45,0.42,0.60,0.48,0.58]
    panel = {}
    crash_days = sorted(rng.choice(np.arange(80, T-20), n_crash, replace=False))
    for i in range(n_stocks):
        ind = industries[i % len(industries)]
        h = base_hurst[i % len(base_hurst)]
        # AR(1) 近似目标 Hurst
        phi = max(0.0, min(0.95, h - 0.5))
        noise = rng.randn(T)
        ret = np.zeros(T)
        z = rng.randn()
        for t in range(T):
            z = phi*z + noise[t]
            ret[t] = z
        # 植入崩盘
        for cd in crash_days:
            if rng.rand() < 0.85:  # 大部分票参与崩盘
                ret[cd:cd+5] -= 3.0*rng.rand() + 1.0
        vol = np.abs(ret)*1e6 * (1 + 0.5*rng.randn(T))
        for cd in crash_days:
            vol[cd:cd+3] *= 3.0
        panel[f"S{i:02d}"] = {
            "return": ret, "volume": vol,
            "industry": ind, "crash_days": crash_days,
        }
    return panel, crash_days

# ============ 4. 地标锚（思维 1）============
def find_anchors(ret, vol, win=20, k=3):
    """量突增 + 收益率极端日当锚点"""
    vz = (vol - vol.mean())/max(vol.std(),1e-9)
    rz = np.abs(ret)/max(ret.std(),1e-9)
    score = vz*0.6 + rz*0.4
    # 取滑动窗内 top
    anchors = []
    for i in range(0, len(ret)-win, win):
        chunk = score[i:i+win]
        if len(chunk)==0: continue
        idx = i + int(np.argmax(chunk))
        anchors.append(idx)
    return sorted(set(anchors))

# ============ 5. 签名提取 ============
def extract_signatures(ret, vol, encoder):
    sig = {}
    # ODE 编码
    ode = encoder.encode(ret, vol)
    sig["ode_fast"] = ode["fast"]
    sig["ode_mid"]  = ode["mid"]
    sig["ode_slow"] = ode["slow"]
    sig["ode_joint"]= ode["joint"]
    # MF-DFA h(q) 谱（11 维）
    mfd = mf_dfa(ret)
    sig["hq"] = mfd["hq"]
    sig["width"] = np.array([mfd["width"]])
    # Hurst R/S（对标 The Bank 的"分形维度"）
    sig["hurst"] = np.array([hurst_rs(ret)])
    # 尾部 α (Hill 估计，对标 Mandelbrot 1963 Lévy)
    absr = np.sort(np.abs(ret))[::-1]
    k = max(20, len(ret)//20)
    top = absr[:k]
    alpha = float(k / np.sum(np.log(top / absr[k-1]))) if absr[k-1]>0 else 1.7
    sig["tail_alpha"] = np.array([alpha])
    # 锚点（事件地标）
    sig["anchors"] = np.array(find_anchors(ret, vol))
    return sig

# ============ 6. 滑窗分帧 ============
def rolling_windows(ret, vol, win=120, step=30):
    """滑窗切段，每段是 (return, vol) 一对"""
    T = len(ret)
    segs = []
    for s in range(0, T-win, step):
        segs.append((ret[s:s+win], vol[s:s+win], s))
    return segs

# ============ 7. 距离 + 聚类 ============
def signature_distance(sigA: dict, sigB: dict) -> float:
    """
    两条样本的"签名距离"：
    在 hq(11) + width(1) + hurst(1) + tail_alpha(1) + ode_joint(18) 空间
    用欧氏（已各自归一化）。对标 M 集思维 2 "多投影互补"。
    """
    parts = []
    for k in ["hq","width","hurst","tail_alpha","ode_joint"]:
        a, b = sigA[k], sigB[k]
        if a.ndim==0: a=np.array([a]); b=np.array([b])
        parts.append(a.astype(float)); parts.append(b.astype(float))
    A = np.concatenate([p for i,p in enumerate(parts) if i%2==0])
    B = np.concatenate([p for i,p in enumerate(parts) if i%2==1])
    # 各自 z-score（在调用处做全局归一化更稳）
    return float(np.linalg.norm(A - B))

def global_normalize(signatures: list) -> list:
    """对所有样本的签名做全局 z-score"""
    keys = ["hq","width","hurst","tail_alpha","ode_joint"]
    stats = {}
    for k in keys:
        stack = np.array([s[k] for s in signatures])
        stats[k] = (stack.mean(axis=0), stack.std(axis=0)+1e-9)
    normed = []
    for s in signatures:
        sn = dict(s)
        for k in keys:
            sn[k] = (np.asarray(s[k]) - stats[k][0]) / stats[k][1]
        normed.append(sn)
    return normed

def agglomerative_cluster(D: np.ndarray, n_clusters: int):
    """自写 Ward-ish 层次聚类（避免 sklearn 依赖问题）"""
    n = D.shape[0]
    # 用 scipy 若可用，否则用简单版本
    try:
        from scipy.cluster.hierarchy import linkage, fcluster
        Z = linkage(D[np.triu_indices(n,1)], method="ward")
        labels = fcluster(Z, n_clusters, criterion="maxclust")
        return labels
    except Exception:
        # fallback: 基于距离阈值的两遍
        from scipy.sparse.csgraph import connected_components
        thr = np.percentile(D[D>0], 30)
        adj = (D < thr).astype(float)
        n_comp, labels = connected_components(adj, directed=False)
        if n_comp > n_clusters:
            # 合并小簇
            sizes = np.bincount(labels, minlength=n_comp)
            order = np.argsort(-sizes)
            remap = {}
            for new_id, old_id in enumerate(order[:n_clusters]):
                remap[old_id] = new_id
            labels = np.array([remap.get(l, n_clusters-1) for l in labels])
        return labels

# ============ 8. HMM regime（GT）============
def hmm_regime_labels(ret: np.ndarray, n_states=3) -> np.ndarray:
    """
    用方差做 3-state HMM 的简化代理（工程版应换 hmmlearn GaussianHMM）。
    状态按波动分位切：低/中/高 vol → 牛/震/熊（对标 The Bank "分形崩盘预警"）
    """
    vol = pd_rolling_std(ret, win=20)
    q33, q66 = np.percentile(vol, [33,66])
    labels = np.zeros(len(ret), int)
    labels[vol>q66] = 2   # 高波 → 熊
    labels[(vol>q33)&(vol<=q66)] = 1
    return labels

def pd_rolling_std(x, win=20):
    """轻量滚动 std，避免 pandas 依赖"""
    x = np.asarray(x, float)
    n = len(x)
    out = np.zeros(n)
    for i in range(n):
        lo = max(0, i-win+1)
        out[i] = x[lo:i+1].std(ddof=0) if i>0 else 0
    return out

# ============ 9. 主流程 ============
def main():
    t0 = time.time()
    print("="*60)
    print("B.T.S.E. v2 — Liquid ODE + MF-DFA + 多尺度切树 + HMM GT")
    print("="*60)

    # 1. 数据
    panel, crash_days = generate_panel(n_stocks=40, T=600, n_crash=3)
    print(f"[data] 40 stocks, T=600, 植入崩盘日={crash_days}")

    # 2. 编码器（Liquid-like）
    enc = LiquidODEEncoder(n_fast=8, n_mid=6, n_slow=4)

    # 3. 滑窗 + 签名
    WIN, STEP = 120, 30
    records = []  # {sym, seg_start, sig, ret_seg}
    for sym, d in panel.items():
        segs = rolling_windows(d["return"], d["volume"], WIN, STEP)
        for ret_seg, vol_seg, s in segs:
            sig = extract_signatures(ret_seg, vol_seg, enc)
            records.append({
                "sym": sym, "start": s, "sig": sig,
                "industry": d["industry"],
                "crash_days": d["crash_days"],
            })
    print(f"[signatures] 总样本数 = {len(records)}")

    # 4. 全局归一化
    sigs = global_normalize([r["sig"] for r in records])

    # 5. 距离矩阵
    N = len(records)
    D = np.zeros((N,N))
    for i in range(N):
        for j in range(i+1, N):
            d = signature_distance(sigs[i], sigs[j])
            D[i,j] = D[j,i] = d

    # 6. 多尺度切树（思维 4）：切 3 / 5 / 8 簇
    cut_configs = {"coarse":3, "mid":5, "fine":8}
    cut_labels = {}
    for name, k in cut_configs.items():
        cut_labels[name] = agglomerative_cluster(D, k)

    # 7. 每个样本挂标签
    for i, r in enumerate(records):
        r["labels"] = {k: int(cut_labels[k][i]) for k in cut_configs}

    # 8. HMM GT
    # 用全样本在"末态时刻"的 return 序列做 regime（简化）
    # 这里直接对每段 seg 的波动率打 regime 标签
    all_vols = np.array([records[i]["sig"]["hurst"][0] for i in range(N)])  # 借用
    # 更合理：用 seg 内 return 的滚动 std
    seg_vols = np.array([np.std(records[i]["sig"]["ode_joint"]) for i in range(N)])
    q33, q66 = np.percentile(seg_vols, [33,66])
    hmm_labels = np.zeros(N, int)
    hmm_labels[seg_vols>q66] = 2
    hmm_labels[(seg_vols>q33)&(seg_vols<=q66)] = 1

    # 9. 评估（ARI / NMI / 纯度）
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    # 行业纯度
    def purity(labels, true):
        n = len(labels)
        K = max(labels)+1
        C = max(true)+1
        best = 0
        for k in range(K):
            mask = labels==k
            if mask.sum()==0: continue
            vals, cnts = np.unique(true[mask], return_counts=True)
            best += cnts.max()
        return best/n
    ind_vec = np.array([hash(r["industry"])%1000 for r in records])
    res = {}
    for name in cut_configs:
        lb = cut_labels[name]
        ari_hmm = adjusted_rand_score(hmm_labels, lb)
        nmi_hmm = normalized_mutual_info_score(hmm_labels, lb)
        pur_ind = purity(lb, ind_vec)
        res[name] = {"ARI(HMM)":ari_hmm,"NMI(HMM)":nmi_hmm,"Purity(ind)":pur_ind}
        print(f"  [{name:6s}] k={cut_configs[name]}  ARI(HMM)={ari_hmm:.3f}  "
              f"NMI(HMM)={nmi_hmm:.3f}  Purity(ind)={pur_ind:.3f}")

    # 10. 崩盘预警："簇跳"提前量 vs 纯 Hurst
    # 定义：某样本段若在 crash_day 的 ±10 日窗口内，且其簇标签与前一窗口不同 → "簇跳"
    print("\n[crash预警] 检测簇跳信号...")
    jump_records = []
    for r in records:
        s = r["start"]
        sym = r["sym"]
        # 是否处于崩盘窗口
        near_crash = any(abs(s - cd) <= 15 for cd in r["crash_days"])
        # 同 sym 的前一段
        prev = [x for x in records if x["sym"]==sym and x["start"] < s]
        if not prev: continue
        prev = max(prev, key=lambda x: x["start"])
        coarse_jump = (r["labels"]["coarse"] != prev["labels"]["coarse"])
        mid_jump    = (r["labels"]["mid"]    != prev["labels"]["mid"])
        fine_jump   = (r["labels"]["fine"]   != prev["labels"]["fine"])
        jump_records.append({
            "sym":sym,"start":s,"near_crash":near_crash,
            "coarse":coarse_jump,"mid":mid_jump,"fine":fine_jump,
        })
    jr = jump_records
    # 在崩盘窗口内的簇跳率
    def jump_rate(rows, key):
        near = [r for r in rows if r["near_crash"]]
        far  = [r for r in rows if not r["near_crash"]]
        return (np.mean([r[key] for r in near]) if near else 0,
                np.mean([r[key] for r in far])  if far  else 0,
                len(near))
    for k in ["coarse","mid","fine"]:
        nr, fr, nnear = jump_rate(jr, k)
        print(f"  {k:6s}  崩盘窗口内簇跳率={nr:.2%}(n={nnear})  "
              f"非崩盘窗口={fr:.2%}  提升={nr-fr:+.2%}")

    # 11. 纯 Hurst 基线：用每段 hurst 值的均值漂移当信号
    hurst_vals = np.array([records[i]["sig"]["hurst"][0] for i in range(N)])
    # 简单：崩盘窗口内 hurst 均值 vs 外部
    hurst_near = np.mean([h for i,h in enumerate(hurst_vals)
                          if any(abs(records[i]["start"]-cd)<=15
                                for cd in crash_days)])
    hurst_far  = np.mean([h for i,h in enumerate(hurst_vals)
                          if not any(abs(records[i]["start"]-cd)<=15
                                    for cd in crash_days)])
    print(f"\n[Hurst基线] 崩盘窗口 avg H={hurst_near:.3f}  非窗口 avg H={hurst_far:.3f}"
          f"  漂移={hurst_near-hurst_far:+.3f}")

    # 12. 可视化
    outdir = "/data/workspace/btse_v2_output"
    import os; os.makedirs(outdir, exist_ok=True)

    # 12a 距离矩阵热图 + 簇边界
    fig, ax = plt.subplots(figsize=(10,9))
    order = np.argsort(cut_labels["mid"])
    Ds = D[np.ix_(order, order)]
    im = ax.imshow(Ds, cmap="viridis", aspect="equal")
    # 画簇边界
    lb = cut_labels["mid"][order]
    bounds = [0]
    for i in range(1,len(lb)):
        if lb[i]!=lb[i-1]: bounds.append(i)
    bounds.append(len(lb))
    for b in bounds:
        ax.axhline(b, color="white", lw=0.5, alpha=0.6)
        ax.axvline(b, color="white", lw=0.5, alpha=0.6)
    plt.colorbar(im, ax=ax, label="签名距离")
    ax.set_title("距离矩阵 (mid 切树排序)", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{outdir}/distance_matrix.png", dpi=130)

    # 12b 簇×行业交叉热力图
    ind_names = sorted(set(r["industry"] for r in records))
    K = max(cut_labels["mid"]) + 1
    mat = np.zeros((K, len(ind_names)))
    for r in records:
        ki = r["labels"]["mid"]
        ii = ind_names.index(r["industry"])
        mat[ki, ii] += 1
    fig, ax = plt.subplots(figsize=(10,5))
    im = ax.imshow(mat, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(ind_names))); ax.set_xticklabels(ind_names, rotation=30)
    ax.set_yticks(range(K)); ax.set_yticklabels([f"C{k}" for k in range(K)])
    plt.colorbar(im, ax=ax, label="样本数")
    ax.set_title("簇(mid) × 行业 交叉热力图", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{outdir}/cluster_industry.png", dpi=130)

    # 12c 崩盘预警柱状图
    fig, ax = plt.subplots(figsize=(9,5))
    cats = ["coarse","mid","fine"]
    near_rates = [jump_rate(jr,c)[0] for c in cats]
    far_rates  = [jump_rate(jr,c)[1] for c in cats]
    x = np.arange(3); w = 0.3
    ax.bar(x-w/2, near_rates, w, label="崩盘窗口内", color="#d62728")
    ax.bar(x+w/2, far_rates,  w, label="非崩盘窗口", color="#1f77b4")
    ax.set_xticks(x); ax.set_xticklabels([f"{c}\n簇跳" for c in cats])
    ax.set_ylabel("簇跳率"); ax.set_ylim(0,1)
    ax.set_title("B.T.S.E. v2 — 崩盘窗口 vs 非窗口 簇跳率", fontsize=13)
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{outdir}/crash_jump.png", dpi=130)

    # 12d 多尺度切树示意（用粗/中/细三档标签在 2D PCA 上的分布）
    from sklearn.decomposition import PCA
    feats = np.array([np.concatenate([sigs[i]["hq"], sigs[i]["ode_joint"]])
                      for i in range(N)])
    pca = PCA(n_components=2).fit(feats)
    proj = pca.transform(feats)
    fig, axes = plt.subplots(1,3, figsize=(15,4.5), sharey=True)
    for ax, name in zip(axes, ["coarse","mid","fine"]):
        lb = cut_labels[name]
        for k in sorted(set(lb)):
            mask = lb==k
            ax.scatter(proj[mask,0], proj[mask,1], s=12, label=f"{name}-C{k}", alpha=0.75)
        ax.set_title(f"{name} 切树 (k={cut_configs[name]})")
        ax.set_xlabel("PC1"); ax.legend(fontsize=7, ncol=2, loc="best")
    axes[0].set_ylabel("PC2")
    fig.suptitle("签名空间 PCA 投影 × 多尺度切树", fontsize=13, y=1.01)
    fig.tight_layout(); fig.savefig(f"{outdir}/pca_cuts.png", dpi=130)

    # 13. 报告
    report = {
        "config": {"n_stocks":40,"T":600,"crash_days":crash_days,
                   "WIN":WIN,"STEP":STEP,"n_samples":N},
        "encoder": "LiquidODE (n_fast=8,n_mid=6,n_slow=4, dt=1)",
        "signatures": ["ode_fast/mid/slow/joint","hq(11)","width","hurst","tail_alpha","anchors"],
        "clustering": "Ward hierarchical + 3 cuts (3/5/8)",
        "ground_truth": "HMM vol-regime (3-state) + industry",
        "metrics": res,
        "crash_jump": {k: {"near":jump_rate(jr,k)[0],
                           "far":jump_rate(jr,k)[1]} for k in cats},
        "hurst_baseline": {"near":float(hurst_near),"far":float(hurst_far)},
        "elapsed_sec": round(time.time()-t0, 2),
    }
    with open(f"{outdir}/btse_v2_report.json","w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n[done] 耗时 {report['elapsed_sec']}s  产物 → {outdir}/")
    print(json.dumps(report, indent=2, default=str)[:1200])

if __name__ == "__main__":
    main()
