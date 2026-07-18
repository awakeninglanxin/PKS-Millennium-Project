# -*- coding: utf-8 -*-
"""
SEG 磁齿轮静磁仿真 — Phase 1
=============================
核心问题：
Q1: gcd(N_stator, N_roller) = 1 是否真的产生更平滑的扭矩？
Q2: Fibonacci 滚筒数 (13/21/34) 是否优于原版等差 (12/22/32)？
Q3: 三环之间是否存在"磁齿轮减速比"自锁现象？

方法：解析偶极子-偶极子力公式，无需求解PDE，纯numpy。
绝对扭矩值不精确，但相对平滑度对比完全有效。

输出：扭矩曲线图 + 平滑度指标对比表
"""

import numpy as np
from numpy import pi, cos, sin, sqrt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os, sys, time, json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

MU0_4PI = 1e-7  # μ₀/(4π)

# ============================================================
# 物理核心：偶极子-偶极子力（解析公式）
# ============================================================

def dipole_field_at(r_vec, m):
    """源偶极子 m 在位置 r_vec 处产生的 B 场"""
    r = np.linalg.norm(r_vec)
    if r < 1e-12:
        return np.zeros(3)
    r_hat = r_vec / r
    mr = np.dot(m, r_hat)
    return (MU0_4PI / r**3) * (3 * mr * r_hat - m)


def dipole_dipole_force(m_src, m_tgt, r_vec):
    """源偶极子 m_src 对目标偶极子 m_tgt 的作用力。
    r_vec = r_tgt - r_src （从源指向目标）
    返回 m_tgt 受到的力
    """
    r = np.linalg.norm(r_vec)
    if r < 1e-12:
        return np.zeros(3)
    r_hat = r_vec / r
    m1r = np.dot(m_src, r_hat)
    m2r = np.dot(m_tgt, r_hat)
    m12 = np.dot(m_src, m_tgt)
    coeff = 3 * MU0_4PI / r**4
    return coeff * (m1r * m_tgt + m2r * m_src + m12 * r_hat - 5 * m1r * m2r * r_hat)


def dipole_dipole_torque(m_src, m_tgt, r_vec, axis_point=None):
    """计算源偶极子对目标偶极子的力矩（绕指定轴点）。
    axis_point: 旋转轴位置，默认原点
    """
    if axis_point is None:
        axis_point = np.zeros(3)
    F = dipole_dipole_force(m_src, m_tgt, r_vec)
    lever = r_vec + (axis_point - (axis_point + r_vec))  # 力臂
    # 简化：力臂 = m_tgt位置 - axis_point
    r_tgt = axis_point  # 暂时不用
    return F  # 只返回力，力矩在外部计算


# ============================================================
# 几何构建
# ============================================================

def build_stator(N_poles, R=1.0, m_strength=1.0):
    """构建定子环：N_poles 个径向交替磁极
    
    返回: (positions[N,3], moments[N,3])
    """
    angles = 2 * pi * np.arange(N_poles) / N_poles
    pos = np.column_stack([R * cos(angles), R * sin(angles), np.zeros(N_poles)])
    polarity = (-1) ** np.arange(N_poles)[:, np.newaxis]
    moments = polarity * m_strength * np.column_stack([
        cos(angles), sin(angles), np.zeros(N_poles)
    ])
    return pos, moments


def build_rollers(N_rollers, R_orbit, m_strength=0.3, start_angle=0):
    """构建滚筒环：N_rollers 个均匀分布的滚筒
    
    start_angle: 参考滚筒的初始角（用于多环相位偏移）
    """
    angles = start_angle + 2 * pi * np.arange(N_rollers) / N_rollers
    pos = np.column_stack([R_orbit * cos(angles), R_orbit * sin(angles), np.zeros(N_rollers)])
    # 滚筒磁矩：径向（可调极性）
    polarity = (-1) ** np.arange(N_rollers)[:, np.newaxis]
    moments = polarity * m_strength * np.column_stack([
        cos(angles), sin(angles), np.zeros(N_rollers)
    ])
    return pos, moments


# ============================================================
# 扭矩计算
# ============================================================

