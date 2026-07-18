#!/usr/bin/env python3
"""PKS 回溯验证 v2 — 全新股票池 + 3年数据"""
import subprocess, sys, math
from collections import defaultdict

NODE = r"C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe"
WSK = r"C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js"

# 全新股票池 — 避开 TOP10 已测过的
STOCKS = [
    ("sh600519", "贵州茅台"), ("sz000858", "五粮液"), ("sh601318", "中国平安"),
    ("sh600036", "招商银行"), ("sz300750", "宁德时代"), ("sz002594", "比亚迪"),
    ("sh688981", "中芯国际"), ("sh601012", "隆基绿能"), ("sh600900", "长江电力"),
    ("sz002415", "海康威视"), ("sh601088", "中国神华"), ("sh600809", "山西汾酒"),
    ("sz000001", "平安银行"), ("sh601166", "兴业银行"), ("sz002230", "科大讯飞"),
    ("sz000063", "中兴通讯"), ("sz300059", "东方财富"), ("sh600585", "海螺水泥"),
]

def fetch_kline(code, limit=800):
    try:
        r = subprocess.run([NODE, WSK, "kline", code, "--period", "day", "--limit", str(limit)],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0: return []
        lines = r.stdout.strip().split('\n')
        data = []
        for line in lines:
            if not line.startswith('| ') or line.startswith('| ---'): continue
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) < 7: continue
            try:
                data.append({'date': parts[0], 'open': float(parts[1]),
                    'close': float(parts[2]), 'high': float(parts[3]),
                    'low': float(parts[4]), 'volume': float(parts[5])})
            except: continue
        return data
    except: return []

def pks_params(window):
    closes = [d['close'] for d in window]
    highs = [d['high'] for d in window]
    lows = [d['low'] for d in window]
    baseline = sum(closes) / len(closes)
    if baseline <= 0: return None
    p_max, p_min = max(highs), min(lows)
    r_max = (p_max-baseline)/baseline if p_max>baseline else 0.001
    r_min = (baseline-p_min)/baseline if p_min<baseline else 0.001
    r1, r2 = max(r_max,r_min), min(r_max,r_min)
    if r2 < 1e-8: r2 = 1e-8
    h = 2*r1*r2/(r1+r2)
    tan_g = (r1-r2)/(r1+r2)
    gamma = math.degrees(math.atan(tan_g))
    u1, u2 = 1.0/r1, 1.0/r2
    z0 = (u1*u1+u2*u2)/(u1+u2)
    tan_a = -u1*u2*(u2-u1)/(u1+u2)
    alpha = math.degrees(math.atan(tan_a))
    c = (z0*math.sqrt(2)/2)*math.tan(2*math.radians(alpha))
    # v2.1 修正评级
    if gamma >= 30 or z0 < 3: grade = 'X'
    elif c < -1 or c > 3: grade = 'X'
    elif gamma < 5: grade = 'D'
    elif gamma >= 25 and z0 >= 8: grade = 'A'
    elif gamma >= 20 and z0 >= 8: grade = 'B'
    elif gamma >= 10: grade = 'C'
    else: grade = 'D'
    return {'h':h,'gamma':gamma,'z0':z0,'alpha':alpha,'c':c,'grade':grade,'price':closes[-1]}

all_results = []
for code, name in STOCKS:
    print(f"  {name}...", end=" ", flush=True)
    data = fetch_kline(code, 800)
    if len(data) < 80: print(f"数据不足({len(data)})"); continue
    n = len(data)
    count = 0
    for i in range(60, n-20):
        w = data[i-60:i]
        p = pks_params(w)
        if p is None: continue
        p_now = data[i-1]['close']
        for horizon in [10, 20, 30, 60]:
            fi = min(i+horizon-1, n-1)
            if fi <= i: continue
            fp = data[fi]['close']
            all_results.append({'grade':p['grade'],'gamma':p['gamma'],'h':p['h'],
                'z0':p['z0'],'alpha':p['alpha'],'c':p['c'],
                'horizon':horizon,'fwd':(fp-p_now)/p_now*100,'date':data[i-1]['date']})
            count += 1
    print(f"{count}个观测 ({data[0]['date']}~{data[-1]['date']})")

print(f"\n{'='*60}")
print(f"  汇总 N={len(all_results)}")
print(f"{'='*60}")

grade_groups = defaultdict(list)
for r in all_results: grade_groups[r['grade']].append(r)

for horizon in [10, 20, 30, 60]:
    print(f"\n  未来{horizon}日")
    print(f"  {'评级':<6}{'样本':<8}{'均值%':<10}{'中位%':<10}{'胜率':<8}{'A-X':<10}")
    print(f"  {'-'*42}")
    stats = {}
    for grade in ['A','B','C','D','X']:
        items = [r for r in grade_groups.get(grade,[]) if r['horizon']==horizon]
        if not items: continue
        rets = [r['fwd'] for r in items]
        m = sum(rets)/len(rets); med = sorted(rets)[len(rets)//2]
        wr = sum(1 for r in rets if r>0)/len(rets)*100
        stats[grade] = m
        print(f"  {grade:<6}{len(items):<8}{m:<+10.2f}{med:<+10.2f}{wr:<8.1f}", end="")
        if grade == 'X': print()
        elif grade == 'A':
            if 'X' in stats: print(f"{m-stats['X']:<+10.2f}")
            else: print()

# 参数区间
items_20 = [r for r in all_results if r['horizon']==20]
print(f"\n{'='*60}")
print(f"  参数区间 — 20日")
print(f"{'='*60}")
for name, key, bins in [
    ('γ','gamma',[0,5,10,15,20,25,30,99]),
    ('z₀','z0',[0,3,5,8,12,20,50,999]),
    ('c','c',[-999,-1,0,1,3,5,999]),
]:
    print(f"\n  {name}:")
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        items = [r for r in items_20 if lo<=r[key]<hi]
        if len(items)<20: continue
        rets = [r['fwd'] for r in items]
        m = sum(rets)/len(rets); wr = sum(1 for r in rets if r>0)/len(rets)*100
        print(f"  [{lo:>5},{hi:>5}) n={len(items):<6} {m:+.2f}% wr={wr:.1f}%")
