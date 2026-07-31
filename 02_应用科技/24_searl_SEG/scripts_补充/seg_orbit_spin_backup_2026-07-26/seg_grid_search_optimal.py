# -*- coding: utf-8 -*-
"""
SEG 磁齿轮网格搜索 — 最优磁极充磁数量设定
============================================
搜索空间: N_stator × P_roller × (N_outer, N_mid, N_inner)
指标: gcd/lcm + 磁齿轮耦合条件

核心物理（磁齿轮理论）：
- 每对相邻环之间的平滑度取决于 gcd(有效极对数)
- 扭矩传递效率取决于磁齿轮耦合条件
- 滚筒数 × 每滚筒极对数 = 该环有效极对数
"""

import numpy as np
from math import gcd, lcm
from itertools import product
import json, os

# ============================================================
# 搜索空间
# ============================================================

# 定子磁极对数候选 (来自Searl真值表 + Jellium推荐)
# 每个值 = 总磁极数/2 (N-S对)
STATOR_PAIRS_CANDIDATES = [
    # Searl真值表核心值（总极数/2）
    2205//2,    # 1102  (IGV型, 总2205)
    3990//2,    # 1995  (SEG标准)
    4410//2,    # 2205  (SEG标准)
    5040//2,    # 2520  (Jellium 5040推荐)
    5250//2,    # 2625
    # Jellium性价比规格
    1680//2,    # 840   (规格A, ANU共振)
    2520//2,    # 1260  (规格A变体)
    57960//32,  # 1811  (规格C, 实际要缩小模拟)
    115920//64, # 1811  (规格D, 缩小)
    # 更多幻方共振值
    2835//2,    # 1417
    4290//2,    # 2145
    4830//2,    # 2415
    4950//2,    # 2475
    # 素数基数
    30//2,      # 15
    105//2,     # 52
    210//2,     # 105
    1050//2,    # 525
]

# 每滚筒的磁极对数候选 (默认34极=17对)
ROLLER_PAIR_CANDIDATES = [16, 17, 18, 20, 22, 24, 25, 28, 30, 32, 34]
# 注: 17对=34极(标准), 其他是探索值

# 三环滚筒数候选
OUTER_ROLLERS = [32, 34, 30, 36, 38]
MID_ROLLERS = [21, 22, 23, 24, 25]
INNER_ROLLERS = [12, 13, 14, 15]


# ============================================================
# 磁齿轮指标计算
# ============================================================

def magnetic_gear_metrics(p_stator, p_roller, n_rollers, ring_name=""):
    """计算单环的磁齿轮平滑度指标
    
    p_stator: 定子极对数
    p_roller: 每滚筒极对数
    n_rollers: 滚筒数量
    """
    # 滚筒总有效极对数 = 滚筒数 × 每滚筒极对数
    p_ring_total = n_rollers * p_roller
    
    g = gcd(p_stator, p_roller)       # 单滚筒-定子gcd
    L_single = lcm(p_stator, p_roller) # 单滚筒-定子lcm
    
    g_ring = gcd(p_stator, p_ring_total)
    L_ring = lcm(p_stator, p_ring_total)
    
    # 磁齿轮耦合条件: |p_stator ± kN_rollers| 应该接近某个有效值
    # 对于k=1: p_inner = |p_stator - n_rollers| (如果>0)
    coupling_inner = abs(p_stator - n_rollers)
    
    # 平滑度评分
    # 1. gcd小 = 好 (磁静音)
    gcd_score = 1.0 / (g + 1)
    gcd_ring_score = 1.0 / (g_ring + 1)
    
    # 2. lcm大 = 好 (长寿命/均匀退磁)
    lcm_score = L_single / max(p_stator * p_roller, 1)
    lcm_ring_score = L_ring / max(p_stator * p_ring_total, 1)
    
    # 3. 谐波丰富度 = lcm(p_stator, p_roller) / gcd(p_stator, p_roller) 越大越好
    harmonic_richness = L_single / max(g, 1)
    harmonic_richness_ring = L_ring / max(g_ring, 1)
    
    # 4. 相位多样性 = n_rollers / gcd(n_rollers, p_stator) 
    #    衡量多少滚筒处于不同相位
    phase_diversity = n_rollers / max(gcd(n_rollers, p_stator), 1)
    
    # 5. Jellium兼容性：p_ring_total应该接近Jellium幻数
    jellium = [2, 8, 18, 20, 28, 34, 40, 58, 90, 92, 112, 126, 138, 184, 322]
    jellium_score = 0
    for j in jellium:
        # p_ring_total接近Jellium幻数的倍数
        if p_ring_total > 0 and j > 0:
            ratio = p_ring_total / j
            if abs(ratio - round(ratio)) < 0.1:
                jellium_score += 1.0 / (abs(ratio - round(ratio)) + 0.01)
    
    return {
        'p_stator': p_stator,
        'p_roller': p_roller,
        'n_rollers': n_rollers,
        'p_ring_total': p_ring_total,
        'ring': ring_name,
        'gcd_single': g,
        'gcd_ring': g_ring,
        'lcm_single': L_single,
        'lcm_ring': L_ring,
        'harmonic_richness': harmonic_richness,
        'harmonic_richness_ring': harmonic_richness_ring,
        'phase_diversity': phase_diversity,
        'coupling_inner': coupling_inner,
        'jellium_score': round(jellium_score, 2),
    }


