#!/usr/bin/env python3
"""智能路由系统回测验证 — 历史每日检测 → 按推荐执行 → 对比实际收益"""
import subprocess, math
from collections import defaultdict

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

def fetch(code, limit=800):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=30)
    if r.returncode: return None, None
    prices = []; vols = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        p = [x.strip() for x in line.split('|')]
        if len(p) < 8: continue
        try:
            prices.append((p[1], float(p[3])))
            if len(p) > 6: vols.append((p[1], float(p[6])))
        except: continue
    prices.reverse(); vols.reverse()
    return dict(prices), dict(vols) if vols else {}

def trend(px, dt_list, days):
    if len(dt_list) < days+1: return 0
    t0 = dt_list[-days-1]; t1 = dt_list[-1]
    if t0 not in px or t1 not in px: return 0
    return (px[t1] - px[t0]) / px[t0] * 100

def ma(px, dt_list, n):
    vals = [px[d] for d in dt_list[-n:] if d in px]
    return sum(vals)/len(vals) if vals else 0

def atr_val(px, dt_list, n=14):
    vals = [px[d] for d in dt_list if d in px]
    if len(vals) < n+30: return 0
    p = vals[-n-1:]
    return sum(abs(p[i] - p[i-1]) / p[i-1] for i in range(1, len(p))) / (len(p)-1) * 100

# ── 历史回溯范围 ──
print('Loading indices...')
hs300_p, hs300_v = fetch('sh000300')
sz50_p, _ = fetch('sh000016')
zz500_p, _ = fetch('sh000905')
spx_p, _ = fetch('us.INX')

if not hs300_p: print('沪深300数据失败'); exit(1)

dates = sorted(hs300_p.keys())
dates_60plus = [d for i, d in enumerate(dates) if i >= 60]
print(f'{dates[0]} ~ {dates[-1]}, {len(dates_60plus)} testable days')

# ── 验证用股票池（多池覆盖）──
POOLS = {
    '成长': ['sh688525','sz001309','sh688336','sz002653','sh603259','sh688331','sz002555'],
    '蓝筹': ['sh600519','sh600036','sh601318','sh600900','sh601088','sz000333','sh600887'],
    '周期': ['sh601899','sh600019','sh601857','sh601225','sh600438','sz002466','sz002460'],
    '金融': ['sh601398','sh601939','sh601288','sh601988','sh601166','sh600016','sz000001'],
}

# Pre-fetch all stocks
print('Loading stocks...')
stock_px = {}
for pool_name, codes in POOLS.items():
    for code in codes:
        px, _ = fetch(code, 800)
        if px: stock_px[code] = px

