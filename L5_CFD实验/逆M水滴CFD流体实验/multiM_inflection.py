"""多种子规模拐点序列对比 — 通项公式探索"""
import numpy as np, math, os, json

this_dir = os.path.dirname(os.path.abspath(__file__))
pts = np.loadtxt(os.path.join(this_dir, 'droplet_invM_analytic.csv'), delimiter=',', skiprows=1)
N_half = len(pts) // 2
ux, uy = pts[:N_half, 0], pts[:N_half, 1]
D = np.ptp(ux)

def coprime(a, b): return math.gcd(a, b) == 1

def inv_cardioid(th):
    return 1.0 / (0.5 * np.exp(1j * th) - 0.25 * np.exp(2j * th))

def seg_dev(a, b):
    if a >= b: return 0.0, a
    md, mi = 0.0, a
    ax, ay = ux[a], uy[a]
    bx, by = ux[b], uy[b]
    abx, aby = bx - ax, by - ay
    ab2 = abx**2 + aby**2
    if ab2 < 1e-20: return 0.0, a
    for i in range(a, b + 1):
        t = max(0, min(1, ((ux[i] - ax) * abx + (uy[i] - ay) * aby) / ab2))
        d = np.hypot(ux[i] - (ax + t * abx), uy[i] - (ay + t * aby))
        if d > md: md, mi = d, i
    return md, mi

def compute_inflections(max_period, slope_thresh=3, max_pts=800):
    """对给定 max_period 生成 Farey 种子, 运行贪婪, 提取拐点"""
    anc_idx = [0]
    for q in range(2, max_period + 1):
        for p in range(1, q):
            if coprime(p, q):
                th = 2 * np.pi * p / q
                ci = inv_cardioid(th)
                if 0 < th < np.pi and ci.imag <= 0:
                    anc_idx.append(int(np.argmin(np.hypot(ux - ci.real, uy + ci.imag))))
    anc_idx.append(N_half - 1)
    anc_idx = sorted(set(anc_idx))
    n0 = len(anc_idx)

    k = list(anc_idx)
    history = []
    while len(k) * 2 < max_pts and len(k) * 2 < N_half:
        ki = sorted(k)
        wd, ws, worst_mi = 0, 0, 0
        for s in range(len(ki) - 1):
            d, mi = seg_dev(ki[s], ki[s + 1])
            if d > wd: wd, ws, worst_mi = d, s, mi
        ga, gb = ki[ws], ki[ws + 1]
        history.append((len(k) * 2, wd, ga, gb, gb - ga))
        if wd < 5e-5: break
        k.append(worst_mi)

    # 拐点提取
    all_inf = []
    for i in range(5, len(history) - 5):
        b5 = history[i - 5][1]
        b0 = history[i][1]
        b_p5 = history[i + 5][1]
        sb = (b5 - b0) / 5
        sa = (b0 - b_p5) / 5
        ratio = abs(sb / sa) if sa > 0 else 999
        if ratio > slope_thresh:
            all_inf.append(history[i][0])

    # 去除微调对
    if not all_inf:
        return n0, [], history
    major = [all_inf[0]]
    for i in range(1, len(all_inf)):
        if all_inf[i] - all_inf[i - 1] > 2:
            major.append(all_inf[i])

    return n0, major, history


# ═══ 运行 M=6,7,8,9,10,11 ═══
print('=' * 72)
print(f'多种子规模拐点序列对比 (slope_thresh=3)')
print('=' * 72)

results = {}
for mp in [6, 7, 8, 9, 10, 11]:
    n0, seq, hist = compute_inflections(mp, max_pts=1000)
    greedy = [n - n0 * 2 for n in seq]
    results[mp] = {
        'period': mp,
        'seeds': n0,
        'seed_vertices': n0 * 2,
        'total_sequence': seq,
        'greedy_sequence': greedy,
        'num_terms': len(seq),
        'history': hist,
    }
    print(f'\nperiod 1-{mp}: {n0} seeds ({n0*2} vertices)')
    print(f'  顶点序列 ({len(seq)}项): {seq[:8]}{"..." if len(seq)>8 else ""}')
    print(f'  纯增量: {greedy[:8]}{"..." if len(greedy)>8 else ""}')

