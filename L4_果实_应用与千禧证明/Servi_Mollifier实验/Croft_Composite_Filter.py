#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Croft Totative 合数精准筛除算法
══════════════════════════════════════════════════════
原理：Croft totatives = 7-rough numbers (OEIS A007775)
      合数 totative = 质因子全部 ≥7 的合数

方法：线性筛 + SPF 预计算 → O(1) 判定每个 totative 是素/合
      对合数施加权重衰减 (1/ω(n) 或直接剔除)

验证：N=10^7, 看看 ratio 能恢复到什么程度
"""
import numpy as np, time, os
od = os.path.dirname(os.path.abspath(__file__))

N_MAX = 10_000_000
t_points, T_max = 300, 80
t_arr = np.linspace(10, T_max, t_points, dtype=np.float64)

print("=" * 60)
print(f"  Croft 合数精准筛除 — N={N_MAX:,}")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# Phase 1: 线性筛 — SPF (Smallest Prime Factor) + 素数列表
# ═══════════════════════════════════════════════════════════════
t0 = time.perf_counter()
spf = np.arange(N_MAX + 1, dtype=np.int32)
primes_list = []
for i in range(2, N_MAX + 1):
    if spf[i] == i:  # i 是素数
        primes_list.append(i)
    for p in primes_list:
        if p * i > N_MAX:
            break
        spf[p * i] = p
        if p == spf[i]:  # p 是 i 的最小质因子
            break
t_linear = time.perf_counter() - t0
print(f"\n[Phase 1] 线性筛 (SPF): {t_linear:.1f}s ({len(primes_list):,} primes)")

# ═══════════════════════════════════════════════════════════════
# Phase 2: 构建 Croft totatives + 分类
# ═══════════════════════════════════════════════════════════════
t0 = time.perf_counter()
CROFT = [1, 7, 11, 13, 17, 19, 23, 29]

all_n, all_log_n, all_isqrt = [], [], []
all_category = []  # 0=prime totative, 1=prime-power composite, 2=multi-prime composite

for base in CROFT:
    if base == 1:  # skip 1
        continue
    for n in range(base, N_MAX + 1, 30):
        if spf[n] == n:  # 素数 totative → 纯粹信号
            cat = 0
        elif spf[n] == spf[n // spf[n]]:  # p^k 型 → 质数幂
            cat = 1
        else:                               # 多质因子积 → 最想筛除的
            cat = 2
        all_n.append(n)
        all_log_n.append(np.log(n))
        all_isqrt.append(1.0 / np.sqrt(n))
        all_category.append(cat)

n_tot = len(all_n)
log_n = np.array(all_log_n, dtype=np.float64)
inv_sqrt = np.array(all_isqrt, dtype=np.float64)
n_arr = np.array(all_n, dtype=np.int64)
cat_arr = np.array(all_category, dtype=np.int8)
t_build = time.perf_counter() - t0

# 统计
n_prime = int(np.sum(cat_arr == 0))
n_ppow = int(np.sum(cat_arr == 1))
n_multi = int(np.sum(cat_arr == 2))
print(f"[Phase 2] Totatives: {n_tot:,}")
print(f"  素数:        {n_prime:>10,} ({100*n_prime/n_tot:.1f}%)  cat=0 ★")
print(f"  质数幂(p^k): {n_ppow:>10,} ({100*n_ppow/n_tot:.1f}%)  cat=1")
print(f"  多质因子积:  {n_multi:>10,} ({100*n_multi/n_tot:.1f}%)  cat=2 ✗")
print(f"  Build: {t_build:.1f}s")

# ═══════════════════════════════════════════════════════════════
# Phase 3: 分层 Servi-Croft Kernel
# ═══════════════════════════════════════════════════════════════
t0 = time.perf_counter()
BATCH = 50000

K_prime  = np.zeros(t_points, dtype=np.float64)  # 素数 totative
K_ppow   = np.zeros(t_points, dtype=np.float64)  # 质数幂 totative
K_multi  = np.zeros(t_points, dtype=np.float64)  # 多质因子 totative

n_batches = (n_tot + BATCH - 1) // BATCH
for b in range(n_batches):
    i0 = b * BATCH; i1 = min(i0 + BATCH, n_tot)
    ln_b = log_n[i0:i1]; is_b = inv_sqrt[i0:i1]
    cat_b = cat_arr[i0:i1]; bs = i1 - i0

    cos_term = np.cos(np.outer(-t_arr, ln_b)) * is_b[np.newaxis, :]

    K_prime += cos_term[:, cat_b == 0].sum(axis=1)
    K_ppow  += cos_term[:, cat_b == 1].sum(axis=1)
    K_multi += cos_term[:, cat_b == 2].sum(axis=1)

    if (b+1) % 50 == 0:
        print(f"  batch {b+1}/{n_batches} ({time.perf_counter()-t0:.0f}s)")

t_kernel = time.perf_counter() - t0
print(f"[Phase 3] Kernel: {t_kernel:.0f}s")

# ═══════════════════════════════════════════════════════════════
# Phase 4: 多维 Ratio 分析
# ═══════════════════════════════════════════════════════════════

# 传统 ratio (旧方法)
var_p = np.var(K_prime)
var_c = np.var(K_ppow + K_multi)
ratio_trad = var_p / max(var_c, 1e-15)

# 分层 ratio
var_ppow  = np.var(K_ppow)
var_multi = np.var(K_multi)

# Ratio 1: 素数 vs 仅质数幂
ratio_vs_ppow  = var_p / max(var_ppow, 1e-15)
# Ratio 2: 素数 vs 仅多质因子
ratio_vs_multi = var_p / max(var_multi, 1e-15)
# Ratio 3: 素数 vs (质数幂+多质因子)
ratio_vs_all_comp = ratio_trad

# ═══════════════════════════════════════════════════════════════
# Phase 5: 加权核实验 — 合数权重衰减
# ═══════════════════════════════════════════════════════════════
# 方案A: 合数权重 = 1/ω (ω = 不同质因子数)
# 方案B: 合数权重 = μ²(n) * (1 if prime else 0) ← 彻底剔除合数
# 方案C: 合数权重 = φ(n)/n (Euler totient / n → 越小越"合数")

# 快速实现方案B: 只用素数 totatives vs 只用非 totative 合数
# (需要重新构建非 totative 合数作为对照)

# 先用 K_prime vs K_multi 作为最干净的对比
print(f"\n{'='*60}")
print(f"  RESULTS: N={N_MAX:,} — 分层 Croft 核")
print(f"{'='*60}")
print(f"  传统 ratio (素数 vs 全部合数):   {ratio_trad:10.2f}")
print(f"  分层 ratio (素数 vs 质数幂):     {ratio_vs_ppow:10.2f}")
print(f"  分层 ratio (素数 vs 多质因子):   {ratio_vs_multi:10.2f}")
print(f"")
print(f"  Var(素数):        {var_p:.4f}")
print(f"  Var(质数幂):      {var_ppow:.4f}")
print(f"  Var(多质因子):    {var_multi:.4f}")
print(f"  Var(全部合数):    {var_c:.4f}")
print(f"")
print(f"  素数 count:      {n_prime:>10,} — 信号源")
print(f"  质数幂 count:    {n_ppow:>10,} — 勉强可分")
print(f"  多质因子 count:  {n_multi:>10,} — 主要噪声")
print(f"")
print(f"  总耗时:          {t_linear+t_build+t_kernel:.0f}s")
print(f"{'='*60}")

# ═══════════════════════════════════════════════════════════════
# Phase 6: 可视化
# ═══════════════════════════════════════════════════════════════
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Panel 1: K_prime vs K_multi 时间序列
ax = axes[0, 0]
ax.plot(t_arr, K_prime, 'b-', lw=1, alpha=0.7, label=f'K_prime ({n_prime:,} terms)')
ax.plot(t_arr, K_multi, 'r-', lw=1, alpha=0.7, label=f'K_multi ({n_multi:,} terms)')
ax.set_xlabel('t'); ax.set_ylabel('K(t)')
ax.set_title(f'Prime vs Multi-prime Composite Kernel\nRatio={ratio_vs_multi:.2f}')
ax.legend(); ax.grid(alpha=0.3)

# Panel 2: 饼图 — totative 组成
ax = axes[0, 1]
sizes = [n_prime, n_ppow, n_multi]
labels = [f'Primes\n{n_prime:,}', f'p^k\n{n_ppow:,}', f'Multi-prime\n{n_multi:,}']
colors = ['#27ae60', '#f39c12', '#e74c3c']
wedges, _, _ = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                       explode=(0, 0, 0.05), textprops={'fontsize': 9})
ax.set_title(f'Croft Totatives Composition\nN={N_MAX/1e6:.0f}M, {n_tot:,} total')

# Panel 3: Ratio 柱状图
ax = axes[1, 0]
ratios = [ratio_trad, ratio_vs_ppow, ratio_vs_multi]
labels_r = ['Traditional\n(prime vs all comp)', 'vs p^k only', 'vs multi-prime\nonly']
colors_r = ['#7f8c8d', '#f39c12', '#27ae60']
bars = ax.bar(range(3), ratios, color=colors_r, edgecolor='white')
ax.axhline(1.2, color='red', ls='--', alpha=0.5, label='Loiseau threshold')
ax.axhline(2.0, color='green', ls='--', alpha=0.5)
ax.set_xticks(range(3)); ax.set_xticklabels(labels_r, fontsize=8)
ax.set_ylabel('Ratio'); ax.set_title('Ratio by Composite Type')
for bar, r in zip(bars, ratios):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{r:.1f}', ha='center', fontweight='bold', fontsize=11)
ax.legend(); ax.grid(axis='y', alpha=0.3)

# Panel 4: 判决
ax = axes[1, 1]
ax.axis('off')
lines = [
    "=" * 50,
    "Croft 合数精准筛除 — 判决",
    "=" * 50,
    "",
    f"N = {N_MAX:,}",
    f"Totatives: {n_tot:,} (8/30 of all integers)",
    f"  — Primes:   {n_prime:>8,} ({100*n_prime/n_tot:.1f}%)",
    f"  — p^k:      {n_ppow:>8,} ({100*n_ppow/n_tot:.1f}%)",
    f"  — Multi-p:  {n_multi:>8,} ({100*n_multi/n_tot:.1f}%)",
    "",
    "Kernel Ratios:",
    f"  Ratio (prime vs all comp):    {ratio_trad:.2f}",
    f"  Ratio (prime vs p^k):         {ratio_vs_ppow:.2f}",
    f"  Ratio (prime vs multi-p):     {ratio_vs_multi:.2f}",
    "",
    "Key insight:",
    "  Multi-prime composites are the main noise.",
    f"  Stripping them → ratio jumps to {ratio_vs_multi:.1f}",
    f"  vs Loiseau threshold 1.2: {ratio_vs_multi/1.2:.1f}x margin",
]
for i, line in enumerate(lines):
    y = 0.98 - i * 0.038
    c = '#2c3e50' if ('=' in line or 'Key' in line) else '#555555'
    s = 9 if '=' in line else 7.5
    ax.text(0.02, y, line, fontsize=s, color=c, fontfamily='monospace', fontweight='bold' if '=' in line else 'normal')

plt.suptitle(f'Croft Totative Composite Filtering — N={N_MAX/1e6:.0f}M\n'
             f'SPF Linear Sieve → 3-class decomposition',
             fontsize=13, fontweight='bold')
plt.tight_layout()

png_path = os.path.join(od, 'Croft_Composite_Filter_N1e7.png')
plt.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# CSV
csv_path = os.path.join(od, 'Croft_Composite_Filter_N1e7.csv')
with open(csv_path, 'w', encoding='utf-8-sig') as f:
    f.write("N_max,ratio_prime_vs_all,ratio_prime_vs_ppow,ratio_prime_vs_multi,"
            "var_p,var_ppow,var_multi,n_prime,n_ppow,n_multi,t_linear,t_build,t_kernel,t_total\n")
    f.write(f"{N_MAX},{ratio_trad:.4f},{ratio_vs_ppow:.4f},{ratio_vs_multi:.4f},"
            f"{var_p:.4f},{var_ppow:.4f},{var_multi:.4f},"
            f"{n_prime},{n_ppow},{n_multi},"
            f"{t_linear:.1f},{t_build:.1f},{t_kernel:.1f},{t_linear+t_build+t_kernel:.1f}\n")

print(f"\n[PNG] {png_path}")
print(f"[CSV] {csv_path}")
