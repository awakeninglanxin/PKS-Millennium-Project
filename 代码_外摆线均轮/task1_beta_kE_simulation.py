# ============================================================
# Task 1: k_E vs beta — PKS双锥体耦合模拟验证
# 核心: beta = 电性/磁性锥曲率比 → k_E - 1 = (alpha/2)*beta
# 输出: fig_task1_beta_kE_simulation.png
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
plt.rcParams.update({"figure.dpi":150, "savefig.dpi":200, "savefig.bbox":"tight"})

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALPHA_FS = 1.0 / 137.036

# ---- 1. PKS双锥体几何模型 ----
def egg_degree(z0, alpha):
    """从双锥体截面参数直接计算蛋形度 k_E"""
    yp = 1.0 / max(z0 - 1.5*np.sin(alpha), 0.05)
    ym = 1.0 / (z0 + 1.5*np.sin(alpha))
    return abs(yp / ym)

def plasma_beta(z0, alpha):
    """beta = p_elec/p_mag。PKS: 磁性锥曲率 kappa_mag ∝ 1/z0^2"""
    kappa_mag = 1.0 / (z0**2 + 0.1)
    return alpha * kappa_mag / ALPHA_FS

# ---- 2. 理论预测 ----
def theory_kE(beta):
    return 1 + ALPHA_FS / 2 * beta

# ---- 3. 生成合成数据 ----
def generate(n=300, seed=42):
    np.random.seed(seed)
    z0s = np.random.uniform(1.5, 8.0, n)
    alphas = np.random.uniform(0.05, 0.40, n)
    beta_list, kE_list = [], []
    for z, a in zip(z0s, alphas):
        b = plasma_beta(z, a)
        k0 = egg_degree(z, a)
        k = k0 + np.random.normal(0, 0.02*k0)
        beta_list.append(b); kE_list.append(k)
    return np.array(beta_list), np.array(kE_list), z0s, alphas

# ---- 4. 分析 ----
beta, kE, z0s, alphas = generate(300)
slope, intercept, r_val, p_val, std_err = stats.linregress(beta, kE)
r2 = r_val**2
alpha_eff = 2 * slope

print(f"=== k_E vs beta 双锥体耦合分析 ===")
print(f"  斜率 C = {slope:.4f} +/- {std_err:.4f}")
print(f"  截距 = {intercept:.4f} (期望 ~1.0)")
print(f"  R^2 = {r2:.4f}, p = {p_val:.4f}, N = {len(beta)}")
print(f"  观测 alpha_eff = {alpha_eff:.6f} vs 真实 {ALPHA_FS:.6f}")
print(f"  偏差 = {abs(alpha_eff-ALPHA_FS)/ALPHA_FS*100:.2f}%")

# ---- 5. 四面板图 ----
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

ax = axes[0,0]
ax.scatter(beta, kE, c='#DC2626', alpha=0.4, s=15, edgecolors='none')
bg = np.linspace(0, beta.max(), 100)
ax.plot(bg, intercept+slope*bg, 'b-', lw=2, label=f'fit: kE={intercept:.3f}+{slope:.3f}*beta')
ax.plot(bg, theory_kE(bg), 'g--', lw=2, label='theory: kE=1+(alpha/2)*beta')
ax.set_xlabel('beta = p_elec / p_mag'); ax.set_ylabel('kE')
ax.set_title(f'PKS双锥体: kE vs beta (R^2={r2:.3f})', fontweight='bold')
ax.legend(fontsize=8)

ax = axes[0,1]
res = kE - (intercept + slope*beta)
ax.scatter(beta, res, c='#2563EB', alpha=0.4, s=12)
ax.axhline(0, color='gray', ls='--')
ax.set_xlabel('beta'); ax.set_ylabel('residuals')
ax.set_title('残差分布', fontweight='bold')

ax = axes[1,0]
sc = ax.scatter(z0s, alphas, c=kE, cmap='RdYlBu_r', alpha=0.6, s=12)
plt.colorbar(sc, ax=ax, label='kE')
ax.set_xlabel('z0'); ax.set_ylabel('alpha')
ax.set_title('kE 在 (z0, alpha) 的分布', fontweight='bold')

ax = axes[1,1]; ax.axis('off')
info = [
    "PKS双锥体耦合验证 — Task 1", "="*40, "",
    "ab=1 → a=x(电性锥) + b=1/x(磁性锥)",
    f"alpha_FS = 1/137.036 = {ALPHA_FS:.6f}",
    f"alpha_eff(观测) = {alpha_eff:.6f}",
    f"偏差 = {abs(alpha_eff-ALPHA_FS)/ALPHA_FS*100:.2f}%",
    "", f"斜率 C = {slope:.4f}", f"截距 = {intercept:.4f} (期望 1.0)",
    f"R^2 = {r2:.4f}", f"p = {p_val:.2e}",
    "", "beta<<1: 磁性锥主导 → kE→1",
    "beta~1: 两锥平衡 → kE~1.5",
    "beta>>1: 电性锥主导 → 蛋形破裂",
]
for i, line in enumerate(info):
    c = '#DC2626' if 'alpha' in line.lower() and '=' in line else '#1F2937'
    ax.text(0.02, 0.98-i*0.045, line, transform=ax.transAxes,
            fontsize=9, fontweight='bold' if i<2 else 'normal', color=c, va='top')

fig.suptitle('Task 1: PKS双锥体 kE vs beta 模拟验证', fontsize=14, fontweight='bold')
fig.tight_layout()
path = os.path.join(SCRIPT_DIR, "fig_task1_beta_kE_simulation.png")
fig.savefig(path); plt.close(fig)
print(f"\n[chart] {path}")
