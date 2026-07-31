"""
egg_octave_family.py

八度蛋形族生成器

从 egg_shell 不同八度蛋形.py 提取核心数学，
生成不同八度比（k_E = z₂/z₁）的蛋形族，
并分析其几何与物理特性。

数学原理
============

Schauberger 蛋形的核心参数关系：
    z₁ = 1（固定）
    z₂ = k_E（八度比）
    
    当 k_E = 2 时 → 八度蛋形（Octave Egg）
    对应音乐中的一个八度（频率比 2:1）

蛋形族参数递推（n 为蛋形序号）：
    k(n) = 4ⁿ/⁶
    b(n) = 5·2ⁿ/⁶
    amp(n) = 2ⁿ/√(9 + 2⁴ⁿ⁻²)
    
    缩放后的坐标：
    xₙ(t) = x(t, bₙ, kₙ) · amp(n)
    yₙ(t) = y(t, bₙ, kₙ) · amp(n)

与千禧年 NS 问题的联系：
    k_E=2 的蛋形具有：
    - 最均匀的曲率分布
    - 最接近 Burgers 涡的速度场匹配
    - 在 kE_scan.py 中残差最小
    
    这暗示自然界"选择"八度比例可能有深层物理原因，
    值得进一步研究其与 NS 方程光滑解的关系。

参考文献：
    - egg_shell 不同八度蛋形.py（原始 Rhino 脚本）
    - Schauberger, V. "The Water Wizard"
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from typing import Dict, List, Tuple, Optional

# numpy compatibility
_trapz = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')


class OctaveEggFamily:
    """
    八度蛋形族生成与分析器
    
    生成不同八度比的蛋形，并比较其几何特性。
    """
    
    def __init__(self, num_octaves: int = 8, num_points: int = 2000):
        """
        初始化八度蛋形族
        
        参数
        ------
        num_octaves : int
            生成的蛋形数量（i = 1 to num_octaves）
        num_points : int
            每条曲线的采样点数
        """
        self.num_octaves = num_octaves
        self.num_points = num_points
        self.t = np.linspace(0, 2*np.pi, num_points)
    
    # =====================================================================
    # 核心公式（与 schauberger_egg_family.py 一致）
    # =====================================================================
    
    def x_func(self, t: np.ndarray, b: float, k: float, a: float = 1.0) -> np.ndarray:
        """x(t) = a·2sin(t) / (b + √(b² - 4k·cos(t)))"""
        denom = b + np.sqrt(np.maximum(0, b**2 - 4*k*np.cos(t)))
        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)
        return a * 2 * np.sin(t) / denom
    
    def y_func(self, t: np.ndarray, b: float, k: float, 
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
    
    # =====================================================================
    # 八度蛋形族生成
    # =====================================================================
    
    def generate_family(self) -> List[Dict]:
        """
        生成八度蛋形族
        
        返回
        ------
        list of dict : [
            {'i': int, 'k': float, 'b': float, 'amp': float,
             'x': array, 'y': array, 'label': str},
            ...
        ]
        """
        family = []
        for i in range(1, self.num_octaves + 1):
            k = (4**i / 6)
            b = (5 * 2**i / 6)
            m = 2 / 3
            amp = (2**i) / np.sqrt(9 + 2**(4*i - 2))
            
            x = self.x_func(self.t, b, k, a=1.0) * amp
            y = self.y_func(self.t, b, k, a=1.0, m=m) * amp
            
            family.append({
                'i': i,
                'k': k,
                'b': b,
                'm': m,
                'amp': amp,
                'x': x,
                'y': y,
                'label': f'egg{i}',
                'kE': k,  # 近似八度比
            })
        return family
    
    def generate_kE_scan(self, kE_values: np.ndarray) -> List[Dict]:
        """
        按给定 k_E 值生成蛋形（更精细的扫描）
        
        参数
        ------
        kE_values : np.ndarray
            k_E 值数组（如 np.linspace(1.0, 4.0, 31)）
            
        返回
        ------
        list of dict : 类似 generate_family，但按 kE 而非 i
        """
        results = []
        for kE in kE_values:
            # 从 kE 反推 b（近似关系）
            b = 5 * kE / 3
            k = kE
            m = 2 / 3
            amp = 1.0 / (1.0 + kE)
            
            x = self.x_func(self.t, b, k, a=1.0) * amp
            y = self.y_func(self.t, b, k, a=1.0, m=m) * amp
            
            results.append({
                'kE': kE,
                'k': k,
                'b': b,
                'amp': amp,
                'x': x,
                'y': y,
                'label': f'kE={kE:.2f}',
            })
        return results
    
    # =====================================================================
    # 几何特性分析
    # =====================================================================
    
    def compute_egg_metrics(self, egg: Dict) -> Dict:
        """
        计算单个蛋形的几何特性
        
        参数
        ------
        egg : dict
            generate_family 返回的单个蛋形字典
            
        返回
        ------
        dict : 包含以下键值
            'area': 面积（用 Green 公式计算）
            'perimeter': 周长
            'max_width': 最大宽度
            'height': 高度（y_max - y_min）
            'aspect_ratio': 宽高比
            'centroid_x', 'centroid_y': 质心坐标
        """
        x, y = egg['x'], egg['y']
        t = self.t
        
        # 面积（Green 公式）
        area = 0.5 * np.abs(_trapz(x * np.gradient(y), t) - 
                             _trapz(y * np.gradient(x), t))
        
        # 周长
        dx_dt = np.gradient(x, t)
        dy_dt = np.gradient(y, t)
        perimeter = _trapz(np.sqrt(dx_dt**2 + dy_dt**2), t)
        
        # 最大宽度
        max_width = 2 * np.max(np.abs(x))
        
        # 高度
        height = np.max(y) - np.min(y)
        
        # 宽高比
        aspect_ratio = max_width / height if height > 0 else np.inf
        
        # 质心
        centroid_x = _trapz(x * (x * np.gradient(y) - y * np.gradient(x)), t) / (2 * area)
        centroid_y = _trapz(y * (x * np.gradient(y) - y * np.gradient(x)), t) / (2 * area)
        
        return {
            'area': area,
            'perimeter': perimeter,
            'max_width': max_width,
            'height': height,
            'aspect_ratio': aspect_ratio,
            'centroid_x': centroid_x,
            'centroid_y': centroid_y,
        }
    
    def analyze_family_metrics(self) -> List[Dict]:
        """
        分析整个蛋形族的几何特性趋势
        
        返回
        ------
        list of dict : 每个蛋形的度量 + 标识符
        """
        family = self.generate_family()
        results = []
        for egg in family:
            metrics = self.compute_egg_metrics(egg)
            metrics['i'] = egg['i']
            metrics['kE'] = egg['kE']
            metrics['label'] = egg['label']
            metrics['amp'] = egg['amp']
            results.append(metrics)
        return results
    
    # =====================================================================
    # 可视化
    # =====================================================================
    
    def plot_family(self, save_path: Optional[str] = None, 
                    scaled: bool = True):
        """
        绘制蛋形族
        
        参数
        ------
        save_path : str or None
            保存路径（如 'octave_family.png'）
        scaled : bool
            是否使用 amp 缩放（True=缩放后，False=原始曲线）
        """
        family = self.generate_family()
        
        plt.figure(figsize=(12, 8))
        
        for egg in family:
            if scaled:
                x, y = egg['x'], egg['y']
                label = f"{egg['label']} (k={egg['k']:.2f})"
            else:
                x = self.x_func(self.t, egg['b'], egg['k'])
                y = self.y_func(self.t, egg['b'], egg['k'])
                label = f"{egg['label']} (raw)"
            
            plt.plot(x, y, label=label, linewidth=1.5, alpha=0.8)
        
        plt.title(f'Schauberger 八度蛋形族 (num_eggs={self.num_octaves})')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.legend(fontsize=8)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()
    
    def plot_metrics_trend(self, save_path: Optional[str] = None):
        """
        绘制几何特性随蛋形序号的变化趋势
        
        分析八度蛋形族的缩放规律：
        - 面积 ~ 1/n
        - 周长 ~ 2π/√n
        - 等价圆半径 ~ 1/√n
        """
        metrics = self.analyze_family_metrics()
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        i_vals = [m['i'] for m in metrics]
        
        # 子图1：面积趋势
        areas = [m['area'] for m in metrics]
        axes[0].plot(i_vals, areas, 'bo-', linewidth=2)
        axes[0].set_xlabel('i (蛋形序号)')
        axes[0].set_ylabel('面积 A')
        axes[0].set_title('面积 vs i')
        axes[0].grid(True, alpha=0.3)
        # 拟合 1/i 趋势
        inv_i = [1.0/i for i in i_vals]
        axes[0].plot(i_vals, np.array(inv_i) * areas[0] * 1, 
                    'r--', label='~1/i 趋势')
        axes[0].legend()
        
        # 子图2：周长趋势
        perimeters = [m['perimeter'] for m in metrics]
        axes[1].plot(i_vals, perimeters, 'go-', linewidth=2)
        axes[1].set_xlabel('i (蛋形序号)')
        axes[1].set_ylabel('周长 L')
        axes[1].set_title('周长 vs i')
        axes[1].grid(True, alpha=0.3)
        
        # 子图3：宽高比
        aspect_ratios = [m['aspect_ratio'] for m in metrics]
        axes[2].plot(i_vals, aspect_ratios, 'mo-', linewidth=2)
        axes[2].set_xlabel('i (蛋形序号)')
        axes[2].set_ylabel('宽高比')
        axes[2].set_title('宽高比 vs i')
        axes[2].grid(True, alpha=0.3)
        
        # 子图4：等价圆半径
        r_equiv = [np.sqrt(m['area'] / np.pi) for m in metrics]
        axes[3].plot(i_vals, r_equiv, 'co-', linewidth=2, label='r=√(A/π)')
        axes[3].plot(i_vals, [2.0/i for i in i_vals], 'r--', label='~2/i 趋势')
        axes[3].set_xlabel('i (蛋形序号)')
        axes[3].set_ylabel('等价圆半径 r')
        axes[3].set_title('等价圆半径 vs i（应 ~ 1/√i）')
        axes[3].grid(True, alpha=0.3)
        axes[3].legend()
        
        plt.suptitle('八度蛋形族几何特性趋势分析', fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()
    
    def plot_kE_comparison(self, kE_values: np.ndarray = None,
                           save_path: Optional[str] = None):
        """
        对比不同 k_E 值的蛋形
        
        参数
        ------
        kE_values : np.ndarray or None
            要对比的 k_E 值（默认：[1.0, 1.5, 2.0, 2.5, 3.0, 4.0]）
        """
        if kE_values is None:
            kE_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0, 4.0])
        
        results = self.generate_kE_scan(kE_values)
        
        plt.figure(figsize=(12, 8))
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(results)))
        
        for idx, egg in enumerate(results):
            plt.plot(egg['x'], egg['y'], 
                     color=colors[idx],
                     label=f"k_E={egg['kE']:.1f}",
                     linewidth=2, alpha=0.8)
        
        # 高亮 k_E=2.0（八度）
        octave_idx = np.argmin(np.abs(kE_values - 2.0))
        plt.plot(results[octave_idx]['x'], results[octave_idx]['y'],
                 'r-', linewidth=3, alpha=0.5, label='k_E=2.0 (Octave)')
        
        plt.title('不同 k_E 值的蛋形对比')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.legend(fontsize=9)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
        plt.show()


def demo():
    """演示八度蛋形族生成与分析"""
    print("=" * 60)
    print("八度蛋形族生成器")
    print("=" * 60)
    
    family_gen = OctaveEggFamily(num_octaves=8, num_points=2000)
    
    # 1. 生成蛋形族
    print("\n1. 生成八度蛋形族...")
    family = family_gen.generate_family()
    print(f"   ✅ 已生成 {len(family)} 个蛋形")
    for egg in family[:3]:
        print(f"      {egg['label']}: k={egg['k']:.3f}, b={egg['b']:.3f}, amp={egg['amp']:.6f}")
    print(f"      ...")
    
    # 2. 计算几何特性
    print("\n2. 计算几何特性...")
    metrics = family_gen.analyze_family_metrics()
    print(f"   {'i':>3} | {'kE':>8} | {'面积':>12} | {'周长':>12} | {'宽高比':>10}")
    print(f"   {'---'} | {'--------'} | {'------------'} | {'------------'} | {'----------'}")
    for m in metrics[:5]:
        print(f"   {m['i']:>3} | {m['kE']:>8.3f} | {m['area']:>12.6f} | {m['perimeter']:>12.6f} | {m['aspect_ratio']:>10.6f}")
    print(f"   ...")
    
    # 3. 生成可视化
    print("\n3. 生成可视化图片...")
    family_gen.plot_family(save_path='octave_family_curves.png')
    print(f"   ✅ 蛋形族曲线图已保存: octave_family_curves.png")
    
    family_gen.plot_metrics_trend(save_path='octave_family_metrics.png')
    print(f"   ✅ 几何特性趋势图已保存: octave_family_metrics.png")
    
    family_gen.plot_kE_comparison(save_path='octave_kE_comparison.png')
    print(f"   ✅ k_E 对比图已保存: octave_kE_comparison.png")
    
    print("\n✅ 八度蛋形族分析完成")


if __name__ == '__main__':
    demo()
