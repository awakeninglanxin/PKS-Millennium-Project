#!/usr/bin/env python
"""
funnel_surface.py — 漏斗旋转曲面与切面交线几何
================================================
从舒伯格黄金比锥的红色母线旋转生成漏斗曲面，
并计算切线平面与曲面的交线。

数学背景:
  红色母线: x = 1/t, z = ln(t)/ln(φ)   (来自超双曲锥 xy=1)
  旋转曲面: r(t) = r_start/t, z = ln(t)/ln(φ)
  
  PKS 切线: z = k·x + b_n, k = 1/(2π·ln(φ))
  切面与漏斗曲面相交 → 2D 边缘曲线

源:
  - pks两张图公式 太阳太阴螺旋.docx
  - yang_yin_spiral.py (交点几何)
  - egg黄金比锥切面系列
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '01_geometry'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, Optional, List, Dict
from scipy.optimize import fsolve


# ════════════════════════════════════════════════════════════════════════
# PKS 公共常数
# ════════════════════════════════════════════════════════════════════════
PHI = (np.sqrt(5) - 1) / 2
LN_PHI = np.log(PHI)
LN2 = np.log(2)
K_SPIRAL = 1.0 / (2 * np.pi * LN_PHI)


class FunnelSurface:
    """黄金比锥漏斗旋转曲面"""
    
    def __init__(self, r_start: float = 1.0):
        self.phi = PHI
        self.ln_phi = LN_PHI
        self.r_start = r_start
    
    def generatrix(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        t_safe = np.maximum(t, 1e-10)
        r = self.r_start / t_safe
        z = np.log(t_safe) / self.ln_phi
        return r, z
    
    def revolve(self, t: np.ndarray, n_theta: int = 72
                ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        r_vals, z_vals = self.generatrix(t)
        theta = np.linspace(0, 2 * np.pi, n_theta)
        TH, R = np.meshgrid(theta, r_vals)
        Z = np.tile(z_vals, (n_theta, 1)).T
        X = R * np.cos(TH)
        Y = R * np.sin(TH)
        return X, Y, Z
    
    def tangent_plane_intersection(self, n: int, r_start: float = 1.0,
                                    n_points: int = 200) -> Dict:
        from yang_yin_spiral import IntersectionGeometry
        geo = IntersectionGeometry()
        b_n = geo.find_b_n(n, r_start)
        k = K_SPIRAL
        
        theta_vals = np.linspace(0, 2 * np.pi, n_points)
        X_local, Y_local = [], []
        X_global, Y_global, Z_global = [], [], []
        
        for theta in theta_vals:
            def f(t):
                r = r_start / max(t, 1e-10)
                lhs = np.log(max(t, 1e-10)) / self.ln_phi
                rhs = k * r * np.cos(theta) + b_n
                return lhs - rhs
            
            t_guess = np.exp(b_n * self.ln_phi)
            solved = False
            for scale in [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0]:
                try:
                    t_sol = fsolve(f, t_guess * scale, xtol=1e-10, maxfev=200)[0]
                    if 0.01 < t_sol < 1000:
                        solved = True; break
                except Exception:
                    continue
            if not solved:
                continue
            
            r_val = r_start / t_sol
            x_g = r_val * np.cos(theta)
            y_g = r_val * np.sin(theta)
            z_g = np.log(t_sol) / self.ln_phi
            
            X_local.append(x_g)
            Y_local.append(y_g)
            X_global.append(x_g)
            Y_global.append(y_g)
            Z_global.append(z_g)
        
        return {
            'theta': np.array(theta_vals[:len(X_local)]),
            'X_local': np.array(X_local), 'Y_local': np.array(Y_local),
            'X_global': np.array(X_global), 'Y_global': np.array(Y_global),
            'Z_global': np.array(Z_global),
            'b_n': b_n, 'k': k,
        }
    
    def egg_golden_funnel(self, t_range: Tuple[float, float] = (-np.pi/3, 2*np.pi/3),
                          steps: int = 660) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        b = (1 + np.sqrt(5)) / 2
        a_deg = 100.0 / 3
        a_rad = a_deg * np.pi / 180
        d = 216
        t_min, t_max = t_range
        t_vals = np.linspace(t_min, t_max, steps)
        denom = 1.0 / (b - t_vals * np.sin(a_rad))**2 - (t_vals * np.cos(a_rad))**2
        valid = denom >= 0
        t_v = t_vals[valid]; d_v = np.sqrt(denom[valid])
        x = np.sin(d * t_v) * d_v
        y = np.cos(d * t_v) * d_v
        z = t_v
        return x, y, z


# ════════════════════════════════════════════════════════════════════════
# 可视化
# ════════════════════════════════════════════════════════════════════════

def generate_all_images():
    """生成漏斗曲面全套可视化"""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    funnel = FunnelSurface(r_start=1.0)
    
    # ── 图1: 漏斗旋转曲面 (3D 线框) ──
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    t_wall = np.linspace(0.5, 30, 60)
    theta_wire = np.linspace(0, 2*np.pi, 24)
    
    # 经线 (constant theta)
    for th in theta_wire:
        r, z = funnel.generatrix(t_wall)
        x_r = r * np.cos(th)
        y_r = r * np.sin(th)
        ax.plot(x_r, y_r, z, color='red', linewidth=0.5, alpha=0.4)
    
    # 纬线 (constant t)
    for ti in np.linspace(1, 28, 8):
        t_val = ti
        r_ring, z_ring = funnel.generatrix(np.array([t_val]))
        theta_ring = np.linspace(0, 2*np.pi, 72)
        x_ring = r_ring[0] * np.cos(theta_ring)
        y_ring = r_ring[0] * np.sin(theta_ring)
        ax.plot(x_ring, y_ring, [z_ring[0]]*72, 'gray', linewidth=0.5, alpha=0.5)
    
    # 母线 (正侧)
    rx, rz = funnel.generatrix(t_wall)
    ax.plot(rx, np.zeros_like(rx), rz, 'red', linewidth=2, label='母线 x=1/t')
    
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('Golden Ratio Funnel Surface (Revolution of x=1/t)',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.view_init(elev=20, azim=-50)
    
    fname = os.path.join(output_dir, 'funnel_surface_wireframe.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图2: 交点 A_n, B_n + 切线 (r=1) ──
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    from yang_yin_spiral import IntersectionGeometry
    geo = IntersectionGeometry()
    
    # 母线
    t_prof = np.linspace(0.5, 20, 300)
    fx, _, fz = funnel.funnel_profile_3d(t_prof) if hasattr(funnel, 'funnel_profile_3d') else (None, None, None)
    
    if fx is None:
        rx_full, rz_full = funnel.generatrix(t_prof)
        ax.plot(rx_full, np.zeros_like(rx_full), rz_full, 'red', linewidth=1.2, alpha=0.6)
        ax.plot(-rx_full, np.zeros_like(rx_full), rz_full, 'red', linewidth=0.5, alpha=0.3)
    
    # A_n, B_n 标记
    for n in range(1, 7):
        ip = geo.intersection_point(n, 'A')
        ip_b = geo.intersection_point(n, 'B')
        
        ax.scatter(*ip, c='blue', s=50, edgecolors='darkblue', linewidths=0.5)
        ax.scatter(*ip_b, c='darkgreen', s=50, edgecolors='darkgreen', linewidths=0.5)
        
        if n <= 3:
            ax.text(ip[0], ip[1], ip[2]+0.2, f'A{n}', fontsize=9, color='blue')
            ax.text(ip_b[0], ip_b[1], ip_b[2]+0.2, f'B{n}', fontsize=9, color='darkgreen')
    
    # 蓝色切线 (n=1,3,5)
    for n in [1, 3, 5]:
        b_n = geo.find_b_n(n)
        x_line = np.linspace(-1, 1, 100)
        z_line = K_SPIRAL * x_line + b_n
        ax.plot(x_line, np.zeros_like(x_line), z_line, '--', color='cyan',
                linewidth=0.8, alpha=0.7, label=f'切线 n={n}' if n==1 else '')
    
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('Funnel Intersection Points A_n, B_n (r=1)',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left')
    
    fname = os.path.join(output_dir, 'funnel_intersection_points.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图3: 切线平面交线 (n=1,3,5 的局部2D曲线) ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    colors = ['blue', 'orange', 'purple']
    
    for idx, n in enumerate([1, 3, 5]):
        inter = funnel.tangent_plane_intersection(n=n, n_points=100)
        
        if len(inter['X_local']) > 0:
            axes[idx].plot(inter['X_local'], inter['Y_local'], 
                          color=colors[idx], linewidth=1.5)
            axes[idx].scatter([0], [0], color='red', s=50, marker='+', 
                             linewidths=2, label=f'(0,0,b_n)')
            
            axes[idx].set_xlabel('X local'); axes[idx].set_ylabel('Y local')
            axes[idx].set_title(f'n={n}, b_n={inter["b_n"]:.3f}', fontweight='bold')
            axes[idx].set_aspect('equal')
            axes[idx].legend(fontsize=8)
            axes[idx].grid(True, alpha=0.3)
    
    plt.suptitle('Tangent Plane Intersection Curves (Local 2D)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    fname = os.path.join(output_dir, 'funnel_tangent_intersections.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图4: 蛋黄金比螺旋漏斗 ──
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    ex, ey, ez = funnel.egg_golden_funnel(steps=1000)
    ax.plot(ex, ey, ez, linewidth=1, color='goldenrod', alpha=0.9,
            label='Egg Golden Spiral Funnel')
    
    # 投影虚线
    ax.plot(ex, ey, np.full_like(ex, ez.min()), color='goldenrod', 
            linewidth=0.3, alpha=0.2)
    
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('Egg Golden Ratio Spiral Funnel (Rhino叉积公式)',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    
    fname = os.path.join(output_dir, 'funnel_egg_golden_spiral.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    # ── 图5: r=1 vs r=2 漏斗对比 ──
    fig = plt.figure(figsize=(16, 7))
    
    for idx, r_start in enumerate([1.0, 2.0]):
        ax = fig.add_subplot(1, 2, idx+1, projection='3d')
        f = FunnelSurface(r_start=r_start)
        
        t_w = np.linspace(0.5, 20, 40)
        for th in np.linspace(0, 2*np.pi, 12):
            r, z = f.generatrix(t_w)
            x_r = r * np.cos(th); y_r = r * np.sin(th)
            ax.plot(x_r, y_r, z, color='red', linewidth=0.4, alpha=0.3)
        
        rx_f, rz_f = f.generatrix(t_w)
        ax.plot(rx_f, np.zeros_like(rx_f), rz_f, 'red', linewidth=1.8, label='母线')
        
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.set_title(f'Funnel r={r_start}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=8)
    
    plt.suptitle('PKS Funnel Comparison: r=1 vs r=2',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    fname = os.path.join(output_dir, 'funnel_r1_r2_comparison.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight'); plt.close()
    print(f"  ✅ {fname}")
    
    print(f"\n  📁 所有图像已保存至: {output_dir}")


def demo():
    """控制台漏斗曲面几何分析"""
    print("=" * 60)
    print("漏斗曲面几何分析")
    print("=" * 60)
    
    funnel = FunnelSurface(r_start=1.0)
    
    t_test = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    r_vals, z_vals = funnel.generatrix(t_test)
    print("\n漏斗母线:")
    for i, t in enumerate(t_test):
        print(f"  t={t:.1f}: r={r_vals[i]:.4f}, z={z_vals[i]:.4f}")
    
    ex, ey, ez = funnel.egg_golden_funnel()
    print(f"\n蛋黄金比螺旋漏斗: 点数={len(ex)}")
    print(f"  x范围: [{ex.min():.4f}, {ex.max():.4f}]")
    
    from yang_yin_spiral import IntersectionGeometry
    geo = IntersectionGeometry()
    print(f"\n交点几何 (r=1):")
    for n in range(1, 6):
        ip = geo.intersection_point(n, 'A')
        ip_b = geo.intersection_point(n, 'B')
        L_n = np.sqrt((ip_b[0]-ip[0])**2 + (ip_b[2]-ip[2])**2)
        print(f"  n={n}: A({ip[0]:.4f}, {ip[2]:.4f}) "
              f"B({ip_b[0]:.4f}, {ip_b[2]:.4f}) L_n={L_n:.4f}")
    
    print(f"\n✅ 漏斗曲面几何分析完成")


if __name__ == '__main__':
    demo()
    generate_all_images()
