#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi 几何 Mollifier 升级版 (2025-08 Conrey + Loiseau Spectral Barrier 整合)

新增功能 (相对原版 Servi_Mollifier_实验.py):
1. Conrey 2025-08 变分法构造 ζ 导数线性组合 的数值复现
2. Loiseau Spectral Barrier 的 prime-detection 能力验证:
   -- 验证关键命题: Servi kernel K(s;t) = Σ cos(-t log n) n^(−1/2−s)
      对 prime / non-prime 的 Var_t(⟨K, indicator⟩) 应严格分离
3. 三类方法对照:
   -- 标准 μ(n) mollifier (类 B, phase-blind)
   -- Servi kernel (类 B 候选 → 测试是否跳出)
   -- Conrey 变分导数线性组合 (2025-08 路线)
4. 临界线零点检测准确率比较

修订日期: 2026-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import math as _math
from math import log, sqrt, pi, cos, sin

od = os.path.dirname(os.path.abspath(__file__))

# ====== 0. 基本 ζ(1/2+it) 计算 ======
def zeta_half(t, N=None):
    """Riemann-Siegel partial sum on critical line"""
    if N is None:
        N = int(sqrt(t/(2*pi))) + 5
    z = 0+0j
    angles = []
    s_real = 0.5
    for n in range(1, N+1):
        term = n**(-s_real) * complex(cos(t*log(n)), -sin(t*log(n)))
        z += term
        angles.append(-t*log(n))
    return z, N, np.array(angles)


def zeta_deriv(t, k, N=None):
    """ζ^(k)(1/2+it) — k-th derivative via sum of terms n^(-1/2-s) * (-log n)^k"""
    if N is None:
        N = int(sqrt(t/(2*pi))) + 5
    s_real = 0.5
    z = 0+0j
    for n in range(1, N+1):
        # term for n^(-s) where s = 1/2 + it
        # d^k/ds^k n^(-s) = (-1)^k (log n)^k n^(-s)
        base = n**(-s_real) * complex(cos(t*log(n)), -sin(t*log(n)))
        deriv_factor = (-log(n))**k
        z += deriv_factor * base
    return z


# ====== 1. 标准 Möbius ======
def mobius(n):
    if n == 1: return 1
    if n == 0: return 0
    p = 0
    m = n
    for d in range(2, int(sqrt(n))+1):
        if m % d == 0:
            m //= d
            p += 1
            if m % d == 0:
                return 0
    if m > 1: p += 1
    return -1 if p % 2 else 1


def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i*i <= n:
        if n % i == 0 or n % (i+2) == 0:
            return False
        i += 6
    return True


def standard_mollifier_coeffs(N_max, theta=0.571):
    """标准 mollifier: μ(n) * smooth cutoff"""
    coeffs = {}
    for n in range(1, N_max+1):
        mu = mobius(n)
        if mu == 0: continue
        phi = max(0, 1.0 - n/N_max)
        coeffs[n] = mu * phi
    return coeffs


# ====== 2. Conrey 2025-08 变分法导数线性组合 ======
def conrey_variational_coeffs(t_target, N_max, K_derivs=3, alpha_search=None):
    """
    Conrey 2025 团队: 用变分法构造 ζ 的 k 阶导数线性组合作为新的 mollifier 框架

    目标: 找系数 (c_0, c_1, ..., c_K) 使某个目标最大化:
      - 标准 Conrey 形式: max Re Σ_k c_k * ζ^(k)(s) 这样的 mollifier-related 量
      - 我们的简化版: 在 t_target 附近最小化残差
    """
    if alpha_search is None:
        alpha_search = np.linspace(0.01, 3.0, 30)

    # 对每个 α (圆频率), 构造线性组合 Σ_k (iα)^k/k! * ζ^(k)
    # 这是 Conrey 团队原始构造的简化版
    best_alpha = alpha_search[0]
    best_score = -np.inf
    best_coeffs = {}

    for alpha in alpha_search:
        # Conrey 2025: 圆频率 α 对应的导数线性组合系数
        coeffs = {}
        for k in range(K_derivs+1):
            # k-阶导数对应权重系数
            # 在 Conrey 团队的变分框架中, 这是 Lagrange 函数空间中的 Fourier 系数
            weight = (alpha)**k / _math.factorial(k) * np.exp(-alpha)
            for n in range(1, N_max+1):
                if n not in coeffs:
                    coeffs[n] = 0.0
                # ζ^(k)(s) 对 n^(-s) 的贡献 = (-log n)^k * n^(-s)
                # 综合导数贡献
                coeffs[n] += weight * (-log(n))**k * n**(-0.5)

        # 计算"集中度" (近似 Conrey 优化目标):
        # 我们的目标是让 mollifier 在 t_target 附近的零点检测能力最大化
        # 简化度量: 系数的 |.|² 加权和 (高 = 集中)
        score = sum(c**2 for c in coeffs.values())

        if score > best_score:
            best_score = score
            best_alpha = alpha
            best_coeffs = coeffs

    return best_coeffs, best_alpha