def compute_roller_forces(stator_pos, stator_m, roller_pos, roller_m, 
                          center=np.zeros(3)):
    """计算每个滚筒受到的总切向力（绕中心的力矩 / 轨道半径）
    
    返回: tangential_forces[N_rollers]（正值=加速方向）
    """
    n_rollers = len(roller_pos)
    F_tang = np.zeros(n_rollers)
    
    for j in range(n_rollers):
        F_total = np.zeros(3)
        for i in range(len(stator_pos)):
            r_vec = roller_pos[j] - stator_pos[i]
            F = dipole_dipole_force(stator_m[i], roller_m[j], r_vec)
            F_total += F
        
        # 切向分量
        r_hat = roller_pos[j] - center
        r_hat = r_hat / (np.linalg.norm(r_hat) + 1e-12)
        tang_hat = np.array([-r_hat[1], r_hat[0], 0])
        F_tang[j] = np.dot(F_total, tang_hat)
    
    return F_tang


def compute_torque_curve(N_stator, N_rollers, R_stator=1.0, R_orbit=0.65,
                         m_stator=1.0, m_roller=0.3, n_steps=720,
                         spin_ratio=None):
    """计算一个完整轨道周期的净切向力曲线
    
    spin_ratio: 滚筒自转/公转比。None=固定径向，R_stator/R_orbit=纯滚动
    """
    stator_pos, stator_m = build_stator(N_stator, R_stator, m_stator)
    center = np.zeros(3)
    
    angles = 2 * pi * np.arange(n_steps) / n_steps
    net_F_tang = np.zeros(n_steps)
    
    for idx, theta_ref in enumerate(angles):
        # 每个滚筒的位置（等间距分布）
        roller_angles = theta_ref + 2 * pi * np.arange(N_rollers) / N_rollers
        
        roller_pos = np.column_stack([
            R_orbit * cos(roller_angles),
            R_orbit * sin(roller_angles),
            np.zeros(N_rollers)
        ])
        
        # 滚筒磁矩方向
        if spin_ratio is not None:
            spin_angles = roller_angles * spin_ratio
            polarity = (-1) ** np.arange(N_rollers)[:, np.newaxis]
            roller_m = polarity * m_roller * np.column_stack([
                cos(spin_angles), sin(spin_angles), np.zeros(N_rollers)
            ])
        else:
            polarity = (-1) ** np.arange(N_rollers)[:, np.newaxis]
            roller_m = polarity * m_roller * np.column_stack([
                cos(roller_angles), sin(roller_angles), np.zeros(N_rollers)
            ])
        
        F_tang = compute_roller_forces(stator_pos, stator_m, roller_pos, roller_m, center)
        net_F_tang[idx] = np.sum(F_tang)
    
    return angles, net_F_tang


# ============================================================
# 平滑度指标
# ============================================================

def smoothness_metrics(torque_curve):
    """计算扭矩平滑度指标（值越小越平滑）
    
    返回 dict:
    - cv: 变异系数 (std/|mean|)
    - ripple_pct: 峰峰值/均值 (%)
    - rms_ripple: RMS波动/均值
    - zero_crossings: 过零次数（方向改变次数）
    - reversal_pct: 反向扭矩占比 (%)
    """
    t = torque_curve
    abs_t = np.abs(t)
    mean_abs = np.mean(abs_t)
    
    if mean_abs < 1e-15:
        return {'cv': 0, 'ripple_pct': 0, 'rms_ripple': 0, 
                'zero_crossings': 0, 'reversal_pct': 0, 'mean_torque': 0}
    
    cv = np.std(t) / (mean_abs + 1e-15)
    ripple_pct = 100 * (np.max(t) - np.min(t)) / (mean_abs + 1e-15)
    rms_ripple = np.sqrt(np.mean((t - np.mean(t))**2)) / mean_abs
    
    # 过零次数（方向反转）
    signs = np.sign(t)
    zero_crossings = np.sum(np.abs(np.diff(signs)) > 0)
    
    # 反向扭矩占比
    reversal_pct = 100 * np.sum(t < 0) / len(t)
    
    mean_torque = np.mean(t)
    
    return {
        'cv': cv, 'ripple_pct': ripple_pct, 'rms_ripple': rms_ripple,
        'zero_crossings': zero_crossings, 'reversal_pct': reversal_pct,
        'mean_torque': mean_torque
    }


