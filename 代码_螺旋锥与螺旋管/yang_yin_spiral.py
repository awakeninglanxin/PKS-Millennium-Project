"""
yang_yin_spiral.py — 阳阴螺旋几何（白银比·黄金比）
====================================================
从舒伯格黄金比锥面上提取的两种核心螺旋序列。

名相释义（传统数学物理对应）:
  ======== ========== ====== ============================
  中文名    英文译名    数学比   物理含义
  ======== ========== ====== ============================
  阳螺旋   Yang Spiral 白银比  扩张/发散/阳性
  (太阳)   (Silver Ratio)        (r = 2^(-t/2π) 以2为底)
  ------- ---------- ------ ----------------------------
  阴螺旋   Yin Spiral  黄金比  收缩/收敛/阴性
  (太阴)   (Golden Ratio)        (r = sin(t)/t 振荡衰减)
  ======== ========== ====== ============================

  注: 阳(太阳)、阴(太阴) 是中国传统哲学中"阴阳"的
  专有名词，不可直译为 sun/moon。在 PKS 体系中:
  - 阳 → 白银比数列 2^n (Silver Ratio = 1+√2 ≈ 2.414)
  - 阴 → 黄金比数列 φ^n (Golden Ratio = (√5-1)/2 ≈ 0.618)

数学背景:
  阳螺旋（白银比数列）: r = 2^(-t/2π), z = t·ln(2) / (2π·ln(ϕ))
     — 半径以 2 的幂次指数衰减，z 线性增长
     — 对应"扩张/发散"的阳性涡旋
     
  阴螺旋（黄金比数列）: r ∝ sin(t)/t (连续对数积分衰减),
     z = t/T (线性) 或 z = ln(t)/ln(ϕ) (对数)
     — 对应"收缩/收敛"的阴性涡旋

docx 参考:
  PKS两张图公式中的:
  - 红色曲线（双曲型）: x=±1/t, z=ln(t)/ln(ϕ)  — 超双曲锥 xy=1 的反比母线
  - 绿色曲线（sinc型）: x=(2π·sin(t))/t, z=log(t)/log(ϕ) — sinc(t)=sin(t)/t 辛格函数调幅
  - 阳数列2^t螺旋: 蓝色螺旋线在漏斗面上的投影

核心参数:
  ϕ = (√5 - 1)/2  — 黄金比例
  n — 波段/圈编号
  k = 1/(2π·ln(ϕ)) — 锥面螺旋常数

来源:
  - egg黄金比锥切面螺旋线-太阳数列2^t.py (r=1/r=2起点)
  - 螺旋蛋公式转成sin波 正.py
  - 双曲线阴-螺旋蛋公式转成sin波 ... -3d.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, Optional, List, Dict


# ========================================================================
# 公共常数
# ========================================================================
PHI = (np.sqrt(5) - 1) / 2          # 黄金比例 ϕ ≈ 0.618
LN_PHI = np.log(PHI)                 # ln(ϕ) ≈ -0.481 (负值)
LN2 = np.log(2)                      # ln(2) ≈ 0.693
K_SPIRAL = 1.0 / (2 * np.pi * LN_PHI)  # 螺旋常数 ≈ -0.331

# 白银比 (Silver Ratio)
SILVER_RATIO = 1 + np.sqrt(2)        # δ_S = 1+√2 ≈ 2.414


class YangSpiral:
    """阳螺旋（白银比 2^n 数列）
    
    红色曲线（双曲型）: x = 1/t, z = ln(t)/ln(ϕ)
      — 来自超双曲锥 xy=1 的反比母线，在数学物理中称 "双曲型螺旋"
      — 对应 PKS 图1中的红色母线：二维反比曲线在三维锥面上的展开
    蓝色螺旋线（白银比2^n）: r = 2^(-t/2π), z = t·ln(2)/(2π·ln(ϕ))
      — 半径以 2 的幂次指数衰减，每转一圈半径减半: r_n = 2^(-n)
    
    白银比 δ_S = 1+√2 ≈ 2.414 的离散展开形式。
    """
    
    def __init__(self, r_start: float = 1.0):
        """
        参数:
            r_start: 螺旋起始半径 (1.0 或 2.0, 对应docx中的r=1/r=2起点)
        """
        self.r_start = r_start
        self.phi = PHI
        self.ln_phi = LN_PHI
        self.ln2 = LN2
    
    # ------------------------------------------------------------------
    # 红色漏斗母线
    # ------------------------------------------------------------------
    
    def funnel_profile(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """红色漏斗母线（壁面轮廓）
        
        公式（来自 egg黄金比锥切面-太阳数列2^t.py）:
            x(t) = 1/t
            y(t) = 0
            z(t) = ln(t) / ln(ϕ)
        
        当 t → 0+: x → ∞, z → ∞（漏斗口）
        当 t → ∞:  x → 0,  z → -∞（漏斗尖）
        t = 1 时:  x = 1,  z = 0
        
        物理意义:
            这是涡旋漏斗的壁面轮廓线，
            沿 z 轴以黄金比对数螺旋自相似递进。
        """
        t_safe = np.maximum(t, 1e-10)
        x = 1.0 / t_safe
        if self.r_start > 1.0:
            x = self.r_start / t_safe
        y = np.zeros_like(t)
        z = np.log(t_safe) / self.ln_phi
        return x, y, z
    
    # ------------------------------------------------------------------
    # 阳螺旋（白银比 2^n 数列）核心公式
    # ------------------------------------------------------------------
    
    def spiral_2t(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阳螺旋（白银比 2^n 数列）对数螺旋线
        
        公式（来自 egg黄金比锥切面螺旋线-太阳数列2^t.py，第31-42行）:
            r(t)      = 2^(-t / 2π)          — 半径以2为底的指数衰减
            z(t)      = t/(2π) · (ln2/lnϕ)  — z 随 t 线性增长
            x(t)      = r(t) · cos(t)
            y(t)      = r(t) · sin(t)
        
        每转一圈 (t += 2π): 
            r 减半: r_{n+1} = r_n / 2
            z 增长: Δz = ln2/lnϕ ≈ 1.442 (固定步长)
        
        此即"太阳数列"（= 白银比数列 2^n）
        
        参数:
            t_vals: 参数 t 数组（弧度），从 0 到 t_max
        """
        r = 2.0 ** (-t_vals / (2 * np.pi))
        z = (t_vals / (2 * np.pi)) * (self.ln2 / self.ln_phi)
        
        if self.r_start > 1.0:
            r = r * self.r_start
        
        x = r * np.cos(t_vals)
        y = r * np.sin(t_vals)
        return x, y, z
    
    def spiral_markers(self, n_max: int) -> Dict:
        """阳螺旋的圈数标记点（r=2^(-n) 的位置）
        
        每个整圈位置 n:
            t_n    = 2π·n
            r_n    = 2^(-n)
            z_n    = n · (ln2/lnϕ)
            x_n    = r_n, y_n = 0 (在ZX平面)
        
        返回:
            {'n': [], 't': [], 'r': [], 'z': [], 'x': [], 'y': []}
        """
        n_arr = np.arange(n_max + 1)
        t_arr = 2 * np.pi * n_arr
        r_arr = 2.0 ** (-n_arr)
        if self.r_start > 1.0:
            r_arr = r_arr * self.r_start
        z_arr = n_arr * (self.ln2 / self.ln_phi)
        return {
            'n': n_arr, 't': t_arr, 'r': r_arr, 'z': z_arr,
            'x': r_arr, 'y': np.zeros_like(n_arr),
        }
    
    # ------------------------------------------------------------------
    # 平方数列变体（docx "创新"部分）
    # ------------------------------------------------------------------
    
    def spiral_square(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """平方数列 t² 螺旋变体
        
        公式（来自 egg黄金比锥切面螺旋线-平方数列t^2.py）:
            r(t) = (t_0 / t)²    — 半径按 t² 倒数衰减
            z(t) = ln(t)/ln(ϕ)   — 对数增长
        
        参数:
            t_vals: 从某个 t_min 开始
        """
        t_safe = np.maximum(t_vals, 1e-6)
        t0 = t_safe[0] if len(t_safe) > 0 else 1.0
        r = (t0 / t_safe) ** 2
        if self.r_start > 1.0:
            r = r * self.r_start
        z = np.log(t_safe) / self.ln_phi
        x = r * np.cos(t_safe)
        y = r * np.sin(t_safe)
        return x, y, z
    
    # ------------------------------------------------------------------
    # 黄金比数列变体
    # ------------------------------------------------------------------
    
    def spiral_golden(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """黄金比 ϕ^n 数列螺旋变体（太阴相关）
        
        公式（来自 egg黄金比锥切面螺旋线-黄金比数列.py）:
            r(t) = ϕ^(t/2π)   — 半径按黄金比衰减（ϕ<1）
            z(t) = ln(t)/ln(ϕ) 
        """
        t_safe = np.maximum(t_vals, 1e-6)
        r = self.phi ** (t_safe / (2 * np.pi))
        if self.r_start > 1.0:
            r = r * self.r_start
        z = np.log(t_safe) / self.ln_phi
        x = r * np.cos(t_safe)
        y = r * np.sin(t_safe)
        return x, y, z


class YinSpiral:
    """阴螺旋（黄金比 φ^n 数列）
    
    绿色曲线（sinc型）: x = (2π·sin(t))/t, z = ln(t)/ln(ϕ)
      — 数学本质是辛格函数 sinc(t) = sin(t)/t 的调幅
      — 在信号处理和物理中，sinc 函数描述理想低通滤波/驻波模式
      — 对应 PKS 图1中的绿色曲线：sinc 型调幅在黄金比锥面上的螺旋
    如 sin(t)/t 振荡衰减，零点间距 π，振幅按 1/t 衰减。
    
    与阳螺旋（白银比双曲型）的对比:
        阳螺旋（双曲型）: r = 2^(-t/2π)    — 指数衰减，无振荡
        阴螺旋（sinc型）: r ∝ sin(t)/t      — 振荡衰减（有零点）
        → 双曲型"发散"，sinc型"收敛"
    """
    
    def __init__(self):
        self.phi = PHI
        self.ln_phi = LN_PHI
    
    def spiral_decay_envelope(self, t: np.ndarray) -> np.ndarray:
        """连续对数积分衰减因子
        
        来自 双曲线阴...-3d.py 第13-19行:
            amp_continuous(t):
                n = t / T
                numerator   = 2(2n² + 2n + 1)
                denominator = n(n + 1)
                return 1/(t · √(numerator/denominator))  — 双曲水滴漏斗管型
        
        这个衰减因子是"阴"螺旋的核心——它比简单的 1/t 衰减更快，
        在 t 较大时产生更强烈的收缩。
        """
        T = 2 * np.pi
        n = t / T
        num = 2 * (2 * n**2 + 2 * n + 1)
        denom = n * (n + 1)
        return 1.0 / (t * np.sqrt(num / denom))
    
    def spiral_sin(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阴螺旋 sin(t)/t 数列
        
        公式（docx 绿色曲线）:
            x(t) = (2π · sin(t)) / t
            z(t) = ln(t) / ln(ϕ)
        
        旋转展开（用 t 作为极角）:
            x = r(t) · cos(t)
            y = r(t) · sin(t)
            r(t) = (2π · |sin(t)|) / t   （取绝对值保持正半径）
        
        参数:
            t_vals: 从 t_min (≥π) 开始
        """
        t_safe = np.maximum(np.abs(t_vals), 1e-6)
        amp = 2 * np.pi * np.abs(np.sin(t_safe)) / t_safe
        z = np.log(t_safe) / self.ln_phi
        x = amp * np.cos(t_safe)
        y = amp * np.sin(t_safe)
        return x, y, z
    
    def spiral_sin_continuous_decay(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阴螺旋 + 连续对数积分衰减（双曲水滴漏斗管型）
        
        来自 双曲线阴-螺旋蛋公式转成sin波...-3d.py 的实际实现:
            r(t) = amp_continuous(t) · sin(t)
            z(t) = t / T (线性高度)
        
        这是更复杂的"阴"螺旋，有更强烈的末端收缩。
        """
        T = 2 * np.pi
        amp = self.spiral_decay_envelope(t_vals)
        z = t_vals / T
        r = amp * 5.0  # 缩放因子，匹配原始脚本的视觉比例
        x = r * np.sin(t_vals)
        y = r * np.cos(t_vals)
        return x, y, z


# ========================================================================
# 交点几何：A_n 和 B_n
# ========================================================================

class IntersectionGeometry:
    """切线平面与漏斗曲线的交点几何
    
    对应 docx 中的蓝色切线:
        z = k·x + b_n
        k = 1/(2π·ln(ϕ))
    
    与红色曲线 x=±1/t 交于 A_n (负侧) 和 B_n (正侧)。
    
    交点条件:
        z   = ln(t)/ln(ϕ)     (红色曲线)
        z   = k·x + b_n       (蓝色切线)
        x   = ±1/t
        
    → ln(t)/ln(ϕ) = k·(±1/t) + b_n
    
    其中 b_n 由第n个波段的条件确定:
        每个波段的起点 t = (2n-1)π, 终点 t = 2nπ
    """
    
    def __init__(self):
        self.phi = PHI
        self.ln_phi = LN_PHI
        self.k = K_SPIRAL
    
    def tangent_line(self, x: np.ndarray, b_n: float) -> np.ndarray:
        """蓝色切线方程 z = k·x + b_n"""
        return self.k * x + b_n
    
    def find_b_n(self, n: int, r_start: float = 1.0) -> float:
        """计算第 n 个波段的 b_n
        
        对给定的 n（波段编号）:
            t_left  = (n-1)*π    — 波段左端点（即A_n位置）
            t_right = n*π        — 波段右端点（即B_n位置）
        
        当 r_start=1: A_n(-1/n, 0, ?), B_n(-1/(n+0.5), 0, ?)
        当 r_start=2: A_n(2/n, 0, ?), B_n(-1/n, 0, 0)  (docx中r=2的特殊情况)
        
        注意: 这里实现的是 docx 中 r=1 版本的标准交点计算。
        r=2 版本的 b_n 不同，见 docx 第39-42行。
        """
        if r_start == 1.0:
            t_start = (2 * n - 1) * np.pi
            t_end = 2 * n * np.pi
            
            x_A = -1.0 / t_start
            z_A = np.log(t_start) / self.ln_phi
            b_A = z_A - self.k * x_A
            
            x_B = 1.0 / t_end
            z_B = np.log(t_end) / self.ln_phi
            b_B = z_B - self.k * x_B
            
            b_n = (b_A + b_B) / 2.0
            return b_n
            
        elif r_start == 2.0:
            t_A = n * np.pi
            x_A = 2.0 / t_A
            z_A_real = np.log(t_A / 2) / self.ln_phi
            
            b_n = z_A_real - self.k * x_A
            return b_n
        
        return 0.0
    
    def intersection_point(self, n: int, side: str = 'A', 
                          r_start: float = 1.0) -> Tuple[float, float, float]:
        """计算 A_n 或 B_n 交点的精确坐标
        
        side: 'A' — 左交点 (负x侧), 'B' — 右交点 (正x侧)
        
        返回 (x, y, z)
        """
        if r_start == 1.0:
            if side == 'A':
                t_val = (2 * n - 1) * np.pi
                x_val = -1.0 / t_val
                z_val = np.log(t_val) / self.ln_phi
            else:
                t_val = 2 * n * np.pi
                x_val = 1.0 / t_val
                z_val = np.log(t_val) / self.ln_phi
        elif r_start == 2.0:
            if side == 'A':
                t_val = n * np.pi
                x_val = 2.0 / t_val
                z_val = np.log(t_val / 2) / self.ln_phi
            else:
                t_val = n * np.pi
                x_val = -1.0 / t_val
                z_val = 0.0
        
        return (x_val, 0.0, z_val)
    
    def distance_L_n(self, n: int, r_start: float = 1.0) -> float:
        """A_n 和 B_n 之间的距离 L_n"""
        A = self.intersection_point(n, 'A', r_start)
        B = self.intersection_point(n, 'B', r_start)
        return np.sqrt((B[0] - A[0])**2 + (B[2] - A[2])**2)
    
    def ratio_n(self, n: int, r_start: float = 1.0) -> float:
        """abs(x_A_n / x_B_n) 比值"""
        A = self.intersection_point(n, 'A', r_start)
        B_val = self.intersection_point(n, 'B', r_start)
        if abs(B_val[0]) < 1e-15:
            return float('inf')
        return abs(A[0] / B_val[0])
    
    def z_axis_intercept(self, n: int, r_start: float = 1.0) -> float:
        """切线在 z 轴的截距 (0, 0, b_n)"""
        b_n = self.find_b_n(n, r_start)
        return b_n


# ========================================================================
# 可视化
# ========================================================================

def demo():
    """演示阳阴螺旋几何"""
    print("=" * 60)
    print("阳阴螺旋（白银比·黄金比）几何分析")
    print("=" * 60)
    
    # 1. 阳螺旋（白银比）
    print("\n1. 阳螺旋 2^t（白银比数列, r=1起点）")
    yang = YangSpiral(r_start=1.0)
    t_vals = np.linspace(0, 12 * np.pi, 1000)
    sx, sy, sz = yang.spiral_2t(t_vals)
    print(f"   螺旋点数: {len(sx)}")
    print(f"   x范围: [{sx.min():.4f}, {sx.max():.4f}]")
    print(f"   z范围: [{sz.min():.4f}, {sz.max():.4f}]")
    
    markers = yang.spiral_markers(5)
    print(f"\n   圈数标记 (r=2^(-n)):")
    for i in range(len(markers['n'])):
        print(f"     n={int(markers['n'][i])}: r={markers['r'][i]:.6f}, "
              f"z={markers['z'][i]:.4f}")
    
    # 2. 阴螺旋（黄金比）
    print("\n2. 阴螺旋 sin(t)/t（黄金比数列）")
    yin = YinSpiral()
    t_yin = np.linspace(np.pi, 15 * np.pi, 1000)
    mx, my, mz = yin.spiral_sin(t_yin)
    print(f"   螺旋点数: {len(mx)}")
    print(f"   x范围: [{mx.min():.4f}, {mx.max():.4f}]")
    
    # 3. 交点几何 (A_n, B_n)
    print("\n3. 交点几何分析 (r=1)")
    geo = IntersectionGeometry()
    for n in range(1, 6):
        A = geo.intersection_point(n, 'A')
        B_val = geo.intersection_point(n, 'B')
        L = geo.distance_L_n(n)
        ratio = geo.ratio_n(n)
        b_n = geo.z_axis_intercept(n)
        print(f"   n={n}: A({A[0]:.4f}, {A[2]:.4f}) "
              f"B({B_val[0]:.4f}, {B_val[2]:.4f}) "
              f"L_n={L:.4f} ratio={ratio:.4f} b_n={b_n:.4f}")
    
    # 4. 平方数列变体
    print("\n4. 平方数列 t² 螺旋变体")
    t_sq = np.linspace(1.0, 6 * np.pi, 1000)
    qx, qy, qz = yang.spiral_square(t_sq)
    print(f"   点数: {len(qx)}")
    print(f"   首点半径: {np.sqrt(qx[0]**2+qy[0]**2):.4f}")
    print(f"   末点半径: {np.sqrt(qx[-1]**2+qy[-1]**2):.4f}")
    
    print(f"\n✅ 阳阴螺旋几何分析完成")


if __name__ == '__main__':
    demo()
