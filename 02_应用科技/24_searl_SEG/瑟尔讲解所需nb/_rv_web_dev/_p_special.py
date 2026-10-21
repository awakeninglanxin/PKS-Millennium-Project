# -*- coding: utf-8 -*-
"""挂曲线（attach='curve' 贴管壁）+ L0~L6 七层：对 p=2..8 各自求「最粗又不相交」的 ρ，
看 p=7 是否在 ρ_max(p) 这条曲线上有极值。

口径与页面逐字一致：prunePlan 剪枝、tau=2π/(|n|·p)·i、u1=B·sC / v1=(N×B)·sC、nest 公转。
q 的取法：q = kq · sin(π/p)（kq=0.92 是页面「最优七级」用的比例；kq=0.6 作为对照）。
"""
import json
import sys
import numpy as np
import _p7_solve as P

G = 6                     # L0~L6 共 7 层
NW, KW, ND, KD = 5, 1680, 1, 7


def rho_cap(p, g, q, it=9, lo=0.004, hi=0.40):
    """静止相位下全对上限（Δmin=0 的零点）。挂曲线时 d_ij 也随 ρ 变 ⇒ 每档都要重建。"""
    best = lo
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        sc, _, _ = P.build(p, g, q, mid)
        r, _, _ = P.gap_ratio(sc, mid)
        if r > mid:
            best = mid; lo = mid
        else:
            hi = mid
    return best


rows = []
for p in [2, 3, 4, 5, 6, 7, 8]:
    sp = np.sin(np.pi / p)
    for kq in (0.92, 0.60):
        q = kq * sp
        rc = rho_cap(p, G, q)
        sc, cut, tot = P.build(p, G, q, rc)
        r0, info, pairs = P.gap_ratio(sc, rc)
        rows.append(dict(p=p, g=G, kq=kq, q=round(q, 4), sinpi=round(sp, 4),
                         rings_theory=int(sum(p ** l for l in range(G + 1))),
                         rings_draw=tot, cut=cut, rhoCap=round(rc, 5),
                         ratio=round(r0, 5), bind='L%s/L%s' % (info[0], info[1]),
                         rhoOverQ=round(rc / q, 4)))
        print('p=%d kq=%.2f q=%.4f sin(π/p)=%.4f | 环数理论 %6d 实绘 %5d | ρ上限 %.5f （ρ/q=%.4f）'
              % (p, kq, q, sp, rows[-1]['rings_theory'], tot, rc, rc / q))
json.dump(rows, open('_p_special.json', 'w'), ensure_ascii=False, indent=1)
print('→ _p_special.json')