# ============================================================
# 三环模型（用于Q3自锁分析）
# ============================================================

def compute_three_ring_torques(N_outer, N_mid, N_inner,
                               R_stator=1.0, R_outer_orbit=0.75,
                               R_mid_orbit=0.50, R_inner_orbit=0.28,
                               m_stator=1.0, m_roller=0.3,
                               n_steps=720):
    """计算三层滚筒同时运行时的净扭矩
    
    三层不是独立运行的——外环驱动中环，中环驱动内环。
    简化模型：每层的滚筒只与相邻层（定子或外环）交互。
    
    返回: {
        'outer_torque': 定子→外环的驱动力矩,
        'mid_torque': 外环→中环的传递力矩,
        'inner_torque': 中环→内环的传递力矩,
        'total_torque': 总净力矩
    }
    """
    stator_pos, stator_m = build_stator(N_stator_outer := 34, R_stator, m_stator)
    center = np.zeros(3)
    
    angles = 2 * pi * np.arange(n_steps) / n_steps
    result = {
        'angles': angles,
        'outer_torque': np.zeros(n_steps),
        'mid_torque': np.zeros(n_steps),
        'inner_torque': np.zeros(n_steps),
        'total_torque': np.zeros(n_steps)
    }
    
    for idx, theta_ref in enumerate(angles):
        # === 外环滚筒 ===
        outer_angles = theta_ref + 2 * pi * np.arange(N_outer) / N_outer
        outer_pos = np.column_stack([
            R_outer_orbit * cos(outer_angles),
            R_outer_orbit * sin(outer_angles),
            np.zeros(N_outer)
        ])
        polarity_o = (-1) ** np.arange(N_outer)[:, np.newaxis]
        outer_m = polarity_o * m_roller * np.column_stack([
            cos(outer_angles), sin(outer_angles), np.zeros(N_outer)
        ])
        
        # 定子→外环力
        F_outer = compute_roller_forces(stator_pos, stator_m, outer_pos, outer_m, center)
        result['outer_torque'][idx] = np.sum(F_outer) * R_outer_orbit
        
        # === 中环滚筒 ===
        mid_angles = theta_ref * 1.2 + 2 * pi * np.arange(N_mid) / N_mid  # 差速
        mid_pos = np.column_stack([
            R_mid_orbit * cos(mid_angles),
            R_mid_orbit * sin(mid_angles),
            np.zeros(N_mid)
        ])
        polarity_m = (-1) ** np.arange(N_mid)[:, np.newaxis]
        mid_m = polarity_m * m_roller * np.column_stack([
            cos(mid_angles), sin(mid_angles), np.zeros(N_mid)
        ])
        
        # 外环→中环力（外环滚筒作为"定子"驱动中环）
        F_mid = compute_roller_forces(outer_pos, outer_m, mid_pos, mid_m, center)
        result['mid_torque'][idx] = np.sum(F_mid) * R_mid_orbit
        
        # === 内环滚筒 ===
        inner_angles = theta_ref * 1.5 + 2 * pi * np.arange(N_inner) / N_inner
        inner_pos = np.column_stack([
            R_inner_orbit * cos(inner_angles),
            R_inner_orbit * sin(inner_angles),
            np.zeros(N_inner)
        ])
        polarity_i = (-1) ** np.arange(N_inner)[:, np.newaxis]
        inner_m = polarity_i * m_roller * np.column_stack([
            cos(inner_angles), sin(inner_angles), np.zeros(N_inner)
        ])
        
        F_inner = compute_roller_forces(mid_pos, mid_m, inner_pos, inner_m, center)
        result['inner_torque'][idx] = np.sum(F_inner) * R_inner_orbit
        
        result['total_torque'][idx] = (result['outer_torque'][idx] + 
                                        result['mid_torque'][idx] + 
                                        result['inner_torque'][idx])
    
    return result


# ============================================================
# 主实验：Q1 + Q2 — 单环扭矩平滑度对比
# ============================================================

