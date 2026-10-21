# -*- coding: utf-8 -*-
"""p=7 / g=7 / a=1 在「整圈 nest 公转（mix=1、摆幅 180）」下找不穿的 (q, rho)。

与页面逐字同口径，四件事必须一致：
  ① prunePlan 剪枝（MAXDRAW=6000）—— p=7,g=7 理论 960800 只，实际只画 1772 只
  ② 落点 tau = 2π/(|n|·p)·i （nW=5 时 2π/35）
  ③ 贴管壁挂法 u1 = B·sC, v1 = (N×B)·sC
  ④ revNest：L(k) 绕自己父环的中轴转 ph·Σmix^i，整棵子树刚体带走

度量同页面 CapScan：ratio = d_ij / (sU_i + sU_j)，要求 ρ ≤ min ratio。
"""
import json
import sys

import numpy as np

BUDGET = 6000
CAPN = 48
TAB = np.linspace(0, 2 * np.pi, CAPN, endpoint=False)
TCOS, TSIN = np.cos(TAB), np.sin(TAB)


def prune_cut(p, g, budget=BUDGET):
    best = None
    for cut in range(0, g + 1):
        nfull = sum(p ** l for l in range(cut + 1))
        per = p ** cut
        tot = nfull + per * (g - cut)
        if tot <= budget and (best is None or tot > best[1]):
            best = (cut, tot)
        if cut == g and nfull <= budget and (best is None or nfull > best[1]):
            best = (cut, nfull)
    if best is None:
        best = (0, 1 + (1 if g > 0 else 0))
    return best


def curve_frame(t, uh, vh, wh, sU, r, n, k, tau):
    phi, th = n * tau, k * tau
    cph, sph, cth, sth = np.cos(phi), np.sin(phi), np.cos(th), np.sin(th)
    rad = cph * uh + sph * wh
    A = sU + r * cth
    P = t + A * rad + r * sth * vh
    N = cth * rad + sth * vh
    B = -sth * rad + cth * vh
    return P, N, B


def build(p, g, q, rho, nW=5, kW=1680, nD=1, kD=7, a=1.0, budget=BUDGET):
    cut, total = prune_cut(p, g, budget)
    out = []

    def rec(u, v, t, depth, lv, sU, r, pi):
        me = len(out)
        out.append(None)
        if depth > 0:
            nch = p if (lv + 1 <= cut) else 1
            sV = np.linalg.norm(v)
            w = np.cross(u, v)
            uh, vh, wh = u / sU, v / sV, w / np.linalg.norm(w)
            sC, rC = q * sU, (rho * q * sU if rho is not None else 0.0)
            n, k = (nW, kW) if lv == 0 else (nD, kD)
            nwind = max(1, abs(int(round(n))))
            alc = 2 * np.pi / (nwind * p)
            for i in range(1, nch + 1):
                P, N, B = curve_frame(t, uh, vh, wh, sU, r, n, k, alc * i)
                rec(sC * B, sC * np.cross(N, B), P, depth - 1, lv + 1, sC, rC, me)
        out[me] = dict(t=t, u=u, v=v, uh=u / np.linalg.norm(u), vh=v / np.linalg.norm(v),
                       lv=lv, sU=sU, r=r, pi=pi)
    rec(np.array([a, 0.0, 0.0]), np.array([0.0, a, 0.0]), np.zeros(3), g, 0,
        a, (rho * a if rho is not None else 0.0), -1)
    for o in out:
        o['wh'] = np.cross(o['u'], o['v']) / np.linalg.norm(np.cross(o['u'], o['v']))
    return out, cut, total


def rot_axis(v, ax, ang):
    c, s = np.cos(ang), np.sin(ang)
    return v * c + np.cross(ax, v) * s + ax * np.dot(ax, v) * (1 - c)


def rev_nest(sc, ph, mix=1.0):
    n = len(sc)
    kids = [[] for _ in range(n)]
    for i, o in enumerate(sc):
        if 0 <= o['pi'] < n:
            kids[o['pi']].append(i)
    sub = [0] * n
    for i in range(n - 1, -1, -1):
        sub[i] = sub[kids[i][-1]] if kids[i] else i + 1

    def walk2(i, kk):
        C = kids[i]
        if not C:
            return
        aa = ph * kk
        pc = sc[i]
        cen, ax = pc['t'], pc['vh']
        for c in C:
            for m in range(c, sub[c]):
                t = sc[m]
                t['t'] = cen + rot_axis(t['t'] - cen, ax, aa)
                for key in ('u', 'v', 'uh', 'vh', 'wh'):
                    t[key] = rot_axis(t[key], ax, aa)
            walk2(c, kk * mix)
    walk2(0, 1.0)
    return sc


