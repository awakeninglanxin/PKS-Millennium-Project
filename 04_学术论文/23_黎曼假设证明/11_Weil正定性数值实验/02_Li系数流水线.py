# -*- coding: utf-8 -*-
"""
阶段 1 数值实验：Li 系数流水线 λ_n（Li 判据的正值性扫描）
==========================================================

数学背景
--------
Li (1997) 判据：设 ξ 的零点（即非平凡零点）为 ρ，定义

    λ_n = Σ_ρ [ 1 - (1 - 1/ρ)^n ],        n = 1, 2, 3, ...

则 **RH ⟺ 对所有 n ≥ 1 都有 λ_n ≥ 0**（事实上 λ_n > 0）。

按共轭对 ρ = 1/2 ± iγ 归并（γ > 0，每个零点 ρ 与共轭 1-ρ 都计入），
每对贡献为实值：

    T_n(γ) = 2 - 2·Re[ (1 - 1/(1/2 + iγ))^n ]

    λ_n = Σ_{γ>0} T_n(γ)

收敛性：|1 - 1/(1/2+iγ)| ≈ 1 + O(1/γ^2)，而 T_n(γ) ~ n(n+1)/(2γ^2)，
配合零点密度 ~ (1/2π)ln(γ/2πe)·dγ，尾部 ~ (ln T)/T，收敛缓慢但确定。
本脚本用前 K 个零点做截断，并给出已知闭合值锚点校验：

    λ_1 = Σ_ρ 1/ρ = 1 + γ_E/2 - (1/2)·ln(4π) ≈ 0.0230957...

（γ_E 为 Euler 常数。）尾部误差 ~ (ln γ_K)/γ_K，随 K 增大而减小。

诚实边界
--------
1. Li 判据要求「所有 n」——本脚本只扫 n = 1..N_max 的有限段（必要条件演示）。
2. 用 zetazero() 取零点 = 默认零点在临界线上；λ_n > 0 只是与 RH 一致的数值证据，
   不能构成证明（Davenport-Heilbronn 判据同理适用）。
3. 截断误差随 K 增大按 ~(ln γ_K)/γ_K 衰减；如需高精度需尾部解析修正或区间算术。

运行：系统 Python（D:/Program Files/Python312/python.exe，含 mpmath）
"""

import math
from mpmath import zetazero, im, mp, euler

mp.dps = 25


def li_coefficients(n_max, K, gamma_cache):
    """返回 λ_1..λ_Nmax（用前 K 个零点虚部）。"""
    lam = [0.0] * (n_max + 1)  # 1-indexed
    for g in gamma_cache[:K]:
        rho = 0.5 + 1j * g
        z = 1.0 - 1.0 / rho          # z = 1 - 1/ρ
        pw = z
        for n in range(1, n_max + 1):
            lam[n] += 2.0 - 2.0 * pw.real
            pw *= z
    return lam


def main():
    K = 600          # 用前 600 个零点（γ_600 ≈ 938）
    N_max = 20

    print("=" * 72)
    print(f"Li 系数流水线：λ_n = Σ_ρ[1-(1-1/ρ)^n]，前 {K} 个零点，n = 1..{N_max}")
    print("=" * 72)

    print(f"计算前 {K} 个零点虚部 γ（zetazero，缓存一次）...", flush=True)
    gammas = [float(im(zetazero(n))) for n in range(1, K + 1)]
    print(f"γ_1 = {gammas[0]:.6f},  γ_{K} = {gammas[-1]:.3f}")

    lam = li_coefficients(N_max, K, gammas)

    # 锚点校验：λ_1 的闭合值
    lam1_closed = 1.0 + float(euler) / 2.0 - 0.5 * math.log(4.0 * math.pi)
    res = lam[1] - lam1_closed

    print(f"\n锚点校验：λ_1(数值) = {lam[1]:.10f}")
    print(f"          λ_1(闭合) = {lam1_closed:.10f}   （1 + γ_E/2 - ln4π/2）")
    print(f"          残差      = {res:+.3e}   （≈尾部截断，负值仅因截断）")
    print()

    print(f"{'n':>4}  {'λ_n':>16}  {'log10 λ_n':>11}  {'符号':>4}")
    print("-" * 42)
    ok = True
    for n in range(1, N_max + 1):
        pos = lam[n] > 0
        ok = ok and pos
        print(f"{n:>4}  {lam[n]:>16.8e}  "
              f"{math.log10(abs(lam[n])):>11.4f}  {'✓' if pos else '✗'}")
    print()
    print(f"判读：n = 1..{N_max} 全部 λ_n > 0 {'✓' if ok else '✗'}"
          f"  —— 与 Li 判据/RH 一致（必要条件，非充分；"
          f"残差 ~ (ln γ_K)/γ_K ≈ {(math.log(gammas[-1])/gammas[-1]):.1e} 量级）")


if __name__ == "__main__":
    main()
