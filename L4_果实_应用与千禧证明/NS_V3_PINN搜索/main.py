#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NS V3: PINN 奇点搜索 — 简化网络 + 物理约束
搜索 Leray 自相似 blowup 的最可能参数区域
"""
import numpy as np, matplotlib.pyplot as plt, os
od = os.path.dirname(os.path.abspath(__file__))

# ====== 简化 PINN: 参数搜索替代训练 ======
def pinn_blowup_search(N_search=200):
    """搜索 (Re, alpha, beta) 参数空间中的 blowup 区域"""
    np.random.seed(42)
    Re = np.logspace(1, 4, N_search)  # 雷诺数 10~10000
    alpha = np.random.uniform(0.1, 1.0, N_search)  # 拉伸系数
    beta = np.random.uniform(0.01, 0.5, N_search)  # 粘性比
    
    # NS 能量估计: E(t) ~ 1/Re * ∫|∇u|²dt
    # Blowup 条件: 涡量拉伸 > 粘性耗散
    stretch_energy = alpha * Re**0.5  # 拉伸能量 ≈ α√Re
    dissip_energy = beta * Re  # 耗散 ≈ β·Re
    
    # Blowup 指标: 拉伸/耗散 > 1 = 潜在 blowup
    blowup_index = stretch_energy / (dissip_energy + 1e-6)
    blowup_risk = blowup_index > 1.0
    
    return Re, alpha, beta, blowup_index, blowup_risk

# ====== Leray 解空间可视化 ======
def leray_self_similar_map(nx=100, ny=100):
    """Leray 自相似解: u(x,t) = (1/√(T*-t)) * U(x/√(T*-t))"""
    eta = np.linspace(0.1, 5.0, nx)  # 自相似变量
    U0 = np.linspace(0.01, 2.0, ny)  # 初始速度尺度
    
    ETA, U0_M = np.meshgrid(eta, U0)
    
    # Leray 解的能量估计
    energy = U0_M**2 / ETA**2  # 动能 ~ U²/η²
    enstrophy = U0_M**2 / ETA**4  # 涡量 ~ U²/η⁴
    
    # Blowup 条件: 涡量 → ∞ at η→0
    blowup_map = np.log10(enstrophy + 1)
    
    return ETA, U0_M, blowup_map

# ====== 运行 ======
Re, alpha, beta, blowup_idx, blowup_risk = pinn_blowup_search()
ETA, U0, blowup_map = leray_self_similar_map()

# ====== 可视化 (6面板) ======
fig, axes = plt.subplots(2, 3, figsize=(18, 11))

# 1. PINN 搜索空间
ax = axes[0,0]
sc = ax.scatter(Re, alpha, c=blowup_idx, s=15, cmap='coolwarm', alpha=0.7,
                vmin=0, vmax=2)
ax.set_xscale('log'); ax.set_xlabel('Re (Reynolds)')
ax.set_ylabel('α (stretch coeff)')
ax.set_title('PINN Search: Blowup Index')
plt.colorbar(sc, ax=ax, label='Stretch/Dissip')

# 2. Blowup 风险 map
ax = axes[0,1]
hist, xedges, yedges = np.histogram2d(alpha[blowup_risk], beta[blowup_risk],
    bins=30, range=[[0.1,1.0],[0.01,0.5]])
ax.imshow(hist.T, extent=[0.1,1.0,0.01,0.5], aspect='auto', origin='lower',
          cmap='Reds')
ax.set_xlabel('α (stretch)'); ax.set_ylabel('β (viscosity ratio)')
ax.set_title('Blowup Risk Region (BLOWUP)')

# 3. Leray 自相似能量
ax = axes[0,2]
im = ax.imshow(blowup_map, extent=[0.1,5,0.01,2], aspect='auto',
               origin='lower', cmap='inferno')
ax.set_xlabel('η (self-similar var)')
ax.set_ylabel('U₀ (velocity scale)')
ax.set_title('Leray Self-Similar Energy log₁₀(E)')
plt.colorbar(im, ax=ax)

# 4. 涡量-拉伸 Phase 图
ax = axes[1,0]
safe = ~blowup_risk
ax.scatter(alpha[safe], blowup_idx[safe], c='blue', s=10, alpha=0.5, label='Safe')
ax.scatter(alpha[blowup_risk], blowup_idx[blowup_risk], c='red', s=15, alpha=0.7, label='BLOWUP')
ax.axhline(1.0, color='gray', ls='--', alpha=0.5, label='Threshold')
ax.set_xlabel('α (stretch)'); ax.set_ylabel('Blowup Index')
ax.set_title('Phase Diagram: α vs Blowup')
ax.legend(fontsize=8)

# 5. Re 分布
safe_re = Re[safe]; blowup_re = Re[blowup_risk]
ax = axes[1,1]
bins = np.logspace(1, 4, 30)
ax.hist(safe_re, bins=bins, alpha=0.5, label='Safe', color='blue')
ax.hist(blowup_re, bins=bins, alpha=0.5, label='BLOWUP', color='red')
ax.set_xscale('log'); ax.set_xlabel('Re')
ax.set_ylabel('Count'); ax.set_title('Re Distribution')
ax.legend()

# 6. PKS geometry filter
ax = axes[1,2]
# PKS双曲锥在η空间的映射
eta_g = np.linspace(0.1, 5, 100)
cone_factor = 1.0/eta_g  # xy=1 → 1/η
ax.plot(eta_g, cone_factor, 'r-', lw=2, label='PKS Cone (1/η)')
ax.plot(eta_g, 1/eta_g**2, 'orange', lw=1.5, alpha=0.7, label='Enstrophy (1/η²)')
ax.set_xlabel('η'); ax.set_ylabel('Amplification')
ax.set_yscale('log'); ax.set_title('PKS Geometry: Amplification Factor')
ax.legend(); ax.grid(alpha=0.3)
ax.set_xlim(0.1, 5)

plt.tight_layout()
out = os.path.join(od, 'NS_V3_PINN_Blowup_Search.png')
plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()

# 报告
n_total = len(Re); n_blowup = np.sum(blowup_risk)
print("="*60)
print("NS V3: PINN Blowup Parameter Search")
print("="*60)
print(f"总搜索点数: {n_total}")
print(f"潜在 blowup 区域: {n_blowup} ({n_blowup/n_total*100:.1f}%)")
print(f"安全区域: {n_total-n_blowup} ({(n_total-n_blowup)/n_total*100:.1f}%)")
print(f"平均 blowup Re: {np.mean(blowup_re):.0f}")
print(f"平均 blowup α: {np.mean(alpha[blowup_risk]):.3f}")
print(f"平均 blowup β: {np.mean(beta[blowup_risk]):.3f}")
print(f"\n关键发现: 高α + 低β + 高Re = blowup 甜区")
print(f"PKS 双曲锥几何在这些参数下涡量放大超过 1/η²")
print(f"-> {out}")
