"""验证：PKS v2.4 在纯成长/动量型池中是否始终最优（第三批全新股票）"""
import subprocess, math
from collections import defaultdict

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

# ====== 第三批：纯成长/动量型 —— 跟 v1/v2 完全不重叠 ======
GROWTH_POOL = [
    # 半导体设备/材料（高波高成长）
    ('sh688012','中微公司'),('sh688536','芯源微'),('sh688072','拓荆科技'),
    ('sh688082','盛美上海'),('sz300666','江丰电子'),('sh688200','华峰测控'),
    ('sh688126','沪硅产业'),('sz002371','北方华创'),
    # AI/机器人
    ('sh688008','澜起科技'),('sz300474','景嘉微'),('sz002747','埃斯顿'),
    ('sz300024','机器人'),('sh688017','绿的谐波'),('sh688160','步科股份'),
    # 新能源材料
    ('sh688005','容百科技'),('sh688116','天奈科技'),('sz300750','宁德时代'),
    ('sh688599','天合光能'),('sh688303','大全能源'),
    # 创新药/Biotech
    ('sh688185','康希诺'),('sh688180','君实生物'),('sz300759','康龙化成'),
    ('sh688202','美迪西'),('sh688235','百济神州'),
    # 军工/卫星
    ('sh688568','中科星图'),('sh688066','航天宏图'),('sz300101','振芯科技'),
]

def raw_fetch(code, limit=800):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0: return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        fields = [x.strip() for x in line.split('|')]
        if len(fields) < 9: continue
        try: data.append({'d':fields[1], 'o':float(fields[2]), 'c':float(fields[3]),
                          'h':float(fields[4]), 'l':float(fields[5])})
        except: continue
    data.reverse(); return data

def raw_fetch_close(code, limit=800):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0: return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        fields = [x.strip() for x in line.split('|')]
        if len(fields) < 9: continue
        try: data.append({'d':fields[1], 'c':float(fields[3])})
        except: continue
    data.reverse(); return data

def pks_v24(data_60d):
    cls = [d['c'] for d in data_60d]; bl = sum(cls)/len(cls)
    ph = max(d['h'] for d in data_60d); pl = min(d['l'] for d in data_60d)
    r1 = max((ph-bl)/bl, (bl-pl)/bl); r2 = min((ph-bl)/bl, (bl-pl)/bl)
    if r2 < 1e-8: return None
    g = math.degrees(math.atan((r1-r2)/(r1+r2)))
    u1, u2 = 1/r1, 1/r2
    z = (u1*u1+u2*u2)/(u1+u2)
    ar = math.atan(-u1*u2*(u2-u1)/(u1+u2))
    tana = abs(math.tan(ar))
    z_min = 2*math.sqrt(tana) if tana > 0 else 0.001
    safety = z/z_min if z_min > 0 else 999
    c_val = (z*math.sqrt(2)/2)*math.tan(2*ar)
    if g > 30 or c_val < -1 or c_val > 3: grade = 'X'
    elif g >= 20: grade = 'A'
    elif g >= 10: grade = 'B'
    elif safety >= 2: grade = 'C'
    else: grade = 'D'
    return {'g':g, 'grade':grade}

# ── 大盘 ──
print('获取沪深300...', end=' ', flush=True)
mkt = raw_fetch_close('sh000300', 800)
if not mkt: print('FAIL'); exit()
mkt_map = {d['d']: i for i, d in enumerate(mkt)}
print(f'{len(mkt)}天 {mkt[0]["d"]}→{mkt[-1]["d"]}')

# ── 预取 ──
print(f'预取 {len(GROWTH_POOL)} 只成长股...', flush=True)
stock_db = {}
for code, name in GROWTH_POOL:
    data = raw_fetch(code, 800)
    if data and len(data) >= 80:
        stock_db[code] = data
        print(f'  {name}: {len(data)}天', flush=True)
    else:
        print(f'  {name}: FAIL', flush=True)

# ── 环境分类 ──
def market_regime(mkt_list, idx):
    if idx < 60: return None
    c0, c60 = mkt_list[idx]['c'], mkt_list[idx-60]['c']
    c20 = mkt_list[idx-20]['c'] if idx >= 20 else c60
    ma60 = sum(d['c'] for d in mkt_list[idx-60:idx])/60
    p60 = (c0-c60)/c60*100; p20 = (c0-c20)/c20*100
    if p60 > 10 and c0 > ma60*1.03: return 'BULL'
    if p60 < -8: return 'BEAR'
    if abs(p20) < 5 and abs(c0/ma60-1) < 0.05: return 'CHOP'
    if p60 > 0 and c0 > ma60: return 'BIAS_UP'
    return 'BIAS_DOWN'

# ── 回测 ──
print(f'回测 {len(stock_db)} 只...', flush=True)
results = {r: {'pks':[], 'router':[], 'all':[]}
           for r in ['BULL','BIAS_UP','CHOP','BIAS_DOWN','BEAR']}

for code in stock_db:
    data = stock_db[code]; n = len(data)
    for i in range(60, n-20):
        dt = data[i]['d']
        if dt not in mkt_map: continue
        mi = mkt_map[dt]
        regime = market_regime(mkt, mi)
        if regime is None: continue
        
        w = data[i-60:i]; p = pks_v24(w)
        if p is None: continue
        
        pn = data[i-1]['c']; fi = min(i+19, n-1)
        fwd = (data[fi]['c']-pn)/pn*100
        
        results[regime]['all'].append(fwd)
        if p['grade'] in ('A','B'):
            results[regime]['pks'].append(fwd)
        
        # 智能路由
        if regime == 'BULL': r_sel = p['grade'] in ('A','B','C')
        elif regime == 'BEAR': r_sel = p['grade'] == 'A'
        elif regime == 'CHOP': r_sel = p['grade'] in ('A','B')
        elif regime == 'BIAS_UP': r_sel = p['grade'] in ('A','B','C')
        else: r_sel = p['grade'] == 'A'
        
        if r_sel: results[regime]['router'].append(fwd)

