# -*- coding: utf-8 -*-
"""
SEG 磁齿轮静磁仿真 — Phase 1 v2（修正版）
===========================================
修正：测量单个滚筒的力波动（而不是所有滚筒的净合力），
     这才对应磁静音/振动的物理本质。

Q1: gcd=1是否让单个滚筒的受力更平滑？
Q2: Fibonacci滚筒数是否优于等差？
Q3: 三环扭矩传递效率对比

核心物理：
- 每个滚筒绕定子环公转时，经历的磁场周期变化取决于gcd
- gcd=1 → 每个滚筒相位不同 → 力波动频谱宽 → 总振动低（磁静音）
- gcd>1 → 多个滚筒同步经历相同力 → 波动同相叠加 → 振动高
"""

import numpy as np
from numpy import pi, cos, sin, sqrt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os, time, json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

MU0_4PI = 1e-7

# ============================================================
# 物理核心
# ============================================================

def dipole_dipole_force(m_src, m_tgt, r_vec):
    """源→目标的偶极子力"""
    r = np.linalg.norm(r_vec)
    if r < 1e-10:
        return np.zeros(3)
    r_hat = r_vec / r
    m1r, m2r = np.dot(m_src, r_hat), np.dot(m_tgt, r_hat)
    m12 = np.dot(m_src, m_tgt)
    return (3 * MU0_4PI / r**4) * (
        m1r * m_tgt + m2r * m_src + m12 * r_hat - 5 * m1r * m2r * r_hat
    )


def build_stator(N_poles, R=1.0, m_strength=1.0):
    angles = 2 * pi * np.arange(N_poles) / N_poles
    pos = np.column_stack([R * cos(angles), R * sin(angles), np.zeros(N_poles)])
    pol = (-1) ** np.arange(N_poles)[:, np.newaxis]
    mom = pol * m_strength * np.column_stack([cos(angles), sin(angles), np.zeros(N_poles)])
    return pos, mom


# ============================================================
# 修正后的核心指标：单个滚筒的轨道力波动
# ============================================================

def compute_single_roller_force_trace(N_stator, N_rollers, R_stator=1.0, 
                                       R_orbit=0.65, m_stator=1.0, m_roller=0.3,
                                       n_steps=1440):
    """追踪单个滚筒绕完整轨道一圈的切向力变化
    
    这是最重要的指标——模拟"一个滚筒从定子磁极间滑过"的力感受。
    """
    stator_pos, stator_m = build_stator(N_stator, R_stator, m_stator)
    
    angles = 2 * pi * np.arange(n_steps) / n_steps
    single_force = np.zeros(n_steps)
    
    for idx, theta in enumerate(angles):
        roller_pos = np.array([R_orbit * cos(theta), R_orbit * sin(theta), 0])
        # 滚筒磁矩：径向（假设不自转时保持径向）
        pol = 1  # 固定极性
        roller_m = pol * m_roller * np.array([cos(theta), sin(theta), 0])
        
        F_total = np.zeros(3)
        for i in range(N_stator):
            r_vec = roller_pos - stator_pos[i]
            F = dipole_dipole_force(stator_m[i], roller_m, r_vec)
            F_total += F
        
        tang = np.array([-sin(theta), cos(theta), 0])
        single_force[idx] = np.dot(F_total, tang)
    
    return angles, single_force


def compute_spatial_variance_trace(N_stator, N_rollers, R_stator=1.0, 
                                    R_orbit=0.65, m_stator=1.0, m_roller=0.3,
                                    n_steps=360):
    """在每个角度时刻，计算所有滚筒之间受力的空间标准差
    
    这是磁静音的直接指标：
    - std低 → 所有滚筒受力相似 → 力波动同相 → 振动大 ❌
    - std高 → 每个滚筒受力不同 → 力波动分散 → 振动小 ✅
    
    实际上更好的指标是：
    - 所有滚筒受力的傅里叶频谱宽度
    - 频谱越宽（能量分布在更多频率上）→ 单个频率振幅越小 → 振动低
    """
    stator_pos, stator_m = build_stator(N_stator, R_stator, m_stator)
    
    angles = 2 * pi * np.arange(n_steps) / n_steps
    spatial_std = np.zeros(n_steps)
    all_roller_forces = np.zeros((n_steps, N_rollers))
    
    for idx, theta_ref in enumerate(angles):
        for j in range(N_rollers):
            theta_j = theta_ref + 2 * pi * j / N_rollers
            r_pos = np.array([R_orbit * cos(theta_j), R_orbit * sin(theta_j), 0])
            pol = (-1) ** j  # 交替极性
            r_m = pol * m_roller * np.array([cos(theta_j), sin(theta_j), 0])
            
            F_total = np.zeros(3)
            for i in range(N_stator):
                r_vec = r_pos - stator_pos[i]
                F_total += dipole_dipole_force(stator_m[i], r_m, r_vec)
            
            tang = np.array([-sin(theta_j), cos(theta_j), 0])
            all_roller_forces[idx, j] = np.dot(F_total, tang)
        
        # 跨滚筒的空间标准差
        spatial_std[idx] = np.std(all_roller_forces[idx, :])
    
    return angles, spatial_std, all_roller_forces


