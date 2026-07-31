#!/usr/bin/env python3
"""
SEG 磁齿轮 GPU 扭矩验证
========================
用 CuPy 建模真实多极滚筒磁体（每滚筒 N 个径向磁极），
计算单滚筒轨道的扭矩波形，对比不同配置的平滑度。

验证对象：网格搜索 Top 3 候选 + 原版Searl + Fibonacci
"""
import numpy as np
import time, sys, json

# 检测 CuPy
try:
    import cupy as cp
    GPU = True
    print(f"[GPU] CuPy {cp.__version__}, GPU: {cp.cuda.runtime.getDeviceCount()} devices")
except ImportError:
    cp = np  # 回退CPU
    GPU = False
    print("[CPU] CuPy不可用，回退NumPy")

MU0_4PI = 1e-7

def build_stator_gpu(N_poles, R=1.0):
    """定子：N_poles个径向交替磁极"""
    angles = 2 * np.pi * np.arange(N_poles, dtype=np.float64) / N_poles
    pos_x = R * np.cos(angles)
    pos_y = R * np.sin(angles)
    pos = np.stack([pos_x, pos_y, np.zeros(N_poles)], axis=1)
    
    polarity = np.where(np.arange(N_poles) % 2 == 0, 1.0, -1.0)
    mom_x = polarity * np.cos(angles)
    mom_y = polarity * np.sin(angles)
    mom = np.stack([mom_x, mom_y, np.zeros(N_poles)], axis=1)
    
    return pos, mom


def build_roller_poles_gpu(P_poles, roller_center, roller_radius=0.03, 
                            orbit_angle=0.0, spin_angle=0.0,
                            asymmetry=0.0, random_seed=42):
    """滚筒：P_poles个径向磁极，可加非对称扰动（模拟DC+AC复合磁化）
    
    asymmetry: 非对称度 0~1, 0=完美对称, 1=最强不对称
    random_seed: 随机种子（可复现）
    """
    rng = np.random.RandomState(random_seed + int(orbit_angle * 100))
    
    # 滚筒上每个磁极的基准角度
    base_angles = spin_angle + 2 * np.pi * np.arange(P_poles, dtype=np.float64) / P_poles
    
    # 非对称扰动：随机偏移磁极角度和强度
    if asymmetry > 0:
        angle_noise = asymmetry * 0.3 * rng.randn(P_poles)  # 角度抖动
        pole_angles = base_angles + angle_noise
    else:
        pole_angles = base_angles
    
    # 磁极位置（滚筒表面）
    cx, cy = roller_center[0], roller_center[1]
    px = cx + roller_radius * np.cos(pole_angles)
    py = cy + roller_radius * np.sin(pole_angles)
    pz = np.zeros(P_poles)
    pos = np.stack([px, py, pz], axis=1)
    
    # 磁极方向：径向
    polarity = np.where(np.arange(P_poles) % 2 == 0, 1.0, -1.0).astype(np.float64)
    
    # 非对称扰动：随机改变磁极强度（模拟非均匀磁畴）
    if asymmetry > 0:
        strength_noise = 1.0 + asymmetry * 0.5 * rng.randn(P_poles)
        polarity *= strength_noise
    
    dx = np.cos(pole_angles)
    dy = np.sin(pole_angles)
    mom = np.stack([polarity * dx, polarity * dy, np.zeros(P_poles)], axis=1)
    
    return pos, mom


def dipole_force_batch_gpu(stator_pos, stator_mom, target_pos, target_mom):
    """批量计算：所有定子磁极对所有滚筒磁极的力（GPU并行）
    
    stator_pos: [N_s, 3]
    stator_mom: [N_s, 3]
    target_pos: [N_t, 3]
    target_mom: [N_t, 3]
    
    返回: [N_t, 3] 每个目标磁极受的总力
    """
    N_s = stator_pos.shape[0]
    N_t = target_pos.shape[0]
    
    # 向量化：r_vec[i,j] = target_pos[i] - stator_pos[j]
    # 用广播
    r_vec = target_pos[:, np.newaxis, :] - stator_pos[np.newaxis, :, :]  # [N_t, N_s, 3]
    
    r = np.sqrt(np.sum(r_vec**2, axis=2))  # [N_t, N_s]
    r = np.maximum(r, 1e-10)
    r_hat = r_vec / r[:, :, np.newaxis]  # [N_t, N_s, 3]
    
    # m1 = stator, m2 = target
    m1r = np.sum(stator_mom[np.newaxis, :, :] * r_hat, axis=2)  # [N_t, N_s]
    m2r = np.sum(target_mom[:, np.newaxis, :] * r_hat, axis=2)  # [N_t, N_s]
    m12 = np.sum(target_mom[:, np.newaxis, :] * stator_mom[np.newaxis, :, :], axis=2)  # [N_t, N_s]
    
    coeff = 3 * MU0_4PI / r**4  # [N_t, N_s]
    
    # F = coeff * (m1r*m2 + m2r*m1 + m12*r_hat - 5*m1r*m2r*r_hat)
    term1 = m1r[:, :, np.newaxis] * target_mom[:, np.newaxis, :]  # [N_t, N_s, 3]
    term2 = m2r[:, :, np.newaxis] * stator_mom[np.newaxis, :, :]
    term3 = m12[:, :, np.newaxis] * r_hat
    term4 = 5 * m1r[:, :, np.newaxis] * m2r[:, :, np.newaxis] * r_hat
    
    F = coeff[:, :, np.newaxis] * (term1 + term2 + term3 - term4)  # [N_t, N_s, 3]
    F_total = np.sum(F, axis=1)  # [N_t, 3]
    
    return F_total