def three_ring_score(m_outer, m_mid, m_inner):
    """三环综合评分"""
    
    # 单环评分
    outer_score = (
        0.3 * m_outer['gcd_ring'] + 
        0.2 * (1.0 / max(m_outer['lcm_ring'] / (m_outer['p_stator'] * m_outer['p_ring_total'] + 1), 0.01)) +
        0.2 * (1.0 / max(m_outer['harmonic_richness_ring'] / 10000, 0.01)) +
        0.3 * (1.0 / m_outer['phase_diversity'] if m_outer['phase_diversity'] > 0 else 1)
    )
    # 注：这里用倒数让所有指标都"越小越好"
    
    # 跨环耦合指标
    # 外环和中环之间的gcd
    g_om = gcd(m_outer['p_ring_total'], m_mid['p_ring_total'])
    L_om = lcm(m_outer['p_ring_total'], m_mid['p_ring_total'])
    
    # 中环和内环之间的gcd
    g_mi = gcd(m_mid['p_ring_total'], m_inner['p_ring_total'])
    L_mi = lcm(m_mid['p_ring_total'], m_inner['p_ring_total'])
    
    # 跨环平滑度（gcd小=好）
    cross_smoothness = 1.0 / (g_om + 1) + 1.0 / (g_mi + 1)
    
    # 磁齿轮级联条件：每一级的"内转子"应该匹配下一级的"外定子"
    # 对于外环→中环: m_outer.coupling_inner 应该接近 m_mid.p_ring_total
    coupling_om = abs(m_outer['coupling_inner'] * m_outer['p_roller'] - m_mid['p_ring_total'])
    coupling_mi = abs(m_mid['coupling_inner'] * m_mid['p_roller'] - m_inner['p_ring_total'])
    coupling_score = 1.0 / (coupling_om + 1) + 1.0 / (coupling_mi + 1)
    
    # 三环总lcm（越大越好）
    L_total = lcm(lcm(m_outer['p_ring_total'], m_mid['p_ring_total']), m_inner['p_ring_total'])
    
    # 综合评分（越高越好）
    total_score = (
        0.25 * (1.0 / (m_outer['gcd_ring'] + 1)) +      # 外环gcd小
        0.15 * (1.0 / (m_mid['gcd_ring'] + 1)) +         # 中环
        0.10 * (1.0 / (m_inner['gcd_ring'] + 1)) +       # 内环
        0.15 * cross_smoothness +                         # 跨环平滑
        0.10 * coupling_score +                           # 磁齿轮耦合
        0.10 * np.log10(L_total + 1) / 10 +              # 总lcm
        0.15 * (m_outer['jellium_score'] + m_mid['jellium_score'] + m_inner['jellium_score']) / 30
    )
    
    return {
        'total_score': round(total_score, 6),
        'cross_gcd_om': g_om,
        'cross_gcd_mi': g_mi,
        'cross_lcm_om': L_om,
        'cross_lcm_mi': L_mi,
        'coupling_om': coupling_om,
        'coupling_mi': coupling_mi,
        'L_total': L_total,
    }


