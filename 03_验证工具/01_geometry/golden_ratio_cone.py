#!/usr/bin/env python
"""
golden_ratio_cone.py — 黄金比锥面几何与螺旋漏斗
==================================================
从 rhino 脚本"egg黄金比锥切面"系列提取的黄金比锥面几何模块。

数学背景:
  黄金比锥是舒伯格超双曲锥 xy=1 与黄金比例 φ 的融合。
  锥面沿 z 轴的对数螺旋结构由黄金比控制：
    z = ln(t) / ln(φ)    其中 φ = (√5 - 1)/2 ≈ 0.618

核心参数:
  k = 1 / (2π · ln φ)    — 锥面螺旋常数（负值）
  D = √(1 + k²)          — 锥面几何因子

隐式曲面方程:
  (1/n²) · e^{-(u/(πD) + 1/(πn))} - u²/D² = v²
  
红色轮廓线（双曲型/涡旋漏斗壁面）:
  x = 1/t, z = ln(t) / ln(φ)    — 来自超双曲锥 xy=1 的反比母线
  
PKS 太阳太阴螺旋:
  阳螺旋（白银比 2^n）: r = r_start·2^(-t/2π), z = t/(2π)·(ln2/lnφ)
  阴螺旋（黄金比 φ^n）: r = (2π·|sin(t)|)/t, z = ln(t)/ln(φ)

源: pks两张图公式 太阳太阴螺旋.docx, yang_yin_spiral.py
"""

import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, Optional, List, Dict
from scipy.optimize import fsolve