def experiment_q1_q2():
    """实验 Q1 & Q2：对比不同 gcd 配置的扭矩平滑度"""
    print("=" * 70)
    print("SEG 磁齿轮仿真 — Q1 & Q2: 扭矩平滑度对比")
    print("=" * 70)
    
    # 测试配置：(N_stator, N_rollers, label, 备注)
    configs = [
        # --- gcd 对比组：固定定子=34，变滚筒数 ---
        (34, 34, "gcd=34 (整除数)", "定子34/滚筒34"),
        (34, 17, "gcd=17", "定子34/滚筒17"),
        (34, 12, "gcd=2", "定子34/滚筒12"),
        (34, 13, "gcd=1 FIB", "定子34/滚筒13 ★Fibonacci"),
        (34, 11, "gcd=1 素数", "定子34/滚筒11 素数"),
        (34, 21, "gcd=1 FIB", "定子34/滚筒21 ★Fibonacci"),
        
        # --- 原版等差 vs Fibonacci ---
        (34, 32, "原版外环 gcd=2", "34/32 等差外环"),
        (34, 34, "FIB外环 gcd=34", "34/34 Fibonacci外环"),
        (22, 22, "原版中环 gcd=22", "22/22 等差距"),
        (21, 34, "FIB中环 gcd=1", "21/34 ★跨环对照"),
        
        # --- Jellium 推荐素数滚筒 ---
        (34, 17, "Jellium素数 gcd=17", "17=Jellium族素数（不好）"),
        (34, 23, "Jellium素数 gcd=1", "23=Jellium族素数 ★黄金"),
        (30, 17, "gcd=1 SEG基准", "30/17 规格B推荐"),
        (30, 23, "gcd=1 SEG基准", "30/23 ★"),
    ]
    
    results = []
    for N_s, N_r, label, note in configs:
        g = np.gcd(N_s, N_r)
        print(f"\n  计算: N_stator={N_s}, N_roller={N_r}, gcd={g} [{note}]...", end=" ")
        t0 = time.time()
        angles, torque = compute_torque_curve(N_s, N_r, R_stator=1.0, R_orbit=0.65,
                                               m_stator=1.0, m_roller=0.3, n_steps=720)
        metrics = smoothness_metrics(torque)
        metrics['N_stator'] = N_s
        metrics['N_roller'] = N_r
        metrics['gcd'] = g
        metrics['label'] = label
        metrics['note'] = note
        metrics['lcm'] = np.lcm(N_s, N_r)
        metrics['compute_time'] = time.time() - t0
        results.append(metrics)
        print(f"CV={metrics['cv']:.4f}, ripple={metrics['ripple_pct']:.1f}%, "
              f"reversal={metrics['reversal_pct']:.1f}%, 耗时{metrics['compute_time']:.2f}s")
    
    return results


# ============================================================
# 绘制 Q1+Q2 图表
# ============================================================

