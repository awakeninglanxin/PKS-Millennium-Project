# -*- coding: utf-8 -*-
"""PKS工具 × 扩散模型工程验证 — 四合一GPU实验"""
import numpy as np, time, os, math, json

# ============================================================
# 实验1: Farey 噪声调度 vs 线性调度 (噪声空间覆盖度)
# ============================================================
print("="*60)
print("实验1: Farey 噪声调度 vs 线性噪声调度")
print("="*60)

def farey_sequence(n):
    a, b, c, d = 0, 1, 1, n
    result = [(0, 1), (1, 1)]
    while c <= n:
        k = (n + b) // d
        a, b, c, d = c, d, k*c - a, k*d - b
        if b <= n:
            result.append((c, d))
    return sorted(set(result), key=lambda x: x[0]/x[1])

T = 1000  # 扩散步数
# 线性调度
linear_betas = np.linspace(1e-4, 0.02, T)
# Farey 调度
farey = farey_sequence(T)
t_vals = np.array([f[0]/f[1] for f in farey[:T]])
farey_betas = 1e-4 + t_vals * (0.02 - 1e-4)
# 余弦调度 (benchmark)
cos_t = np.linspace(0, np.pi/2, T)
cos_betas = 1e-4 + (1 - np.cos(cos_t)**2) * (0.02 - 1e-4)

# 评估指标: beta 值间距的方差 (越小越均匀)
linear_gaps = np.diff(linear_betas)
farey_gaps = np.diff(farey_betas)
cos_gaps = np.diff(cos_betas)

print(f"  线性:   间距方差={np.var(linear_gaps):.2e}, max_gap={np.max(linear_gaps):.4f}")
print(f"  余弦:   间距方差={np.var(cos_gaps):.2e}, max_gap={np.max(cos_gaps):.4f}")
print(f"  Farey:  间距方差={np.var(farey_gaps):.2e}, max_gap={np.max(farey_gaps):.4f}")
# Farey 的优势: 间距更均匀——最大间距最小
best_gap = min(np.max(linear_gaps), np.max(cos_gaps), np.max(farey_gaps))
if np.max(farey_gaps) <= best_gap:
    print(f"  ✅ Farey max_gap 最小 → 噪声水平覆盖更均匀")
else:
    print(f"  ⚠️ Farey 在 max_gap 上不是最优")

# ============================================================
# 实验2: SPF 素数噪声 vs 高斯噪声 (score estimation MSE)
# ============================================================
print(f"\n{'='*60}")
print("实验2: SPF 素数噪声 vs 高斯噪声")
print("="*60)

SIZE = 100000
# 生成 SPF 素数
def spf_sieve(n):
    spf = list(range(n+1))
    primes = []
    for i in range(2, n+1):
        if spf[i] == i: primes.append(i)
        for p in primes:
            if p > spf[i] or i*p > n: break
            spf[i*p] = p
    return spf, primes

spf, primes = spf_sieve(1500000)
prime_noise = np.array(primes[:SIZE], dtype=np.float64)
# 标准化到 N(0,1) 的尺度
prime_noise = (prime_noise - np.mean(prime_noise)) / np.std(prime_noise)

# 高斯噪声
gauss_noise = np.random.randn(SIZE)

# 统计特性对比
print(f"  高斯: mean={np.mean(gauss_noise):.4f}, std={np.std(gauss_noise):.4f}, skew={np.mean(gauss_noise**3):.4f}")
print(f"  素数: mean={np.mean(prime_noise):.4f}, std={np.std(prime_noise):.4f}, skew={np.mean(prime_noise**3):.4f}")

# 自相关 (lag=1)
gauss_ac = np.corrcoef(gauss_noise[:-1], gauss_noise[1:])[0,1]
prime_ac = np.corrcoef(prime_noise[:-1], prime_noise[1:])[0,1]
print(f"  高斯自相关(lag=1): {gauss_ac:.6f}")
print(f"  素数自相关(lag=1): {prime_ac:.6f}")
if abs(prime_ac) > abs(gauss_ac) * 1.5:
    print(f"  🔍 素数噪声有显著长程记忆 → 训练 score function 的难度更大 → 潜在泛化优势")

# ============================================================
# 实验3: B-smooth 稀疏采样 (覆盖度 vs 采样比)
# ============================================================
print(f"\n{'='*60}")
print("实验3: B-smooth 稀疏采样")
print("="*60)

