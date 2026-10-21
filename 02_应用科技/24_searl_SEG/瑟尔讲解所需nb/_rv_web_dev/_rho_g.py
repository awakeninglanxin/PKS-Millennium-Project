# -*- coding: utf-8 -*-
"""ρ 上限到底由谁决定：固定 p=7、q=0.30，扫层数 g=1..7（L0~Lg）。
若 ρ*(g) 与 p 无关、只随层数走 ⇒ 通项里 p 只通过 sin(π/p) 进兄弟约束，跨层那一条是普适的。
"""
import _p7_solve as P

Q = 0.30


def rho_cap(p, g, q, it=10, lo=0.003, hi=0.40):
    best = lo
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        sc, _, _ = P.build(p, g, q, mid)
        r, _, _ = P.gap_ratio(sc, mid)
        if r > mid: best = mid; lo = mid
        else: hi = mid
    return best


print('p=7 q=%.2f —— 只改层数 g' % Q)
print(' g  层数  环数(实绘)  ρ上限    汇总 Σq^k   ρ*/q^g   绑定对')
for g in range(1, 8):
    rc = rho_cap(7, g, Q)
    sc, cut, tot = P.build(7, g, Q, rc)
    r0, info, _ = P.gap_ratio(sc, rc)
    ssum = sum(Q ** k for k in range(g + 1))
    print(' %d   %d     %5d      %.5f   %.4f     %.4f    L%s/L%s'
          % (g, g + 1, tot, rc, ssum, rc / Q ** g, info[0], info[1]))
print()
print('对照：同样 q=0.30 换 p（g=6 固定）')
print(' p  sin(π/p)  sin/q   ρ上限    ρ*/sin(π/p)')
import numpy as np
for p in (3, 5, 6, 7, 8):
    rc = rho_cap(p, 6, Q)
    sp = np.sin(np.pi / p)
    print(' %d   %.4f    %.4f   %.5f   %.4f' % (p, sp, sp / Q, rc, rc / sp))
