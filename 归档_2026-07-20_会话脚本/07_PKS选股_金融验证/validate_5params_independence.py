"""五参数独立性检验 — 64只成长股 × 3年"""
import subprocess, math

NODE=r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK=r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

POOL=[('sh688012','中微'),('sh688536','芯源'),('sh688072','拓荆'),('sh688082','盛美'),
      ('sz300666','江丰'),('sh688200','华峰'),('sh688126','沪硅'),('sz002371','北华'),
      ('sh688008','澜起'),('sz300474','景嘉'),('sh688017','绿的'),('sh688160','步科'),
      ('sh688005','容百'),('sh688116','天奈'),('sz300750','宁德'),('sh688599','天合'),
      ('sh688303','大全'),('sh688185','康希'),('sh688180','君实'),('sz300759','康龙'),
      ('sh688202','美迪'),('sh688235','百济'),('sh688111','金山'),('sh688095','福昕'),
      ('sz300454','深信'),('sz300033','同花'),('sz300624','万兴'),('sz300124','汇川'),
      ('sz300450','先导'),('sz300760','迈瑞'),('sh688029','南微'),('sz300633','开立'),
      ('sz300206','理邦'),('sh688016','心脉'),('sz300529','健帆'),('sh688256','寒武'),
      ('sz300502','新易'),('sz300308','中际'),('sh603019','曙光'),('sh688390','固德'),
      ('sh688032','禾迈'),('sh688063','派能'),('sz300274','阳光'),('sh688036','传音'),
      ('sz002920','德赛'),('sh688208','道通'),('sz300748','金力'),('sz300012','华测'),
      ('sz300782','卓胜'),('sz300458','全志'),('sh688595','芯海'),('sz300413','芒果'),
      ('sz002624','完美'),('sz300113','顺网'),('sz300052','中青'),('sz300487','蓝晓'),
      ('sh688106','金宏'),('sz300596','利安'),('sh688550','瑞联'),('sz300661','圣邦'),
      ('sh688368','晶丰'),('sz300327','中颖')]

def fetch(code):
    r=subprocess.run([NODE,WSK,'kline',code,'--period','day','--limit','800'],
                    capture_output=True,text=True,timeout=60)
    if r.returncode: return []
    data=[]
    for l in r.stdout.strip().split('\n'):
        if not l.startswith('| ') or '---' in l: continue
        f=[x.strip() for x in l.split('|')]
        if len(f)<9: continue
        try: data.append({'d':f[1],'o':float(f[2]),'c':float(f[3]),'h':float(f[4]),'l':float(f[5])})
        except: continue
    data.reverse(); return data

def params(w):
    cs=[d['c'] for d in w]; bl=sum(cs)/len(cs)
    ph=max(d['h'] for d in w); pl=min(d['l'] for d in w)
    r1=max((ph-bl)/bl,(bl-pl)/bl); r2=min((ph-bl)/bl,(bl-pl)/bl)
    if r2<1e-8: return None
    g=math.degrees(math.atan((r1-r2)/(r1+r2)))
    h_val=2*r1*r2/(r1+r2)
    u1,u2=1/r1,1/r2; z=(u1*u1+u2*u2)/(u1+u2)
    ar=math.atan(-u1*u2*(u2-u1)/(u1+u2))
    ta=abs(math.tan(ar)); zm=2*math.sqrt(ta) if ta>0 else 0.001
    s=z/zm if zm>0 else 999
    cv=(z*math.sqrt(2)/2)*math.tan(2*ar)
    return {'g':g,'h':h_val,'z':z,'a':math.degrees(ar),'c':cv,'s':s,'v':max(r1,r2)}

print('预取64只...', flush=True)
db={}
for c,n in POOL:
    d=fetch(c)
    if d: db[c]=d

obs=[]
for c in db:
    d=db[c]; n=len(d)
    for i in range(60,n-20):
        w=d[i-60:i]; p=params(w)
        if p is None: continue
        pn=d[i-1]['c']; fi=min(i+19,n-1)
        obs.append({**p,'f':(d[fi]['c']-pn)/pn*100})