# ── 逐日回测 ──
results = []
for di in range(60, min(len(dates)-20, len(dates_60plus))):
    dt = dates[di]
    dt_list = dates[:di+1]
    
    # 六维检测
    h60 = trend(hs300_p, dt_list, 60)
    h20 = trend(hs300_p, dt_list, 20)
    hma = hs300_p[dt] / ma(hs300_p, dt_list, 60) - 1
    hvol = trend(hs300_v, dt_list, 20) if hs300_v else 0
    hatr = atr_val(hs300_p, dt_list, 14)
    
    s20 = trend(sz50_p, dt_list, 20) if sz50_p else 0
    z20 = trend(zz500_p, dt_list, 20) if zz500_p else 0
    rotation = s20 - z20
    
    spx20 = trend(spx_p, dt_list, 20) if spx_p else 0
    corr = '高' if h20*spx20 > 0 and abs(h20-spx20) < 3 else ('负' if h20*spx20 < 0 else '中')
    
    # 评分
    score = 50
    if h60 > 10: score += 15
    elif h60 > 5: score += 8
    elif h60 < -8: score -= 20
    elif h60 < -3: score -= 10
    if hma > 0.03: score += 10
    elif hma < -0.03: score -= 10
    if abs(h20) < 5 and abs(hma) < 0.03: score += 5 if abs(h20) < 3 else 0
    else: score += 3 if h20 > 0 else -3
    if rotation > 2: score += 5
    elif rotation < -2: score += 5
    if spx20 < -3: score -= 8
    elif spx20 > 3 and corr == '高': score += 5
    if hatr > 1.8: score -= 8
    elif hatr < 0.8: score += 3
    if hvol > 10: score += 3
    elif hvol < -10: score -= 3
    
    # 推荐算法
    if score >= 70: algo = '96f'
    elif score >= 55: algo = '96f+PKS'
    elif score >= 40: algo = 'PKS'
    elif score >= 25: algo = '96fD'
    else: algo = 'SKIP'
    
    # 在该日期计算所有股票的 PKS 评级 + 未来收益
    stock_returns = []
    for code, px in stock_px.items():
        if dt not in px: continue
        di_s = list(px.keys()).index(dt)
        if di_s < 60: continue
        
        # PKS params
        w_dates = sorted(px.keys())[di_s-60:di_s]
        w_cls = [px[d] for d in w_dates if d in px]
        if len(w_cls) < 60: continue
        
        bl = sum(w_cls)/len(w_cls)
        ph = max(w_cls); pl = min(w_cls)
        r1 = max((ph-bl)/bl, (bl-pl)/bl); r2 = min((ph-bl)/bl, (bl-pl)/bl)
        if r2 < 1e-8: continue
        
        g = math.degrees(math.atan((r1-r2)/(r1+r2)))
        u1, u2 = 1/r1, 1/r2
        z = (u1*u1+u2*u2)/(u1+u2)
        ar = math.atan(-u1*u2*(u2-u1)/(u1+u2)); tana = abs(math.tan(ar))
        z_min = 2*math.sqrt(tana) if tana > 0 else 0.001
        safety = z/z_min if z_min > 0 else 999
        c_val = (z*math.sqrt(2)/2)*math.tan(2*ar)
        h_val = 2*r1*r2/(r1+r2)
        vol = max(r1, r2)
        
        # PKS grade
        if g > 30 or c_val < -1 or c_val > 3: pks = 'X'
        elif g >= 20: pks = 'A'
        elif g >= 10: pks = 'B'
        elif safety >= 2: pks = 'C'
        else: pks = 'D'
        
        pn = px.get(list(px.keys())[di_s-1] if di_s > 0 else dt, px[dt])
        fwd_dates = sorted(px.keys())[di_s:min(di_s+20, len(px))]
        if len(fwd_dates) < 5: continue
        fp = px[fwd_dates[-1]]
        fwd_ret = (fp - pn) / pn * 100
        
        stock_returns.append({'code': code[:6], 'pks': pks, 'fwd': fwd_ret,
                             'g': g, 'safety': safety, 'vol': vol, 'h': h_val})
    
    if len(stock_returns) < 5: continue
    
    # 按算法模拟选股
    all_r = stock_returns
    
    # 96fen: take all
    all_ret = sum(r['fwd'] for r in all_r)/len(all_r)
    
    # PKS: take A+B
    pks_ab = [r for r in all_r if r['pks'] in ('A','B')]
    pks_ret = sum(r['fwd'] for r in pks_ab)/len(pks_ab) if pks_ab else all_ret
    
    # PKS v2.4 enhancement: A+B + h>median + (cycle:c>=0)
    pks_v24 = [r for r in all_r if r['pks'] in ('A','B') and r['h'] > sum(x['h'] for x in all_r)/len(all_r)]
    pks24_ret = sum(r['fwd'] for r in pks_v24)/len(pks_v24) if pks_v24 else pks_ret
    
    results.append({
        'date': dt, 'score': score, 'algo': algo,
        'all_ret': all_ret, 'pks_ret': pks_ret, 'pks24_ret': pks24_ret,
        'h60': h60, 'h20': h20, 'spx20': spx20, 'rotation': rotation,
        'atr': hatr, 'hvol': hvol,
        'n_all': len(all_r), 'n_pks': len(pks_ab),
    })

N = len(results)
if N < 50:
    print(f'Only {N} test days — insufficient'); exit(1)

print(f'\n{"="*55}')
print(f'  智能路由系统回测验证 (N={N} trading days)')
print(f'{"="*55}')

# 分组分析
regime_groups = defaultdict(list)
for r in results:
    regime_groups[r['algo']].append(r)

total = {
    'all_correct': 0, 'pks_correct': 0, 'pks24_correct': 0,
    'all_sum': 0.0, 'pks_sum': 0.0, 'pks24_sum': 0.0,
    'recommended_sum': 0.0, 'recommended_n': 0,
    'missed_sum': 0.0, 'missed_n': 0,
}

