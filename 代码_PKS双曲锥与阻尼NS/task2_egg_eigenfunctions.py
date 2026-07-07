#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 2: 蛋形域本征函数求解器
=============================
将椭圆压力求解器(elliptic_pressure_solver.py)推广到蛋形域。

方法: 坐标拉伸法 — 将蛋形映射回单位圆, 在拉伸坐标下求解 Helmholtz:
  Delta phi + lambda * phi = 0    (蛋形域, Dirichlet BC)

本脚本只计算本征值序列, 与椭圆域对比, 验证:
  - 蛋形的 lambda_n 是否按 ~ln n 增长 (蛋形谐波猜想)
  - 椭圆的 lambda_n 是否按 ~n 增长 (Mathieu/Weyl)

不声称:
  - 蛋形域上 NS 解的存在性
  - 本征值与 k_E 的解析关系

日期: 2026-06-13
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os, math, numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

# ============================================================
# 铁律: matplotlib 中文三步
# ============================================================
_cache_dir = matplotlib.get_cachedir()
for _f in os.listdir(_cache_dir):
    if _f.endswith('.json'):
        try: os.remove(os.path.join(_cache_dir, _f))
        except OSError: pass
fm._load_fontmanager(try_read_cache=False)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# 1. 蛋形 → 单位圆 坐标映射
# ============================================================
def egg_to_circle_mapping(z0=5.0, alpha_deg=33.69):
    """
    构建从蛋形域到单位圆的径向拉伸因子。
    蛋形: r_bound(theta) = f(theta), 不同theta有不同的径向范围。
    映射: r_egg(r_circle, theta) = r_circle * r_bound(theta)
    将 Helmholtz 在拉伸坐标下离散。
    """
    alpha = np.radians(alpha_deg)

    def r_bound(th):
        """蛋形边界在角度 theta 处的 r"""
        th = abs(th)
        if th < 1e-6: th = 1e-6
        x_min = 0.05
        x_max = 1.0 / max(z0 - 2.0 * np.sin(alpha), 0.1)
        x = np.linspace(x_min, x_max, 500)
        y_bound = 1.0 / x
        # 找角度 th 对应的 r
        for i, xx in enumerate(x):
            yy = y_bound[i]
            r_val = np.sqrt(xx**2 + yy**2)
            th_val = abs(np.arctan2(yy, xx))
            if abs(th_val - abs(th)) < 0.02:
                return r_val
        return y_bound[-1]  # fallback

    return r_bound


# ============================================================
# 2. 有限差分 Laplace 在拉伸坐标下
# ============================================================
def build_laplacian_egg(z0=5.0, alpha_deg=33.69, nr=40, nth=60):
    """
    在蛋形域上建立 5点 Laplace 算子 (有限差分)。
    使用物理坐标 (r, theta) 直接离散, 蛋形边界为 Dirichlet=0。
    """
    from task1_egg_jeffrey_hamel import build_grid

    r, th, mask = build_grid(z0, alpha_deg, nr, nth)
    dr = r[1] - r[0]
    dth = th[1] - th[0]

    # 给每个内部网格点分配序号
    idx_map = -np.ones((nr, nth), dtype=int)
    count = 0
    for i in range(nr):
        for j in range(nth):
            if mask[i, j]:
                idx_map[i, j] = count
                count += 1

    N = count
    if N == 0:
        return None, None, None, None

    # 构建稀疏矩阵
    A = sparse.lil_matrix((N, N))
    B = sparse.lil_matrix((N, N))  # 质量矩阵 (单位矩阵)

    for i in range(1, nr-1):
        for j in range(1, nth-1):
            k = idx_map[i, j]
            if k < 0: continue

            # 极坐标 Laplace: d2/dr2 + (1/r)d/dr + (1/r^2)d2/dth2
            rr = max(r[i], 1e-6)
            inv_r2 = 1.0 / (rr * rr)

            # r 方向二阶差分
            A[k, k] += -2.0 / (dr*dr)
            if idx_map[i-1, j] >= 0:
                A[k, idx_map[i-1, j]] += 1.0 / (dr*dr)
            if idx_map[i+1, j] >= 0:
                A[k, idx_map[i+1, j]] += 1.0 / (dr*dr)
            # 边界点(相邻mask=False): 吸收到对角 (Dirichlet=0 自然满足)

            # (1/r) d/dr: 中心差分
            if idx_map[i-1, j] >= 0 and idx_map[i+1, j] >= 0:
                A[k, idx_map[i+1, j]] += (1.0/rr) * 0.5/dr
                A[k, idx_map[i-1, j]] -= (1.0/rr) * 0.5/dr
            elif idx_map[i+1, j] >= 0:
                A[k, idx_map[i+1, j]] += (1.0/rr) / dr
                A[k, k] -= (1.0/rr) / dr
            elif idx_map[i-1, j] >= 0:
                A[k, k] -= (1.0/rr) / dr
                A[k, idx_map[i-1, j]] += (1.0/rr) / dr

            # theta 方向二阶差分
            A[k, k] += -2.0 * inv_r2 / (dth*dth)
            if idx_map[i, (j-1)%nth] >= 0:
                A[k, idx_map[i, (j-1)%nth]] += 1.0 * inv_r2 / (dth*dth)
            if idx_map[i, (j+1)%nth] >= 0:
                A[k, idx_map[i, (j+1)%nth]] += 1.0 * inv_r2 / (dth*dth)

            B[k, k] = 1.0

    A = A.tocsr()
    B = B.tocsr()
    return A, B, N, (r, th, mask)


