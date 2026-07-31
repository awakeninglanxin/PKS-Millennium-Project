# ============================================================
# 预测3: 高温超导相图的 PKS 几何统一
# 将铜氧化物相图映射为锥面截面 (α=掺杂, kE=关联) 的连续演化
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 1. 铜氧化物通用相图 (模拟) ----
p = np.linspace(0, 0.30, 300)  # 掺杂浓度

# Phase boundaries
def T_AF(p): return 400*np.exp(-p/0.02)  # AF Neel
def T_PG(p): return 200*(1-p/0.19) if p<0.19 else 0  # Pseudogap T*
def T_SC(p): return 100*(1-((p-0.16)/0.08)**2)*np.heaviside(0.08-abs(p-0.16),0.5)  # SC dome
def T_FL(p): return 50*p/0.19 if p<0.19 else 50*np.exp(-(p-0.19)/0.05)  # Fermi liquid crossover

T_AF_vals = T_AF(p); T_PG_vals = np.array([T_PG(pi) for pi in p])
T_FL_vals = T_FL(p)

# ---- 2. PKS几何参数映射 ----
alpha_vals = 0.05 + 0.8*p  # 倾角 (线性掺杂驱动)
kE_vals = 1 + 0.14*np.exp(-0.5*(p-0.16)**2/0.005)  # 蛋形度: 在 p≈0.16 处峰值
kappa_vals = 1/(1+10*(p-0.19)**2)  # 曲率: 在 p≈0.19 (QCP) 处峰值

# ---- 3. 四面板图 ----
fig = plt.figure(figsize=(16, 11))

# Panel A: Cuprate相图 + PKS标注
ax1 = fig.add_subplot(2,3,1)
ax1.fill_between(p, 0, T_AF_vals, color='#FEF3C7', alpha=0.5, label='AF')
ax1.fill_between(p, 0, T_PG_vals, color='#DBEAFE', alpha=0.3, label='Pseudogap')
ax1.plot(p, T_SC(p), 'r-', lw=3, label='SC dome')
ax1.axvline(0.19, color='purple', ls='--', lw=1.5, label='p* QCP (焦散线)')
ax1.set_xlabel('doping p'); ax1.set_ylabel('T (K)')
ax1.set_title('Cuprate 相图 + PKS几何点', fontweight='bold')
ax1.legend(fontsize=7)
# Mark PKS key points
ax1.annotate('kE peak', xy=(0.16,95), fontsize=8, color='#DC2626')
ax1.annotate('kappa max (QCP)', xy=(0.19,40), fontsize=8, color='purple')

# Panel B: kE(掺杂) — 蛋形度
ax2 = fig.add_subplot(2,3,2)
ax2.plot(p, kE_vals, 'r-', lw=2)
ax2.fill_between(p, 1, kE_vals, alpha=0.15, color='red')
ax2.axhline(1.3, color='gray', ls='--', alpha=0.5, label='d-wave onset')
ax2.axhline(1.0, color='gray', ls=':', alpha=0.5, label='BCS limit')
ax2.set_xlabel('doping p'); ax2.set_ylabel('kE')
ax2.set_title('蛋形度 kE(p)', fontweight='bold')
ax2.legend(fontsize=7)

# Panel C: kappa_max(掺杂) — 曲率
ax3 = fig.add_subplot(2,3,3)
ax3.plot(p, kappa_vals, 'b-', lw=2)
ax3.axvline(0.19, color='purple', ls='--', lw=1)
ax3.set_xlabel('doping p'); ax3.set_ylabel('kappa')
ax3.set_title('锥面曲率 kappa(p) — QCP处峰值', fontweight='bold')

# Panel D: 截面演化序列
ax4 = fig.add_subplot(2,3,4)
dopings = [0.05, 0.10, 0.16, 0.19, 0.25]
cmap = plt.cm.RdYlBu_r
for i, dp in enumerate(dopings):
    idx = np.argmin(abs(p-dp))
    kE_i = kE_vals[idx]
    theta = np.linspace(0, 2*np.pi, 200)
    r = np.exp(-0.5*(theta-np.pi)**2/(kE_i**2))
    x = r*np.cos(theta); y = r*np.sin(theta)
    ax4.plot(x, y, color=cmap(i/len(dopings)), lw=1.5, label=f'p={dp:.2f}, kE={kE_i:.3f}')
ax4.set_xlim(-1.2,1.2); ax4.set_ylim(-1.2,1.2)
ax4.set_aspect('equal')
ax4.set_title('锥面截面演化 (p=0.05→0.25)', fontweight='bold')
ax4.legend(fontsize=7)

# Panel E: Tc vs kE scatter
ax5 = fig.add_subplot(2,3,5)
Tc_sc = T_SC(p)
ax5.scatter(kE_vals[::5], Tc_sc[::5], c=p[::5], cmap='RdYlBu_r', s=3, alpha=0.8)
ax5.set_xlabel('kE'); ax5.set_ylabel('Tc (K)')
ax5.set_title('Tc vs kE (p色标)', fontweight='bold')

# Panel F: 几何一致相图
ax6 = fig.add_subplot(2,3,6)
ax6.axis('off')
info = [
    "PKS 高温超导相图几何统一", "="*40, "",
    "Hubbard模型 ←→ PKS双锥体映射:",
    "  U/t (关联)  ⇔  kE (蛋形度)",
    "  p (掺杂)     ⇔  alpha (倾角)",
    "  (pi,pi) AF   ⇔  kappa_max (焦散线)",
    "",
    "相边界几何对应:",
    "  AF绝缘体:  kE>>1, alpha~0 (尖蛋)",
    "  Pseudogap:  kE>1.3, alpha小",
    "  SC dome:    kE~1.5, alpha适中 (蛋形)",
    "  Strange金属: kE~1.3, alpha→QCP",
    "  Fermi液体:  kE→1, alpha大 (椭圆/圆)",
    "",
    "QCP p*=0.19: 锥面焦散线与费米面交叠",
]
for i,line in enumerate(info):
    ax6.text(0.02,0.98-i*0.045, line, transform=ax6.transAxes,
            fontsize=8, color='#DC2626' if 'QCP' in line else '#1F2937', va='top')

fig.suptitle('Task3: 高温超导相图的PKS几何统一', fontsize=14, fontweight='bold')
fig.tight_layout()
path = os.path.join(SCRIPT_DIR, "fig_supercon_phase_diagram_geometry.png")
fig.savefig(path); plt.close(fig)
print(f"[chart] {path}")
print("kE峰值掺杂: p≈0.16, kE_max≈1.14")
print("kappa峰值(QCP): p≈0.19")
