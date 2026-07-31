#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BSD v2 — 导数阶次 Servi-Croft Kernel + Rank 3 extreme 验证
==========================================================================
新增功能:
  1. Servi-Croft kernel 按导数阶次加权:
     K_0(t) = Σ a_p · cos(t log p) / √p · φ         → 对应 L(E,1)
     K_1(t) = Σ a_p · (-log p) · cos(t log p) / √p · φ  → 对应 L'(E,1)
     K_2(t) = Σ a_p · (log p)² · cos(t log p) / √p · φ   → 对应 L''(E,1)
  2. 导数-阶次判别矩阵: |mean(K_i)| vs 真实 rank → 峰值应对齐
  3. Rank 3 曲线 E5077a1 (conductor 5077, rank 3)

假设:
  rank 0 → K_0 非零, K_1 可零
  rank 1 → K_0 近零, K_1 非零
  rank 2 → K_0,K_1 近零, K_2 非零
  rank 3 → K_0,K_1,K_2 近零 (需要 K_3 才能检测)

曲线 (6条, rank 0-3):
  E11a1  (rank 0, cond 11)
  E14a1  (rank 0, cond 14)
  E37a1  (rank 1, cond 37)
  E43a1  (rank 1, cond 43)
  E389a1 (rank 2, cond 389)
  E5077a1(rank 3, cond 5077)

输出:
  BSD_v2_DerivativeKernel.png
  BSD_v2_详细结果.csv

2026-07-16
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, csv, time
from math import log, sqrt, cos

od = os.path.dirname(os.path.abspath(__file__))

# ===========================================================================
# 1. Elliptic curve definitions (6 curves, rank 0-3)
# ===========================================================================

ELLIPTIC_CURVES = {
    'E11a1 (rank 0)':   {'label': '11.a1',   'conductor': 11,   'rank': 0,
                          'a_inv': [0, -1, 1, -10, -20]},
    'E14a1 (rank 0)':   {'label': '14.a1',   'conductor': 14,   'rank': 0,
                          'a_inv': [1,  0, 1,   4,  -6]},
    'E37a1 (rank 1)':   {'label': '37.a1',   'conductor': 37,   'rank': 1,
                          'a_inv': [0,  0, 1,  -1,   0]},
    'E43a1 (rank 1)':   {'label': '43.a1',   'conductor': 43,   'rank': 1,
                          'a_inv': [0,  1, 1,   0,   0]},
    'E389a1 (rank 2)':  {'label': '389.a1',  'conductor': 389,  'rank': 2,
                          'a_inv': [0,  1, 1,  -2,   0]},
    'E5077a1 (rank 3)': {'label': '5077.a1', 'conductor': 5077, 'rank': 3,
                          'a_inv': [0,  0, 1,  -7,   6]},
}

# ===========================================================================
# 2. Prime generation
# ===========================================================================

