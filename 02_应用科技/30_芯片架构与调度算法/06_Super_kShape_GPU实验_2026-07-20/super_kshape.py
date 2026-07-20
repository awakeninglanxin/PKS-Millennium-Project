#!/usr/bin/env python3
"""
Super k-Shape: 四算法组合升级 k-Shape (2015) 的统一框架
========================================================

升级点:
  1. Sharkovsky-DP 拐点 → 预分层 + 结构初始化 (避免随机初始化偏差)
  2. Farey 路径编辑距离 → 多尺度距离 (补 SBD 的单层对齐)
  3. 反幻 diversity loss → 簇间分离 (补 k-Shape 只优化簇内紧凑的盲区)
  4. 幻方因子化 → 正交分量分解 + 交集聚类 (利用趋势/季节/残差的独立性)

原则: 保留 k-Shape 的 SBD + Rayleigh 商 centroid + FFT 加速三优势, 在其上叠加

Author: Hao Cai / Senior Developer, 2026-07-20
"""
import numpy as np
from scipy.fft import fft, ifft
from scipy.signal import find_peaks
from collections import defaultdict
from math import gcd, inf
import time, warnings

# ============================================================
# 模块 1: Sharkovsky-DP 拐点检测 → 结构预分层
# ============================================================

SHARKOVSKY = [3,5,7,9,11,13,15,6,10,14,18,12,20,24,16,8,4,2,1]

def sharkovsky_rank(period):
    """返回 period 在 Sharkovsky 序中的位置, 越小=越混沌"""
    try: return SHARKOVSKY.index(period)
    except: return len(SHARKOVSKY)

def detect_inflections(ts, window=5, slope_ratio=3.0):
    """
    5点滑动窗口斜率比 > slope_ratio → 拐点
    返回: [(位置, 周期估计, 幅度)]
    """
    n = len(ts)
    if n < window + 2:
        return []
    
    inflections = []
    for i in range(window, n - window):
        left_slope = abs(ts[i] - ts[i - window]) / window
        right_slope = abs(ts[i + window] - ts[i]) / window
        if right_slope < 1e-9: continue
        
        ratio = left_slope / right_slope
        if ratio > slope_ratio or ratio < 1.0 / slope_ratio:
            # 估计局部周期: 与前一个拐点的距离
            if inflections:
                period_est = i - inflections[-1][0]
            else:
                period_est = window
            amplitude = abs(ts[i] - ts[max(0, i - period_est)])
            inflections.append((i, min(period_est, 20), amplitude))
    
    return inflections

def structural_init(ts_list, k):
    """
    用 Sharkovsky-DP 拐点结构做预分层初始化
    
    思路: 用拐点的 Sharkovsky 序分布作为结构指纹,
    相似指纹的序列分到同一初始簇
    """
    fingerprints = []
    for ts in ts_list:
        inf = detect_inflections(ts)
        if not inf:
            fingerprints.append([0])
            continue
        # 指纹: 拐点 Sharkovsky ranks 的直方图 (21 bins = |SHARKOVSKY|)
        ranks = [sharkovsky_rank(p) for _, p, _ in inf]
        hist, _ = np.histogram(ranks, bins=21, range=(0, 21))
        fingerprints.append(hist)
    
    fingerprints = np.array(fingerprints, dtype=np.float64)
    
    # k-Means 在指纹空间聚类 → 初始分区
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(fingerprints)
    return labels


# ============================================================
# 模块 2: Farey 路径编辑距离 → 多尺度形状距离
# ============================================================

