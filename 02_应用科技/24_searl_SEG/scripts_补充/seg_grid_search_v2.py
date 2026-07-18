# -*- coding: utf-8 -*-
"""
SEG 磁齿轮网格搜索 v2 — 扩展版
================================
修正:
1. 整数除法修复（幻方线和保留原值）
2. 允许三环使用不同的每滚筒磁极数（跨环互质的关键！）
3. 更强调 gcd=1 的物理约束
"""
import numpy as np
from math import gcd, lcm
from itertools import product
import json, os

# ============================================================
# 搜索空间（扩大）
# ============================================================

# 定子总磁极数（必须是偶数）
STATOR_POLES = [
    # Searl真值表（偶数化）
    2204, 2206,     # 2205附近
    3990,            # SEG标准
    4410,            # SEG标准
    5040,            # Jellium推荐
    5250,            # 
    2834, 2836,     # 2835附近
    4290, 4830, 4950,
    # 素数+Jellium组合
    2520, 1680, 1050, 210, 30, 60,
    # 4410的倍数/约数
    4410, 2205*2,   # 4410
    5040,            # Jellium
    10080,           # 5040×2
    57960//32 * 2,  # 约3622
    # 扩展
    7350,  # 4410*5/3
    8820,  # 4410*2
    1260, 5880,
]

# 每滚筒磁极对数（不同环可不同）
ROLLER_PAIRS = [14, 15, 16, 17, 18, 19, 20, 22, 24, 25, 28, 30, 32, 34, 36, 40]

# 三环滚筒数（全组合）
ROLLER_COUNTS = {
    'outer': [30, 32, 34, 36, 38, 40],
    'mid':   [20, 21, 22, 23, 24, 25, 26],
    'inner': [11, 12, 13, 14, 15, 16, 17],
}