def compute_single_roller_torque_gpu(N_stator, P_roller, n_steps=360, 
                                      R_stator=1.0, R_orbit=0.65, 
                                      r_roller=0.03, asymmetry=0.0):
    """GPU加速：单滚筒完整轨道的扭矩曲线"""
    stator_pos, stator_mom = build_stator_gpu(N_stator, R_stator)
    
    angles = 2 * np.pi * np.arange(n_steps, dtype=np.float64) / n_steps
    torques = np.zeros(n_steps)
    
    for idx in range(n_steps):
        theta = angles[idx]
        roller_center = np.array([R_orbit * np.cos(theta), R_orbit * np.sin(theta), 0.0])
        
        # 滚筒磁极位置（可加非对称扰动）
        pole_pos, pole_mom = build_roller_poles_gpu(
            P_roller, roller_center, r_roller, orbit_angle=theta,
            asymmetry=asymmetry, random_seed=42
        )
        
        # GPU批量计算
        forces = dipole_force_batch_gpu(stator_pos, stator_mom, pole_pos, pole_mom)
        
        # 每个磁极的切向力（绕滚筒中心）
        total_tangential = 0.0
        for j in range(P_roller):
            r_rel = pole_pos[j] - roller_center
            r_hat = r_rel / (np.linalg.norm(r_rel) + 1e-10)
            tang = np.array([-r_hat[1], r_hat[0], 0.0])
            total_tangential += np.dot(forces[j], tang)
        
        torques[idx] = total_tangential
    
    return angles, torques


def smoothness_metrics(torque):
    """扭矩平滑度指标"""
    t = torque
    abs_t = np.abs(t)
    mean_abs = np.mean(abs_t)
    
    if mean_abs < 1e-15:
        return {'cv': 0, 'ripple_pct': 0, 'reversal_pct': 0, 'mean_abs': 0, 
                'cogging': 0, 'peak_to_peak': 0}
    
    cv = np.std(t) / mean_abs
    ripple = 100 * (np.max(t) - np.min(t)) / mean_abs
    reversal = 100 * np.sum(t[:-1] * t[1:] < 0) / len(t)
    
    # 齿槽转矩 (cogging)：扭矩过零时的斜率
    zero_cross = np.where(t[:-1] * t[1:] < 0)[0]
    if len(zero_cross) > 0:
        cogging = np.mean(np.abs(np.diff(t)[zero_cross]))
    else:
        cogging = 0
    
    return {
        'cv': float(cv), 'ripple_pct': float(ripple),
        'reversal_pct': float(reversal), 'mean_abs': float(mean_abs),
        'cogging': float(cogging),
        'peak_to_peak': float(np.max(t) - np.min(t)),
    }


def main():
    print("SEG GPU 扭矩验证")
    print("=" * 70)
    
    # 测试配置
    # (N_stator, P_roller, label)
    configs = [
        (4410, 34, "原版4410/34极"),
        (5040, 34, "Jellium5040/34极"),
        (5250, 64, "最优5250/64极"),
    ]
    
    # 测试不同非对称度
    asym_levels = [0.0, 0.1, 0.3, 0.5]
    
    all_results = []
    
    for asym in asym_levels:
        print(f"\n{'='*60}")
        print(f"非对称度 asymmetry = {asym}")
        print(f"{'='*60}")
        
        for N_stator, P_roller, label in configs:
            g = np.gcd(N_stator // 2, P_roller // 2)
            
            # GPU缩比
            p_s = N_stator // 2
            p_r = P_roller // 2
            scale = max(1, p_s // 120)
            N_eff = max(p_s // scale, 40) * 2
            P_eff = max(p_r // max(1, scale // 3), 4) * 2
            
            p_se = N_eff // 2
            p_re = P_eff // 2
            while np.gcd(p_se, p_re) != g:
                p_se += 1
            N_eff = p_se * 2
            
            t0 = time.time()
            angles, torque = compute_single_roller_torque_gpu(
                N_eff, P_eff, n_steps=180,
                R_stator=1.0, R_orbit=0.65, r_roller=0.04,
                asymmetry=asym
            )
            elapsed = time.time() - t0
            
            m = smoothness_metrics(torque)
            m['label'] = label
            m['asymmetry'] = asym
            m['N_stator'] = N_stator
            m['P_roller'] = P_roller
            m['gcd'] = g
            m['time'] = elapsed
            all_results.append(m)
            
            print(f"  {label:<20} CV={m['cv']:.4f} ripple={m['ripple_pct']:.1f}% "
                  f"cog={m['cogging']:.4f} pp={m['peak_to_peak']:.4f} "
                  f"mean_abs={m['mean_abs']:.6f} ({elapsed:.1f}s)")
    
    # 汇总
    print(f"\n{'='*70}")
    print("汇总：非对称度 vs 扭矩产生")
    print(f"{'='*70}")
    print(f"{'asym':<8} {'配置':<20} {'CV':<8} {'cogging':<12} {'mean_abs':<14} {'峰峰值':<12}")
    print("-" * 75)
    
    for r in sorted(all_results, key=lambda x: (x['asymmetry'], x['cogging'])):
        print(f"{r['asymmetry']:<8.1f} {r['label']:<20} {r['cv']:<8.4f} "
              f"{r['cogging']:<12.6f} {r['mean_abs']:<14.8f} {r['peak_to_peak']:<12.6f}")
    
    # 保存
    out_path = '/tmp/seg_gpu_results.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n结果保存: {out_path}")
    
    return results

if __name__ == '__main__':
    main()