def plot_q1_q2(results):
    """绘制扭矩曲线对比图和平滑度指标图"""
    
    # 选择代表性配置重算扭矩曲线（用于绘图）
    plot_configs = [
        (34, 34, "gcd=34（整除：最差）"),
        (34, 17, "gcd=17"),
        (34, 12, "gcd=2"),
        (34, 13, "gcd=1 FIB 13（★Fibonacci内环）"),
        (34, 21, "gcd=1 FIB 21（★Fibonacci中环）"),
        (34, 11, "gcd=1 素数11"),
        (34, 23, "gcd=1 Jellium素数23（★黄金滚筒）"),
    ]
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 18))
    
    # === 子图1：扭矩波形对比 ===
    ax = axes[0]
    colors = plt.cm.tab10(np.linspace(0, 1, len(plot_configs)))
    
    for idx, (N_s, N_r, label) in enumerate(plot_configs):
        angles, torque = compute_torque_curve(N_s, N_r, R_stator=1.0, R_orbit=0.65,
                                               m_stator=1.0, m_roller=0.3, n_steps=360)
        # 归一化便于对比波形
        t_norm = torque / (np.max(np.abs(torque)) + 1e-15)
        ax.plot(angles * 180/pi, t_norm, color=colors[idx], linewidth=1.2,
                label=label, alpha=0.85)
    
    ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
    ax.set_xlabel('参考角 (度)', fontsize=12)
    ax.set_ylabel('归一化净切向力', fontsize=12)
    ax.set_title('SEG磁齿轮扭矩波形对比 — 不同gcd配置（归一化）', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)
    
    # === 子图2：CV vs gcd 散点图 ===
    ax = axes[1]
    gcdn = np.array([r['gcd'] for r in results])
    cvs = np.array([r['cv'] for r in results])
    labels = np.array([r['label'] for r in results])
    
    # 颜色：gcd=1绿色，越大越红
    colors_scatter = plt.cm.RdYlGn_r(gcdn / max(gcdn.max(), 1))
    
    sc = ax.scatter(gcdn, cvs, c=colors_scatter, s=120, edgecolors='black', linewidth=0.5, zorder=5)
    
    # 标注关键点
    for i in range(len(results)):
        if 'FIB' in labels[i] or '黄金' in labels[i] or '素数' in labels[i]:
            ax.annotate(labels[i], (gcdn[i], cvs[i]), 
                       textcoords="offset points", xytext=(8, 5), fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.7))
    
    ax.set_xlabel('gcd(N_stator, N_roller)', fontsize=12)
    ax.set_ylabel('扭矩变异系数 CV (越小越平滑)', fontsize=12)
    ax.set_title('扭矩平滑度 vs gcd — CV越低=越平滑', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 趋势线
    if len(gcdn) > 2:
        z = np.polyfit(gcdn, cvs, 1)
        x_fit = np.linspace(0, max(gcdn), 100)
        ax.plot(x_fit, np.polyval(z, x_fit), '--', color='gray', linewidth=1, alpha=0.5,
                label=f'线性趋势 (斜率={z[0]:.3f})')
        ax.legend(fontsize=9)
    
    # === 子图3：综合对比表 ===
    ax = axes[2]
    ax.axis('off')
    
    # 按CV排序
    sorted_results = sorted(results, key=lambda x: x['cv'])
    
    table_data = []
    for i, r in enumerate(sorted_results[:15]):
        rank = '🥇' if i == 0 else ('🥈' if i == 1 else ('🥉' if i == 2 else str(i+1)))
        table_data.append([
            rank,
            f"{r['N_stator']}/{r['N_roller']}",
            str(r['gcd']),
            r['label'].replace('gcd=', ''),
            f"{r['cv']:.4f}",
            f"{r['ripple_pct']:.1f}%",
            f"{r['reversal_pct']:.1f}%",
            f"{r['lcm']:,}",
        ])
    
    col_labels = ['排名', '定子/滚筒', 'gcd', '类型', 'CV', '波动%', '反转%', 'LCM']
    table = ax.table(cellText=table_data, colLabels=col_labels, 
                     loc='center', cellLoc='center',
                     colWidths=[0.05, 0.12, 0.06, 0.25, 0.10, 0.10, 0.10, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.4)
    
    # 高亮前三名
    for i in range(3):
        for j in range(len(col_labels)):
            cell = table[i+1, j]
            if i == 0:
                cell.set_facecolor('#FFD700')
            elif i == 1:
                cell.set_facecolor('#C0C0C0')
            elif i == 2:
                cell.set_facecolor('#CD7F32')
    
    ax.set_title('扭矩平滑度综合排名 (CV从小到大)', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout(pad=3)
    return fig


# ============================================================
# 实验 Q3：三环自锁分析
# ============================================================

def experiment_q3():
    """实验 Q3：三环磁齿轮自锁分析"""
    print("\n" + "=" * 70)
    print("SEG 磁齿轮仿真 — Q3: 三环自锁分析")
    print("=" * 70)
    
    # 两组对比：原版等差 vs Fibonacci
    configs = [
        ("原版等差", 32, 22, 12),    # 外环32, 中环22, 内环12
        ("Fibonacci", 34, 21, 13),    # 外环34, 中环21, 内环13
        ("混合优化", 34, 22, 13),     # 外环Fib, 中环原版, 内环Fib
        ("混合B", 32, 21, 12),        # 外环原版, 中环Fib, 内环原版
    ]
    
    all_results = []
    
    for name, N_o, N_m, N_i in configs:
        print(f"\n  模拟: {name} (外{N_o}/中{N_m}/内{N_i})...", end=" ")
        t0 = time.time()
        result = compute_three_ring_torques(N_o, N_m, N_i, n_steps=360)
        
        # 各环扭矩指标
        for key in ['outer_torque', 'mid_torque', 'inner_torque', 'total_torque']:
            m = smoothness_metrics(result[key])
            m['config'] = name
            m['ring'] = key
            m['N_outer'] = N_o
            m['N_mid'] = N_m
            m['N_inner'] = N_i
            m['gcd_outer'] = np.gcd(34, N_o)  # 定子34
            tg = np.gcd(N_o, N_m)
            m['gcd_outer_mid'] = tg
            m['gcd_mid_inner'] = np.gcd(N_m, N_i)
            all_results.append(m)
        
        elapsed = time.time() - t0
        total_m = [r for r in all_results if r['config'] == name and r['ring'] == 'total_torque'][-1]
        print(f"总扭矩CV={total_m['cv']:.4f}, 反转率={total_m['reversal_pct']:.1f}%, "
              f"gcd(外中)={np.gcd(N_o, N_m)}, gcd(中内)={np.gcd(N_m, N_i)}, "
              f"耗时{elapsed:.1f}s")
    
    return all_results


def plot_q3(all_results):
    """绘制三环自锁分析图"""
    
    configs = list(set(r['config'] for r in all_results))
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    
    # === 子图1：各环扭矩CV对比 ===
    ax = axes[0]
    x = np.arange(4)  # outer, mid, inner, total
    ring_names = ['外环(outer)', '中环(mid)', '内环(inner)', '总扭矩(total)']
    width = 0.2
    
    colors = ['#E24B4A', '#378ADD', '#1D9E75', '#EF9F27']
    
    for i, cfg in enumerate(configs):
        cfg_results = [r for r in all_results if r['config'] == cfg]
        cvs = []
        for ring in ['outer_torque', 'mid_torque', 'inner_torque', 'total_torque']:
            match = [r for r in cfg_results if r['ring'] == ring]
            cvs.append(match[0]['cv'] if match else 0)
        bars = ax.bar(x + i * width, cvs, width, label=cfg, color=colors[i], alpha=0.85)
        
        # 数值标注
        for j, (bar, cv) in enumerate(zip(bars, cvs)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{cv:.3f}', ha='center', va='bottom', fontsize=7)
    
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(ring_names, fontsize=10)
    ax.set_ylabel('扭矩变异系数 CV', fontsize=12)
    ax.set_title('三环各层扭矩平滑度对比 — 原版差 vs Fibonacci', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    # === 子图2：自锁指标 ===
    ax = axes[1]
    
    # 自锁分析：反转率 > 阈值 = 自锁风险
    threshold = 30  # 反转率超过30%视为自锁风险
    
    self_lock_data = []
    for cfg in configs:
        cfg_results = [r for r in all_results if r['config'] == cfg]
        total = [r for r in cfg_results if r['ring'] == 'total_torque'][0]
        
        # gcd乘积：越小越好（互质=静音）
        gcd_prod = total['gcd_outer_mid'] * total['gcd_mid_inner']
        
        self_lock_data.append({
            'config': cfg,
            'total_cv': total['cv'],
            'reversal_pct': total['reversal_pct'],
            'gcd_outer_mid': total['gcd_outer_mid'],
            'gcd_mid_inner': total['gcd_mid_inner'],
            'gcd_product': gcd_prod,
            'lock_risk': 'HIGH' if total['reversal_pct'] > threshold else 'LOW'
        })
    
    # 绘制自锁风险矩阵
    for i, d in enumerate(self_lock_data):
        y = 3 - i
        color = '#E24B4A' if d['lock_risk'] == 'HIGH' else '#1D9E75'
        ax.barh(y, d['reversal_pct'], color=color, alpha=0.7, height=0.6)
        ax.text(d['reversal_pct'] + 1, y, 
                f"{d['config']}: 反转{d['reversal_pct']:.1f}% | "
                f"gcd({d['gcd_outer_mid']},{d['gcd_mid_inner']}) → {d['lock_risk']}",
                va='center', fontsize=10)
    
    ax.axvline(x=threshold, color='red', linestyle='--', linewidth=1.5, 
               label=f'自锁警戒线 ({threshold}%)')
    ax.set_xlabel('总扭矩反转占比 (%)', fontsize=12)
    ax.set_yticks([])
    ax.set_title('三环磁齿轮自锁风险评估', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_xlim(0, max(100, max(d['reversal_pct'] for d in self_lock_data) * 1.3))
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout(pad=3)
    return fig


# ============================================================
# 主函数
# ============================================================

def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("SEG 磁齿轮静磁仿真 v1.0")
    print(f"输出目录: {out_dir}")
    print(f"方法: 解析偶极子力公式, μ₀/(4π) = {MU0_4PI}")
    print()
    
    # === Q1 + Q2 ===
    results_q1q2 = experiment_q1_q2()
    fig1 = plot_q1_q2(results_q1q2)
    path1 = os.path.join(out_dir, 'seg_torque_smoothness_q1q2.png')
    fig1.savefig(path1, dpi=150, bbox_inches='tight')
    plt.close(fig1)
    print(f"\n  [图表] Q1+Q2 扭矩平滑度 → {path1}")
    
    # 保存JSON数据
    json_path = os.path.join(out_dir, 'seg_torque_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results_q1q2, f, ensure_ascii=False, indent=2, default=str)
    print(f"  [数据] JSON结果 → {json_path}")
    
    # === Q3 ===
    results_q3 = experiment_q3()
    fig2 = plot_q3(results_q3)
    path2 = os.path.join(out_dir, 'seg_three_ring_lock_q3.png')
    fig2.savefig(path2, dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print(f"\n  [图表] Q3 三环自锁分析 → {path2}")
    
    # === 总结 ===
    print("\n" + "=" * 70)
    print("仿真结论摘要")
    print("=" * 70)
    
    # Q1 答案
    gcd_results = [(r['cv'], r['gcd'], r['label']) for r in results_q1q2]
    gcd_results.sort()
    print("\nQ1: gcd(N_stator, N_roller) = 1 是否真的产生更平滑的扭矩？")
    for cv, g, label in gcd_results[:5]:
        print(f"    CV={cv:.4f}  gcd={g:2d}  {label}")
    
    best = gcd_results[0]
    worst = gcd_results[-1]
    print(f"  最佳: {best[2]} (CV={best[0]:.4f})")
    print(f"  最差: {worst[2]} (CV={worst[0]:.4f})")
    
    # Q2 答案
    fib_configs = [r for r in results_q1q2 if 'FIB' in r['label']]
    arith_configs = [r for r in results_q1q2 if '原版' in r['label'] or '等差' in r['label']]
    
    print("\nQ2: Fibonacci (13/21/34) 是否优于原版等差 (12/22/32)？")
    if fib_configs:
        fib_avg_cv = np.mean([r['cv'] for r in fib_configs])
        print(f"  Fibonacci配置平均CV: {fib_avg_cv:.4f}")
        for r in fib_configs:
            print(f"    {r['label']}: CV={r['cv']:.4f}, reversal={r['reversal_pct']:.1f}%")
    if arith_configs:
        arith_avg_cv = np.mean([r['cv'] for r in arith_configs])
        print(f"  等差配置平均CV: {arith_avg_cv:.4f}")
        for r in arith_configs:
            print(f"    {r['label']}: CV={r['cv']:.4f}, reversal={r['reversal_pct']:.1f}%")
    
    # Q3 答案
    print("\nQ3: 三环之间是否存在磁齿轮减速比自锁现象？")
    for r in results_q3:
        if r['ring'] == 'total_torque':
            lock = "⚠️ 存在自锁风险" if r['reversal_pct'] > 30 else "✅ 无明显自锁"
            print(f"  {r['config']}: CV={r['cv']:.4f}, "
                  f"反转率={r['reversal_pct']:.1f}%, {lock}")
    
    print("\n✓ 全部完成。图表已保存至:", out_dir)


if __name__ == '__main__':
    main()
