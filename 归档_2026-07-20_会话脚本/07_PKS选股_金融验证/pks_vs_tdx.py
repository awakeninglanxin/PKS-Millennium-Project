"""PKS v2.5 vs 通达信主力监测器 — 买卖信号质量 head-to-head"""
import subprocess, math
from collections import defaultdict

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

# 20只成长股（与PKS回测池重叠，公平比较）
POOL = [
    ('sh688012','中微'),('sh688536','芯源'),('sh688072','拓荆'),('sh688082','盛美'),
    ('sz300666','江丰'),('sh688200','华峰'),('sh688126','沪硅'),('sz002371','北华'),
    ('sh688008','澜起'),('sz300474','景嘉'),('sh688017','绿的'),('sh688160','步科'),
    ('sh688111','金山'),('sh688095','福昕'),('sz300454','深信'),('sh688256','寒武'),
    ('sz300502','新易'),('sz300308','中际'),('sz300750','宁德'),('sh688005','容百'),
]

def fetch(code):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', '800'],
                      capture_output=True, text=True, timeout=60)
    if r.returncode: return []
    data = []
    for l in r.stdout.strip().split('\n'):
        if not l.startswith('| ') or '---' in l: continue
        f = [x.strip() for x in l.split('|')]
        if len(f) < 9: continue
        try: data.append({'d':f[1],'o':float(f[2]),'c':float(f[3]),'h':float(f[4]),'l':float(f[5])})
        except: continue
    data.reverse(); return data

def td_ema(data, period, idx):
    """通达信EMA (与标准EMA略有不同，TD用最后一个值初始化)"""
    if idx < period: return sum(data[i]['c'] for i in range(idx+1)) / (idx+1)
    k = 2.0 / (period + 1)
    ema = data[0]['c']
    for i in range(1, idx+1):
        ema = data[i]['c'] * k + ema * (1 - k)
    return ema

def td_sma(data, idx, n, m):
    """通达信SMA: SMA(X,N,M) = (M*X+(N-M)*SMA')/N"""
    if idx < n: return data[idx]['c']
    sma = data[0]['c']
    for i in range(1, idx+1):
        sma = (m * data[i]['c'] + (n - m) * sma) / n
    return sma

def td_hhv(data, idx, period):
    """N日内最高价"""
    start = max(0, idx-period+1)
    return max(data[i]['h'] for i in range(start, idx+1))

def td_llv(data, idx, period):
    """N日内最低价"""
    start = max(0, idx-period+1)
    return min(data[i]['l'] for i in range(start, idx+1))

def td_ma(data, idx, period):
    """N日移动平均"""
    start = max(0, idx-period+1)
    return sum(data[i]['c'] for i in range(start, idx+1)) / (idx-start+1)

def td_signals(data, idx):
    """
    计算通达信主力监测器的核心信号
    返回: {'hold': bool, 'buy': bool, 'sell': bool, 'oversold': bool}
    """
    if idx < 35: return None
    
    c = data[idx]['c']; h = data[idx]['h']; l = data[idx]['l']; o = data[idx]['o']
    c1 = data[idx-1]['c']; c2 = data[idx-2]['c']
    
    # === 红色持股序列 VAR1~VARC ===
    # 简化: 12步交替模式检测
    hold = False
    # VAR1: C>Ref(C,1) AND C>Ref(C,2)
    v1 = (c > c1) and (c > c2)
    # VAR2: Ref(VAR1,1) AND C<=Ref(C,1) AND C>=Ref(C,2)
    c1_1 = data[idx-1]['c']; c2_1 = data[idx-2]['c']; c3_1 = data[idx-3]['c'] if idx>=3 else 0
    v1_prev = (c1 > c2_1) and (c1 > c3_1) if idx>=3 else False
    v2 = v1_prev and (c <= c1) and (c >= c2_1)
    
    # 简化: 只看近3天是否有持币信号(价格上涨通道)
    ma3 = td_ma(data, idx, 3)
    ma10 = td_ma(data, idx, 10)
    hold = (c > ma3 and ma3 > ma10)
    
    # === 青色观望序列 VARD~VAR18 ===
    wait = (c < ma3 or ma3 < ma10)
    
    # === 短买 VAR19 ===
    # VARD: C<Ref(C,1) AND C<Ref(C,2)
    vd = (c < c1) and (c < c2)
    vd_prev = (c1 < c2_1) and (c1 < c3_1) if idx>=3 else False
    v19 = vd_prev and v1  # 昨天是跌,今天是涨双确认
    
    # === 白色离场 VAR1A ===
    v1a = v1_prev and vd  # 昨天涨双确认,今天跌双确认
    
    # === 急速超跌 ===
    ma34 = td_ma(data, idx, 34)
    oversold = (c - ma34) / ma34 * 100 < -14
    
    # === 八因子评分 ===
    ma5 = td_ma(data, idx, 5); ma20 = td_ma(data, idx, 20); ma60 = td_ma(data, idx, 60)
    x1 = 20 if ma5 > ma10 else 0
    x2 = 10 if ma20 > ma60 else 0
    xx = x1 + x2  # KDJ/MACD/VOL/WINNER省略(需要额外数据)
    td_score = xx
    
    return {'hold': hold, 'buy': v19, 'sell': v1a, 'oversold': oversold, 'score': td_score}

def pks_v25(data_60d):
    """PKS v2.5 四参数评级"""
    cls = [d['c'] for d in data_60d]; bl = sum(cls)/len(cls)
    ph = max(d['h'] for d in data_60d); pl = min(d['l'] for d in data_60d)
    r1 = max((ph-bl)/bl, (bl-pl)/bl); r2 = min((ph-bl)/bl, (bl-pl)/bl)
    if r2 < 1e-8: return None
    g = math.degrees(math.atan((r1-r2)/(r1+r2)))
    h_val = 2*r1*r2/(r1+r2)
    u1,u2 = 1/r1,1/r2; z = (u1*u1+u2*u2)/(u1+u2)
    ar = math.atan(-u1*u2*(u2-u1)/(u1+u2))
    cv = (z*math.sqrt(2)/2)*math.tan(2*ar)
    return {'g':g, 'h':h_val, 'z':z, 'c':cv}

