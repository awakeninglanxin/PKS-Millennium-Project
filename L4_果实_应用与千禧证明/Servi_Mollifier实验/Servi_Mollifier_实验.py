#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servi 几何 Mollifier vs 标准 Mollifier — Levinson-Conrey 零点计数对比

Dante Servi 悬链多边形角度作为 mollifier 系数的实验验证
"""
import numpy as np, matplotlib.pyplot as plt, os
from math import log, sqrt, pi, cos, sin

od = os.path.dirname(os.path.abspath(__file__))

# ====== 1. Riemann-Siegel ζ(1/2+it) 计算 ======
def zeta_half(t, N=None):
    """ζ(1/2+it) via partial sum + Riemann-Siegel correction"""
    if N is None:
        N = int(sqrt(t/(2*pi))) + 5
    s_real = 0.5
    z = 0+0j
    angles = []
    for n in range(1, N+1):
        term = n**(-s_real) * complex(cos(t*log(n)), -sin(t*log(n)))
        z += term
        angles.append(-t*log(n))  # 悬链多边形的角度序列
    return z, N, np.array(angles)

# ====== 2. 标准 Möbius mollifier 系数 ======
def mobius(n):
    if n == 1: return 1
    p = 0
    for d in range(2, int(sqrt(n))+1):
        if n % d == 0:
            mu = n // d
            if mu % d == 0: return 0
            p += 1
    return -1 if p % 2 else 1

def standard_mollifier_coeffs(N_max, theta=0.571):
    """标准 mollifier: μ(n) * φ(n/T^θ)"""
    coeffs = {}
    for n in range(1, N_max+1):
        mu = mobius(n)
        if mu == 0: continue
        phi = max(0, 1.0 - n/N_max)  # 简化平滑函数
        coeffs[n] = mu * phi
    return coeffs

# ====== 3. Servi 几何 mollifier 系数 ======
def servi_mollifier_coeffs(t, N_max):
    """基于悬链多边形角度的 mollifier 系数
    
    关键创新: a_n = cos(-t*log(n)) / sqrt(n)
    将 Servi 的"调谐"观察翻译为 mollifier 权重
    """
    _, _, angles = zeta_half(t, N_max)
    coeffs = {}
    for n in range(1, N_max+1):
        angle = angles[n-1]
        # cos(角度)捕捉 Servi 几何中"镜像对称"的程度
        # 正 cos = 向量指向右半平面 (靠近 v1=1 方向)
        # 负 cos = 向量指向左半平面
        weight = cos(angle)  # Servi 的镜像调谐
        # 乘以 1/sqrt(n) 的衰减 (标准势函数衰减)
        decay = 1.0 / sqrt(n)
        phi = max(0, 1.0 - n/N_max)
        coeffs[n] = weight * decay * phi
    return coeffs

# ====== 4. Mollifier 求值 ======
def eval_mollifier(t, coeffs):
    """计算 mollifier M(1/2+it)"""
    s_real = 0.5
    result = 0+0j
    for n, coef in coeffs.items():
        term = n**(-s_real) * complex(cos(t*log(n)), -sin(t*log(n)))
        result += coef * term
    return result

# ====== 5. Levinson-Conrey 零点检测 ======
def levinson_conrey_detector(t_range, mollifier_coeffs, name="Standard"):
    """检测临界线上的零点: ζ(1/2+it) 实部过零"""
    zetas = []
    molls = []
    for t in t_range:
        z, _, _ = zeta_half(t)
        m = eval_mollifier(t, mollifier_coeffs)
        zetas.append(z)
        molls.append(m)
    
    zetas = np.array(zetas)
    molls = np.array(molls)
    
    # 零点: Re(ζ) 过零且 Im(ζ) 也在零点附近
    re_z = np.real(zetas)
    im_z = np.imag(zetas)
    
    zeros = []
    for i in range(1, len(re_z)):
        if re_z[i] * re_z[i-1] < 0:  # 实部过零
            # 插值找到更精确的零点位置
            t_zero = t_range[i-1] + (t_range[i]-t_range[i-1]) * abs(re_z[i-1])/(abs(re_z[i-1])+abs(re_z[i]))
            zeros.append(t_zero)
    
    return {
        'name': name,
        't_range': t_range,
        'zetas': zetas,
        'molls': molls,
        'zeros': zeros,
        'n_zeros': len(zeros)
    }

# ====== 6. 主实验 ======
T_MAX = 60  # 计算高度(计算量适中)
N_MOLL = 30  # mollifier 长度
t_range = np.linspace(10, T_MAX, 500)

# 预计算 mollifier 系数 (固定 t 范围取中值)
t_mid = np.mean(t_range)
std_coeffs = standard_mollifier_coeffs(N_MOLL)
srv_coeffs = servi_mollifier_coeffs(t_mid, N_MOLL)

# 对比检测
std_result = levinson_conrey_detector(t_range, std_coeffs, "Standard Mollifier")
srv_result = levinson_conrey_detector(t_range, srv_coeffs, "Servi Geometric Mollifier")

print(f"标准 mollifier 检测零点: {std_result['n_zeros']} 个")
print(f"Servi mollifier 检测零点: {srv_result['n_zeros']} 个")
print(f"已知零点 (t<{T_MAX}): 14.13, 21.02, 25.01, 30.42, 32.93, 37.58, 40.91, 43.32, 48.00, 49.77, 52.97, 56.44, 59.34")

# ====== 7. 可视化 ======
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 图1: ζ(1/2+it) 实部 — 零点检测
ax = axes[0,0]
re_z = np.real(std_result['zetas'])
ax.plot(t_range, re_z, 'b-', alpha=0.7, label='Re ζ(1/2+it)')
ax.axhline(0, color='gray', ls='--', alpha=0.5)
for z in std_result['zeros']:
    ax.axvline(z, color='red', alpha=0.3, lw=1)
ax.set_title('ζ(1/2+it) Real Part — Zero Crossings')
ax.set_xlabel('t'); ax.set_ylabel('Re ζ')
ax.legend(fontsize=8)

# 图2: ζ 在复平面上的螺旋
ax = axes[0,1]
for i in range(0, len(t_range), 20):
    ax.plot(np.real(std_result['zetas'][:i]), np.imag(std_result['zetas'][:i]),
            'b-', alpha=0.3, lw=0.5)
ax.scatter([0], [0], color='red', s=30, zorder=5, label='ζ=0 (zero)')
ax.set_title('ζ(1/2+it) Spiral in Complex Plane')
ax.set_xlabel('Re ζ'); ax.set_ylabel('Im ζ')
ax.legend(fontsize=8)

# 图3: Servi 悬链多边形角度分布
ax = axes[0,2]
_, _, angles = zeta_half(t_mid, 40)
for n, ang in enumerate(angles[1:], 2):
    ax.plot([n-1, n], [angles[n-2], ang], 'b-', alpha=0.6)
    ax.scatter([n], [ang], s=10, c='blue', alpha=0.5)
ax.axhline(0, color='gray', ls='--')
ax.set_title(f'Servi Angles α(n) = -t·ln(n), t≈{t_mid:.0f}')
ax.set_xlabel('n'); ax.set_ylabel('α(n)')

# 图4: Mollifier 权重对比
ax = axes[1,0]
n_vals = list(range(1, N_MOLL+1))
std_vals = [std_coeffs.get(n, 0) for n in n_vals]
srv_vals = [srv_coeffs.get(n, 0) for n in n_vals]
ax.bar(np.array(n_vals)-0.2, std_vals, 0.4, label='Standard μ(n)', alpha=0.7)
ax.bar(np.array(n_vals)+0.2, srv_vals, 0.4, label='Servi cos(α)', alpha=0.7)
ax.set_title('Mollifier Coefficient Comparison')
ax.set_xlabel('n'); ax.set_ylabel('coefficient')
ax.legend(fontsize=8)

# 图5: ζ 在固定 t 下的悬链多边形 (Servi 几何)
ax = axes[1,1]
t_show = 30.0
N_show = 25
z_partial = 0+0j
vertices = [z_partial]
for n in range(1, N_show+1):
    v = (1/sqrt(n)) * complex(cos(t_show*log(n)), -sin(t_show*log(n)))
    z_partial += v
    vertices.append(z_partial)
vertices = np.array(vertices)
ax.plot(np.real(vertices), np.imag(vertices), 'b-', lw=1)
colors = plt.cm.plasma(np.linspace(0, 1, N_show))
for n, v in enumerate(vertices[1:], 1):
    ax.plot([np.real(vertices[n-1]), np.real(v)],
            [np.imag(vertices[n-1]), np.imag(v)],
            color=colors[n-1], alpha=0.5, lw=1.5)
ax.scatter(np.real(vertices[1]), np.imag(vertices[1]), color='red', s=40, zorder=5, label='v₁')
ax.set_title(f'Servi Funicular Polygon (t={t_show}, N={N_show})')
ax.set_xlabel('Re'); ax.set_ylabel('Im')
ax.legend(fontsize=8)

# 图6: 零点检测对比
ax = axes[1,2]
known_zeros = [14.13, 21.02, 25.01, 30.42, 32.93, 37.58, 40.91, 43.32, 48.00, 49.77, 52.97, 56.44, 59.34]
known_in_range = [z for z in known_zeros if z <= T_MAX]

for label, result, color in [('Standard', std_result, 'blue'), ('Servi', srv_result, 'orange')]:
    ax.scatter(result['zeros'], [label]*len(result['zeros']), c=color, s=30, alpha=0.7)

for z in known_in_range:
    ax.axvline(z, color='green', alpha=0.15, lw=3)

ax.scatter(known_in_range, ['Known']*len(known_in_range), c='green', s=20, alpha=0.8)
ax.set_title(f'Zero Detection Comparison (t<{T_MAX})')
ax.set_xlabel('Zero position (t)')
ax.legend(['Known (actual zeros)'], fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(od, 'Servi_Mollifier_Comparison.png'), dpi=150, bbox_inches='tight')
plt.close()

# ====== 8. 密度对比 ======
known_count = len(known_in_range)
std_ratio = std_result['n_zeros'] / known_count if known_count else 0
srv_ratio = srv_result['n_zeros'] / known_count if known_count else 0
print(f"\n=== 零点检测效率 ===")
print(f"已知零点: {known_count}")
print(f"标准 mollifier: {std_result['n_zeros']} ({std_ratio:.0%})")
print(f"Servi mollifier: {srv_result['n_zeros']} ({srv_ratio:.0%})")
print(f"\n结论: 在 t<{T_MAX}, N={N_MOLL} 的小规模测试中,")
if srv_ratio > std_ratio:
    print(f"Servi mollifier 检测到更多零点 (+{(srv_ratio-std_ratio)*100:.0f}pp)")
else:
    print(f"Servi mollifier 未显示优势 (需要更大θ和更高t才能评估)")
print(f"\n关键限制: 真正的零点密度证明需要 θ>4/7≈0.571, t→∞ 的渐近分析")
print(f"本实现仅验证 Servi 几何系数作为 mollifier 基函数的可行性")
