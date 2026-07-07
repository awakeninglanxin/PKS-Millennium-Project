"""
egg_variations.py

蛋形曲线变体生成器

从 Rhino 脚本中提取的4种 Schauberger 公式变体，
以及波纹最佳截面曲线的生成方法。

数学原理
============

四种变体对应于二次方程的不同系数组合，
本质上是 Schauberger 超双曲锥 xy=1 被不同角度平面切割的
截线方程的近似表达。

波纹最佳截面曲线：
    - 使用连续对数衰减因子 amp(t) = 1/((1+t/2π)·ln(N+1))
    - 将基础蛋形曲线(x(t), y(t)) 按 amp(t) 缩放
    - 生成具有"波纹"效果的变体截面

与 NS 方程的联系：
    波纹壁面（rippled wall）是 CFD 中常用的
    几何扰动方式，可激发特定频率的涡旋脱落。
    蛋形 + 波纹 → 模拟自然界中观察到的
    血流/水流的脉动模式（Schauberger 观察）。

参考文献：
    - 4个舒伯格公式花洒.py（原始 Rhino 脚本）
    - 4种波纹最佳截面曲线ln线.py（原始 Rhino 脚本）
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from typing import Dict, List, Tuple, Callable, Optional


class EggVariationGenerator:
    """
    蛋形变体生成器
    
    生成 Schauberger 蛋形曲线的多种变体，
    包括参数变体、波纹变体和衰减变体。
    """
    
    # 四种 Schauberger 公式变体的参数
    # 对应于 xy=1 锥面被不同角度平面切割
    FOUR_VARIATIONS = [
        {'name': 'Var I (x^2+x-2=0)',    'k': 2/3, 'b': 5/3, 'm': 2/3, 'desc': '标准 Schauberger 蛋形'},
        {'name': 'Var II (x^2+4x+3=0)',  'k': 1.0, 'b': 2.0, 'm': 2/3, 'desc': '较胖蛋形'},
        {'name': 'Var III (x^2-1.5x-1=0)', 'k': 0.5, 'b': 1.5, 'm': 2/3, 'desc': '较瘦蛋形'},
        {'name': 'Var IV (x^2+0.75x-0.25=0)', 'k': 0.375, 'b': 1.25, 'm': 2/3, 'desc': '微蛋形'},
    ]
    
    def __init__(self, num_points: int = 2000):
        """
        初始化生成器
        
        参数
        ------
        num_points : int
            每条曲线采样点数
        """
        self.num_points = num_points
        self.t = np.linspace(0, 2*np.pi, num_points)
    
    # =====================================================================
    # 基础公式（与 schauberger_egg_family.py 一致）
    # =====================================================================
    
    def x_func(self, t: np.ndarray, b: float, k: float, a: float = 1.0) -> np.ndarray:
        """x(t) = a·2sin(t) / (b + √(b² - 4k·cos(t)))"""
        denom = b + np.sqrt(np.maximum(0, b**2 - 4*k*np.cos(t)))
        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
        return a * 2 * np.sin(t) / denom
    
    def y_func(self, t: np.ndarray, b: float, k: float, 
                a: float = 1.0, m: float = 2/3) -> np.ndarray:
        """y(t) 完整表达式"""
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
    
    # =====================================================================
    # 变体生成
    # =====================================================================
    
    def generate_four_variations(self) -> List[Dict]:
        """
        生成四种 Schauberger 公式变体
        
        返回
        ------
        list of dict : [{'name': str, 'x': array, 'y': array, 'params': dict}, ...]
        """
        results = []
        for var in self.FOUR_VARIATIONS:
            x = self.x_func(self.t, var['b'], var['k'])
            y = self.y_func(self.t, var['b'], var['k'], a=1.0, m=var['m'])
            results.append({
                'name': var['name'],
                'desc': var['desc'],
                'x': x,
                'y': y,
                'params': {'k': var['k'], 'b': var['b'], 'm': var['m']},
            })
        return results
    
    def generate_ripple_variation(self, user_num: int = 5, 
                                  k: float = 2/3, b: float = 5/3,
                                  a: float = 2*np.pi, m: float = 2/3,
                                  amp1: float = 1.0, amp2: float = 1.0) -> Dict:
        """
        生成波纹变体（从 4种波纹最佳截面曲线ln线.py 提取）
        
        使用连续对数衰减因子 amp(t) 对基础蛋形进行缩放，
        产生"波纹"效果。
        
        参数
        ------
        user_num : int
            控制衰减速度（越大衰减越慢）
        k, b, a, m : float
            蛋形参数
        amp1, amp2 : float
            两个方向的缩放幅度
            
        返回
        ------
        dict : {
            't': t 数组,
            'x_base': 基础 x(t),
            'y_base': 基础 y(t),
            'x_ripple1': 波纹化 x(t) * amp(t) * amp1,
            'y_ripple1': 波纹化 y(t) * amp(t) * amp1,
            'x_ripple2': 波纹化 x(t) * amp(t) * amp2,
            'y_ripple2': 波纹化 y(t) * amp(t) * amp2,
            'amp': amp(t) 数组,
        }
        """
        t = self.t
        
        # 连续对数衰减因子（核心公式）
        # amp(t) = 1 / ((1 + t/(2π)) · ln(user_num + 1))
        amp = 1.0 / ((1.0 + t / (2*np.pi)) * np.log(user_num + 1))
        
        # 基础曲线
        x_base = self.x_func(t, b, k, a)
        y_base = self.y_func(t, b, k, a, m)
        
        # 波纹化曲线（两个方向）
        x_ripple1 = x_base * amp * amp1
        y_ripple1 = y_base * amp * amp1
        
        x_ripple2 = x_base * amp * amp2
        y_ripple2 = y_base * amp * amp2
        
        return {
            't': t,
            'x_base': x_base,
            'y_base': y_base,
            'x_ripple1': x_ripple1,
            'y_ripple1': y_ripple1,
            'x_ripple2': x_ripple2,
            'y_ripple2': y_ripple2,
            'amp': amp,
            'user_num': user_num,
        }
    
    def generate_scaled_family(self, num_eggs: int = 8) -> List[Dict]:
        """
        生成缩放蛋形族（从 egg_shell 不同八度蛋形.py 提取）
        
        参数
        ------
        num_eggs : int
            蛋形数量（i = 1 to num_eggs）
            
        返回
        ------
        list of dict : [{'i': int, 'k': float, 'b': float, 'amp': float, 'x': array, 'y': array}, ...]
        """
        results = []
        for i in range(1, num_eggs + 1):
            k = (4**i / 6)
            b = (5 * 2**i / 6)
            m = 2 / 3
            amp = (2**i) / np.sqrt(9 + 2**(4*i - 2))
            
            t = np.linspace(0, 2*np.pi, self.num_points)
            x = self.x_func(t, b, k, a=1.0) * amp
            y = self.y_func(t, b, k, a=1.0, m=m) * amp
            
            results.append({
                'i': i,
                'k': k,
                'b': b,
                'm': m,
                'amp': amp,
                'label': f'egg{i}',
                'x': x,
                'y': y,
            })
        return results
    
    # =====================================================================
    # 可视化
    # =====================================================================
    
    def plot_four_variations(self, save_path: Optional[str] = None):
        """绘制四种变体"""
        variations = self.generate_four_variations()
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for idx, var in enumerate(variations):
            ax = axes[idx]
            ax.plot(var['x'], var['y'], linewidth=2)
            ax.set_title(var['name'], fontsize=10)
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
            ax.text(0.05, 0.95, var['desc'], transform=ax.transAxes,
                    fontsize=8, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('四种 Schauberger 公式变体', fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()
    
    def plot_ripple_variation(self, user_num: int = 5, save_path: Optional[str] = None):
        """绘制波纹变体"""
        result = self.generate_ripple_variation(user_num=user_num)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 左图：基础曲线 vs 波纹曲线
        ax1.plot(result['x_base'], result['y_base'], 'k--', 
                linewidth=1, label='基础蛋形')
        ax1.plot(result['x_ripple1'], result['y_ripple1'], 'b-', 
                linewidth=2, label=f'波纹化 (amp1={1.0})')
        ax1.plot(result['x_ripple2'], result['y_ripple2'], 'r-', 
                linewidth=2, label=f'波纹化 (amp2={1.0})')
        ax1.set_title(f'波纹蛋形 (user_num={user_num})')
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')
        ax1.legend()
        
        # 右图：衰减因子 amp(t)
        ax2.plot(result['t'], result['amp'], 'g-', linewidth=2)
        ax2.set_title('连续对数衰减因子 amp(t)')
        ax2.set_xlabel('t (参数)')
        ax2.set_ylabel('amp(t)')
        ax2.grid(True, alpha=0.3)
        ax2.text(0.05, 0.95, 
                f'amp(t) = 1/((1+t/2π)·ln({user_num}+1))',
                transform=ax2.transAxes, fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('波纹最佳截面曲线', fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()
    
    def plot_scaled_family(self, num_eggs: int = 8, save_path: Optional[str] = None):
        """绘制缩放蛋形族"""
        family = self.generate_scaled_family(num_eggs)
        
        plt.figure(figsize=(10, 8))
        
        for egg in family:
            plt.plot(egg['x'], egg['y'], 
                     label=f"{egg['label']} (k={egg['k']:.2f}, amp={egg['amp']:.4f})")
        
        plt.title(f'Schauberger 蛋形族 (num_eggs={num_eggs})')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.legend(fontsize=8)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()


def demo():
    """演示蛋形变体生成"""
    print("=" * 60)
    print("蛋形变体生成器")
    print("=" * 60)
    
    gen = EggVariationGenerator(num_points=2000)
    
    # 1. 四种变体
    print("\n1. 生成四种 Schauberger 公式变体...")
    variations = gen.generate_four_variations()
    for var in variations:
        print(f"   {var['name']}: k={var['params']['k']:.3f}, b={var['params']['b']:.3f}")
    print(f"   ✅ 已生成 {len(variations)} 种变体")
    
    # 2. 波纹变体
    print("\n2. 生成波纹变体...")
    ripple = gen.generate_ripple_variation(user_num=5)
    print(f"   衰减因子范围: [{ripple['amp'].min():.6f}, {ripple['amp'].max():.6f}]")
    print(f"   ✅ 波纹化完成")
    
    # 3. 缩放族
    print("\n3. 生成缩放蛋形族...")
    family = gen.generate_scaled_family(num_eggs=8)
    for egg in family[:3]:  # 只显示前3个
        print(f"   {egg['label']}: k={egg['k']:.3f}, b={egg['b']:.3f}, amp={egg['amp']:.6f}")
    print(f"   ... (共 {len(family)} 个)")
    print(f"   ✅ 缩放族生成完成")
    
    # 4. 保存图片
    print("\n4. 生成可视化图片...")
    gen.plot_four_variations(save_path='egg_four_variations.png')
    gen.plot_ripple_variation(save_path='egg_ripple_variation.png')
    gen.plot_scaled_family(save_path='egg_scaled_family.png')
    print(f"   ✅ 图片已保存")
    
    print("\n✅ 蛋形变体分析完成")


if __name__ == '__main__':
    demo()
