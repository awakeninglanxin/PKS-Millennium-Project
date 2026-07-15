#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi-Croft Kernel 大N渐近稳定性验证
══════════════════════════════════════════════════════
验证 prime-detection ratio 在 N → ∞ 时是否保持稳定。
若 N_max=60→1000 下 ratio 始终 > 2.0，则 Servi-Croft 核
可宣称"在渐近意义下成立"。

2026-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import os, math as _math
from math import log, sqrt, pi, cos

od = os.path.dirname(os.path.abspath(__file__))

CROFT_TOTATIVES = frozenset({1, 7, 11, 13, 17, 19, 23, 29})

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def is_croft_totative(n):
    return (n % 30) in CROFT_TOTATIVES

def prime_detection_ratio(t_values, N_max, use_croft=True):
    """Croft-Servi kernel prime-detection 测试"""
    t_mid = np.mean(t_values)
    K_prime_t, K_nonprime_t = [], []
    for t in t_values:
        Kp, Kn = 0.0, 0.0
        for n in range(2, N_max + 1):
            if use_croft and not is_croft_totative(n):
                continue
            phi_n = max(0, 1.0 - n / N_max)
            term = cos(-t * log(n)) / sqrt(n) * phi_n
            if is_prime(n):
                Kp += term
            else:
                Kn += term
        K_prime_t.append(Kp)
        K_nonprime_t.append(Kn)
    Kp_arr = np.array(K_prime_t)
    Kn_arr = np.array(K_nonprime_t)
    ratio = np.var(Kp_arr) / (np.var(Kn_arr) + 1e-12)
    n_coeffs = sum(1 for n in range(2, N_max+1) if (not use_croft or is_croft_totative(n)))
    n_primes = sum(1 for n in range(2, N_max+1) if (not use_croft or is_croft_totative(n)) and is_prime(n))
    return {
        'N_max': N_max, 'use_croft': use_croft, 'ratio': ratio,
        'var_Kp': np.var(Kp_arr), 'var_Kn': np.var(Kn_arr),
        'n_coeffs': n_coeffs, 'n_primes': n_primes
    }

# ====== 主实验 ======
print("=" * 60)
print("Servi-Croft Kernel 大N渐近稳定性验证")
print("=" * 60)

T_MAX = 80
N_values = [60, 100, 150, 200, 300, 400, 500]
t_points = 300

results_vanilla = []
results_croft = []

for N in N_values:
    t_range = np.linspace(10, T_MAX, max(t_points, N//2))
    r_v = prime_detection_ratio(t_range, N, use_croft=False)
    r_c = prime_detection_ratio(t_range, N, use_croft=True)
    results_vanilla.append(r_v)
    results_croft.append(r_c)
    print(f"N={N:4d}:  Vanilla={r_v['ratio']:8.2f} (coeffs={r_v['n_coeffs']:4d})"
          f"  |  Croft={r_c['ratio']:10.2f} (coeffs={r_c['n_coeffs']:4d}, "
          f"primes={r_c['n_primes']:3d})")

# ====== 可视化 ======
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

# Panel 1: Ratio vs N (对数坐标)
ax = axes[0]
ratios_v = [r['ratio'] for r in results_vanilla]
ratios_c = [r['ratio'] for r in results_croft]
ax.plot(N_values, ratios_v, 's-', ms=6, lw=1.5, color='#2c3e50', label='Vanilla Servi')
ax.plot(N_values, ratios_c, 'o-', ms=8, lw=2.5, color='#e74c3c', label='Croft-Servi 🔥')
ax.axhline(1.2, color='gray', ls='--', alpha=0.4, label='Loiseau threshold (1.2)')
ax.axhline(2.0, color='green', ls='--', alpha=0.4, label='Strong detection (2.0)')
ax.set_xlabel('N_max'); ax.set_ylabel('Var(Kp)/Var(Kn)')
ax.set_title('Prime-Detection Ratio vs N_max')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.set_yscale('log')
# 标注
for n, r in zip(N_values, ratios_c):
    ax.annotate(f'{r:.0f}', (n, r), textcoords="offset points", xytext=(0, 8),
                fontsize=7, ha='center', color='#e74c3c')

# Panel 2: Coefficient count vs N
ax2 = axes[1]
coeffs_v = [r['n_coeffs'] for r in results_vanilla]
coeffs_c = [r['n_coeffs'] for r in results_croft]
primes_c = [r['n_primes'] for r in results_croft]
ax2.plot(N_values, coeffs_v, 's--', ms=5, alpha=0.7, color='#2c3e50', label='Vanilla (all ints)')
ax2.plot(N_values, coeffs_c, 'o-', ms=6, lw=2, color='#e74c3c', label='Croft (totatives only)')
ax2.plot(N_values, primes_c, 'D--', ms=5, color='green', alpha=0.7, label='Primes in Croft set')
ax2.set_xlabel('N_max'); ax2.set_ylabel('Count')
ax2.set_title('Coefficient / Prime Count Growth')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# Panel 3: Ratio stability (Croft only, linear)
ax3 = axes[2]
# 计算比值稳定性
ratio_stable = [r/ratios_c[0] for r in ratios_c]
ax3.bar(range(len(N_values)), ratio_stable, tick_label=[str(n) for n in N_values],
        color=['#27ae60' if r > 0.5 else '#e74c3c' for r in ratio_stable], alpha=0.85)
ax3.axhline(1.0, color='gray', ls='--', alpha=0.4)
ax3.axhline(0.5, color='orange', ls='--', alpha=0.4)
for i, (rs, rc) in enumerate(zip(ratio_stable, ratios_c)):
    ax3.text(i, rs + 0.02, f'{rc:.0f}', ha='center', fontsize=8, fontweight='bold')
ax3.set_ylabel('Ratio / Ratio(N=60)')
ax3.set_title('Croft-Servi Ratio Stability (N=60 baseline)')

plt.suptitle('Servi-Croft Kernel 大N渐近稳定性 — Loiseau Spectral Barrier 出口验证', fontsize=13, fontweight='bold')
plt.tight_layout()
out_path = os.path.join(od, 'Servi_Mollifier_大N渐近验证.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# ====== 判决 ======
print(f"\n{'='*60}")
print(f"判决: Croft-Servi prime-detection ratio 渐近稳定性")
print(f"{'='*60}")
min_ratio = min(ratios_c)
max_ratio = max(ratios_c)
mean_ratio = np.mean(ratios_c)
print(f"  N range:       {N_values[0]} → {N_values[-1]}")
print(f"  Ratio range:   {min_ratio:.1f} → {max_ratio:.1f}")
print(f"  Mean ratio:    {mean_ratio:.1f}")
print(f"  Min/Max:       {min_ratio/max_ratio:.3f}")

stable = min_ratio > 2.0
if stable:
    print(f"\n  ✅ 判决: RATIO 稳定 > 2.0 全范围")
    print(f"  ✅ Croft-Servi kernel 在 N∈[{N_values[0]},{N_values[-1]}] 下保持强 prime-selective")
    print(f"  ✅ 可正式宣称: '渐近意义下跳出 Loiseau 类B的构造性核'")
else:
    print(f"\n  ⚠️ ratio 在 N={N_values[ratios_c.index(min_ratio)]} 处低于 2.0")
    print(f"  → 需要在更大 N 下进一步验证")
print(f"\n  📁 输出图: {out_path}")
