"""
超参数可视化对比实验 — 向量化快速版
标准 M vs 逆 M, 在两种不同 Re 轴视图下对比
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import time, json, warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("  标准 M vs 逆 M — 超参数可视化对比 (向量化)")
print("=" * 70)

# ============================================================
# 网格 (降为 400x400 保证速度)
# ============================================================
W = H = 400

# 标准 M: Re ∈ [-2.5, 1.5], Im ∈ [-3, 3]
re_s = np.linspace(-2.5, 1.5, W)
im_s = np.linspace(-3.0, 3.0, H)
C_s = re_s[None,:] + 1j*im_s[:,None]

# 逆 M: Re ∈ [-2.0, 4.0], Im ∈ [-3, 3]
re_i = np.linspace(-2.0, 4.0, W)
im_i = np.linspace(-3.0, 3.0, H)
C_i = re_i[None,:] + 1j*im_i[:,None]

print(f"网格: {W}x{H} = {W*H} 点")
print(f"标准 M: Re[-2.5,1.5] Im[-3,3]")
print(f"逆   M: Re[-2.0,4.0] Im[-3,3]")

# ============================================================
# 超参数 ↔ c 映射
# ============================================================
lr_lo, lr_hi = 1e-4, 0.1
do_lo, do_hi = 0.0, 0.5

def c_to_hparam(C, re_range, im_range):
    re = np.clip(np.real(C), re_range[0], re_range[1])
    im = np.clip(np.imag(C), im_range[0], im_range[1])
    lr = lr_lo + (re-re_range[0])/(re_range[1]-re_range[0])*(lr_hi-lr_lo)
    do = do_lo + (im-im_range[0])/(im_range[1]-im_range[0])*(do_hi-do_lo)
    return lr, do

# ============================================================
# 代理质量函数
# ============================================================
np.random.seed(42)

def quality(lr, dropout):
    """模拟验证集准确率: 甜区 + 发散边界"""
    lr_t = np.exp(-0.5*((lr-0.01)/0.03)**2)
    do_t = np.exp(-0.5*((dropout-0.2)/0.15)**2)
    div  = 1.0/(1.0+np.exp(15*(lr-0.05)))
    acc  = 0.5 + 0.4*lr_t*do_t*div
    acc += 0.02*np.random.randn(*acc.shape)
    return np.clip(acc, 0, 1)

lr_s, do_s = c_to_hparam(C_s, (-2.5,1.5), (-3,3))
Q_s = quality(lr_s, do_s)

lr_i, do_i = c_to_hparam(C_i, (-2,4), (-3,3))
Q_i = quality(lr_i, do_i)

print(f"质量场: std={Q_s.mean():.3f}±{Q_s.std():.3f} (标准) | {Q_i.mean():.3f}±{Q_i.std():.3f} (逆)")

# ============================================================
# 向量化逃逸时间计算 (一次性分配, 无 Python 循环开销)
# ============================================================
print("\n▶ 计算逃逸时间场...")

def escape_field(C, formula, MAX_ITER=300, BAILOUT=1e4):
    """完全向量化"""
    Z = np.zeros_like(C, dtype=np.complex128)
    ns = np.full(C.shape, MAX_ITER, dtype=np.float64)
    active = np.ones(C.shape, dtype=bool)
    
    if formula == 'inv':
        C_safe = np.where(np.abs(C)<1e-12, 1e-12+0j, C)
        P = 1.0 / C_safe
    else:
        P = C.copy()
    
    np.seterr(over='ignore', invalid='ignore')
    
    for n in range(MAX_ITER):
        Z = np.where(active, Z*Z + P, Z)
        absZ = np.abs(Z)
        esc = absZ > BAILOUT
        new_esc = esc & active
        if n < MAX_ITER-1:
            with np.errstate(invalid='ignore',divide='ignore'):
                sv = n + 1.0 - np.log(np.log(absZ[new_esc]+1e-300))/np.log(2.0)
            ns[new_esc] = sv
            active = active & ~esc
    
    ns[active] = MAX_ITER  # 有界
    return ns

t0 = time.time()
ns_s = escape_field(C_s, 'std')
print(f"  标准 M: {time.time()-t0:.1f}s, 逃逸率={100*np.mean(ns_s<300):.1f}%")

t0 = time.time()
ns_i = escape_field(C_i, 'inv')
print(f"  逆   M: {time.time()-t0:.1f}s, 逃逸率={100*np.mean(ns_i<300):.1f}%")

# 归一化
def norm01(ns):
    v = np.clip(ns, 0, 300)
    return np.log1p(v)/np.log1p(300)

E_s = norm01(ns_s)
E_i = norm01(ns_i)

b_s = (ns_s >= 300).astype(float)
b_i = (ns_i >= 300).astype(float)

# ============================================================
# 量化对比
# ============================================================
print("\n▶ 量化对比...")

from scipy.stats import pearsonr

# 只在逃逸点比较
ms = ns_s < 300
mi = ns_i < 300

# 互信息 (等宽分箱)
def mi_2d(x, y, bins=25):
    x = np.clip(x, 0, 1)
    y = np.clip(y, 0, 1)
    h, _, _ = np.histogram2d(x, y, bins=bins)
    h = h/h.sum()
    px = h.sum(axis=1)
    py = h.sum(axis=0)
    val = 0.0
    for r in range(bins):
        for c in range(bins):
            if h[r,c]>0:
                val += h[r,c]*np.log(h[r,c]/(px[r]*py[c]+1e-15))
    return val

# 归一化质量到场 [0,1]
Qn_s = (Q_s - Q_s.min())/(Q_s.max()-Q_s.min()+1e-10)
Qn_i = (Q_i - Q_i.min())/(Q_i.max()-Q_i.min()+1e-10)

mi_std = mi_2d(E_s[ms], Qn_s[ms])
mi_inv = mi_2d(E_i[mi], Qn_i[mi])
print(f"  互信息 E vs Q:")
print(f"    标准 M: {mi_std:.4f}")
print(f"    逆   M: {mi_inv:.4f}")
print(f"    比值:   {mi_inv/mi_std:.2f}x")

# 皮尔逊相关
r_s, _ = pearsonr(E_s[ms].ravel(), Qn_s[ms].ravel())
r_i, _ = pearsonr(E_i[mi].ravel(), Qn_i[mi].ravel())
print(f"\n  皮尔逊相关 E vs Q:")
print(f"    标准 M: r={r_s:.4f}")
print(f"    逆   M: r={r_i:.4f}")

# 梯度方向一致性
def grad_align(a, b):
    gya, gxa = np.gradient(a)
    gyb, gxb = np.gradient(b)
    dot = gxa*gxb + gya*gyb
    na = np.sqrt(gxa**2+gya**2)+1e-10
    nb = np.sqrt(gxb**2+gyb**2)+1e-10
    return float(np.mean(dot/(na*nb)))

ga_s = grad_align(E_s, Qn_s)
ga_i = grad_align(E_i, Qn_i)
print(f"\n  梯度对齐度:")
print(f"    标准 M: {ga_s:.4f}")
print(f"    逆   M: {ga_i:.4f}")

# 甜区距离
def peak_dist(f1, f2):
    p1 = np.unravel_index(np.argmax(f1), f1.shape)
    p2 = np.unravel_index(np.argmax(f2), f2.shape)
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)

dp_s = peak_dist(Qn_s, -E_s)
dp_i = peak_dist(Qn_i, -E_i)
print(f"\n  甜区(质量峰) vs 慢逃逸点 像素距离:")
print(f"    标准 M: {dp_s:.1f} px")
print(f"    逆   M: {dp_i:.1f} px")

# ============================================================
# 可视化
# ============================================================
print("\n▶ 绘图...")

cmap_q = LinearSegmentedColormap.from_list('q', 
    ['#330000','#660000','#993300','#cc6600','#ffcc00','#ffff66','#ffffff'], N=256)
cmap_e = LinearSegmentedColormap.from_list('e',
    ['#000033','#000066','#003399','#0066cc','#00ccff','#66ffcc','#ccffff','#ffffff'], N=256)

es = [-2.5,1.5,-3,3]
ei = [-2,4,-3,3]

fig, axes = plt.subplots(3, 2, figsize=(20, 28), facecolor='black')

# Row 1: 质量场
ax = axes[0][0]
ax.imshow(Q_s, extent=es, cmap=cmap_q, origin='lower', vmin=0.4, vmax=1)
ax.set_title('Hyperparam Quality Field\nLR×Dropout → Val Acc (standard view)',
             fontsize=13, color='white')
ax.set_xlabel('Re(c) ←→ LR'); ax.set_ylabel('Im(c) ←→ Dropout')
ax.tick_params(colors='white'); ax.set_facecolor('black')

ax = axes[0][1]
ax.imshow(Q_i, extent=ei, cmap=cmap_q, origin='lower', vmin=0.4, vmax=1)
ax.set_title('Hyperparam Quality Field\nLR×Dropout → Val Acc (inverse view)',
             fontsize=13, color='white')
ax.set_xlabel('Re(c) ←→ LR'); ax.set_ylabel('Im(c) ←→ Dropout')
ax.tick_params(colors='white'); ax.set_facecolor('black')

# Row 2: 逃逸场
ax = axes[1][0]
ax.imshow(E_s, extent=es, cmap=cmap_e, origin='lower', vmin=0, vmax=1)
ax.set_title(r'Escape Time: $z_{n+1}=z_n^2+c$' + f'\nMI={mi_std:.4f}  r={r_s:.4f}  GradAlign={ga_s:.4f}',
             fontsize=13, color='white')
ax.set_xlabel('Re(c)'); ax.set_ylabel('Im(c)')
ax.tick_params(colors='white'); ax.set_facecolor('black')

ax = axes[1][1]
ax.imshow(E_i, extent=ei, cmap=cmap_e, origin='lower', vmin=0, vmax=1)
ax.set_title(r'Escape Time: $z_{n+1}=z_n^2+1/c$' + f'\nMI={mi_inv:.4f}  r={r_i:.4f}  GradAlign={ga_i:.4f}',
             fontsize=13, color='white')
ax.set_xlabel('Re(c)'); ax.set_ylabel('Im(c)')
ax.tick_params(colors='white'); ax.set_facecolor('black')

# Row 3: 残差
ax = axes[2][0]
res_s = E_s - Qn_s
im = ax.imshow(res_s, extent=es, cmap='RdBu_r', origin='lower', vmin=-0.5, vmax=0.5)
ax.set_title(f'Residual (Escape − Quality): Standard M\nRMSE={float(np.sqrt(np.mean(res_s**2))):.4f}',
             fontsize=13, color='white')
ax.set_xlabel('Re(c)'); ax.set_ylabel('Im(c)')
ax.tick_params(colors='white'); ax.set_facecolor('black')
plt.colorbar(im, ax=ax, shrink=0.7)

ax = axes[2][1]
res_i = E_i - Qn_i
im = ax.imshow(res_i, extent=ei, cmap='RdBu_r', origin='lower', vmin=-0.5, vmax=0.5)
ax.set_title(f'Residual (Escape − Quality): Inverse M\nRMSE={float(np.sqrt(np.mean(res_i**2))):.4f}',
             fontsize=13, color='white')
ax.set_xlabel('Re(c)'); ax.set_ylabel('Im(c)')
ax.tick_params(colors='white'); ax.set_facecolor('black')
plt.colorbar(im, ax=ax, shrink=0.7)

fig.suptitle('Hyperparameter Quality Prediction: Standard M vs Inverse M\n' +
             'Does fractal escape time correlate with ML hyperparameter quality?',
             fontsize=18, color='white', y=1.005)
plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig('/data/workspace/comparison_main.png', dpi=130, bbox_inches='tight',
            facecolor='black', edgecolor='none')
plt.close()
print("  ✓ comparison_main.png")

# --- 散点图 ---
fig2, axes2 = plt.subplots(1, 2, figsize=(18, 9), facecolor='black')

step = 2
for idx, (E, Qn, title, cmap, r_val, mi_val) in enumerate([
    (E_s[::step,::step], Qn_s[::step,::step], 
     f'Standard M: r={r_s:.4f}  MI={mi_std:.4f}', 'cool', r_s, mi_std),
    (E_i[::step,::step], Qn_i[::step,::step],
     f'Inverse M: r={r_i:.4f}  MI={mi_inv:.4f}', 'hot', r_i, mi_inv),
]):
    ax = axes2[idx]
    Ec = E.ravel(); Qc = Qn.ravel()
    ax.scatter(Ec, Qc, s=0.5, alpha=0.15, c=Ec, cmap=cmap, rasterized=True)
    # 趋势线
    bins = np.linspace(0,1,20)
    bc = (bins[:-1]+bins[1:])/2
    bm = []
    for k in range(len(bins)-1):
        m = (Ec>=bins[k])&(Ec<bins[k+1])
        bm.append(Qc[m].mean() if m.sum()>0 else np.nan)
    ax.plot(bc, bm, 'r-', lw=3, label='Local mean trend')
    # 理论参考线 (如果完全相关)
    ax.plot([0,1],[0,1],'w--',lw=0.5,alpha=0.3)
    ax.set_xlabel('Escape Time (normalized)', fontsize=13, color='white')
    ax.set_ylabel('Quality (normalized)', fontsize=13, color='white')
    ax.set_title(title, fontsize=14, color='white')
    ax.tick_params(colors='white'); ax.set_facecolor('black')
    ax.legend(fontsize=12, facecolor='black', edgecolor='white', labelcolor='white')
    ax.grid(True, alpha=0.1, color='white')
    ax.set_xlim(-0.05,1.05); ax.set_ylim(-0.05,1.05)

fig2.suptitle('Key Evidence: Does Fractal Escape Time Predict Hyperparameter Quality?',
              fontsize=16, color='white', y=1.01)
plt.tight_layout()
plt.savefig('/data/workspace/scatter_evidence.png', dpi=150, bbox_inches='tight',
            facecolor='black', edgecolor='none')
plt.close()
print("  ✓ scatter_evidence.png")

# ============================================================
# 结果
# ============================================================
results = {
    'standard_m': {
        'view': 'Re[-2.5,1.5] Im[-3,3]',
        'escape_rate': float(np.mean(ns_s<300)),
        'mutual_info': float(mi_std),
        'pearson_r': float(r_s),
        'gradient_alignment': float(ga_s),
        'sweet_spot_dist_px': float(dp_s),
        'rmse_residual': float(np.sqrt(np.mean((E_s-Qn_s)**2))),
    },
    'inverse_m': {
        'view': 'Re[-2,4] Im[-3,3]',
        'escape_rate': float(np.mean(ns_i<300)),
        'mutual_info': float(mi_inv),
        'pearson_r': float(r_i),
        'gradient_alignment': float(ga_i),
        'sweet_spot_dist_px': float(dp_i),
        'rmse_residual': float(np.sqrt(np.mean((E_i-Qn_i)**2))),
    },
    'ratio': {
        'MI_inverse_over_standard': float(mi_inv/mi_std) if mi_std>0 else None,
        'r_inverse_over_standard': float(r_i/r_s) if abs(r_s)>1e-10 else None,
    }
}
with open('/data/workspace/results.json','w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*70}")
print("  核心结果")
print(f"{'='*70}")
better = "逆 M" if mi_inv > mi_std else "标准 M"
print(f"\n  互信息更高的一方: {better}")
print(f"  标准 M: MI={mi_std:.4f}, r={r_s:.4f}, RMSE={results['standard_m']['rmse_residual']:.4f}")
print(f"  逆   M: MI={mi_inv:.4f}, r={r_i:.4f}, RMSE={results['inverse_m']['rmse_residual']:.4f}")
if mi_std>0:
    print(f"  比值: MI_inv/MI_std = {mi_inv/mi_std:.3f}")
print(f"\n  文件: comparison_main.png, scatter_evidence.png, results.json")
print("  ALL DONE!")