# ═══ 嵌套验证 ═══
print('\n' + '=' * 72)
print('嵌套性验证: I_M ⊂ I_{M+1} ?')
print('=' * 72)
for mp1, mp2 in [(6, 7), (7, 8), (8, 9), (9, 10)]:
    s1 = set(results[mp1]['total_sequence'])
    s2 = set(results[mp2]['total_sequence'])
    overlap = s1 & s2
    print(f'  M={mp1} vs M={mp2}: 交集={len(overlap)}/{len(s1)} ({len(overlap)/len(s1)*100:.0f}%)')

# ═══ 第1个拐点对比 ═══
print('\n' + '=' * 72)
print('首拐点与初始偏差对比')
print('=' * 72)
for mp in [6, 7, 8, 9, 10, 11]:
    r = results[mp]
    n_first = r['total_sequence'][0] if r['total_sequence'] else None
    # 找首个拐点对应的dev
    hist = r['history']
    first_dev = None
    if n_first:
        first_dev = hist[n_first // 2 - r['seeds'] - 1][1] if n_first // 2 > r['seeds'] else hist[0][1]
    print(f'  M={r["seeds"]}: first_inf={n_first}, dev={first_dev:.5f}' if first_dev else f'  M={r["seeds"]}: 无拐点')

# ═══ 通项公式验证 ═══
print('\n' + '=' * 72)
print('通项公式验证: gap_weight = L * sqrt(kappa)')
print('=' * 72)

# 对M=8 (12 seeds), 列出每个gap的权重
mp = 8
r = results[mp]
n0 = r['seeds']

# 重建种子锚点
anc_idx = [0]
for q in range(2, mp + 1):
    for p in range(1, q):
        if coprime(p, q):
            th = 2 * np.pi * p / q
            ci = inv_cardioid(th)
            if 0 < th < np.pi and ci.imag <= 0:
                anc_idx.append(int(np.argmin(np.hypot(ux - ci.real, uy + ci.imag))))
anc_idx.append(N_half - 1)
anc_idx = sorted(set(anc_idx))

# 算曲率
def curvature(idx):
    if idx < 2 or idx >= N_half - 2: return 0
    x1, x2, x3 = ux[idx - 1], ux[idx], ux[idx + 1]
    y1, y2, y3 = uy[idx - 1], uy[idx], uy[idx + 1]
    a = np.hypot(x2 - x1, y2 - y1)
    b = np.hypot(x3 - x2, y3 - y2)
    c = np.hypot(x3 - x1, y3 - y1)
    s = (a + b + c) / 2
    area = np.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))
    if a * b * c < 1e-20: return 0
    return 4 * area / (a * b * c)

gap_weights = []
for s in range(n0 - 1):
    a, b = anc_idx[s], anc_idx[s + 1]
    if b <= a: continue
    L = b - a
    kappa_sum = sum(curvature(i) for i in range(a, b + 1))
    avg_kappa = kappa_sum / (L + 1e-10)
    w = L * np.sqrt(avg_kappa)  # 权重
    gap_weights.append((a, b, L, avg_kappa, w))

# 排序看哪个gap最先填满
gap_weights.sort(key=lambda x: -x[4])
print(f'  {"gap":>12s}  {"len":>5s}  {"avg_kappa":>10s}  {"weight":>10s}')
print('  ' + '-' * 42)
for a, b, L, k, w in gap_weights[:6]:
    print(f'  [{a:>4d}..{b:<4d}] {L:>5d}  {k:>10.4f}  {w:>10.2f}')

# ═══ 保存 ═══
out = {str(k): {
    'seeds': v['seeds'],
    'seed_vertices': v['seed_vertices'],
    'total_sequence': v['total_sequence'],
    'greedy_sequence': v['greedy_sequence'],
    'num_terms': v['num_terms'],
} for k, v in results.items()}

with open(os.path.join(this_dir, 'multiM_inflections.json'), 'w') as f:
    json.dump(out, f, indent=2)
print(f'\n💾 已保存 multiM_inflections.json')
print('完成!')
