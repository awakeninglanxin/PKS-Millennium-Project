"""PKS v2.4 第四批验证 — 软件/制造/材料/器械成长池"""
import subprocess, math
from collections import defaultdict

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

# 第四批：软件/高端制造/新材料/医疗器械（全新，与v1-v3不重叠）
POOL = [
    # 计算机软件/SaaS
    ('sh688111','金山办公'),('sh688095','福昕软件'),('sz300454','深信服'),
    ('sz300033','同花顺'),('sz300624','万兴科技'),('sh688568','中科星图'),
    # 高端制造/自动化
    ('sh688017','绿的谐波'),('sh688160','步科股份'),('sz300124','汇川技术'),
    ('sz300450','先导智能'),('sz002747','埃斯顿'),('sz300024','机器人'),
    # 新材料/化工
    ('sh688116','天奈科技'),('sz300782','卓胜微'),('sz300408','三环集团'),
    ('sz300285','国瓷材料'),('sh688005','容百科技'),
    # 医疗器械
    ('sz300760','迈瑞医疗'),('sh688029','南微医学'),('sz300633','开立医疗'),
    ('sz300206','理邦仪器'),('sh688016','心脉医疗'),('sz300529','健帆生物'),
    # 数据中心/云计算
    ('sh688256','寒武纪'),('sz300502','新易盛'),('sz300308','中际旭创'),
    ('sh603019','中科曙光'),
]

def raw_fetch(code, limit=800):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode: return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        f = [x.strip() for x in line.split('|')]
        if len(f) < 9: continue
        try: data.append({'d':f[1],'o':float(f[2]),'c':float(f[3]),'h':float(f[4]),'l':float(f[5])})
        except: continue
    data.reverse(); return data

def fetch_close(code, limit=800):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode: return []
    data = []
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        f = [x.strip() for x in line.split('|')]
        if len(f) < 9: continue
        try: data.append({'d':f[1],'c':float(f[3])})
        except: continue
    data.reverse(); return data

def pks_v24(w):
    cls=[d['c'] for d in w]; bl=sum(cls)/len(cls)
    ph=max(d['h'] for d in w); pl=min(d['l'] for d in w)
    r1=max((ph-bl)/bl,(bl-pl)/bl); r2=min((ph-bl)/bl,(bl-pl)/bl)
    if r2<1e-8: return None
    g=math.degrees(math.atan((r1-r2)/(r1+r2)))
    u1,u2=1/r1,1/r2; z=(u1*u1+u2*u2)/(u1+u2)
    ar=math.atan(-u1*u2*(u2-u1)/(u1+u2))
    tana=abs(math.tan(ar)); zm=2*math.sqrt(tana) if tana>0 else 0.001
    s=z/zm if zm>0 else 999
    cv=(z*math.sqrt(2)/2)*math.tan(2*ar)
    h_val=2*r1*r2/(r1+r2)
    if g>30 or cv<-1 or cv>3: gd='X'
    elif g>=20: gd='A'
    elif g>=10: gd='B'
    elif s>=2: gd='C'
    else: gd='D'
    return {'g':g,'h':h_val,'s':s,'c':cv,'gd':gd}

def regime(mkt,i):
    if i<60: return None
    c0=mkt[i]['c']; c60=mkt[i-60]['c']
    c20=mkt[i-20]['c'] if i>=20 else c60
    ma60=sum(d['c'] for d in mkt[i-60:i])/60
    p60=(c0-c60)/c60*100; p20=(c0-c20)/c20*100
    if p60>10 and c0>ma60*1.03: return 'BULL'
    if p60<-8: return 'BEAR'
    if abs(p20)<5 and abs(c0/ma60-1)<.05: return 'CHOP'
    if p60>0 and c0>ma60: return 'BIAS_UP'
    return 'BIAS_DOWN'

# ── 1. 大盘 ──
print('大盘...', end=' ', flush=True)
mkt=fetch_close('sh000300',800)
if not mkt: print('FAIL'); exit()
mm={d['d']:i for i,d in enumerate(mkt)}
print(f'{len(mkt)}天')

# ── 2. 股票 ──
print(f'预取 {len(POOL)} 只...', flush=True)
db={}
for code,name in POOL:
    d=raw_fetch(code,800)
    if d and len(d)>=80:
        db[code]=d
        print(f'  {name}: {len(d)}天', flush=True)

# ── 3. 回测 ──
print(f'回测 {len(db)} 只...', flush=True)
R={r:{'pk':[],'rt':[],'al':[]} for r in ['BULL','BIAS_UP','CHOP','BIAS_DOWN','BEAR']}

for code in db:
    data=db[code]; n=len(data)
    for i in range(60,n-20):
        dt=data[i]['d']
        if dt not in mm: continue
        mi=mm[dt]; rg=regime(mkt,mi)
        if rg is None: continue
        w=data[i-60:i]; p=pks_v24(w)
        if p is None: continue
        pn=data[i-1]['c']; fi=min(i+19,n-1)
        fwd=(data[fi]['c']-pn)/pn*100
        R[rg]['al'].append(fwd)
        if p['gd'] in ('A','B'): R[rg]['pk'].append(fwd)
        # 路由
        if rg=='BULL': rs=p['gd'] in ('A','B','C')
        elif rg=='BEAR': rs=p['gd']=='A'
        elif rg=='CHOP': rs=p['gd'] in ('A','B')
        elif rg=='BIAS_UP': rs=p['gd'] in ('A','B','C')
        else: rs=p['gd']=='A'
        if rs: R[rg]['rt'].append(fwd)