# ============================================================
# 3. 椭圆域求解 (对照组)
# ============================================================
def build_laplacian_ellipse(a=2.0, b=1.0, nr=40, nth=60):
    """
    椭圆域 Laplace: (x/a)^2 + (y/b)^2 = 1, 极坐标下边界 r(theta).
    r_bound(th) = a*b / sqrt((b*cos(th))^2 + (a*sin(th))^2)
    """
    r = np.linspace(0.02, max(a, b) + 0.5, nr)
    th = np.linspace(0, 2*np.pi, nth)

    mask = np.zeros((nr, nth), dtype=bool)
    for i in range(nr):
        for j in range(nth):
            rr = r[i]
            x = rr * np.cos(th[j])
            y = rr * np.sin(th[j])
            if (x/a)**2 + (y/b)**2 <= 1.0:
                mask[i, j] = True

    dr = r[1] - r[0]
    dth = th[1] - th[0]

    idx_map = -np.ones((nr, nth), dtype=int)
    count = 0
    for i in range(nr):
        for j in range(nth):
            if mask[i, j]:
                idx_map[i, j] = count
                count += 1

    N = count
    if N == 0:
        return None, None, None

    A = sparse.lil_matrix((N, N))
    B = sparse.lil_matrix((N, N))

    for i in range(1, nr-1):
        for j in range(nth):
            k = idx_map[i, j]
            if k < 0: continue

            rr = max(r[i], 1e-6)
            inv_r2 = 1.0 / (rr * rr)

            A[k, k] += -2.0 / (dr*dr)
            if idx_map[i-1, j] >= 0:
                A[k, idx_map[i-1, j]] += 1.0 / (dr*dr)
            if idx_map[i+1, j] >= 0:
                A[k, idx_map[i+1, j]] += 1.0 / (dr*dr)

            jp = (j-1) % nth
            jn = (j+1) % nth
            A[k, k] += -2.0 * inv_r2 / (dth*dth)
            if idx_map[i, jp] >= 0:
                A[k, idx_map[i, jp]] += 1.0 * inv_r2 / (dth*dth)
            if idx_map[i, jn] >= 0:
                A[k, idx_map[i, jn]] += 1.0 * inv_r2 / (dth*dth)

            B[k, k] = 1.0

    A = A.tocsr()
    B = B.tocsr()
    return A, B, N


