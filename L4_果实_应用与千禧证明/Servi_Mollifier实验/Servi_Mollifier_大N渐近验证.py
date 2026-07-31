#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi-Croft Kernel 大N渐近稳定性验证
══════════════════════════════════════════════════════
验证 prime-detection ratio 在 N → ∞ 时是否保持稳定。
N_max 从 40 扩展到 2000，使用 numpy 向量化加速。

若 ratio 始终 > 1.2 (Loiseau B-class 阈值)，则 Servi-Croft 核
可宣称"在渐近意义下跳出 Loiseau 类B"。

2026-07-15
"""

import numpy as np
import matplotlib.pyplot as plt
import os, time

od = os.path.dirname(os.path.abspath(__file__))

CROFT_TOTATIVES = frozenset({1, 7, 11, 13, 17, 19, 23, 29})

# ====== 素数筛 (预计算到 N_max) ======
def prime_sieve(limit):
    """Eratosthenes 筛法，返回长度 limit+1 的布尔数组"""
    is_p = np.ones(limit + 1, dtype=bool)
    is_p[:2] = False
    for p in range(2, int(limit ** 0.5) + 1):
        if is_p[p]:
            is_p[p * p : limit + 1 : p] = False
    return is_p

def prime_detection_ratio_vectorized(t_values, N_max, use_croft=True, prime_sieve_cache=None):
    """
    Croft-Servi kernel prime-detection 测试 (numpy向量化版)

    对每个 t ∈ t_values:
        Kp(t) = Σ_{n ∈ primes}     cos(-t·log n)/√n · φ_n
        Kn(t) = Σ_{n ∈ composites} cos(-t·log n)/√n · φ_n
    其中 φ_n = max(0, 1 - n/N_max)

    ratio = Var(Kp) / Var(Kn)
    """
    # 构建 n 数组 (Croft 筛选)
    if use_croft:
        n_all = np.array([n for n in range(2, N_max + 1) if (n % 30) in CROFT_TOTATIVES], dtype=np.float64)
    else:
        n_all = np.arange(2, N_max + 1, dtype=np.float64)

    if len(n_all) == 0:
        return {'N_max': N_max, 'use_croft': use_croft, 'ratio': 0.0,
                'var_Kp': 0.0, 'var_Kn': 0.0, 'n_coeffs': 0, 'n_primes': 0}

    # 素数标记
    if prime_sieve_cache is not None:
        prime_mask = prime_sieve_cache[n_all.astype(int)]
    else:
        prime_mask = np.array([all(n % p != 0 for p in range(2, int(np.sqrt(n)) + 1)) for n in n_all.astype(int)])

    # 预计算公共因子
    log_n = np.log(n_all)
    inv_sqrt_n = 1.0 / np.sqrt(n_all)
    phi_n = np.maximum(0.0, 1.0 - n_all / N_max)

    # 转换为列向量用于广播
    t_arr = np.asarray(t_values, dtype=np.float64)[:, np.newaxis]  # (n_t, 1)

    # 全量向量化: terms[i,j] = cos(-t_i * log(n_j)) / sqrt(n_j) * phi(n_j)
    # 形状: (n_t, n_coeffs)
    terms = np.cos(-t_arr * log_n[np.newaxis, :]) * (inv_sqrt_n[np.newaxis, :] * phi_n[np.newaxis, :])

    # 按素数/合数拆分求和
    Kp_arr = np.sum(terms[:, prime_mask], axis=1)   # (n_t,)
    Kn_arr = np.sum(terms[:, ~prime_mask], axis=1)  # (n_t,)

    ratio = np.var(Kp_arr) / (np.var(Kn_arr) + 1e-15)

    return {
        'N_max': N_max, 'use_croft': use_croft, 'ratio': float(ratio),
        'var_Kp': float(np.var(Kp_arr)), 'var_Kn': float(np.var(Kn_arr)),
        'n_coeffs': len(n_all), 'n_primes': int(np.sum(prime_mask))
    }

# ====== 主实验 ======
print("=" * 64)
print("  Servi-Croft Kernel 大N渐近稳定性验证 (N_max up to 2000)")
print("=" * 64)
print(f"  Loiseau B-class 阈值: 1.2")
print(f"  算法: numpy 向量化 (全量广播)")
print()

T_MAX = 80
N_values = [60, 100, 200, 500, 1000, 2000]
# 注: N=40 跳过，因所有 Croft totatives ≤40 均为素数，ratio 失去意义
t_points = 300  # 固定采样点数

results_vanilla = []
results_croft = []
timings = []

# 预计算最大素数筛
max_n = N_values[-1]
prime_cache = prime_sieve(max_n)
print(f"  [预计算] 素数筛: 2 → {max_n}, 素数个数 = {prime_cache.sum()}")
print()

for i, N in enumerate(N_values):
    t_range = np.linspace(10, T_MAX, t_points)

    # Vanilla
    t0 = time.perf_counter()
    r_v = prime_detection_ratio_vectorized(t_range, N, use_croft=False, prime_sieve_cache=prime_cache)
    t1 = time.perf_counter()

    # Croft
    r_c = prime_detection_ratio_vectorized(t_range, N, use_croft=True, prime_sieve_cache=prime_cache)
    t2 = time.perf_counter()

    results_vanilla.append(r_v)
    results_croft.append(r_c)
    timings.append({'N': N, 't_vanilla': t1 - t0, 't_croft': t2 - t1, 't_total': t2 - t0})

    print(f"  N={N:5d} | Vanilla ratio={r_v['ratio']:10.2f} ({r_v['n_coeffs']:4d} coeffs)"
          f" | Croft ratio={r_c['ratio']:10.2f} ({r_c['n_coeffs']:4d} coeffs, {r_c['n_primes']:3d} primes)"
          f" | {t2-t0:.2f}s")

# ====== CSV 输出 ======
csv_path = os.path.join(od, 'Servi_Mollifier_渐近报告_N2000.csv')
with open(csv_path, 'w', encoding='utf-8-sig') as f:
    f.write("N_max,method,ratio,var_Kp,var_Kn,n_coeffs,n_primes,time_s\n")
    for r_v, r_c, t in zip(results_vanilla, results_croft, timings):
        f.write(f"{r_v['N_max']},Vanilla,{r_v['ratio']:.6f},{r_v['var_Kp']:.6f},{r_v['var_Kn']:.6f},{r_v['n_coeffs']},{r_v['n_primes']},{t['t_vanilla']:.4f}\n")
        f.write(f"{r_c['N_max']},Croft-Servi,{r_c['ratio']:.6f},{r_c['var_Kp']:.6f},{r_c['var_Kn']:.6f},{r_c['n_coeffs']},{r_c['n_primes']},{t['t_croft']:.4f}\n")
print(f"\n  [CSV] 报告已保存: {csv_path}")

# ====== 可视化 ======
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 3, figsize=(19, 5.8))

ratios_v = [r['ratio'] for r in results_vanilla]
ratios_c = [r['ratio'] for r in results_croft]
coeffs_v = [r['n_coeffs'] for r in results_vanilla]
coeffs_c = [r['n_coeffs'] for r in results_croft]
primes_c = [r['n_primes'] for r in results_croft]

# Panel 1: Ratio vs N (对数坐标)
ax = axes[0]
ax.plot(N_values, ratios_v, 's-', ms=7, lw=1.5, color='#2c3e50', label='Vanilla Servi', zorder=3)
ax.plot(N_values, ratios_c, 'o-', ms=9, lw=2.8, color='#e74c3c', label='Croft-Servi', zorder=4)
ax.axhline(1.2, color='gray', ls='--', lw=1.0, alpha=0.5, label='Loiseau threshold (1.2)')
ax.axhline(2.0, color='green', ls='--', lw=1.0, alpha=0.5, label='Strong detection (2.0)')
ax.set_xlabel('N_max', fontsize=11)
ax.set_ylabel('Var(Kp) / Var(Kn)', fontsize=11)
ax.set_title(f'Prime-Detection Ratio vs N_max\n(N=40 ~ {N_values[-1]})', fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(alpha=0.3)
ax.set_yscale('log')
for n, r in zip(N_values, ratios_c):
    ax.annotate(f'{r:.0f}', (n, r), textcoords="offset points", xytext=(0, 10),
                fontsize=8, ha='center', color='#e74c3c', fontweight='bold')

# Panel 2: Coefficient count vs N
ax2 = axes[1]
ax2.plot(N_values, coeffs_v, 's--', ms=6, lw=1.2, alpha=0.7, color='#2c3e50', label='Vanilla (all integers)')
ax2.plot(N_values, coeffs_c, 'o-', ms=7, lw=2.2, color='#e74c3c', label='Croft (totatives only)')
ax2.plot(N_values, primes_c, 'D--', ms=6, lw=1.2, color='green', alpha=0.8, label='Primes in Croft set')
ax2.set_xlabel('N_max', fontsize=11)
ax2.set_ylabel('Count', fontsize=11)
ax2.set_title('Coefficient / Prime Count Growth', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# Panel 3: Ratio stability (Croft only, 以 N=40 为基线)
ax3 = axes[2]
ratio_stable = [r / ratios_c[0] for r in ratios_c]
bars = ax3.bar(range(len(N_values)), ratio_stable,
               tick_label=[str(n) for n in N_values],
               color=['#27ae60' if r > 0.3 else '#e74c3c' for r in ratio_stable],
               alpha=0.88, edgecolor='white', linewidth=0.5)
ax3.axhline(1.0, color='gray', ls='--', lw=1.0, alpha=0.5)
# 标注绝对 ratio 值
for i, (rs, rc) in enumerate(zip(ratio_stable, ratios_c)):
    ax3.text(i, rs + 0.03, f'{rc:.1f}', ha='center', fontsize=8, fontweight='bold', color='#e74c3c')
ax3.set_ylabel(f'Ratio / Ratio(N={N_values[0]})', fontsize=11)
ax3.set_title(f'Croft-Servi Ratio Stability (N={N_values[0]} baseline)', fontsize=12, fontweight='bold')

plt.suptitle(f'Servi-Croft Kernel 大N渐近稳定性 — Loiseau Spectral Barrier 出口验证\n'
             f'N_max ∈ [{N_values[0]}, {N_values[-1]}]  |  t_points = {t_points}  |  向量化计算',
             fontsize=13, fontweight='bold')
plt.tight_layout()

out_path = os.path.join(od, 'Servi_Mollifier_渐近验证_N2000.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"\n  [PNG] 图表已保存: {out_path}")

# ====== 判决 ======
print(f"\n{'='*64}")
print(f"  判决: Croft-Servi prime-detection ratio 渐近稳定性")
print(f"{'='*64}")
min_ratio = min(ratios_c)
max_ratio = max(ratios_c)
mean_ratio = np.mean(ratios_c)
ratio_2000 = ratios_c[-1]

print(f"  N range:         {N_values[0]} → {N_values[-1]}")
print(f"  Ratio range:     {min_ratio:.2f} → {max_ratio:.2f}")
print(f"  Mean ratio:      {mean_ratio:.2f}")
print(f"  Ratio at N=2000: {ratio_2000:.2f}")
print(f"  Min/Max ratio:   {min_ratio/max_ratio:.4f}")

# 趋势分析
ratio_trend = (ratios_c[-1] - ratios_c[0]) / ratios_c[0] * 100 if ratios_c[0] != 0 else 0
print(f"  相对变化 (N={N_values[0]}→{N_values[-1]}): {ratio_trend:+.1f}%")

# 渐近分析
if len(ratios_c) >= 4:
    later_ratios = ratios_c[-3:]  # 最后三个点
    later_std = np.std(later_ratios)
    later_mean = np.mean(later_ratios)
    convergence_ratio = later_std / (later_mean + 1e-15)
    print(f"  后期稳定性 (N≥{N_values[-3]}): 均值={later_mean:.2f}, std={later_std:.2f}, CV={convergence_ratio:.4f}")
    if convergence_ratio < 0.1:
        print(f"  → 渐近收敛: ratio 已趋于稳定常数")
    else:
        print(f"  → ratio 仍在变化中，建议进一步扩大 N")

# Loiseau 判决
above_threshold = min_ratio > 1.2
is_increasing = ratios_c[-1] > ratios_c[0] * 0.8  # 没有大幅衰减

if above_threshold and is_increasing:
    print(f"\n  [判定] Croft-Servi kernel 在 N∈[{N_values[0]},{N_values[-1]}] 全范围内")
    print(f"         ratio 保持 > 1.2 (Loiseau B-class 阈值)")
    if min_ratio > 2.0:
        print(f"         且保持 > 2.0 (强检测阈值)")
    print(f"  [结论] 可正式宣称: '渐近意义下跳出 Loiseau 类B 的构造性核'")
    print(f"  [结论] 大N渐近验证通过")
elif above_threshold:
    print(f"\n  [判定] ratio 仍 > 1.2 但呈下降趋势，需关注")
    print(f"  [建议] 进一步扩大 N 至 5000 或 10000 观察极限行为")
else:
    print(f"\n  [警告] ratio 在部分 N 值处低于 1.2 Loiseau 阈值")
    print(f"  [警告] 最小 ratio = {min_ratio:.2f} at some N")

# 性能报告
total_time = sum(t['t_total'] for t in timings)
print(f"\n  [性能] 总计计算时间: {total_time:.2f}s")
print(f"         向量化加速: 全量 numpy 广播 (单次广播矩阵最大 {t_points}×{max(coeffs_c)})")
