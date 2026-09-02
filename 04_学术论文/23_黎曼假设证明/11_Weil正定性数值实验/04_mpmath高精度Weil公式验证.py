# -*- coding: utf-8 -*-
"""
04_mpmath高精度Weil公式验证.py — 突破 float64 噪声地板（README「下一步」③）
=================================================================================

背景
----
01 号脚本在 L>=2.0 后残差卡在 ~1e-11（L=3.0 实测 1.2e-11，不再随 K 下降）。
当时的归因是：A = main - psum + arch 存在约 4e5 倍的抵消，float64 求积的
绝对噪声地板 ~1e-11 封顶（「求积噪声地板」）。

本脚本用 mpmath 把求积提到 dps=40，在同样的 L 上逐 K 扫描，**裁决这个归因**：

  * 若残差随 K 下降并远低于 1e-11  → 先前 1.2e-11 确实是 float64 求积地板；
    公式本身在更高精度下依然成立（尾随项还可被 Archimedean 截断上限控制）。
  * 若残差在 mpmath 下仍卡 ~1e-11 且不随 K 降 → 先前归因错误，卡点是
    零点尾部截断（或 T_arch 截断），需更大 K 或更大 T_arch 才会改善。

对偶参数（K, T_arch）都扫，即可把「求积噪声」与「尾部截断」两种可能彻底分开。

诚实边界
--------
1. 零点仍由 mpmath zetazero() 给出（默认在临界线上）→ 验证的是公式自洽性，
   不是 RH（Davenport-Heilbronn 判据仍然适用）。
2. dps=40 远未到 Connes 的 10^-55 精度；本脚本目标是**清除 float64 归因歧义**，
   把「引擎自检」的精度证书从 1e-11 提升到 1e-18 量级。
3. 零点本身只需 ~20 位精度（残差目标 1e-18，零点的绝对误差贡献远低于此），
   故 zetazero 在临时 dps=25 下计算，避免高精度找零点拖慢运行。

运行：系统 Python（D:/Program Files/Python312/python.exe，含 mpmath）
"""

import os
import sys
import time
import math
import pickle

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台 UTF-8
except Exception:
    pass

import mpmath as mp

CACHE_PKL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zeros_cache_800.pkl")

mp.dps = 40            # 求积/函数求值精度
PI = mp.pi
ZERO_DPS = 20          # 计算 zetazero 时用的临时精度（20 位 ≫ 1e-17 残差目标）

# ---------------------------------------------------------------
# 测试函数（mpmath 版，与 01 完全同口径，仅 float -> mpf）
# ---------------------------------------------------------------
def h_basis(k, u, L):
    c = PI * u / (2 * L)
    return mp.cos(c) ** 4 * mp.cos(PI * k * u / L)


def hhat_closed(k, L, t):
    a = PI * k / L
    total = mp.mpf(0)
    for alpha, w in ((0, 3), (PI / L, 4), (2 * PI / L, 1)):
        for s1 in (1, -1):
            for s2 in (1, -1):
                om = alpha + s1 * a + s2 * t
                if om == 0:
                    total += w * L
                else:
                    total += w * mp.sin(om * L) / om
    return total / 16


def theta_prime(t):
    return 0.5 * mp.re(mp.digamma(mp.mpc(0.25, t / 2))) - 0.5 * mp.log(PI)


# ---------------------------------------------------------------
# von Mangoldt 项：n = p^m <= e^L（素数与 01 一致，纯 int 筛法）
# ---------------------------------------------------------------
def mangoldt_terms(L):
    N = int(math.floor(float(mp.e ** L)))
    sieve = [True] * (N + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, N + 1, i):
                sieve[j] = False
    terms = []
    for p in range(2, N + 1):
        if not sieve[p]:
            continue
        n = p
        while n <= N:
            terms.append((mp.mpf(n), mp.log(p), p))
            n *= p
    terms.sort(key=lambda t: float(t[0]))
    return terms


# ---------------------------------------------------------------
# 算术侧（mpmath 高精度求积）
# ---------------------------------------------------------------
def arith_side(k, L, T_arch):
    """返回 (main, psum, arch, A)。积分逐段做，保证收敛且便于诊断。"""
    main = 2 * mp.quad(lambda u: h_basis(k, u, L) * mp.cosh(u / 2), [-L, L])

    psum = mp.mpf(0)
    for n, lp, p in mangoldt_terms(L):
        u = mp.log(n)  # = m·ln p
        psum += (lp / mp.sqrt(n)) * h_basis(k, u, L)
    psum *= 2

    # Archimedean：分段积分 [0,600]（θ' 缓增 × ĥ 快衰，600 以上贡献可忽略）
    def f(t):
        return theta_prime(t) * hhat_closed(k, L, t)

    bounds = [0.0, 20.0, 60.0, 150.0, 300.0, float(T_arch)]
    total = mp.mpf(0)
    prev = 0.0
    for b in bounds[1:]:
        if b > float(T_arch):
            break
        total += mp.quad(f, [prev, b])
        prev = b
    arch = (2 / PI) * total

    return main, psum, arch, main - psum + arch


# ---------------------------------------------------------------
# 谱侧：2·Σ_{j<=K} hhat_k(γ_j)
# ---------------------------------------------------------------
def spectral_side(k, L, gammas, K):
    return 2 * mp.fsum(hhat_closed(k, L, g) for g in gammas[:K])


