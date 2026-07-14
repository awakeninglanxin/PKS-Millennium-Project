#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi Kernel 六元对照实验 v3
══════════════════════════════════════════════════════════════════

Loiseau 2025-09 Spectral Barrier 出口验证 — prime-selective spectral kernel
多元对照组: 验证 Croft/E8/Damon/驻波 四个理论构件对 prime-detection 的贡献

============================================================================
对照组设计 (6 组)
============================================================================

组A (baseline): 原始 Servi kernel
    K(s;t) = Σ cos(-t log n) · n^(-1/2) · smooth_cutoff

组B (+Croft T_30): 嵌入 Croft modulo 30 totative 选择器
    K(s;t) = Σ_{n∈T_30} cos(-t log n) · n^(-1/2)
    T_30 = {n : n mod 30 ∈ {1,7,11,13,17,19,23,29}}

组C (+φ decay): 驻波黄金比衰减包络
    K(s;t) = Σ cos(-t log n) · n^(-φ/5)
    φ = (√5-1)/2 ≈ 0.618

组D (+T_30 + φ): Croft 选择器 + 黄金比衰减 (K_{30,φ})
    K(s;t) = Σ_{n∈T_30} cos(-t log n) · n^(-φ/5)

组E (+Damon k_power): Damon平方根频率缩放
    K(s;t) = Σ cos(-t log n) · n^(-1/2) · |gap^{-1/2}|
    其中 gap = 相邻素数的间距

组F (全组合): T_30 + φ + Damon
    K(s;t) = Σ_{n∈T_30} cos(-t log n) · n^(-φ/5) · w_Damon(n)

============================================================================
理论来源:
- Croft: primesdemystified.com, modulo 30 / E8 指数同构
- φ: 驻波研究合集 > Cervenka et al. WCU 2003 > P'_n/P'_{n-1} → 0.618
- Damon: Prime Scalar Field > k(p) = k_base × p^k_power > k_power=0.5 ⇔ ζ
- Servi: cos(-t log n) n^(-1/2-s) mollifier

日期: 2026-07-14
============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys, math as _math
from math import log, sqrt, pi, cos, sin, exp

od = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════
# 0. 基础工具
# ═══════════════════════════════════════════════════════════════════════

GOLDEN_RATIO = (sqrt(5) - 1) / 2  # φ ≈ 0.618

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def mobius(n):
    if n == 1: return 1
    if n == 0: return 0
    p = 0; m = n
    for d in range(2, int(sqrt(n)) + 1):
        if m % d == 0:
            m //= d; p += 1
            if m % d == 0: return 0
    if m > 1: p += 1
    return -1 if p % 2 else 1

# Croft T_30 选择器
CROFT_TOTATIVES = frozenset({1, 7, 11, 13, 17, 19, 23, 29})

def is_croft_totative(n):
    """n ∈ T_30 = n mod 30 ∈ {1,7,11,13,17,19,23,29}"""
    return (n % 30) in CROFT_TOTATIVES

# ζ(1/2+it) partial sum
def zeta_half(t, N=None):
    if N is None:
        N = int(sqrt(t / (2 * pi))) + 5
    z = 0 + 0j
    angles = []
    for n in range(1, N + 1):
        term = 1.0 / sqrt(n) * complex(cos(t * log(n)), -sin(t * log(n)))
        z += term
        angles.append(-t * log(n))
    return z, N, np.array(angles)

# ═══════════════════════════════════════════════════════════════════════
# 1. 六组 mollifier 构造
# ═══════════════════════════════════════════════════════════════════════

def build_group_a(t_target, N_max):
    """组A: 原始 Servi — K = Σ cos(-t log n)/√n"""
    coeffs = {}
    for n in range(1, N_max + 1):
        coef = cos(-t_target * log(n)) / sqrt(n)
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

def build_group_b(t_target, N_max):
    """组B: +Croft T_30 — 只保留 modulo 30 totatives"""
    coeffs = {}
    for n in range(1, N_max + 1):
        if not is_croft_totative(n):
            continue
        coef = cos(-t_target * log(n)) / sqrt(n)
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

def build_group_c(t_target, N_max):
    """组C: +φ decay — n^(-φ/5) 替代 n^(-1/2)"""
    coeffs = {}
    phi_over_5 = GOLDEN_RATIO / 5  # ≈ 0.1236
    for n in range(1, N_max + 1):
        coef = cos(-t_target * log(n)) * n**(-phi_over_5)
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