N=len(obs)
print(f'N={N}\n')

# 1. γ 单独
bins=[(0,5),(5,10),(10,15),(15,20),(20,25),(25,30),(30,99)]
print('=== 1. gamma 单独 ===')
for lo,hi in bins:
    it=[o for o in obs if lo<=o['g']<hi]
    if len(it)<50: continue
    m=sum(o['f'] for o in it)/len(it); w=sum(1 for o in it if o['f']>0)/len(it)*100
    print(f'  g[{lo},{hi}) n={len(it):<6} {m:+6.2f}% wr={w:.0f}%')

# 2. h x gamma
h_med=sum(o['h'] for o in obs)/N
print('\n=== 2. h x gamma (g>=15) ===')
for g_lo,g_hi in [(15,20),(20,25),(25,30),(30,99)]:
    lo_h=[o for o in obs if g_lo<=o['g']<g_hi and o['h']<h_med]
    hi_h=[o for o in obs if g_lo<=o['g']<g_hi and o['h']>=h_med]
    if len(lo_h)>20 and len(hi_h)>20:
        lm=sum(o['f'] for o in lo_h)/len(lo_h)
        hm_=sum(o['f'] for o in hi_h)/len(hi_h)
        print(f'  g{g_lo}-{g_hi}: small_h={lm:+.2f}% large_h={hm_:+.2f}% diff={hm_-lm:+.2f}%')

# 3. egg_safety x gamma
print('\n=== 3. egg_safety x gamma ===')
for g_lo,g_hi in [(15,20),(20,25),(25,30),(30,99)]:
    frag=[o for o in obs if g_lo<=o['g']<g_hi and o['s']<2]
    healthy=[o for o in obs if g_lo<=o['g']<g_hi and o['s']>=2]
    if len(frag)>20 and len(healthy)>20:
        fm=sum(o['f'] for o in frag)/len(frag)
        hm_=sum(o['f'] for o in healthy)/len(healthy)
        print(f'  g{g_lo}-{g_hi}: fragile={fm:+.2f}% healthy={hm_:+.2f}% diff={hm_-fm:+.2f}%')
    elif len(frag)>20:
        fm=sum(o['f'] for o in frag)/len(frag)
        print(f'  g{g_lo}-{g_hi}: fragile={fm:+.2f}% (healthy<20)')

# 4. c 分组 (高波)
print('\n=== 4. c 分组 (vol>=0.15) ===')
for lo,hi,lb in [(-99,-1,'c<-1'),(-1,0,'c[-1,0)'),(0,3,'c[0,3]'),(3,99,'c>3')]:
    it=[o for o in obs if o['v']>=0.15 and lo<=o['c']<hi]
    if len(it)>50:
        m=sum(o['f'] for o in it)/len(it); w=sum(1 for o in it if o['f']>0)/len(it)*100
        print(f'  {lb}: n={len(it):<6} {m:+6.2f}% wr={w:.0f}%')

# 5. |alpha|
print('\n=== 5. |alpha| 分组 ===')
for lo,hi in [(0,30),(30,60),(60,80),(80,90)]:
    it=[o for o in obs if lo<=abs(o['a'])<hi]
    if len(it)>50:
        m=sum(o['f'] for o in it)/len(it); w=sum(1 for o in it if o['f']>0)/len(it)*100
        print(f'  |a|[{lo},{hi}): n={len(it):<6} {m:+6.2f}% wr={w:.0f}%')