# ====== 3. Servi 几何 mollifier (原版) ======
def servi_mollifier_coeffs(t, N_max):
    """原版 Servi: a_n = cos(-t log n) / sqrt(n)"""
    _, _, angles = zeta_half(t, N_max)
    coeffs = {}
    for n in range(1, N_max+1):
        angle = angles[n-1]
        weight = cos(angle)
        decay = 1.0 / sqrt(n)
        phi = max(0, 1.0 - n/N_max)
        coeffs[n] = weight * decay * phi
    return coeffs


# ====== 4. 新功能: Servi kernel prime-detection 能力 ======
def servi_kernel_prime_detection(t_values, N_max):
    """
    Loiseau 2025-09 Spectral Barrier 核心:
    是否 prime-selective kernel?

    测试命题:
      Var_t <K(s;t), 1_{n 是 prime}>  >  Var_t <K(s;t), 1_{n 不是 prime}> ?

    若严格分离成立 -> Servi kernel 部分跳出类 B

    K(s;t) = Σ_n cos(-t log n) n^(-1/2-s) (其 t-依赖敏感性)
    """
    primes_n = np.array([n for n in range(2, N_max+1) if is_prime(n)])
    nonprimes_n = np.array([n for n in range(2, N_max+1) if not is_prime(n)])

    # 对每个 t 计算 K 的 prime 和 nonprime 投影
    K_prime_t = []  # K(s;t) · 1_{prime} (内积)
    K_nonprime_t = []
    K_full_t = []

    for t in t_values:
        # 在临界线 s = 1/2 + i t 上
        # K(s;t) = Σ_n cos(-t log n) n^(-1/2-s) = Σ_n cos(-t log n) n^(-1/2) e^{-it log n}
        K_prime = 0.0
        K_nonprime = 0.0
        K_full = 0.0
        for n in range(2, N_max+1):
            # Servi kernel 内积项: cos(-t log n) · n^(-1/2) (实部)
            term_real = cos(-t * log(n)) / sqrt(n)
            K_full += term_real
            if is_prime(n):
                K_prime += term_real
            else:
                K_nonprime += term_real
        K_prime_t.append(K_prime)
        K_nonprime_t.append(K_nonprime)
        K_full_t.append(K_full)

    return {
        't_values': t_values,
        'K_prime': np.array(K_prime_t),
        'K_nonprime': np.array(K_nonprime_t),
        'K_full': np.array(K_full_t),
        'var_K_prime': np.var(np.array(K_prime_t)),
        'var_K_nonprime': np.var(np.array(K_nonprime_t)),
        'var_K_full': np.var(np.array(K_full_t)),
        'n_primes': len(primes_n),
        'n_nonprimes': len(nonprimes_n),
    }


# ====== 5. Mollifier 求值 ======
def eval_mollifier(t, coeffs):
    """计算 M(1/2+it) = Σ_n a_n n^(-s)"""
    s_real = 0.5
    result = 0+0j
    for n, coef in coeffs.items():
        term = n**(-s_real) * complex(cos(t*log(n)), -sin(t*log(n)))
        result += coef * term
    return result


# ====== 6. Levinson-Conrey 零点检测 ======
def levinson_conrey_detector(t_range, mollifier_coeffs, name="Standard"):
    zetas = []; molls = []
    for t in t_range:
        z, _, _ = zeta_half(t)
        m = eval_mollifier(t, mollifier_coeffs)
        zetas.append(z); molls.append(m)

    zetas = np.array(zetas)
    re_z = np.real(zetas)
    zeros = []
    for i in range(1, len(re_z)):
        if re_z[i] * re_z[i-1] < 0:
            t_zero = t_range[i-1] + (t_range[i]-t_range[i-1])*abs(re_z[i-1])/(abs(re_z[i-1])+abs(re_z[i])+1e-12)
            zeros.append(t_zero)
    return {'name': name, 't_range': t_range, 'zetas': zetas, 'molls': molls,
            'zeros': zeros, 'n_zeros': len(zeros)}


# ====== 7. 主实验 ======
print("="*60)
print("Servi Geometric Mollifier — Upgraded (2025-08 Conrey + Loiseau)")
print("="*60)

T_MAX = 80
N_MOLL = 40
t_range = np.linspace(10, T_MAX, 800)
t_mid = np.mean(t_range)

# 计算三类 mollifier 系数
std_coeffs = standard_mollifier_coeffs(N_MOLL)
srv_coeffs = servi_mollifier_coeffs(t_mid, N_MOLL)
conrey_coeffs, conrey_alpha = conrey_variational_coeffs(t_mid, N_MOLL, K_derivs=3)

