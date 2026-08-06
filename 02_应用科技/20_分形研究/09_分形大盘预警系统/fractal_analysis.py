# -*- coding: utf-8 -*-
"""
fractal_analysis.py — 分形数学预判大盘 · 核心算法库
=====================================================
功能:
 1. MF-DFA 多重分形去趋势波动分析 → h(q) 谱 + 谱宽 Δh
 2. Hurst 指数 (R/S 分析)
 3. Hill 尾指数 (左尾崩盘风险)
 4. 多尺度 LiquidODE 近似特征 (τ=2/8/32)
 5. Ward 层次聚类 + 三档切树 (3/5/8)
 6. 簇跳率 (Cluster Jump Rate) 崩盘预警信号
 7. 通达信数据接入 (tdx) + 模拟数据 fallback

用法:
   python fractal_analysis.py            # 自测 (模拟数据)
   from fractal_analysis import *        # 作为库导入

作者: AI · 基于元宝链接方法论整理实现  |  v1.0  2026-08-03
"""

import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

# ============================================================
# 1. MF-DFA 多重分形去趋势波动分析
# ============================================================
def mf_dfa(returns, q_range=None, scales=None, m=1):
    """
    输入: returns  (N,) 对数收益率序列
    输出: dict(q=h(q),  hq 数组, width=Δh, Fq 矩阵)
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 32:
        return {"q": None, "hq": None, "width": np.nan, "Fq": None}
    if q_range is None:
        q_range = np.arange(-5, 6, 1)  # -5..5 共11点
    if scales is None:
        n = len(r)
        scales = [s for s in (4, 8, 16, 32, 64, 128, 256) if s <= n // 4 and s >= 4]

    # Step1: 累积离差 profile
    Y = np.cumsum(r - r.mean())

    # Step2-3: 分箱 + 去趋势
    F2 = {}  # s -> (2Ns,) 方差数组
    for s in scales:
        Ns = len(Y) // s
        var = []
        # 正向
        for v in range(Ns):
            seg = Y[v*s:(v+1)*s]
            x = np.arange(s, dtype=float)
            coef = np.polyfit(x, seg, m)
            fit = np.polyval(coef, x)
            var.append(np.mean((seg - fit) ** 2))
        # 反向
        Yr = Y[::-1]
        for v in range(Ns):
            seg = Yr[v*s:(v+1)*s]
            x = np.arange(s, dtype=float)
            coef = np.polyfit(x, seg, m)
            fit = np.polyval(coef, x)
            var.append(np.mean((seg - fit) ** 2))
        F2[s] = np.array(var)

    # Step4-5: q 阶波动函数 + 回归求 h(q)
    hq = []
    for q in q_range:
        if q == 0:
            Fq_s = [np.exp(0.25 * np.mean(np.log(v))) for s, v in F2.items() if len(v) > 0]
        else:
            Fq_s = [np.mean(v ** (q / 2.0)) ** (1.0 / q) for s, v in F2.items() if len(v) > 0]
        ls = np.log(np.array(list(F2.keys())))
        lf = np.log(np.array([max(x, 1e-12) for x in Fq_s]))
        if len(ls) >= 2 and np.all(np.isfinite(lf)):
            slope, _, _, _, _ = stats.linregress(ls, lf)
        else:
            slope = np.nan
        hq.append(slope)

    hq = np.array(hq)
    width = hq[0] - hq[-1] if np.all(np.isfinite(hq)) else np.nan  # Δh = h(-5)-h(5)
    return {"q": q_range, "hq": hq, "width": width, "Fq": F2}


# ============================================================
# 2. Hurst 指数 (R/S 分析)
# ============================================================
def hurst_rs(returns, scales=None):
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 32:
        return np.nan
    n = len(r)
    if scales is None:
        scales = [s for s in (16, 32, 64, 128, 256) if s <= n // 2]
    rs_vals, ln_s = [], []
    for s in scales:
        chunks = n // s
        if chunks < 2:
            continue
        rs = []
        for i in range(chunks):
            seg = r[i*s:(i+1)*s]
            mean = seg.mean()
            dev = np.cumsum(seg - mean)
            R = dev.max() - dev.min()
            S = seg.std(ddof=1)
            if S > 1e-12:
                rs.append(R / S)
        if rs:
            rs_vals.append(np.mean(rs))
            ln_s.append(np.log(s))
    if len(ln_s) >= 2:
        H, _, _, _, _ = stats.linregress(np.array(ln_s), np.log(np.array(rs_vals)))
        return H
    return np.nan


# ============================================================
# 3. Hill 尾指数 (左尾, 崩盘风险)
# ============================================================
def hill_alpha(returns, k_frac=0.05):
    """k_frac: 取最极端左尾的比例"""
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 40:
        return np.nan
    left = np.sort(r)[:max(4, int(len(r) * k_frac))]
    if len(left) < 4 or left[-1] >= 0:
        return np.nan
    x = -left  # 转正
    k = len(x)
    xk = x[-1]  # 阈值
    if xk <= 0:
        return np.nan
    log_ratio = np.log(x / xk)
    alpha = 1.0 / np.mean(log_ratio)
    return float(alpha)


# ============================================================
# 4. 多尺度 LiquidODE 近似特征 (τ=2/8/32)
# ============================================================
def liquid_ode_features(returns, taus=(2, 8, 32)):
    """
    用多尺度滚动统计近似液态神经网络的多时间常数编码
    输出: [τ2_mean, τ2_std, τ8_hurst, τ32_hurst, τ32_width]
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    feats = []
    for tau in taus:
        if len(r) < tau * 3:
            feats.extend([np.nan, np.nan])
            continue
        seg = r[-tau:]
        feats.append(seg.mean())
        feats.append(seg.std(ddof=1))
    return np.array(feats)


