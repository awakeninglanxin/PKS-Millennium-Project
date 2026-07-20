"""PKS v2.4 vs 智能路由 验证 v2（新池 × 3年）—— 修复版"""
import subprocess, math, sys
from collections import defaultdict

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

POOLS = {
    '消费电子': [('sz002241','歌尔'),('sz002475','立讯'),('sz300433','蓝思'),('sz002456','欧菲光'),
                ('sz300136','信维'),('sh603160','汇顶'),('sz002351','漫步者')],
    '新能源车': [('sh601238','广汽'),('sz000625','长安'),('sz002594','比亚迪'),
                ('sh600104','上汽'),('sz300014','亿纬'),('sh600733','北汽'),('sz002466','天齐')],
    '医药健康': [('sh600276','恒瑞'),('sz300760','迈瑞'),('sh300015','爱尔'),
                ('sz300122','智飞'),('sz002001','新和成'),('sh600196','复星')],
    '互联网传媒': [('sz300418','昆仑'),('sz002230','讯飞'),('sh600050','联通'),
                  ('sz300058','蓝标'),('sz002605','姚记'),('sh603000','人民网'),('sz002558','巨人')],
}

def raw_fetch(code, limit=800):
    """抓取原始K线，返回 [(date, close), ...] 列表，oldest first"""
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line:
            continue
        fields = [x.strip() for x in line.split('|')]
        if len(fields) < 9:
            continue
        try:
            data.append({'d': fields[1], 'c': float(fields[3])})
        except (ValueError, IndexError):
            continue
    data.reverse()  # oldest first
    return data

def raw_fetch_ohlc(code, limit=800):
    """抓取OHLC数据用于PKS计算"""
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line:
            continue
        fields = [x.strip() for x in line.split('|')]
        if len(fields) < 9:
            continue
        try:
            data.append({'d': fields[1], 'o': float(fields[2]), 'c': float(fields[3]),
                        'h': float(fields[4]), 'l': float(fields[5])})
        except (ValueError, IndexError):
            continue
    data.reverse()
    return data

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
    return {'g': g, 's': safety, 'c': c_val, 'grade': grade}

# ── 1. 获取大盘 ──
print('1/3 获取沪深300...', flush=True)
mkt = raw_fetch('sh000300', 800)
if not mkt:
    print('ERROR: 大盘数据获取失败！'); sys.exit(1)
mkt_map = {d['d']: i for i, d in enumerate(mkt)}
print(f'   沪深300: {len(mkt)}天  {mkt[0]["d"]}→{mkt[-1]["d"]}')

# ── 2. 预取股票 ──
all_codes = set()
for codes in POOLS.values():
    for c, _ in codes: all_codes.add(c)
print(f'2/3 预取 {len(all_codes)} 只股票...', flush=True)

stock_db = {}
for code in sorted(all_codes):
    data = raw_fetch_ohlc(code, 800)
    if data and len(data) >= 80:
        stock_db[code] = data
        print(f'   {code}: {len(data)}天', flush=True)
    else:
        print(f'   {code}: FAIL', flush=True)

# ── 3. 回测 ──
print(f'3/3 回测 ({len(stock_db)} 只)...', flush=True)

def market_regime(mkt_list, idx):
    """基于沪深300判断环境"""
    if idx < 60: return None
    c0 = mkt_list[idx]['c']
    c60 = mkt_list[idx-60]['c']
    c20 = mkt_list[idx-20]['c'] if idx >= 20 else c60
    ma60 = sum(d['c'] for d in mkt_list[idx-60:idx]) / 60
    p60 = (c0 - c60) / c60 * 100
    p20 = (c0 - c20) / c20 * 100
    if p60 > 10 and c0 > ma60 * 1.03: return 'BULL'
    if p60 < -8: return 'BEAR'
    if abs(p20) < 5 and abs(c0/ma60 - 1) < 0.05: return 'CHOP'
    if p60 > 0 and c0 > ma60: return 'BIAS_UP'
    return 'BIAS_DOWN'

results = {
    'BULL':    {'pks': [], 'router': [], 'all': []},
    'BIAS_UP': {'pks': [], 'router': [], 'all': []},
    'CHOP':    {'pks': [], 'router': [], 'all': []},
    'BIAS_DOWN': {'pks': [], 'router': [], 'all': []},
    'BEAR':    {'pks': [], 'router': [], 'all': []},
}

pool_results = defaultdict(lambda: {'pks': [], 'all': []})

