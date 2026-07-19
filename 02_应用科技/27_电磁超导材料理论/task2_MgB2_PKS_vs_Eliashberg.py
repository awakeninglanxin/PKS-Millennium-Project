# ============================================================
# 预测2: PKS vs Eliashberg 交叉验证 — MgB2 (BCS框架, 已知λ)
# 检验 k_E→1 时 T_c^PKS = T_c^Eliashberg 的精度
# ============================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm, os
_cache = matplotlib.get_cachedir()
for _f in os.listdir(_cache):
    if _f.endswith('.json'):
        try: os.remove(os.path.join(_cache, _f))
        except OSError: pass
fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"figure.dpi":150,"savefig.dpi":200,"savefig.bbox":"tight"})

# ---- MgB2 已知参数 (文献值) ----
MgB2 = {
    "omega_log": 670,    # K, 对数平均声子频率
    "lambda_ep": 0.87,   # 总电声耦合 σ带+π带
    "mu_star": 0.12,     # Coulomb pseudopotential
    "Tc_exp": 39.0,      # K, 实验Tc
    "U_over_t": 0.01,    # MgB2 几乎无关联
}

# ---- Eliashberg (McMillan) ----
def Tc_mcmillan(omega_log, lam, mu_star):
    return omega_log/1.20 * np.exp(-1.04*(1+lam)/(lam - mu_star*(1+0.62*lam)))

Tc_eli = Tc_mcmillan(**{k:MgB2[k] for k in ["omega_log","lambda_ep","mu_star"]})
print(f"Eliashberg/McMillan: Tc = {Tc_eli:.1f} K (实验: {MgB2['Tc_exp']} K)")

# ---- PKS Tc with varying k_E (should converge to BCS when kE→1) ----
def Tc_pks(omega_log, lam_ep, kE, doping_alpha=0.0):
    CR = 1 + 0.5*(kE-1)
    g = (kE**(CR-1)/(1+doping_alpha**2)) * (1/(1-np.exp(-1/(kE-1+1e-6))+1e-6))
    lam_pks = lam_ep * max(g, 0.01)
    return 1.14*omega_log * np.exp(-1/lam_pks)

kE_range = np.linspace(1.001, 1.5, 50)
Tc_pks_vals = [Tc_pks(MgB2["omega_log"], MgB2["lambda_ep"], k) for k in kE_range]

print(f"\nPKS (kE=1.001→BCS极限): Tc = {Tc_pks_vals[0]:.1f} K")
print(f"PKS vs Eliashberg 偏差: {abs(Tc_pks_vals[0]-Tc_eli)/Tc_eli*100:.1f}%")

# ---- 绘图 ----
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

ax = axes[0]
ax.plot(kE_range, Tc_pks_vals, 'r-', lw=2, label='PKS (MgB2)')
ax.axhline(Tc_eli, color='blue', ls='--', lw=2, label=f'Eliashberg: {Tc_eli:.1f}K')
ax.axhline(MgB2["Tc_exp"], color='green', ls=':', lw=2, label=f'实验: {MgB2["Tc_exp"]}K')
ax.set_xlabel('kE (蛋形度)'); ax.set_ylabel('Tc (K)')
ax.set_title('PKS vs Eliashberg: MgB2', fontweight='bold')
ax.legend(fontsize=8)
ax.text(0.02,0.95, f'kE=1.001: Tc={Tc_pks_vals[0]:.1f}K\n偏差={abs(Tc_pks_vals[0]-Tc_eli)/Tc_eli*100:.1f}%',
        transform=ax.transAxes, fontsize=9, va='top')

ax = axes[1]
doping = np.linspace(0, 0.3, 50)
alphas = 0.05 + 0.8*doping
Tc_dome = [Tc_pks(MgB2["omega_log"], MgB2["lambda_ep"]*1.5, 1+0.15*np.exp(-0.5*(d-0.16)**2/0.01), a)
           for d,a in zip(doping, alphas)]
ax.plot(doping, Tc_dome, 'r-', lw=2)
ax.set_xlabel('掺杂浓度 p'); ax.set_ylabel('预测 Tc (K)')
ax.set_title('PKS预测: SC dome (模拟)', fontweight='bold')

fig.suptitle('Task2: PKS vs Eliashberg 交叉验证', fontsize=14, fontweight='bold')
fig.tight_layout()
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_supercon_PKS_vs_Eliashberg.png")
fig.savefig(p); plt.close(fig)
print(f"\n[chart] {p}")
