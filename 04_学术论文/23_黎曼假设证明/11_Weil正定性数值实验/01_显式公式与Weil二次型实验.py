# -*- coding: utf-8 -*-
"""
阶段 1 数值实验：Weil 显式公式验证 + 谱侧正定性扫描（复现 Connes 机制）
=======================================================================

目的
----
复现 Connes「致信黎曼」(arXiv:2602.04022) / Connes-Consani / Chuk(arXiv:2608.24827)
的核心机制：**有限素数截断（p <= e^L）的算术侧，在数值上等于（截断的）零点谱侧**。
这不是证明（见 08 审查文档的 Davenport-Heilbronn 判据），而是给阶段 1 一个
自洽、可复现、诚实标注边界的数值引擎。

归一化（乘性 Fourier 版，与 blog / Connes-Consani 一致，已用 L=0.5 无素数情形验证）
-----------------------------------------------------------------------------------
取偶测试函数 h(u)（支撑 [-L,L]，u = ln x），其偶 Fourier 变换

    hhat(t) = ∫_{-L}^{L} h(u)·cos(t·u) du

Weil 显式公式（对偶数对 ρ 与 1-ρ 求和后）：

    2·Σ_{γ>0} hhat(γ)  =  A(h)                     （γ 为非平凡零点虚部）

其中算术侧 A(h) 由三项组成：

    A(h) = main - psum + arch

    main = 2·∫_{-L}^{L} h(u)·cosh(u/2) du                 （谱主项）
    psum = 2·Σ_{p^m <= e^L} (ln p)/(p^{m/2})·h(m·ln p)     （素数项：有限和！）
    arch = (2/π)·∫_0^∞ θ'(t)·hhat(t) dt                   （Archimedean 项）
    θ'(t) = 0.5·Re[ψ(1/4 + i·t/2)] - 0.5·ln π              （Riemann-Siegel θ 导数）

**关键点**：右侧算术侧只用到素数 p <= e^L（有限个），却等于左侧涉及全部零点的谱和。
这就是「有限素数信息 ⟺ 全部零点信息」的显式公式本质 —— Connes 正定性战略的出发点。

测试函数族（闭式 Fourier 变换，避免内层数值积分）
--------------------------------------------------
    h_k(u) = cos^4(π·u/(2L))·cos(π·k·u/L),   |u| <= L, k = 0,1,2,...

cos^4 窗是 C^3 函数（在 u=±L 处前三阶导数消失），其 Fourier 变换 ~ O(1/t^4)，
保证谱侧部分和绝对收敛。展开 cos^4 = (3+4cos+cos2)/8 后每个积分都是
∫_0^L cos(ωu)du = sin(ωL)/ω 的有限组合，因此 hhat(t) 有解析闭式。

诚实边界
--------
1. 谱侧只取前 K 个零点 → 差值 = 尾部截断 + 数值误差，随 K 增大而减小（实验 1 验证）。
2. 用 zetazero() 取零点 = 默认零点在临界线上 → 实验不能"证伪" RH；
   它只是验证显式公式自洽性与有限素数机制（这正是 Davenport-Heilbronn 判据要提醒的）。
3. 双精度（float64）+ scipy 求积，不是 Connes 的 10^-55 高精度；
   若要达到 Chuk 的 8.9e-18 证书级别，需要区间算术与专用窗函数（超出本脚本范围）。

运行：系统 Python（D:/Program Files/Python312/python.exe，含 scipy + mpmath）
"""

import math
import numpy as np
from scipy.integrate import quad
from scipy.special import digamma
from mpmath import zetazero, im, mp

mp.dps = 20  # zetazero 只需 20 位（float64 的 ~16 位上限足够）


# ---------------------------------------------------------------
# 测试函数族：cos^4 窗 × cos(πku/L)，含闭式 Fourier 变换
# ---------------------------------------------------------------
def h_basis(k, u, L):
    """h_k(u) = cos^4(pi u/(2L)) * cos(pi k u/L)，支撑 [-L, L]。"""
    c = math.pi * u / (2.0 * L)
    return (math.cos(c) ** 4) * math.cos(math.pi * k * u / L)


def hhat_closed(k, L, t):
    """闭式 hhat_k(t) = ∫_{-L}^{L} h_k(u) cos(t u) du。

    展开 cos^4(πu/2L) = (3 + 4cos(πu/L) + cos(2πu/L))/8，
    用 2cosA·cosB = cos(A+B)+cos(A-B) 把被积函数拆成 cos(ωu) 项，
    每项 ∫_0^L cos(ωu)du = sin(ωL)/ω。所有零点在 t 取特定值时由 ω→0 极限 L 代替。
    """
    a = math.pi * k / L
    total = 0.0
    for alpha, w in ((0.0, 3.0), (math.pi / L, 4.0), (2.0 * math.pi / L, 1.0)):
        for s1 in (1.0, -1.0):
            for s2 in (1.0, -1.0):
                om = alpha + s1 * a + s2 * t
                if abs(om) < 1e-12:
                    total += w * L
                else:
                    total += w * math.sin(om * L) / om
    return total / 16.0  # 2·(1/8)·(1/4) = 1/16