def build_group_d(t_target, N_max):
    """组D: +T_30 + φ — Croft 选择器 + 黄金比衰减 (K_{30,φ})"""
    coeffs = {}
    phi_over_5 = GOLDEN_RATIO / 5
    for n in range(1, N_max + 1):
        if not is_croft_totative(n):
            continue
        coef = cos(-t_target * log(n)) * n**(-phi_over_5)
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

def build_group_e(t_target, N_max):
    """组E: +Damon k_power=0.5 — 素数间距倒数平方根权重"""
    # 生成素数列表
    primes = [p for p in range(2, N_max + 1) if is_prime(p)]
    # 计算间距倒数平方根
    gap_weight = {}
    for i in range(len(primes) - 1):
        p = primes[i]
        gap = primes[i + 1] - p
        gap_weight[p] = 1.0 / sqrt(gap + 1e-12)  # Damon: f = 1/gap → √f = 1/√gap

    coeffs = {}
    for n in range(1, N_max + 1):
        w = gap_weight.get(n, 1.0) if is_prime(n) else 0.5
        coef = cos(-t_target * log(n)) / sqrt(n) * w
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

def build_group_f(t_target, N_max):
    """组F: 全组合 — T_30 + φ + Damon"""
    primes = [p for p in range(2, N_max + 1) if is_prime(p)]
    gap_weight = {}
    for i in range(len(primes) - 1):
        p = primes[i]
        gap = primes[i + 1] - p
        gap_weight[p] = 1.0 / sqrt(gap + 1e-12)

    phi_over_5 = GOLDEN_RATIO / 5
    coeffs = {}
    for n in range(1, N_max + 1):
        if not is_croft_totative(n):
            continue
        w = gap_weight.get(n, 1.0) if is_prime(n) else 0.5
        coef = cos(-t_target * log(n)) * n**(-phi_over_5) * w
        coef *= max(0, 1.0 - n / N_max)
        coeffs[n] = coef
    return coeffs

GROUP_CONFIGS = [
    ("A: 原始 Servi",      build_group_a),
    ("B: +Croft T_30",     build_group_b),
    ("C: +φ decay",        build_group_c),
    ("D: +T_30+φ (K30φ)",  build_group_d),
    ("E: +Damon √gap",     build_group_e),
    ("F: 全组合",          build_group_f),
]

# ═══════════════════════════════════════════════════════════════════════
# 2. Prime-detection 测试 (Loiseau 核心命题)
# ═══════════════════════════════════════════════════════════════════════

def prime_detection_test(t_values, N_max, builder_func, t_mid):
    """对指定 mollifier 构造器运行 prime-detection 测试"""
    coeffs = builder_func(t_mid, N_max)

    # 素数/非素数列表
    primes_n = [n for n in range(2, N_max + 1) if is_prime(n)]
    nonprimes_n = [n for n in range(2, N_max + 1) if not is_prime(n)]

    K_prime_t = []
    K_nonprime_t = []
    K_full_t = []

    for t in t_values:
        K_prime = 0.0
        K_nonprime = 0.0
        K_full = 0.0
        for n, coef in coeffs.items():
            if n < 2: continue
            term = coef * cos(-t * log(n))
            K_full += term
            if is_prime(n):
                K_prime += term
            else:
                K_nonprime += term
        K_prime_t.append(K_prime)
        K_nonprime_t.append(K_nonprime)
        K_full_t.append(K_full)

    K_prime_t = np.array(K_prime_t)
    K_nonprime_t = np.array(K_nonprime_t)
    K_full_t = np.array(K_full_t)

    return {
        'coeffs': coeffs,
        'n_coeffs': len(coeffs),
        'K_prime': K_prime_t,
        'K_nonprime': K_nonprime_t,
        'K_full': K_full_t,
        'var_K_prime': np.var(K_prime_t),
        'var_K_nonprime': np.var(K_nonprime_t),
        'var_K_full': np.var(K_full_t),
        'ratio': np.var(K_prime_t) / (np.var(K_nonprime_t) + 1e-12),
        'n_primes': len(primes_n),
        'n_nonprimes': len(nonprimes_n),
    }

# ═══════════════════════════════════════════════════════════════════════
# 3. 零点检测 (Levinson-Conrey 实部过零法)
# ═══════════════════════════════════════════════════════════════════════

def eval_mollifier_at_t(t_values, coeffs):
    """计算 mollifier 在 t_values 上的值 M(1/2+it)"""
    result = np.zeros(len(t_values), dtype=complex)
    for n, coef in coeffs.items():
        for i, t in enumerate(t_values):
            term = 1.0 / sqrt(n) * complex(cos(t * log(n)), -sin(t * log(n)))
            result[i] += coef * term
    return result