print(f'\n  {"算法推荐":<12} {"天数":<6} {"占比":<6} {"全量均值":<10} {"推荐算法":<10} {"推荐+增强":<10} {"超额":<8}')
print(f'  {"-"*60}')

for algo, label in [('96f','96分全攻'),('96f+PKS','96分+PKS'),('PKS','PKS增强'),('96fD','96分防守'),('SKIP','暂停')]:
    days = regime_groups.get(algo, [])
    if not days: continue
    
    n = len(days)
    all_avg = sum(r['all_ret'] for r in days)/n
    
    # 根据推荐选择对应算法收益
    if algo == '96f': rec_ret = [r['all_ret'] for r in days]
    elif algo in ('96f+PKS','96fD'): rec_ret = [r['all_ret'] for r in days]
    elif algo == 'PKS': rec_ret = [r['pks_ret'] for r in days]
    else: rec_ret = [0]*n
    
    rec_avg = sum(rec_ret)/n if rec_ret else 0
    pks24_avg = sum(r['pks24_ret'] for r in days)/n
    
    # 对比: 如果不用推荐而用PKS会怎样
    pks_would = sum(r['pks_ret'] for r in days)/n
    
    print(f'  {label:<12} {n:<6} {n/N*100:<5.1f}% {all_avg:+7.2f}% {rec_avg:+9.2f}% {pks24_avg:+9.2f}% {rec_avg-all_avg:+7.2f}%')
    
    total['recommended_sum'] += sum(rec_ret)
    total['recommended_n'] += len(rec_ret)

# 核心对比: 始终用PKS vs 智能路由
always_all = sum(r['all_ret'] for r in results)/N
always_pks = sum(r['pks_ret'] for r in results)/N
always_pks24 = sum(r['pks24_ret'] for r in results)/N
smart_rec = total['recommended_sum']/total['recommended_n'] if total['recommended_n'] else 0

print(f'\n  {"="*55}')
print(f'  终极对比')
print(f'  {"="*55}')
print(f'  始终96分全量:  {always_all:+.2f}%')
print(f'  始终PKS基础:   {always_pks:+.2f}%')
print(f'  始终PKS v2.4:  {always_pks24:+.2f}%')
print(f'  >> 智能路由:   {smart_rec:+.2f}%')
print(f'  智能vs全量:    {smart_rec-always_all:+.2f}%')
print(f'  智能vs PKS:    {smart_rec-always_pks:+.2f}%')

# 不同大盘环境下的智能路由表现
print(f'\n  {"="*55}')
print(f'  分大盘环境: 智能路由推荐 vs 实际')
print(f'  {"="*55}')
for env_name, env_fn in [
    ('牛(60d>10%+>MA3%)', lambda r: r['h60']>10 and r['h20']>2),
    ('偏多(60d>0,>MA)', lambda r: r['h60']>0 and r['h20']>0),
    ('震(近MA±3%,20d<5%)', lambda r: abs(r['h20'])<5 and abs(r['h20'])>0.1 and abs(r['h60'])<15),
    ('偏空(60d<0)', lambda r: r['h60']<0),
]:
    days = [r for r in results if env_fn(r)]
    if len(days) < 20: continue
    n = len(days)
    all_avg = sum(r['all_ret'] for r in days)/n
    pks_avg = sum(r['pks_ret'] for r in days)/n
    pks24_avg = sum(r['pks24_ret'] for r in days)/n
    
    # 推荐是否正确
    correct_pks = sum(1 for r in days if r['algo'] == 'PKS' and r['pks_ret'] > r['all_ret'])
    total_pks_days = sum(1 for r in days if r['algo'] == 'PKS')
    correct_96f = sum(1 for r in days if r['algo'] in ('96f','96f+PKS') and r['all_ret'] > r['pks_ret'])
    total_96f_days = sum(1 for r in days if r['algo'] in ('96f','96f+PKS'))
    
    print(f'\n  {env_name} (n={n}天)')
    print(f'  ALL={all_avg:+.2f}% PKS={pks_avg:+.2f}% v2.4={pks24_avg:+.2f}%')
    if total_pks_days > 0:
        print(f'  PKS推荐准确率: {correct_pks}/{total_pks_days} = {correct_pks/total_pks_days*100:.0f}%')
    if total_96f_days > 0:
        print(f'  96f推荐准确率: {correct_96f}/{total_96f_days} = {correct_96f/total_96f_days*100:.0f}%')