def gap_ratio(sc, rho, capn=CAPN):
    """返回 (min ratio, (lv_i, lv_j, d), 对数)。ratio = d/(sU_i+sU_j)。"""
    n = len(sc)
    T = np.array([o['t'] for o in sc])
    S = np.array([o['sU'] for o in sc])
    U = np.array([o['uh'] for o in sc])
    W = np.array([o['wh'] for o in sc])
    LV = np.array([o['lv'] for o in sc])
    idx = np.arange(n)
    best, info, pairs = 9e9, None, 0
    chord = 1 - np.cos(np.pi / capn)
    chunk = max(1, int(1.2e6 / n))
    for i0 in range(0, n, chunk):
        i1 = min(n, i0 + chunk)
        d = np.linalg.norm(T[i0:i1, None, :] - T[None, :, :], axis=-1)
        bound = (S[i0:i1, None] + S[None, :]) * (1 + rho) * 1.7
        m = (d < bound) & (idx[i0:i1, None] < idx[None, :])
        ii, jj = np.nonzero(m)
        if not len(ii):
            continue
        ii = ii + i0
        pairs += len(ii)
        swap = S[ii] > S[jj]
        ai = np.where(swap, jj, ii)
        bi = np.where(swap, ii, jj)
        # 采小圆（ai）的 capn 点，量到 B（bi）
        Ta, Ra, Ua, Wa = T[ai], S[ai], U[ai], W[ai]
        Tb, Rb, Ub, Wb = T[bi], S[bi], U[bi], W[bi]
        P = Ta[:, None, :] + Ra[:, None, None] * (TCOS[None, :, None] * Ua[:, None, :]
                                                 + TSIN[None, :, None] * Wa[:, None, :])
        Q = P - Tb[:, None, :]
        aa = (Q * Ub[:, None, :]).sum(-1)
        bb = (Q * Wb[:, None, :]).sum(-1)
        h2 = np.maximum((Q * Q).sum(-1) - aa * aa - bb * bb, 0.0)
        rr = np.sqrt(aa * aa + bb * bb) - Rb[:, None]
        dd = np.sqrt(h2 + rr * rr).min(axis=1) - Ra * chord
        dd = np.maximum(dd, 0.0)
        rt = dd / (S[ii] + S[jj])
        k = int(np.argmin(rt))
        if rt[k] < best:
            best = float(rt[k])
            info = (int(LV[ii[k]]), int(LV[jj[k]]), float(dd[k]))
    return best, info, pairs


def phase_min(p, g, q, rho, M=12, mix=1.0, nW=5, kW=1680, nD=1, kD=7):
    worst, wat, winfo = 9e9, 0.0, None
    for ph in np.linspace(0, 2 * np.pi, M, endpoint=False):
        sc, _, _ = build(p, g, q, rho, nW, kW, nD, kD)
        if ph:
            rev_nest(sc, float(ph), mix)
        r, info, npairs = gap_ratio(sc, rho)
        if r < worst:
            worst, wat, winfo = r, float(ph), info
    return worst, float(np.degrees(wat)), winfo


if __name__ == '__main__':
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    g = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    qs = [float(x) for x in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['0.30', '0.40', '0.50', '0.62'])]
    rhos = [float(x) for x in (sys.argv[4].split(',') if len(sys.argv) > 4 else ['0.05'])]
    M = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    rows = []
    for q in qs:
        for rho in rhos:
            sc, cut, total = build(p, g, q, rho)
            r0, i0, np0 = gap_ratio(sc, rho)
            rw, ang, iw = phase_min(p, g, q, rho, M)
            ok0 = r0 > rho
            okw = rw > rho
            print('p=%d g=%d q=%.3f rho=%.3f | cut=%d n=%d | 静置 ratio=%.5f Δ=%+.5f %s L%s | 全程 ratio=%.5f Δ=%+.5f @%d° %s L%s'
                  % (p, g, q, rho, cut, total, r0, (r0 - rho) * 1.0, 'OK' if ok0 else 'XX',
                     str(i0[0]) + '/' + str(i0[1]),
                     rw, rw - rho, round(ang), 'OK' if okw else 'XX',
                     str(iw[0]) + '/' + str(iw[1]) if iw else '?'))
            rows.append(dict(p=p, g=g, q=q, rho=rho, cut=cut, n=total,
                             r0=round(r0, 5), i0=i0, rw=round(rw, 5), ang=round(ang), iw=iw,
                             ok0=ok0, okw=okw))
    json.dump(rows, open('_p7_solve.json', 'w'), ensure_ascii=False, indent=1)
    print('→ _p7_solve.json')