def grid_search():
    """全网格搜索"""
    
    results = []
    total = len(STATOR_PAIRS_CANDIDATES) * len(ROLLER_PAIR_CANDIDATES) * \
            len(OUTER_ROLLERS) * len(MID_ROLLERS) * len(INNER_ROLLERS)
    
    count = 0
    print(f"搜索空间: {total:,} 组合")
    
    # 固定p_roller（先扫34极=17对的标准配置，再扩展）
    for N_s in STATOR_PAIRS_CANDIDATES:
        for P_r in ROLLER_PAIR_CANDIDATES:
            # 外环指标
            outer_metrics = {}
            for N_o in OUTER_ROLLERS:
                outer_metrics[N_o] = magnetic_gear_metrics(N_s, P_r, N_o, "outer")
            
            # 中环指标 (以各外环滚筒数的有效极对数为"定子")
            mid_metrics = {}
            for N_o in OUTER_ROLLERS:
                mid_metrics[N_o] = {}
                for N_m in MID_ROLLERS:
                    # 中环的"定子" = 外环滚筒的总有效极对数
                    p_outer_total = N_o * P_r
                    mid_metrics[N_o][N_m] = magnetic_gear_metrics(
                        p_outer_total, P_r, N_m, "mid"
                    )
            
            # 内环指标
            inner_metrics = {}
            for N_m in MID_ROLLERS:
                inner_metrics[N_m] = {}
                for N_i in INNER_ROLLERS:
                    # 内环的"定子" = 中环滚筒的总有效极对数
                    p_mid_total = N_m * P_r
                    inner_metrics[N_m][N_i] = magnetic_gear_metrics(
                        p_mid_total, P_r, N_i, "inner"
                    )
            
            # 三环组合评分
            for N_o in OUTER_ROLLERS:
                for N_m in MID_ROLLERS:
                    for N_i in INNER_ROLLERS:
                        m_o = outer_metrics[N_o]
                        m_m = mid_metrics[N_o][N_m]
                        m_i = inner_metrics[N_m][N_i]
                        combo = three_ring_score(m_o, m_m, m_i)
                        
                        results.append({
                            'N_stator_pairs': N_s,
                            'N_stator_poles': N_s * 2,
                            'P_roller_pairs': P_r,
                            'P_roller_poles': P_r * 2,
                            'N_outer': N_o, 'N_mid': N_m, 'N_inner': N_i,
                            'roller_ratio': f"{N_o}/{N_m}/{N_i}",
                            'outer': m_o, 'mid': m_m, 'inner': m_i,
                            'combo': combo,
                        })
                        
                        count += 1
                        if count % 5000 == 0:
                            print(f"  进度: {count}/{total} ({100*count/total:.1f}%)")
    
    print(f"  完成: {count} 组合")
    return results


def find_optimal(results, top_n=30):
    """找最优配置"""
    
    # 按总分排序
    sorted_by_score = sorted(results, key=lambda x: x['combo']['total_score'], reverse=True)
    
    # 按不同准则筛选
    # 准则A: 外环gcd=1 + 高lcm
    gcd1_high_lcm = sorted(
        [r for r in results if r['outer']['gcd_single'] == 1],
        key=lambda x: x['combo']['L_total'], reverse=True
    )
    
    # 准则B: 三环全互质
    all_coprime = sorted(
        [r for r in results if r['combo']['cross_gcd_om'] == 1 and r['combo']['cross_gcd_mi'] == 1],
        key=lambda x: x['combo']['total_score'], reverse=True
    )
    
    # 准则C: Jellium最优
    best_jellium = sorted(
        results, key=lambda x: (
            x['outer']['jellium_score'] + x['mid']['jellium_score'] + x['inner']['jellium_score']
        ), reverse=True
    )
    
    return {
        'top_overall': sorted_by_score[:top_n],
        'gcd1_high_lcm': gcd1_high_lcm[:top_n],
        'all_coprime': all_coprime[:top_n],
        'best_jellium': best_jellium[:top_n],
        'all_results': results,
    }


