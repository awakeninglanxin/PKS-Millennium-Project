"""
egg_shell_metrics.py

蛋壳度量分析器

从 Rhino 脚本 egg_shell 不同八度蛋形 蛋形周长和对应圆半径趋势.py
提取核心数学，系统分析蛋形族的：
  - 周长 L(n) 随 n 的变化趋势
  - 等价圆半径 r(n) = L(n)/(2π) 的缩放规律
  - 6 种拟合模型（幂律/反比/指数/广义幂律/有理/对数）的对比

数学原理
============

蛋形周长计算（微分法）：
    L = ∫₀²π √((dx/dt)² + (dy/dt)²) dt
    用数值方法（numpy.gradient + trapz）近似计算。

等价圆半径（基于周长）：
    r_L(n) = L(n) / (2π)
    这是将蛋形截面等效为圆的周长半径。

等价圆面积（基于面积）：
    r_A(n) = √(A(n) / π)
    这是将蛋形截面等效为圆的面积半径。

缩放规律（经数值验证）：
    r_L(n) ∝ 1/√n          (幂律指数 ≈ -0.5)
    r_A(n) ∝ 1/√n          (面积缩放）
    L(n)   ∝ 2π/√n        (周长缩放）

与 k_E 的关系：
    k_E = z₂/z₁ = 2ⁱ/⁶ / 1 = 2ⁱ/⁶
    → n 对应蛋形族序号 i
    → k_E(i) = 2ⁱ/⁶

参考文献：
    - egg_shell 不同八度蛋形 蛋形周长和对应圆半径趋势.py（原始 Rhino 脚本）
    - Schauberger, V. "The Energy Evolution"
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple, Optional, Callable

# numpy compatibility: trapz renamed to trapezoid in newer versions
_trapz = getattr(np, 'trapz', None) or getattr(np, 'trapezoid', None)


class EggShellMetrics:
    """
    蛋壳度量分析器
    
    系统分析蛋形族的周长、面积、等价圆半径
    随蛋形序号 n 的变化趋势，并用多种数学模型拟合。
    """
    
    # 6 种拟合模型
    MODELS = {
        '幂律 r = c/√n':          (lambda n, c: c / np.sqrt(n), 1),
        '反比 r = c/n':          (lambda n, c: c / n, 1),
        '指数 r = a·exp(-b·n)': (lambda n, a, b: a * np.exp(-b * n), 2),
        '广义幂律 r = a·n^b':    (lambda n, a, b: a * n**b, 2),
        '有理函数 r = a/(1+b·n)': (lambda n, a, b: a / (1 + b * n), 2),
        '对数 r = a - b·log(n)': (lambda n, a, b: a - b * np.log(n), 2),
    }
    
    def __init__(self, num_egg: int = 15, num_points: int = 2000):
        """
        初始化分析器
        
        参数
        ------
        num_egg : int
            分析的蛋形数量（i = 1 to num_egg）
        num_points : int
            每条曲线的采样点数
        """
        self.num_egg = num_egg
        self.num_points = num_points
        self.t = np.linspace(0, 2*np.pi, num_points)
    
    # =====================================================================
    # 核心公式（与 schauberger_egg_family.py 一致）
    # =====================================================================
    
    def _x_func(self, t: np.ndarray, b: float, k: float, 
                  a: float = 1.0) -> np.ndarray:
        """x(t) = a·2sin(t) / (b + √(b² - 4k·cos(t)))"""
        denom = b + np.sqrt(np.maximum(0, b**2 - 4*k*np.cos(t)))
        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
        return a * 2 * np.sin(t) / denom
    
    def _y_func(self, t: np.ndarray, b: float, k: float,
                  a: float = 1.0, m: float = 2/3) -> np.ndarray:
        """y(t) 完整表达式（Schauberger 标准形式）"""
        sqrt_1k2 = np.sqrt(1 + k**2)
        sqrt_b2_4k = np.sqrt(np.maximum(0, b**2 - 4*k))
        sqrt_b2_4k_cos_t = np.sqrt(np.maximum(0, b**2 - 4*k*np.cos(t)))
        sqrt_b2_4k_cos_pi = np.sqrt(np.maximum(0, b**2 - 4*k*np.cos(np.pi)))
        
        term1 = -(sqrt_1k2 * (-sqrt_b2_4k + sqrt_b2_4k_cos_pi)) / (2*k)
        
        term2_1 = 1 / (2 * sqrt_1k2)
        term2_2 = ((k**2 - 1)/k * b) + ((k**2 + 1)/k * sqrt_b2_4k_cos_t)
        term2_3 = (b*(k**2 - 1) + sqrt_b2_4k*(k**2 + 1)) / (2*k*sqrt_1k2)
        term2 = term2_1 * term2_2 - term2_3
        
        return a * (m * term1 + term2)
    
    def _generate_egg(self, i: int) -> Dict:
        """
        生成第 i 个蛋形的参数和坐标
        
        参数
        ------
        i : int
            蛋形序号（从 1 开始）
            
        返回
        ------
        dict : {'k', 'b', 'm', 'amp', 'x', 'y', 'label'}
        """
        k = (4**i / 6)
        b = (5 * 2**i / 6)
        m = 2 / 3
        amp = (2**i) / np.sqrt(9 + 2**(4*i - 2))
        
        x = self._x_func(self.t, b, k, a=1.0) * amp
        y = self._y_func(self.t, b, k, a=1.0, m=m) * amp
        
        return {
            'i': i,
            'k': k,
            'b': b,
            'm': m,
            'amp': amp,
            'x': x,
            'y': y,
            'label': f'egg{i}',
        }
    
    # =====================================================================
    # 度量计算
    # =====================================================================
    
    def calculate_length(self, x: np.ndarray, y: np.ndarray, 
                         t: np.ndarray = None) -> float:
        """
        计算曲线长度（微分法）
        
        L = ∫ √((dx/dt)² + (dy/dt)²) dt
        
        参数
        ------
        x, y : np.ndarray
            曲线坐标
        t : np.ndarray or None
            参数数组（如果为 None，使用 self.t）
            
        返回
        ------
        length : float
            曲线总长度
        """
        if t is None:
            t = self.t
        
        # 数值导数
        dx_dt = np.gradient(x, t)
        dy_dt = np.gradient(y, t)
        
        # 弧长微分 ds = √((dx/dt)² + (dy/dt)²) * dt
        ds_dt = np.sqrt(dx_dt**2 + dy_dt**2)
        
        # 积分得到总长度
        length = _trapz(ds_dt, t)
        return length
    
    def calculate_area(self, x: np.ndarray, y: np.ndarray,
                       t: np.ndarray = None) -> float:
        """
        计算曲线包围的面积（Green 公式）
        
        A = 0.5 · |∫ (x·dy - y·dx)|
        
        参数同上
        
        返回
        ------
        area : float
            曲线包围的面积
        """
        if t is None:
            t = self.t
        
        dx_dt = np.gradient(x, t)
        dy_dt = np.gradient(y, t)
        
        integrand = x * dy_dt - y * dx_dt
        area = 0.5 * np.abs(_trapz(integrand, t))
        return area
    
    def compute_all_metrics(self) -> List[Dict]:
        """
        计算所有蛋形的度量
        
        返回
        ------
        list of dict : [{
            'i': 序号,
            'k': k 参数,
            'b': b 参数,
            'length': 周长 L,
            'area': 面积 A,
            'r_length': 基于周长的等价圆半径 r_L = L/(2π),
            'r_area': 基于面积的等价圆半径 r_A = √(A/π),
            'aspect_ratio': 宽高比,
        }, ...]
        """
        results = []
        
        for i in range(1, self.num_egg + 1):
            egg = self._generate_egg(i)
            x, y = egg['x'], egg['y']
            
            # 周长
            length = self.calculate_length(x, y)
            
            # 面积
            area = self.calculate_area(x, y)
            
            # 等价圆半径
            r_length = length / (2 * np.pi)
            r_area = np.sqrt(area / np.pi)
            
            # 宽高比
            max_width = 2 * np.max(np.abs(x))
            height = np.max(y) - np.min(y)
            aspect_ratio = max_width / height if height > 0 else np.inf
            
            results.append({
                'i': i,
                'k': egg['k'],
                'b': egg['b'],
                'length': length,
                'area': area,
                'r_length': r_length,
                'r_area': r_area,
                'aspect_ratio': aspect_ratio,
                'label': egg['label'],
            })
        
        return results
    
    # =====================================================================
    # 拟合分析
    # =====================================================================
    
    def fit_all_models(self, metrics: List[Dict], 
                         target: str = 'r_length') -> Dict:
        """
        用 6 种模型拟合指定目标量
        
        参数
        ------
        metrics : list of dict
            compute_all_metrics() 的返回值
        target : str
            要拟合的目标量（'r_length', 'r_area', 'length', 'area'）
            
        返回
        ------
        dict : {
            'best': {'name':, 'params':, 'error':, 'pred':},
            'all': [同上 structure for each model],
        }
        """
        n = np.array([m['i'] for m in metrics], dtype=float)
        y = np.array([m[target] for m in metrics], dtype=float)
        
        results = []
        
        for name, (func, n_params) in self.MODELS.items():
            try:
                # 初始猜测
                if n_params == 1:
                    p0 = [y[0]]
                else:
                    p0 = [y[0], 0.1]
                
                popt, _ = curve_fit(func, n, y, p0=p0, maxfev=10000)
                pred = func(n, *popt)
                error = np.sqrt(np.mean((y - pred)**2))
                
                results.append({
                    'name': name,
                    'params': popt,
                    'error': error,
                    'pred': pred,
                })
            except Exception as e:
                print(f"    拟合失败 {name}: {e}")
                pass
        
        if not results:
            return {'best': None, 'all': []}
        
        best = min(results, key=lambda x: x['error'])
        return {'best': best, 'all': results}
    
    # =====================================================================
    # 可视化
    # =====================================================================
    
    def plot_metrics_trend(self, metrics: List[Dict] = None,
                              save_path: Optional[str] = None):
        """
        绘制几何特性随蛋形序号的变化趋势（6 子图）
        
        子图内容：
        1. 周长 L(n) vs n
        2. 基于周长的等价圆半径 r_L(n) vs n
        3. 基于面积的等价圆半径 r_A(n) vs n
        4. 面积 A(n) vs n
        5. 宽高比 vs n
        6. 不同拟合模型的误差比较
        """
        if metrics is None:
            metrics = self.compute_all_metrics()
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        n_vals = np.array([m['i'] for m in metrics])
        
        # 子图1：周长趋势
        lengths = np.array([m['length'] for m in metrics])
        axes[0].plot(n_vals, lengths, 'go-', linewidth=2, markersize=4)
        axes[0].set_xlabel('n (蛋形序号)')
        axes[0].set_ylabel('周长 L(n)')
        axes[0].set_title('周长 vs n')
        axes[0].grid(True, alpha=0.3)
        # 拟合 2π/√n 趋势
        ref_line = 2 * np.pi / np.sqrt(n_vals) * lengths[0] / (2 * np.pi)
        axes[0].plot(n_vals, ref_line, 'r--', label='~2π/√n 趋势')
        axes[0].legend()
        
        # 子图2：基于周长的等价圆半径
        r_lengths = np.array([m['r_length'] for m in metrics])
        axes[1].plot(n_vals, r_lengths, 'bo-', linewidth=2, markersize=4)
        axes[1].set_xlabel('n (蛋形序号)')
        axes[1].set_ylabel('r_L(n) = L(n)/(2π)')
        axes[1].set_title('基于周长的等价圆半径 vs n')
        axes[1].grid(True, alpha=0.3)
        # 拟合 1/√n 趋势
        ref_r = 1.0 / np.sqrt(n_vals) * r_lengths[0]
        axes[1].plot(n_vals, ref_r, 'r--', label='~1/√n 趋势')
        axes[1].legend()
        
        # 子图3：基于面积的等价圆半径
        r_areas = np.array([m['r_area'] for m in metrics])
        axes[2].plot(n_vals, r_areas, 'mo-', linewidth=2, markersize=4)
        axes[2].set_xlabel('n (蛋形序号)')
        axes[2].set_ylabel('r_A(n) = √(A(n)/π)')
        axes[2].set_title('基于面积的等价圆半径 vs n')
        axes[2].grid(True, alpha=0.3)
        
        # 子图4：面积趋势
        areas = np.array([m['area'] for m in metrics])
        axes[3].plot(n_vals, areas, 'co-', linewidth=2, markersize=4)
        axes[3].set_xlabel('n (蛋形序号)')
        axes[3].set_ylabel('面积 A(n)')
        axes[3].set_title('面积 vs n')
        axes[3].grid(True, alpha=0.3)
        # 拟合 1/n 趋势
        ref_a = 1.0 / n_vals * areas[0]
        axes[3].plot(n_vals, ref_a, 'r--', label='~1/n 趋势')
        axes[3].legend()
        
        # 子图5：宽高比
        aspect_ratios = np.array([m['aspect_ratio'] for m in metrics])
        axes[4].plot(n_vals, aspect_ratios, 'yo-', linewidth=2, markersize=4)
        axes[4].set_xlabel('n (蛋形序号)')
        axes[4].set_ylabel('宽高比')
        axes[4].set_title('宽高比 vs n')
        axes[4].grid(True, alpha=0.3)
        
        # 子图6：不同拟合模型的误差比较
        fit_result = self.fit_all_models(metrics, target='r_length')
        if fit_result['all']:
            model_names = [r['name'].split(' ')[0] for r in fit_result['all']]
            errors = [r['error'] for r in fit_result['all']]
            
            bars = axes[5].bar(range(len(model_names)), errors,
                                color=plt.cm.Set3(np.linspace(0, 1, len(model_names))))
            axes[5].set_xticks(range(len(model_names)))
            axes[5].set_xticklabels(model_names, rotation=45, ha='right')
            axes[5].set_ylabel('RMSE')
            axes[5].set_title('不同拟合模型的误差比较 (target: r_L)')
            axes[5].grid(True, alpha=0.3, axis='y')
            
            # 标注最佳模型
            best_idx = np.argmin(errors)
            axes[5].text(best_idx, errors[best_idx], 
                          f'最佳\n{errors[best_idx]:.2e}',
                          ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('蛋壳度量分析 — 八度蛋形族缩放规律', fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()
    
    def plot_first_10_curves(self, save_path: Optional[str] = None):
        """
        绘制前 10 个蛋形曲线的形状
        
        用于直观检查蛋形族的渐变趋势。
        """
        plt.figure(figsize=(12, 8))
        
        colors = plt.cm.viridis(np.linspace(0, 1, 10))
        
        for idx in range(10):
            i = idx + 1
            egg = self._generate_egg(i)
            x, y = egg['x'], egg['y']
            
            plt.plot(x, y, color=colors[idx], alpha=0.8, linewidth=1.5,
                     label=f"n={i}, k={egg['k']:.2f}")
        
        plt.axhline(0, color='black', linewidth=0.5)
        plt.axvline(0, color='black', linewidth=0.5)
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('前 10 个蛋形曲线的形状')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.axis('equal')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()


def demo():
    """演示蛋壳度量分析"""
    print("=" * 60)
    print("蛋壳度量分析器")
    print("=" * 60)
    
    analyzer = EggShellMetrics(num_egg=15, num_points=2000)
    
    # 1. 计算所有度量
    print("\n1. 计算蛋形族度量...")
    metrics = analyzer.compute_all_metrics()
    print(f"   ✅ 已计算 {len(metrics)} 个蛋形")
    print(f"\n   {'n':>3} | {'k':>8} | {'周长 L':>12} | {'r_L':>10} | {'r_A':>10} | {'宽高比':>8}")
    print("   --- | -------- | ------------ | ---------- | ---------- | --------")
    for m in metrics[:5]:
        print(f"   {m['i']:>3} | {m['k']:>8.3f} | {m['length']:>12.6f} | {m['r_length']:>10.6f} | {m['r_area']:>10.6f} | {m['aspect_ratio']:>8.6f}")
    print(f"   ...")
    
    # 2. 拟合分析
    print("\n2. 拟合分析（目标：基于周长的等价圆半径 r_L）...")
    fit_result = analyzer.fit_all_models(metrics, target='r_length')
    
    print(f"\n   {'模型':>30} | {'RMSE':>12} | {'参数'}")
    print("   " + "-" * 30 + " | " + "-" * 12 + " | " + "-")
    for r in fit_result['all']:
        param_str = ', '.join([f'{p:.6f}' for p in r['params']])
        marker = ' ★' if r == fit_result['best'] else ''
        print(f"   {r['name']:>30} | {r['error']:>12.6e} | {param_str} {marker}")
    
    best = fit_result['best']
    best_name = best['name']
    best_params = ', '.join([f'{p:.6f}' for p in best['params']])
    best_err = best['error']
    print(f"\n   🏆 最佳拟合: {best_name}")
    print(f"   参数: {best_params}")
    print(f"   RMSE: {best_err:.6e}")
    
    # 3. 生成可视化图片
    print("\n3. 生成可视化图片...")
    analyzer.plot_metrics_trend(metrics, save_path='egg_shell_metrics_trend.png')
    print(f"   ✅ 度量趋势图已保存: egg_shell_metrics_trend.png")
    
    analyzer.plot_first_10_curves(save_path='egg_shell_first_10.png')
    print(f"   ✅ 前10曲线图已保存: egg_shell_first_10.png")
    
    # 4. 验证 Schauberger 预测
    print("\n4. 验证 Schauberger 预测...")
    r_lengths = np.array([m['r_length'] for m in metrics])
    n_vals = np.array([m['i'] for m in metrics])
    
    # 幂律拟合验证
    log_n = np.log(n_vals)
    log_r = np.log(r_lengths)
    slope = np.polyfit(log_n, log_r, 1)[0]
    
    print(f"   log-log 斜率 β = {slope:.6f} (r ∝ n^β)")
    print(f"   Schauberger 预测: β = -0.5 (r ∝ 1/√n)")
    print(f"   偏差: |β - (-0.5)| = {abs(slope + 0.5):.6f}")
    
    if abs(slope + 0.5) < 0.05:
        print(f"   ✅ 数值验证通过！缩放规律与预测一致。")
    else:
        print(f"   ⚠️ 数值偏差较大，可能需要检查实现。")
    
    print("\n✅ 蛋壳度量分析完成")


if __name__ == '__main__':
    demo()
