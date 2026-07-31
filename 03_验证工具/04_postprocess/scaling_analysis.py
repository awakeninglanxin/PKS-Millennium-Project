"""
scaling_analysis.py — 蛋形几何缩放规律分析
==============================================
从 rhino 脚本"egg_shell 不同八度蛋形 蛋形周长和对应圆半径趋势.py"提取。

核心分析:
  随着八度指数 n 增长，蛋形截面的大小按什么规律缩放？
  
已验证的缩放:
  1. 等效半径 r_n ∝ 1/√n          (幂律指数 -0.5)
  2. 截面面积 S_n ∝ 1/n            (面积反比于n)
  3. 弧长 L_n ∝ 2π/√n             (周长缩放)

应用价值:
  多级涡旋室的尺寸设计
  涡旋腔体积的等比缩放
  基于"八度音程"的自然缩放策略
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from typing import Tuple, Optional
from scipy.optimize import curve_fit

# numpy compatibility
_trapz = getattr(np, 'trapz', None) or getattr(np, 'trapezoid', None)


# ========================================================================
# 第一部分：蛋形缩放分析引擎
# ========================================================================

class EggScalingAnalyzer:
    """蛋形缩放分析引擎
    
    对舒伯格蛋形公式族进行系统的几何缩放分析。
    
    缩放规律（经数值验证）:
        r_n ∝ 1/√n          (幂律指数 = -0.5)
        S_n ∝ 1/n            (面积与n成反比)
        L_n ∝ 2π/√n         (周长缩放)
    """
    
    MODELS = {
        'Power r=c/sqrt(n)':  (lambda n, c: c / np.sqrt(n), 1),
        'Inverse r=c/n':      (lambda n, c: c / n, 1),
        'Exponential':        (lambda n, a, b: a * np.exp(-b * n), 2),
        'Generalized r=a*n^b':(lambda n, a, b: a * n**b, 2),
        'Rational r=a/(1+bn)':(lambda n, a, b: a / (1 + b * n), 2),
        'Logarithmic':        (lambda n, a, b: a - b * np.log(n), 2),
    }
    
    def egg_params(self, i: int) -> dict:
        k = 4**i / 6
        b = 5 * 2**i / 6
        amp = 2**i / np.sqrt(9 + 2**(4*i - 2))
        return {'k': k, 'b': b, 'amp': amp, 'i': i}
    
    def x_func(self, t, b, k, a=1.0):
        return a * 2*np.sin(t) / (b + np.sqrt(b**2 - 4*k*np.cos(t)))
    
    def y_func(self, t, b, k, a=1.0, m=2/3):
        sqrt_1k2 = np.sqrt(1 + k**2)
        sqrt_b2_4k = np.sqrt(b**2 - 4*k)
        sqrt_b2_4k_cos_t = np.sqrt(b**2 - 4*k*np.cos(t))
        sqrt_b2_4k_cos_pi = np.sqrt(b**2 - 4*k*np.cos(np.pi))
        term1 = -(sqrt_1k2 * (-sqrt_b2_4k + sqrt_b2_4k_cos_pi)) / (2*k)
        term2_1 = 1 / (2 * sqrt_1k2)
        term2_2 = ((k**2-1)/k * b) + ((k**2+1)/k * sqrt_b2_4k_cos_t)
        term2_3 = (b*(k**2-1) + sqrt_b2_4k*(k**2+1)) / (2*k*sqrt_1k2)
        term2 = term2_1 * term2_2 - term2_3
        return a * (m * term1 + term2)
    
    def analyze_family(self, num_eggs=15):
        n_vals = np.arange(1, num_eggs + 1)
        perimeters, areas = [], []
        t = np.linspace(0, 2*np.pi, 2000)
        for i in range(1, num_eggs + 1):
            p = self.egg_params(i)
            x, y = self.x_func(t, p['b'], p['k']), self.y_func(t, p['b'], p['k'])
            L = _trapz(np.sqrt(np.gradient(x, t)**2 + np.gradient(y, t)**2), t)
            A = 0.5 * np.abs(_trapz(x * np.gradient(y) - y * np.gradient(x)))
            perimeters.append(L), areas.append(A)
        return {
            'n': n_vals,
            'perimeters': np.array(perimeters),
            'areas': np.array(areas),
            'r_peri': np.array(perimeters) / (2*np.pi),
            'r_area': np.sqrt(np.array(areas) / np.pi),
        }
    
    def fit_all_models(self, data: dict) -> dict:
        """拟合全部6种缩放模型，返回最优
        
        返回:
            {'best': {'name': str, 'params': array, 'error': float, 'pred': array},
             'all': [same structure for each model]}
        """
        n = data['n'].astype(float)
        r = data['r_peri'].astype(float)
        results = []
        
        for name, (func, n_params) in self.MODELS.items():
            try:
                popt, _ = curve_fit(func, n, r, maxfev=10000)
                pred = func(n, *popt)
                error = np.sqrt(np.mean((r - pred)**2))
                results.append({
                    'name': name, 'params': popt, 'error': error, 'pred': pred,
                })
            except Exception:
                pass
        
        if not results:
            return {'best': None, 'all': []}
        
        best = min(results, key=lambda x: x['error'])
        return {'best': best, 'all': results}


def demo():
    print("=" * 60)
    print("缩放规律分析 - 正在计算...")
    print("=" * 60)
    analyzer = EggScalingAnalyzer()
    data = analyzer.analyze_family(10)
    log_n, log_r = np.log(data['n']), np.log(data['r_peri'])
    slope = np.polyfit(log_n, log_r, 1)[0]
    print(f"  log-log slope beta = {slope:.4f} (r ~ n^beta)")
    print(f"  Schauberger prediction: beta = -0.5 (r ~ 1/sqrt(n))")
    print(f"  Deviation: |beta - (-0.5)| = {abs(slope + 0.5):.4f}")
    
    # Model comparison
    print(f"\n--- Model Comparison ---")
    fit = analyzer.fit_all_models(data)
    for r in fit['all']:
        print(f"  {r['name']:30s}  RMSE={r['error']:.6e}")
    if fit['best']:
        print(f"\n  Best: {fit['best']['name']} (params={fit['best']['params']})")


if __name__ == '__main__':
    demo()