# ---------------------------------------------------------------
# 零点缓存（临时降精度，够 1e-18 目标用）
# ---------------------------------------------------------------
def zeros_up_to(K):
    """零点虚部（临时降精度计算），带磁盘缓存避免重复 3 分钟计算。"""
    if os.path.exists(CACHE_PKL):
        with open(CACHE_PKL, "rb") as f:
            gs = pickle.load(f)
        if len(gs) >= K:
            print(f"  零点从缓存加载 {len(gs)} 个（γ_{K} = {float(gs[K-1]):.3f}）", flush=True)
            return gs[:K]
    saved = mp.dps
    mp.dps = ZERO_DPS
    t0 = time.time()
    gs = [mp.im(mp.zetazero(n)) for n in range(1, K + 1)]
    mp.dps = saved
    with open(CACHE_PKL, "wb") as f:
        pickle.dump(gs, f)
    print(f"  零点 γ_1..γ_{K} 计算完成，用时 {time.time()-t0:.1f}s "
          f"（γ_{K} = {float(gs[-1]):.3f}，已缓存）", flush=True)
    return gs


def fmt_row(L_label, T_arch, K, resid, note=""):
    print(f"  {L_label:>7}  {T_arch:>6}  {K:>5}  {float(resid):>12.3e}  {note}")


# ---------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 78)
    print("mpmath 高精度 Weil 显式公式验证（dps=40）— 裁决 L=3.0 残差卡点归因")
    print("=" * 78)
    print("对照（01 号 float64 实测）：L=2.0→4.3e-12 | L=ln13→4.0e-12 | L=3.0→1.2e-11 (K=400)")
    print("若 mpmath 残差随 K 下降且 <1e-11 → 卡点是 float64 求积地板；")
    print("若卡 ~1e-11 不随 K 降 → 卡点是零点尾部/T_arch 截断。\n")

    # 预取零点到 K=800（一次，供所有 L 复用）
    KMAX = 800
    print(f"计算前 {KMAX} 个零点虚部（临时 dps={ZERO_DPS}，缓存一次）...", flush=True)
    gammas = zeros_up_to(KMAX)

    # 自检 1：闭式 ĥ 在 t=0 与解析值 0.75L 核对
    for Lv in (mp.mpf(1), mp.mpf(3)):
        got = hhat_closed(0, Lv, mp.mpf(0))
        want = 0.75 * Lv
        print(f"  [自检] hhat_closed(0,L={float(Lv)},t=0) = {mp.nstr(got, 30)}  "
              f"vs 0.75L = {mp.nstr(want, 30)}  → 一致: {got == want}")

    # 自检 2：θ'(t) 渐近核对 θ'(t) ~ 0.5·ln(t/2π)
    for tv in (100.0, 400.0):
        asym = 0.5 * math.log(tv / (2 * math.pi))
        print(f"  [自检] θ'({tv:g}) = {float(theta_prime(mp.mpf(tv))):+.12f}  "
              f"vs 0.5·ln(t/2π) = {asym:+.12f}  差 = {abs(float(theta_prime(mp.mpf(tv))) - asym):.2e}")

    print()
    print(f"{'L':>7} {'T_arch':>6} {'K':>5} {'|A - 谱侧|':>14}  判读")
    print("-" * 78)

    # 1) L=3.0：K × T_arch 全扫描（关键裁决）
    print("L = 3.0（素数 ≤ 19：2,4,8,16,3,9,5,7,11,13,17,19）")
    L3 = mp.mpf(3)
    arith_cache = {}
    for T_arch in (150, 600):
        t0 = time.time()
        main, psum, arch, A = arith_side(0, L3, T_arch)
        arith_cache[T_arch] = (main, psum, arch, A)
        print(f"  [L=3.0, T_arch={T_arch}]  main={float(main):+.9f}  "
              f"psum={float(psum):+.9f}  arch={float(arch):+.9f}  "
              f"A={float(A):+.9e}  （{time.time()-t0:.0f}s）", flush=True)
        for K in (400, 800):
            S = spectral_side(0, L3, gammas, K)
            fmt_row("3.0", T_arch, K, abs(A - S))

    # 2) L=2.0 / L=ln13：大 T_arch 下逐 K
    for Lv, lab in ((mp.mpf(2), "2.0"), (mp.log(13), "ln13")):
        main, psum, arch, A = arith_side(0, Lv, 600)
        print(f"  [L={lab}]  A={float(A):+.9e}  （素数/素幂 ≤ e^L）")
        for K in (400, 800):
            S = spectral_side(0, Lv, gammas, K)
            fmt_row(lab, 600, K, abs(A - S))

    # 3) L=3.0, k=1（二阶基再确认一次）
    main, psum, arch, A = arith_side(1, L3, 600)
    print(f"  [L=3.0, k=1]  A = {float(A):+.9e}")
    for K in (400, 800):
        S = spectral_side(1, L3, gammas, K)
        fmt_row("3.0k1", 600, K, abs(A - S))

    print()
    print("=" * 78)
    print("判读：")
    print("· 若 |A-谱侧| 随 K 下降且显著 < 1e-11  → 公式在 dps=40 下成立到远超 float64 地板，")
    print("  先前 L=3.0 的 1.2e-11 卡点 = float64 求积噪声地板（归因确认）。")
    print("· 若同一 K 下 T_arch=600 比 T_arch=150 明显更小 → 先前还叠加了 Archimedean 截断误差。")