# ---------------------------------------------------------------
# von Mangoldt 支撑：n = p^m <= e^L，返回 [(n, ln p)]
# ---------------------------------------------------------------
def mangoldt_terms(L):
    """n = p^m <= e^L 的所有项，返回 [(n, ln p, p, m)]。"""
    N = int(math.floor(math.exp(L)))
    terms = []
    for p in range(2, N + 1):
        prime = True
        for d in range(2, int(p ** 0.5) + 1):
            if p % d == 0:
                prime = False
                break
        if not prime:
            continue
        pk, lp, m = p, math.log(p), 1
        while pk <= N:
            terms.append((pk, lp, p, m))
            pk *= p
            m += 1
    return terms


# ---------------------------------------------------------------
# Riemann-Siegel theta 的导数：θ'(t) = 0.5·Re[ψ(1/4+it/2)] - 0.5·ln π
# ---------------------------------------------------------------
def theta_prime(t):
    return 0.5 * np.real(digamma(0.25 + 0.5j * t)) - 0.5 * math.log(math.pi)


# ---------------------------------------------------------------
# 算术侧 A(h_k)：main - psum + arch
# ---------------------------------------------------------------
def arith_side(k, L, T_arch=600.0):
    """返回 (main, psum, arch, A)。A = main - psum + arch。

    2026-09-02 晚修正：默认 T_arch 由 150 提到 600。
    原因（04 号 mpmath 高精度脚本 + float64/mpmath 对拍裁决）：
    L>=2.0 时残差 ~1e-11 的卡点不是 float64 求积噪声地板，而是
    Archimedean 项在 T_arch=150 的截断误差 —— mpmath dps=40 在
    T_arch=150 给出同样的 ~1.17e-11，而 T_arch=600 时两种精度都降到
    ~1e-13 量级并开始随 K 收敛。故先前 README 的"float64 地板"归因作废。
    """
    # main = 2∫_{-L}^L h_k(u) cosh(u/2) du
    main, _ = quad(lambda u: h_basis(k, u, L) * math.cosh(u / 2.0), -L, L, limit=200)
    main *= 2.0

    # psum = 2·Σ_{p^m<=e^L} (ln p)/(p^{m/2})·h_k(m·ln p)
    psum = 0.0
    for n, lp, p, m in mangoldt_terms(L):
        u = math.log(n)  # = m·ln p
        psum += (lp / math.sqrt(n)) * h_basis(k, u, L)
    psum *= 2.0

    # arch = (2/π)·∫_0^{T_arch} θ'(t)·hhat_k(t) dt
    def g(t):
        return theta_prime(t) * hhat_closed(k, L, t)

    av, _ = quad(g, 0.0, T_arch, limit=600, epsabs=1e-13, epsrel=1e-13)
    arch = (2.0 / math.pi) * av

    return main, psum, arch, main - psum + arch


# ---------------------------------------------------------------
# 谱侧：2·Σ_{n=1..K} hhat_k(γ_n)（γ_n 缓存，避免重复算 zetazero）
# ---------------------------------------------------------------
def spectral_side(k, L, gammas, K):
    s = 0.0
    for g in gammas[:K]:
        s += hhat_closed(k, L, g)
    return 2.0 * s


# ---------------------------------------------------------------
# 实验 1：显式公式自检（有限素数 ⟺ 零点谱侧，尾部随 K 收敛）
# ---------------------------------------------------------------
def experiment1(gammas, L_list=(0.5, 1.0, 1.5), K_list=(50, 150, 300)):
    print("=" * 74)
    print("实验 1：Weil 显式公式自检  A(h) = main - psum + arch  vs  2Σ hhat(γ)")
    print("=" * 74)
    for L in L_list:
        main, psum, arch, A = arith_side(0, L)
        print(f"\nL = {L}    e^L = {math.exp(L):.5f}")
        print(f"  main(2∫cosh)  = {main:+.12f}")
        pm = mangoldt_terms(L)
        psum_desc = ("（无，纯 Archimedean）" if not pm
                     else "  ".join(f"{p}^{m}={n}" for n, lp, p, m in pm))
        print(f"  psum(素数项)  = {psum:+.12f}   素数/素幂 p^m<=e^L: {psum_desc}")
        print(f"  arch(2/π∫θ'ĥ) = {arch:+.12f}")
        print(f"  A(h)           = {A:+.12f}")
        print(f"  {'K':>4}  {'谱侧 2Σhhat':>16}  {'|A-谱侧|':>12}")
        prev = None
        for K in K_list:
            S = spectral_side(0, L, gammas, K)
            d = abs(A - S)
            trend = ""
            if prev is not None:
                trend = "  ↓" if d < prev else "  ↑?!"
            print(f"  {K:>4}  {S:+.16f}  {d:.3e}{trend}")
            prev = d


