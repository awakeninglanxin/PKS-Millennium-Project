"""
egg_3d_spiral.py — PKS 太阳太阴螺旋 3D 曲线生成器
====================================================

基于 PKS 舒伯格黄金比锥面的阳螺旋（太阳/白银比）和阴螺旋（太阴/黄金比）
3D 曲线生成，并导出为 DXF/VTK 等格式供 CFD 使用。

数学原理
============

核心公式（来自 pks两张图公式 太阳太阴螺旋.docx）：

漏斗双曲线（旋转面母线）:
    x = 1/t, z = ln(t)/ln(φ), t ∈ (0, ∞)
    绕 z 轴旋转 360° 得漏斗曲面。

阳螺旋（太阳·白银比 2^n 数列）:
    r(t) = 2^(-t/2π)
    z(t) = t/(2π) · (ln2/lnφ)
    位于漏斗面上，每转一圈半径减半。

阴螺旋（太阴·黄金比 φ^n 卢卡斯数列）:
    r(t) = r_start · φ_large^(-t/2π)  (φ_large = (1+√5)/2 ≈ 1.618)
    z(t) = t/(2π) · (ln φ_large / ln φ_small) = -t/(2π)
    每转一圈半径乘以 φ_small ≈ 0.618 (卢卡斯极限 L(n-1)/L(n)→φ_small)。
    卢卡斯数列: 2,1,3,4,7,11,18,29,47,... (L(n)=L(n-1)+L(n-2), 比值→φ_large)。

常数:
    φ = (√5 - 1)/2           — 黄金比例
    k = 1/(2π·ln(φ))         — 锥面螺旋常数

交点几何（A_n 和 B_n）:
    蓝色切线 z = k·x + b_n 与红漏斗曲线交于 A_n(负侧) 和 B_n(正侧)。
    每个完整波段 n: t ∈ [(2n-1)π, 2nπ] (r=1) 或 t ∈ [nπ, (n+1)π] (r=2)。

参考文献:
    - pks两张图公式 太阳太阴螺旋.docx
    - yang_yin_spiral.py（阳阴螺旋几何实现）
    - egg黄金比锥切面螺旋线-太阳数列2^t.py（原始 Rhino 脚本）
    - 双曲线阴-螺旋蛋公式转成sin波...-3d.py（阴螺旋衰减）
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# numpy compatibility
_trapz = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')

# ════════════════════════════════════════════════════════════════════════
# PKS 常数
# ════════════════════════════════════════════════════════════════════════
PHI = (np.sqrt(5) - 1) / 2          # 黄金比例 φ ≈ 0.618 (小黄金比)
PHI_LARGE = (1 + np.sqrt(5)) / 2    # 大黄金比 Φ ≈ 1.618
LN_PHI = np.log(PHI)                 # ln(φ) ≈ -0.481 (负值)
LN_PHI_LARGE = np.log(PHI_LARGE)     # ln(Φ) ≈ 0.481
LN2 = np.log(2)                      # ln(2) ≈ 0.693
K_SPIRAL = 1.0 / (2 * np.pi * LN_PHI)  # 螺旋常数 ≈ -0.331


def lucas_sequence(n_max: int) -> np.ndarray:
    """卢卡斯数列 L(n): L(0)=2, L(1)=1, L(n)=L(n-1)+L(n-2)

    前几项: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...
    L(n+1)/L(n) → Φ (大黄金比 ≈ 1.618)，与斐波那契数列同极限。
    """
    if n_max < 0:
        return np.array([])
    if n_max == 0:
        return np.array([2])
    L = [2, 1]
    for i in range(2, n_max + 1):
        L.append(L[-1] + L[-2])
    return np.array(L)


class PKSEggSpiral:
    """PKS 蛋形螺旋曲线生成器

    基于舒伯格黄金比锥面，生成阳螺旋（太阳·白银比 2^n）
    和阴螺旋（太阴·黄金比 φ^n）3D 曲线。

    参数
    ------
    r_start : float
        起始半径 (1.0 或 2.0)，对应 docx 中 r=1/r=2 两种方案
    max_n : int
        最大波段数（螺旋延伸的周期数）
    n_points_per_wave : int
        每个波段 (2π) 的采样点数
    """

    def __init__(self, r_start: float = 1.0, max_n: int = 14,
                 n_points_per_wave: int = 200):
        self.phi = PHI
        self.ln_phi = LN_PHI
        self.ln2 = LN2
        self.r_start = r_start
        self.max_n = max_n
        self.n_ppw = n_points_per_wave

    # ═══════════════════════════════════════════════════════════════════
    # 漏斗双曲线（红色曲线）
    # ═══════════════════════════════════════════════════════════════════

    def funnel_profile(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """漏斗壁面轮廓（正侧 x=1/t, z=ln(t)/lnφ）

        返回 x, y, z（y=plane，即 2D 轮廓在 xz 平面）
        """
        t_safe = np.maximum(t, 1e-10)
        x = self.r_start / t_safe
        y = np.zeros_like(t)
        z = np.log(t_safe) / self.ln_phi
        return x, y, z

    def funnel_surface(self, t: np.ndarray, n_theta: int = 60
                       ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """漏斗曲面网格（旋转 x=1/t 绕 z 轴）

        返回 X, Y, Z 网格 (n_theta × len(t))
        """
        theta = np.linspace(0, 2*np.pi, n_theta)
        t_safe = np.maximum(t, 1e-10)
        r = self.r_start / t_safe
        z = np.log(t_safe) / self.ln_phi

        TH, R = np.meshgrid(theta, r)
        Z = np.tile(z, (n_theta, 1)).T

        X = R * np.cos(TH)
        Y = R * np.sin(TH)
        return X, Y, Z

    # ═══════════════════════════════════════════════════════════════════
    # 阳螺旋（太阳·白银比 2^n 数列）
    # ═══════════════════════════════════════════════════════════════════

    def yang_spiral(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阳螺旋（白银比 2^n 数列）

        公式:
            r(t) = r_start · 2^(-t/2π)
            z(t) = (t/2π) · (ln2/lnφ)
            x(t) = r(t) · cos(t)
            y(t) = r(t) · sin(t)

        验证位于漏斗面上: r_yang = 2^(-t/2π), 漏斗 r_funnel = φ^(-z_yang)
        z_yang = (t/2π)·(ln2/lnφ) → φ^z_yang = 2^(t/2π) → r_funnel = 2^(-t/2π) ✓
        """
        r = self.r_start * (2.0 ** (-t_vals / (2 * np.pi)))
        z = (t_vals / (2 * np.pi)) * (self.ln2 / self.ln_phi)

        x = r * np.cos(t_vals)
        y = r * np.sin(t_vals)
        return x, y, z

    def yang_markers(self, n_max: int = None) -> Dict:
        """阳螺旋圈数标记点（每半圈一个标记）

        n = 0, 1, 2, ... , n_max
        r_n = r_start · 2^(-n) — 每整圈半径减半
        """
        if n_max is None:
            n_max = self.max_n
        n_arr = np.arange(n_max + 1)
        t_arr = 2 * np.pi * n_arr
        r_arr = self.r_start * (2.0 ** (-n_arr))
        z_arr = n_arr * (self.ln2 / self.ln_phi)
        return {
            'n': n_arr, 't': t_arr, 'r': r_arr, 'z': z_arr,
            'x': r_arr, 'y': np.zeros_like(n_arr),
        }

    # ═══════════════════════════════════════════════════════════════════
    # 阴螺旋（太阴·黄金比 φ^n 数列）
    # ═══════════════════════════════════════════════════════════════════

    def yin_spiral(self, t_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阴螺旋 — 卢卡斯数列·黄金比 Φ^(-t/2π)

        公式:
            r(t) = r_start · Φ^(-t/2π)
                  其中 Φ = (1+√5)/2 ≈ 1.618 (大黄金比)
                  → 每转一圈 r_{n+1}/r_n = Φ^(-1) = φ ≈ 0.618
            z(t) = t/(2π) · (ln Φ / ln φ)
                 = -t/(2π)  (因为 ln Φ = -ln φ)

        卢卡斯数列意义:
            L(n): 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...
            L(n+1)/L(n) → Φ (与斐波那契相同极限, 初值不同)
            离散标记: r_n = r_start / L(n) (n≥0 时为衰减序列)

        与阳螺旋的对比:
            阳(白银比 2^n): r_{n+1}/r_n = 0.5,  z step = -1.44/turn
            阴(黄金比 Φ^n): r_{n+1}/r_n = 0.618, z step = -1.00/turn
            → 阴螺旋衰减更慢, 下沉更缓, 视觉上"更舒展"
        """
        t_safe = np.maximum(t_vals, 1e-10)
        # r(t) = r_start · Φ^(-t/2π)  — 以黄金比大值 Φ 为底的指数衰减
        r = self.r_start * (PHI_LARGE ** (-t_safe / (2 * np.pi)))
        # z(t) = t/(2π) · (lnΦ/lnφ) = -t/(2π)  — 线性下降
        z = (t_safe / (2 * np.pi)) * (LN_PHI_LARGE / self.ln_phi)

        x = r * np.cos(t_safe)
        y = r * np.sin(t_safe)
        return x, y, z

    def yin_lucas_markers(self, n_max: int = None) -> Dict:
        """阴螺旋卢卡斯数列标记点

        n = 0, 1, 2, ..., n_max
        r_n = r_start / L(n)  — 基于卢卡斯数列的半径
        z_n = n · (lnΦ/lnφ)  — 对应每步 z 偏移
        """
        if n_max is None:
            n_max = self.max_n
        L = lucas_sequence(n_max)
        n_arr = np.arange(len(L))
        # 半径 = r_start / L(n)
        r_arr = np.where(L > 0, self.r_start / L, 0.0)
        z_arr = n_arr * (LN_PHI_LARGE / self.ln_phi)  # = -n (since LN_PHI_LARGE/ln_phi = -1)
        t_arr = 2 * np.pi * n_arr  # 对应连续 t 值
        return {
            'n': n_arr, 'L': L, 't': t_arr, 'r': r_arr, 'z': z_arr,
            'x': r_arr, 'y': np.zeros_like(n_arr),
        }

    # ═══════════════════════════════════════════════════════════════════
    # 交点几何
    # ═══════════════════════════════════════════════════════════════════

    def intersection_points(self, n: int) -> Dict:
        """计算第 n 个波段的交点 A_n 和 B_n

        r=1 方案:
            A_n: t = (2n-1)π, x = -1/t, z = ln(t)/ln(φ)
            B_n: t = 2nπ,     x = +1/t, z = ln(t)/ln(φ)

        r=2 方案:
            A_n: t = nπ,  x = 2/t,  z = ln(t/2)/ln(φ)
            B_n: t = nπ,  x = -1/t, z = 0

        返回 {'A': (x,y,z), 'B': (x,y,z), 'L_n': 间距,
              'b_n': z截距, 'ratio_n': |x_A/x_B|}
        """
        if self.r_start == 1.0:
            t_A = (2 * n - 1) * np.pi
            t_B = 2 * n * np.pi
            x_A = -self.r_start / t_A
            z_A = np.log(t_A) / self.ln_phi
            x_B = self.r_start / t_B
            z_B = np.log(t_B) / self.ln_phi
        elif self.r_start == 2.0:
            t_A = n * np.pi
            t_B = n * np.pi
            x_A = 2.0 / t_A
            z_A = np.log(t_A / 2) / self.ln_phi
            x_B = -1.0 / t_B
            z_B = 0.0
        else:
            raise ValueError(f"r_start={self.r_start} 仅支持 1.0 或 2.0")

        # 切线 z = K_SPIRAL·x + b_n
        b_A = z_A - K_SPIRAL * x_A
        b_B = z_B - K_SPIRAL * x_B
        b_n = (b_A + b_B) / 2.0

        L_n = np.sqrt((x_B - x_A)**2 + (z_B - z_A)**2)
        ratio_n = abs(x_A / x_B) if abs(x_B) > 1e-15 else float('inf')

        return {
            'A': (float(x_A), 0.0, float(z_A)),
            'B': (float(x_B), 0.0, float(z_B)),
            'L_n': float(L_n),
            'b_n': float(b_n),
            'ratio_n': float(ratio_n),
            'n': n,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 生成完整曲线数据
    # ═══════════════════════════════════════════════════════════════════

    def generate_yang_curve(self, max_n: int = None) -> Dict:
        """生成阳螺旋（太阳）完整 3D 曲线

        返回 dict with 't', 'x', 'y', 'z', 'params', 'length'
        """
        if max_n is None:
            max_n = self.max_n

        t = np.linspace(0, 2 * np.pi * max_n, self.n_ppw * max_n)
        x, y, z = self.yang_spiral(t)

        # 曲线长度
        dx = np.gradient(x, t)
        dy = np.gradient(y, t)
        dz = np.gradient(z, t)
        ds = np.sqrt(dx**2 + dy**2 + dz**2)
        length = _trapz(ds, t)

        return {
            't': t, 'x': x, 'y': y, 'z': z,
            'params': {'r_start': self.r_start, 'max_n': max_n,
                        'type': 'yang', 'spiral': '太阳·白银比 2^n'},
            'length': length,
        }

    def generate_yin_curve(self, max_n: int = None) -> Dict:
        """生成阴螺旋（太阴·卢卡斯数列）完整 3D 曲线"""
        if max_n is None:
            max_n = self.max_n

        t = np.linspace(0, 2 * np.pi * max_n, self.n_ppw * max_n)
        x, y, z = self.yin_spiral(t)

        dx = np.gradient(x, t)
        dy = np.gradient(y, t)
        dz = np.gradient(z, t)
        ds = np.sqrt(dx**2 + dy**2 + dz**2)
        length = _trapz(ds, t)

        return {
            't': t, 'x': x, 'y': y, 'z': z,
            'params': {'r_start': self.r_start, 'max_n': max_n,
                        'type': 'yin', 'spiral': '太阴·黄金比 Lucas'},
            'length': length,
        }

    # ═══════════════════════════════════════════════════════════════════
    # 参数扫描
    # ═══════════════════════════════════════════════════════════════════

    def scan_max_n(self, values: List[int], spiral_type: str = 'yang'
                   ) -> List[Dict]:
        """扫描 max_n 参数（波段数），对比不同延伸深度"""
        results = []
        for val in values:
            if spiral_type == 'yang':
                result = self.generate_yang_curve(max_n=val)
            else:
                result = self.generate_yin_curve(max_n=val)
            result['scan_param'] = 'max_n'
            result['scan_value'] = val
            results.append(result)
        return results

    # ═══════════════════════════════════════════════════════════════════
    # 可视化
    # ═══════════════════════════════════════════════════════════════════

    def plot_3d(self, curve_data: Dict = None, spiral_type: str = 'yang',
                show_funnel: bool = True, show_intersections: bool = True,
                save_path: Optional[str] = None, figsize: Tuple[int, int] = (12, 10)):
        """3D 蛋形螺旋可视化（含漏斗面、交点标记）"""
        if curve_data is None:
            if spiral_type == 'yang':
                curve_data = self.generate_yang_curve()
            else:
                curve_data = self.generate_yin_curve()

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')

        x, y, z = curve_data['x'], curve_data['y'], curve_data['z']
        params = curve_data['params']

        # ── 漏斗曲面（半透明） ──
        if show_funnel:
            t_f = np.linspace(0.5, 2 * params['max_n'], 100)
            Xf, Yf, Zf = self.funnel_surface(t_f, n_theta=40)
            ax.plot_surface(Xf, Yf, Zf, alpha=0.10, color='red',
                            linewidth=0, antialiased=True)

        # ── 螺旋曲线 ──
        color = 'dodgerblue' if params['type'] == 'yang' else 'green'
        label = f'{params["spiral"]} (r={params["r_start"]}, n={params["max_n"]})'
        ax.plot(x, y, z, linewidth=1.5, color=color, label=label)

        # ── 交点标记 ──
        if show_intersections and params['type'] == 'yang':
            markers = self.yang_markers(params['max_n'])
            ax.scatter(markers['x'], markers['y'], markers['z'],
                       c='orange', s=30, edgecolors='darkorange',
                       linewidths=0.5, label='Yang 半圈标记 (r=2^(-n))')

        # ── 漏斗轮廓线（正侧） ──
        if show_funnel:
            t_prof = np.linspace(0.5, 2 * params['max_n'], 200)
            fx, _, fz = self.funnel_profile(t_prof)
            ax.plot(fx, np.zeros_like(fx), fz,
                    'red', linewidth=1, alpha=0.5, label='漏斗母线 x=1/t')

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'PKS Egg Spiral — {params["spiral"]}\n'
                     f'(r={params["r_start"]}, n_max={params["max_n"]}, '
                     f'L={curve_data["length"]:.2f})', fontsize=12)

        ax.legend(fontsize=9, loc='upper left')

        # 等轴调整
        all_coords = np.concatenate([x, y, z])
        max_range = (all_coords.max() - all_coords.min()) * 0.55
        mid = all_coords.mean()
        ax.set_xlim(mid - max_range, mid + max_range)
        ax.set_ylim(mid - max_range, mid + max_range)
        ax.set_zlim(mid - max_range, mid + max_range)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    def plot_scan(self, values: List[int], spiral_type: str = 'yang',
                  save_path: Optional[str] = None, figsize: Tuple[int, int] = (14, 11)):
        """扫描 max_n 参数，多条螺旋叠加 + 漏斗"""
        results = self.scan_max_n(values, spiral_type)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')

        # ── 漏斗曲面 ──
        t_f = np.linspace(0.5, 2 * max(values), 80)
        Xf, Yf, Zf = self.funnel_surface(t_f, n_theta=30)
        ax.plot_surface(Xf, Yf, Zf, alpha=0.08, color='red',
                        linewidth=0, antialiased=True)

        # ── 多条螺旋叠加 ──
        colors = plt.cm.plasma(np.linspace(0.15, 0.95, len(results)))
        for idx, result in enumerate(results):
            x, y, z = result['x'], result['y'], result['z']
            n_val = result['scan_value']
            ax.plot(x, y, z, color=colors[idx], linewidth=1.5,
                    alpha=0.85, label=f'n_max={n_val} (L={result["length"]:.1f})')

        # ── 漏斗轮廓 ──
        t_prof = np.linspace(0.5, 2 * max(values), 200)
        fx, _, fz = self.funnel_profile(t_prof)
        ax.plot(fx, np.zeros_like(fx), fz, 'red', linewidth=1,
                alpha=0.4, label='漏斗母线 x=1/t')

        sp_label = '太阳·白银比 2^n' if spiral_type == 'yang' else '太阴·卢卡斯数列 Φ^n'
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'PKS Egg Spiral Scan — {sp_label} (r={self.r_start})',
                     fontsize=13)

        ax.legend(fontsize=8, loc='upper left', ncol=1)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    def plot_yang_yin_comparison(self, max_n: int = 14,
                                 save_path: Optional[str] = None):
        """阳阴螺旋对比图（双面板）"""
        fig = plt.figure(figsize=(16, 7))

        sp_types = [('yang', '阳螺旋 太阳·白银比 2^n', 'dodgerblue'),
                     ('yin', '阴螺旋 太阴·卢卡斯数列 Φ^n', 'green')]

        for idx, (stype, title, color) in enumerate(sp_types):
            ax = fig.add_subplot(1, 2, idx + 1, projection='3d')

            if stype == 'yang':
                curve = self.generate_yang_curve(max_n)
            else:
                curve = self.generate_yin_curve(max_n)

            x, y, z = curve['x'], curve['y'], curve['z']

            # 漏斗
            t_f = np.linspace(0.5, 2 * max_n, 60)
            Xf, Yf, Zf = self.funnel_surface(t_f, n_theta=25)
            ax.plot_surface(Xf, Yf, Zf, alpha=0.08, color='red',
                            linewidth=0, antialiased=True)

            ax.plot(x, y, z, linewidth=1.5, color=color)

            # 标记（阳=半圈，阴=卢卡斯数列标记）
            if stype == 'yang':
                m = self.yang_markers(max_n)
                ax.scatter(m['x'], m['y'], m['z'], c='orange', s=20,
                          label='r=2^(-n) 标记')
            else:
                m = self.yin_lucas_markers(max_n)
                # 过滤 L(n)>0 的标记
                valid = m['L'] > 0
                ax.scatter(m['x'][valid], m['y'][valid], m['z'][valid],
                          c='lime', s=25, edgecolors='darkgreen',
                          linewidths=0.5, label='卢卡斯数列 r=1/L(n)')

            ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
            ax.set_title(f'{title}\nL={curve["length"]:.2f}', fontsize=12)
            ax.legend(fontsize=8, loc='upper left')

        plt.suptitle(f'PKS Yang-Yin Spiral Comparison (r={self.r_start}, n_max={max_n})',
                     fontsize=14)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig

    # ═══════════════════════════════════════════════════════════════════
    # 导出
    # ═══════════════════════════════════════════════════════════════════

    def export_dxf_bspline(self, curve_data: Dict = None,
                           save_path: str = 'egg_spiral_3d.dxf'):
        """导出为 DXF B 样条曲线"""
        try:
            import ezdxf
            from ezdxf.math import Vec3
        except ImportError:
            print("⚠️ 需要安装 ezdxf：pip install ezdxf")
            return None

        if curve_data is None:
            curve_data = self.generate_yang_curve()

        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        points_3d = [Vec3(x, y, z) for x, y, z in
                     zip(curve_data['x'], curve_data['y'], curve_data['z'])]

        if len(points_3d) >= 4:
            spline = msp.add_spline(points_3d)
            spline.dxf.degree = 3
            doc.saveas(save_path)
            print(f"  ✅ PKS 螺旋 DXF: {save_path}")
            return save_path
        else:
            print(f"  ⚠️ 点数不足 ({len(points_3d)})，至少需要 4 个点")
            return None

    def export_vtk(self, curve_data: Dict = None,
                   save_path: str = 'egg_spiral_3d.vtk'):
        """导出为 VTK 格式（Paraview/VisIt）"""
        if curve_data is None:
            curve_data = self.generate_yang_curve()

        x, y, z = curve_data['x'], curve_data['y'], curve_data['z']
        n = len(x)

        with open(save_path, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("PKS Egg Spiral (Yang/Yin)\n")
            f.write("ASCII\n")
            f.write("DATASET POLYDATA\n")
            f.write(f"POINTS {n} float\n")
            for i in range(n):
                f.write(f"{x[i]:.6f} {y[i]:.6f} {z[i]:.6f}\n")
            f.write(f"LINES 1 {n+1}\n")
            f.write(f"{n}")
            for i in range(n):
                f.write(f" {i}")
            f.write("\n")

        print(f"  ✅ PKS 螺旋 VTK: {save_path}")
        return save_path


# ════════════════════════════════════════════════════════════════════════
# Demo
# ════════════════════════════════════════════════════════════════════════

def demo():
    """演示 PKS 蛋形螺旋曲线生成"""
    print("=" * 60)
    print("PKS 太阳太阴螺旋 — 3D 蛋形曲线生成器")
    print("=" * 60)

    # ── 1. 交点几何验证 ──
    print("\n1. 交点几何 (A_n, B_n), r=1:")
    sp = PKSEggSpiral(r_start=1.0, max_n=14)
    for n in range(1, 6):
        ip = sp.intersection_points(n)
        print(f"   n={n}: A({ip['A'][0]:.4f}, {ip['A'][2]:.4f}) "
              f"B({ip['B'][0]:.4f}, {ip['B'][2]:.4f}) "
              f"L_n={ip['L_n']:.4f} ratio_n={ip['ratio_n']:.2f}")

    print("\n   交点几何 (A_n, B_n), r=2:")
    sp2 = PKSEggSpiral(r_start=2.0, max_n=14)
    for n in range(1, 6):
        ip = sp2.intersection_points(n)
        print(f"   n={n}: A({ip['A'][0]:.4f}, {ip['A'][2]:.4f}) "
              f"B({ip['B'][0]:.4f}, {ip['B'][2]:.4f}) "
              f"L_n={ip['L_n']:.4f} ratio_n={ip['ratio_n']:.2f}")

    # ── 2. 阳螺旋基础曲线 ──
    print("\n2. 阳螺旋 (太阳·白银比 2^n, r=1):")
    yang_curve = sp.generate_yang_curve(max_n=14)
    print(f"   点数={len(yang_curve['t'])}, 长度={yang_curve['length']:.2f}")
    print(f"   首点: ({yang_curve['x'][0]:.4f}, {yang_curve['y'][0]:.4f}, "
          f"{yang_curve['z'][0]:.4f})")
    print(f"   末点: ({yang_curve['x'][-1]:.4f}, {yang_curve['y'][-1]:.4f}, "
          f"{yang_curve['z'][-1]:.4f})")

    markers = sp.yang_markers(6)
    print("   阳螺旋半圈标记 (r=2^(-n)):")
    for i in range(len(markers['n'])):
        print(f"     n={int(markers['n'][i])}: r={markers['r'][i]:.6f}, "
              f"z={markers['z'][i]:.4f}")

    # ── 3. 阴螺旋基础曲线 + 卢卡斯数列验证 ──
    print("\n3. 阴螺旋 (太阴·卢卡斯数列 Φ^n, r=1):")
    yin_curve = sp.generate_yin_curve(max_n=14)
    print(f"   点数={len(yin_curve['t'])}, 长度={yin_curve['length']:.2f}")
    print(f"   首点: ({yin_curve['x'][0]:.4f}, {yin_curve['y'][0]:.4f}, "
          f"{yin_curve['z'][0]:.4f})")
    print(f"   末点: ({yin_curve['x'][-1]:.4f}, {yin_curve['y'][-1]:.4f}, "
          f"{yin_curve['z'][-1]:.4f})")

    lucas = lucas_sequence(10)
    print(f"   卢卡斯数列 (前11项): {lucas.tolist()}")
    print(f"   比值收敛: ", end="")
    for i in range(2, min(10, len(lucas))):
        ratio = lucas[i] / lucas[i-1]
        print(f"L{i}/L{i-1}={ratio:.4f} ", end="")
    print(f"\n   → {PHI_LARGE:.4f} (大黄金比 Φ={PHI_LARGE:.4f})")

    yin_m = sp.yin_lucas_markers(8)
    print("   卢卡斯半径标记 (r=1/L(n)):")
    for i in range(min(9, len(yin_m['n']))):
        if yin_m['L'][i] > 0:
            print(f"     n={int(yin_m['n'][i])}: L={int(yin_m['L'][i])}, "
                  f"r={yin_m['r'][i]:.6f}, z={yin_m['z'][i]:.4f}")
    print(f"   每转 r_n+1/r_n = {PHI:.4f} (小黄金比 φ)")

    # ── 4. 生成可视化 ──
    print("\n4. 生成 3D 可视化...")

    # 阳螺旋 3D + 漏斗
    fig, _ = sp.plot_3d(yang_curve, spiral_type='yang',
                        show_funnel=True, show_intersections=True,
                        save_path='egg_spiral_3d.png')
    print("   ✅ egg_spiral_3d.png (阳螺旋 + 漏斗 + 标记)")

    # 参数扫描（max_n = 4, 7, 10, 14）
    scan_n = [4, 7, 10, 14]
    fig, _ = sp.plot_scan(scan_n, spiral_type='yang',
                          save_path='egg_spiral_scan_k.png')
    print(f"   ✅ egg_spiral_scan_k.png (阳螺旋参数扫描 n={scan_n})")

    # 阳阴对比
    fig = sp.plot_yang_yin_comparison(max_n=14,
                                      save_path='egg_spiral_yang_yin.png')
    print("   ✅ egg_spiral_yang_yin.png (阳阴螺旋对比)")

    # r=2 对比
    sp2 = PKSEggSpiral(r_start=2.0, max_n=14)
    y2 = sp2.generate_yang_curve(14)
    fig, _ = sp2.plot_3d(y2, spiral_type='yang',
                         show_funnel=True, show_intersections=True,
                         save_path='egg_spiral_3d_r2.png')
    print("   ✅ egg_spiral_3d_r2.png (r=2 基准)")

    # ── 5. 导出 ──
    print("\n5. 导出...")
    try:
        sp.export_dxf_bspline(yang_curve, save_path='egg_spiral_3d.dxf')
    except Exception as e:
        print(f"   DXF: {e}")

    try:
        sp.export_vtk(yang_curve, save_path='egg_spiral_3d.vtk')
    except Exception as e:
        print(f"   VTK: {e}")

    print(f"\n✅ PKS 蛋形螺旋分析完成")
    print(f"   小黄金比 φ = {PHI:.6f}, 大黄金比 Φ = {PHI_LARGE:.4f}")
    print(f"   阳螺旋: 每转 r→r/2, z step = {LN2/LN_PHI:.4f} (白银比)")
    print(f"   阴螺旋: 每转 r→r·φ={PHI:.4f}, z step = {LN_PHI_LARGE/LN_PHI:.4f} (卢卡斯·黄金比)")
    print(f"   ln2/lnφ = {LN2/LN_PHI:.4f} (每圈 z 步长)")
    print(f"   修改 max_n 控制螺旋延伸深度")
    print(f"   修改 r_start (1 或 2) 切换基准方案")


if __name__ == '__main__':
    demo()