# 6. 三维最优组合
print('\n=== 6. 三维组合 top10 ===')
combos=[]
for g_lo,g_hi in [(15,20),(20,25),(25,30),(30,99)]:
    for hf in ['s','l']:
        for sf in ['f','h']:
            it=[o for o in obs if g_lo<=o['g']<g_hi]
            h_cond = (lambda x: x < h_med) if hf == 's' else (lambda x: x >= h_med)
            s_cond = (lambda x: x < 2) if sf == 'f' else (lambda x: x >= 2)
            it = [o for o in it if h_cond(o['h']) and s_cond(o['s'])]
            if len(it)<30: continue
            m=sum(o['f'] for o in it)/len(it)
            combos.append((g_lo,g_hi,hf,sf,len(it),m))
combos.sort(key=lambda x:-x[5])
for g_lo,g_hi,hf,sf,cn,cm in combos[:10]:
    print(f'  g[{g_lo},{g_hi}) h={hf} s={sf}: n={cn:<5} {cm:+.2f}%')

# gamma 最佳 vs 三维最佳
gb=[o for o in obs if 25<=o['g']<30]
gbm=sum(o['f'] for o in gb)/len(gb) if gb else 0
print(f'\n  gamma[25,30) alone: {gbm:+.2f}%')
if combos:
    print(f'  3D best: {combos[0][5]:+.2f}%  delta: {combos[0][5]-gbm:+.2f}%')

# 7. 总结：各参数独立贡献
print(f'\n{"="*55}')
print(f'  五参数独立贡献总结 (64只成长股, {N} obs)')
print(f'{"="*55}')
print(f'  {"参数":<12} {"均值(Base)":<12} {"最优子集":<12} {"提升":<8} {"结论":<10}')
# g
g_mid=[o for o in obs if 10<=o['g']<20]
g_hi=[o for o in obs if 25<=o['g']<30]
ga=sum(o['f'] for o in g_mid)/len(g_mid) if g_mid else 0
gb_=sum(o['f'] for o in g_hi)/len(g_hi) if g_hi else 0
print(f'  {"gamma":<12} {ga:+6.2f}%{"":>6} {gb_:+6.2f}%{"":>6} {gb_-ga:+6.2f}%  核心')
# h
h_lo=[o for o in obs if o['h']<h_med and o['g']>=20]
h_hi_=[o for o in obs if o['h']>=h_med and o['g']>=20]
ha=sum(o['f'] for o in h_lo)/len(h_lo) if h_lo else 0
hb=sum(o['f'] for o in h_hi_)/len(h_hi_) if h_hi_ else 0
print(f'  {"h":<12} {ha:+6.2f}%{"":>6} {hb:+6.2f}%{"":>6} {hb-ha:+6.2f}%  辅助')
# egg_safety
sa=[o for o in obs if o['s']<2 and o['v']>=0.2]
sb=[o for o in obs if o['s']>=2 and o['v']>=0.2]
sa_m=sum(o['f'] for o in sa)/len(sa) if sa else 0
sb_m=sum(o['f'] for o in sb)/len(sb) if sb else 0
print(f'  {"egg_safety":<12} {sa_m:+6.2f}%{"":>6} {sb_m:+6.2f}%{"":>6} {sb_m-sa_m:+6.2f}%  高波')
# c
ca=[o for o in obs if o['c']<0 and o['v']>=0.15]
cb=[o for o in obs if 0<=o['c']<=3 and o['v']>=0.15]
ca_m=sum(o['f'] for o in ca)/len(ca) if ca else 0
cb_m=sum(o['f'] for o in cb)/len(cb) if cb else 0
print(f'  {"c":<12} {ca_m:+6.2f}%{"":>6} {cb_m:+6.2f}%{"":>6} {cb_m-ca_m:+6.2f}%  周期')
# alpha
aa=[o for o in obs if abs(o['a'])<80]
ab=[o for o in obs if abs(o['a'])>=80]
aa_m=sum(o['f'] for o in aa)/len(aa) if aa else 0
ab_m=sum(o['f'] for o in ab)/len(ab) if ab else 0
print(f'  {"alpha":<12} {aa_m:+6.2f}%{"":>6} {ab_m:+6.2f}%{"":>6} {ab_m-aa_m:+6.2f}%  无')