def compute_force_spectrum(force_trace):
    """计算力信号的功率谱，返回谱宽度指标"""
    n = len(force_trace)
    fft = np.abs(np.fft.rfft(force_trace - np.mean(force_trace)))
    freqs = np.fft.rfftfreq(n)
    
    # 谱宽度：频率加权平均（类似带宽）
    if np.sum(fft) < 1e-15:
        return 0, 0
    
    weighted_freq = np.sum(freqs[1:] * fft[1:]) / np.sum(fft[1:])
    
    # 峰值频率（最强谐波）
    peak_idx = np.argmax(fft[1:]) + 1
    peak_freq = freqs[peak_idx]
    peak_power = fft[peak_idx] / np.sum(fft[1:])
    
    return weighted_freq, peak_power


def compute_roller_correlation(N_stator, N_rollers, n_steps=360):
    """计算滚筒间力信号的相关性
    
    高相关性 → 多个滚筒同步受力 → 振动叠加 → 噪音大
    低相关性 → 滚筒异步受力 → 振动相消 → 磁静音
    """
    _, _, all_forces = compute_spatial_variance_trace(
        N_stator, N_rollers, n_steps=n_steps
    )
    
    # 计算每对滚筒的互相关系数
    correlations = []
    for i in range(N_rollers):
        for j in range(i+1, N_rollers):
            corr = np.corrcoef(all_forces[:, i], all_forces[:, j])[0, 1]
            correlations.append(abs(corr))
    
    return np.mean(correlations), np.std(correlations)


# ============================================================
# 实验
# ============================================================

def run_all_experiments():
    print("=" * 70)
    print("SEG 磁齿轮仿真 v2 — 修正单滚筒力波动指标")
    print("=" * 70)
    print()
    print("核心指标说明:")
    print("  force_CV: 单滚筒切向力变异系数（越小→力越平滑）")
    print("  peak_power: 最强谐波占比（越小→能量越分散→振动越低）")
    print("  roll_corr: 滚筒间力相关性（越小→异步→磁静音）")
    print("  mean_spatial_std: 跨滚筒力空间标准差（适中→异步好）")
    print()
    
    # 测试配置
    configs = [
        # --- gcd 梯度 ---
        (34, 34, "gcd=34 整除"),
        (34, 17, "gcd=17"),
        (34, 12, "gcd=2"),
        (34, 13, "gcd=1 (Fib内环★)"),
        (34, 11, "gcd=1 (素数11)"),
        (34, 21, "gcd=1 (Fib中环★)"),
        (34, 23, "gcd=1 (Jellium素数23★)"),
        
        # --- 原版等差 vs Fibonacci ---
        (32, 22, "原版 32/22 gcd=2"),
        (34, 21, "FIB 34/21 gcd=1"),
        
        # --- 规格B推荐 ---
        (30, 17, "规格B 30/17 gcd=1"),
        (30, 23, "规格B 30/23 gcd=1"),
    ]
    
    results = []
    
    for N_s, N_r, label in configs:
        g = np.gcd(N_s, N_r)
        l = np.lcm(N_s, N_r)
        print(f"\n[{label}] N_s={N_s}, N_r={N_r}, gcd={g}, lcm={l}")
        t0 = time.time()
        
        # 指标1: 单滚筒力波动
        angles, trace = compute_single_roller_force_trace(N_s, N_r, n_steps=720)
        force_cv = np.std(trace) / (np.mean(np.abs(trace)) + 1e-15)
        reversal = 100 * np.sum(np.diff(np.sign(trace)) != 0) / len(trace)
        
        # 指标2: 频谱分析
        wfreq, pk_power = compute_force_spectrum(trace)
        
        # 指标3: 滚筒间相关性
        roll_corr, roll_corr_std = compute_roller_correlation(N_s, N_r, n_steps=180)
        
        # 指标4: 空间方差
        _, spat_std, _ = compute_spatial_variance_trace(N_s, N_r, n_steps=180)
        mean_spat_std = np.mean(spat_std)
        
        elapsed = time.time() - t0
        
        r = {
            'label': label, 'N_stator': N_s, 'N_roller': N_r,
            'gcd': g, 'lcm': l,
            'force_cv': force_cv, 'reversal_pct': reversal,
            'weighted_freq': wfreq, 'peak_power': pk_power,
            'roller_correlation': roll_corr, 'roller_corr_std': roll_corr_std,
            'mean_spatial_std': mean_spat_std,
            'time': elapsed
        }
        results.append(r)
        
        print(f"  force_CV={force_cv:.4f} | peak_pwr={pk_power:.3f} | "
              f"roll_corr={roll_corr:.3f} | spat_std={mean_spat_std:.4f} | "
              f"reversal={reversal:.1f}% | {elapsed:.1f}s")
    
    return results


