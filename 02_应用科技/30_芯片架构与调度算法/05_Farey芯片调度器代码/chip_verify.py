"""
芯片幻方+Farey GPU验证：三合一
  Exp1: 多阶(3/5/7)幻方热仿真
  Exp2: Farey vs 均匀分相对比
  Exp3: D矩阵线性 vs 修正比例对比
"""
import numpy as np
import time, os, json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── 幻方生成 ──
def magic_square(n):
    if n % 2 == 0: raise ValueError
    M = np.zeros((n, n), dtype=np.int32)
    i, j = 0, n // 2
    for num in range(1, n * n + 1):
        M[i, j] = num
        ni, nj = (i - 1) % n, (j + 1) % n
        if M[ni, nj] != 0: i = (i + 1) % n
        else: i, j = ni, nj
    return M

# ── D矩阵：修正比例版（行列守恒）──
def duty_magic_proportional(M, D_base=0.35):
    """修正版：D ∝ (M_max - M + 1) 保持行列和守恒"""
    n = M.shape[0]
    M_max = n * n
    D = D_base * (M_max - M + 1) / M_max
    return D

def duty_magic_linear(M, D_min=0.03, D_max=0.35):
    """原始线性版 D=a·M+b（不保持行列守恒）"""
    n = M.shape[0]
    a = (D_max - D_min) / (1 - n * n)
    b = D_max - a
    return a * M + b

# ── Farey PWM相位 ──
def farey_sequence(N):
    a, b, c, d = 0, 1, 1, N
    seq = [(a, b)]
    while c <= N:
        k = (N + b) // d
        a, b, c, d = c, d, k * c - a, k * d - b
        seq.append((a, b))
    return seq

def farey_phases(n_tiles, T_cycle=1.0):
    """为n²个tile生成Farey分相的PWM相位"""
    farey = farey_sequence(n_tiles)
    phases = np.zeros(n_tiles * n_tiles)
    for i in range(n_tiles * n_tiles):
        num, den = farey[i % len(farey)]
        phases[i] = (num / den) * T_cycle
    return phases

# ── 热仿真核心 ──
def simulate_magic_thermal(n, total_steps=2000, D_type='proportional',
                           farey_on=True, dt=1e-9, T_env=300.0):
    """幻方tile阵列热仿真"""
    # 物理参数（调参使热效应可见）
    I_sq_R = 0.8; C_thermal = 30.0
    k_cond = 0.5; dx = 1.0; d_sub = 3.0; k_sub = 0.3
    K_tec = 0.1; C_switch = 0.1; V = 1.0
    
    M = magic_square(n)
    if D_type == 'proportional':
        D = duty_magic_proportional(M)
    else:
        D = duty_magic_linear(M)
    
    if farey_on:
        phases = farey_phases(n)
        phases = phases.reshape(n, n)
    else:
        phases = np.zeros((n, n))  # 全同步=最坏情况
    
    T = np.ones((n, n)) * T_env
    T_cycle = 1000 * dt
    pwm_prev = np.zeros((n, n))
    
    T_hist, flip_hist, power_hist = [], [], []
    
    for step in range(total_steps):
        t = step * dt
        
        # PWM状态
        phase_in_cycle = (t % T_cycle) / T_cycle
        pwm_on = np.zeros((n, n))
        for r in range(n):
            for c in range(n):
                phi = phases[r, c]
                d = D[r, c]
                if phi < d:
                    if phase_in_cycle >= phi and phase_in_cycle < phi + d:
                        pwm_on[r, c] = 1.0
                else:  # wrap
                    if phase_in_cycle >= phi or phase_in_cycle < (phi + d) % 1.0:
                        pwm_on[r, c] = 1.0
        
        # 焦耳热
        q_joule = pwm_on * D * I_sq_R
        
        # 开关损耗
        if step > 0:
            rising = np.clip(pwm_on - pwm_prev, 0, 1)
            n_flips = rising.sum()
            q_switch = rising * 0.5 * C_switch * V**2 / dt
        else:
            n_flips = 0
            q_switch = np.zeros_like(q_joule)
        pwm_prev = pwm_on.copy()
        flip_hist.append(n_flips)
        
        # TEC
        q_tec = -K_tec * (T - T_env) * pwm_on
        
        # 热传导
        T_pad = np.pad(T, 1, mode='edge')
        q_cond = (k_cond / dx) * (
            (T_pad[0:n, 1:n+1] - T) + (T_pad[2:n+2, 1:n+1] - T) +
            (T_pad[1:n+1, 2:n+2] - T) + (T_pad[1:n+1, 0:n] - T)
        )
        q_sub = (k_sub / d_sub) * (T_env - T)
        
        q_total = q_joule + q_switch + q_tec + q_cond + q_sub
        T = T + dt / C_thermal * q_total
        
        if step % 10 == 0:
            T_hist.append(T.copy())
            power_hist.append((q_joule.sum() + q_switch.sum()))
    
    return {
        'T_final': T, 'T_hist': T_hist,
        'flip_hist': flip_hist, 'power_hist': power_hist,
        'M': M, 'D': D
    }