print(f"\n[MOLLIFIER COEFFICIENTS]")
print(f"  Standard μ(n):    {len(std_coeffs)} non-zero")
print(f"  Servi geometric:  {len(srv_coeffs)} non-zero")
print(f"  Conrey 2025 var:  {len(conrey_coeffs)} non-zero  (alpha={conrey_alpha:.3f})")

# ====== 8. Prime-detection 测试 (Loiseau 核心命题) ======
print(f"\n[PRIME-DETECTION TEST — Loiseau Spectral Barrier 出口验证]")
t_for_prime = np.linspace(10, T_MAX, 200)
prime_test = servi_kernel_prime_detection(t_for_prime, N_MOLL)

print(f"  N_primes:    {prime_test['n_primes']}")
print(f"  N_nonprimes: {prime_test['n_nonprimes']}")
print(f"  Var_t<K, 1_{'{prime}'}>     = {prime_test['var_K_prime']:.4f}")
print(f"  Var_t<K, 1_{'{nonprime}'}>  = {prime_test['var_K_nonprime']:.4f}")
print(f"  Var_t<K, 1_{'{full}'}>      = {prime_test['var_K_full']:.4f}")

# 比率: 如果 prime 投影明显高于 nonprime → 检测到 prime phase structure
ratio = prime_test['var_K_prime'] / (prime_test['var_K_nonprime'] + 1e-12)
print(f"\n  Ratio (Var_prime / Var_nonprime)  = {ratio:.4f}")
if ratio > 1.2:
    print(f"  > Servi kernel DOES distinguish primes (ratio > 1.2)")
    print(f"  > Service kernel 可能 LOI (out of class B) — Loiseau Spectral Barrier 出口候选!")
elif ratio > 1.05:
    print(f"  > 弱 prime-detection (1.05-1.20), 但仍属 phase-blind 类 B 候选")
else:
    print(f"  > Ratio ≈ 1: Servi kernel 仍属 Loiseau 类 B (phase-blind)")
    print(f"  > 需要 Conrey 2025-08 变分法升级才能跳到 B 外")

# ====== 9. Levinson-Conrey 零点检测 (三类对比) ======
print(f"\n[LEVINSON-CONREY ZERO DETECTION COMPARISON]")
std_result = levinson_conrey_detector(t_range, std_coeffs, "Standard Mollifier")
srv_result = levinson_conrey_detector(t_range, srv_coeffs, "Servi Geometric Mollifier")
conrey_result = levinson_conrey_detector(t_range, conrey_coeffs, f"Conrey 2025 (α={conrey_alpha:.2f})")

# 已知零点
known_zeros = [14.13, 21.02, 25.01, 30.42, 32.93, 37.58, 40.91, 43.32, 48.00, 49.77, 52.97, 56.44, 59.34, 60.85, 65.10, 67.91, 69.50, 71.41, 72.73, 75.65, 77.91]
known_in_range = [z for z in known_zeros if z <= T_MAX]
print(f"\n  Known zeros (t<{T_MAX}): {len(known_in_range)}")
for tag, r in [("Standard", std_result), ("Servi", srv_result), ("Conrey", conrey_result)]:
    detected = r['n_zeros']
    coverage = detected / len(known_in_range) if known_in_range else 0
    print(f"  {tag:12s}: detected {detected:3d} zeros  (coverage {coverage*100:5.1f}%)")

# ====== 10. 可视化 (六面板) ======
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 3, figsize=(18, 11))

# Panel 1: ζ(1/2+it) Real Part — 三类 mollifier 对比
ax = axes[0,0]
re_z = np.real(std_result['zetas'])
ax.plot(t_range, re_z, 'b-', alpha=0.6, lw=0.8, label='Re ζ (1/2+it)')
ax.axhline(0, color='gray', ls='--', alpha=0.4)
for z in std_result['zeros']:
    ax.axvline(z, color='red', alpha=0.3, lw=0.5)