# ============================================================
# 4. 主流程
# ============================================================
def main():
    print("计算蛋形域本征值...")
    A_egg, B_egg, N_egg, grid = build_laplacian_egg(5.0, 33.69, nr=50, nth=70)
    if A_egg is not None:
        evals_egg, _ = eigsh(-A_egg, k=30, M=B_egg, which='LM', sigma=0)
        evals_egg = sorted(abs(evals_egg))
    else:
        evals_egg = []

    print("计算椭圆域本征值 (对照)...")
    A_ell, B_ell, N_ell = build_laplacian_ellipse(2.0, 1.0, nr=50, nth=70)
    if A_ell is not None:
        evals_ell, _ = eigsh(-A_ell, k=30, M=B_ell, which='LM', sigma=0)
        evals_ell = sorted(abs(evals_ell))
    else:
        evals_ell = []

    # ============================================================
    # 出图
    # ============================================================
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    # 面板1: 本征值对比
    ax = axes[0]
    n_egg = np.arange(1, len(evals_egg)+1)
    n_ell = np.arange(1, len(evals_ell)+1)
    ax.plot(n_egg, evals_egg, 'ro-', markersize=4, label=f'蛋形 (N={N_egg})')
    ax.plot(n_ell, evals_ell, 'bs-', markersize=4, label=f'椭圆 (N={N_ell})')
    ax.set_xlabel('n (本征序号)')
    ax.set_ylabel('lambda_n')
    ax.set_title('本征值: 蛋形 vs 椭圆 (Dirichlet)', fontweight='bold')
    ax.legend(fontsize=8)
    ax.set_yscale('log')

    # 面板2: 增长率测试 (Weil vs log)
    ax = axes[1]
    if len(evals_egg) > 5:
        # 拟合: lambda_n ~ C * n^p (Weyl) or ~ C * ln(n) (蛋形谐波)
        log_n = np.log(n_egg[2:])
        log_lam = np.log(evals_egg[2:])
        p_weyl, _ = np.polyfit(log_n, log_lam, 1)

        # 对数拟合
        lam_vs_ln = np.polyfit(np.log(n_egg[2:]), evals_egg[2:], 1)

        ax.plot(n_egg, evals_egg, 'ro-', markersize=4, label='蛋形数据')
        # Weyl: lambda = C * n
        ax.plot(n_egg, evals_egg[0] * n_egg / n_egg[0], 'g--', linewidth=1,
                label=f'Weyl ~ n (斜率理论=1)')
        ax.plot(n_egg, evals_egg[0] * np.log(n_egg + 1) / np.log(2), 'b--', linewidth=1,
                label=f'蛋形谐波 ~ ln n (猜想)')
        ax.set_xlabel('n')
        ax.set_ylabel('lambda_n')
        ax.set_title(f'增长模式检验 (Weyl指数={p_weyl:.2f})', fontweight='bold')
        ax.legend(fontsize=7)

    # 面板3: 诚实声明
    ax = axes[2]
    ax.axis('off')
    lines = [
        f"蛋形域网格点数: {N_egg}",
        f"椭圆域网格点数: {N_ell}",
        f"蛋形本征值范围: {evals_egg[0]:.3f} ~ {evals_egg[-1]:.3f}",
        f"椭圆本征值范围: {evals_ell[0]:.3f} ~ {evals_ell[-1]:.3f}",
        "",
        "结果解读:",
    ]
    if len(evals_egg) > 5:
        p_val = abs(p_weyl)
        if p_val > 1.5:
            lines.append("Weyl指数>1: 非均匀网格效应")
            lines.append("(蛋形尖端网格密度偏高)")
        elif p_val < 0.5:
            lines.append("Weyl指数<1: 蛋形谐波可能")
            lines.append("更接近 ~ln n 而非 ~n")
        else:
            lines.append(f"Weyl指数={p_val:.2f}: 标准2D行为")

    lines += [
        "",
        "诚实声明:",
        "有限差分,粗网格(nr=50,nth=70)",
        "未验证网格独立性",
        "Weyl定律要求网格足够密",
        "蛋形谐波 ~ln n 是猜想",
        "需更精细数值验证",
    ]
    for i, ln in enumerate(lines):
        ax.text(0.05, 0.95 - i*0.05, ln, transform=ax.transAxes,
                fontsize=8, va='top')

    fig.suptitle("蛋形域 vs 椭圆域 — Helmholtz 本征值对比",
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    path = os.path.join(SCRIPT_DIR, "fig_task2_egg_eigenvalues.png")
    fig.savefig(path, dpi=180)
    plt.close(fig)
    print(f"[OK] {path}")

    if len(evals_egg) > 5:
        print(f"\n蛋形本征值 (前10): {[f'{e:.3f}' for e in evals_egg[:10]]}")
        print(f"椭圆本征值 (前10): {[f'{e:.3f}' for e in evals_ell[:10]]}")
        print(f"蛋形 Weyl 指数 = {p_weyl:.3f} (理论: 2D=1, 蛋形谐波猜想 ~ln n 对应 p→0)")


if __name__ == "__main__":
    main()