def magnetic_gear_quality(p_stator, p_roller, n_rollers):
    """磁齿轮质量指标（越低越好，0=完美）
    
    p_stator: 定子极对数
    p_roller: 每滚筒极对数
    n_rollers: 滚筒数
    """
    p_ring = n_rollers * p_roller
    
    g = gcd(p_stator, p_roller)
    l = lcm(p_stator, p_roller)
    
    # gcd惩罚：gcd=1最好
    gcd_penalty = g - 1
    
    # lcm奖励（归一化）
    lcm_reward = max(0, 1 - p_stator * p_roller / max(l, 1))
    
    # 磁齿轮耦合：|p_stator - n_rollers| 越接近下一级越好
    coupling = abs(p_stator - n_rollers)
    
    # 谐波分散度 = lcm/gcd 越大越好
    harmonic = l / max(g, 1)
    
    return {
        'gcd': g,
        'lcm': l,
        'gcd_penalty': gcd_penalty,
        'lcm_reward': lcm_reward,
        'p_ring_total': p_ring,
        'coupling_value': coupling,
        'harmonic_dispersion': harmonic,
        'phase_diversity': n_rollers / max(gcd(n_rollers, p_stator), 1),
    }


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("SEG 磁齿轮网格搜索 v2 — 多环独立磁极数优化")
    print("=" * 90)
    
    # 统计
    n_stator = len(STATOR_POLES)
    n_pairs = len(ROLLER_PAIRS)
    n_outer = len(ROLLER_COUNTS['outer'])
    n_mid = len(ROLLER_COUNTS['mid'])
    n_inner = len(ROLLER_COUNTS['inner'])
    
    # 简化：先固定每滚筒磁极数相同，重点优化滚筒数
    print(f"\n【阶段1】固定P_roller=17对(34极)，优化三环滚筒数和定子极数")
    print(f"  定子候选: {n_stator}, 外环: {n_outer}, 中环: {n_mid}, 内环: {n_inner}")
    print(f"  总组合: {n_stator * n_outer * n_mid * n_inner:,}")
    
    P_roller_pairs = 17  # 标准34极=17对
    P_roller = P_roller_pairs * 2
    
    results_stage1 = []
    for N_s in STATOR_POLES:
        p_s = N_s // 2  # 定子极对数
        
        for N_o in ROLLER_COUNTS['outer']:
            q_o = magnetic_gear_quality(p_s, P_roller_pairs, N_o)
            
            for N_m in ROLLER_COUNTS['mid']:
                # 中环"定子" = 外环滚筒总极对数
                p_mid_stator = N_o * P_roller_pairs
                q_m = magnetic_gear_quality(p_mid_stator, P_roller_pairs, N_m)
                
                for N_i in ROLLER_COUNTS['inner']:
                    p_inner_stator = N_m * P_roller_pairs
                    q_i = magnetic_gear_quality(p_inner_stator, P_roller_pairs, N_i)
                    
                    # 评分：gcd=1最重要，其次是lcm和相位多样性
                    score = (
                        (1.0 if q_o['gcd'] == 1 else 0.5 / q_o['gcd']) * 40 +
                        (1.0 if q_m['gcd'] == 1 else 0.5 / q_m['gcd']) * 25 +
                        (1.0 if q_i['gcd'] == 1 else 0.5 / q_i['gcd']) * 15 +
                        np.log10(q_o['lcm'] + 1) * 5 +
                        np.log10(q_m['lcm'] + 1) * 3 +
                        np.log10(q_i['lcm'] + 1) * 2 +
                        q_o['phase_diversity'] * 5 +
                        q_m['phase_diversity'] * 3 +
                        q_i['phase_diversity'] * 2
                    )
                    
                    results_stage1.append({
                        'N_stator': N_s,
                        'P_roller': P_roller,
                        'N_outer': N_o, 'N_mid': N_m, 'N_inner': N_i,
                        'ratio': f"{N_o}/{N_m}/{N_i}",
                        'outer_gcd': q_o['gcd'],
                        'mid_gcd': q_m['gcd'],
                        'inner_gcd': q_i['gcd'],
                        'outer_phase': q_o['phase_diversity'],
                        'mid_phase': q_m['phase_diversity'],
                        'inner_phase': q_i['phase_diversity'],
                        'outer_lcm': q_o['lcm'],
                        'mid_lcm': q_m['lcm'],
                        'inner_lcm': q_i['lcm'],
                        'cross_gcd_om': gcd(N_o * P_roller_pairs, N_m * P_roller_pairs),
                        'cross_gcd_mi': gcd(N_m * P_roller_pairs, N_i * P_roller_pairs),
                        'score': round(score, 2),
                    })
    
    # 排序
    results_stage1.sort(key=lambda x: x['score'], reverse=True)
    
    # 打印Top 30
    print(f"\n{'排名':<5} {'定子':>6} {'P滚筒':>6} {'外/中/内':>12} "
          f"{'外gcd':>6} {'中gcd':>6} {'内gcd':>6} "
          f"{'外相位':>8} {'中相位':>8} {'内相位':>8} "
          f"{'外lcm':>8} {'评分':>8}")
    print("-" * 105)
    
    for i, r in enumerate(results_stage1[:30]):
        print(f"{i+1:<5} {r['N_stator']:>6} {r['P_roller']:>6} "
              f"{r['ratio']:>12} "
              f"{r['outer_gcd']:>6} {r['mid_gcd']:>6} {r['inner_gcd']:>6} "
              f"{r['outer_phase']:>8.1f} {r['mid_phase']:>8.1f} {r['inner_phase']:>8.1f} "
              f"{r['outer_lcm']:>8,} {r['score']:>8.1f}")
    
    # 找原版Searl的排名
    searl = [r for r in results_stage1 if 
             r['N_stator'] == 4410 and r['N_outer'] == 32 and 
             r['N_mid'] == 22 and r['N_inner'] == 12]
    if searl:
        rank = sum(1 for r in results_stage1 if r['score'] > searl[0]['score']) + 1
        print(f"\n原版Searl (4410/34极, 32/22/12): 排名 {rank}/{len(results_stage1)} "
              f"({100*rank/len(results_stage1):.1f}%), 评分={searl[0]['score']:.1f}")
    
    # Fibonacci配置的排名
    fib = [r for r in results_stage1 if 
           r['N_stator'] == 4410 and r['N_outer'] == 34 and 
           r['N_mid'] == 21 and r['N_inner'] == 13]
    if fib:
        rank_fib = sum(1 for r in results_stage1 if r['score'] > fib[0]['score']) + 1
        print(f"Fibonacci (4410/34极, 34/21/13): 排名 {rank_fib}/{len(results_stage1)} "
              f"({100*rank_fib/len(results_stage1):.1f}%), 评分={fib[0]['score']:.1f}")
    
    # ============================================================
    # 阶段2：允许不同P_roller，寻找三环全互质配置
    # ============================================================
    print(f"\n\n【阶段2】允许三环使用不同的每滚筒磁极数")
    
    # 精简搜索（否则太多组合）
    best_stators = [4410, 5040, 3990, 5250, 2836, 4290]
    best_pairs = [16, 17, 18, 19, 20, 22, 24, 25, 28, 30, 32]
    
    total_combos = len(best_stators) * len(best_pairs)**3 * n_outer * n_mid * n_inner
    print(f"  定子: {len(best_stators)}, P每环: {len(best_pairs)}³, 滚筒: {n_outer}×{n_mid}×{n_inner}")
    print(f"  总组合: {total_combos:,} (较大，用智能筛选)")
    
    # 智能筛选：只保留外环gcd=1的组合
    results_stage2 = []
    count = 0
    
    for N_s in best_stators:
        p_s = N_s // 2
        for P_o in best_pairs:
            q_o_test = magnetic_gear_quality(p_s, P_o, ROLLER_COUNTS['outer'][0])
            if q_o_test['gcd'] != 1:
                continue  # 外环gcd≠1直接跳过
            
            for N_o in ROLLER_COUNTS['outer']:
                q_o = magnetic_gear_quality(p_s, P_o, N_o)
                if q_o['gcd'] != 1:
                    continue
                
                p_mid_stator = N_o * P_o
                for P_m in best_pairs:
                    for N_m in ROLLER_COUNTS['mid']:
                        q_m = magnetic_gear_quality(p_mid_stator, P_m, N_m)
                        
                        # 检查跨环gcd
                        cross_om = gcd(N_o * P_o, N_m * P_m)
                        
                        p_inner_stator = N_m * P_m
                        for P_i in best_pairs:
                            for N_i in ROLLER_COUNTS['inner']:
                                q_i = magnetic_gear_quality(p_inner_stator, P_i, N_i)
                                cross_mi = gcd(N_m * P_m, N_i * P_i)
                                
                                # 评分（强调互质性）
                                all_gcd1 = (q_o['gcd'] == 1 and q_m['gcd'] == 1 and q_i['gcd'] == 1)
                                
                                score = (
                                    (100 if q_o['gcd'] == 1 else 0) +
                                    (50 if q_m['gcd'] == 1 else 0) +
                                    (50 if q_i['gcd'] == 1 else 0) +
                                    (100 if cross_om == 1 else 0) +
                                    (100 if cross_mi == 1 else 0) +
                                    np.log10(q_o['lcm'] + 1) * 2 +
                                    np.log10(q_m['lcm'] + 1) * 2 +
                                    np.log10(q_i['lcm'] + 1) * 2 +
                                    q_o['phase_diversity'] * 3
                                )
                                
                                results_stage2.append({
                                    'N_stator': N_s,
                                    'P_outer': P_o * 2, 'P_mid': P_m * 2, 'P_inner': P_i * 2,
                                    'N_outer': N_o, 'N_mid': N_m, 'N_inner': N_i,
                                    'ratio': f"{N_o}/{N_m}/{N_i}",
                                    'pole_ratio': f"{P_o*2}/{P_m*2}/{P_i*2}",
                                    'outer_gcd': q_o['gcd'],
                                    'mid_gcd': q_m['gcd'],
                                    'inner_gcd': q_i['gcd'],
                                    'cross_gcd_om': cross_om,
                                    'cross_gcd_mi': cross_mi,
                                    'all_gcd1': all_gcd1,
                                    'outer_phase': q_o['phase_diversity'],
                                    'outer_lcm': q_o['lcm'],
                                    'score': round(score, 2),
                                })
                                count += 1
                                if count % 10000 == 0:
                                    print(f"    进度: {count:,}...")
    
    results_stage2.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n  有效组合: {len(results_stage2):,}")
    print(f"\n{'排名':<5} {'定子':>6} {'P(外/中/内)':>14} {'滚筒比':>10} "
          f"{'外gcd':>6} {'中gcd':>6} {'内gcd':>6} {'跨om':>6} {'跨mi':>6} {'全1':>5} {'评分':>8}")
    print("-" * 105)
    
    for i, r in enumerate(results_stage2[:20]):
        all1 = 'YES' if r['all_gcd1'] else ''
        print(f"{i+1:<5} {r['N_stator']:>6} {r['pole_ratio']:>14} "
              f"{r['ratio']:>10} "
              f"{r['outer_gcd']:>6} {r['mid_gcd']:>6} {r['inner_gcd']:>6} "
              f"{r['cross_gcd_om']:>6} {r['cross_gcd_mi']:>6} {all1:>5} {r['score']:>8.1f}")
    
    # 统计
    n_all_gcd1 = sum(1 for r in results_stage2 if r['all_gcd1'])
    print(f"\n  三环全互质组合: {n_all_gcd1} ({100*n_all_gcd1/len(results_stage2):.1f}%)")
    
    # 打印Top全互质配置
    all_gcd1_results = [r for r in results_stage2 if r['all_gcd1']]
    if all_gcd1_results:
        print(f"\n  【★ 三环全互质 Top 10 ★】")
        for i, r in enumerate(all_gcd1_results[:10]):
            print(f"  {i+1}. 定子{r['N_stator']}极, 滚筒{r['pole_ratio']}极, "
                  f"{r['ratio']}, 外lcm={r['outer_lcm']:,}")
    
    # 保存结果
    save_data = {
        'stage1_top30': results_stage1[:30],
        'stage2_top20': results_stage2[:20],
        'stage2_all_gcd1_top20': all_gcd1_results[:20] if all_gcd1_results else [],
        'searl_original': searl[0] if searl else None,
        'fibonacci': fib[0] if fib else None,
    }
    
    json_path = os.path.join(out_dir, 'seg_grid_search_v2_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 结果保存: {json_path}")
    print("✓ 完成!")
    
    return results_stage1, results_stage2


if __name__ == '__main__':
    main()
