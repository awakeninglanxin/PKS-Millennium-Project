# -*- coding: utf-8 -*-
"""
Farey 时钟分相 — GPU SM 调度仿真 + 峰值电流建模
==================================================
实验 B：用 Farey 分数为 GPU 流式多处理器(SM)分配时钟相位偏移，
      量化同步开关噪声(SSN)的降低幅度。

原理：
  所有 SM 在同一时钟边沿翻转 → 电流尖峰叠加 → P_peak = N × I_single
  Farey 分相：SM_k 的相位偏移 θ_k = 2π × p_k/q_k  (Farey 序列)
  → 电流尖峰被分散到不同的时间点 → P_peak ≈ I_single × max_overlap

模拟三个场景：
  1. 均匀分相 (每 SM 均匀间隔) → 理论最优但硬件不可实现
  2. Farey 分相 (基于 Farey 分数序列) → 自然、可实现的近似最优
  3. 无分相 (全部同时翻转) → 基准对照

输出：
  - GPU峰值电流对比图
  - 时序电流波形
  - CSV 数据表

运行：python farey_gpu_clock_phase.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from math import gcd
import os

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = THIS_DIR  # 直接输出到脚本所在目录

# ===== 参数 =====
N_SM = 128              # GPU SM 数量 (模拟 RTX 4090: 128 SM)
CLOCK_PERIOD = 0.4      # 时钟周期 (ns, 对应 2.5 GHz)
SIM_RESOLUTION = 2000   # 单个周期的仿真时间分辨率
SWITCH_DURATION = 0.02  # 单个 SM 开关电流脉冲宽度 (ns)
I_SINGLE = 0.5          # 单个 SM 开关峰值电流 (A, 归一化)
NUM_RUNS = 500          # 多次运行取平均


def farey_sequence(max_denom):
    """生成 Farey 分数序列 p/q (0 <= p/q <= 1, q <= max_denom)"""
    seq = [(0, 1), (1, 1)]
    a, b, c, d = 0, 1, 1, max_denom
    while c <= max_denom:
        k = (max_denom + b) // d
        a, b, c, d = c, d, k * c - a, k * d - b
        if b <= max_denom and d <= max_denom:
            seq.append((c, d))
    return sorted(set(seq), key=lambda x: x[0]/x[1])


def farey_phase_offsets(n_sm):
    """从 Farey 序列中取 n_sm 个等间距分数作为相位偏移"""
    farey = farey_sequence(200)  # 足够大的分母范围
    # 取 n_sm 个等间距的 Farey 分数
    step = max(1, (len(farey) - 2) // (n_sm - 1))
    indices = [1 + i * step for i in range(n_sm - 1)]
    indices = [min(i, len(farey) - 2) for i in indices]
    phases = [0.0]  # 第一个 SM 相位为 0
    for idx in indices:
        p, q = farey[idx]
        phases.append(p / q)
    phases.append(1.0)  # 最后一个
    # 截断到 n_sm
    phases = sorted(set(phases))
    if len(phases) < n_sm:
        # 填充
        while len(phases) < n_sm:
            phases.append(phases[-1] + (1.0 - phases[-1]) / (n_sm - len(phases) + 1))
    return np.array(phases[:n_sm])


def gaussian_pulse(t, center, width):
    """高斯脉冲：模拟单个 SM 的开关电流"""
    return np.exp(-((t - center) / width) ** 2)


def simulate_current_waveform(phases, n_sm, n_points):
    """模拟一个时钟周期内的总电流波形"""
    t = np.linspace(0, 1, n_points)
    total_current = np.zeros(n_points)
    for i in range(n_sm):
        center = phases[i % len(phases)] if len(phases) > 0 else 0
        # 脉冲宽度归一化
        pulse_width = SWITCH_DURATION / CLOCK_PERIOD
        total_current += gaussian_pulse(t, center, pulse_width)
    return t, total_current


def main():
    print("=" * 60)
    print("Farey 时钟分相 — GPU SM 调度仿真")
    print(f"SM数量: {N_SM} | 时钟周期: {CLOCK_PERIOD}ns | 运行轮数: {NUM_RUNS}")
    print("=" * 60)

    # ---- 生成三种分相方案 ----
    # 方案 1: 无分相 (基准)
    phases_none = np.zeros(N_SM)
    # 方案 2: 均匀分相 (理论最优)
    phases_uniform = np.linspace(0, 1, N_SM, endpoint=False)
    # 方案 3: Farey 分相
    phases_farey = farey_phase_offsets(N_SM)

    print(f"\nFarey 分母范围: 1..200")
    print(f"Farey 分数密度: {len(farey_sequence(200))} 个分数")
    print(f"取 {N_SM} 个等间距相位偏移")
    print(f"前10个相位: {np.round(phases_farey[:10], 4)}")

    # ---- 多次运行取平均 ----
    results = {'none': [], 'uniform': [], 'farey': []}

    for run in range(NUM_RUNS):
        # 每次运行加微小随机抖动模拟制造偏差
        jitter = np.random.normal(0, 0.002, N_SM)  # 2‰抖动

        for label, base_phases in [('none', phases_none),
                                     ('uniform', phases_uniform),
                                     ('farey', phases_farey)]:
            p = np.clip(base_phases + jitter, 0, 1)
            t, I = simulate_current_waveform(p, N_SM, SIM_RESOLUTION)
            I_peak = np.max(I)
            I_avg = np.mean(I)
            results[label].append(I_peak)

    # ---- 统计 ----
    print("\n" + "=" * 60)
    print("峰值电流统计 (归一化, 无分相 = 100%)")
    print("=" * 60)

    stats = {}
    for label in ['none', 'uniform', 'farey']:
        arr = np.array(results[label])
        mean_rel = np.mean(arr) / np.mean(results['none']) * 100
        std_rel = np.std(arr) / np.mean(results['none']) * 100
        stats[label] = {'mean': np.mean(arr), 'std': np.std(arr),
                        'rel': mean_rel, 'rel_std': std_rel}
        print(f"  {label:8s}: {mean_rel:5.1f}% ± {std_rel:4.1f}%")

    peak_reduction = (1 - stats['farey']['rel'] / 100) * 100
    uniform_reduction = (1 - stats['uniform']['rel'] / 100) * 100
    print(f"\n  Farey 分相降低峰值电流: {peak_reduction:.1f}%")
    print(f"  均匀分相降低峰值电流: {uniform_reduction:.1f}%")
    print(f"  Farey 达到理论最优的: {peak_reduction / uniform_reduction * 100:.1f}%")

    # ---- 出图 1: 箱线图 ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    colors = ['#e74c3c', '#27ae60', '#2980b9']
    labels = ['无分相\n(基准)', '均匀分相\n(理论最优)', f'Farey分相\n(-{peak_reduction:.1f}%)']
    box_data = [np.array(results[l]) / np.mean(results['none']) * 100 for l in ['none', 'uniform', 'farey']]

    bp = ax1.boxplot(box_data, labels=labels, patch_artist=True, widths=0.5)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.axhline(100, color='red', ls='--', alpha=0.5, label='基准 100%')
    ax1.set_ylabel('峰值电流 (归一化 %)')
    ax1.set_title(f'GPU SM 峰值电流对比 ({N_SM} SM, {NUM_RUNS}轮)')
    ax1.legend()
    ax1.grid(True, ls='--', alpha=0.3)

    # ---- 出图 2: 单周期波形叠加 ----
    # 最后一次运行的波形用于可视化
    t_none, I_none = simulate_current_waveform(phases_none, N_SM, SIM_RESOLUTION)
    t_uniform, I_uniform = simulate_current_waveform(phases_uniform, N_SM, SIM_RESOLUTION)
    t_farey, I_farey = simulate_current_waveform(phases_farey, N_SM, SIM_RESOLUTION)

    ax2.plot(t_none, I_none, color='#e74c3c', alpha=0.7, label='无分相', linewidth=1.2)
    ax2.plot(t_uniform, I_uniform, color='#27ae60', alpha=0.7, label='均匀分相', linewidth=1.2)
    ax2.plot(t_farey, I_farey, color='#2980b9', alpha=0.9, label='Farey分相', linewidth=1.5)

    ax2.axhline(np.max(I_none), color='#e74c3c', ls=':', alpha=0.4)
    ax2.axhline(np.max(I_farey), color='#2980b9', ls=':', alpha=0.4)

    ax2.set_xlabel('归一化时钟周期')
    ax2.set_ylabel('总电流 (归一化)')
    ax2.set_title(f'单周期电流波形对比')
    ax2.legend()
    ax2.grid(True, ls='--', alpha=0.3)

    fig.suptitle('Farey 时钟分相: GPU SM 电流尖峰抑制', fontsize=14, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    png_path = os.path.join(OUT_DIR, 'Farey_GPU_电流对比.png')
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"\n图已保存: {png_path}")

    # ---- 出图 3: 相位分布对比 ----
    fig2, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 3a: Farey 相位直方图
    axes[0, 0].hist(phases_farey, bins=50, color='#2980b9', alpha=0.8, edgecolor='white')
    axes[0, 0].set_xlabel('相位偏移 (归一化)')
    axes[0, 0].set_ylabel('SM 数量')
    axes[0, 0].set_title(f'Farey 分相: {N_SM} SM 相位分布')
    axes[0, 0].grid(True, ls='--', alpha=0.3)

    # 3b: 均匀分相直方图
    axes[0, 1].hist(phases_uniform, bins=50, color='#27ae60', alpha=0.8, edgecolor='white')
    axes[0, 1].set_xlabel('相位偏移 (归一化)')
    axes[0, 1].set_title(f'均匀分相: {N_SM} SM 相位分布')
    axes[0, 1].grid(True, ls='--', alpha=0.3)

    # 3c: 重叠数 vs 相位
    overlap_none = np.ones(SIM_RESOLUTION) * N_SM  # 全部重叠
    _, I_u = simulate_current_waveform(phases_uniform, N_SM, SIM_RESOLUTION)
    _, I_f = simulate_current_waveform(phases_farey, N_SM, SIM_RESOLUTION)

    axes[1, 0].plot(t_uniform, I_u, color='#27ae60', alpha=0.8, linewidth=1)
    axes[1, 0].axhline(np.max(I_u), color='#27ae60', ls=':', alpha=0.5)
    axes[1, 0].axhline(np.mean(I_u), color='gray', ls='--', alpha=0.5)
    axes[1, 0].set_xlabel('归一化周期')
    axes[1, 0].set_ylabel('电流')
    axes[1, 0].set_title('均匀分相: 电流波形')
    axes[1, 0].grid(True, ls='--', alpha=0.3)

    axes[1, 1].plot(t_farey, I_f, color='#2980b9', alpha=0.8, linewidth=1)
    axes[1, 1].axhline(np.max(I_f), color='#2980b9', ls=':', alpha=0.5)
    axes[1, 1].axhline(np.mean(I_f), color='gray', ls='--', alpha=0.5)
    axes[1, 1].set_xlabel('归一化周期')
    axes[1, 1].set_title('Farey 分相: 电流波形 (细节)')
    axes[1, 1].grid(True, ls='--', alpha=0.3)

    fig2.suptitle('Farey vs 均匀 分相: 相位分布与电流波形', fontsize=14, fontweight='bold')
    fig2.tight_layout(rect=[0, 0, 1, 0.95])
    png2 = os.path.join(OUT_DIR, 'Farey_GPU_相位分布.png')
    fig2.savefig(png2, dpi=150)
    plt.close(fig2)
    print(f"图已保存: {png2}")

    # ---- 导出 CSV ----
    csv_path = os.path.join(OUT_DIR, 'Farey_GPU_结果.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("方案,峰值电流均值,峰值电流标准差,相对基准%,降低幅度%\n")
        for label in ['none', 'uniform', 'farey']:
            s = stats[label]
            reduction = (1 - s['rel'] / 100) * 100
            f.write(f"{label},{s['mean']:.4f},{s['std']:.4f},{s['rel']:.1f},{reduction:.1f}\n")
    print(f"CSV已保存: {csv_path}")

    # ---- 导出 Farey 相位表 ----
    phase_csv = os.path.join(OUT_DIR, 'Farey_相位偏移表.csv')
    with open(phase_csv, 'w', encoding='utf-8') as f:
        f.write("SM_ID,相位偏移,角度(度)\n")
        for i, ph in enumerate(phases_farey):
            f.write(f"SM_{i},{ph:.6f},{ph*360:.2f}\n")
    print(f"相位表已保存: {phase_csv}")

    print("\n" + "=" * 60)
    print("【结论】")
    print(f"  Farey 时钟分相降低 GPU SM 同步开关噪声峰值 {peak_reduction:.1f}%")
    print(f"  达到理论最优(均匀分相)的 {peak_reduction/uniform_reduction*100:.1f}%")
    print(f"  优势: Farey 分数天然对应硬件时钟分频器，无需额外电路")
    print("=" * 60)


if __name__ == "__main__":
    main()
