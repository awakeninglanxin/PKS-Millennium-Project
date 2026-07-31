#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 3: 锥面坐标系下的 NS 方程重写
=================================
纯坐标变换练习: 将不可压缩 NS 方程从笛卡尔坐标转换到
PKS 锥面坐标系 (r, theta, z) 其中 z 由锥面约束 xy=1 决定。

本脚本:
  1. 写出笛卡尔 NS 的符号形式
  2. 定义锥面坐标系 (r, theta, z) 及其度量张量
  3. 在锥面坐标系下展开 NS 的各项
  4. 识别曲率依赖的"几何阻尼"项

不声称:
  - NS 在锥面上有光滑解
  - "几何阻尼"保证不爆破
  - PKS 解决了 NS 千禧难题

日期: 2026-06-13
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os, math, numpy as np

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
# 1. 锥面度量
# ============================================================
def cone_metric(x, y, z0=5.0):
    """
    PKS 锥面: z = f(r) where xy=1 旋转体。
    在柱坐标 (r, phi, z): r = sqrt(x^2+y^2), 锥面 z = C_1 - C_2 ln(r)

    锥面切向量:
      e_r = (cos phi, sin phi, dz/dr) = (cos phi, sin phi, -C_2/r)
      e_phi = (-sin phi, cos phi, 0)

    度量张量 g_ij:
      g_rr = 1 + (dz/dr)^2 = 1 + C_2^2/r^2
      g_rphi = 0
      g_phiphi = r^2
    """
    C_2 = z0 / np.log(10)  # 锥面参数: z drops by z0 over r=1 to 10
    C_1 = z0 + C_2 * np.log(10)

    g_rr = 1.0 + (C_2 / x)**2  # x = r approx
    g_phiphi = x**2
    det_g = g_rr * g_phiphi  # = r^2 + C_2^2

    # Christoffel symbols (2D submanifold)
    # Gamma^r_{rr} = (1/2) g^{rr} d_r g_{rr}
    Gamma_rr_r = -C_2**2 / (x**3 * g_rr)
    Gamma_rphiphi = -x / g_rr  # Gamma^r_{phi phi}
    Gamma_phirphi = 1.0 / x   # Gamma^phi_{r phi} = Gamma^phi_{phi r}

    return dict(
        g_rr=g_rr, g_phiphi=g_phiphi, det_g=det_g,
        C_1=C_1, C_2=C_2,
        Gamma_rr_r=Gamma_rr_r,
        Gamma_rphiphi=Gamma_rphiphi,
        Gamma_phirphi=Gamma_phirphi,
    )


def compute_curvature(r, z0=5.0):
    """锥面在半径 r 处的高斯曲率和平均曲率。"""
    C_2 = z0 / np.log(10)
    # 旋转曲面 r -> (r, 0, C_1 - C_2 ln r) 的曲率
    # 第一基本形式系数
    E = 1.0 + (C_2 / r)**2  # g_rr
    G = r**2
    # 法向量 (approx)
    k_gauss = -C_2**2 / (r**2 * (r**2 + C_2**2)**2) * r**2  # simplified
    k_mean = C_2 / (2 * r * np.sqrt(r**2 + C_2**2))  # approx

    return dict(k_gauss=k_gauss, k_mean=k_mean, E=E, G=G)


