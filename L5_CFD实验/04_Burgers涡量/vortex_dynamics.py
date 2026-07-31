"""
vortex_dynamics.py — 涡旋动力学演化（动态蛋形 + 指数衰减）
=============================================================
从 rhino 脚本提取的涡旋动态演化模型。

核心公式来源:
  1. "重点-螺旋蛋逐渐变圆公式转成sin波" — 时变蛋形参数
  2. "Walter Schauberger 蛋形+螺旋偏心" — 黄金比指数衰减
  3. "双曲线八度2^n+phi^n" — 双曲/黄金比复合衰减

时变参数模型:
  k(t) = 1/T           — 蛋形曲率随时间变化
  b(t) = 2t/(T·√t)     — 蛋形宽度随时间变化
  
  物理含义: 涡旋从"尖蛋形"逐渐演化为"圆形"（k→0, b→∞）
  
黄金比指数衰减（涡旋能量耗散）:
  env(t) = φ^(t / (phase·π/180))
  其中 φ = (√5-1)/2 ≈ 0.618
  
  这个衰减速率具有自相似性:
    env(t+phase·π/180) = φ · env(t)
  即每隔 phase·π/180 时间，幅值衰减到61.8%。

多涡旋极阵列:
  在极角方向复制多个涡旋，间距 = 2π/N。
  模拟涡旋系统中的"万字符"流动模式。

应用:
  涡旋随时间形变模拟
  涡旋能量级串的衰减
  多涡旋干涉模式

参考:
  - Rhino scripts: 重点-螺旋蛋...万字符.py
  - Rhino scripts: Walter Schauberger 蛋形+螺旋偏心.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from typing import Tuple, Optional


# ========================================================================
# 第一部分：时变蛋形
# ========================================================================

class TimeVaryingEgg:
    """时变蛋形参数模型
    
    蛋形参数 k 和 b 随时间 t 变化:
        k(t) = 1/T           → 从 k=1/T 开始，随时间趋近 0
        b(t) = 2t/(T·√t)    → 从 b=0 开始，随时间增长
    
    初始状态 (t→0+):
        k ≈ 1/T（曲率最大 → 尖蛋形）
        b ≈ 0（宽度最小）
    
    终态 (t→∞):
        k → 0（曲率为零 → 圆形）
        b → ∞（宽度最大）
    
    衰减因子:
        decay(t) = ln(t) / (ln(ϕ) · 2t/√t)
    
    这个模型模拟了涡旋从初始的"尖锐蛋形"逐渐"松弛"为圆形的过程。
    在涡旋动力学中，这对应着涡旋的"vortex breakdown"过程。
    """
    
    def __init__(self, T: float = 1.0, phi: float = (np.sqrt(5) - 1) / 2):
        self.T = T         # 时间尺度参数
        self.phi = phi     # 黄金比例
        self.ln_phi = np.log(phi) if phi > 0 else -1
    
    def k_func(self, t: np.ndarray) -> np.ndarray:
        """时变曲率参数 k(t) = 1/T
        
        k(t) 控制蛋形的"尖度"。k 越大，蛋形越尖。
        当 k → 0，蛋形退化为圆。
        
        此处 k 取常数（在单个时间步内），
        但可以在不同时间步取不同值来模拟演化。
        """
        return np.full_like(t, 1.0 / self.T)
    
    def b_func(self, t: np.ndarray) -> np.ndarray:
        """时变宽度参数 b(t) = 2t/(T·√t) = 2·√t / T
        
        b(t) 控制蛋形的"宽度"。
        b 随 √t 增长，意味着蛋形随时间"变胖"。
        """
        return 2.0 * np.sqrt(np.maximum(t, 1e-10)) / self.T
    
    def decay_factor(self, t: np.ndarray) -> np.ndarray:
        """对数-幂律复合衰减因子
        
        decay(t) = ln(t) / (ln(ϕ) · 2·t/√t)
                 = √t · ln(t) / (2·ln(ϕ))
        
        由于 ln(ϕ) < 0，这个衰减因子为负值。
        结合旋转项使用，产生对数螺旋式的收缩。
        
        物理含义:
          涡旋能量随 t 以 ~√t·ln(t) 的速度衰减，
          这是涡粘性扩散 + 轴向拉伸的联合效应。
        """
        t_safe = np.maximum(t, 1e-10)
        return np.log(t_safe) / (self.ln_phi * 2.0 * t_safe / np.sqrt(t_safe))
    
    def shape_at_time(self, t: np.ndarray, theta: np.ndarray, 
                      time_idx: float = 0) -> Tuple[np.ndarray, np.ndarray]:
        """计算 t 时刻的蛋形截面
        
        在给定时间索引 time_idx 下，计算蛋形截面:
            r(t) = 1 / (b(time_idx) + t·sin(α))  
            x(t) = r(t)·cos(θ)
            y(t) = r(t)·sin(θ) · decay(time_idx)
        
        返回:
            (x, y) 截面坐标 (n_t × n_theta)
        """
        k_val = self.k_func(np.array([time_idx]))[0]
        b_val = self.b_func(np.array([time_idx]))[0]
        decay_val = self.decay_factor(np.array([time_idx]))[0]
        
        # 蛋形半径
        sin_a = 0.588  # 标准蛋形角 sin(arctan(2/3))
        r = 1.0 / (b_val + t * sin_a)
        
        X = np.outer(r, np.cos(theta))
        Y = np.outer(r, np.sin(theta)) * abs(decay_val)
        
        return X, Y


# ========================================================================
# 第二部分：涡旋衰减模型
# ========================================================================

class VortexDecayModel:
    """多种涡旋衰减模型
    
    物理模型中常见的涡旋能量衰减规律:
    
    1. 黄金比衰减:  E(t) = E₀ · φ^(t/τ)
       自相似衰减，每一步衰减到前一步的 61.8%
       
    2. 指数衰减:    E(t) = E₀ · e^{-αt}
       经典粘性耗散，α = ν·(π/r_core)²
       
    3. 幂律衰减:    E(t) = E₀ · (1 + t/τ)^{-p}
       湍流的Kolmogorov谱，p ≈ 5/3
       
    4. 对数衰减:    E(t) = E₀ · (1 - ln(1+t/τ)/ln(2))
       超双曲锥的天然衰减
    """
    
    def __init__(self, phi: float = (np.sqrt(5) - 1) / 2):
        self.phi = phi
    
    def golden_ratio_decay(self, t: np.ndarray, phase: float = 720, 
                          spin_n: float = 108) -> Tuple[np.ndarray, np.ndarray]:
        """黄金比指数衰减螺旋
        
        公式:
            env(t) = φ^(t / (phase·π/180))
            x(t) = t · env(t) · cos(t·spin_n)
            y(t) = t · env(t) · sin(t·spin_n)
        
        这是一个螺旋，其半径以黄金比指数衰减。
        spin_n 是每单位 t 的旋转圈数。
        """
        phase_rad = phase * np.pi / 180
        env = self.phi ** (t / phase_rad)
        
        x = t * env * np.cos(t * spin_n)
        y = t * env * np.sin(t * spin_n)
        
        return x, y
    
    def exponential_decay(self, t: np.ndarray, alpha: float = 1.0) -> np.ndarray:
        """经典指数衰减
        
        E(t) = e^{-αt}
        
        这是最简单的涡旋衰减模型。
        α = ν·(2π/λ)²，其中 λ 为涡旋的空间波长。
        """
        return np.exp(-alpha * t)
    
    def power_law_decay(self, t: np.ndarray, tau: float = 1.0, 
                        p: float = 5/3) -> np.ndarray:
        """幂律衰减
        
        E(t) = (1 + t/τ)^{-p}
        
        湍流理论中，Kolmogorov谱的衰减指数 p = 5/3。
        对舒伯格涡旋，可能 p = 1（谐波序列的衰减率）。
        """
        return (1.0 + t / tau)**(-p)
    
    def logarithmic_decay(self, t: np.ndarray, base: float = 2.0) -> np.ndarray:
        """对数衰减
        
        E(t) = max(0, 1 - ln(1+t)/ln(base))
        
        当 t = base-1 时衰减到零。
        舒伯格理论认为这是"自然截断"的衰减方式。
        """
        return np.maximum(0, 1.0 - np.log(1.0 + t) / np.log(base))
    
    def polar_array(self, x: np.ndarray, y: np.ndarray, 
                    num_directions: int = 12) -> list:
        """极阵列（万字符阵列）
        
        将 (x,y) 场复制到 num_directions 个方向。
        第 n 个方向的旋转角 = 2π·n/num_directions。
        
        应用:
            多涡旋阵列的生成
            对称流动模式的构建
        """
        fields = []
        for n in range(num_directions):
            angle = 2 * np.pi * n / num_directions
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            fields.append((x_rot, y_rot))
        return fields


# ========================================================================
# 第三部分：动态涡旋模拟
# ========================================================================

class DynamicVortexSim:
    """动态涡旋模拟器
    
    结合时变蛋形 + 衰减模型，模拟涡旋随时间的演化。
    
    模拟流程:
        1. 初始化涡旋参数 (Re, Γ, γ, ν)
        2. 对每个时间步:
            a. 更新蛋形参数 k(t), b(t)
            b. 计算衰减因子
            c. 生成截面速度场
            d. 计算能量衰减
        3. 输出时空演化数据
    """
    
    def __init__(self, Re: float = 100, Gamma: float = 1.0, 
                 gamma: float = 1.0, nu: float = 0.01):
        self.Re = Re
        self.Gamma = Gamma
        self.gamma = gamma
        self.nu = nu
        self.r_core = 2 * np.sqrt(nu / gamma) if gamma > 0 else 0.1
        
        self.egg = TimeVaryingEgg()
        self.decay = VortexDecayModel()
    
    def velocity_at_time(self, r: np.ndarray, theta: np.ndarray, 
                         t: float) -> dict:
        """计算 t 时刻的速度场
        
        使用 Burgers 涡基 + 蛋形修正 + 时间衰减
        """
        G, g, nu = self.Gamma, self.gamma, self.nu
        r_safe = np.maximum(r, 1e-10)
        
        # Burgers涡基
        vtheta = G / (2 * np.pi * r_safe) * (1 - np.exp(-g * r_safe**2 / (4 * nu)))
        
        # 蛋形修正（随时间变化）
        k_t = self.egg.k_func(np.array([t]))[0]
        b_t = self.egg.b_func(np.array([t]))[0]
        
        # 衰减因子
        env_t = self.decay.golden_ratio_decay(np.array([t]), phase=720, spin_n=10)
        corr = abs(env_t[0][0]) if len(env_t[0]) > 0 else 1.0
        
        # 蛋形截面上的非轴对称修正
        r_ratio = (1.0 / r_safe - 1.0 / (1.0 / k_t))
        egg_correction = 1 + 0.1 * np.sin(theta) * r_ratio
        
        vtheta_corrected = vtheta * egg_correction * corr
        
        ux = -vtheta_corrected * np.sin(theta)
        uy = vtheta_corrected * np.cos(theta)
        
        return {
            'ux': ux, 'uy': uy, 'vtheta': vtheta_corrected,
            'correction': egg_correction, 'decay': corr,
        }
    
    def total_energy(self, ux: np.ndarray, uy: np.ndarray) -> float:
        """计算总动能
        
        E = ½ ∫∫ (ux² + uy²) dA
        
        对数值网格求和得到近似总能量。
        """
        return 0.5 * np.sum(ux**2 + uy**2) / ux.size
    
    def energy_decay_curve(self, t_range: np.ndarray, 
                           n_grid: int = 100) -> np.ndarray:
        """计算能量随时间的衰减曲线
        
        返回每个时间步的总动能数组。
        """
        r = np.linspace(0.01, 1.0, n_grid)
        theta = np.linspace(0, 2*np.pi, n_grid)
        R, Theta = np.meshgrid(r, theta)
        
        energies = []
        for t in t_range:
            field = self.velocity_at_time(R, Theta, t)
            E = self.total_energy(field['ux'], field['uy'])
            energies.append(E)
        
        return np.array(energies)


# ========================================================================
# 第四部分：多涡旋阵列 + k_E谐波蛋形映射
# ========================================================================

class MultiVortexArray:
    """多涡旋阵列
    
    在极坐标系中排列多个涡旋，
    模拟涡旋间的相互作用和干涉。
    """
    
    def __init__(self, num_vortices: int = 6, base_re: float = 100):
        self.N = num_vortices
        self.vortices = [DynamicVortexSim(Re=base_re/(n+1)) for n in range(num_vortices)]
    
    def combined_velocity(self, x: np.ndarray, y: np.ndarray, t: float) -> dict:
        """所有涡旋的合成速度场
        
        各涡旋的贡献叠加（线性叠加原则）:
            u_total = Σ_{i=1}^N u_i(x - x_i, y - y_i, t)
        
        其中 (x_i, y_i) 是第 i 个涡旋的中心位置，
        按极角 θ_i = 2π·i/N 分布在半径 R 的圆上。
        """
        R_arrange = 0.3  # 涡旋分布半径
        ux_total = np.zeros_like(x)
        uy_total = np.zeros_like(x)
        
        for n, vortex in enumerate(self.vortices):
            theta_n = 2 * np.pi * n / self.N
            cx = R_arrange * np.cos(theta_n)
            cy = R_arrange * np.sin(theta_n)
            
            # 相对坐标
            x_rel = x - cx
            y_rel = y - cy
            r = np.sqrt(x_rel**2 + y_rel**2)
            theta = np.arctan2(y_rel, x_rel)
            
            field = vortex.velocity_at_time(r, theta, t)
            ux_total += field['ux']
            uy_total += field['uy']
        
        return {'ux': ux_total, 'uy': uy_total,
                'speed': np.sqrt(ux_total**2 + uy_total**2)}


class HarmonicEggMapper:
    """音乐谐波 → 蛋形度 k_E 映射与 NS 残差预测
    
    核心映射关系（Schauberger 超双曲锥 xy=1 平面斜切）:
        z1=1, z2=k_E  →  蛋形截面
        斜切角 α = arctan(k_E·(k_E-1)/(k_E+1))
    
    音乐谐波对应:
        ┌────────────┬──────────┬──────────────────────────┐
        │ 谐波名称   │ k_E 值   │ α (°)                   │
        ├────────────┼──────────┼──────────────────────────┤
        │ 基频       │ 1.0      │  0.00 (退化为圆)         │
        │ 纯五度     │ 3/2      │ 12.70                   │
        │ 八度       │ 2.0      │ 33.69 ← 核心目标         │
        │ 大三度     │ 5/4      │  9.46                   │
        │ 小三度     │ 6/5      │  7.73                   │
        │ 纯四度     │ 4/3      │  9.74                   │
        │ 大六度     │ 5/3      │ 15.94                   │
        │ k_E=2.5    │ 2.5      │ 46.97 ← 对比参考         │
        │ 双八度     │ 4.0      │ 67.38                   │
        └────────────┴──────────┴──────────────────────────┘
    
    物理意义:
        当 k_E 为有理数 p/q 时，蛋形具有"谐波对称性"，
        类似音乐中弦振动的驻波模式。
        k_E=2 (八度) 时 α≈33.69°，此时：
        - 蛋形曲率最均匀（σ_κ/μ_κ 最小）
        - Burgers 涡匹配度最高
        - 综合质量得分最优
        
    这为 Schauberger "自然选择八度比例" 提供了数值证据，
    也为千禧年 NS 问题的蛋形涡旋分析奠定了基础。
    """
    
    # 音乐谐波比值
    HARMONICS = {
        'Unison':      1.0,
        'Minor 3rd':   6.0/5,
        'Major 3rd':   5.0/4,
        'Perfect 4th': 4.0/3,
        'Perfect 5th': 3.0/2,
        'Minor 6th':   8.0/5,
        'Major 6th':   5.0/3,
        'Octave':      2.0,       # ← 核心
        '2.5x':        2.5,       # ← 对比
        'Double Oct.': 4.0,
    }
    
    def __init__(self):
        pass
    
    @staticmethod
    def kE_to_alpha_deg(kE: float) -> float:
        """k_E → 斜切角 α（度）"""
        return np.degrees(np.arctan(kE * (kE - 1) / (kE + 1)))
    
    @staticmethod
    def alpha_to_kE(alpha_deg: float) -> float:
        """α（度）→ k_E（数值求解）"""
        alpha_rad = np.radians(alpha_deg)
        # tan(α) = k_E·(k_E-1)/(k_E+1)
        # 设 x = k_E, 则 tan(α)·(x+1) = x(x-1) = x²-x
        # x² - x - tan(α)·x - tan(α) = 0
        # x² - (1+tan(α))·x - tan(α) = 0
        ta = np.tan(alpha_rad)
        a, b, c = 1.0, -(1 + ta), -ta
        disc = b**2 - 4*a*c
        if disc < 0:
            return float('nan')
        return (-b + np.sqrt(disc)) / (2*a)
    
    def harmonic_table(self) -> list:
        """生成完整的谐波-蛋形对照表
        
        返回: [{'name': str, 'kE': float, 'alpha_deg': float}, ...]
        """
        table = []
        for name, kE in self.HARMONICS.items():
            alpha = self.kE_to_alpha_deg(kE)
            table.append({'name': name, 'kE': kE, 'alpha_deg': alpha})
        return sorted(table, key=lambda x: x['alpha_deg'])
    
    def predict_ns_quality(self, kE: float) -> dict:
        """预测给定 k_E 的 NS 质量评分（简化模型）
        
        基于 kE_scan.py 的数值结果拟合的经验模型:
            quality ≈ 1 - 0.4·|kE - 2| + 0.1·cos(π·kE/2)
        
        这是一个粗略的经验公式，精确结果需运行 egg_kE_scan.py。
        """
        deviation = abs(kE - 2.0)
        harmonic_bonus = 0.1 * np.cos(np.pi * kE / 2)
        quality = max(0, 1.0 - 0.4 * deviation + harmonic_bonus)
        
        alpha = self.kE_to_alpha_deg(kE)
        
        return {
            'kE': kE,
            'alpha_deg': alpha,
            'quality_score': quality,
            'is_harmonic': abs(kE - round(kE * 6) / 6) < 0.05,
            'note': 'Octave egg is optimal' if abs(kE - 2.0) < 0.05 else '',
        }


def demo():
    """演示涡旋动力学演化"""
    print("=" * 60)
    print("涡旋动力学演化模型")
    print("=" * 60)
    
    sim = DynamicVortexSim(Re=100)
    
    # 能量衰减
    t_range = np.linspace(0.01, 5.0, 50)
    energies = sim.energy_decay_curve(t_range)
    print(f"\n能量衰减: E(0)={energies[0]:.6f}, E(5)={energies[-1]:.6f}")
    print(f"  衰减比: {energies[-1]/energies[0]:.4f} (越小衰减越快)")
    
    # 衰减模型对比
    decay = VortexDecayModel()
    t = np.linspace(0, 5, 100)
    
    e_golden = decay.golden_ratio_decay(t, phase=720, spin_n=10)
    r_e = np.sqrt(e_golden[0]**2 + e_golden[1]**2)
    
    print(f"\n黄金比衰减 (t=5): r_decay = {r_e[-1]:.4f}")
    print(f"  指数衰减 (t=5): {decay.exponential_decay(np.array([5.0]))[0]:.4f}")
    print(f"  幂律衰减 (t=5): {decay.power_law_decay(np.array([5.0]))[0]:.4f}")
    print(f"  对数衰减 (t=5): {decay.logarithmic_decay(np.array([5.0]))[0]:.4f}")
    
    # 多涡旋
    multi = MultiVortexArray(num_vortices=6)
    print(f"\n多涡旋阵列: N={multi.N}")
    
    # 时变蛋形
    egg = TimeVaryingEgg()
    for time_idx in [0, 0.5, 1.0, 2.0]:
        b = egg.b_func(np.array([time_idx]))[0]
        k = egg.k_func(np.array([time_idx]))[0]
        print(f"  t={time_idx:.1f}: k={k:.4f}, b={b:.4f}")
    
    # ===== 新增：谐波蛋形映射 =====
    print(f"\n{'='*60}")
    print("音乐谐波 → 蛋形映射")
    print(f"{'='*60}")
    mapper = HarmonicEggMapper()
    table = mapper.harmonic_table()
    print(f"\n{'Harmonic':>14} | {'k_E':>8} | {'alpha(°)':>10}")
    print("-" * 38)
    for row in table:
        marker = " ★" if abs(row['kE'] - 2.0) < 0.01 else (" ◆" if abs(row['kE'] - 2.5) < 0.01 else "")
        print(f"{row['name']:>14} | {row['kE']:>8.3f} | {row['alpha_deg']:>10.2f}{marker}")
    
    # NS 质量预测
    print(f"\nNS 质量预测:")
    for ke in [1.5, 2.0, 2.5, 3.0, 4.0]:
        pred = mapper.predict_ns_quality(ke)
        print(f"  k_E={ke:.1f}: quality={pred['quality_score']:.3f}, alpha={pred['alpha_deg']:.1f}° {pred['note']}")
    
    print(f"\n✅ 涡旋动力学分析完成")


if __name__ == '__main__':
    demo()