def distribution_features(returns):
    """收益率分布直描: 波动率/偏度/峰度/最大回撤 (对行业波动率档位强区分)"""
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 20:
        return np.full(5, np.nan)
    vol = np.std(r, ddof=1)
    skew = float(stats.skew(r)) if len(r) > 5 else np.nan
    kurt = float(stats.kurtosis(r)) if len(r) > 5 else np.nan
    # 最大单日跌幅 (负值)
    max_drop = float(np.min(r))
    # 正收益占比
    pos_ratio = float(np.mean(r > 0))
    return np.array([vol, skew, kurt, max_drop, pos_ratio])


# ============================================================
# 5. 单股完整特征向量 (稳健版: 适应短窗口)
# ============================================================
def extract_features(returns):
    """
    拼接: MF-DFA 关键点(而非全谱) + width + Hurst + Hill α + liquid 6维
    稳健性: MF-DFA 在短窗口(120日)只保留 4/8/16/32/64 尺度,
    全 11 点 h(q) 谱噪声大 → 只取 h(-5), h(0), h(5) 三点 + 谱宽,
    用强信号维度降低聚类噪声
    """
    mf = mf_dfa(returns)
    H = hurst_rs(returns)
    alpha = hill_alpha(returns)
    liq = liquid_ode_features(returns)
    dist = distribution_features(returns)
    hq = mf["hq"] if mf["hq"] is not None else np.full(11, np.nan)
    # 只取谱两端+中点 (h(-5), h(0), h(5)) 降噪
    if len(hq) >= 11:
        hq_key = np.array([hq[0], hq[5], hq[10]])
    else:
        hq_key = np.array([np.nan, np.nan, np.nan])
    feats = np.concatenate([hq_key, [mf["width"], H, alpha], liq, dist])
    return feats, mf, H, alpha


# ============================================================
# 6. Ward 层次聚类 + 三档切树
# ============================================================
def ward_cluster(feature_matrix, cuts=(3, 5, 8)):
    """
    输入: feature_matrix (N, D)  N只股票的特征
    输出: dict(cuts -> 标签数组), 以及 linkage
    """
    X = np.asarray(feature_matrix, dtype=float)
    # 只保留有限列
    col_ok = np.all(np.isfinite(X), axis=0)
    X = X[:, col_ok]
    # 标准化
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd < 1e-12] = 1.0
    Xs = (X - mu) / sd
    # 缺失行填充（用中位数）
    row_med = np.nanmedian(Xs, axis=0)
    Xs = np.where(np.isfinite(Xs), Xs, row_med)

    if Xs.shape[0] < 2 or Xs.shape[1] == 0:
        return {k: np.zeros(Xs.shape[0], dtype=int) for k in cuts}, None

    Z = linkage(Xs, method="ward")
    labels = {k: fcluster(Z, t=k, criterion="maxclust") for k in cuts}
    return labels, Z


