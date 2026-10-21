# -*- coding: utf-8 -*-
"""对每个 p 求「q 扫一遍能拿到的最粗 ρ」—— 只有 max_q ρ_cap(p,q) 才是这个 p 的真实能力。
公平比较的关键：q 不能都取 kq·sin(π/p)（q 大时层级不缩，p 小的会退化）。
"""
import json
import numpy as np
import _p7_solve as P

G = 6


def rho_cap(p, g, q, it=6, lo=0.003, hi=0.40):
    best = lo
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        sc, _, _ = P.build(p, g, q, mid)
        r, _, _ = P.gap_ratio(sc, mid)
        if r > mid: best = mid; lo = mid
        else: hi = mid
    return best


out = []
for p in [2, 3, 4, 5, 6, 7, 8]:
    sp = np.sin(np.pi / p)
    qs = sorted(set([round(k * sp, 4) for k in (0.35, 0.5, 0.65, 0.8, 0.92)] +
                    [0.30, 0.40, 0.50]))
    qs = [q for q in qs if 0.05 < q <= sp + 1e-9]
    best = None
    for q in qs:
        rc = rho_cap(p, G, q)
        tag = ''
        if best is None or rc > best[1]:
            best = (q, rc); tag = ' ★'
        print('p=%d q=%.4f  ρ上限 %.5f  ρ/q=%.4f%s' % (p, q, rc, rc / q, tag))
    out.append(dict(p=p, sinpi=round(sp, 4), qBest=round(best[0], 4), rhoBest=round(best[1], 5),
                    qs=[round(x, 4) for x in qs]))
    print('  ⇒ p=%d 最优 q=%.4f  ρ=%.5f  (ρ/q=%.4f)' % (p, best[0], best[1], best[1] / best[0]))
    print()
json.dump(out, open('_p_best.json', 'w'), ensure_ascii=False, indent=1)
print('→ _p_best.json')