def print_top(results_dict, label, top_n=10):
    """打印Top N结果"""
    print(f"\n{'='*90}")
    print(f"  {label}")
    print(f"{'='*90}")
    print(f"{'排名':<5} {'定子极数':>8} {'滚筒极数':>8} {'外/中/内':>12} "
          f"{'外gcd':>6} {'中gcd':>6} {'内gcd':>6} "
          f"{'跨gcd':>8} {'总lcm':>10} {'总分':>8}")
    print("-" * 90)
    
    for i, r in enumerate(results_dict[:top_n]):
        print(f"{i+1:<5} {r['N_stator_poles']:>8} {r['P_roller_poles']:>8} "
              f"{r['roller_ratio']:>12} "
              f"{r['outer']['gcd_single']:>6} {r['mid']['gcd_single']:>6} {r['inner']['gcd_single']:>6} "
              f"{r['combo']['cross_gcd_om']}/{r['combo']['cross_gcd_mi']:>5} "
              f"{r['combo']['L_total']:>10,} "
              f"{r['combo']['total_score']:>8.4f}")


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("SEG 磁齿轮网格搜索 — 最优磁极充磁数量设定")
    print("=" * 90)
    
    results = grid_search()
    optimal = find_optimal(results)
    
    # 打印各准则Top
    print_top(optimal['top_overall'], "【准则A】综合评分 Top 20")
    print_top(optimal['gcd1_high_lcm'], "【准则B】外环gcd=1 + 高LCM Top 10")
    print_top(optimal['all_coprime'], "【准则C】三环全互质 Top 10")
    print_top(optimal['best_jellium'], "【准则D】Jellium幻数对齐 Top 10")
    
    # 统计
    print(f"\n{'='*90}")
    print("统计摘要")
    print(f"{'='*90}")
    print(f"总组合数: {len(results):,}")
    print(f"外环gcd=1: {sum(1 for r in results if r['outer']['gcd_single']==1):,} "
          f"({100*sum(1 for r in results if r['outer']['gcd_single']==1)/len(results):.1f}%)")
    print(f"三环全互质: {sum(1 for r in results if r['combo']['cross_gcd_om']==1 and r['combo']['cross_gcd_mi']==1):,}")
    
    # 找原始Searl配置在排名中的位置
    searl_orig = [r for r in results if 
                  r['N_stator_poles'] == 4410 and r['P_roller_poles'] == 34 and
                  r['N_outer'] == 32 and r['N_mid'] == 22 and r['N_inner'] == 12]
    if searl_orig:
        rank = sum(1 for r in results if r['combo']['total_score'] > searl_orig[0]['combo']['total_score']) + 1
        print(f"\n原版Searl配置 (4410/34极, 32/22/12) 排名: {rank}/{len(results)} "
              f"(前 {100*rank/len(results):.2f}%)")
    
    # 保存JSON
    json_path = os.path.join(out_dir, 'seg_grid_search_results.json')
    # 只保存Top 500以控制文件大小
    save_data = {
        'summary': {
            'total_combinations': len(results),
            'search_space': {
                'stator_pairs': STATOR_PAIRS_CANDIDATES,
                'roller_pairs': ROLLER_PAIR_CANDIDATES,
                'outer_rollers': OUTER_ROLLERS,
                'mid_rollers': MID_ROLLERS,
                'inner_rollers': INNER_ROLLERS,
            },
        },
        'top20_overall': optimal['top_overall'][:20],
        'top20_gcd1': optimal['gcd1_high_lcm'][:20],
        'top20_coprime': optimal['all_coprime'][:20],
        'top20_jellium': optimal['best_jellium'][:20],
    }
    
    # 清理JSON（移除numpy类型）
    def clean_for_json(obj):
        if isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(v) for v in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        return obj
    
    save_data = clean_for_json(save_data)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 结果保存: {json_path}")
    print(f"✓ 完成!")
    
    return optimal


if __name__ == '__main__':
    main()
