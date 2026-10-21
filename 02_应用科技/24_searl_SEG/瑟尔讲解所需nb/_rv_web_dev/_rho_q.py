# -*- coding: utf-8 -*-
"""ρ 上限对 q 的依赖（p=7 · g=6 七层）—— 找通项 ρ*(q) 的形状。"""
import json
import numpy as np
import _p7_solve as P


def rho_cap(p, g, q, it=11, lo=0.003, hi=0.40):
    best = lo
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        sc, _, _ = P.build(p, g, q, mid)
        r, _, _ = P.gap_ratio(sc, mid)
        if r > mid: best = mid; lo = mid
        else: hi = mid
    return best


rows = []
print('p=7 g=6（L0~L6 七层）')
print('  q     ρ上限     ρ/(1-q)    ρ(1+q)^2   1/(1+q)^2   绑定对')
for q in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45):
    rc = rho_cap(7, 6, q)
    sc, cut, tot = P.build(7, 6, q, rc)
    r0, info, _ = P.gap_ratio(sc, rc)
    rows.append(dict(q=q, rho=round(rc, 5), pair='L%s/L%s' % (info[0], info[1]),
                     a=round(rc / (1 - q), 5), b=round(rc * (1 + q) ** 2, 5),
                     c=round(1 / (1 + q) ** 2, 5)))
    print('  %.2f   %.5f   %.5f    %.5f     %.5f     L%s/L%s'
          % (q, rc, rc / (1 - q), rc * (1 + q) ** 2, 1 / (1 + q) ** 2, info[0], info[1]))
json.dump(rows, open('_rho_q.json', 'w'), ensure_ascii=False, indent=1)

qs = np.array([r['q'] for r in rows]); rs = np.array([r['rho'] for r in rows])
print()
print('拟合尝试（p=7, g=6）：')
for name, f in [('ρ = A/(1+q)^2', lambda q: 1 / (1 + q) ** 2),
                ('ρ = A(1-q)^B', lambda q: (1 - q) ** 1.0),
                ('ρ = A exp(-Bq)', lambda q: np.exp(-q)),
                ('ρ = A q^B', lambda q: q)]:
    X = f(qs)
    A = float((X @ rs) / (X @ X))
    pred = A * X
    err = np.abs(pred - rs) / rs * 100
    print('  %-18s A=%.4f  最大误差 %.1f%%  RMS %.1f%%' % (name, A, err.max(), np.sqrt((err**2).mean())))