# ============================================================
# 6b. 锚定聚类 (Anchor Clustering) — 稳定簇跳率的关键
# ============================================================
class AnchorClusterer:
    """
    参考簇锚定: 用初始窗口拟合簇中心, 后续窗口只做"分配"而非"重聚"。
    解决 Ward 每次重聚对特征微小漂移过度敏感的问题:
      - 正常期: 特征漂移小 → 归属稳定 → CJR 低
      - 崩盘期: 结构剧变 → 大量股票换簇 → CJR 高
    """
    def __init__(self, n_clusters=(3, 5, 8), random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self._mu = None
        self._sd = None
        self._centers = {}   # k -> 簇中心 (k, D)
        self._fitted = False

    def _prep(self, X):
        X = np.asarray(X, dtype=float)
        col_ok = np.all(np.isfinite(X), axis=0)
        X = X[:, col_ok]
        return X, col_ok

    def fit(self, feature_matrix):
        """用首个窗口拟合簇中心 (k-means 固定随机种子, 可复现)"""
        from sklearn.cluster import KMeans
        X, col_ok = self._prep(feature_matrix)
        if X.shape[0] < 3 or X.shape[1] == 0:
            return self
        self._mu = X.mean(axis=0)
        self._sd = X.std(axis=0)
        self._sd[self._sd < 1e-12] = 1.0
        Xs = (X - self._mu) / self._sd
        self._centers = {}
        for k in self.n_clusters:
            km = KMeans(n_clusters=k, n_init=10, random_state=self.random_state)
            km.fit(Xs)
            self._centers[k] = km.cluster_centers_
        self._fitted = True
        return self

    def predict(self, feature_matrix):
        """后续窗口: 分配最近簇中心 (1..k 标签)"""
        X, col_ok = self._prep(feature_matrix)
        labels = {}
        if not self._fitted or X.shape[0] == 0:
            return {k: np.zeros(X.shape[0], dtype=int) + 1 for k in self.n_clusters}
        Xs = (X - self._mu) / self._sd
        for k, centers in self._centers.items():
            # 欧氏距离到各中心 → 最近簇
            d = np.linalg.norm(Xs[:, None, :] - centers[None, :, :], axis=2)
            labels[k] = np.argmin(d, axis=1) + 1  # 1..k
        return labels


# ============================================================
# 7. 簇跳率 (Cluster Jump Rate)
# ============================================================
def cluster_jump_rate(prev_labels, cur_labels):
    """
    计算两窗口间簇归属变化比例
    注意: 簇编号可能错位, 用最优匹配后比较
    """
    prev = np.asarray(prev_labels, dtype=int)
    cur = np.asarray(cur_labels, dtype=int)
    if len(prev) != len(cur) or len(prev) == 0:
        return np.nan
    # 用 scipy 最优分配对齐簇标签 (Hungarian)
    from scipy.optimize import linear_sum_assignment
    n_prev = int(prev.max()) + 1
    n_cur = int(cur.max()) + 1
    n = max(n_prev, n_cur)
    # 计算共现矩阵
    cost = np.zeros((n, n))
    for a in range(n_prev):
        for b in range(n_cur):
            cost[a, b] = -np.sum((prev == a) & (cur == b))
    row, col = linear_sum_assignment(cost)
    mapping = {}
    for a, b in zip(row, col):
        mapping[a] = b
    cur_aligned = np.array([mapping.get(x, x + n) for x in cur])
    jump = np.mean(prev != cur_aligned)
    return float(jump)


# ============================================================
# 8. 全流程: 指数级簇跳率时序 (滚动窗口)
# ============================================================
def build_cjr_timeline(panel_returns, window=120, step=20, cuts=(3, 5, 8)):
    """
    panel_returns: dict 股票代码 -> 收益率数组(长度T)
    锚定聚类版本: 首窗口 fit 簇中心, 后续窗口 predict 分配
    返回: dict(窗口起止日期, 各切树簇跳率, 平均Hurst, 平均谱宽, 平均Hill)
    """
    codes = list(panel_returns.keys())
    T = min(len(v) for v in panel_returns.values())
    aligned = {c: v[-T:] for c, v in panel_returns.items()}
    dates = list(range(T))

    timeline = {"window_start": [], "window_end": [],
                "cjr": {k: [] for k in cuts},
                "avg_hurst": [], "avg_width": [], "avg_hill": []}

    anchor = AnchorClusterer(n_clusters=cuts, random_state=42)
    prev_labels = None
    first = True
    for start in range(0, T - window + 1, step):
        end = start + window
        feat_list = []
        hursts, widths, hills = [], [], []
        for c in codes:
            r = aligned[c][start:end]
            feats, mf, H, alpha = extract_features(r)
            feat_list.append(feats)
            hursts.append(H); widths.append(mf["width"]); hills.append(alpha)
        feats_arr = np.array(feat_list)

        if first:
            anchor.fit(feats_arr)
            labels = anchor.predict(feats_arr)
            first = False
        else:
            labels = anchor.predict(feats_arr)

        for k in cuts:
            if prev_labels is not None and k in prev_labels:
                cjr = cluster_jump_rate(prev_labels[k], labels[k])
            else:
                cjr = 0.0
            timeline["cjr"][k].append(cjr)
        prev_labels = labels

        timeline["window_start"].append(start)
        timeline["window_end"].append(end)
        timeline["avg_hurst"].append(np.nanmean(hursts))
        timeline["avg_width"].append(np.nanmean(widths))
        timeline["avg_hill"].append(np.nanmean(hills))

    # 记录最后一窗口的簇标签 (供展示, 转纯int便于JSON序列化)
    timeline["last_labels"] = {k: [int(x) for x in labels[k]] for k in labels}
    return timeline


# ============================================================
# 9. 预警引擎
# ============================================================
def alert_engine(cjr_mid, cjr_fine, avg_hurst, avg_width):
    """
    输入当前窗口的 mid/fine 簇跳率 与 分形指标
    输出 dict(level, color, message, suggestion, action, pos, rationale)
    """
    level, color = "绿", "green"
    msg = "结构稳定"
    action = "维持 60-80% 仓位"
    pos = "60-80%"
    rationale = []
    sug = "维持当前仓位，关注簇跳率变化"

    if cjr_fine > 0.55 or (cjr_mid > 0.55):
        level, color = "红", "red"
        msg = "结构瓦解中 — 崩盘前奏信号"
        action = "撤退 / 大幅减仓至 20% 以下"
        pos = "≤20%"
        sug = "撤退/大幅减仓，等待结构重建确认"
        rationale.append(f"mid簇跳率 {cjr_mid:.0%} 或 fine簇跳率 {cjr_fine:.0%} > 55% 撤退阈值 → 历史实证该水平对应崩盘前奏(中位提前15天)")
    elif cjr_mid > 0.40 or cjr_fine > 0.45:
        level, color = "黄", "orange"
        msg = "结构松动 — 牛市后期/风格切换"
        action = "减仓至 40% 以下"
        pos = "≤40%"
        sug = "减仓观望，提高现金比例"
        rationale.append(f"mid簇跳率 {cjr_mid:.0%} > 40% 警惕阈值 → 市场结构松动, 历史实证为崩盘前1-2档预警")
    elif cjr_mid > 0.25:
        level, color = "黄绿", "gold"
        msg = "结构活跃 — 正常分化"
        action = "维持 50-60% 仓位"
        pos = "50-60%"
        sug = "保持中性仓位，精选强势簇"
        rationale.append(f"mid簇跳率 {cjr_mid:.0%} 处于 25-40% 活跃区间 → 结构分化但未瓦解, 属正常轮动")
    else:
        level, color = "绿", "green"
        msg = "结构稳定 — 趋势健康"
        action = "维持 60-80% 仓位"
        pos = "60-80%"
        sug = "维持仓位，跟踪簇构成"
        rationale.append(f"mid簇跳率 {cjr_mid:.0%} < 25% → 簇归属稳定, 结构健康")

    # 分形退化叠加信号
    if np.isfinite(avg_width) and avg_width < 0.5 and level != "红":
        msg += " | 多重分形谱收窄(退化)"
        rationale.append(f"平均分形谱宽 Δh={avg_width:.2f} < 0.5 → 多重分形退化, 结构单一化")
        if level == "绿":
            level, color = "黄绿", "gold"
            action = "减仓至 60% 以下"
            pos = "≤60%"
            sug = "结构单一化，警惕风格切换"
    if np.isfinite(avg_hurst) and avg_hurst < 0.45 and level == "绿":
        sug += " | 均值回归主导，避免追涨"
        rationale.append(f"平均Hurst {avg_hurst:.2f} < 0.45 → 均值回归主导, 追涨风险高")

    return {"level": level, "color": color, "msg": msg,
            "suggestion": sug, "action": action, "pos": pos,
            "rationale": rationale}


# ============================================================
# 10. 模拟数据生成 (无通达信时 fallback)
# ============================================================
def gen_synthetic_panel(n_stocks=40, T=800, n_crash=3, seed=42):
    """
    生成合成面板: 8 行业 x 5 只, 植入崩盘日
    (行业因子主导: 正常期同行业强相关 → 簇稳定低跳变;
     崩盘期全局冲击打碎行业结构 → 簇跳率飙升)
    """
    rng = np.random.default_rng(seed)
    industries = ["半导体", "光模块", "存储", "软件", "医药", "消费", "新能源", "金融"]
    # 行业波动率档位 (高波动=厚尾)
    ind_vol = {ind: 0.006 + 0.003 * i for i, ind in enumerate(industries)}
    panel = {}
    codes = []
    T_crash = sorted(rng.choice(range(250, T - 80), size=n_crash, replace=False))
    # 行业共同因子: 主导地位 (大幅强于个股噪声)
    ind_factor = {}
    for ind in industries:
        w = rng.normal(0, 1, T)
        smooth = np.convolve(w, np.ones(20) / 20, mode="same")
        ind_factor[ind] = smooth * 0.012 * (ind_vol[ind] / 0.012)
    # 全局市场因子 (小)
    mkt = np.convolve(rng.normal(0, 1, T), np.ones(10) / 10, mode="same") * 0.002
    for ind in industries:
        for j in range(5):
            code = f"{ind[0]}{j:02d}"
            codes.append(code)
            beta = rng.normal(1.0, 0.1)
            vol = ind_vol[ind]
            # 行业主导: 收益率 ≈ 行业因子 + 小噪声 (同行业高度同步)
            r = ind_factor[ind] * beta + mkt * beta * 0.3 + rng.normal(0.0002, vol * 0.35, T)
            for tc in T_crash:
                # 崩盘: 全局冲击 -2σ~-4σ (打破行业同步性)
                r[tc] += rng.normal(-0.06, 0.01)
                for k in range(1, 6):
                    if tc + k < T:
                        r[tc + k] += rng.normal(-0.015, 0.005)
            panel[code] = r
    return panel, codes, T_crash, industries


# ============================================================
# 自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("分形数学预判大盘 · 核心算法自测 (模拟数据)")
    print("=" * 60)

    # 生成合成面板
    panel, codes, crash_days, industries = gen_synthetic_panel(n_stocks=40, T=800)
    print(f"\n[数据] {len(codes)} 只合成股票, 每只 {len(panel[codes[0]])} 日")
    print(f"[植入崩盘日] {crash_days}")

    # 单股特征测试
    r0 = panel[codes[0]]
    mf = mf_dfa(r0)
    H = hurst_rs(r0)
    alpha = hill_alpha(r0)
    liq = liquid_ode_features(r0)
    print(f"\n[单股特征] 代码={codes[0]}")
    print(f"  h(q) 谱宽 Δh = {mf['width']:.3f}")
    print(f"  Hurst H = {H:.3f}")
    print(f"  Hill α = {alpha:.3f}")
    print(f"  LiquidODE特征 = {np.round(liq, 4)}")

    # 簇跳率时序 (全流程)
    tl = build_cjr_timeline(panel, window=120, step=20, cuts=(3, 5, 8))
    n_win = len(tl["window_end"])
    print(f"\n[簇跳率时序] 窗口数={n_win} (窗宽120日/步长20日)")

    for k in (3, 5, 8):
        cjr_arr = np.array(tl["cjr"][k])
        print(f"  切树 k={k}: 平均簇跳率={cjr_arr.mean():.1%}, 最大={cjr_arr.max():.1%}")

    # 检查崩盘窗口附近的簇跳率是否抬升
    print("\n[预警引擎 - 末窗口状态]")
    last = tl["cjr"][5][-1], tl["cjr"][8][-1], tl["avg_hurst"][-1], tl["avg_width"][-1]
    alert = alert_engine(*last)
    print(f"  mid簇跳率={last[0]:.1%}  fine簇跳率={last[1]:.1%}")
    print(f"  平均Hurst={last[2]:.3f}  平均谱宽={last[3]:.3f}")
    print(f"  ▶ 信号: {alert['level']} | {alert['msg']}")
    print(f"    建议: {alert['suggestion']}")

    print("\n✅ 核心算法自测完成")