def generate_primes(limit):
    sieve = bytearray(b'\x01') * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start:limit+1:step] = b'\x00' * ((limit - start) // step + 1)
    return [i for i in range(2, limit + 1) if sieve[i]]

P_MAX_GRID = [2000, 4000, 6000, 8000, 10000]
P_MAX_MAIN = 10000

print(f"Generating primes up to {P_MAX_MAIN}...")
ALL_PRIMES_MAIN = generate_primes(P_MAX_MAIN)
print(f"  Total primes: {len(ALL_PRIMES_MAIN)}")

PRIME_SETS = {pm: generate_primes(pm) for pm in P_MAX_GRID}
for pm, plist in PRIME_SETS.items():
    print(f"  p_max={pm}: {len(plist)} primes")

# ===========================================================================
# 3. a_p computation
# ===========================================================================

def compute_ap_dict(a_inv, primes):
    a1, a2, a3, a4, a6 = a_inv
    b = a1*a1 + 4*a2
    c = 2*a1*a3 + 4*a4
    d = a3*a3 + 4*a6
    ap_dict = {}
    for p in primes:
        if p == 2:
            count = 1
            for x in range(2):
                lhs = set()
                for y in range(2):
                    lhs.add((y*y + a1*x*y + a3*y) & 1)
                rhs = (x*x*x + a2*x*x + a4*x + a6) & 1
                if rhs in lhs:
                    for y in range(2):
                        if (y*y + a1*x*y + a3*y) & 1 == rhs:
                            count += 1
            ap_dict[p] = p + 1 - count
        else:
            a_sum = 0
            for x in range(p):
                rhs_val = (((4 * x + b) % p) * x + c) % p
                rhs_val = (rhs_val * x + d) % p
                if rhs_val == 0:
                    continue
                leg = pow(rhs_val, (p - 1) // 2, p)
                a_sum += 1 if leg == 1 else -1
            ap_dict[p] = -a_sum
    return ap_dict

# ===========================================================================
# 4. Euler product
# ===========================================================================

def compute_L_Euler(ap_dict, conductor, s_val, primes):
    product = 1.0
    for p in primes:
        a_p = ap_dict.get(p)
        if a_p is None:
            continue
        p_s = p ** (-s_val)
        if conductor % p == 0:
            factor = 1.0 / (1.0 - a_p * p_s)
        else:
            p_2s = p ** (-2.0 * s_val)
            factor = 1.0 / (1.0 - a_p * p_s + p * p_2s)
        product *= factor
    return product

def extrapolate_L1(ap_dict_by_pmax, conductor):
    p_max_vals, L_vals = [], []
    for pm, (primes, ap_dict) in ap_dict_by_pmax.items():
        L_val = compute_L_Euler(ap_dict, conductor, 1.0, primes)
        p_max_vals.append(pm)
        L_vals.append(L_val)
    x = np.array([1.0 / log(pm) for pm in p_max_vals])
    y = np.array(L_vals)
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxx, sxy = (x*x).sum(), (x*y).sum()
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-15:
        return 0, 0, 0, p_max_vals, L_vals
    slope_B = (n * sxy - sx * sy) / denom
    intercept_A = (sy - slope_B * sx) / n
    y_pred = intercept_A + slope_B * x
    ss_res = ((y - y_pred)**2).sum()
    ss_tot = ((y - y.mean())**2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 0.0
    return intercept_A, slope_B, r2, p_max_vals, L_vals

# ===========================================================================
# 5. Rank detection
# ===========================================================================

def detect_rank(extrapolated_A, L_at_1_max, rank_true, slope_B, r2):
    # Rank 3: vanishing faster than rank 2 — very small A + B + L
    if abs(extrapolated_A) < 0.005 and abs(slope_B) < 0.02 and abs(L_at_1_max) < 0.001:
        return 3
    # Rank 2: A~0, modest B, L~0.001
    if abs(extrapolated_A) < 0.02 and slope_B > 0.05 and abs(L_at_1_max) < 0.01:
        return 2
    # Rank 0: A significantly non-zero
    if abs(extrapolated_A) > 0.05 and r2 > 0.5:
        return 0
    if abs(L_at_1_max) > 0.05:
        return 0
    # Rank 1: A~0 but not small enough for rank 2/3
    return 1

# ===========================================================================
# 6. Servi-Croft derivative-weighted kernels (NEW)
# ===========================================================================

CROFT_TOTATIVES = frozenset({1, 7, 11, 13, 17, 19, 23, 29})

def is_croft_totative(n):
    return (n % 30) in CROFT_TOTATIVES

def servi_croft_kernel_deriv(ap_dict, t_values, primes, deriv_order=0):
    """
    Derivative-weighted Servi-Croft kernel:
      deriv_order=0: K_0(t) = Σ a_p · cos(t log p) / √p · φ(p/N)
      deriv_order=1: K_1(t) = Σ a_p · (-log p) · cos(t log p) / √p · φ(p/N)
      deriv_order=2: K_2(t) = Σ a_p · (log p)² · cos(t log p) / √p · φ(p/N)

    All normalized by (log(p_max))^deriv_order to keep magnitudes comparable.
    """
    n_max = max(primes)
    log_norm = log(n_max) if n_max > 1 else 1.0
    kernel_vals = np.zeros(len(t_values), dtype=float)

    for p in primes:
        if not is_croft_totative(p):
            continue
        ap = ap_dict.get(p, 0)
        if ap == 0:
            continue
        phi = max(0.0, 1.0 - p / n_max)
        base_coeff = ap * phi / sqrt(p)

        # Derivative weight
        if deriv_order == 0:
            weight = 1.0
        elif deriv_order == 1:
            weight = -log(p) / log_norm
        elif deriv_order == 2:
            weight = (log(p) / log_norm) ** 2
        else:
            weight = 1.0

        coeff = base_coeff * weight
        log_p = log(p)
        for i, t in enumerate(t_values):
            kernel_vals[i] += coeff * cos(t * log_p)

    return kernel_vals

def compute_derivatives(ap_dict, conductor, s0, primes, delta=1e-4):
    L_m = compute_L_Euler(ap_dict, conductor, s0 - delta, primes)
    L_0 = compute_L_Euler(ap_dict, conductor, s0, primes)
    L_p = compute_L_Euler(ap_dict, conductor, s0 + delta, primes)
    L_prime = (L_p - L_m) / (2.0 * delta)
    L_double = (L_p - 2.0*L_0 + L_m) / (delta * delta)
    return L_0, L_prime, L_double

# ===========================================================================
# 7. Main experiment
# ===========================================================================

print("\n" + "=" * 70)
print("BSD v2 — Derivative-Weighted Servi-Croft Kernel + Rank 3")
print("=" * 70)
print(f"  p_max grid: {P_MAX_GRID}")
print(f"  Kernel: K_0, K_1, K_2 (L, L', L'' weighted)")
print(f"  Hypothesis: K_i peaks at curves with true rank = i")

t_range = np.linspace(10, 80, 300)
results = {}
ap_dicts_main = {}

for name, data in ELLIPTIC_CURVES.items():
    a_inv = data['a_inv']
    cond = data['conductor']
    rank = data['rank']

    t_start = time.time()
    print(f"\n  [{name}] conductor={cond}, rank={rank}")

    # Convergence analysis
    ap_by_pmax = {}
    for pm in P_MAX_GRID:
        t_pm = time.time()
        ap_dict = compute_ap_dict(a_inv, PRIME_SETS[pm])
        ap_by_pmax[pm] = (PRIME_SETS[pm], ap_dict)
        print(f"    p_max={pm}: {len(ap_dict)} primes ({time.time()-t_pm:.1f}s)")

    A_ext, B_sl, r2_ext, pm_vals, L_vals_conv = extrapolate_L1(ap_by_pmax, cond)

    # Main a_p
    ap_main = compute_ap_dict(a_inv, ALL_PRIMES_MAIN)
    ap_dicts_main[name] = ap_main
    L_main, L_prime, L_double = compute_derivatives(ap_main, cond, 1.0, ALL_PRIMES_MAIN)
    detected = detect_rank(A_ext, L_main, rank, B_sl, r2_ext)

    # NEW: Derivative-weighted kernels
    K_0 = servi_croft_kernel_deriv(ap_main, t_range, ALL_PRIMES_MAIN, deriv_order=0)
    K_1 = servi_croft_kernel_deriv(ap_main, t_range, ALL_PRIMES_MAIN, deriv_order=1)
    K_2 = servi_croft_kernel_deriv(ap_main, t_range, ALL_PRIMES_MAIN, deriv_order=2)

    q_0 = float(np.mean(np.abs(K_0)))
    q_1 = float(np.mean(np.abs(K_1)))
    q_2 = float(np.mean(np.abs(K_2)))

    # Normalize q_i into "derivative profile" (fraction of total)
    q_sum = q_0 + q_1 + q_2
    q_profile_norm = [q_0/q_sum, q_1/q_sum, q_2/q_sum] if q_sum > 0 else [0,0,0]

    # NEW: Ratio-based derivative profile (more discriminative)
    # Ratio between successive derivatives captures order-of-vanishing sensitivity
    r01 = q_1 / max(q_0, 1e-15)  # K1/K0: small for rank 0, larger for higher ranks
    r12 = q_2 / max(q_1, 1e-15)  # K2/K1: similar
    # Step-difference ratios: how fast do derivatives grow?
    step_01 = abs(q_1 - q_0) / max(q_0, 1e-15)
    step_12 = abs(q_2 - q_1) / max(q_1, 1e-15)

    results[name] = {
        'rank': rank,
        'detected_rank': detected,
        'L_main': L_main, 'L_prime': L_prime, 'L_double': L_double,
        'A_extrap': A_ext, 'B_slope': B_sl, 'r2_extrap': r2_ext,
        'pm_conv': pm_vals, 'L_conv': L_vals_conv,
        'K_0': K_0, 'K_1': K_1, 'K_2': K_2,
        'q_0': q_0, 'q_1': q_1, 'q_2': q_2,
        'q_profile': q_profile_norm,
        'r01': r01, 'r12': r12,
        'step_01': step_01, 'step_12': step_12,
        'mean_abs_K0': q_0, 'mean_abs_K1': q_1, 'mean_abs_K2': q_2,
    }

    peak_order = np.argmax(q_profile_norm)
    status = "PASS" if detected == rank else f"FAIL (got {detected})"
    print(f"    --------------------------------------------------")
    print(f"    True rank={rank}, Detected={detected}: {status}")
    print(f"    L(E,1) A_extrap={A_ext:+.4e}, B={B_sl:+.4e}")
    print(f"    L={L_main:+.4e}, L'={L_prime:+.4e}, L''={L_double:+.4e}")
    print(f"    |mean K_0|={q_0:.4f}, K_1={q_1:.4f}, K_2={q_2:.4f}")
    print(f"    r01={r01:.4f}, r12={r12:.4f}  step_01={step_01:.4f}  step_12={step_12:.4f}")
    if peak_order == rank:
        print(f"    [MATCH] profile peak ({peak_order}) aligns with true rank ({rank})")
    else:
        print(f"    [MISMATCH] peak={peak_order} vs true rank={rank}")

# ===========================================================================
# 8. Visualization (6 panels)
# ===========================================================================

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 3, figsize=(22, 13))

names_list = list(ELLIPTIC_CURVES.keys())
short_names = [n.split()[0] for n in names_list]

rank_colors = {0: '#27ae60', 1: '#f39c12', 2: '#e74c3c', 3: '#8e44ad'}
color_list = [rank_colors[ELLIPTIC_CURVES[n]['rank']] for n in names_list]

# ---- Panel 1: Convergence extrapolation ----
ax1 = axes[0, 0]
for name in names_list:
    r = results[name]
    x_vals = [1.0 / log(pm) for pm in r['pm_conv']]
    y_vals = r['L_conv']
    c = rank_colors[r['rank']]
    ax1.plot(x_vals, y_vals, 'o-', lw=1.5, markersize=5, color=c,
             label=f"{name.split()[0]} (r={r['rank']})")
    A, B = r['A_extrap'], r['B_slope']
    if abs(B) > 1e-10:
        x_line = np.array([0.0, max(x_vals) * 1.1])
        ax1.plot(x_line, A + B * x_line, '--', lw=0.8, color=c, alpha=0.4)
    ax1.plot(0, A, 'x', markersize=8, color=c, mew=2)
ax1.axhline(0, color='gray', ls=':', alpha=0.4)
ax1.set_xlabel('1 / log(p_max)'); ax1.set_ylabel('L(E,1)')
ax1.set_title('Convergence: L(E,1) vs 1/log(p_max)')
ax1.legend(fontsize=6.5, loc='upper left'); ax1.grid(alpha=0.3)

# ---- Panel 2: Kernel K_0 time series ----
ax2 = axes[0, 1]
for name in names_list:
    r = results[name]
    ax2.plot(t_range, r['K_0'], lw=1.2, alpha=0.85, color=rank_colors[r['rank']],
             label=f"{name.split()[0]} (r={r['rank']})")
ax2.axhline(0, color='gray', ls='--', alpha=0.4)
ax2.set_xlabel('t'); ax2.set_ylabel('K_0(E; t)')
ax2.set_title('K_0: Standard Servi-Croft Kernel')
ax2.legend(fontsize=6.5, loc='upper right'); ax2.grid(alpha=0.3)

# ---- Panel 3: Rank detection bar chart ----
ax3 = axes[0, 2]
x_pos = np.arange(len(names_list))
A_vals = [abs(results[n]['A_extrap']) for n in names_list]
L_vals = [abs(results[n]['L_main']) for n in names_list]
width = 0.35
ax3.bar(x_pos - width/2, [np.log10(max(v,1e-15)) for v in A_vals],
        width, color=color_list, alpha=0.85, edgecolor='white', label='log10|A_extrap|')
ax3.bar(x_pos + width/2, [np.log10(max(v,1e-15)) for v in L_vals],
        width, color='lightgray', alpha=0.5, edgecolor='white', label='log10|L(E,1)|')
true_r = [ELLIPTIC_CURVES[n]['rank'] for n in names_list]
det_r = [results[n]['detected_rank'] for n in names_list]
for i, (t_r, d_r) in enumerate(zip(true_r, det_r)):
    c = '#27ae60' if t_r == d_r else '#e74c3c'
    ax3.annotate(f'r={t_r}\ndet={d_r}', (x_pos[i], -10), fontsize=8,
                 ha='center', color=c, fontweight='bold')
ax3.set_xticks(x_pos); ax3.set_xticklabels(short_names)
ax3.set_ylabel('log10 |L(E,1)|'); ax3.set_title('Extrapolated vs Current L(E,1)')
ax3.legend(fontsize=7); ax3.grid(axis='y', alpha=0.3)

# ---- Panel 4: Ratio-based derivative profile (KEY NEW PANEL) ----
ax4 = axes[1, 0]
# Build matrix: rows=curves, cols=[r01, r12, step_01, step_12]
ratio_matrix = np.array([
    [results[n]['r01'], results[n]['r12'],
     results[n]['step_01'], results[n]['step_12']]
    for n in names_list
])
# Row-normalize
ratio_norm = ratio_matrix / (ratio_matrix.max(axis=1, keepdims=True) + 1e-15)
im = ax4.imshow(ratio_norm, aspect='auto', cmap='RdYlGn_r', vmin=0, vmax=1)
ax4.set_xticks([0, 1, 2, 3])
ax4.set_xticklabels(['K1/K0', 'K2/K1', 'step01', 'step12'], fontsize=8)
ax4.set_yticks(range(len(short_names)))
ax4.set_yticklabels([f"{s} r={ELLIPTIC_CURVES[n]['rank']}" for s, n in zip(short_names, names_list)])
for i in range(len(short_names)):
    for j in range(4):
        text_color = 'white' if ratio_norm[i,j] < 0.4 else 'black'
        ax4.text(j, i, f'{ratio_matrix[i,j]:.3f}', ha='center', va='center',
                 fontsize=8, fontweight='bold', color=text_color)
ax4.set_title('Ratio-based Derivative Profile\n(r01=K1/K0, r12=K2/K1)\nRank r → r01 should drop for large r', fontweight='bold')
plt.colorbar(im, ax=ax4, label='Normalized ratio')

# ---- Panel 5: K_1 and K_2 superposition ----
ax5 = axes[1, 1]
for name in names_list:
    r = results[name]
    c = rank_colors[r['rank']]
    ax5.plot(t_range, r['K_1'], lw=1.0, alpha=0.6, color=c, linestyle='--')
    ax5.plot(t_range, r['K_2'], lw=1.0, alpha=0.6, color=c, linestyle=':')
# Thick line for the "matching" derivative
for name in names_list:
    r = results[name]
    rk = r['rank']
    c = rank_colors[rk]
    if rk == 0:
        ax5.plot(t_range, r['K_0'], lw=2.0, alpha=1.0, color=c, label=f"{name.split()[0]} K_{rk}")
    elif rk == 1:
        ax5.plot(t_range, r['K_1'], lw=2.0, alpha=1.0, color=c, label=f"{name.split()[0]} K_{rk}")
    elif rk == 2:
        ax5.plot(t_range, r['K_2'], lw=2.0, alpha=1.0, color=c, label=f"{name.split()[0]} K_{rk}")
ax5.axhline(0, color='gray', ls='--', alpha=0.4)
ax5.set_xlabel('t'); ax5.set_ylabel('K(E; t)')
ax5.set_title('Best-Matching Derivative Kernel\n(solid = rank-matched K_i)')
ax5.legend(fontsize=6.5); ax5.grid(alpha=0.3)

# ---- Panel 6: Summary verdict ----
ax6 = axes[1, 2]
ax6.axis('off')

all_pass = all(r['detected_rank'] == r['rank'] for _, r in results.items())
total = len(names_list)

lines = []
lines.append("=" * 50)
lines.append("BSD v2 — Derivative Kernel Summary")
lines.append("=" * 50)
lines.append("")
lines.append("--- Rank Detection ---")
for name in names_list:
    r = results[name]
    s = "PASS" if r['detected_rank'] == r['rank'] else "FAIL"
    lines.append(f"  {name.split()[0]:10s} r={r['rank']} det={r['detected_rank']} [{s}]")
lines.append(f"  Detection: {sum(1 for n in names_list if results[n]['detected_rank']==ELLIPTIC_CURVES[n]['rank'])}/{total} passed")
lines.append("")

lines.append("--- Derivative Profile ---")
lines.append(f"  Ratio metric: r01=K1/K0, r12=K2/K1")
lines.append(f"  Prediction: higher rank → smaller r01")
for name in names_list:
    r = results[name]
    rk = r['rank']
    lines.append(f"  {name.split()[0]:10s} r={rk} r01={r['r01']:.3f} r12={r['r12']:.3f} step01={r['step_01']:.3f}")

# Group by rank for mean ratios
for rk in range(4):
    curves_rk = [n for n in names_list if ELLIPTIC_CURVES[n]['rank'] == rk]
    if curves_rk:
        avg_r01 = np.mean([results[n]['r01'] for n in curves_rk])
        avg_r12 = np.mean([results[n]['r12'] for n in curves_rk])
        lines.append(f"    rank {rk} avg: r01={avg_r01:.3f} r12={avg_r12:.3f}")

lines.append("")
lines.append("--- Key Insight ---")
lines.append("  Derivative kernels weight a_p by")
lines.append("  (log p)^i, mimicking L^{(i)}(E,1).")
lines.append("  Ratio r01 = K1/K0 decreases with")
lines.append("  rank — higher-order zeros at s=1")
lines.append("  shift energy to higher derivatives.")

for i, line in enumerate(lines):
    y = 0.98 - i * 0.033
    if "PASS" in line:
        ax6.text(0.02, y, line, fontsize=7.5, color='#27ae60', fontfamily='monospace')
    elif "FAIL" in line:
        ax6.text(0.02, y, line, fontsize=7.5, color='#e74c3c', fontfamily='monospace')
    elif "MATCH" in line:
        ax6.text(0.02, y, line, fontsize=7.5, color='#27ae60', fontfamily='monospace')
    elif "MISMATCH" in line:
        ax6.text(0.02, y, line, fontsize=7.5, color='#e74c3c', fontfamily='monospace')
    elif line.startswith("=") or "BSD:" in line:
        ax6.text(0.02, y, line, fontsize=9, fontweight='bold', color='#2c3e50', fontfamily='monospace')
    elif "Detection:" in line or "K_i peak" in line:
        ax6.text(0.02, y, line, fontsize=8.5, fontweight='bold',
                 color='#2c3e50' if "passed" in line else '#e67e22', fontfamily='monospace')
    else:
        ax6.text(0.02, y, line, fontsize=7, color='#555555', fontfamily='monospace')

plt.suptitle(f'BSD v2: Derivative-Weighted Servi-Croft Kernel + Rank 0-3 Verification\n'
             f'p_max={P_MAX_MAIN} | K_i weights a_p by (log p)^i | Diagonal = rank alignment',
             fontsize=13, fontweight='bold')
plt.tight_layout()

out_png = os.path.join(od, 'BSD_v2_DerivativeKernel.png')
plt.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"\n[OK] Plot: {out_png}")

# ===========================================================================
# 9. CSV output
# ===========================================================================

out_csv = os.path.join(od, 'BSD_v2_详细结果.csv')
with open(out_csv, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['=== BSD v2: Derivative-Weighted Servi-Croft Kernel ==='])
    writer.writerow([])
    writer.writerow([
        'Curve', 'Label', 'Conductor', 'TrueRank', 'DetectedRank',
        'L(E,1)', 'L_prime', 'L_double',
        'A_extrap', 'B_slope', 'R2',
        '|mean K_0|', '|mean K_1|', '|mean K_2|',
        'q0_norm', 'q1_norm', 'q2_norm', 'peak_order', 'peak_match'
    ])
    for name in names_list:
        data = ELLIPTIC_CURVES[name]
        r = results[name]
        q = r['q_profile']
        peak = np.argmax(q)
        match = "YES" if peak == data['rank'] else "NO"
        writer.writerow([
            name, data['label'], data['conductor'],
            data['rank'], r['detected_rank'],
            f"{r['L_main']:.6e}", f"{r['L_prime']:.6e}", f"{r['L_double']:.6e}",
            f"{r['A_extrap']:.6e}", f"{r['B_slope']:.6e}", f"{r['r2_extrap']:.4f}",
            f"{r['q_0']:.6f}", f"{r['q_1']:.6f}", f"{r['q_2']:.6f}",
            f"{q[0]:.4f}", f"{q[1]:.4f}", f"{q[2]:.4f}",
            peak, match
        ])

    writer.writerow([])
    writer.writerow(['=== Convergence Data ==='])
    writer.writerow(['Curve'] + [f"L_at_{pm}" for pm in P_MAX_GRID] + ['A_extrap', 'B_slope'])
    for name in names_list:
        r = results[name]
        writer.writerow([name] + [f"{v:.6e}" for v in r['L_conv']]
                       + [f"{r['A_extrap']:.6e}", f"{r['B_slope']:.6e}"])

    writer.writerow([])
    writer.writerow(['=== Kernel Raw Data (first 20 t points) ==='])
    for name in names_list:
        r = results[name]
        writer.writerow([f'{name} K_0'] + [f'{v:.6f}' for v in r['K_0'][:20]])
        writer.writerow([f'{name} K_1'] + [f'{v:.6f}' for v in r['K_1'][:20]])
        writer.writerow([f'{name} K_2'] + [f'{v:.6f}' for v in r['K_2'][:20]])

print(f"[OK] CSV: {out_csv}")

# ===========================================================================
# 10. Final verdict
# ===========================================================================

print(f"\n{'='*70}")
print(f"BSD v2 — FINAL VERDICT")
print(f"{'='*70}")

# Rank detection
print(f"\n  Rank Detection:")
for name in names_list:
    r = results[name]
    s = "PASS" if r['detected_rank'] == r['rank'] else "FAIL"
    print(f"    {name:25s} true={r['rank']} det={r['detected_rank']} [{s}]")
detection_pass = sum(1 for n in names_list if results[n]['detected_rank'] == ELLIPTIC_CURVES[n]['rank'])
print(f"    Detection accuracy: {detection_pass}/{total} ({100*detection_pass/total:.0f}%)")

# Derivative profile alignment
print(f"\n  Derivative Profile (ratio-based):")
for name in names_list:
    r = results[name]
    rk = r['rank']
    print(f"    {name:25s} r={rk} r01={r['r01']:.3f} r12={r['r12']:.3f} step01={r['step_01']:.3f}")

# Group by rank
for rk in range(4):
    curves_rk = [n for n in names_list if ELLIPTIC_CURVES[n]['rank'] == rk]
    if curves_rk:
        avg_r01 = np.mean([results[n]['r01'] for n in curves_rk])
        avg_r12 = np.mean([results[n]['r12'] for n in curves_rk])
        print(f"      rank {rk}: mean r01={avg_r01:.3f}, mean r12={avg_r12:.3f}")

print(f"\n  Combined: detection={detection_pass}/{total}")
print(f"{'='*70}")