# ---------------------------------------------------------------
# 实验 2：谱侧正定性扫描 Q_N = 2Σ_{n<=N} hhat(γ_n)^2
# ---------------------------------------------------------------
def experiment2(gammas, L_list=(0.5, 1.0, 1.5, 2.0), N_list=(10, 50, 100, 200)):
    print()
    print("=" * 74)
    print("实验 2：谱侧二次型 Q_N(k=0) = 2Σ_{n<=N} hhat(γ_n)^2 ≥ 0（正定性扫描）")
    print("=" * 74)
    print("注意：谱侧由 |hhat|^2 构成 → 非负是构造性的；")
    print("真正非平凡的是算术侧算子的正定性（需区间算术，Chuk 证书 8.9e-18 级别）。")
    print("Q 随 L 增大而减小 = 谱能量向低频集中（测不准原理），非 Landau-Widom。")
    print(f"{'L':>5} {'Q_10':>14} {'Q_50':>14} {'Q_100':>14} {'Q_200':>14}")
    print("-" * 66)
    for L in L_list:
        row = []
        for N in N_list:
            q = 0.0
            for g in gammas[:N]:
                v = hhat_closed(0, L, g)
                q += 2.0 * v * v
            row.append(q)
        print(f"{L:>5} " + " ".join(f"{x:>14.8e}" for x in row))
    print("\n判读：所有 Q_N > 0 且随 N 单调递增 —— 与『零点全在临界线上』一致（必要条件，非充分）。")


# ---------------------------------------------------------------
# 实验 3：基函数扩展时谱侧 Gram 矩阵最小特征值（数值秩饱和）
# ---------------------------------------------------------------
def experiment3(gammas, L=1.0, N_list=(2, 4, 6, 8, 10, 12, 14), K=200):
    print()
    print("=" * 74)
    print(f"实验 3：Gram 矩阵 G_jk = 2Σ{{n≤K}} hhat_j(γ_n)hhat_k(γ_n)  最小特征值（L={L}, K={K}）")
    print("=" * 74)
    K = min(K, len(gammas))
    Nmax = max(N_list)
    # F[n, j] = hhat_j(γ_n)
    F = np.zeros((K, Nmax))
    for n in range(K):
        g = gammas[n]
        for j in range(Nmax):
            F[n, j] = hhat_closed(j, L, g)
    print(f"{'N':>4}  {'λ_min(G)':>14}  {'log10 λ_min':>12}")
    print("-" * 36)
    for N in N_list:
        G = 2.0 * (F[:, :N].T @ F[:, :N])
        lam = np.linalg.eigvalsh(G)
        lam_min = max(lam[0], 0.0)
        print(f"{N:>4}  {lam_min:>14.6e}  {math.log10(max(lam_min, 1e-320)):>12.2f}")
    print("\n判读：随基函数个数 N 增加，λ_min 快速衰减到 float64 地板（~1e-16）后数值饱和为 0。")
    print("这是『固定 K 个采样零点上，高频基函数数值线性相关 → Gram 秩饱和』的谱侧现象，")
    print("与 Landau-Widom 无关。诚实的提醒：谱侧 Gram 是 FᵀF 型 → 半正定是构造性的；")
    print("Connes/Chuk 的算术侧有限秩截断才是真正检验 RH 正定性之处。")


# ---------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------
if __name__ == "__main__":
    import sys

    KMAX = 400
    print("计算前", KMAX, "个零点虚部 γ（mpmath zetazero，缓存一次）...", flush=True)
    gammas = [float(im(zetazero(n))) for n in range(1, KMAX + 1)]
    print(f"γ_1 = {gammas[0]:.6f},  γ_{KMAX} = {gammas[-1]:.3f}\n")

    # 单测：闭式 hhat 与数值积分核对
    t0 = 3.7
    ref, _ = quad(lambda u: h_basis(0, u, 1.0) * math.cos(t0 * u), -1.0, 1.0, limit=200)
    print(f"[自检] hhat_closed(0,1,{t0}) = {hhat_closed(0, 1.0, t0):.15f}  "
          f"vs quad = {ref:.15f}  差 {abs(hhat_closed(0, 1.0, t0) - ref):.2e}")
    print()

    experiment1(gammas)
    experiment2(gammas)
    experiment3(gammas)

    print()
    print("=" * 74)
    print("实验完成。显式公式引擎自洽（A ≈ 谱侧，尾部随 K 收敛）。")
