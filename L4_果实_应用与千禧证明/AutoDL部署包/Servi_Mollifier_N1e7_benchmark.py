#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi-Croft Kernel N=10^7 分批向量化验证
══════════════════════════════════════════════════════
分批处理 2.67M Croft totatives，内存 < 200 MB。
输出 N=10^7 下的 prime-detection ratio。
"""
import numpy as np, time, os
od = os.path.dirname(os.path.abspath(__file__))

N_MAX = 10_000_000
t_points, T_max = 300, 80
BATCH_SIZE = 20000  # ~48 MB per batch for 300×20000 float64 matrix

CROFT = frozenset({1,7,11,13,17,19,23,29})
t_arr = np.linspace(10, T_max, t_points, dtype=np.float64)

print("=" * 60)
print(f"  Servi-Croft N={N_MAX:,} 分批向量化")
print(f"  t: {t_points} pts in [{t_arr[0]:.0f}, {t_arr[-1]:.0f}]")
print(f"  Batch size: {BATCH_SIZE:,}")
print("=" * 60)

# ── Phase 1: 素数筛 ──
t0 = time.perf_counter()
limit = N_MAX
is_prime = np.ones(limit + 1, dtype=bool)
is_prime[:2] = False
for p in range(2, int(limit ** 0.5) + 1):
    if is_prime[p]:
        is_prime[p * p : limit + 1 : p] = False
t_sieve = time.perf_counter() - t0
print(f"\n[Phase 1] 素数筛 2→{N_MAX:,}: {t_sieve:.1f}s ({is_prime.sum():,} 素数)")

# ── Phase 2: 构建 Croft totative 数组 ──
t0 = time.perf_counter()
# 用 modulo 30 步长加速: 只检查 totative 余数类
all_n, all_log_n, all_isqrt = [], [], []
n_prime_count = 0
step = 30
for base in sorted(CROFT):
    if base >= 30: break
    for n in range(base, N_MAX + 1, step):
        if n < 2: continue
        all_n.append(n)
        all_log_n.append(np.log(n))
        all_isqrt.append(1.0 / np.sqrt(n))
        if is_prime[n]:
            n_prime_count += 1

n_tot = len(all_n)
log_n = np.array(all_log_n, dtype=np.float64)
inv_sqrt = np.array(all_isqrt, dtype=np.float64)
n_arr = np.array(all_n, dtype=np.int64)
t_build = time.perf_counter() - t0
print(f"[Phase 2] Croft totatives: {n_tot:,} ({n_prime_count:,} primes, "
      f"{n_tot - n_prime_count:,} composites), {t_build:.1f}s")

# ── Phase 3: 分批向量化累加 ──
t0 = time.perf_counter()
Kp = np.zeros(t_points, dtype=np.float64)
Kn = np.zeros(t_points, dtype=np.float64)

n_batches = (n_tot + BATCH_SIZE - 1) // BATCH_SIZE
for b in range(n_batches):
    i_start = b * BATCH_SIZE
    i_end = min(i_start + BATCH_SIZE, n_tot)
    n_b = n_arr[i_start:i_end]
    ln_b = log_n[i_start:i_end]
    is_b = inv_sqrt[i_start:i_end]
    bs = i_end - i_start

    # 全量广播: cos(-t_i * log n_j) * (1/√n_j) → (t_points, bs)
    # 内存: t_points × bs × 8 bytes = 300 × 20000 × 8 = 48 MB
    cos_term = np.cos(np.outer(-t_arr, ln_b)) * is_b[np.newaxis, :]  # (300, bs)
    p_mask = is_prime[n_b]  # (bs,)
    Kp += cos_term[:, p_mask].sum(axis=1)  # (300,)
    Kn += cos_term[:, ~p_mask].sum(axis=1)  # (300,)

    if (b + 1) % 200 == 0 or b == 0 or b == n_batches - 1:
        elapsed = time.perf_counter() - t0
        eta = elapsed / (b + 1) * (n_batches - b - 1)
        print(f"  batch {b+1:4d}/{n_batches} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

t_kernel = time.perf_counter() - t0

# ── Phase 4: Ratio ──
var_p = np.var(Kp)
var_n = np.var(Kn)
ratio = var_p / max(var_n, 1e-15)

# 也计算 vanilla (全整数) ratio 作为参考
# 用小 N=10^5 外推
# (N=10^7 全 10^7 个整数做逐 t 太慢，不做)

print(f"\n[Phase 3] Kernel: {t_kernel:.0f}s ({n_batches} batches)")
print(f"\n{'='*60}")
print(f"  RESULTS: N={N_MAX:,}")
print(f"  Ratio (Croft):      {ratio:8.2f}")
print(f"  Var(Kp):            {var_p:.6e}")
print(f"  Var(Kn):            {var_n:.6e}")
print(f"  Totatives:          {n_tot:,}")
print(f"  Primes in Croft:    {n_prime_count:,}")
print(f"  Composites in Croft:{n_tot - n_prime_count:,}")
print(f"  Total time:         {t_sieve + t_build + t_kernel:.0f}s")
print(f"{'='*60}")

# ── Phase 5: 保存 ──
csv_path = os.path.join(od, 'Servi_Mollifier_N1e7_结果.csv')
with open(csv_path, 'w', encoding='utf-8-sig') as f:
    f.write("N_max,ratio,var_Kp,var_Kn,n_totatives,n_primes,n_composites,t_sieve,t_build,t_kernel,t_total\n")
    f.write(f"{N_MAX},{ratio:.6f},{var_p:.6e},{var_n:.6e},"
            f"{n_tot},{n_prime_count},{n_tot - n_prime_count},"
            f"{t_sieve:.1f},{t_build:.1f},{t_kernel:.1f},{t_sieve+t_build+t_kernel:.1f}\n")
print(f"\n[CSV] {csv_path}")

# ── Phase 6: 与已有数据合并作图 ──
# 读取之前的 CSV 并合并
prev_csv = os.path.join(od, 'Servi_Mollifier_渐近报告_N2000.csv')
import csv
prev_data = []
if os.path.exists(prev_csv):
    with open(prev_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prev_data.append(row)

# 提取 Croft 数据
prev_N, prev_ratio = [], []
for row in prev_data:
    if row['method'] == 'Croft-Servi':
        prev_N.append(int(row['N_max']))
        prev_ratio.append(float(row['ratio']))

# 合并新数据
all_N = prev_N + [N_MAX]
all_R = prev_ratio + [ratio]

# ── 作图 ──
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Panel 1: Ratio vs N (log-log)
ax1.loglog(prev_N, prev_ratio, 'o-', ms=8, lw=2.5, color='#e74c3c', label='Croft-Servi (prev)')
ax1.loglog([N_MAX], [ratio], 'D', ms=15, color='darkred', zorder=10,
           label=f'N={N_MAX/1e6:.0f}M: ratio={ratio:.2f}')
ax1.axhline(1.2, color='gray', ls='--', lw=1, alpha=0.5, label='Loiseau threshold (1.2)')
ax1.axhline(2.0, color='green', ls='--', lw=1, alpha=0.5, label='Strong detection (2.0)')
ax1.set_xlabel('N_max'); ax1.set_ylabel('Ratio (log)')
ax1.set_title(f'Croft-Servi Ratio: N=60 → N={N_MAX/1e6:.0f}M')
ax1.legend(fontsize=9); ax1.grid(alpha=0.3, which='both')

# Annotate
for n, r in zip(prev_N, prev_ratio):
    ax1.annotate(f'{r:.1f}', (n, r), textcoords="offset points", xytext=(8, 5),
                 fontsize=7, color='#e74c3c', alpha=0.7)
ax1.annotate(f'{ratio:.2f}', (N_MAX, ratio), textcoords="offset points", xytext=(10, 10),
             fontsize=10, color='darkred', fontweight='bold')

# Panel 2: Ratio vs 1/log(N) 外推
x_extra = np.array([1.0 / np.log(n) for n in all_N])
ax2.plot(x_extra, all_R, 'o-', ms=8, lw=2, color='#e74c3c')
# 用最后 4 点外推
x_fit = x_extra[-4:]
y_fit = np.array(all_R[-4:])
coeff = np.polyfit(x_fit, y_fit, 1)
x_ext = np.linspace(0, x_fit[0] * 1.2, 50)
y_ext = np.polyval(coeff, x_ext)
ax2.plot(x_ext, y_ext, '--', lw=1.5, color='gray', alpha=0.6,
         label=f'Extrap: ratio→{coeff[1]:.2f} as N→∞')
ax2.plot(0, coeff[1], 's', ms=10, color='darkred', label=f'Limit ≈ {coeff[1]:.1f}')
ax2.set_xlabel('1 / log(N)'); ax2.set_ylabel('Ratio')
ax2.set_title('Convergence Extrapolation')
ax2.legend(); ax2.grid(alpha=0.3)

plt.suptitle(f'Servi-Croft Kernel N={N_MAX/1e6:.0f}M 渐近验证\n'
             f'{n_tot:,} totatives, {n_prime_count:,} primes | CPU {t_sieve+t_build+t_kernel:.0f}s',
             fontsize=13, fontweight='bold')
plt.tight_layout()

png_path = os.path.join(od, 'Servi_Mollifier_N1e7.png')
plt.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"[PNG] {png_path}")

# ── 判定 ──
print(f"\n  外推极限 ratio ≈ {coeff[1]:.2f}")
print(f"  Loiseau 阈值倍数: {ratio/1.2:.1f}×")
if ratio > 2.0:
    print(f"  [判定] 强检测 (ratio > 2.0) ✓")
elif ratio > 1.2:
    print(f"  [判定] 通过 Loiseau 阈值 (ratio > 1.2) ✓")
else:
    print(f"  [判定] 低于阈值 ✗")
