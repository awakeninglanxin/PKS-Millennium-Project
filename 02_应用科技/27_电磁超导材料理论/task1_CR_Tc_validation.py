# ============================================================
# 预测1: 验证 T_c ∝ |CR-1|^0.5
# 用铜氧化物 ARPES 数据 (模拟) 提取四点交比, 对比 Tc
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
from scipy import stats

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 1. 铜氧化物数据集 (模拟 ARPES + Tc 文献值) ----
# kF 四点: (π,0), (0,π), (π/2,π/2), (3π/4,3π/4) 归一化到 [0,1]
# Tc 单位: K
cuprates = {
    "LSCO_x=0.10": {"kF":[(0.88,0),(0,0.88),(0.55,0.55),(0.72,0.72)],"Tc":10},
    "LSCO_x=0.12": {"kF":[(0.90,0),(0,0.90),(0.50,0.50),(0.70,0.70)],"Tc":22},
    "LSCO_x=0.15": {"kF":[(0.92,0),(0,0.92),(0.45,0.45),(0.68,0.68)],"Tc":38},
    "LSCO_x=0.18": {"kF":[(0.94,0),(0,0.94),(0.40,0.40),(0.66,0.66)],"Tc":35},
    "LSCO_x=0.22": {"kF":[(0.95,0),(0,0.95),(0.38,0.38),(0.65,0.65)],"Tc":25},
    "LSCO_x=0.26": {"kF":[(0.96,0),(0,0.96),(0.36,0.36),(0.64,0.64)],"Tc":10},
    "BSCCO_u/d=0.12":{"kF":[(0.85,0),(0,0.85),(0.52,0.52),(0.73,0.73)],"Tc":45},
    "BSCCO_u/d=0.16":{"kF":[(0.89,0),(0,0.89),(0.44,0.44),(0.69,0.69)],"Tc":65},
    "BSCCO_u/d=0.20":{"kF":[(0.91,0),(0,0.91),(0.40,0.40),(0.67,0.67)],"Tc":78},
    "BSCCO_u/d=0.24":{"kF":[(0.93,0),(0,0.93),(0.38,0.38),(0.66,0.66)],"Tc":60},
    "YBCO_d=0.50":  {"kF":[(0.86,0),(0,0.86),(0.48,0.48),(0.70,0.70)],"Tc":55},
    "YBCO_d=0.70":  {"kF":[(0.90,0),(0,0.90),(0.42,0.42),(0.68,0.68)],"Tc":85},
    "YBCO_d=0.90":  {"kF":[(0.92,0),(0,0.92),(0.40,0.40),(0.67,0.67)],"Tc":92},
}

def cross_ratio_kF(k1,k2,k3,k4):
    """费米面四点交比: CR = |k1-k3|·|k2-k4| / |k1-k4|·|k2-k3|"""
    d13 = np.sqrt((k1[0]-k3[0])**2 + (k1[1]-k3[1])**2)
    d24 = np.sqrt((k2[0]-k4[0])**2 + (k2[1]-k4[1])**2)
    d14 = np.sqrt((k1[0]-k4[0])**2 + (k1[1]-k4[1])**2)
    d23 = np.sqrt((k2[0]-k3[0])**2 + (k2[1]-k3[1])**2)
    return d13*d24/(d14*d23 + 1e-6)

CR_vals, Tc_vals, labels = [], [], []
for name, d in cuprates.items():
    cr = cross_ratio_kF(*d["kF"])
    CR_vals.append(cr)
    Tc_vals.append(d["Tc"])
    labels.append(name)

CR_arr = np.array(CR_vals)
Tc_arr = np.array(Tc_vals)
delta_CR = abs(CR_arr - 1)

# ---- 2. 拟合 T_c ∝ |CR-1|^ν ----
log_dCR = np.log10(delta_CR)
log_Tc = np.log10(Tc_arr)
slope, intercept, r_val, p_val, _ = stats.linregress(log_dCR, log_Tc)
nu_fit = slope

print(f"=== PKS预测验证: T_c ∝ |CR-1|^ν ===")
print(f"  ν观测 = {nu_fit:.3f}")
print(f"  ν预测 = 0.500")
print(f"  R^2 = {r_val**2:.3f}, p = {p_val:.4f}")
print(f"  偏差 = {abs(nu_fit-0.5)/0.5*100:.1f}%")

# ---- 3. 可视化 ----
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

ax = axes[0,0]
ax.scatter(delta_CR, Tc_arr, c='#DC2626', s=60, zorder=5)
dCR_grid = np.logspace(-2, 0, 100)
Tc_pred = 10**(intercept) * dCR_grid**nu_fit
ax.plot(dCR_grid, Tc_pred, 'b-', lw=2, label=f'fit: Tc={10**intercept:.1f}*|CR-1|^{nu_fit:.3f}')
ax.plot(dCR_grid, 10**(intercept)*dCR_grid**0.5, 'g--', lw=2, label='PKS预测: ν=0.5')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('|CR - 1|'); ax.set_ylabel('Tc (K)')
ax.set_title(f'Tc vs |CR-1| (R^2={r_val**2:.3f}, nu={nu_fit:.3f})', fontweight='bold')
ax.legend(fontsize=8)

ax = axes[0,1]
for name in cuprates:
    k1,k2,k3,k4 = cuprates[name]["kF"]
    ax.plot([k1[0]],[k1[1]],'ro',ms=3); ax.plot([k2[0]],[k2[1]],'bo',ms=3)
ax.set_xlabel('kx (pi/a)'); ax.set_ylabel('ky (pi/a)')
ax.set_title('费米面四点采样位置', fontweight='bold')
ax.set_xlim(0,1); ax.set_ylim(0,1)

ax = axes[1,0]
families = {"LSCO":[], "BSCCO":[], "YBCO":[]}
colors = {"LSCO":"#DC2626","BSCCO":"#2563EB","YBCO":"#059669"}
for n,t,d in zip(labels, delta_CR, Tc_arr):
    for f in families:
        if f in n: families[f].append((t,d))
for f, pts in families.items():
    if pts:
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        ax.scatter(xs,ys,c=colors[f],s=50,label=f, zorder=5)
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('|CR - 1|'); ax.set_ylabel('Tc (K)')
ax.set_title('按材料族分组', fontweight='bold')
ax.legend(fontsize=8)

ax = axes[1,1]; ax.axis('off')
info = [
    "PKS预测1: Tc vs CR 验证", "="*40, "",
    f"nu观测 = {nu_fit:.3f}, nu预测 = 0.500",
    f"R^2 = {r_val**2:.3f}, p = {p_val:.4f}",
    f"偏差 = {abs(nu_fit-0.5)/0.5*100:.1f}%",
    "", "材料和Tc:"
]
for name,d in cuprates.items():
    info.append(f"  {name}: Tc={d['Tc']}K, CR={cross_ratio_kF(*d['kF']):.3f}")

for i,line in enumerate(info):
    ax.text(0.02,0.98-i*0.038, line, transform=ax.transAxes,
            fontsize=8, color='#DC2626' if 'nu' in line else '#1F2937', va='top')

fig.suptitle('Task1: PKS T_c vs CR 验证', fontsize=14, fontweight='bold')
fig.tight_layout()
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_supercon_CR_Tc.png")
fig.savefig(p); plt.close(fig)
print(f"\n[chart] {p}")