class GoldenRatioCone:
    """黄金比锥面几何计算器"""
    
    def __init__(self):
        self.phi = (np.sqrt(5) - 1) / 2
        self.ln_phi = np.log(self.phi)
        self.k = 1.0 / (2 * np.pi * self.ln_phi)
        self.D = np.sqrt(1 + self.k**2)
    
    def cone_profile(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        t_safe = np.maximum(t, 1e-10)
        x = 1.0 / t_safe
        z = np.log(t_safe) / self.ln_phi
        return x, z
    
    def implicit_surface(self, u: np.ndarray, n: float) -> np.ndarray:
        exp_arg = -(u / (np.pi * self.D) + 1.0 / (np.pi * n))
        return (1.0 / n**2) * np.exp(exp_arg) - (u / self.D)**2
    
    def solve_v(self, u: float, n: float) -> float:
        F_val = self.implicit_surface(np.array([u]), n)[0]
        if F_val < 0:
            return float('nan')
        return np.sqrt(F_val)
    
    def find_u_range(self, n: float, n_pts: int = 1000) -> Tuple[float, float, np.ndarray]:
        u_coarse = np.linspace(0, 5, n_pts)
        F_coarse = self.implicit_surface(u_coarse, n)
        sign_changes = np.where(np.diff(np.sign(F_coarse)))[0]
        if len(sign_changes) < 2:
            return (0.0, 0.0, np.array([]))
        u_low = u_coarse[sign_changes[0]]
        u_high = u_coarse[sign_changes[-1] + 1]
        u_fine = np.linspace(u_low, u_high, n_pts)
        return (u_low, u_high, u_fine)
    
    # ====================================================================
    # PKS 太阳太阴螺旋
    # ====================================================================
    
    def yang_spiral_2t(self, t_vals: np.ndarray, r_start: float = 1.0
                      ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """阳螺旋（白银比 2^n）: r=2^(-t/2π), z=t/(2π)·(ln2/lnφ)"""
        r = r_start * (2.0 ** (-t_vals / (2 * np.pi)))
        z = (t_vals / (2 * np.pi)) * (np.log(2) / self.ln_phi)
        x = r * np.cos(t_vals)
        y = r * np.sin(t_vals)
        return x, y, z
    
    def sun_funnel_profile(self, t: np.ndarray, r_start: float = 1.0
                           ) -> Tuple[np.ndarray, np.ndarray]:
        t_safe = np.maximum(t, 1e-10)
        x = r_start / t_safe
        z = np.log(t_safe) / self.ln_phi
        return x, z
    
    def log_spiral_3d(self, t_range: np.ndarray
                      ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        t_safe = np.maximum(t_range, 1e-6)
        r = 2.0 / t_safe
        x = -r * np.cos(t_safe / 2)
        y = -r * np.sin(t_safe / 2)
        z = (np.log(t_safe) - np.log(2)) / self.ln_phi
        return x, y, z


class ConeSpiral:
    """黄金比锥螺旋漏斗组合体"""
    
    def __init__(self, cone: Optional[GoldenRatioCone] = None):
        self.cone = cone or GoldenRatioCone()
    
    def funnel_profile(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return self.cone.cone_profile(t)
    
    def spiral_core(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.cone.log_spiral_3d(t)


class ConeSectionAnalyzer:
    """黄金比锥截面分析器"""
    
    def __init__(self, cone: Optional[GoldenRatioCone] = None):
        self.cone = cone or GoldenRatioCone()
    
    def elliptic_cross_section(self, z_level: float) -> dict:
        n = np.exp(z_level * self.cone.ln_phi)
        r = 1.0 / n
        a = r * self.cone.D
        b = r
        return {
            'a': a, 'b': b,
            'area': np.pi * a * b,
            'aspect_ratio': a / b,
            'n': n, 'r': r, 'z': z_level,
        }


# ════════════════════════════════════════════════════════════════════════
# 可视化
# ════════════════════════════════════════════════════════════════════════

def generate_all_images():
    """生成黄金比锥面全套可视化图像"""
    cone = GoldenRatioCone()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ── 图1: 黄金比锥壁面轮廓 + 阳螺旋 ──
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 阳螺旋 (n=14)
    t_yang = np.linspace(0, 28*np.pi, 2800)
    yx, yy, yz = cone.yang_spiral_2t(t_yang)
    ax.plot(yx, yy, yz, linewidth=1.5, color='dodgerblue',
            label='阳螺旋 (白银比 2^n)')
    
    # 壁面轮廓
    t_wall = np.linspace(0.5, 60, 200)
    wx, wz = cone.cone_profile(t_wall)
    ax.plot(wx, np.zeros_like(wx), wz, 'red', linewidth=1.5, alpha=0.6,
            label='漏斗母线 x=1/t')
    
    # 右侧镜像（负x用来参考）
    ax.plot(-wx, np.zeros_like(wx), wz, 'red', linewidth=0.8, alpha=0.3)
    
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('Golden Ratio Cone — Yang Spiral (Silver Ratio 2^n)',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.view_init(elev=25, azim=-60)
    
    # 等轴调整（参考 egg_3d_spiral.py 方法）
    all_coords = np.concatenate([yx, yy, yz])
    max_range = (all_coords.max() - all_coords.min()) * 0.55
    mid = all_coords.mean()
    ax.set_xlim(mid - max_range, mid + max_range)
    ax.set_ylim(mid - max_range, mid + max_range)
    ax.set_zlim(mid - max_range, mid + max_range)
    
    fname = os.path.join(output_dir, 'golden_cone_yang_spiral.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图2+3: 阳阴螺旋对比（引用 egg_3d_spiral.py 的 PKS 阳阴螺旋） ──
    fig = plt.figure(figsize=(16, 7))
    
    for idx, (stype, color, title) in enumerate([
        ('yang', 'dodgerblue', 'Yang Spiral (Silver Ratio 2^n)'),
        ('yang2', 'dodgerblue', 'Yang Spiral (Alt View)'),
    ]):
        ax = fig.add_subplot(1, 2, idx+1, projection='3d')
        
        t_v = np.linspace(0, 14*np.pi, 1400)
        sx, sy, sz = cone.yang_spiral_2t(t_v)
        
        ax.plot(sx, sy, sz, linewidth=1.5, color=color)
        ax.plot(wx[:100], np.zeros(100), wz[:100], 'red', linewidth=1, alpha=0.4)
        
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        if idx == 0:
            ax.view_init(elev=25, azim=-60)
        else:
            ax.view_init(elev=45, azim=30)
        
        # 等轴调整（参考 egg_3d_spiral.py 方法）
        all_coords = np.concatenate([sx, sy, sz])
        max_range = (all_coords.max() - all_coords.min()) * 0.55
        mid = all_coords.mean()
        ax.set_xlim(mid - max_range, mid + max_range)
        ax.set_ylim(mid - max_range, mid + max_range)
        ax.set_zlim(mid - max_range, mid + max_range)
    
    plt.suptitle('PKS Yang Spiral on Golden Ratio Cone',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    fname = os.path.join(output_dir, 'golden_cone_yang_yin_compare.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图4: 截面面积 vs z ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    analyzer = ConeSectionAnalyzer()
    
    z_vals = np.linspace(-5, 8, 50)
    areas = [analyzer.elliptic_cross_section(z)['area'] for z in z_vals]
    ratios = [analyzer.elliptic_cross_section(z)['aspect_ratio'] for z in z_vals]
    
    axes[0].semilogy(z_vals, areas, 'b-', linewidth=2)
    axes[0].set_xlabel('z (axial position)'); axes[0].set_ylabel('Cross-section Area')
    axes[0].set_title('Area vs Axial Position', fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(z_vals, ratios, 'r-', linewidth=2)
    axes[1].axhline(y=cone.D, color='gray', linestyle='--', alpha=0.5,
                    label=f'D={cone.D:.3f}')
    axes[1].set_xlabel('z (axial position)'); axes[1].set_ylabel('Aspect Ratio (a/b)')
    axes[1].set_title('Aspect Ratio vs Axial Position', fontweight='bold')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)
    
    fname = os.path.join(output_dir, 'golden_cone_section_analysis.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图5: 壁面曲率 ──
    fig, ax = plt.subplots(figsize=(12, 6))
    t_curve = np.logspace(-1, 1.5, 500)
    
    # 曲率分析
    t_safe = np.maximum(t_curve, 1e-10)
    xp = -1.0 / t_safe**2
    xpp = 2.0 / t_safe**3
    zp = 1.0 / (t_safe * cone.ln_phi)
    zpp = -1.0 / (t_safe**2 * cone.ln_phi)
    kappa = np.abs(xp * zpp - zp * xpp) / (xp**2 + zp**2)**1.5
    
    ax.loglog(t_curve, kappa, 'b-', linewidth=2)
    ax.set_xlabel('t (height parameter)'); ax.set_ylabel('Curvature kappa(t)')
    ax.set_title('Golden Ratio Cone — Wall Profile Curvature', fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 标记 t=1 和 t=φ
    for tx, label in [(1.0, 't=1'), (cone.phi, 't=φ')]:
        ki = np.interp(tx, t_curve, kappa)
        ax.axvline(x=tx, color='red', linestyle='--', alpha=0.4)
        ax.annotate(f'{label}\nκ={ki:.4f}', (tx, ki),
                    fontsize=9, xytext=(tx*2, ki*2),
                    arrowprops=dict(arrowstyle='->', color='gray'))
    
    fname = os.path.join(output_dir, 'golden_cone_curvature.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    print(f"\n  📁 所有图像已保存至: {output_dir}")


def demo():
    """控制台黄金比锥几何分析"""
    print("=" * 60)
    print("黄金比锥几何分析")
    print("=" * 60)
    
    cone = GoldenRatioCone()
    print(f"\n黄金比 φ = {cone.phi:.6f}")
    print(f"ln(φ) = {cone.ln_phi:.6f}（负值，对数螺旋向下）")
    print(f"螺旋常数 k = 1/(2π·ln(φ)) = {cone.k:.6f}")
    print(f"几何因子 D = √(1+k²) = {cone.D:.6f}")
    
    # 壁面轮廓
    t_test = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    wall_x, wall_z = cone.cone_profile(t_test)
    print(f"\n壁面轮廓采样:")
    print(f"  {'t':>6}  {'x':>8}  {'z':>10}")
    for i, t in enumerate(t_test):
        print(f"  {t:>6.2f}  {wall_x[i]:>8.4f}  {wall_z[i]:>10.4f}")
    
    # PKS 螺旋
    print("\n阳螺旋 (白银比 2^n):")
    t_sun = np.linspace(0, 6*np.pi, 7)
    sx, sy, sz = cone.yang_spiral_2t(t_sun)
    for i in range(7):
        print(f"  t={t_sun[i]:.2f}: x={sx[i]:.4f} y={sy[i]:.4f} z={sz[i]:.4f}")
    
    print("\n阴螺旋 (黄金比 sinc):")
    t_moon = np.linspace(np.pi, 6*np.pi, 7)
    mx, my, mz = cone.yin_spiral_sin(t_moon)
    for i in range(7):
        print(f"  t={t_moon[i]:.2f}: x={mx[i]:.4f} y={my[i]:.4f} z={mz[i]:.4f}")
    
    # 截面分析
    analyzer = ConeSectionAnalyzer()
    for z in [0, 1, 2, 5]:
        sec = analyzer.elliptic_cross_section(z)
        print(f"  z={z:>4}: n={sec['n']:.4f}, area={sec['area']:.4f}, "
              f"a/b={sec['aspect_ratio']:.4f}")
    
    print(f"\n✅ 黄金比锥几何分析完成")
    print(f"   运行 generate_all_images() 生成可视化图像")


if __name__ == '__main__':
    import os
    demo()
    generate_all_images()