def plot_results(results):
    """绘制综合对比图"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    gcdn = np.array([r['gcd'] for r in results])
    labels_short = [r['label'].split('(')[0].strip() for r in results]
    
    # === 子图1: peak_power vs gcd ===
    ax = axes[0, 0]
    pp = np.array([r['peak_power'] for r in results])
    colors = ['#1D9E75' if g == 1 else '#E24B4A' for g in gcdn]
    
    for i in range(len(results)):
        ax.scatter(gcdn[i], pp[i], s=150, c=colors[i], edgecolors='black', 
                  linewidth=0.5, zorder=5)
        ax.annotate(labels_short[i], (gcdn[i], pp[i]),
                   textcoords="offset points", xytext=(6, 4), fontsize=7,
                   alpha=0.85)
    
    ax.set_xlabel('gcd(N_stator, N_roller)', fontsize=12)
    ax.set_ylabel('最强谐波占比 (越小越好)', fontsize=12)
    ax.set_title('磁振动强度指标: 谐波能量集中度', fontsize=13, fontweight='bold')
    ax.axhline(y=np.mean(pp[gcdn == 1]), color='green', linestyle='--', alpha=0.5, label=f'gcd=1均值')
    ax.axhline(y=np.mean(pp[gcdn > 1]), color='red', linestyle='--', alpha=0.5, label=f'gcd>1均值')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1, max(gcdn) + 2)
    
    # === 子图2: roller_correlation vs gcd ===
    ax = axes[0, 1]
    rc = np.array([r['roller_correlation'] for r in results])
    
    for i in range(len(results)):
        ax.scatter(gcdn[i], rc[i], s=150, c=colors[i], edgecolors='black',
                  linewidth=0.5, zorder=5)
        ax.annotate(labels_short[i], (gcdn[i], rc[i]),
                   textcoords="offset points", xytext=(6, 4), fontsize=7,
                   alpha=0.85)
    
    ax.set_xlabel('gcd(N_stator, N_roller)', fontsize=12)
    ax.set_ylabel('滚筒间力相关性 (越小≈越异步≈磁静音)', fontsize=12)
    ax.set_title('磁静音指标: 滚筒受力异步程度', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1, max(gcdn) + 2)
    
    # === 子图3: 单滚筒力波形（选3个对比） ===
    ax = axes[1, 0]
    plot_configs = [
        (34, 34, "gcd=34 整除", "#E24B4A"),
        (34, 17, "gcd=17", "#EF9F27"),
        (34, 13, "gcd=1 Fib13", "#1D9E75"),
        (34, 23, "gcd=1 Jellium23", "#378ADD"),
    ]
    
    for N_s, N_r, lbl, clr in plot_configs:
        angles, trace = compute_single_roller_force_trace(N_s, N_r, n_steps=360)
        # 归一化
        trace_n = trace / (np.max(np.abs(trace)) + 1e-15)
        ax.plot(angles * 180/pi, trace_n, color=clr, linewidth=1.2, label=lbl, alpha=0.8)
    
    ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
    ax.set_xlabel('滚筒轨道角度 (度)', fontsize=12)
    ax.set_ylabel('归一化切向力', fontsize=12)
    ax.set_title('单滚筒受力波形对比（归一化）', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)
    
    # === 子图4: 综合排名表 ===
    ax = axes[1, 1]
    ax.axis('off')
    
    # 综合评分: peak_power(低好) + roller_corr(低好) 
    for r in results:
        r['score'] = r['peak_power'] * 0.6 + r['roller_correlation'] * 0.4
    
    sorted_r = sorted(results, key=lambda x: x['score'])
    
    table_data = []
    for i, r in enumerate(sorted_r):
        rank = '★' if i < 3 else str(i+1)
        table_data.append([
            rank,
            f"{r['N_stator']}/{r['N_roller']}",
            str(r['gcd']),
            r['label'].replace('(', '\n('),
            f"{r['peak_power']:.3f}",
            f"{r['roller_correlation']:.3f}",
            f"{r['score']:.3f}",
            f"{r['reversal_pct']:.0f}%",
        ])
    
    col_labels = ['排名', '定子/滚筒', 'gcd', '类型', '谐波集中', '滚筒相关', '综合分', '反转%']
    table = ax.table(cellText=table_data, colLabels=col_labels,
                    loc='center', cellLoc='center',
                    colWidths=[0.05, 0.12, 0.06, 0.25, 0.11, 0.11, 0.10, 0.08])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.35)
    
    # 高亮前三
    for i in range(min(3, len(sorted_r))):
        for j in range(len(col_labels)):
            cell = table[i+1, j]
            cell.set_facecolor(['#FFD700', '#C0C0C0', '#CD7F32'][i])
    
    ax.set_title('综合排名: 谐波集中度(60%) + 滚筒异步度(40%)', fontsize=13, fontweight='bold', pad=20)
    
    plt.tight_layout(pad=3)
    return fig


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = run_all_experiments()
    
    # 绘图
    fig = plot_results(results)
    path = os.path.join(out_dir, 'seg_torque_smoothness_v2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\n✓ 图表保存: {path}")
    
    # JSON
    jpath = os.path.join(out_dir, 'seg_torque_v2_results.json')
    with open(jpath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"✓ 数据保存: {jpath}")
    
    # 摘要
    print("\n" + "=" * 70)
    print("结论")
    print("=" * 70)
    
    gcd1 = [r for r in results if r['gcd'] == 1]
    gcd_gt1 = [r for r in results if r['gcd'] > 1]
    
    if gcd1 and gcd_gt1:
        print(f"\ngcd=1 组 (n={len(gcd1)}):")
        print(f"  谐波集中度均值: {np.mean([r['peak_power'] for r in gcd1]):.4f}")
        print(f"  滚筒相关性均值: {np.mean([r['roller_correlation'] for r in gcd1]):.4f}")
        
        print(f"\ngcd>1 组 (n={len(gcd_gt1)}):")
        print(f"  谐波集中度均值: {np.mean([r['peak_power'] for r in gcd_gt1]):.4f}")
        print(f"  滚筒相关性均值: {np.mean([r['roller_correlation'] for r in gcd_gt1]):.4f}")
        
        # 统计显著性
        pp_diff = (np.mean([r['peak_power'] for r in gcd1]) - 
                   np.mean([r['peak_power'] for r in gcd_gt1]))
        rc_diff = (np.mean([r['roller_correlation'] for r in gcd1]) - 
                   np.mean([r['roller_correlation'] for r in gcd_gt1]))
        
        print(f"\ngcd=1 vs gcd>1 差异:")
        print(f"  谐波集中度差: {pp_diff:+.4f} ({'gcd=1更优 ✅' if pp_diff < 0 else 'gcd>1更优 ⚠️'})")
        print(f"  滚筒相关性差: {rc_diff:+.4f} ({'gcd=1更优 ✅' if rc_diff < 0 else 'gcd>1更优 ⚠️'})")
        
        if pp_diff < 0 and rc_diff < 0:
            print("\n★★★ 结论：gcd=1 确认更优！磁静音理论在偶极子模型中得到验证。")
        elif pp_diff < 0 or rc_diff < 0:
            print("\n★★☆ 结论：gcd=1 在一个指标上更优，另一个指标持平或略差。")
        else:
            print("\n★☆☆ 结论：在简化偶极子模型中未观察到gcd=1的优势。需要有限尺寸磁体模型。")
    
    print("\n✓ 全部完成。")


if __name__ == '__main__':
    main()