# ============================================================
# 2. NS 方程在锥面坐标下的各项
# ============================================================
def ns_terms_on_cone(r, u_r, u_phi, z0=5.0, nu=0.01):
    """
    计算锥面坐标系下 NS 动量方程的各项。
    使用非正交坐标下的协变导数。

    动量: Du^i/Dt = -g^{ij} d_j p + nu * Delta_g u^i + f_cone^i

    其中 f_cone 是锥面约束产生的几何力:
      f_cone^r = -kappa(r) * u^r   (曲率阻尼)
      f_cone^phi = 0
    """
    C_2 = z0 / np.log(10)

    # 对流项 (简化: 忽略 phi 导数, 仅径向流)
    conv_r = u_r * (-C_2 * u_r / r**2) if r > 0 else 0

    # 粘性项 (2D 锥面上的 Laplace-de Rham)
    lap_r = nu * (-C_2**2 * u_r / r**4) if r > 0 else 0

    # 锥面约束力: 曲率依赖
    kappa = C_2 / (r * np.sqrt(r**2 + C_2**2)) if r > 0 else 0
    cone_force_r = -kappa * abs(u_r)  # 曲率阻尼, 近似 β=2

    # 总加速度
    accel_r = conv_r + lap_r + cone_force_r

    return dict(
        conv_r=conv_r,
        lap_r=lap_r,
        cone_force_r=cone_force_r,
        accel_r=accel_r,
        kappa=kappa,
    )


# ============================================================
# 3. 几何阻尼系数可视化
# ============================================================
def main():
    r = np.linspace(0.5, 10, 200)
    z0_vals = [3.0, 5.0, 10.0]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    colors = ['#DC2626', '#2563EB', '#059669']
    labels = ['z0=3 (陡锥)', 'z0=5 (标准)', 'z0=10 (缓锥)']

    for row, z0 in enumerate(z0_vals):
        C_2 = z0 / np.log(10)

        # 面板1: 锥面轮廓 z(r)
        ax = axes[0, row]
        z = z0 + C_2 * np.log(10) - C_2 * np.log(r)
        ax.plot(r, z, color=colors[row], linewidth=2)
        ax.set_xlabel('r')
        ax.set_ylabel('z')
        ax.set_title(f'{labels[row]}\nz(r) = C - C2 ln r', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, z.max()*1.1)

        # 面板2: 曲率 kappa(r)
        ax = axes[1, row]
        kappa = C_2 / (r * np.sqrt(r**2 + C_2**2))
        ax.plot(r, kappa, color=colors[row], linewidth=2)
        ax.set_xlabel('r')
        ax.set_ylabel('kappa (曲率)')
        ax.set_title(f'曲率 kappa(r) ~ 1/r^2', fontsize=9)
        ax.grid(True, alpha=0.3)

        # 标注几何阻尼区域
        ax.axvspan(0.5, 2.0, alpha=0.1, color='red')
        ax.text(1.2, kappa.max()*0.8, '强阻尼区\nbeta~3', fontsize=7,
                color='red', ha='center')
        ax.axvspan(3.0, 10, alpha=0.1, color='green')
        ax.text(6.0, kappa.max()*0.3, '弱阻尼区\nbeta~1', fontsize=7,
                color='green', ha='center')

    # 全局图注
    fig.text(0.5, 1.02,
             'PKS 锥面坐标系: 曲率依赖的几何阻尼 (纯坐标变换, 不声称NS爆破解决)',
             ha='center', fontsize=11, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    path = os.path.join(SCRIPT_DIR, "fig_task3_conical_ns.png")
    fig.savefig(path, dpi=180)
    plt.close(fig)
    print(f"[OK] {path}")

    # 打印数值结果
    print("\n=== 锥面坐标系 NS 各项 (r=1.0, u_r=1.0) ===")
    for z0 in z0_vals:
        terms = ns_terms_on_cone(1.0, 1.0, 0.0, z0)
        print(f"\nz0={z0} (C2={z0/np.log(10):.2f}):")
        print(f"  kappa = {terms['kappa']:.4f}")
        print(f"  对流项 = {terms['conv_r']:.4f}")
        print(f"  粘性项 = {terms['lap_r']:.6f}")
        print(f"  锥面约束力 = {terms['cone_force_r']:.4f}")
        print(f"  → 总加速度 = {terms['accel_r']:.4f}")

    print("\n◆ 诚实声明 ◆")
    print("  本脚本仅执行坐标变换, 未求解 NS 方程。")
    print("  '几何阻尼' 是启发式概念, 非严格数学证明。")
    print("  锥面约束力项在一般 NS 框架中没有被证明为正则化项。")


if __name__ == "__main__":
    main()
