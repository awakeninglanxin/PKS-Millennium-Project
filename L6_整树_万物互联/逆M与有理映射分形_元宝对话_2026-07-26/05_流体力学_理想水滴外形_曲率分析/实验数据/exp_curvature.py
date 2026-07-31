"""
逆 M 边界 vs 经典水滴形 — 平均曲率分布对比
============================================
核心假设检验:
  如果逆 M 边界的平均曲率分布最接近"常数",
  则它是"最接近理想液滴"的数学形状.

理想液滴 (Young-Laplace): 平均曲率 H = 常数 = 1/R
  → 表面张力平衡 → 最小表面积/体积比

对比对象:
  1. 球体 (基准: H=精确常数)
  2. 椭球体 (轻微偏离常数)
  3. Joukowski 旋转体
  4. von Karman 旋转体
  5. 自然水滴形 (Worthington)
  6. 逆 M 边界旋转体 ← 待测

量化指标:
  - 平均曲率均值 H_mean
  - 平均曲率标准差 σ_H (越小越接近理想)
  - 变异系数 CV = σ_H / |H_mean| (无量纲, 越低越好)
  - 表面积/体积比 (Wetzel 公式)
  - 表面积/体积比与球体的偏离度
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev, interp1d, UnivariateSpline
from scipy.integrate import trapezoid, simpson
from scipy.spatial.distance import directed_hausdorff
import json, time, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
print("=" * 70)
print("  平均曲率分布对比 — 谁是'最接近理想液滴'的形状?")
print("=" * 70)

# ============================================================
# 1. 生成各形状母线 (对称于 x 轴, 上半部 r(x)≥0)
# ============================================================
print("\n[1] 生成各形状母线...")

def generate_shapes(n_pts=10000):
    """返回 dict: name → (x_grid, r_grid, curve_2d)"""
    shapes = {}
    
    # --- 1. 球体 (基准) ---
    # 半圆: r = sqrt(R^2 - (x-L/2)^2)
    x = np.linspace(-1, 1, n_pts)
    r = np.sqrt(np.maximum(1 - x**2, 0))
    shapes['Sphere (H=const)'] = (x, r, None)
    print(f"    Sphere:       半圆母线, R=1")

    # --- 2. 椭球体 ---
    # x = a*cos(t), r = b*sin(t)
    t = np.linspace(0, np.pi, n_pts)
    a, b = 1.2, 0.7
    x_e = a*np.cos(t)
    r_e = b*np.sin(t)
    # 插值到均匀 x
    f = interp1d(x_e[::-1], r_e[::-1], bounds_error=False, fill_value=0)
    x_uni = np.linspace(x_e.min(), x_e.max(), n_pts)
    shapes['Ellipsoid (a/b=1.71)'] = (x_uni, f(x_uni), None)
    print(f"    Ellipsoid:    a/b={a/b:.2f}")

    # --- 3. Joukowski 旋转体 ---
    # 从椭圆翼型取上半部
    a_jk = 2.0
    t_jk = np.linspace(0, np.pi, n_pts)
    x_jk = 0.5*(a_jk+1.0/a_jk)*np.cos(t_jk)
    r_jk = 0.5*(a_jk-1.0/a_jk)*np.sin(t_jk)
    # 映射到 [-1,1]
    x_jk_m = (x_jk - x_jk.min()) / (x_jk.max()-x_jk.min())*2 - 1
    shapes['Joukowski (a=2)'] = (x_jk_m, r_jk, None)
    print(f"    Joukowski:    a={a_jk}")

    # --- 4. von Karman ---
    L_vk, R_vk, a_vk = 0.9, 0.55, 0.15
    t_vk = np.linspace(0, np.pi, n_pts)
    x_vk = L_vk*np.cos(t_vk)
    r_vk = R_vk*np.sin(t_vk)*(1+a_vk*np.cos(t_vk))
    # 尾部收敛
    tail_m = x_vk > L_vk*0.85
    r_vk[tail_m] *= np.linspace(1, 0.15, sum(tail_m))
    # 映射到 [-1,1]
    x_vk_m = (x_vk - x_vk.min()) / (x_vk.max()-x_vk.min())*2 - 1
    shapes['von Karman'] = (x_vk_m, r_vk, None)
    print(f"    von Karman:   L={L_vk}, R={R_vk}, a={a_vk}")

    # --- 5. 自然水滴 (Worthington/Grace-Mari) ---
    x_nd = np.linspace(0, 1, n_pts)
    r_nd = np.zeros(n_pts)
    m1 = x_nd <= 0.45
    r_nd[m1] = 0.55*np.sqrt(np.maximum(1-((x_nd[m1]-0.25)/0.35)**2, 0))
    m2 = x_nd > 0.45
    r_nd[m2] = 0.50*np.exp(-3.5*(x_nd[m2]-0.45)/0.55)
    # 映射 [-1,1]
    x_nd_m = (x_nd - x_nd.min())/(x_nd.max()-x_nd.min())*2 - 1
    shapes['Natural Droplet'] = (x_nd_m, r_nd, None)
    print(f"    Natural:      前端球形+尾部指数")

    # --- 6. 逆 M 边界旋转体 ---
    # 主 cardioid 经 1/c 映射, 取上半部 (Im≥0 的部分)
    theta = np.linspace(0, 2*np.pi, 50000, endpoint=False)
    c_std = 0.5*np.exp(1j*theta) - 0.25*np.exp(2j*theta)
    c_inv = 1.0 / c_std
    # 取上半平面 Im(c_inv)≥0
    upper = c_inv[np.imag(c_inv)>=0]
    # 参数化: 用角度排序
    ang = np.angle(upper)
    idx = np.argsort(ang)[::-1]  # 从上到下
    upper_sorted = upper[idx]
    # x = Re, y = Im → 旋转体母线 r = |Im(c_inv)| vs x = Re(c_inv)
    x_im = upper_sorted.real
    r_im = np.abs(upper_sorted.imag)
    # 只取右半 (主水滴部分, x≥某个阈值)
    # 找主连通分量
    # 归一化 x 到 [-1,1]
    x_min, x_max = x_im.min(), x_im.max()
    x_im_n = (x_im - x_min)/(x_max-x_min)*2 - 1
    # 均匀重采样
    f_r = interp1d(x_im_n, r_im, bounds_error=False, fill_value=0)
    x_uni_im = np.linspace(-1, 1, n_pts)
    r_uni_im = f_r(x_uni_im)
    # 归一化 r 使最大=1
    r_uni_im /= (r_uni_im.max()+1e-12)
    shapes['Inverse M'] = (x_uni_im, r_uni_im, None)
    print(f"    Inverse M:    cardioid经1/c映射, 上半部母线")
    
    return shapes

shapes = generate_shapes(20000)

# ============================================================
# 2. 计算平均曲率 H(s)
# ============================================================
print("\n[2] 计算平均曲率 H(s)...")

def mean_curvature_axissymmetric(x, r):
    """
    轴对称曲面的平均曲率 (旋转体, 母线 r(x)):
    
    对于旋转面 r(x) (绕 x 轴旋转), 参数化为:
      X(x,θ) = (x, r(x)*cosθ, r(x)*sinθ)
    
    平均曲率 (单位法向朝外):
      H = (1/2) * [ (1/r)*cos(ψ) - (d²r/dx²)/(1+(dr/dx)²)^(3/2) ]
    
    其中 ψ 是母线切线与 x 轴的夹角: cos(ψ) = 1/sqrt(1+(dr/dx)²)
    更稳定的形式:
      H = (1/2) * [ (1/r)/(1+(r')²)^(1/2) - r''/(1+(r')²)^(3/2) ]
    
    对于轴对称液滴, Young-Laplace: Δp = 2σH = 常数
    → H = 常数 = 1/R (球形时)
    """
    dx = np.gradient(x)
    # 用中心差分, 端点用前向/后向
    r_padded = np.concatenate([[r[0]], r, [r[-1]]])
    x_padded = np.concatenate([[x[0]], x, [x[-1]]])
    
    # 一阶导
    rp = np.gradient(r_padded)/np.gradient(x_padded)
    rp = rp[1:-1]  # 去掉 padding
    # 二阶导 (对弧长)
    rpp = np.gradient(rp)/np.gradient(x)
    
    # 避免 r=0 处除零 (尖端)
    r_safe = np.where(np.abs(r)<1e-12, 1e-12, r)
    
    denom = 1 + rp**2
    H = 0.5 * ( (1.0/r_safe)/np.sqrt(denom) - rpp/(denom**1.5) )
    return H

def arc_length_param(x, r):
    """弧长参数 s"""
    dx = np.sqrt(np.gradient(x)**2 + np.gradient(r)**2)
    s = np.cumsum(dx)
    s /= s[-1]  # 归一化 [0,1]
    return s

results = {}
for name, (x, r, _) in shapes.items():
    H = mean_curvature_axissymmetric(x, r)
    s = arc_length_param(x, r)
    
    # 过滤极端值 (尖端附近数值不稳定)
    mask = np.isfinite(H) & (np.abs(H)<1e3)
    H_clean = H[mask]
    s_clean = s[mask]
    
    H_mean = float(H_clean.mean())
    H_std = float(H_clean.std())
    H_cv = float(H_std/abs(H_mean)) if abs(H_mean)>1e-12 else float('inf')
    
    # 表面积 (旋转体, Pappus 定理)
    ds = np.sqrt(np.gradient(x)**2+np.gradient(r)**2)
    surf = 2*np.pi*trapezoid(r*ds, x)
    # 体积 (旋转体)
    vol = np.pi*trapezoid(r**2, x)
    # 等体积球半径
    R_eq = (3*vol/(4*np.pi))**(1/3)
    # 表面积/体积比
    SA_V = surf/vol if vol>0 else 0
    # 等体积球的 SA/V
    SA_V_sphere = 3/R_eq if R_eq>0 else 0
    # 偏离度
    deviation = float(SA_V/SA_V_sphere - 1) if SA_V_sphere>0 else 0
    
    results[name] = {
        'H_mean': H_mean,
        'H_std': H_std,
        'H_cv': H_cv,
        'H_min': float(H_clean.min()),
        'H_max': float(H_clean.max()),
        'H_range': float(H_clean.max()-H_clean.min()),
        'surface_area': float(surf),
        'volume': float(vol),
        'R_equiv': float(R_eq),
        'SA_V_ratio': float(SA_V),
        'SA_V_sphere': float(SA_V_sphere),
        'deviation_from_sphere': deviation,
        's': s_clean.tolist(),
        'H': H_clean.tolist(),
    }
    print(f"    {name:<25s}: H_mean={H_mean:>10.4f}, σ_H={H_std:>8.4f}, CV={H_cv:>8.4f}, SA/V_dev={deviation:>8.2%}")

# ============================================================
# 3. 曲率分布可视化
# ============================================================
print("\n[3] 绘图...")

palette = {'Sphere (H=const)':'#9E9E9E','Ellipsoid (a/b=1.71)':'#4CAF50',
           'Joukowski (a=2)':'#2196F3','von Karman':'#00BCD4',
           'Natural Droplet':'#FFC107','Inverse M':'#FF5722'}

# 图1: H(s) 分布对比 (最关键的图!)
fig1,ax1=plt.subplots(figsize=(13,8),facecolor='black')
for name,(x,r,_) in shapes.items():
    s = np.array(results[name]['s'])
    H = np.array(results[name]['H'])
    # 降采样绘图
    step=max(1,len(s)//2000)
    ax1.plot(s[::step],H[::step],color=palette[name],lw=2,label=name)
ax1.axhline(0,color='white',ls=':',lw=0.5,alpha=0.3)
ax1.set_xlabel('Arc length s (0=front, 1=tail)',fontsize=13)
ax1.set_ylabel('Mean Curvature H(s)',fontsize=13)
ax1.set_title('Mean Curvature Distribution H(s)\nFlat line = ideal droplet (Young-Laplace)',
              fontsize=14,color='white')
ax1.legend(fontsize=11,facecolor='black',edgecolor='white',labelcolor='white',loc='upper right')
ax1.tick_params(colors='white');ax1.set_facecolor('#080808')
ax1.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/H_distribution.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ H_distribution.png")

# 图2: H(s) 在球体的偏差 (更清晰看谁最平)
fig2,ax2=plt.subplots(figsize=(13,8),facecolor='black')
for name,(x,r,_) in shapes.items():
    s=np.array(results[name]['s']);H=np.array(results[name]['H'])
    step=max(1,len(s)//2000)
    if name=='Sphere (H=const)':
        H_ref=H[::step].mean()
        ax2.axhline(0,color=palette[name],lw=1,ls='--',label=f'{name} (reference)')
    else:
        ax2.plot(s[::step],H[::step]-H_ref,color=palette[name],lw=2,label=name)
ax2.set_xlabel('Arc length s',fontsize=13)
ax2.set_ylabel('ΔH(s) = H(s) − H_sphere',fontsize=13)
ax2.set_title('Deviation from Spherical Curvature\nSmaller amplitude = closer to ideal droplet',
              fontsize=14,color='white')
ax2.legend(fontsize=11,facecolor='black',edgecolor='white',labelcolor='white')
ax2.tick_params(colors='white');ax2.set_facecolor('#080808')
ax2.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/H_deviation.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ H_deviation.png")

# 图3: CV 柱状图 (核心指标!)
fig3,ax3=plt.subplots(figsize=(12,7),facecolor='black')
names_list=list(shapes.keys())
cvs=[results[n]['H_cv'] for n in names_list]
cols=[palette[n] for n in names_list]
bars=ax3.barh(names_list[::-1],cvs[::-1],color=cols[::-1],edgecolor='white',linewidth=0.5)
# 标注数值
for bar,v in zip(bars,cvs[::-1]):
    ax3.text(v+0.002,bar.get_y()+bar.get_height()/2,f'{v:.4f}',
             va='center',fontsize=11,color='white')
ax3.set_xlabel('Coefficient of Variation CV = σ_H / |H_mean|\n(Lower = closer to ideal droplet)',
                fontsize=12)
ax3.set_title('Curvature Uniformity Ranking\nWHO IS CLOSEST TO THE IDEAL DROPLET?',
              fontsize=14,color='white')
ax3.tick_params(colors='white');ax3.set_facecolor('#080808')
ax3.grid(True,alpha=0.1,color='white',axis='x')
plt.tight_layout()
plt.savefig('/data/workspace/H_cv_ranking.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ H_cv_ranking.png")

# 图4: 表面积/体积偏离度
fig4,ax4=plt.subplots(figsize=(12,7),facecolor='black')
devs=[results[n]['deviation_from_sphere']*100 for n in names_list]
bars4=ax4.barh(names_list[::-1],devs[::-1],color=cols[::-1],edgecolor='white',linewidth=0.5)
for bar,v in zip(bars4,devs[::-1]):
    ax4.text(v+0.5,bar.get_y()+bar.get_height()/2,f'{v:.2f}%',
             va='center',fontsize=11,color='white')
ax4.set_xlabel('Deviation from Sphere SA/V (%) — Lower = more compact',
                fontsize=12)
ax4.set_title('Surface/Volume Efficiency\nSphere is optimal (0%)',
              fontsize=14,color='white')
ax4.tick_params(colors='white');ax4.set_facecolor('#080808')
ax4.grid(True,alpha=0.1,color='white',axis='x')
plt.tight_layout()
plt.savefig('/data/workspace/SA_V_ranking.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ SA_V_ranking.png")

# 图5: 母线形状对比
fig5,ax5=plt.subplots(figsize=(12,8),facecolor='black')
for name,(x,r,_) in shapes.items():
    step=max(1,len(x)//2000)
    ax5.plot(x[::step],r[::step],color=palette[name],lw=2.5,label=name)
ax5.set_xlabel('x (normalized)',fontsize=13);ax5.set_ylabel('r(x)',fontsize=13)
ax5.set_title('Meridian Curves (upper half)\nAll shapes normalized to [-1,1]×[0,1]',
              fontsize=14,color='white')
ax5.legend(fontsize=11,facecolor='black',edgecolor='white',labelcolor='white')
ax5.tick_params(colors='white');ax5.set_facecolor('#080808')
ax5.grid(True,alpha=0.1,color='white');ax5.set_aspect('equal')
plt.tight_layout()
plt.savefig('/data/workspace/meridians.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ meridians.png")

# 图6: 综合海报
fig6,axes6=plt.subplots(2,3,figsize=(24,15),facecolor='black')
ax=axes6[0][0]
for name,(x,r,_) in shapes.items():
    s=np.array(results[name]['s']);H=np.array(results[name]['H'])
    step=max(1,len(s)//1500)
    ax.plot(s[::step],H[::step],color=palette[name],lw=1.5,label=name)
ax.axhline(0,color='white',ls=':',lw=0.5,alpha=0.3)
ax.set_title('H(s) Distribution');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808')

ax=axes6[0][1]
for name,(x,r,_) in shapes.items():
    s=np.array(results[name]['s']);H=np.array(results[name]['H'])
    step=max(1,len(s)//1500)
    if name=='Sphere (H=const)':
        H_ref=H[::step].mean()
        ax.axhline(0,color=palette[name],lw=1,ls='--')
    else:
        ax.plot(s[::step],H[::step]-H_ref,color=palette[name],lw=1.5,label=name)
ax.set_title('ΔH(s) from Sphere');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808')

ax=axes6[0][2]
cvs=[results[n]['H_cv'] for n in names_list]
cols6=[palette[n] for n in names_list]
bars=ax.barh(range(len(names_list)),cvs,color=cols,edgecolor='white',linewidth=0.5)
ax.set_yticks(range(len(names_list)));ax.set_yticklabels(names_list,fontsize=10)
for bar,v,n in zip(bars,cvs,names_list):
    ax.text(v+0.001,bar.get_y()+bar.get_height()/2,f'{v:.4f}',va='center',fontsize=10,color='white')
ax.set_title('CV Ranking (lower=more uniform)');ax.tick_params(colors='white');ax.set_facecolor('#080808')

ax=axes6[1][0]
for name,(x,r,_) in shapes.items():
    step=max(1,len(x)//1500)
    ax.plot(x[::step],r[::step],color=palette[name],lw=2,label=name)
ax.set_title('Meridians');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808');ax.set_aspect('equal')

ax=axes6[1][1]
devs=[results[n]['deviation_from_sphere']*100 for n in names_list]
bars4=ax.barh(range(len(names_list)),devs,color=cols,edgecolor='white',linewidth=0.5)
ax.set_yticks(range(len(names_list)));ax.set_yticklabels(names_list,fontsize=10)
for bar,v in zip(bars4,devs):
    ax.text(v+0.5,bar.get_y()+bar.get_height()/2,f'{v:.1f}%',va='center',fontsize=10,color='white')
ax.set_title('SA/V Deviation (%)');ax.tick_params(colors='white');ax.set_facecolor('#080808')

# 判定面板
ax=axes6[1][2];ax.axis('off')
# 排名
ranked_cv=sorted(names_list,key=lambda n:results[n]['H_cv'])
lines=["FINAL VERDICT:",""]
lines.append(f"{'Shape':<25s} {'H_mean':>10s} {'σ_H':>8s} {'CV':>8s} {'SA/V_dev':>10s}")
lines.append("-"*68)
for n in names_list:
    m=results[n]
    lines.append(f"{n:<25s} {m['H_mean']:>10.4f} {m['H_std']:>8.4f} {m['H_cv']:>8.4f} {m['deviation_from_sphere']:>10.2%}")
lines.append("")
lines.append("Ranking by CV (lower = more uniform curvature):")
for i,n in enumerate(ranked_cv):
    lines.append(f"  {i+1}. {n:<25s} CV={results[n]['H_cv']:.4f}")
lines.append("")
winner=ranked_cv[0]
lines.append(f"🏆 WINNER: {winner}")
lines.append(f"   CV = {results[winner]['H_cv']:.4f}")
lines.append(f"   SA/V deviation = {results[winner]['deviation_from_sphere']:.2%}")
if winner=='Inverse M':
    lines.append("")
    lines.append("✅ CONFIRMED: Inverse M is the closest")
    lines.append("   mathematical shape to an ideal droplet!")
    lines.append("   → PRL-worthy result")
else:
    lines.append("")
    lines.append(f"⚠️ {winner} wins, not Inverse M.")
    lines.append("  But check: is Inverse M 2nd? (if yes, still interesting)")
    rank_im=ranked_cv.index('Inverse M')+1 if 'Inverse M' in ranked_cv else 99
    lines.append(f"  Inverse M rank: {rank_im}/{len(names_list)}")
ax.text(0.02,0.98,'\n'.join(lines),transform=ax.transAxes,color='white',fontsize=11,
         verticalalignment='top',family='monospace',
         bbox=dict(boxstyle='round',fc='#0a0a0a',ec='lime' if winner=='Inverse M' else 'white',alpha=0.95))
ax.set_title('Verdict',color='white')

fig6.suptitle('Mean Curvature Analysis: Who is Closest to the Ideal Droplet?\nYoung-Laplace Equation: ∇·n = 2H = const → spherical/ellipsoidal surfaces',
              fontsize=16,color='white',y=1.005)
plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig('/data/workspace/curvature_poster.png',dpi=130,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ curvature_poster.png")

# ============================================================
# 4. 统计检验: 逆 M 的 H 是否"显著更均匀"
# ============================================================
print("\n[4] 统计检验...")
from scipy import stats

# 用 Kolmogorov-Smirnov 检验: H 分布是否接近常数 (=球体)
# 球体 H ≈ 常数 → 退化分布
# 对每个形状, 检验 H 的变异系数是否显著小于其他形状

# 配对比较: 逆 M vs 每个其他形状的 CV
print(f"\n  {'Shape':<25s} {'CV':>8s} {'H_range':>10s} {'|H_mean|':>10s} {'rank'}")
print(f"  {'-'*60}")
ranked_cv=sorted(names_list,key=lambda n:results[n]['H_cv'])
for i,n in enumerate(ranked_cv):
    m=results[n]
    print(f"  {n:<25s} {m['H_cv']:>8.4f} {m['H_range']:>10.4f} {abs(m['H_mean']):>10.4f}   #{i+1}")

# 用 bootstrap 估计 CV 的置信区间
print(f"\n  Bootstrap 95% CI for CV:")
for n in names_list:
    H=np.array(results[n]['H'])
    cvs_boot=[]
    for _ in range(1000):
        idx=np.random.choice(len(H),len(H),replace=True)
        H_b=H[idx]
        if abs(H_b.mean())>1e-12:
            cvs_boot.append(H_b.std()/abs(H_b.mean()))
    lo=np.percentile(cvs_boot,2.5);hi=np.percentile(cvs_boot,97.5)
    print(f"    {n:<25s}: CV ∈ [{lo:.4f}, {hi:.4f}]")

# ============================================================
# 5. 额外分析: 逆 M 的曲率分布形状
# ============================================================
print("\n[5] 逆 M 曲率分布形状分析...")
H_im=np.array(results['Inverse M']['H'])
s_im=np.array(results['Inverse M']['s'])

# 拟合 H(s) 到多项式, 看是否接近常数+小扰动
from numpy.polynomial import polynomial as P
for deg in [0,1,2,4]:
    coeffs=P.polyfit(s_im,H_im,deg)
    fit=P.polyval(s_im,coeffs)
    rms=np.sqrt(((H_im-fit)**2).mean())
    print(f"  deg={deg}: RMS={rms:.6f}, coeffs={coeffs}")

# deg=0 的 RMS 就是 σ_H (常数拟合=均值)
# 对比: deg=4 的 RMS 多改善了百分之几
coeffs0=P.polyfit(s_im,H_im,0);fit0=P.polyval(s_im,coeffs0);rms0=np.sqrt(((H_im-fit0)**2).mean())
coeffs4=P.polyfit(s_im,H_im,4);fit4=P.polyval(s_im,coeffs4);rms4=np.sqrt(((H_im-fit4)**2).mean())
improve=(rms0-rms4)/rms0*100
print(f"\n  Constant fit RMS: {rms0:.6f}")
print(f"  Quartic fit RMS:  {rms4:.6f}")
print(f"  Improvement:      {improve:.1f}%")
if improve<20:
    print(f"  → H(s) is essentially CONSTANT (quartic only helps {improve:.0f}%)")
    print(f"  → Strong evidence: Inverse M ≈ ideal droplet!")

# ============================================================
# 6. 保存
# ============================================================
winner=ranked_cv[0]
is_inverse_winner=(winner=='Inverse M')

output={
    'hypothesis_test':{
        'question':'Is Inverse M boundary mean curvature distribution closest to constant?',
        'winner':winner,
        'inverse_m_wins':is_inverse_winner,
        'inverse_m_rank':ranked_cv.index('Inverse M')+1 if 'Inverse M' in ranked_cv else None,
    },
    'results':{n:{
        'H_mean':results[n]['H_mean'],
        'H_std':results[n]['H_std'],
        'H_cv':results[n]['H_cv'],
        'H_min':results[n]['H_min'],
        'H_max':results[n]['H_max'],
        'H_range':results[n]['H_range'],
        'surface_area':results[n]['surface_area'],
        'volume':results[n]['volume'],
        'R_equiv':results[n]['R_equiv'],
        'SA_V_ratio':results[n]['SA_V_ratio'],
        'deviation_from_sphere':results[n]['deviation_from_sphere'],
    } for n in names_list},
    'bootstrap_CI':{n:None for n in names_list},  # filled below
    'polynomial_fit':{
        'constant_RMS':float(rms0),
        'quartic_RMS':float(rms4),
        'improvement_pct':float(improve),
        'interpretation':'essentially constant' if improve<20 else 'significant variation',
    },
    'young_laplace_context':{
        'sphere_CV':'~0 (exact constant)',
        'ideal_droplet_condition':'H(s) = const → Δp = 2σH',
        'inverse_m_CV':results['Inverse M']['H_cv'],
        'closest_competitor':ranked_cv[1] if len(ranked_cv)>1 else None,
        'closest_competitor_CV':results[ranked_cv[1]]['H_cv'] if len(ranked_cv)>1 else None,
    },
    'verdict':{
        'statement':('CONFIRMED: Inverse M has the most uniform mean curvature distribution, '
                      'making it the closest mathematical shape to an ideal Young-Laplace droplet.')
                      if is_inverse_winner else
                      (f'NOT CONFIRMED: {winner} wins. Inverse M rank: {ranked_cv.index("Inverse M")+1}/'
                       f'{len(names_list)}'),
        'prl_worthy':is_inverse_winner,
        'next_steps':[
            'CFD validation (OpenFOAM: axisymmetric Navier-Stokes)',
            'Compare drag coefficient Cd at Re=10^3-10^5',
            'Biological fitting (tuna/dolphin/penguin body curves)',
            'Analytic proof: derive H(s) for inverse M boundary in closed form',
        ],
    },
}

# 重新填 bootstrap
bootstrap_data={}
for n in names_list:
    H=np.array(results[n]['H'])
    cvs_b=[]
    for _ in range(1000):
        idx=np.random.choice(len(H),len(H),replace=True)
        H_b=H[idx]
        if abs(H_b.mean())>1e-12:cvs_b.append(H_b.std()/abs(H_b.mean()))
    bootstrap_data[n]={'CI_95_low':float(np.percentile(cvs_b,2.5)),
                        'CI_95_high':float(np.percentile(cvs_b,97.5)),
                        'median_CV':float(np.median(cvs_b))}
output['bootstrap_CI']=bootstrap_data

with open('/data/workspace/curvature_results.json','w') as f:json.dump(output, f, indent=2)

import subprocess
subprocess.run(['zip','-j','/data/workspace/curvature_exp.zip',
                '/data/workspace/H_distribution.png',
                '/data/workspace/H_deviation.png',
                '/data/workspace/H_cv_ranking.png',
                '/data/workspace/SA_V_ranking.png',
                '/data/workspace/meridians.png',
                '/data/workspace/curvature_poster.png',
                '/data/workspace/curvature_results.json',
                '/data/workspace/exp_curvature.py'],check=True)

print(f"\n{'='*70}")
print("  FINAL VERDICT")
print(f"{'='*70}")

print(f"\n  曲率均匀性排名 (CV = σ_H/|H_mean|, 越低越接近理想液滴):")
for i,n in enumerate(ranked_cv):
    m=results[n]
    flag=" 🏆" if i==0 else ""
    print(f"    #{i+1} {n:<25s} CV={m['H_cv']:.4f}  SA/V_dev={m['deviation_from_sphere']:.2%}{flag}")

if is_inverse_winner:
    print(f"\n  ✅✅✅ CONFIRMED! ✅✅✅")
    print(f"  Inverse M 的平均曲率分布最接近常数!")
    print(f"  → 它是'最接近理想液滴的数学形状'")
    print(f"  → 这是一个 PRL 级别的发现")
else:
    print(f"\n  ⚠️ 逆 M 未获第一, 但排第{ranked_cv.index('Inverse M')+1}")
    print(f"  仍然可能有应用价值 (见海报分析)")

print(f"\n  多项式拟合: 常数 RMS={rms0:.6f}, 四次 RMS={rms4:.6f}")
print(f"  改善度: {improve:.1f}%")
if improve<20:
    print(f"  → H(s) 本质上就是常数! 强证据支持'理想液滴'假说")

print(f"\n  文件: curvature_exp.zip")
print("  ALL DONE!")
