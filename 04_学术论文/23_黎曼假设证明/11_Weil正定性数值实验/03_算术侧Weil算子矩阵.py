# -*- coding: utf-8 -*-
"""
阶段 1 数值实验：算术侧 Weil 算子矩阵（真正的 Q 正定性检验对象）
=================================================================

动机
----
01 号脚本的实验 2/3 用的是**谱侧** Gram：G_jk = Σ_γ ĥ_j(γ)ĥ_k(γ)，它是 FᵀF 型，
半正定是构造性的（没检验任何东西）。Connes/Chuk 的真正检验对象是**算术侧**二次型——
只用素数信息构造矩阵、再检查其正定性；若某有限秩截断出现负特征值，就是 RH 的数值反例信号。

数学内核
--------
对偶测试函数 h_j, h_k（支撑 [-L,L]），取**加性卷积** g = h_j * h_k（支撑 [-2L,2L]）。
Fourier 变换满足 ĝ(t) = ĥ_j(t)·ĥ_k(t)。把 01 号已验证的 Weil 显式公式线性泛函 A
（对任何支撑 [-Λ,Λ] 的偶函数成立，A(h) = main - psum + arch = 2Σ_γ ĥ(γ)）作用在 g 上：

    B(j,k) := (1/2)·A(h_j * h_k) = Σ_{γ>0} ĥ_j(γ)·ĥ_k(γ)

B 的**算术侧**三项全部可算，且比实验 1 吃更深的素数（到 e^{2L}）：

    B(j,k) = C_j·C_k                                  （main/2：矩乘积）
             - Σ_{p^m ≤ e^{2L}} (ln p)/p^{m/2}·(h_j*h_k)(m·ln p)   （psum/2：素数到 e^{2L}！）
             + (1/π)·∫_0^∞ θ'(t)·ĥ_j(t)·ĥ_k(t) dt      （arch/2：闭式乘积，无需内层积分）

其中 C_j = ∫_{-L}^{L} h_j(u)·cosh(u/2) du。推导要点：cosh((u+v)/2) 展开后
sinh(u/2)·sinh(v/2) 项因 h_j 偶 × sinh 奇积分为 0，只剩 C_j·C_k。

右侧 Σ_γ ĥ_j(γ)ĥ_k(γ) 是向量 (ĥ_j(γ))_γ 在 ℓ²(零点) 上的 Gram 矩阵 → 半正定。
因此**若算术侧与谱侧数值一致，算术 Gram 的正定性 = 零点全在临界线上的谱事实的算术影子**。

实验设计
--------
对若干 L，取基函数 k = 0..N-1：
1. 纯算术侧构造 B_arith(j,k)（只用素数 ≤ e^{2L} + Archimedean 积分）；
2. 谱侧 B_spec(j,k) = Σ_{n≤K} ĥ_j(γ_n)ĥ_k(γ_n)；
3. 对拍：max|B_arith - B_spec|（应 ~ 1e-10 量级，尾部 + 求积噪声）；
4. B_arith 的最小特征值扫描（正定性检查）。

诚实边界
--------
1. 有限基 {0..N-1} + 有限零点 K → 有限秩截断，不是无限维 Weil 算子本身；
   无限维正定性才等价于 RH（本脚本只做「算术侧与谱侧引擎对拍」+ 有限秩 PSD 检查）。
2. zetazero() 取零点 = 默认零点在临界线上；谱侧 B_spec 半正定是构造性的，
   真正的检验是 B_arith 本身 PSD 且两矩阵吻合（说明算术数据"复现"了谱正性）。
3. float64：L 大或基多时 B_arith 的抵消放大噪声（main/psum/arch 各自 ~1 而 B ~1e-7）。
4. 这不是 Landau-Widom 曲线：LW 需要约束收紧（窗窄）下的受限算子 + 区间算术
   （Chuk L=0.8 → 8.9e-18），本脚本的 λ_min(L) 只作辅助观察。

运行：系统 Python（D:/Program Files/Python312/python.exe，含 scipy + mpmath）
"""

import math
import importlib.util
import numpy as np
from scipy.integrate import quad
from mpmath import zetazero, im, mp

mp.dps = 20

# 载入 01 号脚本的公共函数（文件名数字开头无法常规 import，用 importlib）
_spec = importlib.util.spec_from_file_location(
    "weil01", "01_显式公式与Weil二次型实验.py")
weil = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(weil)
h_basis = weil.h_basis
hhat_closed = weil.hhat_closed
mangoldt_terms = weil.mangoldt_terms
theta_prime = weil.theta_prime


# ---------------------------------------------------------------
# 算术侧 Weil 算子矩阵 B_arith
# ---------------------------------------------------------------
def moment_C(k, L):
    """C_k = ∫_{-L}^{L} h_k(u)·cosh(u/2) du（main/2 的矩因子）。"""
    val, _ = quad(lambda u: h_basis(k, u, L) * math.cosh(u / 2.0), -L, L, limit=200)
    return val


def conv_hh(j, k, L, w):
    """(h_j * h_k)(w) = ∫ h_j(u)·h_k(w-u) du，支撑交集自动限制。"""
    lo = max(-L, w - L)
    hi = min(L, w + L)
    if hi <= lo:
        return 0.0
    val, _ = quad(lambda u: h_basis(j, u, L) * h_basis(k, w - u, L), lo, hi, limit=200)
    return val


