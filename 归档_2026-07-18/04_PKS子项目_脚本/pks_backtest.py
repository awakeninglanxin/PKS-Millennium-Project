#!/usr/bin/env python3
"""PKS 五参数回溯验证 v1.0
对 TOP10 股票和扩展池，回溯 2 年数据，验证 PKS 评级的预测力。
关键问题：
1. PKS-C 评级后的 30/60/90 日平均收益 vs PKS-X 评级？
2. h、γ、z₀、α、c 各自对未来的预测力？
3. 是否需要调整映射原理？
"""
import subprocess, json, sys, math
from datetime import datetime, timedelta
from collections import defaultdict

NODE = r"C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe"
WSK = r"C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js"

# TOP10 from today's report (PKS综合筛选_20260702_1410.md)
TOP10 = [
    ("sh688525", "佰维存储"), ("sz001309", "德明利"), ("sh688331", "荣昌生物"),
    ("sz002653", "海思科"), ("sz001270", "铖昌科技"), ("sh688336", "三生国健"),
    ("sz000987", "越秀资本"), ("sz300573", "兴齐眼药"), ("sh603259", "药明康德"),
    ("sz000792", "盐湖股份"),
]

# Extended pool: add major indices and more stocks
EXTRA = [
    ("sh600519", "贵州茅台"), ("sz000858", "五粮液"), ("sh601318", "中国平安"),
    ("sh600036", "招商银行"), ("sz300750", "宁德时代"), ("sz002594", "比亚迪"),
    ("sh688981", "中芯国际"), ("sh601012", "隆基绿能"), ("sh600900", "长江电力"),
]

ALL_STOCKS = TOP10 + EXTRA

