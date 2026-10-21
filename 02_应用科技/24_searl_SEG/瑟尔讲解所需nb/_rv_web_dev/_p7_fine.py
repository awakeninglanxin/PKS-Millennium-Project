# -*- coding: utf-8 -*-
"""对 p=7/g=7 的候选档做加密相位扫描，找真实最坏点（粗扫会漏）。"""
import sys
import numpy as np
import _p7_solve as P

q = float(sys.argv[1]); rho = float(sys.argv[2]); M = int(sys.argv[3]) if len(sys.argv) > 3 else 72
best, bat, binfo = 9e9, 0, None
rows = []
for ph in np.linspace(0, 2 * np.pi, M, endpoint=False):
    sc, _, _ = P.build(7, 7, q, rho)
    if ph: P.rev_nest(sc, float(ph), 1.0)
    r, info, _ = P.gap_ratio(sc, rho)
    rows.append((float(np.degrees(ph)), r, info))
    if r < best: best, bat, binfo = r, float(np.degrees(ph)), info
print('q=%.3f rho=%.3f  %d 相位加密扫描' % (q, rho, M))
print('最坏 ratio=%.5f @%.1f°  绑定 L%s/L%s  Δ=%+.5f  %s' %
      (best, bat, binfo[0], binfo[1], best - rho, 'OK' if best > rho else 'XX'))
rows.sort(key=lambda t: t[1])
print('最坏 6 个相位：')
for a, r, i in rows[:6]:
    print('   %7.2f°  ratio=%.5f  L%s/L%s' % (a, r, i[0], i[1]))
# 最坏点附近再压 8 点
h = 360.0 / M / 8
print('附近细化（步长 %.3f°）：' % h)
b2, a2 = best, bat
for k in range(-4, 5):
    ph = np.radians(bat + k * h)
    sc, _, _ = P.build(7, 7, q, rho)
    P.rev_nest(sc, float(ph), 1.0)
    r, info, _ = P.gap_ratio(sc, rho)
    flag = ' <<<' if r < b2 else ''
    if r < b2: b2, a2 = r, bat + k * h
    print('   %8.3f°  ratio=%.5f  L%s/L%s%s' % (bat + k * h, r, info[0], info[1], flag))
print('⇒ 真最坏 ratio=%.5f @%.3f°  Δ=%+.5f  %s' % (b2, a2, b2 - rho, 'OK' if b2 > rho else 'XX'))