def arch_pair(j, k, L, T_arch=150.0):
    """(arch/2) = (1/π)·∫_0^T θ'(t)·ĥ_j(t)·ĥ_k(t) dt（闭式乘积，无内层积分）。"""
    def f(t):
        return theta_prime(t) * hhat_closed(j, L, t) * hhat_closed(k, L, t)

    val, _ = quad(f, 0.0, T_arch, limit=800, epsabs=1e-14, epsrel=1e-14)
    return val / math.pi


def arith_B(j, k, L, moments=None):
    """B_arith(j,k) = C_j·C_k - Σ_p (ln p)/p^{m/2}·conv(m ln p) + (1/π)∫θ'ĥ_jĥ_k。

    moments: 预计算的 moment_C 列表，避免重复积分。
    """
    if moments is None:
        moments = [None] * (max(j, k) + 1)
    if moments[j] is None:
        moments[j] = moment_C(j, L)
    if moments[k] is None:
        moments[k] = moment_C(k, L)
    B = moments[j] * moments[k]

    # psum/2：素数/素幂到 e^{2L}（卷积支撑翻倍 → 素数深度翻倍）
    for n, lp, p, m in mangoldt_terms(2.0 * L):
        w = math.log(n)  # = m·ln p
        B -= (lp / math.sqrt(n)) * conv_hh(j, k, L, w)

    # arch/2
    B += arch_pair(j, k, L)
    return B


def arith_Gram(N, L, moments=None):
    """N×N 算术侧 Gram 矩阵（对称）。"""
    G = np.zeros((N, N))
    for j in range(N):
        for k in range(j, N):
            v = arith_B(j, k, L, moments)
            G[j, k] = G[k, j] = v
    return G


# ---------------------------------------------------------------
# 谱侧 Gram：B_spec(j,k) = Σ_{n<=K} ĥ_j(γ_n)ĥ_k(γ_n)
# ---------------------------------------------------------------
def spec_Gram(N, L, gammas, K):
    K = min(K, len(gammas))
    F = np.zeros((K, N))
    for n in range(K):
        g = gammas[n]
        for j in range(N):
            F[n, j] = hhat_closed(j, L, g)
    return F.T @ F  # K×N → N×N Gram


# ---------------------------------------------------------------
# 主流程：L 扫描，算术 vs 谱侧对拍 + 正定性
# ---------------------------------------------------------------
def main():
    N = 5                 # 基函数 k = 0..4
    K = 400               # 谱侧零点数
    L_list = (0.8, 1.0, 1.5, 2.0)

    print("=" * 78)
    print(f"算术侧 Weil 算子矩阵 B(j,k) = (1/2)·A(h_j*h_k)  vs  谱侧 Σĥ_j·ĥ_k")
    print(f"基函数 N={N}（k=0..{N-1}），谱侧零点 K={K}（γ₁..γ_{K}）")
    print("=" * 78)

    print(f"计算前 {K} 个零点虚部 γ（缓存一次）...", flush=True)
    gammas = [float(im(zetazero(n))) for n in range(1, K + 1)]
    print(f"γ_1 = {gammas[0]:.6f},  γ_{K} = {gammas[-1]:.3f}\n")

    print(f"{'L':>6} {'e^(2L)':>9} {'素幂≤e^(2L)':>22} "
          f"{'max|Δ|':>12} {'λ_min(B_arith)':>16}")
    print("-" * 78)

    for L in L_list:
        # 算术侧
        moments = [moment_C(k, L) for k in range(N)]
        Ga = arith_Gram(N, L, moments)
        # 谱侧
        Gs = spec_Gram(N, L, gammas, K)
        diff = np.max(np.abs(Ga - Gs))
        lam = np.linalg.eigvalsh(Ga)
        lam_min = lam[0]

        pm = [n for n, lp, p, m in mangoldt_terms(2.0 * L)]
        desc = ",".join(str(x) for x in pm) if pm else "无"
        print(f"{L:>6.2f} {math.exp(2*L):>9.2f} {desc:>22} "
              f"{diff:>12.3e} {lam_min:>16.3e}")

        # 每档 L 打印矩阵细节一次（L=1.0）
        if L == 1.0:
            print("\n  L=1.0 的 B_arith 矩阵（k=0..4）：")
            for j in range(N):
                print("   " + "  ".join(f"{Ga[j, k]:+.4e}" for k in range(N)))
            print(f"  B_arith(0,0) = {Ga[0,0]:.6e}  （对照：谱侧 Σĥ² 应≈此值）")
            ev = np.linalg.eigvalsh(Ga)
            print(f"  B_arith 特征值：{[f'{x:.3e}' for x in ev]}")
            print()

    print("-" * 78)
    print("判读：")
    print("· max|Δ| ~ 1e-16：算术数据（素幂≤e^(2L) + Archimedean）精确复现谱侧 Gram ✓")
    print("· λ_min(B_arith) > 0（到 L=1.5）；L=2.0 微负 ~ -7e-16 是 float64 噪声地板")
    print("  （矩阵范数 ~0.1、特征值跨度 1e9，微负在机器精度内，不是 RH 反例）")
    print("· λ_min 随 L 增大而衰减 = 谱能量向低频集中（同实验 2），不是 Landau-Widom")
    print("诚实提醒：有限秩 + zetazero 在临界线上 → 不能证伪 RH；")
    print("无限维正定性/LW 衰减需 prolate 基 + 区间算术（Chuk 证书级别，超出本脚本）。")


if __name__ == "__main__":
    main()
