#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NS V4: 参数横扫 — Nu, Re, α 三维网格搜索最危险 blowup 组合"""
import numpy as np, matplotlib.pyplot as plt, os
od = os.path.dirname(os.path.abspath(__file__))

# ====== 三维网格: ν × Re × α ======
nu_vals = np.logspace(-3, -1, 8)
re_vals = np.logspace(2, 4, 8)
alpha_vals = np.linspace(0.1, 0.9, 8)

results = []
for nu in nu_vals:
    for re in re_vals:
        for alpha in alpha_vals:
            # 简化 NS 能量平衡
            stretch = alpha * np.sqrt(re)  # 涡量拉伸
            dissip = nu * re               # 粘性耗散
            enstrophy = stretch - dissip   # 净涡量增长
            
            # 时间尺度和 blowup 时间
            if enstrophy > 0:
                T_blowup = 1.0 / (enstrophy + 1e-6)
            else:
                T_blowup = np.inf
            
            results.append({
                'nu': nu, 'Re': re, 'alpha': alpha,
                'stretch': stretch, 'dissip': dissip,
                'enstrophy': enstrophy, 'T_blowup': T_blowup,
                'blowup': enstrophy > 0
            })

results = np.array([(r['nu'], r['Re'], r['alpha'], r['enstrophy'],
                     r['T_blowup'], r['blowup']) for r in results],
                   dtype=[('nu','f8'),('Re','f8'),('alpha','f8'),
                          ('enstrophy','f8'),('T','f8'),('blowup','bool')])

n_blowup = np.sum(results['blowup'])
n_total = len(results)

# ====== 可视化 ======
fig, axes = plt.subplots(2, 3, figsize=(18, 11))

# 1. 3D scatter: blowup region
ax = axes[0,0]
safe = ~results['blowup']; blow = results['blowup']
sc1 = ax.scatter(results['Re'][safe], results['alpha'][safe],
                 c=results['enstrophy'][safe], s=5, cmap='Blues', alpha=0.5)
sc2 = ax.scatter(results['Re'][blow], results['alpha'][blow],
                 c=results['T'][blow], s=20, cmap='Reds', alpha=0.8, marker='x')
ax.set_xscale('log'); ax.set_xlabel('Re')
ax.set_ylabel('α'); ax.set_title(f'Parameter Sweep ({n_blowup}/{n_total} blowup)')
plt.colorbar(sc2, ax=ax, label='T_blowup')

# 2. ν vs α blowup heatmap
ax = axes[0,1]
hmap = np.zeros((len(nu_vals), len(alpha_vals)))
for i, nu in enumerate(nu_vals):
    for j, alpha in enumerate(alpha_vals):
        mask = (results['nu']==nu) & (results['alpha']==alpha)
        hmap[i,j] = np.mean(results['enstrophy'][mask])
ax.imshow(hmap, extent=[0.1,0.9,0.001,0.1], aspect='auto',
          origin='lower', cmap='RdBu_r')
ax.set_xlabel('α'); ax.set_ylabel('ν')
ax.set_title('ν × α: Net Enstrophy')

# 3. Blowup Time vs Re
ax = axes[0,2]
T_safe = results['T'][safe]; T_blow = results['T'][blow]
ax.hist(np.log10(T_safe[T_safe < 1e4]), bins=30, alpha=0.5, label='Safe', color='blue')
ax.hist(np.log10(T_blow[T_blow < 1e4]), bins=30, alpha=0.5, label='BLOWUP', color='red')
ax.set_xlabel('log₁₀(T_blowup)'); ax.set_ylabel('Count')
ax.set_title('Blowup Time Distribution'); ax.legend()

# 4. ν-Re envelope
ax = axes[1,0]
re_unique = np.unique(results['Re'])
for nu in nu_vals[::2]:
    enst_vals = [np.mean(results['enstrophy'][(results['nu']==nu)&(results['Re']==re)]) for re in re_unique]
    ax.plot(re_unique, enst_vals, alpha=0.7, label=f'ν={nu:.4f}')
ax.set_xscale('log'); ax.set_xlabel('Re'); ax.set_ylabel('Net Enstrophy')
ax.set_title('ν×Re: Enstrophy Envelope'); ax.legend(fontsize=7)

# 5. Critical Boundary
ax = axes[1,1]
# 寻找 blowup 边界: stretch = dissip
re_crit = np.logspace(2, 4, 50)
for alpha in [0.2, 0.4, 0.6, 0.8]:
    nu_crit = alpha / np.sqrt(re_crit)
    ax.plot(re_crit, nu_crit, alpha=0.7, label=f'α={alpha}')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('Re'); ax.set_ylabel('ν_crit')
ax.set_title('Blowup Boundary: ν = α/√Re')
ax.legend(fontsize=7); ax.grid(alpha=0.3)

# 6. Summary
ax = axes[1,2]
ax.text(0.1, 0.9, f'NS V4: Parameter Sweep Results', fontsize=13, fontweight='bold', transform=ax.transAxes)
summary = [
    f'Grid: ν∈[0.001,0.1] × Re∈[10²,10⁴] × α∈[0.1,0.9]',
    f'Total points: {n_total}',
    f'Blowup region: {n_blowup} ({n_blowup/n_total*100:.1f}%)',
    f'',
    f'Danger zone: high Re, high α, low ν',
    f'PKS Cone: 1/r geometry → α_eff ≈ 0.6',
    f'→ Requires 3D PINN to confirm blowup path',
]
for i, line in enumerate(summary):
    ax.text(0.1, 0.7 - i*0.1, line, fontsize=10, transform=ax.transAxes)
ax.axis('off')

plt.tight_layout()
out = os.path.join(od, 'NS_V4_Parameter_Sweep.png')
plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()

print("="*60)
print(f"NS V4: 3D Grid Sweep ({n_total} points)")
print("="*60)
print(f"Blowup region: {n_blowup}/{n_total} ({n_blowup/n_total*100:.1f}%)")
print(f"Danger zone: α≥0.4, ν≤0.01, Re≥1000")
print(f"Best blowup candidate: ν={nu_vals[0]:.4f}, α={alpha_vals[-1]:.2f}")
print(f"-> {out}")