for code in stock_db:
    data = stock_db[code]
    n = len(data)
    for i in range(60, n - 20):
        dt = data[i]['d']
        if dt not in mkt_map: continue
        mi = mkt_map[dt]
        regime = market_regime(mkt, mi)
        if regime is None: continue
        
        w = data[i-60:i]
        p = pks_v24(w)
        if p is None: continue
        
        pn = data[i-1]['c']
        fi = min(i + 19, n - 1)
        fwd = (data[fi]['c'] - pn) / pn * 100
        
        results[regime]['all'].append(fwd)
        if p['grade'] in ('A', 'B'):
            results[regime]['pks'].append(fwd)
        
        # 智能路由: 根据环境切换
        if regime == 'BULL':
            router_sel = p['grade'] in ('A','B','C')  # 牛放宽
        elif regime == 'BEAR':
            router_sel = p['grade'] == 'A'  # 熊收紧
        elif regime == 'CHOP':
            router_sel = p['grade'] in ('A','B')  # 震=PKS
        elif regime == 'BIAS_UP':
            router_sel = p['grade'] in ('A','B','C')
        else:  # BIAS_DOWN
            router_sel = p['grade'] == 'A'
        
        if router_sel:
            results[regime]['router'].append(fwd)
        
        # 按池统计
        for pn_name, codes in POOLS.items():
            if code in [c for c,_ in codes]:
                pool_results[pn_name]['all'].append(fwd)
                if p['grade'] in ('A','B'):
                    pool_results[pn_name]['pks'].append(fwd)

# ── 输出 ──
total_obs = sum(len(v['all']) for v in results.values())
pks_total = sum(len(v['pks']) for v in results.values())
router_total = sum(len(v['router']) for v in results.values())

print(f'\n{"="*60}')
print(f'  PKS v2.4 vs 智能路由 验证 v2（全新池 × 3年）')
print(f'{"="*60}')
print(f'  总观测: {total_obs} | PKS选中: {pks_total} | 路由选中: {router_total}')

labels_cn = {'BULL': '🐂牛', 'BIAS_UP': '📈偏多', 'CHOP': '↔️震', 'BIAS_DOWN': '📉偏空', 'BEAR': '🐻熊'}

print(f'\n  {"环境":<10} {"样本":<8} {"PKS v2.4":<10} {"智能路由":<10} {"全量":<10} {"PKSvs全量":<10} {"PKvs路由":<10}')
print(f'  {"-"*10} {"-"*8} {"-"*10} {"-"*10} {"-"*10} {"-"*10} {"-"*10}')

all_regime_pks = []
all_regime_router = []
all_regime_all = []

for regime in ['BULL','BIAS_UP','CHOP','BIAS_DOWN','BEAR']:
    rr = results[regime]
    if not rr['all']: continue
    am = sum(rr['all'])/len(rr['all'])
    pm = sum(rr['pks'])/len(rr['pks']) if rr['pks'] else 0
    rm = sum(rr['router'])/len(rr['router']) if rr['router'] else 0
    print(f'  {labels_cn[regime]:<10} {len(rr["all"]):<8} {pm:+8.2f}%  {rm:+8.2f}%  {am:+8.2f}%  {pm-am:+8.2f}%  {pm-rm:+8.2f}%')
    all_regime_pks.extend(rr['pks'])
    all_regime_router.extend(rr['router'])
    all_regime_all.extend(rr['all'])

# 汇总
total_pm = sum(all_regime_pks)/len(all_regime_pks) if all_regime_pks else 0
total_rm = sum(all_regime_router)/len(all_regime_router) if all_regime_router else 0
total_am = sum(all_regime_all)/len(all_regime_all) if all_regime_all else 0
pks_wr = sum(1 for x in all_regime_pks if x > 0) / len(all_regime_pks) * 100 if all_regime_pks else 0
router_wr = sum(1 for x in all_regime_router if x > 0) / len(all_regime_router) * 100 if all_regime_router else 0
all_wr = sum(1 for x in all_regime_all if x > 0) / len(all_regime_all) * 100 if all_regime_all else 0

print(f'\n  {"汇总":<10} {total_obs:<8} {total_pm:+8.2f}%  {total_rm:+8.2f}%  {total_am:+8.2f}%  {total_pm-total_am:+8.2f}%  {total_pm-total_rm:+8.2f}%')
print(f'  {"胜率":<10} {"":<8} {pks_wr:7.1f}%  {router_wr:7.1f}%  {all_wr:7.1f}%')

# ── 按池 ──
print(f'\n{"="*60}')
print(f'  按池拆分: PKS A+B vs 全量')
print(f'{"="*60}')
for pn, pr in pool_results.items():
    if not pr['all']: continue
    pm = sum(pr['pks'])/len(pr['pks']) if pr['pks'] else 0
    am = sum(pr['all'])/len(pr['all'])
    print(f'  {pn:<12} PKS={pm:+.2f}%  ALL={am:+.2f}%  → +{pm-am:+.2f}%  (n={len(pr["all"])})')

# ── 结论 ──
print(f'\n{"="*60}')
if total_pm > total_rm and total_pm > total_am:
    print(f'  ✅ PKS v2.4 最优: {total_pm:+.2f}%')
    print(f'     胜路由 +{total_pm-total_rm:+.2f}%  |  胜全量 +{total_pm-total_am:+.2f}%')
elif total_rm > total_pm:
    print(f'  ⚠️ 智能路由最优: {total_rm:+.2f}%')
    print(f'     胜PKS +{total_rm-total_pm:+.2f}%  |  胜全量 +{total_rm-total_am:+.2f}%')
else:
    print(f'  ➡️ 全量最优: {total_am:+.2f}%')
print(f'{"="*60}')