print('预取20只...', flush=True)
db = {}
for c,n in POOL:
    d = fetch(c)
    if d: db[c] = d

# 回测
td_buy = []; td_sell = []; td_oversold = []
pks_buy = []; pks_sell = []
baseline = []

for code in db:
    data = db[code]; n = len(data)
    
    # 池中位数
    pool_h = []; pool_z = []
    for i in range(60, n-20):
        w = data[i-60:i]; p = pks_v25(w)
        if p is None: continue
        pool_h.append(p['h']); pool_z.append(p['z'])
    if not pool_h: continue
    h_med = sum(pool_h)/len(pool_h); z_med = sum(pool_z)/len(pool_z)
    
    for i in range(60, n-20):
        w = data[i-60:i]
        p = pks_v25(w)
        if p is None: continue
        
        td = td_signals(data, i)
        if td is None: continue
        
        pn = data[i-1]['c']
        
        for hor, lb in [(5, '5d'), (10, '10d'), (20, '20d')]:
            fi = min(i+hor-1, n-1)
            if fi <= i: continue
            fwd = (data[fi]['c'] - pn) / pn * 100
            
            baseline.append((lb, fwd))
            
            # PKS 信号
            if p['g'] >= 20 and p['h'] >= h_med and p['z'] >= z_med and -1 <= p['c'] <= 3:
                pks_buy.append((lb, fwd))
            if p['g'] > 30 or p['c'] < -1 or p['c'] > 3:
                pks_sell.append((lb, fwd))
            
            # TD 信号
            if td['buy']:
                td_buy.append((lb, fwd))
            if td['sell']:
                td_sell.append((lb, fwd))
            if td['oversold']:
                td_oversold.append((lb, fwd))

# ── 输出 ──
print(f'\n{"="*60}')
print(f'  PKS v2.5 vs 通达信主力监测器 — 买卖信号质量')
print(f'{"="*60}')
print(f'  20只成长股 × 3年')

for hor in ['5d', '10d', '20d']:
    td_b = [f for lb,f in td_buy if lb==hor]
    td_s = [f for lb,f in td_sell if lb==hor]
    td_o = [f for lb,f in td_oversold if lb==hor]
    pk_b = [f for lb,f in pks_buy if lb==hor]
    pk_s = [f for lb,f in pks_sell if lb==hor]
    bl = [f for lb,f in baseline if lb==hor]
    
    print(f'\n  --- {hor} ---')
    def stat(name, lst, expect_sign='+'):
        if not lst: return
        m = sum(lst)/len(lst); wr = sum(1 for x in lst if x>0)/len(lst)*100
        ok = '✅' if (expect_sign=='+' and m>0) or (expect_sign=='-' and m<0) else '❌'
        print(f'  {name:<18} n={len(lst):<6} {m:+6.2f}% wr={wr:.0f}% {ok}')
    
    bl_m = sum(bl)/len(bl) if bl else 0
    print(f'  {"全量基准":<18} n={len(bl):<6} {bl_m:+6.2f}%')
    
    stat('TD 短买', td_b, '+')
    stat('PKS 买入(A+~A)', pk_b, '+')
    
    stat('TD 离场', td_s, '-')
    stat('PKS 卖出(X级)', pk_s, '-')
    stat('TD 超跌', td_o, '+')

# 汇总
print(f'\n{"="*60}')
print(f'  综合对比')
print(f'{"="*60}')

all_td_b = [f for _,f in td_buy]
all_pk_b = [f for _,f in pks_buy]
all_td_s = [f for _,f in td_sell]
all_pk_s = [f for _,f in pks_sell]

td_bm = sum(all_td_b)/len(all_td_b) if all_td_b else 0
pk_bm = sum(all_pk_b)/len(all_pk_b) if all_pk_b else 0
td_sm = sum(all_td_s)/len(all_td_s) if all_td_s else 0
pk_sm = sum(all_pk_s)/len(all_pk_s) if all_pk_s else 0

print(f'  {"":<20} {"样本":<8} {"期望":<10} {"方向":<6}')
print(f'  {"TD 短买":<20} {len(all_td_b):<8} {td_bm:+8.2f}% {"✅买后涨" if td_bm>0 else "❌买后跌"}')
print(f'  {"PKS 买入":<20} {len(all_pk_b):<8} {pk_bm:+8.2f}% {"✅买后涨" if pk_bm>0 else "❌买后跌"}')
print(f'  {"TD 离场":<20} {len(all_td_s):<8} {td_sm:+8.2f}% {"✅卖后跌" if td_sm<0 else "❌卖后涨"}')
print(f'  {"PKS 卖出":<20} {len(all_pk_s):<8} {pk_sm:+8.2f}% {"✅卖后跌" if pk_sm<0 else "❌卖后涨"}')

print(f'\n  买入质量: {"PKS" if pk_bm>td_bm else "TD"} 更好 ({pk_bm:+.2f}% vs {td_bm:+.2f}%)')
print(f'  卖出质量: {"PKS" if pk_sm>td_sm else "TD"} 更好 ({pk_sm:+.2f}% vs {td_sm:+.2f}%)')
print(f'  综合: {"PKS 全面胜出" if pk_bm>td_bm and pk_sm>td_sm else ("TD 全面胜出" if td_bm>pk_bm and td_sm>pk_sm else "各有优劣")}')
