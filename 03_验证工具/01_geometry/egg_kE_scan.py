"""
egg_kE_scan.py — k_E参数扫描：验证八度蛋形(k_E=2)最优性
===========================================================
Schauberger超双曲锥 xy=1 被平面斜切 → 蛋形截面

k_E 与斜切角 α 的关系（取 z1=1, z2=k_E）:
  alpha = arctan(z1*z2*(z2-z1)/(z1+z2))
       = arctan(k_E*(k_E-1)/(k_E+1))

关键对照：
  k_E=2.0   → α≈33.69°  ← 八度蛋形（音乐谐波 2:1，Fibonacci n=2 精确对应）
  k_E≈1.9371 → α≈31.72°  ← 黄金比极限蛋形（Fibonacci n→∞ 收敛，φ·k_E²-φ²·k_E-1=0）
  k_E=2.5   → α≈46.97°  ← 对比参考点

使用方法：
  python egg_kE_scan.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '01_geometry'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '03_simulation'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '03_simulation', 'python_cfd'))

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from egg_curve import EggCurve, EggParams
from burgers_vortex_init import VortexParams


def kE_to_alpha_deg(kE):
    """k_E → 斜切角 α（度数）"""
    return np.degrees(np.arctan(kE * (kE - 1) / (kE + 1)))


def compute_composite_score(kE, nu=0.02):
    """
    综合评分: 蛋形质量指标 (越小越好)

    组成部分:
      1. 曲率非均匀性 σ_κ/μ_κ — 越小越光滑
      2. 边界偏离圆度 — 蛋形边界与最佳拟合圆的偏差
      3. 涡量适配度 — Burgers涡在蛋形边界的匹配程度
    """
    ep = EggParams(z1=1.0, z2=kE)
    egg = EggCurve(ep)
    
    # === 1. 曲率非均匀性 ===
    s, kappa = egg.curvature()
    kappa_cv = np.std(kappa) / np.mean(kappa) if np.mean(kappa) > 0 else 10.0
    
    # === 2. 边界偏离圆度 (aspect ratio penalty) ===
    x_bnd, y_bnd = egg.get_curve_points(500)
    x_range = np.max(x_bnd) - np.min(x_bnd)
    y_range = np.max(y_bnd) - np.min(y_bnd)
    aspect_ratio = max(x_range, y_range) / min(x_range, y_range)
    circularity_penalty = abs(aspect_ratio - 1.0)  # 偏离正圆的程度
    
    # === 3. 涡量场适配度 ===
    vp = VortexParams(Gamma=1.0, gamma=1.0, nu=nu)
    cy = (np.max(y_bnd) + np.min(y_bnd)) / 2
    n_pts = len(x_bnd) // 2
    
    r = np.sqrt(x_bnd[:n_pts]**2 + (y_bnd[:n_pts] - cy)**2)
    r_safe = np.maximum(r, 1e-8)
    
    # Burgers涡精确涡量
    omega_exact = vp.Gamma * vp.gamma / (4*np.pi*vp.nu) * np.exp(-vp.gamma*r_safe**2/(4*vp.nu))
    
    # 从速度数值微分得涡量
    vtheta = vp.Gamma / (2*np.pi*r_safe) * (1 - np.exp(-vp.gamma*r_safe**2/(4*vp.nu)))
    dr = r_safe[1] - r_safe[0] if len(r_safe) > 1 else 1e-6
    d_rvtheta = np.gradient(r_safe * vtheta, dr)
    omega_num = d_rvtheta / r_safe
    
    # 涡量误差（考虑蛋形边界非轴对称导致的额外扰动）
    vort_mismatch = np.mean(np.abs(omega_num - omega_exact))
    
    # === 综合得分 (加权组合) ===
    score = (
        0.40 * kappa_cv +
        0.30 * circularity_penalty +
        0.30 * vort_mismatch
    )
    return score, kappa_cv, circularity_penalty, vort_mismatch


def full_scan():
    """完整扫描并生成带alpha副轴的图表"""
    print("=" * 60)
    print("k_E Parameter Scan — NS Residual vs Cutting Angle")
    print("=" * 60)
    
    # kE_PHI_LIMIT = 黄金比极限蛋: 方程 φ·k_E²-φ²·k_E-1=0 的正根
    _phi = (1 + np.sqrt(5)) / 2
    kE_PHI_LIMIT = (-(-_phi**2) + np.sqrt(_phi**4 + 4*_phi)) / (2*_phi)  # ≈1.9371

    kE_values = np.array([1.1, 1.2, 1.3, 1.5, 1.7, kE_PHI_LIMIT, 2.0, 2.3, 2.5, 3.0, 3.5, 4.0])
    alphas_deg = [kE_to_alpha_deg(ke) for ke in kE_values]

    print(f"\n{'k_E':>6} | {'alpha(deg)':>12} | {'Note':<35}")
    print("-" * 58)
    for ke, ad in zip(kE_values, alphas_deg):
        note = ""
        if abs(ke - 2.0) < 0.01:
            note = "<-- Octave Egg (harmonic, Fib n=2)"
        elif abs(ke - 2.5) < 0.01:
            note = "<-- Target comparison"
        elif abs(ke - kE_PHI_LIMIT) < 0.01:
            note = "<-- Golden Ratio Limit (Fib n->inf)"
        elif abs(ke - 1.618) < 0.05:
            note = "<-- Golden ratio near"
        print(f"{ke:>6.3f} | {ad:>11.2f} | {note}")
    
    # 计算所有指标
    scores = []; kappas = []; circs = []; vorts = []
    for ke in kE_values:
        sc, kv, cv, vm = compute_composite_score(ke)
        scores.append(sc); kappas.append(kv); circs.append(cv); vorts.append(vm)
    
    scores = np.array(scores)
    kappas = np.array(kappas)
    circs = np.array(circs)
    vorts = np.array(vorts)
    
    # 归一化（用最大值，让最小值可以出现在任何位置）
    scores_norm = scores / np.max(scores)
    kappas_norm = kappas / np.max(kappas)
    circs_norm = circs / np.max(circs)
    vorts_norm = vorts / np.max(vorts)
    
    # 找最小值位置
    best_kE_scores = kE_values[np.argmin(scores)]
    best_kE_curv = kE_values[np.argmin(kappas)]
    print(f"\n  Composite minimum @ k_E={best_kE_scores:.4f}")
    print(f"  Curvature minimum @ k_E={best_kE_curv:.4f}")
    print(f"  Golden Ratio Limit  k_E={kE_PHI_LIMIT:.4f}  α={kE_to_alpha_deg(kE_PHI_LIMIT):.2f}°")
    
    # ===== 绘图 (2行4列, 面板4拆为左右对比) =====
    fig = plt.figure(figsize=(24, 12))
    gs = fig.add_gridspec(2, 4, hspace=0.35, wspace=0.35)
    
    # ---- 面板1：综合残差曲线 (左半行) ----
    ax1 = fig.add_subplot(gs[0, 0:2])
    ax1.plot(kE_values, scores_norm, 'o-', color='#1f77b4', linewidth=2.5,
             markersize=7, label='Composite Score')
    
    # k_E=2 高亮
    idx2 = list(kE_values).index(2.0)
    # kE_PHI_LIMIT 高亮
    idx_phi = list(kE_values).index(kE_PHI_LIMIT)

    # ---- 黄金比极限参考线（面板1） ----
    ax1.axvline(x=kE_PHI_LIMIT, color='gold', ls='-', lw=2.5, alpha=0.9)
    ax1.scatter([kE_PHI_LIMIT], [scores_norm[idx_phi]], color='goldenrod', s=180, marker='h', zorder=10,
                edgecolors='darkgoldenrod', linewidths=1.5)
    ax1.annotate(f'$k_E$={kE_PHI_LIMIT:.3f} Golden\nLimit score=%.3f' % scores_norm[idx_phi],
                 (kE_PHI_LIMIT, scores_norm[idx_phi]), fontsize=8, color='goldenrod',
                 xytext=(kE_PHI_LIMIT - 0.55, scores_norm[idx_phi] + 0.10),
                 arrowprops=dict(arrowstyle='->', color='goldenrod', lw=1.2))

    ax1.axvline(x=2.0, color='red', ls='--', lw=2.5, alpha=0.8)
    ax1.scatter([2.0], [scores_norm[idx2]], color='red', s=180, marker='*', zorder=10,
                edgecolors='darkred', linewidths=1.5)
    ax1.annotate('k$_E$=2 Octave\nscore=%.3f' % scores_norm[idx2],
                 (2.0, scores_norm[idx2]), fontsize=8, color='red',
                 xytext=(2.15, scores_norm[idx2]+0.08),
                 arrowprops=dict(arrowstyle='->', color='red', lw=1.2))
    
    # k_E=2.5 高亮
    idx25 = list(kE_values).index(2.5)
    ax1.axvline(x=2.5, color='orange', ls='-.', lw=2.5, alpha=0.8)
    ax1.scatter([2.5], [scores_norm[idx25]], color='orange', s=150, marker='D', zorder=10,
                edgecolors='darkorange', linewidths=1.5)
    ax1.annotate('k$_E$=2.5 Target\nscore=%.3f' % scores_norm[idx25],
                 (2.5, scores_norm[idx25]), fontsize=8, color='darkorange',
                 xytext=(2.65, scores_norm[idx25]+0.06),
                 arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.2))
    
    ax1.set_xlabel('Eggness k$_E$ = $z_2/z_1$', fontsize=12)
    ax1.set_ylabel('Normalized Score (lower=better)', fontsize=12)
    ax1.set_title('Composite Quality Score', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax1.set_xlim(0.9, 4.3)
    
    # alpha 副轴
    ax1t = ax1.twiny()
    ax1t.set_xlim(ax1.get_xlim())
    ax1t.set_xticks(kE_values)
    ax1t.set_xticklabels([f'{a:.0f}$^\\circ$' for a in alphas_deg], fontsize=8)
    ax1t.set_xlabel('Cutting Angle $\\alpha$', fontsize=10, color='#555')
    ax1t.tick_params(axis='x', colors='#555')
    
    # ---- 面板2：曲率非均匀性 (右半行) ----
    ax2 = fig.add_subplot(gs[0, 2:4])
    ax2.plot(kE_values, kappas_norm, 's-', color='purple', linewidth=2.5,
             markersize=7, label='$\\sigma_\\kappa/\\mu_\\kappa$')
    ax2.fill_between(kE_values, 0, kappas_norm, alpha=0.15, color='purple')
    
    ax2.axvline(x=kE_PHI_LIMIT, color='gold', ls='-', lw=2, alpha=0.9)
    ax2.scatter([kE_PHI_LIMIT], [kappas_norm[idx_phi]], color='goldenrod', s=120, marker='h', zorder=10)
    ax2.axvline(x=2.0, color='red', ls='--', lw=2)
    ax2.scatter([2.0], [kappas_norm[idx2]], color='red', s=120, marker='*', zorder=10)
    ax2.axvline(x=2.5, color='orange', ls='-.', lw=2)
    ax2.scatter([2.5], [kappas_norm[idx25]], color='orange', s=100, marker='D', zorder=10)
    
    ax2.set_xlabel('k$_E$', fontsize=12)
    ax2.set_ylabel('Normalized Curvature CV', fontsize=12)
    ax2.set_title('Curvature Non-uniformity (smoother=lower)', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_xlim(0.9, 4.3)
    
    ax2t = ax2.twiny()
    ax2t.set_xlim(ax2.get_xlim())
    ax2t.set_xticks(kE_values)
    ax2t.set_xticklabels([f'{a:.0f}$^\\circ$' for a in alphas_deg], fontsize=8)
    ax2t.set_xlabel('$\\alpha$', fontsize=10, color='#555')
    ax2t.tick_params(axis='x', colors='#555')
    
    # ---- 面板3：圆度偏离 (左半行) ----
    ax3 = fig.add_subplot(gs[1, 0:2])
    ax3.plot(kE_values, circs_norm, '^-', color='green', linewidth=2.5,
             markersize=7, label='Circularity Deviation')
    ax3.axvline(x=kE_PHI_LIMIT, color='gold', ls='-', lw=2, alpha=0.9)
    ax3.scatter([kE_PHI_LIMIT], [circs_norm[idx_phi]], color='goldenrod', s=100, marker='h', zorder=10)
    ax3.axvline(x=2.0, color='red', ls='--', lw=2)
    ax3.axvline(x=2.5, color='orange', ls='-.', lw=2)
    ax3.scatter([2.0], [circs_norm[idx2]], color='red', s=100, marker='*', zorder=10)
    ax3.scatter([2.5], [circs_norm[idx25]], color='orange', s=80, marker='D', zorder=10)
    ax3.set_xlabel('k$_E$', fontsize=12)
    ax3.set_ylabel('Normalized Deviation', fontsize=12)
    ax3.set_title('Deviation from Circle (closer=more symmetric)', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.set_xlim(0.9, 4.3)
    
    ax3t = ax3.twiny()
    ax3t.set_xlim(ax3.get_xlim())
    ax3t.set_xticks(kE_values)
    ax3t.set_xticklabels([f'{a:.0f}$^\\circ$' for a in alphas_deg], fontsize=8)
    ax3t.set_xlabel('$\\alpha$', fontsize=10, color='#555')
    ax3t.tick_params(axis='x', colors='#555')
    
    # ---- 面板4 LEFT：ybar-采样 (二分法) ----
    ax4L = fig.add_subplot(gs[1, 2])
    
    # ---- 面板4 RIGHT：x_func/y_func 全周期参数化 (x*-1, 蛋尖朝上) ----
    ax4R = fig.add_subplot(gs[1, 3])
    
    # 共享颜色和 k_E 列表
    kE_show_list = [1.1, 1.5, kE_PHI_LIMIT, 2.0, 2.3, 2.5, 3.0, 4.0]
    hsv_colors = plt.cm.hsv(np.linspace(0.05, 0.85, len(kE_show_list)))
    
    for idx, ke_show in enumerate(kE_show_list):
        ep = EggParams(z1=1.0, z2=float(ke_show))
        egg = EggCurve(ep)
        
        lw = 1.5 if ke_show in [2.0, kE_PHI_LIMIT] else 1.0 if ke_show == 2.5 else 0.6
        label_short = f'k={ke_show:.2f}'
        if abs(ke_show - kE_PHI_LIMIT) < 0.01:
            label_short = f'k*={ke_show:.3f} \u03a6'
        elif abs(ke_show - 2.0) < 0.01:
            label_short = 'k=2.0 Oct'
        
        # === LEFT: ybar-采样 (180°翻转) ===
        x_ybar, y_ybar = egg.get_curve_points_ybar(2000)
        ax4L.plot(-x_ybar, -y_ybar, color=hsv_colors[idx], linewidth=lw, alpha=0.9)
        
        # === RIGHT: parametric_form (x=r·cosφ, y=r·sinφ) 交换翻转 ===
        # x=[-0.60,1.20]水平 → 交换并翻 y → 蛋尖朝上
        phi_full = np.linspace(0, 2*np.pi, 2000)
        cos_mask = np.abs(np.cos(phi_full)) > 1e-8
        phi_safe = phi_full[cos_mask]
        _, _, x_raw, y_raw = egg.parametric_form(phi_safe)
        x_curve = y_raw         # 水平→垂直: x 取 y 值
        y_curve = -x_raw        # 翻转: 尖端翻到顶部
        
        ax4R.plot(x_curve, y_curve, color=hsv_colors[idx], linewidth=lw, alpha=0.9)
        
        # 填充高亮
        if abs(ke_show - kE_PHI_LIMIT) < 0.01:
            ax4L.fill(-x_ybar, -y_ybar, alpha=0.12, color='gold')
            ax4R.fill(x_curve, y_curve, alpha=0.12, color='gold')
        elif abs(ke_show - 2.0) < 0.01:
            ax4L.fill(-x_ybar, -y_ybar, alpha=0.08, color='red')
            ax4R.fill(x_curve, y_curve, alpha=0.08, color='red')
    
    # LEFT 面板格式
    ax4L.set_xlabel('x', fontsize=10)
    ax4L.set_ylabel('y', fontsize=10)
    ax4L.set_title('ybar-采样 (二分法, n=2000)', fontsize=11, fontweight='bold', color='#c0392b')
    ax4L.set_aspect('equal')
    ax4L.set_xlim(-1.8, 1.8); ax4L.set_ylim(-1.5, 1.5)
    ax4L.grid(True, alpha=0.2)
    
    # RIGHT 面板格式
    ax4R.set_xlabel('x', fontsize=10)
    ax4R.set_ylabel('y', fontsize=10)
    ax4R.set_title('parametric_form (n=2000, 自动闭合)', fontsize=11, fontweight='bold', color='#27ae60')
    ax4R.set_aspect('equal')
    ax4R.set_xlim(-1.8, 1.8); ax4R.set_ylim(-1.5, 1.5)
    ax4R.grid(True, alpha=0.2)
    
    # 共享图例 (放在右侧)
    handles, labels = ax4R.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, fontsize=6.5, loc='center right',
                   bbox_to_anchor=(1.01, 0.25), framealpha=0.7, ncol=1)
    
    plt.subplots_adjust(left=0.06, right=0.92, top=0.93, bottom=0.08, wspace=0.35, hspace=0.40)
    
    # 保存到两个路径
    out_local = os.path.join(os.path.dirname(__file__), 'kE_scan_results.png')
    out_target = r'D:\AAA我的文件\egg_vortex_cfd\egg_vortex_cfd\egg_vortex_cfd\kE_scan_results.png'
    plt.savefig(out_local, dpi=160, bbox_inches='tight')
    plt.savefig(out_target, dpi=160, bbox_inches='tight')
    plt.close()
    
    print(f"\nSaved:")
    print(f"  {out_local}")
    print(f"  {out_target}")
    
    # 数值摘要表
    print(f"\n{'='*60}")
    print("NUMERICAL SUMMARY")
    print(f"{'='*60}")
    print(f"{'k_E':>6}|{'α(°)':>8}|{'CompSc':>8}|{'κ_CV':>8}|{'Circ':>8}|{'Vort':>8}")
    print("-"*56)
    for i, ke in enumerate(kE_values):
        marker = " *" if ke in [2.0, 2.5, kE_PHI_LIMIT] else ""
        label = ""
        if abs(ke - 2.0) < 0.01:
            label = " Octave"
        elif abs(ke - kE_PHI_LIMIT) < 0.01:
            label = " GoldenLim"
        elif abs(ke - 2.5) < 0.01:
            label = " Target"
        print(f"{ke:>6.3f}|{alphas_deg[i]:>7.1f}|{scores_norm[i]:>8.3f}|{kappas_norm[i]:>8.3f}"
              f"|{circs_norm[i]:>8.3f}|{vorts_norm[i]:>8.3f}{marker}{label}")


if __name__ == '__main__':
    full_scan()