# ── 4. 输出 ──
total=sum(len(v['al']) for v in R.values())
lb={'BULL':'🐂牛','BIAS_UP':'📈偏多','CHOP':'↔️震','BIAS_DOWN':'📉偏空','BEAR':'🐻熊'}
print(f'\n{"="*62}')
print(f'  PKS v2.4 验证 v4 — 软件/制造/材料/器械 成长池')
print(f'{"="*62}')
print(f'  {len(db)}只 | {total}观测\n')
print(f'  {"环境":<10}{"样本":<8}{"PKS":<10}{"路由":<10}{"全量":<10}{"PKSvs全":<10}{"PKvs路":<10}')
print(f'  {"-"*10}{"-"*8}{"-"*10}{"-"*10}{"-"*10}{"-"*10}{"-"*10}')
ap=[]; ar=[]; aa=[]
for rg in ['BULL','BIAS_UP','CHOP','BIAS_DOWN','BEAR']:
    rr=R[rg]
    if not rr['al']: continue
    am=sum(rr['al'])/len(rr['al'])
    pm=sum(rr['pk'])/len(rr['pk']) if rr['pk'] else 0
    rm=sum(rr['rt'])/len(rr['rt']) if rr['rt'] else 0
    print(f'  {lb[rg]:<10}{len(rr["al"]):<8}{pm:+8.2f}%{rm:+8.2f}%{am:+8.2f}%{pm-am:+8.2f}%{pm-rm:+8.2f}%')
    ap.extend(rr['pk']); ar.extend(rr['rt']); aa.extend(rr['al'])

tp=sum(ap)/len(ap) if ap else 0; tr=sum(ar)/len(ar) if ar else 0
ta=sum(aa)/len(aa) if aa else 0
wp=sum(1 for x in ap if x>0)/len(ap)*100 if ap else 0
wr=sum(1 for x in ar if x>0)/len(ar)*100 if ar else 0
wa=sum(1 for x in aa if x>0)/len(aa)*100 if aa else 0

print(f'\n  {"汇总":<10}{total:<8}{tp:+8.2f}%{tr:+8.2f}%{ta:+8.2f}%{tp-ta:+8.2f}%{tp-tr:+8.2f}%')
print(f'  {"胜率":<10}{"":<8}{wp:7.1f}%{wr:7.1f}%{wa:7.1f}%')

# ── γ分层 ──
print(f'\n  γ分层(20d):')
for lo,hi in [(0,5),(5,10),(10,15),(15,20),(20,25),(25,30),(30,99)]:
    it=[]; pk=[]
    for code in db:
        data=db[code]; n=len(data)
        for i in range(60,n-20):
            w=data[i-60:i]; p=pks_v24(w)
            if p is None: continue
            if not (lo<=p['g']<hi): continue
            pn=data[i-1]['c']; fi=min(i+19,n-1)
            fwd=(data[fi]['c']-pn)/pn*100
            it.append(fwd)
            if p['gd'] in ('A','B'): pk.append(fwd)
    if len(it)<30: continue
    m=sum(it)/len(it); w=sum(1 for x in it if x>0)/len(it)*100
    pm=sum(pk)/len(pk) if pk else 0
    print(f'  [{lo},{hi}) n={len(it):<6} all={m:+5.2f}% wr={w:.0f}% pk={pm:+5.2f}%')

# ── 四轮对比 ──
print(f'\n{"="*62}')
print(f'  四轮总对比')
print(f'{"="*62}')
pools_info = [
    ('v1','96fen成长(游戏/芯片)', 28, '+3.36%','+2.13%','+2.38%','PKS'),
    ('v2','消费/新能源/医药混合', 26, '+0.69%','+0.53%','+0.93%','全量'),
    ('v3','半导体/AI/军工', 27, '+3.02%','+2.55%','+2.07%','PKS'),
]
n4=str(len(db)); p4tp=f'{tp:+7.2f}%'; p4tr=f'{tr:+7.2f}%'; p4ta=f'{ta:+7.2f}%'
b4='PKS' if tp>=tr and tp>=ta else ('路由' if tr>=ta else '全量')
print(f'  {"轮":<5}{"池型":<22}{"只":<5}{"PKS":<10}{"路由":<10}{"全量":<10}{"最优":<6}')
for vn,pt,n,pl,rl,al,bs in pools_info:
    print(f'  {vn:<5}{pt:<22}{n:<5}{pl:<10}{rl:<10}{al:<10}{bs:<6}')
print(f'  {"v4":<5}{"软件/制造/器械/云计算":<22}{n4:<5}{p4tp:<10}{p4tr:<10}{p4ta:<10}{b4:<6}')

if tp>=tr and tp>=ta:
    print(f'\n  ✅ PKS v2.4 最优: 四轮中 3/4 胜出（纯成长池）')
elif tr>=ta:
    print(f'\n  ⚠️ 智能路由最优')
else:
    print(f'\n  ⚠️ 全量最优')