def fetch_kline(code, limit=500):
    try:
        result = subprocess.run(
            [NODE, WSK, "kline", code, "--period", "day", "--limit", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0: return []
        lines = result.stdout.strip().split('\n')
        data = []
        for line in lines:
            if not line.startswith('| ') or line.startswith('| ---'): continue
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) < 7: continue
            try:
                data.append({
                    'date': parts[0], 'open': float(parts[1]),
                    'close': float(parts[2]), 'high': float(parts[3]),
                    'low': float(parts[4]), 'volume': float(parts[5])
                })
            except: continue
        return data
    except: return []

def compute_pks_params(window, baseline_type='ma60'):
    """在60日窗口上计算五参数"""
    closes = [d['close'] for d in window]
    highs = [d['high'] for d in window]
    lows = [d['low'] for d in window]
    
    if baseline_type == 'ma60':
        baseline = sum(closes) / len(closes)
    else:
        baseline = closes[-1]  # latest close
    
    if baseline <= 0: return None
    
    p_max = max(highs)
    p_min = min(lows)
    
    r_max = (p_max - baseline) / baseline if p_max > baseline else 0.001
    r_min = (baseline - p_min) / baseline if p_min < baseline else 0.001
    r1 = max(r_max, r_min)
    r2 = min(r_max, r_min)
    
    if r2 < 1e-8: r2 = 1e-8
    
    # 椭圆参数
    h = 2*r1*r2 / (r1 + r2)
    tan_g = (r1 - r2) / (r1 + r2)
    gamma = math.degrees(math.atan(tan_g))
    
    # 蛋形参数
    u1, u2 = 1.0/r1, 1.0/r2
    denom = u1 + u2
    z0 = (u1*u1 + u2*u2) / denom
    tan_a = -u1*u2*(u2 - u1) / denom
    alpha = math.degrees(math.atan(tan_a))
    
    # 蛋形存在性
    egg_exists = z0 > 2*math.sqrt(max(math.tan(math.radians(alpha)), 1e-10))
    
    # 耦合
    c_couple = (z0 * math.sqrt(2) / 2) * math.tan(2 * math.radians(alpha))
    
    # 评级
    if gamma >= 40 or gamma < 0:
        grade = 'X'
    elif c_couple < 0 and gamma < 10:
        grade = 'X'
    elif gamma >= 30:
        grade = 'A'
    elif gamma >= 20:
        grade = 'B'  
    elif gamma >= 10:
        grade = 'C'
    else:
        grade = 'D'
    
    return {
        'h': h, 'gamma': gamma, 'z0': z0, 'alpha': alpha,
        'c': c_couple, 'egg_exists': egg_exists, 'grade': grade,
        'price': closes[-1], 'ma60': baseline,
        'r1': r1, 'r2': r2,
    }

def backtest_stock(code, name, data):
    """单只股票全景回溯"""
    results = []
    n = len(data)
    
    for i in range(60, n - 20):  # 每个交易日，留20天看未来
        window = data[i-60:i]
        future_window = data[i:min(i+60, n)]
        
        params = compute_pks_params(window)
        if params is None: continue
        
        p_now = data[i-1]['close']
        
        # 未来收益
        for horizon in [5, 10, 20, 30, 60]:
            future_idx = min(i + horizon - 1, n - 1)
            if future_idx < i: continue
            future_price = data[future_idx]['close']
            fwd_return = (future_price - p_now) / p_now * 100
            
            results.append({
                'date': data[i-1]['date'],
                'grade': params['grade'],
                'gamma': params['gamma'],
                'h': params['h'],
                'z0': params['z0'],
                'alpha': params['alpha'],
                'c': params['c'],
                'horizon': horizon,
                'fwd_return': fwd_return,
            })
    
    return results

def analyze_backtest(all_results):
    """聚合分析：各评级在各持有期的表现"""
    # 按评级分组
    grade_groups = defaultdict(list)
    for r in all_results:
        grade_groups[r['grade']].append(r)
    
    print(f"\n{'='*70}")
    print(f"  PKS 回溯验证 — 按评级分组 (N={len(all_results)} 个观测)")
    print(f"{'='*70}")
    
    for horizon in [5, 10, 20, 30, 60]:
        print(f"\n  ── 未来{horizon}日收益 ──")
        header = f"  {'评级':<6}{'样本':<8}{'均值%':<10}{'中位%':<10}{'胜率':<8}{'最大%':<10}{'最小%':<10}"
        print(header)
        print("  " + "-"*62)
        
        grade_stats = {}
        for grade in ['A', 'B', 'C', 'D', 'X']:
            items = [r for r in grade_groups.get(grade, []) if r['horizon'] == horizon]
            if not items: continue
            returns = [r['fwd_return'] for r in items]
            mean_r = sum(returns) / len(returns)
            median_r = sorted(returns)[len(returns)//2]
            win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
            max_r = max(returns)
            min_r = min(returns)
            grade_stats[grade] = {'mean': mean_r, 'win_rate': win_rate, 'n': len(items)}
            print(f"  {grade:<6}{len(items):<8}{mean_r:<+10.2f}{median_r:<+10.2f}{win_rate:<8.1f}{max_r:<+10.2f}{min_r:<+10.2f}")
        
        # 对比 C vs X
        if 'C' in grade_stats and 'X' in grade_stats:
            c_mean = grade_stats['C']['mean']
            x_mean = grade_stats['X']['mean']
            spread = c_mean - x_mean
            print(f"  {'':>6}{'':>8}{'C-X spread:':<10}{spread:<+10.2f}")
    
    # 按参数区间分析
    print(f"\n{'='*70}")
    print(f"  参数区间分析 — 未来20日")
    print(f"{'='*70}")
    
    items_20 = [r for r in all_results if r['horizon'] == 20]
    
    # γ 分组
    for param, name, bins in [
        ('gamma', 'γ(趋势烈度)', [0, 5, 10, 15, 20, 25, 30, 45]),
        ('h', 'h(市场尺度)', [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 10]),
        ('z0', 'z₀(市场温度)', [0, 3, 5, 8, 12, 20, 100]),
        ('c', 'c(两力耦合)', [-100, -1, 0, 1, 3, 5, 10, 100]),
    ]:
        print(f"\n  ── {name} ──")
        print(f"  {'区间':<20}{'样本':<8}{'均值%':<10}{'胜率':<8}")
        print("  " + "-"*46)
        for i in range(len(bins)-1):
            lo, hi = bins[i], bins[i+1]
            items_bin = [r for r in items_20 if lo <= r[param] < hi]
            if len(items_bin) < 10: continue
            returns = [r['fwd_return'] for r in items_bin]
            mean_r = sum(returns) / len(returns)
            win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
            print(f"  [{lo:>5.0f}, {hi:>5.0f}){'':>10}{len(items_bin):<8}{mean_r:<+10.2f}{win_rate:<8.1f}")
    
    # 组合规则分析
    print(f"\n{'='*70}")
    print(f"  组合规则 — PKS-C vs PKS-X 逐月表现")
    print(f"{'='*70}")
    
    # 按月聚合
    month_data = defaultdict(lambda: {'C_returns': [], 'X_returns': []})
    for r in all_results:
        if r['horizon'] != 20: continue
        month_key = r['date'][:7]  # YYYY-MM
        if r['grade'] == 'C':
            month_data[month_key]['C_returns'].append(r['fwd_return'])
        elif r['grade'] == 'X':
            month_data[month_key]['X_returns'].append(r['fwd_return'])
    
    c_wins = 0
    x_wins = 0
    total_months = 0
    for month in sorted(month_data.keys()):
        c_avg = sum(month_data[month]['C_returns'])/len(month_data[month]['C_returns']) if month_data[month]['C_returns'] else 0
        x_avg = sum(month_data[month]['X_returns'])/len(month_data[month]['X_returns']) if month_data[month]['X_returns'] else 0
        if month_data[month]['C_returns'] and month_data[month]['X_returns']:
            total_months += 1
            if c_avg > x_avg: c_wins += 1
            else: x_wins += 1
    
    if total_months > 0:
        print(f"  C胜率: {c_wins}/{total_months} = {c_wins/total_months*100:.1f}%  (CvsX月比)")

if __name__ == '__main__':
    all_results = []
    
    for code, name in ALL_STOCKS:
        print(f"  {name}({code})...", end=" ", flush=True)
        data = fetch_kline(code, 500)
        if len(data) < 80:
            print(f"数据不足({len(data)}条)")
            continue
        
        results = backtest_stock(code, name, data)
        all_results.extend(results)
        print(f"回溯{len(results)}个观测点 ({data[0]['date']}~{data[-1]['date']})")
    
    if not all_results:
        print("无数据")
        sys.exit(1)
    
    analyze_backtest(all_results)
    
    # 最后：检查当前评级是否需要调整
    print(f"\n{'='*70}")
    print(f"  诊断建议")
    print(f"{'='*70}")
    c_items_20 = [r for r in all_results if r['horizon']==20 and r['grade']=='C']
    x_items_20 = [r for r in all_results if r['horizon']==20 and r['grade']=='X']
    c_mean = sum(r['fwd_return'] for r in c_items_20)/len(c_items_20) if c_items_20 else 0
    x_mean = sum(r['fwd_return'] for r in x_items_20)/len(x_items_20) if x_items_20 else 0
    print(f"  PKS-C 平均20日收益: {c_mean:+.2f}%")
    print(f"  PKS-X 平均20日收益: {x_mean:+.2f}%")
    if c_mean > x_mean:
        print(f"  ✅ 评级方向正确 (C > X) ，差异 {c_mean-x_mean:+.2f}%")
    else:
        print(f"  ❌ 评级方向错误 (C < X) ，需要调整参数映射！差异 {x_mean-c_mean:+.2f}%")
