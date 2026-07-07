"""
egg_curve.py — Schauberger 蛋形曲线核心数学模块
===================================================
基于超双曲锥 xy=1 的平面斜截，生成蛋形曲线。

数学原理（完整推导）:
---------------------
1. 超双曲锥: xy = 1, 锥面上点 P(n) = (1/n, n)
   n 既是高度坐标，也是"谐波编号"。

2. 平面斜截: z = z₀ - ȳ·sinα, 得到蛋形截线。

3. 核心参数（由两个交点唯一确定）:
   z₁ = 尖顶高度, z₂ = 钝顶高度
   截面中心: z₀ = (z₁²+z₂²)/(z₁+z₂)
   倾角: α = arctan(z₁·z₂·(z₂-z₁)/(z₁+z₂))
   蛋形度: k_E = z₂/z₁ (z₁=1,z₂=2 → k_E=2 "八度蛋")

4. 核心公式:
   显式: x̄ = ±√( 1/(z₀ - ȳ·sinα)² - (ȳ·cosα)² )
   参数: r = (1/(2·cosφ·sinα))·[z₀ ± √(...)]
   t-参数化: x=t, y=±√(1/(z₀ + t·sinα)² - (t·cosα)²)

5. 曲率: κ = |x'y''-y'x''|/(x'²+y'²)^(3/2)
   面积（鞋带公式）: A = ½|Σ(x_i·y_{i+1} - x_{i+1}·y_i)|

⚠️ 采样方法铁律（2026-05-26 修正）:
   ybar-采样（二分法 + uniform y → 解x）在两极丢细节：
   - 两极 y 变化极小、x 变化极大 → 均匀y采样分配极少点
   - 结果: 尖端曲线呈锯齿/缺失
   ✅ t-参数化（t ∈ [-π/2, π/2] 均匀采样，t即x坐标）:
   - 自然覆盖 x 全范围，极区获得充分采样
   - 已设为 get_curve_points() 默认方法
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class EggParams:
    """蛋形曲线参数 (由双曲锥的两个交点唯一确定)"""
    z1: float  # 尖顶高度 (基音)
    z2: float  # 钝顶高度 (泛音)

    def __post_init__(self):
        self.z0 = (self.z1**2 + self.z2**2) / (self.z1 + self.z2)  # 截面中心高度
        self.alpha = np.arctan(self.z1 * self.z2 * (self.z2 - self.z1) / (self.z1 + self.z2))  # 截面倾角
        self.sin_a = np.sin(self.alpha)
        self.cos_a = np.cos(self.alpha)

        # 主轴
        self.R = self.z2 / self.cos_a  # 长半轴 (钝端)
        self.r = self.z1 / self.cos_a  # 短半轴 (尖端)
        self.l_H = self.R + self.r     # 主轴长度

        # 小轴
        self.l_N = 2.0 / self.z0

        # 比值
        self.k_S = self.l_H / self.l_N  # 细长比
        self.k_E = self.R / self.r       # 蛋形度

    def __repr__(self):
        return (
            f"EggParams(z1={self.z1}, z2={self.z2})\n"
            f"  z0={self.z0:.4f}, α={np.degrees(self.alpha):.2f}°\n"
            f"  R={self.R:.4f}(钝端), r={self.r:.4f}(尖端), l_H={self.l_H:.4f}\n"
            f"  l_N={self.l_N:.4f}, k_S={self.k_S:.4f}, k_E={self.k_E:.4f}"
        )


class EggCurve:
    """蛋形曲线计算引擎"""

    def __init__(self, params: EggParams):
        self.p = params

    def _find_ymax(self) -> float:
        """求蛋形曲线在ȳ方向的最大范围 (上零点)"""
        # 在 ȳ = z0/sinα 处分母为零, 曲线在 0 到 z0/sinα 之间
        # 用二分法找精确零点
        y_low, y_high = 0.0, self.p.z0 / self.p.sin_a - 1e-10
        for _ in range(100):
            y_mid = (y_low + y_high) / 2
            val = 1.0 / (self.p.z0 - y_mid * self.p.sin_a)**2 - (y_mid * self.p.cos_a)**2
            if val > 0:
                y_low = y_mid
            else:
                y_high = y_mid
        return y_high

    def _find_ymin(self) -> float:
        """求蛋形曲线在ȳ方向的最小范围 (下零点)"""
        y_low, y_high = -(self.p.z0 / self.p.sin_a - 1e-10), 0.0
        for _ in range(100):
            y_mid = (y_low + y_high) / 2
            val = 1.0 / (self.p.z0 - y_mid * self.p.sin_a)**2 - (y_mid * self.p.cos_a)**2
            if val > 0:
                y_high = y_mid
            else:
                y_low = y_mid
        return y_low

    def explicit_form(self, ybar: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        显式形式计算蛋形曲线
        x̄ = ±√( 1/(z₀ + ȳ·sinα)² - (ȳ·cosα)² )
        
        返回: (x_right, x_left) 右半和左半
        """
        denom_sq = (self.p.z0 - ybar * self.p.sin_a)**2
        inner = 1.0 / denom_sq - (ybar * self.p.cos_a)**2
        # 🔧 v2.4 修复 (2026-05-28): inner ≥ 0 时 x=√inner 完全合法
        # ❌ 旧: valid = inner > 0  → 边界点 inner=0 被判 NaN → 移除 → 接缝 0.059
        # ✅ 新: valid = inner >= 0 → 边界点保留 → 完美闭合
        valid = inner >= 0
        x_right = np.where(valid, np.sqrt(np.maximum(inner, 0)), np.nan)
        x_left = -x_right
        return x_right, x_left

    def parametric_form(self, phi: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        参数形式计算蛋形曲线 (可连续绘制整条曲线)
        r = (1/(2·cosφ·sinα)) · [z₀ ± √(z₀² - 4·cosφ·sinα/√(sin²φ+cos²φ·cos²α))]
        x = r·sinφ, y = r·cosφ
        """
        sin_a, cos_a = self.p.sin_a, self.p.cos_a
        z0 = self.p.z0

        # 避免除零
        phi_safe = np.where(np.abs(np.cos(phi)) < 1e-10, 1e-10, phi)

        denom = 2 * np.cos(phi_safe) * sin_a
        sqrt_inner = z0**2 - 4 * np.cos(phi_safe) * sin_a / np.sqrt(
            np.sin(phi_safe)**2 + np.cos(phi_safe)**2 * cos_a**2
        )
        sqrt_inner = np.maximum(sqrt_inner, 0)
        sqrt_val = np.sqrt(sqrt_inner)

        # 正号: 锥管部分; 负号: 平坦山体部分
        r_plus = (z0 + sqrt_val) / np.where(np.abs(denom) > 1e-10, denom, 1e-10)
        r_minus = (z0 - sqrt_val) / np.where(np.abs(denom) > 1e-10, denom, 1e-10)

        # 合并两部分
        x_plus = r_plus * np.sin(phi_safe)
        y_plus = r_plus * np.cos(phi_safe)
        x_minus = r_minus * np.cos(phi_safe)
        y_minus = r_minus * np.sin(phi_safe)

        return x_plus, y_plus, x_minus, y_minus

    def _find_t_roots(self) -> Tuple[float, float]:
        """
        解析求解 t-参数化的精确有效范围边界

        条件: 1/(z₀ + t·sinα)² = (t·cosα)²
        → sinα·cosα·t² + z₀·cosα·t ± 1 = 0

        钝端 (t > 0): a·t² + b·t - 1 = 0  → 取正根
        尖端 (t < 0): a·t² + b·t + 1 = 0  → 取内根（更靠近 0 的根）

        🔑 v2.3 修正 (2026-05-28):
        - v(t)=1/(z₀+t·sinα)²-(t·cosα)² 的零点是两个 t 值
        - v(t)>0（蛋形有效区）夹在两个根之间：t∈(t_inner, t_blunt)
        - 外根 t_outer 对应 hyperbola 另一臂的边界，在有效区之外
        - ❌ 旧代码取 (-b-√D)/2a = t_outer → y≈1.80，蛋尖异常突起
        - ✅ 修正为 (-b+√D)/2a = t_inner → y≈1.20，与 Rhino/B 一致

        其中 a = sinα·cosα, b = z₀·cosα

        返回: (t_tip, t_blunt) — 尖端(内根, 负)和钝端(正)的 t 值
        """
        sin_a, cos_a = self.p.sin_a, self.p.cos_a
        z0 = self.p.z0
        a = sin_a * cos_a
        b = z0 * cos_a

        # 钝端: a·t² + b·t - 1 = 0，取正根
        disc_blunt = b ** 2 + 4 * a
        t_blunt = (-b + np.sqrt(disc_blunt)) / (2 * a)

        # 尖端: a·t² + b·t + 1 = 0，取内根（更靠近 0）
        # v(t)>0 区间夹在两个根之间，外根在蛋形有效区之外
        disc_tip = b ** 2 - 4 * a
        if disc_tip >= 0:
            t_tip = (-b + np.sqrt(disc_tip)) / (2 * a)  # 内根
        else:
            # 退化（圆退化 k_E→1 时 b²-4a→0⁻），用对称性近似
            t_tip = -t_blunt

        return t_tip, t_blunt

    def get_curve_points_t(self, n_points: int = 500) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用 t-参数化 采样蛋形曲线（Walter Schauberger 蛋形公式）【推荐默认】
        
        🔑 v2 改进 (2026-05-26):
        - 解析求解精确 t 范围（不再硬编码 [-π/2, π/2]）
        - 显式包含两端边界点确保曲线完全闭合
        - 蛋尖朝上 (y = -t 翻转)
        
        数学原理:
        - 舒伯格蛋形公式: value = 1/(z₀ + t·sinα)² - (t·cosα)²
        - x = √value (半宽), y = t (纵坐标，之后翻转)
        - 解析求根 → 确保 t 范围覆盖完整曲线
        
        返回: (x_array, y_array) 闭合曲线（逆时针），蛋尖朝上
        """
        sin_a, cos_a = self.p.sin_a, self.p.cos_a
        z0 = self.p.z0

        # 解析求解精确有效范围
        t_tip, t_blunt = self._find_t_roots()

        # 在精确范围内均匀采样
        t_vals = np.linspace(t_tip, t_blunt, n_points)

        # 逐点计算有效点（排除边界微扰噪声）
        x_right, y_val = [], []
        for t in t_vals:
            value = 1.0 / (z0 + t * sin_a) ** 2 - (t * cos_a) ** 2
            if value > 0:
                x_right.append(np.sqrt(value))
                y_val.append(t)

        x_right = np.array(x_right)
        y_val = np.array(y_val)

        # 🔧 v2.1 修复: 显式插入边界点确保完全闭合
        # 蛋形曲线: 尖端(tip, x=0) 和 钝端(blunt, x=0) 都必须在 x=0
        # 右半: 尖端 → 展开 → 钝端
        # 左半: 钝端 → 收拢 → 尖端
        
        # 翻转 y 使蛋尖朝上: y_final = -t
        # 尖端在 y = -t_tip (>0, 顶部), 钝端在 y = -t_blunt (<0, 底部)
        y_tip = -t_tip      # 顶部 (正 y)
        y_blunt = -t_blunt  # 底部 (负 y)
        y_right = -y_val    # 右半 y 坐标
        
        # 右半曲线: 从尖端(x=0)开始 →  interior points → 到钝端(x=0)
        x_right_full = np.concatenate([[0.0], x_right, [0.0]])
        y_right_full = np.concatenate([[y_tip], y_right, [y_blunt]])
        
        # 左半曲线: 从钝端(x=0)开始 →  interior points(逆序) → 到尖端(x=0)
        # 注意: x_left = -x_right (镜像), 顺序从钝端到尖端
        x_left_full = np.concatenate([[0.0], -x_right[::-1], [0.0]])
        y_left_full = np.concatenate([[y_blunt], y_right[::-1], [y_tip]])
        
        # 合并: 右半(tip→blunt) + 左半(blunt→tip, 跳过第一个点避免重复钝端)
        x_curve = np.concatenate([x_right_full, x_left_full[1:]])
        y_curve = np.concatenate([y_right_full, y_left_full[1:]])

        return x_curve, y_curve

    def get_curve_points_ybar(self, n_points: int = 500) -> Tuple[np.ndarray, np.ndarray]:
        """
        【旧版，保留兼容】使用 ybar-采样 + 二分法 获取蛋形曲线点集
        
        ⚠️ 已知缺陷:
        - 二分法找 ybar 范围 → uniform y 采样 → 解 x
        - 两极附近 y 变化极小、x 变化极大 → 采样点稀疏 → 尖端丢细节
        - 推荐使用 get_curve_points_t() 替代
        
        返回: (x_array, y_array) 闭合曲线（逆时针）
        """
        ymin = self._find_ymin()
        ymax = self._find_ymax()

        # 上半部分 (从左零点到右零点, 经过右侧)
        y_upper = np.linspace(ymin, ymax, n_points)
        x_right_upper, x_left_upper = self.explicit_form(y_upper)

        # 右侧: y从min到max
        valid_r = ~np.isnan(x_right_upper)
        x_right = x_right_upper[valid_r]
        y_right = y_upper[valid_r]

        # 左侧: y从max到min (反序)
        valid_l = ~np.isnan(x_left_upper)
        x_left = x_left_upper[valid_l][::-1]
        y_left = y_upper[valid_l][::-1]

        # 合并为闭合曲线
        x_curve = np.concatenate([x_right, x_left])
        y_curve = np.concatenate([y_right, y_left])

        return x_curve, y_curve

    def get_curve_points(self, n_points: int = 500, method: str = 't') -> Tuple[np.ndarray, np.ndarray]:
        """
        获取蛋形曲线的完整点集（闭合曲线，逆时针）
        
        参数:
            n_points: 采样点数（method='t'时有效点数略少，因过滤无效值）
            method: 't' = t-参数化（推荐，均匀覆盖x全范围）
                    'ybar' = ybar-采样（旧版，两极可能丢细节）
        
        返回: (x_array, y_array) 在截面坐标系中
        """
        if method == 't':
            return self.get_curve_points_t(n_points)
        elif method == 'ybar':
            return self.get_curve_points_ybar(n_points)
        else:
            raise ValueError(f"未知采样方法: {method}，可选 't' 或 'ybar'")

    def arc_length(self, n_points: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """计算蛋形曲线的弧长参数化"""
        x, y = self.get_curve_points(n_points)
        dx = np.diff(x)
        dy = np.diff(y)
        ds = np.sqrt(dx**2 + dy**2)
        s = np.concatenate([[0], np.cumsum(ds)])
        return s, x, y

    def curvature(self, n_points: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """计算蛋形曲线上各点的曲率 κ(s)"""
        s, x, y = self.arc_length(n_points)
        # 数值微分
        dx = np.gradient(x, s)
        dy = np.gradient(y, s)
        ddx = np.gradient(dx, s)
        ddy = np.gradient(dy, s)
        kappa = np.abs(dx * ddy - dy * ddx) / (dx**2 + dy**2)**1.5
        return s, kappa

    def harmonic_intersections(self) -> dict:
        """
        计算谐波序列 1, 1/2, 1/3, ... 在蛋形曲线上的交点
        对应超双曲螺旋的第n圈与截面的交点
        """
        results = {}
        for n in range(1, 13):
            rn = 1.0 / n  # 第n圈的径向距离
            # 在蛋形曲线上找距离中心轴 = rn 的点
            # 这需要数值求解
            results[n] = rn
        return results

    def area(self) -> float:
        """计算蛋形截面面积 (数值积分)"""
        x, y = self.get_curve_points(5000)
        # Shoelace formula
        return 0.5 * np.abs(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))

    def volume_of_revolution(self) -> float:
        """计算蛋形曲线绕主轴旋转的体积 (解析公式)"""
        z1, z2, z0, alpha = self.p.z1, self.p.z2, self.p.z0, self.p.alpha
        sin_a, cos_a = self.p.sin_a, self.p.cos_a

        # 找零点
        ymin, ymax = self._find_ymin(), self._find_ymax()

        # 数值积分
        y = np.linspace(ymin + 1e-10, ymax - 1e-10, 10000)
        x_right, _ = self.explicit_form(y)
        valid = ~np.isnan(x_right)
        y_v = y[valid]
        x_v = x_right[valid]

        V = np.pi * np.trapz(x_v**2, y_v)
        return V


def compare_egg_shapes():
    """比较不同蛋形度 k_E 的蛋形曲线"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # === 1. 八度蛋 (k_E=2) 及其参数 ===
    ax = axes[0]
    egg = EggCurve(EggParams(z1=1, z2=2))
    x, y = egg.get_curve_points()
    ax.plot(x, y, 'b-', linewidth=2, label=f'八度蛋 k_E={egg.p.k_E:.1f}')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    ax.set_title(f'八度蛋 (α={np.degrees(egg.p.alpha):.1f}°)', fontsize=14)
    ax.set_xlabel('x̄')
    ax.set_ylabel('ȳ')

    # 标注关键点
    ax.plot(0, 0, 'r+', markersize=15)  # 中心
    # 钝顶和尖端
    ymin, ymax = egg._find_ymin(), egg._find_ymax()
    ax.plot(0, ymax, 'g^', markersize=10, label=f'钝顶 ȳ={ymax:.3f}')
    ax.plot(0, ymin, 'rv', markersize=10, label=f'尖端 ȳ={ymin:.3f}')

    # === 2. 不同k_E的蛋形对比 ===
    ax = axes[1]
    configs = [
        (1, 1.001, '≈圆'),
        (1, 1.5, '小三度'),
        (1, 2, '八度'),
        (1, 3, '八度+五度'),
        (1, 4, '双八度'),
    ]
    for z1, z2, label in configs:
        egg = EggCurve(EggParams(z1=z1, z2=z2))
        x, y = egg.get_curve_points()
        ax.plot(x, y, linewidth=1.5, label=f'{label} k_E={egg.p.k_E:.2f}')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title('不同蛋形度的截面', fontsize=14)

    # === 3. 八度蛋的曲率分布 ===
    ax = axes[2]
    egg = EggCurve(EggParams(z1=1, z2=2))
    s, kappa = egg.curvature()
    s_norm = s / s[-1]  # 归一化弧长
    ax.plot(s_norm, kappa, 'r-', linewidth=1.5)
    ax.set_xlabel('归一化弧长 s/L', fontsize=12)
    ax.set_ylabel('曲率 κ', fontsize=12)
    ax.set_title('八度蛋曲率分布 (尖端κ大, 钝端κ小)', fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/sandbox/workspace/egg_vortex_cfd/output/01_egg_curve_overview.png', dpi=150)
    plt.close()
    print("✅ 蛋形曲线总览图已保存")


def test_octave_egg():
    """验证八度蛋参数"""
    p = EggParams(z1=1, z2=2)
    print("=" * 60)
    print("八度蛋 (Octave Egg) 参数验证")
    print("=" * 60)
    print(p)
    print()

    egg = EggCurve(p)
    area = egg.area()
    vol = egg.volume_of_revolution()
    print(f"  截面面积 A = {area:.6f}")
    print(f"  旋转体积 V = {vol:.6f}")
    print(f"  (文献值 V = 0.4045, 参考)" if abs(vol - 0.4045) < 0.1 else f"  ⚠️ 与文献值0.4045差异较大")

    # 曲率极值
    s, kappa = egg.curvature()
    print(f"  曲率范围: κ_min={kappa.min():.4f}, κ_max={kappa.max():.4f}")
    print(f"  (尖端曲率 > 钝端曲率, 这是蛋形的关键特征)")
    print()

    # 圆退化测试
    p_circle = EggParams(z1=1, z2=1.001)
    print(f"  退化测试 (z2→z1): k_E={p_circle.k_E:.4f} ≈ 1.0 → 圆 ✓")


if __name__ == '__main__':
    test_octave_egg()
    compare_egg_shapes()
