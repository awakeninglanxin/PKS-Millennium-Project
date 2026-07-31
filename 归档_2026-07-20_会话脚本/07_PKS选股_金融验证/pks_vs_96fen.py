#!/usr/bin/env python3
"""PKS vs 96fen 算法竞赛 — 历史选股回测"""
import subprocess, math

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

REPORTS = {
    '2026-06-26': 9, '2026-06-29': 15, '2026-07-01': 10, '2026-07-02': 16,
}

def fetch(code):
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', '200'],
                      capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or len(r.stdout) < 200: return None
    data = []; dmap = {}
    # Data is newest-first: data[0]=today, data[-1]=oldest
    for line in r.stdout.strip().split('\n'):
        if not line.startswith('| ') or '---' in line: continue
        fields = [x.strip() for x in line.split('|')]
        if len(fields) < 9: continue
        try:
            data.append({'d': fields[1], 'o': float(fields[2]), 'c': float(fields[3]),
                        'h': float(fields[4]), 'l': float(fields[5])})
            dmap[fields[1]] = len(data) - 1
        except ValueError: continue
    return data, dmap

results = []
for code in sorted(set(c for v in [
    ['sh688578','sh603256','sh603259','sh605020','sz000987','sz001309','sz002517','sz002558','sz301345'],
    ['sh600770','sh603256','sh603259','sh603444','sh603929','sh605020','sh688578','sz000987','sz001270','sz001309','sz002517','sz002558','sz002602','sz002668','sz301345'],
    ['sh603259','sh603379','sh603444','sh688336','sz000792','sz002415','sz002558','sz002653','sz300975','sz301345'],
    ['sh603259','sh603444','sh688331','sh688336','sh688525','sz000792','sz000987','sz001270','sz001309','sz002517','sz002555','sz002558','sz002602','sz002653','sz300043','sz300573'],
] for c in v)):
    fetched = fetch(code)
    if not fetched: 
        print(f'  {code}: FAIL')
        continue
    data, dmap = fetched
    print(f'  {code}: {len(data)}d {data[-1]["d"]}~{data[0]["d"]}')
    
    for date_str, nstock in REPORTS.items():
        if date_str not in dmap: continue
        idx = dmap[date_str]
        if idx + 60 > len(data): continue  # need 60 days prior
        
        w = data[idx:idx+60]  # newest-first: idx=report_date, idx+60=60days_prior
        w.reverse()  # Make chronological: oldest→newest
        cls = [d['c'] for d in w]; bl = sum(cls)/len(cls)
        ph = max(d['h'] for d in w); pl = min(d['l'] for d in w)
        r1 = max((ph-bl)/bl, (bl-pl)/bl); r2 = min((ph-bl)/bl, (bl-pl)/bl)
        if r2 < 1e-8: continue
        
        g = math.degrees(math.atan((r1-r2)/(r1+r2)))
        u1, u2 = 1/r1, 1/r2
        z = (u1*u1+u2*u2)/(u1+u2)
        ar = math.atan(-u1*u2*(u2-u1)/(u1+u2))
        tana = abs(math.tan(ar))
        z_min = 2*math.sqrt(tana) if tana > 0 else 0.001
        safety = z/z_min if z_min > 0 else 999
        c_val = (z*math.sqrt(2)/2)*math.tan(2*ar)
        
        if g > 30 or c_val < -1 or c_val > 3: gd = 'X'
        elif g >= 20: gd = 'A'
        elif g >= 10: gd = 'B'
        elif safety >= 2: gd = 'C'
        else: gd = 'D'
        
        pn = data[idx-1]['c']
        for hor in [5, 10, 20]:
            fi = min(idx+hor-1, len(data)-1)
            if fi <= idx: continue
            results.append({'gd': gd, 'hor': hor, 'f': (data[fi]['c']-pn)/pn*100})

N = len(results)
if N == 0:
    print('\nNO RESULTS')
    exit(1)

print(f'\n{"="*45}')
print(f'  96fen裸选 vs PKS增强 (N={N})')
print(f'{"="*45}')

for hor in [5, 10, 20]:
    ai = [r for r in results if r['hor']==hor]
    ab = [r for r in ai if r['gd'] in ('A','B')]
    dx = [r for r in ai if r['gd'] in ('D','X')]
    am = sum(r['f'] for r in ai)/len(ai); aw = sum(1 for r in ai if r['f']>0)/len(ai)*100
    gm = sum(r['f'] for r in ab)/len(ab) if ab else 0; gw = sum(1 for r in ab if r['f']>0)/len(ab)*100 if ab else 0
    xm = sum(r['f'] for r in dx)/len(dx) if dx else 0
    
    print(f'\n  --- {hor}d (n={len(ai)}) ---')
    for gd in 'ABCDX':
        it = [r for r in ai if r['gd']==gd]
        if not it: continue
        rr = [r['f'] for r in it]; m = sum(rr)/len(rr); w = sum(1 for x in rr if x>0)/len(rr)*100
        print(f'  {gd}: n={len(it):<4} {m:+6.2f}% win={w:.0f}%')
    
    print(f'  {"96fen ALL":<8} n={len(ai):<4} {am:+6.2f}% win={aw:.0f}%')
    print(f'  {"PKS A+B":<8} n={len(ab):<4} {gm:+6.2f}% win={gw:.0f}%')
    print(f'  >> 超额: {gm-am:+.2f}% | A+B vs D+X: {gm-xm:+.2f}%')