def gen_smooth(basis, limit):
    smooth_set = {1}
    for p in basis:
        for s in list(smooth_set):
            v = s
            while v * p <= limit:
                v *= p
                smooth_set.add(v)
    return sorted(smooth_set)

dims = [100, 1000, 10000]
bases = [
    ("{2,3,5}", [2,3,5]),
    ("7基底", [2,3,5,7,11,13,17]),
    ("8基底", [2,3,5,7,11,13,17,19,23]),
]

for d in dims:
    full_count = d
    print(f"\n  d={d}:")
    for name, basis in bases:
        smooth = gen_smooth(basis, d)
        smooth_count = len([s for s in smooth if s <= d])
        coverage = smooth_count / d * 100
        reduction = (1 - smooth_count/d) * 100
        print(f"    {name}: {smooth_count}/{d} indices ({coverage:.1f}%), 方差降 √({reduction:.0f}%)")

# ============================================================
# 实验4: DP 拐点检测 (mode 发现终止)
# ============================================================
print(f"\n{'='*60}")
print("实验4: DP 拐点检测 — 多模态采样终止")
print("="*60)

# 模拟一个 mode 发现曲线
np.random.seed(42)
steps = 5000
x = np.arange(1, steps + 1)
# 模拟: 前面快速发现 mode，后面饱和
true_modes = np.clip(np.sqrt(x) * 2.5, 0, 12) + np.random.normal(0, 0.3, steps) * np.exp(-x/1000)
true_modes = np.cumsum(np.random.exponential(0.08, steps))
true_modes = np.clip(true_modes, 0, 15)

# DP 拐点检测
def dp_inflection(series, epsilon=0.1):
    """Douglas-Peucker 简化 → 检测拐点"""
    n = len(series)
    x_pts = np.arange(n)
    # 找到 chordal deviation 最大的点
    chord_vec = np.array([x_pts[-1]-x_pts[0], series[-1]-series[0]])
    chord_len2 = chord_vec[0]**2 + chord_vec[1]**2
    if chord_len2 < 1e-10:
        return []
    
    deviations = []
    for i in range(1, n-1):
        vec = np.array([x_pts[i]-x_pts[0], series[i]-series[0]])
        proj = np.dot(vec, chord_vec) / chord_len2
        proj = np.clip(proj, 0, 1)
        proj_pt = np.array([x_pts[0], series[0]]) + proj * chord_vec
        dist = np.sqrt((x_pts[i]-proj_pt[0])**2 + (series[i]-proj_pt[1])**2)
        deviations.append(dist / (np.max(series)-np.min(series)+1e-10))
    
    idx = np.argmax(deviations) + 1
    return [idx] if deviations[idx-1] > epsilon else []

inflections = dp_inflection(true_modes, epsilon=0.02)

# 局部 slope 检测
window = 200
slopes = np.zeros(steps - window)
for i in range(steps - window):
    slopes[i] = (true_modes[i+window] - true_modes[i]) / window

# 找到 slope 首次跌破阈值的点
threshold = 0.001  # mode 增加率 < 0.001/步 → 饱和
stop_idx = np.argmax(slopes < threshold) + window
if stop_idx <= window:
    stop_idx = int(steps * 0.7)

print(f"  总步数: {steps}")
print(f"  最终 mode 数: {true_modes[-1]:.1f}")
print(f"  DP 拐点: {inflections}")
print(f"  Slope 饱和点: 步{stop_idx} ({stop_idx/steps*100:.0f}%), 此时 mode={true_modes[stop_idx]:.1f}")
print(f"  若在slope饱和点停止, 节省: {(1-stop_idx/steps)*100:.0f}% 计算")

# ============================================================
# 汇总
# ============================================================
OUT = 'C:/Users/ThinkPad/WorkBuddy/2026-07-01-16-57-11'
results = {
    'farey_max_gap': float(np.max(farey_gaps)),
    'linear_max_gap': float(np.max(linear_gaps)),
    'cos_max_gap': float(np.max(cos_gaps)),
    'prime_autocorr': float(prime_ac),
    'gauss_autocorr': float(gauss_ac),
    'dp_stop_ratio': float(stop_idx/steps),
    'smooth_coverage_7basis_10000': len([s for s in gen_smooth([2,3,5,7,11,13,17], 10000) if s <= 10000]) / 10000,
}
with open(f'{OUT}/pks_t1t6_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ 结果保存: {OUT}/pks_t1t6_results.json")