# ── 输出 ──
total = sum(len(v['all']) for v in results.values())
labels = {'BULL':'🐂牛','BIAS_UP':'📈偏多','CHOP':'↔️震','BIAS_DOWN':'📉偏空','BEAR':'🐻熊'}

print(f'\n{"="*65}')
print(f'  PKS v2.4 纯成长池验证（第三批全新 × 3年）')
print(f'{"="*65}')
print(f'  总观测: {total}')
print(f'\n  {"环境":<10} {"样本":<8} {"PKS v2.4":<10} {"智能路由":<10} {"全量":<10} {"PKSvs全":<10} {"PKvs路":<10}')
print(f'  {"-"*10} {"-"*8} {"-"*10} {"-"*10} {"-"*10} {"-"*10} {"-"*10}')

all_pks = []; all_router = []; all_all = []
for regime in ['BULL','BIAS_UP','CHOP','BIAS_DOWN','BEAR']:
    rr = results[regime]
    if not rr['all']: continue
    am = sum(rr['all'])/len(rr['all'])
    pm = sum(rr['pks'])/len(rr['pks']) if rr['pks'] else 0
    rm = sum(rr['router'])/len(rr['router']) if rr['router'] else 0
    print(f'  {labels[regime]:<10} {len(rr["all"]):<8} {pm:+8.2f}%  {rm:+8.2f}%  {am:+8.2f}%  {pm-am:+8.2f}%  {pm-rm:+8.2f}%')
    all_pks.extend(rr['pks']); all_router.extend(rr['router']); all_all.extend(rr['all'])

tp = sum(all_pks)/len(all_pks) if all_pks else 0
tr = sum(all_router)/len(all_router) if all_router else 0
ta = sum(all_all)/len(all_all) if all_all else 0
wp = sum(1 for x in all_pks if x>0)/len(all_pks)*100 if all_pks else 0
wr = sum(1 for x in all_router if x>0)/len(all_router)*100 if all_router else 0
wa = sum(1 for x in all_all if x>0)/len(all_all)*100 if all_all else 0

print(f'\n  {"汇总":<10} {total:<8} {tp:+8.2f}%  {tr:+8.2f}%  {ta:+8.2f}%  {tp-ta:+8.2f}%  {tp-tr:+8.2f}%')
print(f'  {"胜率":<10} {"":<8} {wp:7.1f}%  {wr:7.1f}%  {wa:7.1f}%')

# ── γ 分层（验证成长股专属模式）──
print(f'\n{"="*65}')
print(f'  γ 分层分析（20日）')
print(f'{"="*65}')
i20 = []
for code in stock_db:
    data = stock_db[code]; n = len(data)
    for i in range(60, n-20):
        w = data[i-60:i]; p = pks_v24(w)
        if p is None: continue
        pn = data[i-1]['c']; fi = min(i+19, n-1)
        i20.append({'g':p['g'], 'f':(data[fi]['c']-pn)/pn*100, 'gd':p['grade']})

print(f'  {"γ区间":<12} {"样本":<8} {"收益":<10} {"胜率":<8} {"PKS选":<8}')
for lo, hi in [(0,5),(5,10),(10,15),(15,20),(20,25),(25,30),(30,99)]:
    it = [r for r in i20 if lo<=r['g']<hi]
    if len(it)<30: continue
    m = sum(r['f'] for r in it)/len(it); w = sum(1 for r in it if r['f']>0)/len(it)*100
    pk = [r for r in it if r['gd'] in ('A','B')]
    pm = sum(r['f'] for r in pk)/len(pk) if pk else 0
    print(f'  [{lo},{hi}){"":>6} {len(it):<8} {m:+8.2f}% {w:5.1f}% {pm:+8.2f}%')

# ── 对比 v1 v2 ──
print(f'\n{"="*65}')
print(f'  三轮对比')
print(f'{"="*65}')
print(f'  {"轮次":<6} {"池型":<12} {"股票":<6} {"PKS":<10} {"路由":<10} {"全量":<10} {"最优":<6}')
# v1数据（手动填入）
print(f'  {"v1":<6} {"96fen成长":<12} {"28":<6} {"+3.36%":<10} {"+2.13%":<10} {"+2.38%":<10} {"PKS":<6}')
print(f'  {"v2":<6} {"消费/新能源/医药":<16} {"26":<6} {"+0.69%":<10} {"+0.53%":<10} {"+0.93%":<10} {"全量":<6}')
n_stocks = str(len(stock_db))
p_tp = f"{tp:+7.2f}%"
p_tr = f"{tr:+7.2f}%"
p_ta = f"{ta:+7.2f}%"
print(f'  {"v3":<6} {"半导体/AI/军工":<14} {n_stocks:<6} {p_tp:<10} {p_tr:<10} {p_ta:<10} ', end='')
best = 'PKS' if tp>=tr and tp>=ta else ('路由' if tr>=ta else '全量')
print(f'{best:<6}')

if tp >= tr and tp >= ta:
    print(f'\n  ✅ 确认: PKS v2.4 在纯成长/动量池中始终最优')
else:
    print(f'\n  ❌ 证伪: PKS v2.4 不是始终最优')
