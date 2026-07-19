"""四系列交叉分析: Fibonacci | Prime | Lucas | 2^n"""
import numpy as np, math, os, json

this_dir = os.path.dirname(os.path.abspath(__file__) or '.')
pts = np.loadtxt(os.path.join(this_dir, 'droplet_invM_analytic.csv'), delimiter=',', skiprows=1)
N_half = len(pts) // 2; ux, uy = pts[:N_half, 0], pts[:N_half, 1]

def coprime(a, b): return math.gcd(a, b) == 1
def inv_cardioid(th):
    return 1.0 / (0.5 * np.exp(1j * th) - 0.25 * np.exp(2j * th))
def seg_dev(a, b):
    if a >= b: return 0.0, a
    md, mi = 0.0, a
    ax, ay = ux[a], uy[a]; bx, by = ux[b], uy[b]
    abx, aby = bx - ax, by - ay; ab2 = abx**2 + aby**2
    if ab2 < 1e-20: return 0.0, a
    for i in range(a, b + 1):
        t = max(0, min(1, ((ux[i] - ax) * abx + (uy[i] - ay) * aby) / ab2))
        d = np.hypot(ux[i] - (ax + t * abx), uy[i] - (ay + t * aby))
        if d > md: md, mi = d, i
    return md, mi

def seed_anc(max_period):
    anc = [0]
    for q in range(2, max_period + 1):
        for p in range(1, q):
            if coprime(p, q):
                th = 2 * np.pi * p / q
                ci = inv_cardioid(th)
                if 0 < th < np.pi and ci.imag <= 0:
                    anc.append(int(np.argmin(np.hypot(ux - ci.real, uy + ci.imag))))
    anc.append(N_half - 1)
    return sorted(set(anc))

def compute_seq(anc):
    k = list(anc); history = []
    while len(k) * 2 < 800:
        ki = sorted(k); wd, ws, worst_mi = 0, 0, 0
        for s in range(len(ki) - 1):
            d, mi = seg_dev(ki[s], ki[s + 1])
            if d > wd: wd, ws, worst_mi = d, s, mi
        history.append((len(k) * 2, wd))
        if wd < 5e-5: break
        k.append(worst_mi)

    inflections = []
    for i in range(5, len(history) - 5):
        b5, b0, b_p5 = history[i-5][1], history[i][1], history[i+5][1]
        sb, sa = (b5 - b0) / 5, (b0 - b_p5) / 5
        ratio = abs(sb / sa) if sa > 0 else 999
        if ratio > 3: inflections.append(history[i][0])

    if not inflections: return []
    major = [inflections[0]]
    for i in range(1, len(inflections)):
        if inflections[i] - inflections[i-1] > 2:
            major.append(inflections[i])
    return major

# ═══ 四系列定义 ═══
fib_set   = {1, 2, 3, 5, 8, 13, 21, 34, 55}
prime_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
lucas_set = {1, 2, 3, 4, 7, 11, 18, 29, 47}
pow2_set  = {2, 4, 8, 16, 32, 64}

# ═══ 扫描 period 2~15 所有 M ═══
print(f'{"period":>8s} | {"M":>3s} | {"φ(M)":>4s} | {"Fibo":>4s} {"Prime":>6s} {"Lucas":>5s} {"2^n":>4s}')
print('-' * 50)
period_map = {}
for mp in range(2, 16):
    anc = seed_anc(mp)
    M = len(anc)
    tags = []
    if M in fib_set: tags.append('Fibo')
    if M in prime_set: tags.append('Prime')
    if M in lucas_set: tags.append('Lucas')
    if M in pow2_set: tags.append('2^n')
    period_map[mp] = {'M': M, 'tags': tags, 'anc': anc}
    tags_str = (
        ('F' if M in fib_set else ' ').rjust(4) +
        ('P' if M in prime_set else ' ').rjust(6) +
        ('L' if M in lucas_set else ' ').rjust(5) +
        ('2^n' if M in pow2_set else ' ').rjust(4)
    )
    print(f'period 1-{mp:>2d} | {M:>3d} | {sum(1 for k in range(1,M) if math.gcd(k,M)==1):>4d} | {tags_str}')

# ═══ 对每种特殊M跑序列 ═══
print('\n' + '=' * 70)
for series_name, series_set in [('Fibonacci', fib_set), ('Prime', prime_set),
                                  ('Lucas', lucas_set), ('2^n', pow2_set)]:
    print(f'\n═══ {series_name} M = {sorted(series_set)[:8]} ═══')
    for mp, info in period_map.items():
        M = info['M']
        if M in series_set and M > 1:
            seq = compute_seq(info['anc'])
            if seq:
                n = len(seq)
                greedy = [s - M*2 for s in seq]
                diffs = np.diff(seq)
                growth = [seq[i]/max(1,seq[i-1]) for i in range(1, len(seq))]
                avg_g = np.mean(growth) if growth else 0
                phi = (1+math.sqrt(5))/2

                extra = ''
                # Fibonacci: 检查 F[n] ≈ F[n-1]+F[n-2]
                if series_name == 'Fibonacci' and n >= 3:
                    r = [seq[i]/(seq[i-1]+seq[i-2]) for i in range(2,n)]
                    avg_r = np.mean(r)
                    extra = f' | F-ratio={avg_r:.3f} (ideal=1.0)'
                # Prime: 间距中素数占比
                if series_name == 'Prime':
                    p_in_diffs = sum(1 for d in diffs if d in prime_set)
                    extra = f' | Δ中素数={p_in_diffs}/{len(diffs)}'
                # Lucas: 增长因子 vs φ
                if series_name == 'Lucas':
                    extra = f' | growth={avg_g:.3f} (φ={phi:.3f})'
                # 2^n: 间距中2的幂次数量
                if series_name == '2^n':
                    p2_count = sum(1 for d in diffs if d & (d-1) == 0)  # 2的幂
                    extra = f' | Δ中2^n={p2_count}/{len(diffs)}'

                print(f'  M={M:>3d} ({len(seq)}项) 增长={avg_g:.3f}{extra}')
                print(f'      seq[:6]: {seq[:6]}')
                print(f'      Δ[:8]:   {list(diffs[:8])}')
                print(f'      纯增量[:6]: {greedy[:6]}')
            else:
                print(f'  M={M:>3d}: 无拐点')

# ═══ 跨系列比较 M=3 (所有系列都含) ═══
print('\n' + '=' * 70)
print('跨系列对比: M=3 (Fibo ∩ Prime ∩ Lucas ∩ 2^1+1)')
print('=' * 70)
for mp, info in period_map.items():
    if info['M'] == 3:
        seq = compute_seq(info['anc'])
        print(f'  period 1-{mp}, M=3: seq={seq[:6]}... Δ={list(np.diff(seq)[:8])}')
        print(f'    但 M=3 对所有系列都一样——种子固定')

# 结论
print('\n' + '=' * 70)
print('结论:')
print('=' * 70)
all_special = {}
for mp, info in period_map.items():
    M = info['M']
    for tag in info['tags']:
        all_special.setdefault(tag, []).append(M)

for tag, mlist in all_special.items():
    print(f'  {tag}: M ∈ {sorted(set(mlist))}')

print('\n关键: 自然M由Farey分数决定, 而非数列——')
print('特殊数列M值恰好出现是巧合还是深层共鸣?')
print('如果是共鸣: M = 1 + Σ_{k=2}^{n} ⌈φ(k)/2⌉ 的值集')
print('与 Fibonacci/Prime/Lucas 的交集有密度的数学含义')