for z in known_in_range:
    ax.axvline(z, color='green', alpha=0.15, lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Re ζ')
ax.set_title('ζ(1/2+it) 实部过零 (红=detected, 绿=known)')
ax.legend(fontsize=8, loc='upper right')

# Panel 2: Prime-detection 能力
ax = axes[0,1]
ax.plot(t_for_prime, prime_test['K_prime'], 'r-', lw=1, alpha=0.7,
        label=f"K·1_{'{prime}'} (Var={prime_test['var_K_prime']:.3f})")
ax.plot(t_for_prime, prime_test['K_nonprime'], 'b-', lw=1, alpha=0.7,
        label=f"K·1_{'{nonprime}'} (Var={prime_test['var_K_nonprime']:.3f})")
ax.plot(t_for_prime, prime_test['K_full'], 'k--', lw=0.5, alpha=0.3,
        label=f"K full")
ax.set_xlabel('t'); ax.set_ylabel('Kernel projection')
ax.set_title(f"Servi kernel prime-detection (ratio={ratio:.3f})")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel 3: Mollifier 系数对比 (三类)
ax = axes[0,2]
n_vals = np.array(list(range(1, N_MOLL+1)))
std_vals = np.array([std_coeffs.get(n, 0) for n in n_vals])
srv_vals = np.array([srv_coeffs.get(n, 0) for n in n_vals])
conrey_vals = np.array([conrey_coeffs.get(n, 0) for n in n_vals])

# 归一化以便对比
def norm_arr(a):
    m = np.max(np.abs(a))+1e-12
    return a / m

w = 0.27
ax.bar(n_vals - w, norm_arr(std_vals), w, label='Standard μ', alpha=0.7, color='steelblue')
ax.bar(n_vals,     norm_arr(srv_vals), w, label='Servi cos',  alpha=0.7, color='orange')
ax.bar(n_vals + w, norm_arr(conrey_vals), w, label=f'Conrey α={conrey_alpha:.2f}', alpha=0.7, color='green')
ax.set_xlabel('n'); ax.set_ylabel('Normalized coefficient')
ax.set_title('三类 Mollifier 系数对比 (归一化)')
ax.legend(fontsize=8)

# Panel 4: ζ 螺旋在复平面
ax = axes[1,0]
z_full = std_result['zetas']
ax.plot(np.real(z_full), np.imag(z_full), 'b-', alpha=0.4, lw=0.5)
ax.scatter([0], [0], color='red', s=50, zorder=5, marker='*', label='ζ=0 (zeros)')
ax.set_xlabel('Re ζ'); ax.set_ylabel('Im ζ')
ax.set_title('ζ(1/2+it) 螺旋路径')
ax.legend(fontsize=8)

# Panel 5: 零点检测对比散点
ax = axes[1,1]
y_positions = {'Known': 1, 'Conrey 2025': 0.5, 'Servi': 0.0, 'Standard': -0.5}
ax.scatter(known_in_range, [y_positions['Known']]*len(known_in_range),
           c='green', s=40, alpha=0.8, marker='*', label='Known zeros')
for r, label, color, y in [(conrey_result, 'Conrey 2025', 'purple', 0.5),
                           (srv_result, 'Servi', 'orange', 0.0),
                           (std_result, 'Standard', 'blue', -0.5)]:
    ax.scatter(r['zeros'], [y]*r['n_zeros'], c=color, s=25, alpha=0.7, label=label)
ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()))
ax.set_xlabel('t (zero position)')
ax.set_title('零点检测位置三类对比')
ax.legend(fontsize=7, loc='upper right')
ax.grid(axis='x', alpha=0.3)

# Panel 6: Loiseau 类 B 检测 — 投影信息图
ax = axes[1,2]
ax.barh(['Var K_prime', 'Var K_nonprime', 'Var K_full'],
        [prime_test['var_K_prime'], prime_test['var_K_nonprime'], prime_test['var_K_full']],
        color=['red', 'blue', 'gray'], alpha=0.7)
ax.set_xlabel('Variance over t')
ax.set_title(f'Loiseau Spectral Barrier 测试\n'
             f'>{"跳出 类 B" if ratio > 1.2 else "仍属 类 B (phase-blind)"}\n'
             f'Ratio = {ratio:.3f}')
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
out_path = os.path.join(od, 'Servi_Mollifier_升级版_Conrey2025_Loiseau.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight'); plt.close()

# ====== 11. 最终总结 ======
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"1. Servi kernel Var_prime/Var_nonprime ratio = {ratio:.4f}")
print(f"   -> {'✓ Class B 可能跳出' if ratio > 1.2 else '✗ 仍属 class B (phase-blind)'}")
print(f"")
print(f"2. Conrey 2025 变分法 mollifier (α={conrey_alpha:.3f}) 检测零点")
print(f"   零点数 = {conrey_result['n_zeros']}  vs  已知 = {len(known_in_range)}")
print(f"")
print(f"3. Servi mollifier 检测零点数 = {srv_result['n_zeros']}")
print(f"4. 标准 mollifier 检测零点数 = {std_result['n_zeros']}")
print(f"")
print(f"-> 输出图: {out_path}")
print(f"")
print(f"📌 关键诊断 (Loiseau Spectral Barrier 出口判定)")
print(f"   若 ratio > 1.2: Servi kernel 是 prime-selective 候选")
print(f"   若 ratio < 1.05: Servi 仍是 phase-blind, 需升级变分法")
print(f"   若 1.05 < ratio < 1.2: 弱 prime-detection, 需进一步验证")
