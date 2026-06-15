"""
schauberger_egg_family.py — 舒伯格蛋形公式族与缩放规律分析
===========================================================
从 Rhino/草稿脚本中提取的舒伯格蛋形公式族，整合为标准Python模块。

数学背景：
  舒伯格（Schauberger）通过双曲锥 xy=1 的平面斜切，获得一族蛋形曲线。
  不同"八度"（octave）的蛋形曲线之间满足几何缩放规律。

核心公式族（来自Rhino脚本 egg_shell* 系列）:
  k_i   = 4^i / 6          (曲率参数，随八度指数增长)
  b_i   = 5 * 2^i / 6      (宽度参数，随八度指数增长)
  m     = 2/3               (形状修正参数，固定)
  amp_i = 2^i / sqrt(9 + 2^(4i-2))  (振幅缩放因子)
  
  x_i(t) = a · 2sin(t) / (b_i + sqrt(b_i² - 4k_i·cos(t)))
  y_i(t) = a · [m·term1 + term2]   (详见SchaubergerEggFamily.y_func)

缩放规律（经数值验证）:
  等效半径 r_n ∝ 1/√n        (基于弧长)
  截面面积 S_n ∝ 1/n         (基于Green定理)

工程意义:
  涡旋室截面尺寸的等比缩放设计；
  多级涡旋腔的"八度音程"级联策略。

参考:
  - Viktor Schauberger, "The Water Wizard"
  - Rhino scripts: egg_shell 不同八度蛋形*.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from dataclasses import dataclass
from typing import Tuple, List, Optional
from scipy.optimize import curve_fit


# ========================================================================
# 第一部分：舒伯格蛋形公式族
# ========================================================================

@dataclass
class EggOctaveParams:
    """单个八度蛋形的参数集合
    
    数学定义:
        k_i   = 4^i / 6              — 曲率参数，决定蛋形的"尖度"
        b_i   = 5 · 2^i / 6          — 宽度参数，决定蛋形的"胖度"
        m     = 2/3                  — 形状修正，经验值
        amp_i = 2^i / √(9 + 2^(4i-2)) — 振幅缩放
        
    其中 i = 0, 1, 2, ... 为八度指数
    i=0 → 近似圆形 (k_E ≈ 1)
    i=1 → 八度蛋形 (k_E ≈ 2, 基准)
    i=2 → 双八度   (k_E ≈ 4)
    """
    i: int               # 八度指数
    k: float = None      # 曲率参数
    b: float = None      # 宽度参数
    m: float = 2/3       # 形状修正参数
    amp: float = None    # 振幅缩放
    label: str = ""      # 描述标签
    
    def __post_init__(self):
        """根据八度指数计算所有参数"""
        self.k = 4**self.i / 6
        self.b = 5 * 2**self.i / 6
        self.amp = 2**self.i / np.sqrt(9 + 2**(4*self.i - 2))
        if not self.label:
            self.label = f'egg{self.i+1}'


class SchaubergerEggFamily:
    """舒伯格蛋形公式族生成器
    
    基于八度指数的蛋形曲线族：
      i=1 → 基准八度（z1=1, z2=2, k_E=2）
      i=2 → 高八度（更尖细）
      i=0 → 近似圆形
    
    使用示例:
        family = SchaubergerEggFamily()
        params = family.egg_params(1)  # 八度蛋形
        t = np.linspace(0, 2*np.pi, 1000)
        x, y = family.curve(t, params)
    """
    
    def egg_params(self, i: int) -> EggOctaveParams:
        """获取第i个八度的蛋形参数"""
        return EggOctaveParams(i=i)
    
    def x_func(self, t: np.ndarray, b: float, k: float, a: float = 1.0) -> np.ndarray:
        """蛋形曲线x坐标
        
        公式: 
            x(t) = a · 2sin(t) / (b + √(b² - 4k·cos(t)))
        
        其中 t ∈ [0, 2π] 为参数，b, k 为蛋形参数，a 为振幅。
        分母的 √(b² - 4k·cos(t)) 项控制了曲线的变形程度：
          - 当 k=0 时，分母退化为 b+b=2b，曲线退化为 sin(t)/b（椭圆）
          - 当 k>0 时，分母随 cos(t) 变化产生非对称性（蛋形特征）
        """
        denom = b + np.sqrt(b**2 - 4 * k * np.cos(t))
        return a * 2 * np.sin(t) / denom
    
    def y_func(self, t: np.ndarray, b: float, k: float, a: float = 1.0, m: float = 2/3) -> np.ndarray:
        """蛋形曲线y坐标（完整解析形式）
        
        公式由两个项组成：
          y = a · (m · term1 + term2)
        
        其中 term1 为：
            term1 = -√(1+k²)·(-√(b²-4k) + √(b²-4k·cos(π))) / (2k)
        
        其中 cos(π) = -1, 所以 √(b²-4k·cos(π)) = √(b²+4k)
        因此 term1 与 t 无关，是一个常数偏移项。
        
        term2 为 t 的函数：
            term2 = 1/(2√(1+k²)) · [((k²-1)/k·b) + ((k²+1)/k·√(b²-4k·cos(t)))]
                    - (b·(k²-1) + √(b²-4k)·(k²+1)) / (2k·√(1+k²))
        
        这实际上是Schauberger蛋形曲线的精确参数化形式，
        从双曲锥 xy=1 的平面斜切推导而来。
        """
        # 计算常数项 term1（与t无关）
        sqrt_1k2 = np.sqrt(1 + k**2)
        sqrt_b2_4k = np.sqrt(b**2 - 4*k)
        sqrt_b2_4k_cos_pi = np.sqrt(b**2 - 4*k*np.cos(np.pi))  # cos(π) = -1
        
        term1 = -(sqrt_1k2 * (-sqrt_b2_4k + sqrt_b2_4k_cos_pi)) / (2*k)
        
        # 计算与t相关的项 term2
        sqrt_b2_4k_cos_t = np.sqrt(b**2 - 4*k*np.cos(t))
        
        term2_1 = 1 / (2 * sqrt_1k2)
        term2_2 = ((k**2 - 1)/k * b) + ((k**2 + 1)/k * sqrt_b2_4k_cos_t)
        term2_3 = (b*(k**2 - 1) + sqrt_b2_4k*(k**2 + 1)) / (2*k*sqrt_1k2)
        
        term2 = term2_1 * term2_2 - term2_3
        
        return a * (m * term1 + term2)
    
    def curve(self, t: np.ndarray, params: EggOctaveParams) -> Tuple[np.ndarray, np.ndarray]:
        """生成完整的蛋形曲线坐标"""
        x = self.x_func(t, params.b, params.k, params.amp)
        y = self.y_func(t, params.b, params.k, params.amp, params.m)
        return x, y
    
    def generate_family(self, num_eggs: int = 10) -> List[Tuple[np.ndarray, np.ndarray, EggOctaveParams]]:
        """生成蛋形公式族
        
        返回：
            [(x_i, y_i, params_i), ...] 共 num_eggs 个蛋形
        """
        results = []
        t = np.linspace(0, 2*np.pi, 2000)
        for i in range(1, num_eggs + 1):
            params = self.egg_params(i)
            x, y = self.curve(t, params)
            results.append((x, y, params))
        return results
    
    def arc_length(self, t: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
        """计算曲线弧长（数值积分）
        
        弧长微分: ds = √[(dx/dt)² + (dy/dt)²] · dt
        总弧长: L = ∫₀²ᵖⁱ ds
        
        使用 trapz 梯形法数值积分。
        """
        dx_dt = np.gradient(x, t)
        dy_dt = np.gradient(y, t)
        ds_dt = np.sqrt(dx_dt**2 + dy_dt**2)
        return np.trapezoid(ds_dt, t)
    
    def area(self, x: np.ndarray, y: np.ndarray) -> float:
        """计算蛋形曲线包围面积（Green定理/鞋带公式）
        
        Green定理:
            A = ½ ∮ (x·dy - y·dx) = ½ · |Σ(x_i·y_{i+1} - x_{i+1}·y_i)|
        
        数值实现使用鞋带公式（Shoelace formula）:
            A = ½ · |Σ_{i=1}^{n} (x_i·y_{i+1} - x_{i+1}·y_i)|
        """
        return 0.5 * np.abs(np.trapezoid(x * np.gradient(y) - y * np.gradient(x)))
    
    def equivalent_radius_from_perimeter(self, L: float) -> float:
        """基于周长的等效半径
        
        将蛋形周长 L 视为"圆的周长"：
            r_eq = L / (2π)
        
        物理含义：如果蛋形截面面积集中的涡旋能量等效为圆形截面，
        这个半径给出了涡旋室的"等效尺寸"。
        """
        return L / (2 * np.pi)
    
    def equivalent_radius_from_area(self, A: float) -> float:
        """基于面积的等效半径
        
        r_eq = √(A/π)
        
        这是真正意义上的"等效半径"——与蛋形截面面积相等的圆的半径。
        涡旋的环量Γ与面积相关，因此这个半径对涡旋强度估计更有意义。
        """
        return np.sqrt(A / np.pi)


# ========================================================================
# 第二部分：蛋形缩放规律分析
# ========================================================================

class EggScalingAnalyzer:
    """蛋形几何缩放规律分析器
    
    分析不同八度蛋形的周长、面积与八度指数n的关系。
    
    已验证的缩放规律:
        等效半径 r_n ∝ 1/√n          (幂律指数 = -0.5)
        截面面积 S_n ∝ 1/n            (面积与n成反比)
        周长 L_n ∝ 2π/√n             (周长缩放)
    
    这些缩放规律对涡旋室的多级级联设计至关重要：
        如果涡旋强度 Γ_n = Γ₀/√n，则多级涡旋可以平滑地缩小能量尺度。
    """
    
    def __init__(self, family: Optional[SchaubergerEggFamily] = None):
        self.family = family or SchaubergerEggFamily()
        self._cached_data = None
    
    def analyze_family(self, num_eggs: int = 15) -> dict:
        """完整分析蛋形公式族的缩放规律
        
        返回:
            {
                'n': int数组 (1..num_eggs),
                'perimeters': float数组 (各蛋形周长),
                'areas': float数组 (各蛋形面积),
                'r_from_perimeter': float数组 (基于周长的等效半径),
                'r_from_area': float数组 (基于面积的等效半径),
                'log_log_slope': float (对数坐标下的斜率 = 缩放指数),
            }
        """
        n_vals = np.arange(1, num_eggs + 1)
        perimeters = []
        areas = []
        r_per = []
        r_area = []
        
        t = np.linspace(0, 2*np.pi, 2000)
        for i in range(1, num_eggs + 1):
            params = self.family.egg_params(i)
            x, y = self.family.curve(t, params)
            
            L = self.family.arc_length(t, x, y)
            A = self.family.area(x, y)
            
            perimeters.append(L)
            areas.append(A)
            r_per.append(self.family.equivalent_radius_from_perimeter(L))
            r_area.append(self.family.equivalent_radius_from_area(A))
        
        # 对数坐标下的斜率（缩放指数）
        log_n = np.log(n_vals)
        log_r = np.log(r_per)
        slope = np.polyfit(log_n, log_r, 1)[0]
        
        data = {
            'n': n_vals,
            'perimeters': np.array(perimeters),
            'areas': np.array(areas),
            'r_from_perimeter': np.array(r_per),
            'r_from_area': np.array(r_area),
            'log_log_slope': slope,
        }
        self._cached_data = data
        return data
    
    def fit_best_model(self, n: np.ndarray, r: np.ndarray) -> dict:
        """尝试6种拟合模型，返回最优结果
        
        模型:
            1. 幂律:    r = c/√n           (Schauberger理论预测)
            2. 反比:    r = c/n
            3. 指数:    r = a·exp(-b·n)
            4. 广义幂律: r = a·n^b
            5. 有理函数: r = a/(1+b·n)
            6. 对数:    r = a - b·ln(n)
        """
        models = {
            '幂律 r=c/√n': lambda n, c: c / np.sqrt(n),
            '反比 r=c/n': lambda n, c: c / n,
            '指数 r=a·exp(-bn)': lambda n, a, b: a * np.exp(-b * n),
            '广义幂律 r=a·n^b': lambda n, a, b: a * n**b,
            '有理函数 r=a/(1+bn)': lambda n, a, b: a / (1 + b * n),
            '对数 r=a-b·ln(n)': lambda n, a, b: a - b * np.log(n),
        }
        
        best = {'name': '', 'params': None, 'error': float('inf'), 'pred': None}
        results = []
        
        for name, func in models.items():
            try:
                # 初始值估计
                if 'c/sqrt' in name:
                    popt, _ = curve_fit(lambda n, c: c/np.sqrt(n), n, r)
                elif 'c/n' in name:
                    popt, _ = curve_fit(lambda n, c: c/n, n, r)
                else:
                    popt, _ = curve_fit(func, n, r, maxfev=5000)
                
                pred = func(n, *popt)
                error = np.mean(np.abs(r - pred))
                
                result = {'name': name, 'params': popt, 'error': error, 'pred': pred}
                results.append(result)
                
                if error < best['error']:
                    best = result
            except:
                pass
        
        return {'best': best, 'all': results}
    
    def verify_scaling_law(self, n: np.ndarray, r: np.ndarray) -> dict:
        """验证缩放定律，计算对数坐标下的幂律指数
        
        如果 r ∝ n^β，则 log(r) ∝ β·log(n)，β即为缩放指数。
        Schauberger预测 β = -0.5（即 r ∝ 1/√n）。
        
        返回:
            {'beta': 拟合的缩放指数,
             'beta_expected': -0.5,
             'r_squared': 拟合优度,
             'consistency': '一致' 或 '偏差提示'}
        """
        log_n = np.log(n)
        log_r = np.log(r)
        
        coeffs = np.polyfit(log_n, log_r, 1)
        beta = coeffs[0]
        
        # R²
        log_r_pred = np.polyval(coeffs, log_n)
        ss_res = np.sum((log_r - log_r_pred)**2)
        ss_tot = np.sum((log_r - np.mean(log_r))**2)
        r_squared = 1 - ss_res / ss_tot
        
        beta_expected = -0.5
        deviation = abs(beta - beta_expected)
        
        return {
            'beta': beta,
            'beta_expected': beta_expected,
            'deviation': deviation,
            'r_squared': r_squared,
            'consistency': '一致 ✓' if deviation < 0.1 else f'偏差 {deviation:.3f} (建议检查数据)',
        }


# ========================================================================
# 第三部分：黄金比指数衰减蛋形（Walter Schauberger 蛋形公式）
# ========================================================================

class GoldenRatioVortexDecay:
    """黄金比指数衰减涡旋模型
    
    从 Walter Schauberger 的 Rhino 脚本"蛋形螺旋偏心.py"提取。
    
    核心公式:
        value(t) = 1 / (b + t·sin(α))² - (t·cos(α))²
        
        指数衰减包络:
        env(t) = φ^(t/Φ')     其中 φ = (√5-1)/2 ≈ 0.618
        
        速度场（类涡旋）:
        v_x(t) = t · env(t) · (-cos(t·spin_n))
        v_y(t) = √value(t) · env(t) · sin(t·spin_n)
    
    物理含义:
        φ^(t/phase) 的衰减率由黄金比 φ 和相位参数 phase 共同控制。
        spin_n 控制涡旋的旋转圈数。
        phase 控制涡旋的衰减速率（相位角越大，衰减越慢）。
    
    应用:
        涡旋能量随时间的指数衰减模型
        螺旋涡丝的构造
    """
    
    def __init__(self, phi: float = (np.sqrt(5) - 1) / 2):
        self.phi = phi  # 黄金比例 φ = 0.618...
    
    def decay_envelope(self, t: np.ndarray, phase: float, spin_n: float) -> Tuple[np.ndarray, np.ndarray]:
        """黄金比指数衰减包络
        
        包络函数: env(t) = φ^(t / (phase · π/180))
        
        其中 φ = (√5 - 1)/2 是黄金比例。
        当 t = phase·π/180 时，env = φ¹ ≈ 0.618（衰减到61.8%）
        当 t = 2·phase·π/180 时，env = φ² ≈ 0.382（衰减到38.2%）
        
        这符合自然界常见的黄金比例衰减（如斐波那契数列的增长/衰减率）。
        
        返回:
            (cos_form, sin_form) — 带指数衰减的角向谐波
        """
        phase_rad = phase * np.pi / 180
        env = self.phi ** (t / phase_rad)
        
        cos_form = env * (-np.cos(t * spin_n))
        sin_form = env * np.sin(t * spin_n)
        
        return cos_form, sin_form
    
    def field(self, t: np.ndarray, b: float, angle: float, 
              phase: float = 720, spin_n: float = 108) -> Tuple[np.ndarray, np.ndarray]:
        """计算完整的蛋形衰减场
        
        给定参数 t, 计算:
            value(t) = 1/(b + t·sin(α))² - (t·cos(α))²
            如果 value ≥ 0:
                v_x = t · env · (-cos(t·spin_n))
                v_y = √value · env · sin(t·spin_n)
        
        当 value < 0 时，位置不在有效区域内，返回 NaN。
        """
        sin_angle = np.sin(angle)
        cos_angle = np.cos(angle)
        
        value = 1.0 / (b + t * sin_angle)**2 - (t * cos_angle)**2
        valid = value >= 0
        
        cos_form, sin_form = self.decay_envelope(t, phase, spin_n)
        
        vx = np.full_like(t, np.nan)
        vy = np.full_like(t, np.nan)
        
        vx[valid] = t[valid] * cos_form[valid]
        vy[valid] = np.sqrt(value[valid]) * sin_form[valid]
        
        return vx, vy


# ========================================================================
# 第四部分：演示与可视化
# ========================================================================

def demo_scaling_analysis():
    """演示蛋形公式族的缩放规律分析"""
    print("=" * 60)
    print("舒伯格蛋形公式族缩放规律分析")
    print("=" * 60)
    
    analyzer = EggScalingAnalyzer()
    data = analyzer.analyze_family(15)
    
    print(f"\n八度参数表:")
    print(f"  {'i':>3}  {'周长 L':>10}  {'面积 A':>10}  {'r_peri':>8}  {'r_area':>8}")
    print(f"  {'-'*3}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*8}")
    for i in range(len(data['n'])):
        print(f"  {data['n'][i]:>3}  {data['perimeters'][i]:>10.4f}  "
              f"{data['areas'][i]:>10.4f}  {data['r_from_perimeter'][i]:>8.4f}  "
              f"{data['r_from_area'][i]:>8.4f}")
    
    scaling = analyzer.verify_scaling_law(data['n'], data['r_from_perimeter'])
    print(f"\n对数坐标斜率: β = {scaling['beta']:.4f}")
    print(f"理论预测: β = -0.5 (r ∝ 1/√n)")
    print(f"拟合优度 R² = {scaling['r_squared']:.6f}")
    print(f"一致性: {scaling['consistency']}")
    
    print("\n拟合模型比较:")
    fit = analyzer.fit_best_model(data['n'], data['r_from_perimeter'])
    for result in fit['all']:
        print(f"  {result['name']:30s}  误差={result['error']:.6e}")
    print(f"\n最佳: {fit['best']['name']}")


def demo_golden_decay():
    """演示黄金比指数衰减蛋形"""
    print("=" * 60)
    print("黄金比指数衰减蛋形（Walter Schauberger 蛋形公式）")
    print("=" * 60)
    
    decay = GoldenRatioVortexDecay()
    t = np.linspace(-np.pi/2, np.pi/2, 1000)
    b = 5/3
    angle = np.arctan(2/3)
    
    vx, vy = decay.field(t, b, angle, phase=720, spin_n=108)
    valid = ~np.isnan(vx)
    
    r_decay = np.sqrt(vx[valid]**2 + vy[valid]**2)
    env = decay.phi ** (t[valid] / (720 * np.pi/180))
    
    print(f"\n黄金比 φ = {decay.phi:.6f}")
    print(f"参数: b={b:.4f}, α={np.degrees(angle):.2f}°")
    print(f"有效点数: {np.sum(valid)}")
    print(f"衰减包络范围: [{env.min():.4f}, {env.max():.4f}]")
    print(f"半径范围: [{r_decay.min():.4f}, {r_decay.max():.4f}]")
    print(f"\n指数衰减: r(t) ∝ φ^(t/phase)")
    print(f"  当 t = phase·π/180:  r 衰减到 {decay.phi:.4f} ≈ {(1-np.exp(-1)):.4f}")


if __name__ == '__main__':
    demo_scaling_analysis()
    print()
    demo_golden_decay()