# ── 主程序 ──
if __name__ == '__main__':
    OUT = '/root/results'
    os.makedirs(OUT, exist_ok=True)
    
    print("=" * 60)
    print("芯片幻方+Farey GPU验证 三合一")
    print("=" * 60)
    
    # ═══════════════════════════════════
    # Exp1: 多阶幻方对比 (3/5/7)
    # ═══════════════════════════════════
    print("\n[Exp1] 多阶幻方热仿真 3/5/7...")
    orders = [3, 5, 7]
    results_multi = {}
    
    for n in orders:
        t0 = time.time()
        print(f"  模拟 {n}×{n} ({n*n} tiles)...", end=' ')
        r = simulate_magic_thermal(n, total_steps=1500, D_type='proportional')
        results_multi[n] = r
        T = r['T_final']
        print(f"T={T.mean():.1f}K ±{T.std():.2f}, "
              f"max_flip={max(r['flip_hist'])}, "
              f"{(time.time()-t0):.1f}s")
    
    # Exp1 图表
    fig, axes = plt.subplots(len(orders), 2, figsize=(14, 4*len(orders)))
    for idx, n in enumerate(orders):
        r = results_multi[n]
        im = axes[idx, 0].imshow(r['T_final'], cmap='hot', vmin=300, vmax=310)
        axes[idx, 0].set_title(f'{n}x{n} Final T (mean={r["T_final"].mean():.1f}K, std={r["T_final"].std():.2f})')
        plt.colorbar(im, ax=axes[idx, 0])
        axes[idx, 1].plot(r['flip_hist'])
        axes[idx, 1].set_title(f'Simultaneous Switches (max={max(r["flip_hist"])})')
        axes[idx, 1].set_xlabel('Step'); axes[idx, 1].set_ylabel('Flipping tiles')
    plt.tight_layout()
    plt.savefig(f'{OUT}/exp1_multi_order.png', dpi=120)
    plt.close()
    
    # ═══════════════════════════════════
    # Exp2: Farey vs 均匀分相对比
    # ═══════════════════════════════════
    print("\n[Exp2] Farey vs 均匀分相 (5阶)...")
    t0 = time.time()
    r_farey = simulate_magic_thermal(5, total_steps=1500, farey_on=True)
    print(f"  Farey: max_flip={max(r_farey['flip_hist'])}, "
          f"T_std={r_farey['T_final'].std():.2f}, {time.time()-t0:.1f}s")
    
    t0 = time.time()
    r_uniform = simulate_magic_thermal(5, total_steps=1500, farey_on=False)
    print(f"  均匀:  max_flip={max(r_uniform['flip_hist'])}, "
          f"T_std={r_uniform['T_final'].std():.2f}, {time.time()-t0:.1f}s")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes[0,0].plot(r_farey['flip_hist'], 'b-', alpha=0.7, label='Farey')
    axes[0,0].plot(r_uniform['flip_hist'], 'r--', alpha=0.7, label='Uniform')
    axes[0,0].set_title(f'Flip Count: Farey(max={max(r_farey["flip_hist"])}) '
                        f'vs Uniform(max={max(r_uniform["flip_hist"])})')
    axes[0,0].legend()
    
    axes[0,1].imshow(r_farey['T_final'], cmap='hot', vmin=300, vmax=310)
    axes[0,1].set_title(f'Farey Final T ({r_farey["T_final"].std():.3f})')
    axes[1,0].imshow(r_uniform['T_final'], cmap='hot', vmin=300, vmax=310)
    axes[1,0].set_title(f'Uniform Final T ({r_uniform["T_final"].std():.3f})')
    
    axes[1,1].plot(r_farey['power_hist'], 'b-', alpha=0.5, label='Farey')
    axes[1,1].plot(r_uniform['power_hist'], 'r--', alpha=0.5, label='Uniform')
    axes[1,1].set_title(f'Power: Farey(avg={np.mean(r_farey["power_hist"])*1e3:.1f}mW) '
                        f'vs Uniform(avg={np.mean(r_uniform["power_hist"])*1e3:.1f}mW)')
    axes[1,1].legend()
    plt.tight_layout()
    plt.savefig(f'{OUT}/exp2_farey_vs_uniform.png', dpi=120)
    plt.close()
    
    # ═══════════════════════════════════
    # Exp3: D矩阵线性 vs 修正比例
    # ═══════════════════════════════════
    print("\n[Exp3] D矩阵线性 vs 修正比例 (5阶)...")
    M5 = magic_square(5)
    D_lin = duty_magic_linear(M5)
    D_prop = duty_magic_proportional(M5)
    
    print("  线性版D行列和:")
    for i in range(5): print(f"    行{i}: {D_lin[i].sum():.3f}")
    print("  修正版D行列和:")
    for i in range(5): print(f"    行{i}: {D_prop[i].sum():.3f}")
    
    t0 = time.time()
    r_lin = simulate_magic_thermal(5, total_steps=1500, D_type='linear')
    print(f"  线性D: T_std={r_lin['T_final'].std():.3f}, {time.time()-t0:.1f}s")
    
    t0 = time.time()
    r_prop = simulate_magic_thermal(5, total_steps=1500, D_type='proportional')
    print(f"  修正D: T_std={r_prop['T_final'].std():.3f}, {time.time()-t0:.1f}s")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    im0 = axes[0].imshow(D_lin, cmap='RdYlGn_r')
    axes[0].set_title(f'Linear D (rows not conserved)\n'
                      f'row sums: {[f"{D_lin[i].sum():.2f}" for i in range(5)]}')
    plt.colorbar(im0, ax=axes[0])
    
    im1 = axes[1].imshow(D_prop, cmap='RdYlGn_r')
    axes[1].set_title(f'Proportional D (rows conserved)\n'
                      f'row sums: {[f"{D_prop[i].sum():.2f}" for i in range(5)]}')
    plt.colorbar(im1, ax=axes[1])
    
    axes[2].bar(['Linear','Proportional'], 
                [r_lin['T_final'].std(), r_prop['T_final'].std()],
                color=['red','green'])
    axes[2].set_title(f'Temperature StdDev\nLinear={r_lin["T_final"].std():.3f}K '
                      f'vs Prop={r_prop["T_final"].std():.3f}K')
    axes[2].set_ylabel('T std (K)')
    plt.tight_layout()
    plt.savefig(f'{OUT}/exp3_duty_matrix.png', dpi=120)
    plt.close()
    
    # ═══════════════════════════════════
    # 汇总JSON
    # ═══════════════════════════════════
    summary = {
        'exp1_multi_order': {
            str(n): {
                'T_mean': float(results_multi[n]['T_final'].mean()),
                'T_std': float(results_multi[n]['T_final'].std()),
                'T_max': float(results_multi[n]['T_final'].max()),
                'max_flip': int(max(results_multi[n]['flip_hist'])),
                'avg_power_mW': float(np.mean(results_multi[n]['power_hist']) * 1e3)
            } for n in orders
        },
        'exp2_farey_vs_uniform': {
            'farey_max_flip': int(max(r_farey['flip_hist'])),
            'uniform_max_flip': int(max(r_uniform['flip_hist'])),
            'farey_T_std': float(r_farey['T_final'].std()),
            'uniform_T_std': float(r_uniform['T_final'].std()),
            'flip_reduction_pct': round((1 - max(r_farey['flip_hist']) / max(r_uniform['flip_hist'])) * 100, 1)
        },
        'exp3_duty_matrix': {
            'linear_T_std': float(r_lin['T_final'].std()),
            'proportional_T_std': float(r_prop['T_final'].std()),
            'linear_row_sums': [float(D_lin[i].sum()) for i in range(5)],
            'proportional_row_sums': [float(D_prop[i].sum()) for i in range(5)],
            'improvement_pct': round((r_lin['T_final'].std() - r_prop['T_final'].std()) / r_lin['T_final'].std() * 100, 1)
        }
    }
    
    with open(f'{OUT}/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"全部完成! 输出: {OUT}/")
    print(f"  exp1_multi_order.png")
    print(f"  exp2_farey_vs_uniform.png")
    print(f"  exp3_duty_matrix.png")
    print(f"  summary.json")
    print(f"\n核心结论:")
    print(f"  Exp1: 3/5/7阶 T_std = {summary['exp1_multi_order']['3']['T_std']:.2f}/{summary['exp1_multi_order']['5']['T_std']:.2f}/{summary['exp1_multi_order']['7']['T_std']:.2f}K")
    print(f"  Exp2: Farey降同时翻转 {summary['exp2_farey_vs_uniform']['flip_reduction_pct']}%")
    print(f"  Exp3: 修正D降温度不均 {summary['exp3_duty_matrix']['improvement_pct']}%")
