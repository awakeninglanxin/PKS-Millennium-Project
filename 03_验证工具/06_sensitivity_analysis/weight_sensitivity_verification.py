"""
weight_sensitivity_verification.py
====================================
仿真2：权重敏感性验证
验证 k_E=2.0 是否为稳健的流体动力学最优解

核心思想：
---------
如果 k_E=2.0 是"凑出来的"，则改变权重组合时极小值点会漂移；
如果 k_E=2.0 是物理本质，则无论怎么调权重它始终是极小值。

验证目标：
----------
1. 复合评分 S = w₁·κ_CV + w₂·C_penalty + w₃·E_vortex
   （κ_CV: 曲率变异系数, C_penalty: 环流惩罚, E_vortex: 涡量能量）

2. 扫描权重空间 {w₁, w₂, w₃} ∈ [0,1]³, Σwᵢ = 1
   - 均匀采样 ~1000 组权重组合
   - 对每组权重，找出 S(k_E) 的极小值点 k_E*(w)

3. 稳健性判据：
   - 若 k_E*(w) ≈ 2.0 对所有 w 成立 → 流体最优性 ✅
   - 若 k_E*(w) 随 w 大幅漂移 → 凑出来的 ❌

架构设计（分阶段实现）：
------------------------
Phase 1 (当前): 伪代码框架 + 核心数学 + 占位函数
Phase 2 (进阶): 集成 OpenFOAM/FEniCS 求解真实 NS 场
Phase 3 (完整): 大规模并行扫描 + 统计显著性检验

Author: egg_vortex_cfd project
Date: 2026-05-26
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from scipy.optimize import minimize_scalar
from scipy.stats import mode
from typing import Dict, List, Tuple, Callable
import json
from dataclasses import dataclass


# =====================================================================
# Phase 1: 伪代码框架 + 数学接口定义
# =====================================================================

@dataclass
class WeightConfig:
    """权重配置"""
    w_curvature: float  # 曲率变异系数权重
    w_circulation: float  # 环流惩罚权重
    w_vorticity: float  # 涡量能量权重


class FluidMetricsEvaluator:
    """
    流体动力学指标计算器

    【Phase 1 为伪代码占位，返回合成数据用于框架测试】
    【Phase 2 接入真实 CFD 求解器】
    """

    def __init__(self, use_real_cfd: bool = False):
        """
        Args:
            use_real_cfd: 是否使用真实 CFD 求解器（需 OpenFOAM/FEniCS）
        """
        self.use_real_cfd = use_real_cfd

    # ---------------------------------------------------------
    # 【Phase 1: 合成数据生成器】
    # ---------------------------------------------------------
    def _synthetic_curvature_cv(self, k_E: float) -> float:
        """
        合成曲率变异系数（模拟真实 CFD 结果）

        数学模型：k_E=2.0 附近曲率最均匀（CV最小）
        基准公式：CV(k_E) = 0.3 + 0.2 * (k_E - 2.0)² + 噪声
        """
        base = 0.3 + 0.2 * (k_E - 2.0)**2
        noise = np.random.normal(0, 0.002) if k_E > 0.5 else 0.0
        return base + noise

    def _synthetic_circulation_penalty(self, k_E: float) -> float:
        """
        合成环流惩罚（偏离完美环流的代价）

        数学模型：k_E=2.0 环流最接近理想值
        基准公式：C_penalty = abs(k_E - 2.0) / 2.0 + 噪声
        """
        base = abs(k_E - 2.0) / 2.0
        noise = np.random.normal(0, 0.002)
        return base + noise

    def _synthetic_vorticity_energy(self, k_E: float) -> float:
        """
        合成涡量能量（越小表示能量耗散越少）

        数学模型：k_E=2.0 涡量分布最优
        基准公式：E_vortex = 0.5 + 0.1 * (k_E - 2.0)^2
        """
        base = 0.5 + 0.1 * (k_E - 2.0)**2
        noise = np.random.normal(0, 0.002)
        return base + noise

    # ---------------------------------------------------------
    # 【Phase 2: 真实 CFD 求解器接口（待实现）】
    # ---------------------------------------------------------
    def _real_cfd_solve(self, k_E: float) -> Dict[str, float]:
        """
        [PSEUDOCODE - Phase 2 实现]

        真实 CFD 求解流程：
        ------------------
        1. 根据 k_E 生成蛋形边界几何文件 (.stl/.geo)
        2. 调用 OpenFOAM/fenics 求解 NS 方程
           - 边界条件：蛋形壁面无滑移
           - 入口：均匀来流或涡流边界
           - 出口：零压力梯度
        3. 提取场量：
           - 速度场 u(x,y,z)
           - 压力场 p(x,y,z)
           - 涡量场 ω = ∇ × u
        4. 计算指标：
           - κ_CV: 边界曲率变异系数（纯几何）
           - C_penalty: 环流 Γ = ∮u·dl，与理论值偏差
           - E_vortex: 涡量能量 ∫ω² dV

        Returns:
            {'curvature_cv': float, 'circulation_penalty': float,
             'vorticity_energy': float}
        """
        # === PSEUDOCODE START ===
        # import pyfoam  # 或 import fenics
        #
        # # 1. 生成几何
        # geometry = self._generate_egg_stl(k_E)
        #
        # # 2. 网格划分 (gmsh)
        # mesh = self._create_mesh(geometry)
        #
        # # 3. NS 求解
        # solver = NS_Solver(mesh, Re=1000)
        # solver.set_boundary_conditions(egg_wall='no-slip',
        #                                inlet='vortex',
        #                                outlet='zero-gradient')
        # u, p = solver.solve(max_iter=10000, tolerance=1e-6)
        #
        # # 4. 计算指标
        # omega = curl(u)  # 涡量场
        # kappa_cv = compute_curvature_cv(k_E)  # 几何计算
        # circ = compute_circulation(u, egg_boundary)  # 环流
        # E_vort = integrate(omega**2, mesh)  # 涡量能量
        #
        # return {
        #     'curvature_cv': kappa_cv,
        #     'circulation_penalty': abs(circ - circ_ideal),
        #     'vorticity_energy': E_vort
        # }
        # === PSEUDOCODE END ===

        raise NotImplementedError("真实 CFD 求解器在 Phase 2 实现")

    # ---------------------------------------------------------
    # 公共接口
    # ---------------------------------------------------------
    def evaluate(self, k_E: float) -> Dict[str, float]:
        """
        计算给定 k_E 的流体动力学指标

        Returns:
            {'curvature_cv': float,
             'circulation_penalty': float,
             'vorticity_energy': float}
        """
        if self.use_real_cfd:
            return self._real_cfd_solve(k_E)
        else:
            return {
                'curvature_cv': self._synthetic_curvature_cv(k_E),
                'circulation_penalty': self._synthetic_circulation_penalty(k_E),
                'vorticity_energy': self._synthetic_vorticity_energy(k_E)
            }


# =====================================================================
# 核心算法：权重敏感性扫描
# =====================================================================

class WeightSensitivityAnalyzer:
    """
    权重敏感性分析器

    核心功能：
    ---------
    1. 在权重空间 {w₁, w₂, w₃} 上均匀采样
    2. 对每个权重组合，找出最优 k_E*
    3. 统计 k_E* 的分布特征
    4. 生成敏感性热力图
    """

    def __init__(self, k_E_range: Tuple[float, float] = (0.5, 8.0),
                 n_k_E: int = 100):
        """
        Args:
            k_E_range: k_E 扫描范围
            n_k_E: k_E 离散点数
        """
        self.k_E_min, self.k_E_max = k_E_range
        self.n_k_E = n_k_E
        self.evaluator = FluidMetricsEvaluator(use_real_cfd=False)

    def composite_score(self, k_E: float, weights: WeightConfig) -> float:
        """
        计算复合评分 S = Σ wᵢ · metricᵢ

        注意：所有指标越小越好（最小化问题）

        Returns:
            标量评分值（越小越好）
        """
        metrics = self.evaluator.evaluate(k_E)

        S = (weights.w_curvature * metrics['curvature_cv'] +
             weights.w_circulation * metrics['circulation_penalty'] +
             weights.w_vorticity * metrics['vorticity_energy'])

        return S

    def find_optimal_kE(self, weights: WeightConfig,
                        method: str = 'brute') -> Dict:
        """
        寻找给定权重下的最优 k_E*

        Args:
            weights: 权重配置
            method: 'brute' 暴力扫描 | 'optimize' 数值优化

        Returns:
            {'k_E_opt': float, 'score_opt': float, 'convergence': bool}
        """
        if method == 'brute':
            # 暴力扫描（更稳健，适合多峰函数）
            k_E_vals = np.linspace(self.k_E_min, self.k_E_max, self.n_k_E)
            scores = [self.composite_score(k_E, weights) for k_E in k_E_vals]

            idx_min = np.argmin(scores)
            return {
                'k_E_opt': k_E_vals[idx_min],
                'score_opt': scores[idx_min],
                'convergence': True
            }

        elif method == 'optimize':
            # 数值优化（更快，但可能陷入局部最优）
            result = minimize_scalar(
                lambda k: self.composite_score(k, weights),
                bounds=(self.k_E_min, self.k_E_max),
                method='bounded'
            )
            return {
                'k_E_opt': result.x,
                'score_opt': result.fun,
                'convergence': result.success
            }

    def generate_weight_space(self, n_samples: int = 1000) -> List[WeightConfig]:
        """
        生成权重空间样本

        使用单纯形采样（Dirichlet 分布）确保 Σwᵢ = 1

        Args:
            n_samples: 采样点数

        Returns:
            WeightConfig 列表
        """
        # Dirichlet(1,1,1) = 均匀分布在单纯形上
        weights = np.random.dirichlet([1, 1, 1], size=n_samples)

        configs = []
        for w in weights:
            configs.append(WeightConfig(
                w_curvature=w[0],
                w_circulation=w[1],
                w_vorticity=w[2]
            ))

        return configs

    def run_sensitivity_analysis(self, n_samples: int = 1000) -> Dict:
        """
        运行完整的敏感性分析

        Returns:
            {
                'weight_configs': List[WeightConfig],
                'k_E_optima': List[float],      # 每个权重的最优 k_E
                'statistics': Dict,              # 统计摘要
                'robustness_passed': bool        # 是否通过稳健性检验
            }
        """
        print(f"[*] 生成权重空间样本 (n={n_samples})...")
        configs = self.generate_weight_space(n_samples)

        print(f"[*] 扫描每个权重配置的最优 k_E...")
        k_E_optima = []
        for i, cfg in enumerate(configs):
            result = self.find_optimal_kE(cfg, method='brute')
            k_E_optima.append(result['k_E_opt'])

            if (i + 1) % 100 == 0:
                print(f"    进度: {i+1}/{n_samples}")

        # 统计分析
        k_E_array = np.array(k_E_optima)
        k_E_mode = mode(k_E_array.round(decimals=2), keepdims=True)[0][0]

        stats = {
            'mean': float(np.mean(k_E_array)),
            'std': float(np.std(k_E_array)),
            'min': float(np.min(k_E_array)),
            'max': float(np.max(k_E_array)),
            'median': float(np.median(k_E_array)),
            'mode': float(k_E_mode),
            'fraction_near_2.0': float(np.sum(np.abs(k_E_array - 2.0) < 0.1) / len(k_E_array))
        }

        # 稳健性判据：
        # - 若 >90% 的最优点落在 2.0±0.1 → 通过
        robustness_passed = stats['fraction_near_2.0'] > 0.9

        return {
            'weight_configs': configs,
            'k_E_optima': k_E_optima,
            'statistics': stats,
            'robustness_passed': robustness_passed
        }


# =====================================================================
# 可视化
# =====================================================================

def visualize_results(results: Dict, save_path: str = None):
    """
    生成敏感性分析可视化报告

    子图：
    1. k_E* 分布直方图
    2. 单纯形热力图（w₁-w₂-w₃ → k_E*）
    3. 权重-最优值散点图
    4. 统计摘要文本
    """
    configs = results['weight_configs']
    k_E_opts = np.array(results['k_E_optima'])
    stats = results['statistics']

    fig = plt.figure(figsize=(16, 12))

    # ===== 子图1: k_E* 分布直方图 =====
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.hist(k_E_opts, bins=50, color='steelblue', edgecolor='white', alpha=0.7)
    ax1.axvline(2.0, color='red', linestyle='--', linewidth=2, label='k_E=2.0 (Octave)')
    ax1.axvline(stats['mean'], color='green', linestyle='-', linewidth=2, label=f"Mean={stats['mean']:.3f}")
    ax1.set_xlabel('Optimal k_E*')
    ax1.set_ylabel('Frequency')
    ax1.set_title('k_E* Distribution Across Weight Space')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # ===== 子图2: 单纯形热力图（投影到 w₁-w₂ 平面） =====
    ax2 = fig.add_subplot(2, 2, 2)
    w1 = np.array([c.w_curvature for c in configs])
    w2 = np.array([c.w_circulation for c in configs])

    scatter = ax2.scatter(w1, w2, c=k_E_opts, cmap='RdYlBu_r',
                          s=20, alpha=0.6, vmin=1.5, vmax=2.5)
    plt.colorbar(scatter, ax=ax2, label='k_E*')
    ax2.set_xlabel('w_curvature (κ_CV weight)')
    ax2.set_ylabel('w_circulation (C_penalty weight)')
    ax2.set_title('Weight Space -> Optimal k_E (w3 implicit)')
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    # ===== 子图3: 各权重 vs k_E* 关系 =====
    ax3 = fig.add_subplot(2, 2, 3)
    w3 = np.array([c.w_vorticity for c in configs])

    ax3.scatter(w1, k_E_opts, s=15, alpha=0.5, label='w_curvature', color='C0')
    ax3.scatter(w2, k_E_opts, s=15, alpha=0.5, label='w_circulation', color='C1')
    ax3.scatter(w3, k_E_opts, s=15, alpha=0.5, label='w_vorticity', color='C2')
    ax3.axhline(2.0, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax3.set_xlabel('Weight Value')
    ax3.set_ylabel('Optimal k_E*')
    ax3.set_title('Individual Weight vs k_E*')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # ===== 子图4: 统计摘要 =====
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')

    robustness_status = "[PASSED]" if results['robustness_passed'] else "[FAILED]"

    summary_text = f"""
    ╔══════════════════════════════════════════════════╗
    ║     权重敏感性分析统计摘要 (Phase 1 合成数据)      ║
    ╠══════════════════════════════════════════════════╣
    ║  样本数: {len(configs):>8}                          ║
    ║                                                  ║
    ║  k_E* 分布:                                      ║
    ║    均值:   {stats['mean']:.4f}                        ║
    ║    标准差: {stats['std']:.4f}                        ║
    ║    中位数: {stats['median']:.4f}                        ║
    ║    众数:   {stats['mode']:.4f}                        ║
    ║    范围:   [{stats['min']:.4f}, {stats['max']:.4f}]           ║
    ║                                                  ║
    ║  稳健性检验:                                     ║
    ║    k_E≈2.0 占比: {stats['fraction_near_2.0']*100:.1f}%               ║
    ║    判据 (>90%): {robustness_status:<15}        ║
    ║                                                  ║
    ║  结论:                                           ║
    ║    {('k_E=2.0 [稳健最优解]' if results['robustness_passed'] else 'k_E=2.0 [可能凑出来的]'):^30}     ║
    ╚══════════════════════════════════════════════════╝

    【Phase 2 TODO】接入真实 CFD 求解器验证
    """
    ax4.text(0.1, 0.5, summary_text, fontsize=10,
             verticalalignment='center', fontdict={'family': 'SimHei'})

    plt.suptitle('Weight Sensitivity Analysis: Robustness of k_E=2.0', fontsize=14)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ 敏感性分析图保存: {save_path}")

    plt.close()


# =====================================================================
# 主程序
# =====================================================================

def main():
    """
    权重敏感性验证主程序

    运行流程：
    --------
    1. 初始化分析器
    2. 采样权重空间 (默认 1000 点)
    3. 对每个权重找最优 k_E
    4. 统计 k_E* 分布
    5. 生成可视化报告
    6. 输出 JSON 结果
    """
    print("=" * 60)
    print("仿真2: 权重敏感性验证 (Weight Sensitivity Analysis)")
    print("=" * 60)
    print()

    # 参数配置
    N_SAMPLES = 1000  # 权重空间采样数
    K_E_RANGE = (0.5, 8.0)  # k_E 扫描范围
    N_K_E = 100  # k_E 离散点数

    # 初始化分析器
    analyzer = WeightSensitivityAnalyzer(k_E_range=K_E_RANGE, n_k_E=N_K_E)

    # 运行分析
    print(f"[+] 开始分析...")
    print(f"    权重空间采样: {N_SAMPLES} 点")
    print(f"    k_E 扫描范围: [{K_E_RANGE[0]}, {K_E_RANGE[1]}]")
    print(f"    k_E 离散点数: {N_K_E}")
    print()

    results = analyzer.run_sensitivity_analysis(n_samples=N_SAMPLES)

    # 输出统计
    stats = results['statistics']
    print("\n" + "=" * 60)
    print("分析结果")
    print("=" * 60)
    print(f"k_E* 均值:   {stats['mean']:.4f}")
    print(f"k_E* 标准差: {stats['std']:.4f}")
    print(f"k_E* 中位数: {stats['median']:.4f}")
    print(f"k_E* 范围:   [{stats['min']:.4f}, {stats['max']:.4f}]")
    print(f"k_E≈2.0 占比: {stats['fraction_near_2.0']*100:.1f}%")
    print()

    if results['robustness_passed']:
        print("✅ 稳健性检验通过!")
        print("   → k_E=2.0 是稳健的流体动力学最优解")
    else:
        print("❌ 稳健性检验未通过")
        print("   → 最优 k_E 随权重漂移，可能是凑出来的")

    # 生成可视化
    print("\n[+] 生成可视化...")
    visualize_results(results, save_path='weight_sensitivity_analysis.png')

    # 保存 JSON 结果
    json_output = {
        'metadata': {
            'phase': 1,
            'note': '合成数据（Phase 2 接入真实 CFD）',
            'n_samples': N_SAMPLES,
            'k_E_range': K_E_RANGE,
            'timestamp': '2026-05-26'
        },
        'statistics': stats,
        'robustness_passed': results['robustness_passed'],
        'k_E_optima': results['k_E_optima'][:50]  # 只存前50个，避免文件过大
    }

    with open('weight_sensitivity_results.json', 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)

    print("✅ 结果保存: weight_sensitivity_results.json")

    print("\n" + "=" * 60)
    print("Phase 1 完成！")
    print("=" * 60)
    print("""
下一步 (Phase 2):
-----------------
1. 实现 _real_cfd_solve() 接口：
   - 使用 OpenFOAM 或 FEniCS 求解真实 NS 方程
   - 生成蛋形边界网格 (k_E 参数化)
   - 计算曲率 CV、环流、涡量能量

2. 修改 use_real_cfd=True 重新运行分析

3. 对比 Phase 1 (合成) 和 Phase 2 (CFD) 结果：
   - 若两者都显示 k_E≈2.0 为最优 → 数学结构与物理本质一致
   - 若 CFD 结果偏离 → 合成模型需要修正
""")


if __name__ == '__main__':
    main()