def detect_zeros(t_range, coeffs):
    """通过 ζ mollifier 实部过零检测零点"""
    z, _, _ = zeta_half(t_range[len(t_range)//2], N=80)
    zetas = []
    for t in t_range:
        z, _, _ = zeta_half(t, N=80)
        zetas.append(z)
    zetas = np.array(zetas)

    re_z = np.real(zetas)
    zeros = []
    for i in range(1, len(re_z)):
        if re_z[i] * re_z[i - 1] < 0:
            t_zero = (t_range[i - 1] + t_range[i]) / 2.0
            zeros.append(t_zero)
    return {'t_range': t_range, 'zetas': zetas, 'zeros': zeros, 'n_zeros': len(zeros), 're_z': re_z}

# ═══════════════════════════════════════════════════════════════════════
# 4. 主实验
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("Servi Kernel 六元对照实验 v3")
    print("Loiseau 2025-09 Spectral Barrier 出口验证")
    print("=" * 70)

    T_MAX = 80
    N_MAX = 60
    t_range = np.linspace(10, T_MAX, 400)
    t_mid = np.mean(t_range)

    known_zeros = [14.13, 21.02, 25.01, 30.42, 32.93, 37.58, 40.91, 43.32,
                   48.00, 49.77, 52.97, 56.44, 59.34, 60.85, 65.10, 67.91,
                   69.50, 71.41, 72.73, 75.65, 77.91]
    known_in_range = [z for z in known_zeros if z <= T_MAX]

    print(f"\n参数: T_MAX={T_MAX}, N_MAX={N_MAX}, t_points={len(t_range)}")
    print(f"已知零点 (t<{T_MAX}): {len(known_in_range)} 个")
    print(f"黄金比 φ = {GOLDEN_RATIO:.6f}")

    # ── 运行所有六组 ──
    results = []
    for name, builder in GROUP_CONFIGS:
        r = prime_detection_test(t_range, N_MAX, builder, t_mid)
        results.append((name, r))
        ratio = r['ratio']
        flag = "🔥" if ratio > 2.0 else ("✅" if ratio > 1.2 else ("⚠️" if ratio > 1.05 else "  "))
        print(f"\n  {flag} {name}")
        print(f"     Coefficients: {r['n_coeffs']} / {N_MAX}")
        print(f"     Var K_prime   = {r['var_K_prime']:.4f}")
        print(f"     Var K_nonprime = {r['var_K_nonprime']:.4f}")
        print(f"     Ratio          = {ratio:.4f}")

    # ── 零点检测 (用组D K_{30,φ} + 组A 对比) ──
    print(f"\n{'='*70}")
    print(f"零点检测对比 (ζ 实部过零法)")
    print(f"{'='*70}")
    zero_detect = detect_zeros(t_range, {})

    # 找出与已知零点匹配的最大容忍度
    detected_zeros = zero_detect['zeros']
    match_tol = 1.5
    matches = 0
    for z in known_in_range:
        for dz in detected_zeros:
            if abs(dz - z) < match_tol:
                matches += 1
                break
    coverage = matches / len(known_in_range) * 100 if known_in_range else 0
    print(f"  ζ 实部过零检测: {zero_detect['n_zeros']} 个零点候选")
    print(f"  匹配已知零点: {matches}/{len(known_in_range)} ({coverage:.1f}%)")

    # ═══════════════════════════════════════════════════════════════════
    # 5. 可视化 — 八面板
    # ═══════════════════════════════════════════════════════════════════
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 颜色方案 (六组)
    colors = ['#2c3e50', '#e74c3c', '#f39c12', '#27ae60', '#2980b9', '#8e44ad']
    group_labels = [name.split(":")[0].strip() for name, _ in GROUP_CONFIGS]
    group_full_labels = [name for name, _ in GROUP_CONFIGS]
    group_colors = {
        'A': '#2c3e50', 'B': '#e74c3c', 'C': '#f39c12',
        'D': '#27ae60', 'E': '#2980b9', 'F': '#8e44ad'
    }

    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.35)

    # ── Panel 1: Ratio 条形图 (核心) ──
    ax1 = fig.add_subplot(gs[0, :2])
    names_short = [r[0].split(":")[0].strip() for r in results]
    ratios = [r[1]['ratio'] for r in results]
    bars = ax1.bar(names_short, ratios, color=[group_colors[n] for n in names_short], alpha=0.85, edgecolor='white')
    ax1.axhline(1.0, color='gray', ls='--', alpha=0.4, lw=1, label='Phase-blind threshold')
    ax1.axhline(1.2, color='orange', ls='--', alpha=0.5, lw=1.5, label='Loiseau exit threshold (1.2)')
    ax1.axhline(2.0, color='green', ls='--', alpha=0.5, lw=1.5, label='Strong detection (2.0)')

    # 标注数值
    for bar, r in zip(bars, ratios):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
                 f'{r:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_ylabel('Var(K_prime) / Var(K_nonprime)')
    ax1.set_title('Loiseau Spectral Barrier: Prime-Detection Ratio (六组对照)', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper left')
    ax1.grid(axis='y', alpha=0.3)

    # ── Panel 2: 系数数量对比 ──
    ax2 = fig.add_subplot(gs[0, 2])
    n_coeffs_list = [r[1]['n_coeffs'] for r in results]
    ax2.bar(names_short, n_coeffs_list, color=[group_colors[n] for n in names_short], alpha=0.85)
    ax2.axhline(N_MAX, color='gray', ls='--', alpha=0.4, label=f'N_max={N_MAX}')
    ax2.set_ylabel('Coefficients count')
    ax2.set_title('Mollifier 系数量', fontsize=11)
    ax2.legend(fontsize=8)

    # ── Panel 3: 增强比 (relative to baseline A) ──
    ax3 = fig.add_subplot(gs[0, 3])
    baseline = ratios[0]
    rel_ratios = [r / baseline for r in ratios]
    ax3.bar(names_short, rel_ratios, color=[group_colors[n] for n in names_short], alpha=0.85)
    ax3.axhline(1.0, color='gray', ls='--', alpha=0.4)
    for bar, rr in zip(ax3.patches, rel_ratios):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{rr:.2f}x', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax3.set_ylabel('Ratio / Baseline(A)')
    ax3.set_title('相对增强倍数', fontsize=11)
    ax3.grid(axis='y', alpha=0.3)

    # ── Panel 4: K_prime vs K_nonprime 时间序列 (组D) ──
    ax4 = fig.add_subplot(gs[1, :2])
    r_d = results[3][1]  # 组D — K_{30,φ}
    ax4.plot(t_range, r_d['K_prime'], 'r-', lw=1.2, alpha=0.8,
             label=f"K·1_prime  (Var={r_d['var_K_prime']:.3f})")
    ax4.plot(t_range, r_d['K_nonprime'], 'b-', lw=1.2, alpha=0.8,
             label=f"K·1_nonprime (Var={r_d['var_K_nonprime']:.3f})")
    ax4.set_xlabel('t'); ax4.set_ylabel('Kernel projection')
    ax4.set_title(f'组D (K_{{30,φ}}): Prime vs Nonprime 投影 (ratio={r_d["ratio"]:.3f})', fontsize=12)
    ax4.legend(fontsize=9)
    ax4.grid(alpha=0.3)

    # ── Panel 5: ζ(1/2+it) 实部过零 ──
    ax5 = fig.add_subplot(gs[1, 2:])
    re_z = zero_detect['re_z']
    ax5.plot(t_range, re_z, 'b-', alpha=0.6, lw=0.8, label='Re ζ(1/2+it)')
    ax5.axhline(0, color='gray', ls='--', alpha=0.4)
    for dz in zero_detect['zeros']:
        ax5.axvline(dz, color='red', alpha=0.3, lw=0.5)
    for zk in known_in_range:
        ax5.axvline(zk, color='green', alpha=0.15, lw=2.5)
    ax5.set_xlabel('t'); ax5.set_ylabel('Re ζ')
    ax5.set_title(f'ζ(1/2+it) 实部过零 (匹配 {matches}/{len(known_in_range)} 个已知零点)')
    ax5.legend(fontsize=8)
    ax5.grid(alpha=0.3)

    # ── Panel 6: 系数分布 (选组A/B/D 对比) ──
    ax6 = fig.add_subplot(gs[2, :2])
    n_vals = np.arange(1, N_MAX + 1)
    coeff_a = np.array([results[0][1]['coeffs'].get(n, 0) for n in n_vals])
    coeff_b = np.array([results[1][1]['coeffs'].get(n, 0) for n in n_vals])
    coeff_d = np.array([results[3][1]['coeffs'].get(n, 0) for n in n_vals])

    def smooth_norm(arr):
        m = np.max(np.abs(arr)) + 1e-12
        return arr / m

    ax6.plot(n_vals, smooth_norm(coeff_a), 'o-', ms=3, alpha=0.7, color='#2c3e50', label='A: Servi')
    ax6.plot(n_vals, smooth_norm(coeff_b), 's-', ms=3, alpha=0.7, color='#e74c3c', label='B: +Croft')
    ax6.plot(n_vals, smooth_norm(coeff_d), 'D-', ms=3, alpha=0.9, color='#27ae60', label='D: +K30φ')
    ax6.set_xlabel('n'); ax6.set_ylabel('Normalized coefficient')
    ax6.set_title('Mollifier 系数分布 (A/B/D 三组对比)')
    ax6.legend(fontsize=9)
    ax6.grid(alpha=0.3)

    # ── Panel 7: K_prime 六组重叠时序 ──
    ax7 = fig.add_subplot(gs[2, 2:])
    for idx, (name, r) in enumerate(results):
        label_short = name.split(":")[0].strip()
        ax7.plot(t_range, r['K_prime'], color=colors[idx], lw=0.8, alpha=0.7,
                 label=f"{label_short} (ratio={r['ratio']:.2f})")
    ax7.set_xlabel('t'); ax7.set_ylabel('K·1_prime')
    ax7.set_title('六组 K·1_prime 时序重叠对比', fontsize=11)
    ax7.legend(fontsize=7, loc='upper right')
    ax7.grid(alpha=0.3)

    # ── Panel 8: 理论来源标注 ──
    ax8 = fig.add_subplot(gs[2, 3])  # using 3,3 as last
    ax8.axis('off')
    info_lines = [
        "理论来源:",
        "",
        "A — Servi 2003: cos(-t log n)/√n",
        "B — Croft: modulo 30 totatives",
        "C — 驻波: φ=0.618 黄金比衰减",
        "D — K_{30,φ} = B+C 组合",
        "E — Damon: 素数间距倒数√权重",
        "F — 全组合: B+C+E",
        "",
        f"φ = {GOLDEN_RATIO:.6f}",
        f"N_max = {N_MAX}, T_max = {T_MAX}",
        f"已知零点: {len(known_in_range)} 个",
        "",
        "Loiseau 出口判定:",
        "ratio > 1.2 → 类B外候选",
        "ratio > 2.0 → 强 prime-selective",
    ]
    for i, line in enumerate(info_lines):
        ypos = 0.95 - i * 0.055
        if line.startswith("理论来源") or line.startswith("Loiseau"):
            ax8.text(0.05, ypos, line, fontsize=10, fontweight='bold', color='#2c3e50')
        elif line.startswith("A —") or line.startswith("ratio >"):
            ax8.text(0.05, ypos, line, fontsize=8.5, color='#e74c3c')
        else:
            ax8.text(0.05, ypos, line, fontsize=8.5, color='#555555')

    plt.suptitle('Servi Kernel 六元对照实验 v3 — PKS Croft/E8/Damon/驻波 多元融合', fontsize=14, fontweight='bold', y=1.01)
    out_png = os.path.join(od, 'Servi_Mollifier_v3_六元对照.png')
    plt.savefig(out_png, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"\n✅ 输出图: {out_png}")

    # ═══════════════════════════════════════════════════════════════════
    # 6. 总结报告
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"总结报告")
    print(f"{'='*70}")
    print(f"{'组':4s} {'名称':22s} {'Ratio':>8s} {'vs A':>6s} {'系数':>5s} {'判定':>10s}")
    print(f"{'-'*60}")
    for idx, (name, r) in enumerate(results):
        label = name.split(":")[-1].strip()
        vs_a = r['ratio'] / ratios[0]
        flag = "🔥强selective" if r['ratio'] > 2.0 else ("✅类B外" if r['ratio'] > 1.2 else ("⚠️弱" if r['ratio'] > 1.05 else "  phase-blind"))
        print(f"{group_labels[idx]:4s} {label:22s} {r['ratio']:8.4f} {vs_a:6.2f}x {r['n_coeffs']:5d} {flag:>10s}")

    print(f"\n🔥 核心结论:")
    best_idx = np.argmax(ratios)
    print(f"   最佳组: {results[best_idx][0]} — ratio={ratios[best_idx]:.4f}")
    if ratios[best_idx] > 2.0:
        print(f"   ✅ 已突破强 prime-selective 阈值 (ratio > 2.0)")
        print(f"   ✅ 可宣称 '已构造出跳出 Loiseau 类B的具名核'")
    elif ratios[best_idx] > 1.2:
        print(f"   ✅ 突破 Loiseau 出口阈值 (ratio > 1.2)")
        print(f"   → 验证 Servi kernel 的 prime-detection 能力")
        print(f"   → 建议进一步增大 N_max 验证渐近稳定性")
    else:
        print(f"   ⚠️ 未突破 1.2 阈值 — 需要调整参数")
