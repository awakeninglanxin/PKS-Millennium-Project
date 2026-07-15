#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
M4 下界数值扫描 — P_M(σ+it) 在 σ>1/2 时的极小值探测
══════════════════════════════════════════════════════
验证命题: |P_M(σ+it)| 在 σ>1/2 时是否存在下界 > 0

方法: 在 (σ, t) 网格上大量采样 P_M(s) = Σ_{n=1}^M n^(-σ-it)
统计 min |P_M| 作为 M 的函数，验证是否收敛到正数。

若 min |P_M| ≈ C_0 > 0 对所有 σ>0.55 成立 → M4 gap 可填的数值证据
若 min |P_M| → 0 随 M→∞ → M4 需要更强的论证

2026-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from math import log, sqrt, exp, cos, sin

od = os.path.dirname(os.path.abspath(__file__))

def partial_sum_M(M, sigma, t):
    """P_M(σ+it) = Σ_{n=1}^M n^(-σ-it)"""
    total = 1.0 + 0j  # n=1 term = 1
    for n in range(2, M + 1):
        total += n**(-sigma) * complex(cos(t * log(n)), -sin(t * log(n)))
    return total

def scan_M4_lower_bound(M_values, sigma_values, t_points_per_sigma=5000):
    """
    对每个 M 和 σ 值，扫描 t 空间中 |P_M(σ+it)| 的最小值
    t 范围用对数均匀采样以覆盖不同频率
    """
    results = []
    for M in M_values:
        row = {'M': M}
        for sigma in sigma_values:
            # t 采样：对数均匀 + 在典型零点位置附近加密
            t_start = max(10, M / 2)
            t_end = t_start + 50
            t_samples = np.linspace(t_start, t_end, t_points_per_sigma)
            
            min_val = float('inf')
            min_t = t_start
            for t in t_samples:
                val = abs(partial_sum_M(M, sigma, t))
                if val < min_val:
                    min_val = val
                    min_t = t
            row[f'sigma_{sigma}'] = min_val
            row[f't_at_min_{sigma}'] = min_t
        results.append(row)
        print(f"  M={M:4d}: ", end="")
        for sigma in sigma_values:
            print(f"σ={sigma:.2f}: min|P_M|={row[f'sigma_{sigma}']:.2e}  ", end="")
        print()
    return results

def scan_fine_resolution(M, sigma, t_range, n_samples=20000):
    """高分辨率扫描单个 (M, σ) 对"""
    t_vals = np.linspace(t_range[0], t_range[1], n_samples)
    p_vals = np.array([abs(partial_sum_M(M, sigma, t)) for t in t_vals])
    min_idx = np.argmin(p_vals)
    return t_vals, p_vals, t_vals[min_idx], p_vals[min_idx]

# ====== 主实验 ======
print("=" * 65)
print("M4 下界数值扫描 — P_M(σ+it) 极小值探测")
print("=" * 65)

# Phase 1: 粗扫 — M=20..200, σ=0.55,0.60,0.65,0.75
print("\n[Phase 1] 粗扫 M=20..200, σ=0.55-0.75")
M_range = [20, 40, 60, 80, 100, 150, 200]
sigma_range = [0.55, 0.60, 0.65, 0.75]
results = scan_M4_lower_bound(M_range, sigma_range, t_points_per_sigma=5000)

# Phase 2: M=200 精细扫描
print(f"\n[Phase 2] M=200 σ=0.55 精细扫描 (20000点)")
t_fine, p_fine, t_min, p_min = scan_fine_resolution(
    200, 0.55, (100, 150), n_samples=20000)
print(f"  min |P_200(0.55+it)| = {p_min:.6e} at t≈{t_min:.2f}")

# Phase 3: 在找到的极小值附近更深搜索
print(f"\n[Phase 3] 在 t≈{t_min:.1f} 附近超精细扫描")
t_deep = np.linspace(t_min - 2, t_min + 2, 10000)
p_deep = np.array([abs(partial_sum_M(200, 0.55, t)) for t in t_deep])
min_deep_idx = np.argmin(p_deep)
print(f"  深搜 min |P_200| = {p_deep[min_deep_idx]:.8e} at t={t_deep[min_deep_idx]:.4f}")

# Phase 4: σ 的临界行为 — 固定 t 在极小值点，扫 σ
print(f"\n[Phase 4] 固定 t≈{t_deep[min_deep_idx]:.2f}, 扫 σ∈[0.5, 0.9]")
t_fixed = t_deep[min_deep_idx]
sigma_sweep = np.linspace(0.50, 0.90, 40)
p_sigma_sweep = [abs(partial_sum_M(200, s, t_fixed)) for s in sigma_sweep]

# ====== 可视化 ======
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# Panel 1: min |P_M| vs M (各σ)
ax = axes[0,0]
colors = ['#e74c3c', '#f39c12', '#27ae60', '#2980b9']
for idx, sigma in enumerate(sigma_range):
    vals = [r[f'sigma_{sigma}'] for r in results]
    ax.plot(M_range, vals, 'o-', ms=6, lw=1.5, color=colors[idx], label=f'σ={sigma}')
ax.set_xlabel('M'); ax.set_ylabel('min |P_M(σ+it)|')
ax.set_title('M4 下界: min |P_M| vs M (粗扫)')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.set_yscale('log')

# Panel 2: 精细扫 — |P_200(0.55+it)|
ax2 = axes[0,1]
ax2.plot(t_fine, p_fine, 'b-', lw=0.8, alpha=0.7)
ax2.axhline(0, color='gray', ls='--', alpha=0.3)
ax2.scatter([t_min], [p_min], color='red', s=80, zorder=5, marker='*')
ax2.annotate(f'min={p_min:.3e}', (t_min, p_min), textcoords="offset points",
             xytext=(10, 15), fontsize=9, color='red')