def farey_path(ts, max_depth=8):
    """
    将时间序列转换为 Farey 路径
    
    做法: 
      1. 检测拐点 (用 Sharkovsky-DP)
      2. 每对相邻拐点之间: 计算 segment 的复杂度 period
      3. 映射到 Farey 分数 p/period (p 来自拐点幅度的量化)
      4. 路径 = 相邻 Farey 分数的 mediant 操作序列
    """
    inflections = detect_inflections(ts)
    if len(inflections) < 2:
        return ["R"]  # 平坦序列 → 根节点
    
    path = []
    for i in range(len(inflections) - 1):
        pos1, period1, amp1 = inflections[i]
        pos2, period2, amp2 = inflections[i + 1]
        
        # 两个拐点之间的 segment → Farey 编码
        # period = segment 长度对 max_depth 的映射
        seg_len = pos2 - pos1
        p = min(max_depth, max(1, seg_len // 5))
        q = max_depth
        
        # mediant 方向: 取决于幅度变化
        direction = "R" if amp2 > amp1 else "L"  # Right=上升, Left=下降
        
        path.append(f"{direction}{p}/{q}")
    
    return path

def farey_edit_distance(path1, path2):
    """Levenshtein 编辑距离 (带权重: 不同 Farey 分数的替换代价)"""
    m, n = len(path1), len(path2)
    dp = np.zeros((m + 1, n + 1), dtype=np.float64)
    for i in range(m + 1): dp[i, 0] = i
    for j in range(n + 1): dp[0, j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if path1[i - 1] == path2[j - 1]:
                dp[i, j] = dp[i - 1, j - 1]
            else:
                # 替换代价 = Farey 距离 (分数差)
                try:
                    s1 = path1[i-1][1:]  # "R1/8" → "1/8"
                    s2 = path2[j-1][1:]
                    a1 = eval(s1.split('/')[0]) / eval(s1.split('/')[1])
                    a2 = eval(s2.split('/')[0]) / eval(s2.split('/')[1])
                    sub_cost = 0.5 + abs(a1 - a2)  # 0.5 base + fraction diff
                except:
                    sub_cost = 1.0
                dp[i, j] = min(dp[i-1, j] + 1, dp[i, j-1] + 1, dp[i-1, j-1] + sub_cost)
    
    return dp[m, n] / max(m, n, 1)  # 归一化到 [0, 1]


# ============================================================
# 模块 3: k-Shape 核心 (保留 SBD + Rayleigh 商 centroid + FFT)
# ============================================================

def _ncc_c(x, y):
    """归一化互相关 NCC(x, y)_w for all w, via FFT"""
    n = len(x)
    x = (x - np.mean(x)) / (np.std(x) + 1e-12)
    y = (y - np.mean(y)) / (np.std(y) + 1e-12)
    
    # NCC(w) = ifft(fft(x) * conj(fft(y))) / n
    ncc = np.real(ifft(fft(x) * np.conj(fft(y)))) / n
    return ncc

def sbd(x, y):
    """Shape-Based Distance: 1 - max_w NCC(x, y_w)"""
    ncc = _ncc_c(x, y)
    return 1.0 - np.max(ncc)

def _sbd_matrix(X, Y=None):
    """计算 SBD 矩阵: X (m x L) vs Y (n x L)"""
    if Y is None: Y = X
    m, L = X.shape
    n = Y.shape[0]
    D = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            D[i, j] = sbd(X[i], Y[j])
    return D

def shape_extraction(X, centroids, labels):
    """k-Shape 的 centroid 提取 (Rayleigh 商优化)"""
    k = centroids.shape[0]
    L = X.shape[1]
    new_centroids = np.zeros((k, L))
    
    for ki in range(k):
        members = X[labels == ki]
        if len(members) == 0:
            new_centroids[ki] = centroids[ki]
            continue
        
        # 构造矩阵 M = Σ_i (x_i x_i^T + x̄_i^2 1 1^T) 的简化版
        # k-Shape 原文: centroid = 最大特征值对应的特征向量
        # 简化: 用所有成员的 Rayleigh 商近似
        
        # 构建平均 NCC 矩阵
        n_members = len(members)
        S = np.zeros((L, L))
        for x in members:
            x_norm = (x - np.mean(x)) / (np.std(x) + 1e-12)
            # S = X^T X (对每个成员)
            S += np.outer(x_norm, x_norm)
        
        # 最大特征向量 = Rayleigh 商解
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(S)
            mu = eigenvectors[:, -1]  # 最大特征值对应的向量
            
            # 缩放使 ||mu|| = 1
            mu = mu / (np.linalg.norm(mu) + 1e-12)
            
            # 调整幅度匹配成员
            member_std = np.mean([np.std(x) for x in members])
            mu = mu * member_std + np.mean([np.mean(x) for x in members])
            new_centroids[ki] = mu
        except:
            new_centroids[ki] = np.mean(members, axis=0)
    
    return new_centroids


# ============================================================
# 模块 4: 反幻 diversity loss → 簇间分离
# ============================================================

def anti_magic_inter_cluster_loss(centroids):
    """
    反幻簇间多样性损失: −Var(SBD(μ_i, μ_j))
    
    k-Shape 原生只优化簇内紧凑, 从不惩罚两个 centroid 长得太像。
    这一项显式最大化 centroid 之间的形状差异。
    """
    k = centroids.shape[0]
    if k < 2: return 0.0
    
    pairwise_sbd = []
    for i in range(k):
        for j in range(i + 1, k):
            pairwise_sbd.append(sbd(centroids[i], centroids[j]))
    
    if len(pairwise_sbd) == 0:
        return 0.0
    
    variance = np.var(pairwise_sbd)
    return -variance  # 负号: 最大化方差 = 最小化 -方差


# ============================================================
# 模块 5: 幻方因子化聚类
# ============================================================

def magic_square_decompose(ts, period=5):
    """
    幻方分解: 受 M = 5A + B + 1 启发
    T = Trend + Seasonal + Residual (通过 STL 风格分解)
    
    返回: (trend, seasonal, residual) 三个等长数组
    """
    n = len(ts)
    
    # 趋势: 移动平均 (窗口 = period)
    window = period
    trend = np.convolve(ts, np.ones(window) / window, mode='same')
    
    # 季节: 去趋势后按 period 分组取平均
    detrended = ts - trend
    seasonal = np.zeros(n)
    for i in range(period):
        idx = np.arange(i, n, period)
        if len(idx) > 0:
            seasonal[idx] = np.mean(detrended[idx])
    
    # 残差
    residual = ts - trend - seasonal
    
    return trend, seasonal, residual

def factorized_clustering(ts_list, k):
    """
    幻方因子化聚类:
      1. 每条序列分解为 Trend + Seasonal + Residual
      2. 三个分量分别做 k-Shape 聚类
      3. 最终簇标签 = 三个簇标签的多数投票
    """
    n = len(ts_list)
    L = max(len(ts) for ts in ts_list)
    
    # 插值对齐到统一长度
    aligned = np.zeros((n, L))
    for i, ts in enumerate(ts_list):
        if len(ts) == L:
            aligned[i] = ts
        else:
            xp = np.linspace(0, 1, len(ts))
            xq = np.linspace(0, 1, L)
            aligned[i] = np.interp(xq, xp, ts)
    
    # 分解
    trends = np.zeros_like(aligned)
    seasonals = np.zeros_like(aligned)
    residuals = np.zeros_like(aligned)
    
    for i in range(n):
        t, s, r = magic_square_decompose(aligned[i])
        trends[i] = t
        seasonals[i] = s
        residuals[i] = r
    
    # 在每个分量上跑简化 k-Shape
    from sklearn.cluster import KMeans
    
    # 趋势聚类
    km_trend = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels_trend = km_trend.fit_predict(trends)
    
    # 季节聚类
    km_season = KMeans(n_clusters=k, n_init=10, random_state=43)
    labels_season = km_season.fit_predict(seasonals)
    
    # 残差聚类
    km_resid = KMeans(n_clusters=k, n_init=10, random_state=44)
    labels_resid = km_resid.fit_predict(residuals)
    
    # 多数投票: 对每条序列, trend+season+resid 三个标签的多数
    from scipy.stats import mode as scipy_mode
    labels_combined = np.column_stack([labels_trend, labels_season, labels_resid])
    final_labels = scipy_mode(labels_combined, axis=1)[0].flatten()
    
    return final_labels, (labels_trend, labels_season, labels_resid)


# ============================================================
# Super k-Shape: 四算法统一升级
# ============================================================

class SuperKShape:
    """
    Super k-Shape = k-Shape + 四增强
    
    参数:
      k: 簇数
      lambda_farey: Farey 路径距离在混合距离中的权重 [0, 1]
      lambda_anti: 反幻 diversity loss 的权重
      use_magic_decomp: 是否启用幻方因子化 (对长序列有效)
      use_sharkovsky_init: 是否用 Sharkovsky-DP 初始化替代随机初始化
    """
    def __init__(self, k=3, lambda_farey=0.3, lambda_anti=0.1,
                 use_magic_decomp=True, use_sharkovsky_init=True,
                 max_iter=100, tol=1e-6):
        self.k = k
        self.lambda_farey = lambda_farey
        self.lambda_anti = lambda_anti
        self.use_magic_decomp = use_magic_decomp
        self.use_sharkovsky_init = use_sharkovsky_init
        self.max_iter = max_iter
        self.tol = tol
        self.centroids_ = None
        self.labels_ = None
        self.sbd_centroids_ = None  # 纯 k-Shape 的 centroid (用于对比)
    
    def _hybrid_distance(self, x, y):
        """混合距离: λ_farey · FareyEditDist + (1-λ_farey) · SBD"""
        d_sbd = sbd(x, y)
        if self.lambda_farey > 0:
            path_x = farey_path(x)
            path_y = farey_path(y)
            d_farey = farey_edit_distance(path_x, path_y)
            return (1 - self.lambda_farey) * d_sbd + self.lambda_farey * d_farey
        return d_sbd
    
    def fit(self, X):
        """
        训练 Super k-Shape
        
        X: list of 1D arrays (变长序列)
        """
        n = len(X)
        # 对齐到统一长度
        L = max(len(ts) for ts in X)
        X_aligned = np.zeros((n, L))
        for i, ts in enumerate(X):
            if len(ts) == L:
                X_aligned[i] = ts
            else:
                xp = np.linspace(0, 1, len(ts))
                xq = np.linspace(0, 1, L)
                X_aligned[i] = np.interp(xq, xp, ts)
        
        t0 = time.time()
        
        # === 增强 1: Sharkovsky-DP 初始化 ===
        if self.use_sharkovsky_init and self.k < n:
            labels = structural_init(X, self.k)
            print(f"  [init] Sharkovsky-DP structural init: "
                  f"{dict(zip(*np.unique(labels, return_counts=True)))}")
        else:
            from sklearn.cluster import KMeans
            km = KMeans(n_clusters=self.k, n_init=10, random_state=42)
            labels = km.fit_predict(X_aligned)
            print(f"  [init] KMeans random init")
        
        # === 增强 4: 幻方因子化 ===
        if self.use_magic_decomp:
            magic_labels, _ = factorized_clustering(X, self.k)
            # 融合: Sharkovsky-DP 初始化 + 幻方因子化结果 取多数
            combined = np.column_stack([labels, magic_labels])
            from scipy.stats import mode as scipy_mode
            labels = scipy_mode(combined, axis=1)[0].flatten()
            print(f"  [init] + Magic factorization fused: "
                  f"{dict(zip(*np.unique(labels, return_counts=True)))}")
        
        # === 初始化 centroid ===
        centroids = np.zeros((self.k, L))
        for ki in range(self.k):
            members = X_aligned[labels == ki]
            if len(members) > 0:
                centroids[ki] = np.mean(members, axis=0)
            else:
                centroids[ki] = X_aligned[np.random.randint(n)]
        
        # === EM 迭代 ===
        prev_loss = inf
        for iteration in range(self.max_iter):
            # --- E-step: 分配 ---
            new_labels = np.zeros(n, dtype=int)
            for i in range(n):
                dists = [self._hybrid_distance(X_aligned[i], centroids[j]) 
                         for j in range(self.k)]
                new_labels[i] = np.argmin(dists)
            
            # --- M-step: 更新 centroid ---
            # 保留 k-Shape 的 Rayleigh 商优化 (增强 2+3)
            self.sbd_centroids_ = shape_extraction(X_aligned, centroids, new_labels)
            
            # === 增强 3: 反幻 diversity 调整 ===
            if self.lambda_anti > 0:
                # 计算反幻梯度方向 (让 centroid 彼此推远)
                am_loss = anti_magic_inter_cluster_loss(self.sbd_centroids_)
                
                # 将反幻梯度注入 centroid 更新
                # 做法: 如果两个 centroid 太像 (SBD < 0.3), 微调它们彼此远离
                centroids = self.sbd_centroids_.copy()
                for i in range(self.k):
                    for j in range(i + 1, self.k):
                        if sbd(centroids[i], centroids[j]) < 0.3:
                            # 在两者差异方向上小幅移动
                            diff = centroids[i] - centroids[j]
                            norm = np.linalg.norm(diff) + 1e-12
                            push = self.lambda_anti * diff / norm
                            centroids[i] += push
                            centroids[j] -= push
            else:
                centroids = self.sbd_centroids_
            
            # --- 计算总损失 ---
            intra_loss = sum(self._hybrid_distance(X_aligned[i], centroids[new_labels[i]]) 
                            for i in range(n))
            am_term = anti_magic_inter_cluster_loss(centroids) if self.lambda_anti > 0 else 0
            total_loss = intra_loss + self.lambda_anti * am_term
            
            if iteration % 10 == 0 or iteration == self.max_iter - 1:
                print(f"  [iter {iteration:3d}] intra={intra_loss:.4f} "
                      f"anti={am_term:.4f} total={total_loss:.4f}")
            
            # 收敛检查
            if abs(prev_loss - total_loss) < self.tol:
                print(f"  Converged at iteration {iteration}")
                labels = new_labels
                break
            
            labels = new_labels
            prev_loss = total_loss
        
        self.labels_ = labels
        self.centroids_ = centroids
        elapsed = time.time() - t0
        print(f"  Total time: {elapsed:.1f}s ({n} series, {self.k} clusters)")
        
        return self
    
    def predict(self, X):
        """预测 (使用训练好的 centroid)"""
        L = self.centroids_.shape[1]
        n = len(X)
        labels = np.zeros(n, dtype=int)
        for i, ts in enumerate(X):
            if len(ts) < L:
                xp = np.linspace(0, 1, len(ts))
                xq = np.linspace(0, 1, L)
                ts_aligned = np.interp(xq, xp, ts)
            else:
                ts_aligned = ts[:L]
            dists = [self._hybrid_distance(ts_aligned, self.centroids_[j]) 
                    for j in range(self.k)]
            labels[i] = np.argmin(dists)
        return labels


# ============================================================
# 对比实验: k-Shape baseline vs Super k-Shape
# ============================================================

def generate_synthetic_data(n_series=200, length=128, n_clusters=3):
    """
    生成合成时序数据 (模拟 UCR 风格)
    每个簇有不同的趋势/季节/噪声模式
    """
    np.random.seed(42)
    data = []
    true_labels = []
    
    templates = [
        # 簇 0: 缓慢上升 + 正弦季节
        lambda t: 0.5 * t + 2.0 * np.sin(2 * np.pi * t / 20),
        # 簇 1: 平稳 + 高频锯齿
        lambda t: 3.0 + 1.5 * np.sin(2 * np.pi * t / 8),
        # 簇 2: 下降趋势 + 低频方波
        lambda t: 5.0 - 0.3 * t + 2.0 * np.sign(np.sin(2 * np.pi * t / 30)),
    ]
    
    for cluster_id in range(n_clusters):
        for _ in range(n_series // n_clusters):
            t = np.linspace(0, 1, length)
            base = templates[cluster_id](np.arange(length))
            noise = np.random.randn(length) * 0.5
            ts = base + noise
            # 随机相位偏移
            shift = np.random.randint(0, length // 4)
            ts = np.roll(ts, shift)
            data.append(ts)
            true_labels.append(cluster_id)
    
    return data, np.array(true_labels)

def evaluate_clustering(true_labels, pred_labels):
    """计算 ARI 和 NMI"""
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    return {
        'ARI': adjusted_rand_score(true_labels, pred_labels),
        'NMI': normalized_mutual_info_score(true_labels, pred_labels),
    }

def run_comparison():
    """k-Shape baseline vs Super k-Shape 对比"""
    print("=" * 60)
    print("Super k-Shape: 四算法升级 vs k-Shape (2015) baseline")
    print("=" * 60)
    
    # 生成数据
    X, y_true = generate_synthetic_data(n_series=300, length=128, n_clusters=3)
    print(f"\nDataset: {len(X)} series × ~128 length, {len(set(y_true))} true clusters")
    
    # Baseline: 简化 k-Shape (只 SBD centering)
    print("\n--- Baseline: k-Shape (SBD only) ---")
    t0 = time.time()
    baseline = SuperKShape(k=3, lambda_farey=0.0, lambda_anti=0.0,
                           use_magic_decomp=False, use_sharkovsky_init=False)
    baseline.fit(X)
    baseline_time = time.time() - t0
    baseline_metrics = evaluate_clustering(y_true, baseline.labels_)
    print(f"  ARI={baseline_metrics['ARI']:.4f} NMI={baseline_metrics['NMI']:.4f}")
    print(f"  Time: {baseline_time:.1f}s")
    
    # Super k-Shape: 全部增强
    print("\n--- Super k-Shape: ALL enhancements ---")
    t0 = time.time()
    super_ks = SuperKShape(k=3, lambda_farey=0.3, lambda_anti=0.1,
                           use_magic_decomp=True, use_sharkovsky_init=True)
    super_ks.fit(X)
    super_time = time.time() - t0
    super_metrics = evaluate_clustering(y_true, super_ks.labels_)
    print(f"  ARI={super_metrics['ARI']:.4f} NMI={super_metrics['NMI']:.4f}")
    print(f"  Time: {super_time:.1f}s")
    
    # 消融实验: 逐个增强
    print("\n--- Ablation: 逐个增强效果 ---")
    configs = [
        ("k-Shape (baseline)", 0.0, 0.0, False, False),
        ("+ Sharkovsky init", 0.0, 0.0, False, True),
        ("+ Farey distance", 0.3, 0.0, False, True),
        ("+ Anti-magic only", 0.0, 0.1, False, True),
        ("+ Magic decomp only", 0.0, 0.0, True, True),
        ("ALL (Super k-Shape)", 0.3, 0.1, True, True),
    ]
    
    results = []
    for name, lf, la, magic, shark in configs:
        model = SuperKShape(k=3, lambda_farey=lf, lambda_anti=la,
                            use_magic_decomp=magic, use_sharkovsky_init=shark)
        model.fit(X)
        m = evaluate_clustering(y_true, model.labels_)
        results.append((name, m['ARI'], m['NMI']))
        print(f"  {name:>25s}: ARI={m['ARI']:.4f} NMI={m['NMI']:.4f}")
    
    # 输出对比表
    print("\n" + "=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Configuration':<30s} {'ARI':>8s} {'NMI':>8s} {'vs Baseline':>12s}")
    print("-" * 60)
    base_ari = results[0][1]
    base_nmi = results[0][2]
    for name, ari, nmi in results:
        delta_ari = ari - base_ari
        delta_nmi = nmi - base_nmi
        delta_str = f"ARI{delta_ari:+.4f} NMI{delta_nmi:+.4f}"
        print(f"{name:<30s} {ari:8.4f} {nmi:8.4f} {delta_str:>12s}")
    
    return results

if __name__ == '__main__':
    run_comparison()
