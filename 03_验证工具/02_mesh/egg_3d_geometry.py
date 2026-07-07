"""
egg_3d_geometry.py — Frenet-Serret标架 + Rodrigues旋转3D扫掠几何
===================================================================
从 rhino 脚本"蛋形模型.py"提取的3D几何生成框架。

数学基础:
  Frenet-Serret 标架:
    T(t) = γ'(t) / ||γ'(t)||          — 切向量
    N(t) = γ''(t) / ||γ''(t)||        — 法向量
    B(t) = T(t) × N(t)                — 副法向量
  
  Rodrigues 旋转公式:
    R(v, ψ) = I + sin(ψ)·K + (1-cos(ψ))·K²
    
    其中 K 是旋转轴 v 的叉乘矩阵:
        [0  -vz  vy]
    K = [vz  0  -vx]
        [-vy vx  0 ]

  蛋形螺旋曲线（舒伯格蛋形沿螺旋路径）:
    egg_value(t) = sqrt(1/(b - t·sin(α)/2)² - (t·cos(α)/2)²)
    x(t) = -(3+2cos(t))·sin(3dt)·egg_value(t)
    y(t) = -(3+2cos(t))·cos(3dt)·egg_value(t)
    z(t) = c·sin(t)

  扫掠曲面 C(t, θ):
    在 γ(t) 的 TNB 标架中嵌入截面曲线 s(θ)，
    用 Rodrigues 旋转调整截面朝向:
    C(t,θ) = γ(t) + R_T(ψ(t)) · [s_x(θ)·N(t) + s_y(θ)·B(t)]

应用:
  涡旋管3D网格生成（蛋形截面沿螺旋路径扫掠）
  涡旋发生器叶片建模
  涡轮机械流道几何

参考:
  - Rhino script: 蛋形模型.py
  - Frenet, "Sur les courbes à double courbure" (1847)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, Optional, Callable


# ========================================================================
# 第一部分：Frenet-Serret 标架
# ========================================================================

class FrenetSerretFrame:
    """Frenet-Serret 标架计算器
    
    对任意3D参数曲线 γ(t) = (x(t), y(t), z(t))，
    计算其局部正交标架 {T, N, B}。
    
    Frenet-Serret 公式:
        dT/ds = κ·N
        dN/ds = -κ·T + τ·B
        dB/ds = -τ·N
    
    其中 s 是弧长，κ 是曲率，τ 是挠率。
    """
    
    @staticmethod
    def tangent(x: np.ndarray, y: np.ndarray, z: np.ndarray, 
                t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算切向量 T(t) = γ'(t) / ||γ'(t)||
        
        使用中心差分数值微分:
            γ'(t) ≈ (γ(t+Δt) - γ(t-Δt)) / (2Δt)
        
        归一化:
            T = γ'(t) / |γ'(t)|
        """
        dt = t[1] - t[0] if len(t) > 1 else 0.01
        
        dx = np.gradient(x, dt)
        dy = np.gradient(y, dt)
        dz = np.gradient(z, dt)
        
        norm = np.sqrt(dx**2 + dy**2 + dz**2)
        norm = np.where(norm < 1e-12, 1, norm)
        
        return dx/norm, dy/norm, dz/norm
    
    @staticmethod
    def normal(x: np.ndarray, y: np.ndarray, z: np.ndarray,
               t: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算法向量 N(t) = γ''(t) / ||γ''(t)||
        
        法向量指向曲线弯曲的方向。
        对于平面曲线，N 指向曲线内侧（曲率中心方向）。
        对于空间曲线，N 是曲率向量方向。
        
        N 垂直于 T（由 Frenet 公式证明）。
        """
        dt = t[1] - t[0] if len(t) > 1 else 0.01
        
        d2x = np.gradient(np.gradient(x, dt), dt)
        d2y = np.gradient(np.gradient(y, dt), dt)
        d2z = np.gradient(np.gradient(z, dt), dt)
        
        norm = np.sqrt(d2x**2 + d2y**2 + d2z**2)
        norm = np.where(norm < 1e-12, 1, norm)
        
        return d2x/norm, d2y/norm, d2z/norm
    
    @staticmethod
    def binormal(tx: np.ndarray, ty: np.ndarray, tz: np.ndarray,
                 nx: np.ndarray, ny: np.ndarray, nz: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算副法向量 B(t) = T(t) × N(t)
        
        叉乘:
            B_x = T_y·N_z - T_z·N_y
            B_y = T_z·N_x - T_x·N_z
            B_z = T_x·N_y - T_y·N_x
        
        B 同时垂直于 T 和 N，构成右手系。
        """
        bx = ty * nz - tz * ny
        by = tz * nx - tx * nz
        bz = tx * ny - ty * nx
        return bx, by, bz
    
    @staticmethod
    def compute_frame(x: np.ndarray, y: np.ndarray, z: np.ndarray,
                      t: np.ndarray) -> dict:
        """计算完整 Frenet 标架
        
        返回:
            {'T': (Tx, Ty, Tz), 'N': (Nx, Ny, Nz), 'B': (Bx, By, Bz)}
        """
        tx, ty, tz = FrenetSerretFrame.tangent(x, y, z, t)
        nx, ny, nz = FrenetSerretFrame.normal(x, y, z, t)
        bx, by, bz = FrenetSerretFrame.binormal(tx, ty, tz, nx, ny, nz)
        
        return {
            'T': (tx, ty, tz), 'N': (nx, ny, nz), 'B': (bx, by, bz),
        }
    
    @staticmethod
    def curvature(x: np.ndarray, y: np.ndarray, z: np.ndarray,
                  t: np.ndarray) -> np.ndarray:
        """曲率 κ(t) = ||γ'(t) × γ''(t)|| / ||γ'(t)||³
        
        曲率衡量曲线"弯曲的程度"。
        对圆: κ = 1/r（常数）
        对直线: κ = 0
        对蛋形: 尖端 κ 大，钝端 κ 小
        """
        dt = t[1] - t[0] if len(t) > 1 else 0.01
        
        dx = np.gradient(x, dt)
        dy = np.gradient(y, dt)
        dz = np.gradient(z, dt)
        d2x = np.gradient(dx, dt)
        d2y = np.gradient(dy, dt)
        d2z = np.gradient(dz, dt)
        
        # 叉乘: γ' × γ''
        cross_norm = np.sqrt((dy*d2z - dz*d2y)**2 + (dz*d2x - dx*d2z)**2 + (dx*d2y - dy*d2x)**2)
        gamma_norm = np.sqrt(dx**2 + dy**2 + dz**2)
        gamma_norm = np.where(gamma_norm < 1e-12, 1, gamma_norm)
        
        return cross_norm / gamma_norm**3
    
    @staticmethod
    def torsion(x: np.ndarray, y: np.ndarray, z: np.ndarray,
                t: np.ndarray) -> np.ndarray:
        """挠率 τ(t) = (γ'×γ'')·γ''' / ||γ'×γ''||²
        
        挠率衡量曲线"偏离平面"的程度。
        平面曲线: τ = 0
        螺旋曲线: τ = 常数（不等于0）
        """
        dt = t[1] - t[0] if len(t) > 1 else 0.01
        
        dx = np.gradient(x, dt)
        dy = np.gradient(y, dt)
        dz = np.gradient(z, dt)
        d2x = np.gradient(dx, dt)
        d2y = np.gradient(dy, dt)
        d2z = np.gradient(dz, dt)
        d3x = np.gradient(d2x, dt)
        d3y = np.gradient(d2y, dt)
        d3z = np.gradient(d2z, dt)
        
        # 三重积: (γ' × γ'') · γ'''
        cross = np.array([dy*d2z - dz*d2y, dz*d2x - dx*d2z, dx*d2y - dy*d2x])
        triple = cross[0]*d3x + cross[1]*d3y + cross[2]*d3z
        
        # ||γ' × γ''||²
        cross_norm2 = cross[0]**2 + cross[1]**2 + cross[2]**2
        cross_norm2 = np.where(cross_norm2 < 1e-12, 1, cross_norm2)
        
        return triple / cross_norm2


# ========================================================================
# 第二部分：Rodrigues 旋转
# ========================================================================

class RodriguesRotator:
    """Rodrigues 旋转公式实现
    
    对任意单位向量 v 和旋转角度 ψ，
    Rodrigues 公式给出绕 v 旋转 ψ 的旋转矩阵:
    
        R(v, ψ) = I + sin(ψ)·K + (1-cos(ψ))·K²
    
    其中 K 是 v 的叉乘矩阵:
        K = [[0, -vz, vy],
             [vz, 0, -vx],
             [-vy, vx, 0]]
    
    这是3D旋转最简洁的表示方式，尤适合旋转轴变化的场景。
    """
    
    @staticmethod
    def rotation_matrix(v: np.ndarray, psi: float) -> np.ndarray:
        """绕任意单位向量 v 旋转 psi 的旋转矩阵
        
        公式推导:
            Rodrigues 公式源自对旋转的指数映射:
            R = e^{ψ·K} = I + ψ·K + ψ²·K²/2! + ...
            
            利用 K³ = -K（叉乘矩阵的性质），可封闭为:
            R = I + sin(ψ)·K + (1-cos(ψ))·K²
        """
        v = v / np.linalg.norm(v)
        vx, vy, vz = v
        
        # 叉乘矩阵 K
        K = np.array([
            [0, -vz, vy],
            [vz, 0, -vx],
            [-vy, vx, 0]
        ])
        
        I = np.eye(3)
        R = I + np.sin(psi) * K + (1 - np.cos(psi)) * K @ K
        return R
    
    @staticmethod
    def rotate_vector(v: np.ndarray, axis: np.ndarray, psi: float) -> np.ndarray:
        """将向量 v 绕轴 axis 旋转 psi 角度"""
        R = RodriguesRotator.rotation_matrix(axis, psi)
        return R @ v


# ========================================================================
# 第三部分：蛋形螺旋扫掠
# ========================================================================

class EggSpiralSweep:
    """蛋形螺旋扫掠曲面生成器
    
    将蛋形截面沿螺旋路径 γ(t) 扫掠，生成3D曲面。
    
    螺旋路径 γ(t) = (x(t), y(t), z(t)):
        egg_value(t) = √(1/(b - t·sin(α)/2)² - (t·cos(α)/2)²)
        x(t) = -(3+2cos(t))·sin(3dt)·egg_value(t)
        y(t) = -(3+2cos(t))·cos(3dt)·egg_value(t)
        z(t) = c·sin(t)
    
    扫掠曲面:
        C(t,θ) = γ(t) + R_T(ψ(t)) · [s_x(θ)·N(t) + s_y(θ)·B(t)]
    
    其中 s(θ) 是截面曲线，R_T 是绕 T 的 Rodrigues 旋转。
    
    应用:
        涡旋管3D几何、螺旋叶片、涡旋发生器
    """
    
    def __init__(self, b: float = 1.66, angle: float = 0.588, 
                 c: float = 4.2, d: float = 1):
        self.b = b       # 蛋形宽度参数
        self.angle = angle  # 蛋形截面倾角
        self.c = c       # z轴振幅
        self.d = d       # 螺旋频率
        self.sin_a = np.sin(angle)
        self.cos_a = np.cos(angle)
    
    def egg_value(self, t: np.ndarray) -> np.ndarray:
        """蛋形截面在 t 处的值
        
        egg_value(t) = √(1/(b - t·sin(α)/2)² - (t·cos(α)/2)²)
        
        这是舒伯格蛋形公式在螺旋路径上的局部值。
        当 t 在 [-π/2+ε, π-ε] 范围内取值时有效。
        """
        inner = 1.0 / (self.b - t * self.sin_a / 2)**2 - (t * self.cos_a / 2)**2
        return np.sqrt(np.maximum(inner, 0))
    
    def spiral_curve(self, t: np.ndarray) -> dict:
        """计算螺旋路径 γ(t)
        
        x(t) = -(3+2cos(t))·sin(3dt)·egg_value(t)
        y(t) = -(3+2cos(t))·cos(3dt)·egg_value(t)
        z(t) = c·sin(t)
        
        因子 (3+2cos(t)) 控制螺旋的径向包络。
        sin(3dt) / cos(3dt) 产生螺旋的旋转。
        egg_value(t) 嵌入蛋形截面。
        """
        envelope = 3 + 2 * np.cos(t)
        egg_val = self.egg_value(t)
        
        x = -envelope * np.sin(3 * self.d * t) * egg_val
        y = -envelope * np.cos(3 * self.d * t) * egg_val
        z = self.c * np.sin(t)
        
        return {'x': x, 'y': y, 'z': z, 'envelope': envelope, 'egg_val': egg_val}
    
    def sweep_surface(self, t_range: np.ndarray, theta_range: np.ndarray,
                      cross_section: Optional[Callable] = None) -> dict:
        """沿螺旋路径扫掠截面
        
        对每个 (t, θ):
            1. 计算 γ(t) 和 TNB 标架
            2. 在 N-B 平面中嵌入截面曲线
            3. 用 Rodrigues 旋转调整朝向
            4. C(t,θ) = γ(t) + R_T(ψ(t))·section
        
        返回:
            {'X': (n_t, n_theta), 'Y': ..., 'Z': ...} 3D网格
        """
        curve = self.spiral_curve(t_range)
        
        # 默认截面: 椭圆（由 theta 控制）
        if cross_section is None:
            def cross_section(theta, t_idx):
                return np.cos(theta), 0.5 * np.sin(theta)
        
        # 计算 TNB 标架
        x, y, z = curve['x'], curve['y'], curve['z']
        frame = FrenetSerretFrame.compute_frame(x, y, z, t_range)
        Tx, Ty, Tz = frame['T']
        Nx, Ny, Nz = frame['N']
        Bx, By, Bz = frame['B']
        
        n_t = len(t_range)
        n_theta = len(theta_range)
        
        X = np.zeros((n_t, n_theta))
        Y = np.zeros((n_t, n_theta))
        Z = np.zeros((n_t, n_theta))
        
        for i in range(n_t):
            T_vec = np.array([Tx[i], Ty[i], Tz[i]])
            N_vec = np.array([Nx[i], Ny[i], Nz[i]])
            B_vec = np.array([Bx[i], By[i], Bz[i]])
            
            # 旋转角度（随 t 线性增加）
            psi = t_range[i] - t_range[0]
            
            for j in range(n_theta):
                s_x, s_y = cross_section(theta_range[j], i)
                
                # 截面在 N-B 平面中
                section_vec = s_x * N_vec + s_y * B_vec
                
                # Rodrigues 旋转
                if abs(psi) > 1e-10:
                    rotated = RodriguesRotator.rotate_vector(section_vec, T_vec, psi)
                else:
                    rotated = section_vec
                
                X[i, j] = x[i] + rotated[0]
                Y[i, j] = y[i] + rotated[1]
                Z[i, j] = z[i] + rotated[2]
        
        return {'X': X, 'Y': Y, 'Z': Z}
    
    def radial_array(self, t_range: np.ndarray, theta_range: np.ndarray,
                     num_instances: int = 6) -> list:
        """生成螺旋的圆周阵列
        
        绕 z 轴旋转并复制 num_instances 个螺旋。
        每个相邻螺旋之间的角度差 = 2π / num_instances。
        
        这模拟了多涡旋系统中的涡旋排列（如万字符阵列）。
        """
        base_surf = self.sweep_surface(t_range, theta_range)
        surfaces = [base_surf]
        
        for n in range(1, num_instances):
            angle = n * 2 * np.pi / num_instances
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            X_rot = base_surf['X'] * cos_a - base_surf['Y'] * sin_a
            Y_rot = base_surf['X'] * sin_a + base_surf['Y'] * cos_a
            
            surfaces.append({'X': X_rot, 'Y': Y_rot, 'Z': base_surf['Z'].copy()})
        
        return surfaces


# ========================================================================
# 第四部分：蛋形截面生成器
# ========================================================================

class EggCrossSectionGenerator:
    """2D蛋形截面生成器
    
    从螺旋几何中提取蛋形截面，用于CFD网格的截面定义。
    """
    
    def __init__(self, b: float = 1.66, angle: float = 0.588):
        self.b = b
        self.angle = angle
    
    def profile(self, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """单个蛋形截面轮廓
        
        使用螺旋公式在 t 固定时的截面:
            r(t) = egg_value(t) = √(1/(b - t·sinα/2)² - (t·cosα/2)²)
            x(t) = r(t)·cos(t), y(t) = r(t)·sin(t)
        """
        inner = 1.0 / (self.b - t * np.sin(self.angle) / 2)**2 - (t * np.cos(self.angle) / 2)**2
        r = np.sqrt(np.maximum(inner, 0))
        return r * np.cos(t), r * np.sin(t)
    
    def twisted_profile(self, t: np.ndarray, twist_rate: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """扭转蛋形截面
        
        在截面轮廓上叠加扭转相位:
            θ(t) = t + twist_rate · z(t)
        
        模拟涡旋在轴向的旋转效应。
        """
        inner = 1.0 / (self.b - t * np.sin(self.angle) / 2)**2 - (t * np.cos(self.angle) / 2)**2
        r = np.sqrt(np.maximum(inner, 0))
        theta = t  # 扭转在这里简化为恒定相位
        return r * np.cos(theta), r * np.sin(theta)


def demo():
    """演示蛋形3D几何生成"""
    print("=" * 60)
    print("蛋形3D几何（Frenet-Serret框架 + Rodrigues旋转）")
    print("=" * 60)
    
    # Frenet标架演示
    t = np.linspace(0, 2*np.pi, 100)
    x = np.cos(t)
    y = np.sin(t)
    z = t * 0.2
    
    kappa = FrenetSerretFrame.curvature(x, y, z, t)
    tau = FrenetSerretFrame.torsion(x, y, z, t)
    
    print(f"\n螺旋曲线 (t∈[0,2π]):")
    print(f"  曲率 κ: 均值={kappa.mean():.4f}, 范围=[{kappa.min():.4f}, {kappa.max():.4f}]")
    print(f"  挠率 τ: 均值={tau.mean():.4f}, 范围=[{tau.min():.4f}, {tau.max():.4f}]")
    print(f"  （对均匀螺旋，κ和τ应为常数）")
    
    # Rodrigues旋转演示
    v = np.array([1, 0, 0])
    v_rot = RodriguesRotator.rotate_vector(v, np.array([0, 0, 1]), np.pi/2)
    print(f"\nRodrigues旋转: v=(1,0,0) 绕 z轴 转90° → ({v_rot[0]:.4f}, {v_rot[1]:.4f}, {v_rot[2]:.4f})")
    print(f"  （应为 (0,1,0)）")
    
    # EggSpiral演示
    spiral = EggSpiralSweep()
    t_test = np.linspace(-np.pi/2 + 0.1, np.pi - 0.1, 10)
    curve = spiral.spiral_curve(t_test)
    print(f"\n蛋形螺旋路径:")
    print(f"  t(x)范围: [{curve['x'].min():.4f}, {curve['x'].max():.4f}]")
    print(f"  z范围:    [{curve['z'].min():.4f}, {curve['z'].max():.4f}]")
    
    print(f"\n✅ 蛋形3D几何分析完成")


if __name__ == '__main__':
    demo()