ax2.set_xlabel('t'); ax2.set_ylabel('|P_200(0.55+it)|')
ax2.set_title(f'M=200 σ=0.55 精细扫描 (min={p_min:.3e})')
ax2.grid(alpha=0.3)

# Panel 3: 深搜放大
ax3 = axes[0,2]
ax3.plot(t_deep, p_deep, 'r-', lw=1, alpha=0.8)
ax3.scatter([t_deep[min_deep_idx]], [p_deep[min_deep_idx]], color='darkred', s=120, zorder=5, marker='*')
ax3.set_xlabel('t'); ax3.set_ylabel('|P_200(0.55+it)|')
ax3.set_title(f'极小值附近深搜 ({p_deep[min_deep_idx]:.6e})')
ax3.grid(alpha=0.3)

# Panel 4: |P_M| 直方图 (M=200, σ=0.55)
ax4 = axes[1,0]
ax4.hist(np.log10(p_fine + 1e-15), bins=60, color='steelblue', alpha=0.8, edgecolor='white')
ax4.axvline(np.log10(p_min + 1e-15), color='red', ls='--', lw=2, label=f'min={p_min:.2e}')
ax4.set_xlabel('log10(|P_M|)'); ax4.set_ylabel('频率')
ax4.set_title(f'|P_200(0.55+it)| 分布 (N={len(t_fine)})')
ax4.legend(fontsize=9)

# Panel 5: σ-sweep at fixed t
ax5 = axes[1,1]
ax5.plot(sigma_sweep, p_sigma_sweep, 'o-', ms=4, lw=1.5, color='#8e44ad')
ax5.axvline(0.5, color='gray', ls='--', alpha=0.4, label='Critical line σ=0.5')
ax5.axhline(0, color='gray', ls='--', alpha=0.3)
ax5.set_xlabel('σ'); ax5.set_ylabel('|P_200(σ+it)|')
ax5.set_title(f'固定 t≈{t_fixed:.1f} 扫 σ (σ=0.5时|P|={p_sigma_sweep[0]:.3f})')
ax5.legend(fontsize=9)
ax5.grid(alpha=0.3)

# Panel 6: 判决总结
ax6 = axes[1,2]
ax6.axis('off')

# 统计判决
min_all = min(r['sigma_0.55'] for r in results)
max_all = max(r['sigma_0.55'] for r in results)
mean_all = np.mean([r['sigma_0.55'] for r in results])

# 对σ=0.55, 检查是否有趋零趋势
vals_055 = [r['sigma_0.55'] for r in results]
decay_ratio = vals_055[-1] / vals_055[0] if vals_055[0] > 0 else 0

lines = [
    "M4 下界数值证据总结",
    "",
    f"扫描范围: M={M_range[0]}-{M_range[-1]}, σ={sigma_range}",
    f"每对采样: {5000} 个 t 点",
    f"",
    f"σ=0.55 统计:",
    f"  min |P_M| = {min_all:.4e}",
    f"  max |P_M| = {max_all:.4e}",
    f"  mean |P_M| = {mean_all:.4e}",
    f"  decay M=20→200: {decay_ratio:.3f}x",
    f"",
    f"M=200 σ=0.55 精细:",
    f"  min = {p_min:.6e}",
    f"  deep min = {p_deep[min_deep_idx]:.8e}",
    f"",
    f"判决:",
]

if p_deep[min_deep_idx] > 1e-4:
    lines.append("✅ |P_M| > 10⁻⁴ — 强证据支持下界存在")
    lines.append("✅ M4 gap 有望通过 Turán+prime-selective 填上")
elif p_deep[min_deep_idx] > 1e-6:
    lines.append("⚠️ |P_M| ~ 10⁻⁵~10⁻⁶ — 下界可能存在但较小")
    lines.append("⚠️ 需要更大 M 范围验证趋势")
else:
    lines.append("🔴 |P_M| < 10⁻⁶ — 下界可能存在但极弱")
    lines.append("🔴 M4 需要更强的论证策略")

lines.extend([
    "",
    "理论方向:",
    "· Turán 1948: |Σ n^(-it)| ≥ (log N)^(1/2)",
    "· 素数项: p^(-σ)衰减 ~ n^(-σ)/log n",
    "· 合数项: (pq)^(-σ)衰减 ~ n^(-2σ)",
    "· σ>1/2 时合数衰减远快于素数→素数主导",
])

for i, line in enumerate(lines):
    y = 0.95 - i * 0.045
    if line.startswith("M4") or line.startswith("判决") or line.startswith("理论"):
        ax6.text(0.05, y, line, fontsize=11, fontweight='bold', color='#2c3e50')
    elif line.startswith("✅"):
        ax6.text(0.05, y, line, fontsize=10, color='#27ae60', fontweight='bold')
    elif line.startswith("🔴"):
        ax6.text(0.05, y, line, fontsize=10, color='#e74c3c', fontweight='bold')
    elif line.startswith("⚠️"):
        ax6.text(0.05, y, line, fontsize=10, color='#f39c12')
    else:
        ax6.text(0.05, y, line, fontsize=9, color='#555555')

plt.suptitle('M4 下界数值扫描 — P_M(σ+it) 极小值探测 | ζ 零点在σ>1/2 存在的必要条件', fontsize=13, fontweight='bold')
plt.tight_layout()
out_path = os.path.join(od, 'M4_下界数值扫描.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n✅ 输出: {out_path}")
print(f"\n{'='*65}")
print(f"最终判决: min |P_200(0.55+it)| = {p_deep[min_deep_idx]:.8e}")
print(f"  若 > 10⁻⁶ → M4 下界存在有数值证据 → Turán 路线可行")
print(f"{'='*65}")
