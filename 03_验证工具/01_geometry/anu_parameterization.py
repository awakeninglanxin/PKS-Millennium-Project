"""
anu_parameterization.py — Anu 七级螺旋蛋形环的精确参数化
=========================================================
基于神秘化学 (Leadbeater & Besant, 1895-1933) 的原始描述，
结合 二阶魔方组合数 8!/24 = 1680 与 Schauberger 双曲锥蛋形几何。

理论基础:
----------
1. 神秘化学原文:
   - 每根导线有 1,680 个第一级螺旋体 (线圈)
   - 7 级嵌套: 每个 a → 7 个 b → 7 个 c → ... → 7 个气泡
   - 7 根细彩色导线 (完美 7:1 比例) + 3 根粗导线 (704:100 偏差)
   - 正极 Anu: 逆时针缠绕; 负极 Anu: 顺时针缠绕 (镜像)

2. 二阶魔方组合数:
   8! / 24 = 40320 / 24 = 1680
   (8 个角块的位置排列 / 立方体 24 种旋转对称)

3. Schauberger 超双曲锥斜切:
   xy=1 → 旋转锥面 → 平面斜截 → 蛋形截面

4. 幻方真理表:
   1680 = 2⁴ × 3 × 5 × 7 → 1680 × 7ⁿ 七级序列

作者: [老师] | 2026-05-26
"""

import math
import numpy as np
from typing import Tuple, Optional, List, Dict, Callable
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D


# ========================================================================
# 第一部分：物理常数与层级参数
# ========================================================================

# --- 神秘化学基本常数 ---
N_WIRES_TOTAL = 10          # 总导线数 (7细+3粗)
N_WIRES_THIN = 7            # 细导线 (彩色)
N_WIRES_THICK = 3           # 粗导线
N_COILS_PER_WIRE = 1680     # 每根导线的第一级螺旋体数 (8!/24)
N_SPIRAL_LEVELS = 7         # 螺旋嵌套级数 (a→b→c→d→e→f→g, 共7级)
N_SUBSPIRALS = 7            # 每级包含的次一级螺旋体数
BUBBLES_PER_G = 7           # g 级 (最低级螺旋体) 内含 7 个气泡

# --- 层级半径缩放 ---
R_LEVEL_0 = 0.001           # 气泡半径 (最小单位, 归一化)
R_SCALE_FACTOR = 1.0/7.0    # 每级半径缩小 7 倍

# --- 细导线 vs 粗导线 ---
# 细导线 (7根彩色): 完美 7:1 比例，700 气泡
# 粗导线 (3根): 704:100 比例，704 气泡
RATIO_THIN = 7.0            # 细导线比例
RATIO_THICK = 7.04          # 粗导线比例 (704:100 = 7.04:1)
CORRECTION_THICK = 704.0/700.0  # 粗导线修正因子 ≈ 1.005714

# --- 物理层级 ---
# E1 = 单个 Anu → 第一以太平面
# E2 = ≤7 个 Anu 的组合 → 第二以太平面
# E3 = 更复杂组合 → 第三以太平面
# E4 = 最复杂组合 → 第四以太平面 (物质原子)

# --- 数学常数 ---
PHI = (np.sqrt(5) - 1) / 2  # 黄金比 ϕ ≈ 0.618034
LN_PHI = np.log(PHI)        # ln(ϕ) ≈ -0.4812

# ========================================================================
# 第二部分：NestedSpiral — 七级嵌套螺旋生成器
# ========================================================================

class NestedSpiral:
    """七级嵌套螺旋生成器
    
    生成 Anu 导线中的 7 级螺旋结构。
    每级螺旋的轴线垂直于上一级的切线方向。
    频率比 = 1 : 7 : 7² : 7³ : 7⁴ : 7⁵ : 7⁶ (共 7 级, a→g)
    半径比 = 1 : 1/7 : 1/7² : ... : 1/7⁶
    
    参数化方法:
        x(t) = Σ_{k=0}^{6} R_k · f_k(t)
    其中 f_k(t) 是第 k 级螺旋的调制基函数,
    R_k = R_0 · (1/7)^k,
    t ∈ [0, 1680 · 2π] 覆盖全部 1680 个第一级螺旋。
    """
    
    def __init__(self, radius_0: float = 1.0, 
                 ratio: float = RATIO_THIN,
                 winding: int = 1,
                 n_levels: int = N_SPIRAL_LEVELS):
        """
        参数:
            radius_0: 最外层 (第一级) 螺旋半径
            ratio:     每级次一级数量 (细=7, 粗=7.04)
            winding:   缠绕方向 (+1=逆时针/正极, -1=顺时针/负极)
            n_levels:  嵌套级数 (默认 7)
        """
        self.R0 = radius_0
        self.ratio = ratio
        self.winding = winding
        self.n_levels = n_levels
        
        # 预计算每级半径
        self.radii = np.array([
            radius_0 * (1.0 / ratio) ** k
            for k in range(n_levels)
        ])
        
        # 预计算频率 (各方向分量用不同相位)
        # 每级含有 ratio^k 个次级螺旋
        self.freqs = np.array([
            ratio ** k
            for k in range(n_levels)
        ])
    
    def position_at(self, theta: np.ndarray) -> np.ndarray:
        """计算在参数 theta 处的 3D 位置
        
        使用 3 个正交方向交替调制，
        模拟"轴线垂直于上一级"的几何特性。
        
        参数:
            theta: 参数值数组 (形状: [N]), 
                   范围 [0, N_COILS_PER_WIRE * 2π]
                   
        返回:
            pos: 3D 坐标数组 (形状: [N, 3])
        """
        theta = np.asarray(theta, dtype=float)
        N = len(theta)
        pos = np.zeros((N, 3))
        
        # 各方向分量
        # 第 k 级: 在方向 (k % 3) 和 ((k+1) % 3) 上振荡
        # 相位 = winding · freq_k · theta + phase_shift_k
        
        for k in range(self.n_levels):
            r = self.radii[k]
            w = self.winding * self.freqs[k]
            
            # 交替的方向组合
            if k % 3 == 0:
                pos[:, 0] += r * np.cos(w * theta)
                pos[:, 1] += r * np.sin(w * theta)
            elif k % 3 == 1:
                pos[:, 1] += r * np.cos(w * theta)
                pos[:, 2] += r * np.sin(w * theta)
            else:
                pos[:, 2] += r * np.cos(w * theta)
                pos[:, 0] += r * np.sin(w * theta)
        
        return pos
    
    def tangent_at(self, theta: np.ndarray) -> np.ndarray:
        """计算在参数 theta 处的切线方向
        
        对 position_at 的数值微分。
        """
        theta = np.asarray(theta, dtype=float)
        N = len(theta)
        dt = 1e-6
        
        pos_p = self.position_at(theta + dt)
        pos_m = self.position_at(theta - dt)
        
        # 归一化
        tang = (pos_p - pos_m) / (2 * dt)
        norms = np.linalg.norm(tang, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return tang / norms
    
    def frenet_frame_at(self, theta: np.ndarray) -> Dict[str, np.ndarray]:
        """计算在参数 theta 处的 Frenet 标架
        
        返回:
            {'T': 切线, 'N': 法线, 'B': 副法线}
            每个形状为 [N, 3]
        """
        T = self.tangent_at(theta)
        
        # 求二阶导数得到法线方向
        dt = 1e-6
        T_p = self.tangent_at(theta + dt)
        dT = T_p - T
        N = dT / (np.linalg.norm(dT, axis=1, keepdims=True) + 1e-10)
        
        # 副法线 = T × N
        B = np.cross(T, N)
        B = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-10)
        
        return {'T': T, 'N': N, 'B': B}


# ========================================================================
# 第三部分：AnuWire — 单根导线的完整构造
# ========================================================================

class AnuWire:
    """单根 Anu 导线
    
    包含:
    - 1,680 个第一级螺旋体 (Level 7 / a)
    - 每个 a 含 7 个 b, 每个 b 含 7 个 c, ... 直到 7 个气泡
    - 整体包裹在蛋形包络中
    """
    
    def __init__(self, 
                 is_thin: bool = True,
                 winding: int = 1,
                 egg_params: Optional[Dict] = None,
                 n_spirals: int = N_COILS_PER_WIRE):
        """
        参数:
            is_thin:    True=细导线(7:1), False=粗导线(7.04:1)
            winding:    +1=逆时针(正极), -1=顺时针(负极)
            egg_params: 蛋形包络参数 {z1, z2} 等
            n_spirals:  第一级螺旋体数 (默认 1680)
        """
        self.is_thin = is_thin
        self.winding = winding
        self.n_spirals = n_spirals
        
        ratio = RATIO_THIN if is_thin else RATIO_THICK
        self.nested = NestedSpiral(
            radius_0=1.0, 
            ratio=ratio,
            winding=winding
        )
        
        # 蛋形包络参数
        if egg_params is None:
            # 默认: k_E = 2.0 (八度蛋)
            egg_params = {'z1': 1.0, 'z2': 2.0}
        self.egg = egg_params
    
    def wire_path(self, n_pts: int = 16800) -> np.ndarray:
        """生成沿导线主轴的 3D 路径
        
        参数:
            n_pts: 采样点数 (建议 16800 = 1680×10)
            
        返回:
            path: 形状 [n_pts, 3] 的坐标
        """
        # 参数范围: [0, n_spirals * 2π]
        theta = np.linspace(0, self.n_spirals * 2 * np.pi, n_pts)
        
        # 七级嵌套螺旋位置
        pos = self.nested.position_at(theta)
        
        # 应用蛋形包络调制
        # 蛋形包络在 z 方向渐变:
        # 尖端 (z=0) → 最细, 钝端 (z=最大) → 最粗
        z_max = self.n_spirals * 0.05  # 归一化长度
        z = theta / (self.n_spirals * 2 * np.pi) * z_max
        
        # 蛋形半径调制函数
        t_norm = z / z_max  # 0 → 1
        r_envelope = self._egg_envelope(t_norm)
        
        # 应用包络
        for i in range(3):
            pos[:, i] *= r_envelope
        
        # 沿着 z 方向拉伸
        pos[:, 2] += z
        
        return pos, theta
    
    def _egg_envelope(self, t: np.ndarray) -> np.ndarray:
        """蛋形包络: 沿导线长度方向的半径调制
        
        使用 Schauberger 蛋形公式:
        在尖端 (t=0) 半径最小, 
        向钝端 (t=1) 半径渐增。
        
        参数:
            t: 归一化位置 [0, 1]
            
        返回:
            调制因子 [0, 1] → 范围 [r_min, r_max]
        """
        t = np.asarray(t, dtype=float)
        
        # 简化的蛋形调制
        z1 = self.egg['z1']
        z2 = self.egg['z2']
        
        # 斜切锥面到蛋形
        r = 1.0 / (z1 + (z2 - z1) * t)
        
        # 归一化
        r = r / r.max()
        return r
    
    def generate_dxf(self, filename: str, n_pts: int = 16800):
        """导出为 DXF 文件
        
        参数:
            filename: .dxf 文件路径
            n_pts: 采样点数
        """
        try:
            import ezdxf
        except ImportError:
            print("ezdxf 未安装，跳过 DXF 导出。")
            return
        
        pos, _ = self.wire_path(n_pts)
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # 添加多段线
        points = [(p[0], p[1], p[2]) for p in pos]
        msp.add_polyline3d(points)
        
        doc.saveas(filename)
        print(f"✅ DXF 已保存: {filename}")
    
    def visualize(self, n_pts: int = 16800):
        """3D 可视化
        
        参数:
            n_pts: 采样点数
        """
        pos, theta = self.wire_path(n_pts)
        
        fig = plt.figure(figsize=(14, 5))
        
        # 3D 视图
        ax1 = fig.add_subplot(131, projection='3d')
        ax1.plot(pos[:, 0], pos[:, 1], pos[:, 2], 
                'b-', linewidth=0.5)
        ax1.set_title(f"Anu 导线 ({'细' if self.is_thin else '粗'}, "
                      f"{'正极' if self.winding > 0 else '负极'})")
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        
        # XY 投影
        ax2 = fig.add_subplot(132)
        ax2.plot(pos[:, 0], pos[:, 1], 'b-', linewidth=0.5)
        ax2.set_title('XY 平面投影')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.axis('equal')
        
        # XZ 投影 (显示蛋形包络)
        ax3 = fig.add_subplot(133)
        ax3.plot(pos[:, 0], pos[:, 2], 'b-', linewidth=0.5)
        ax3.set_title('XZ 平面投影 (蛋形轮廓)')
        ax3.set_xlabel('X')
        ax3.set_ylabel('Z')
        ax3.axis('equal')
        
        plt.tight_layout()
        plt.show()


# ========================================================================
# 第四部分：Anu — 完整 Anu 原子构造
# ========================================================================

class AnuAtom:
    """完整 Anu 原子
    
    包含 10 根导线 (7细+3粗):
        - 7 根细导线: 完美 7:1 螺旋比例, 彩色
        - 3 根粗导线: 704:100 比例偏差
        
    整体形状: 蛋形 (因导线进入凹陷处, 从顶点逸出)
    
    正极 Anu:  所有导线逆时针缠绕
    负极 Anu:  所有导线顺时针缠绕 (镜像)
    """
    
    def __init__(self, polarity: int = 1):
        """
        参数:
            polarity: +1=正极, -1=负极
        """
        self.polarity = polarity
        self.wires: List[AnuWire] = []
        
        # 创建 7 根细导线 (等距分布在蛋形环上)
        for i in range(N_WIRES_THIN):
            wire = AnuWire(
                is_thin=True,
                winding=polarity,
                egg_params={'z1': 1.0, 'z2': 2.0}
            )
            self.wires.append(wire)
        
        # 创建 3 根粗导线
        for i in range(N_WIRES_THICK):
            wire = AnuWire(
                is_thin=False,
                winding=polarity,
                egg_params={'z1': 1.0, 'z2': 2.0}
            )
            self.wires.append(wire)
    
    def generate_all_wires(self, n_pts: int = 16800) -> List[np.ndarray]:
        """生成所有导线的路径
        
        返回:
            paths: 10 条导线的路径列表, 每条形状 [n_pts, 3]
        """
        paths = []
        for i, wire in enumerate(self.wires):
            pos, _ = wire.wire_path(n_pts)
            
            # 每条导线在蛋形环上的位置偏移
            angle = 2 * np.pi * i / N_WIRES_TOTAL
            offset = 0.3 * np.array([np.cos(angle), np.sin(angle), 0])
            
            paths.append(pos + offset)
        
        return paths
    
    def visualize(self, n_pts: int = 8400):
        """3D 可视化完整 Anu"""
        paths = self.generate_all_wires(n_pts)
        
        fig = plt.figure(figsize=(16, 6))
        
        # 3D 视图
        ax1 = fig.add_subplot(121, projection='3d')
        colors = ['blue', 'red', 'green', 'orange', 
                  'purple', 'cyan', 'magenta', 
                  'gray', 'brown', 'black']
        
        for i, (path, c) in enumerate(zip(paths, colors)):
            ax1.plot(path[:, 0], path[:, 1], path[:, 2], 
                    color=c, linewidth=0.3, alpha=0.7,
                    label=f'Wire {i+1}')
        
        ax1.set_title(f"Anu {'正极' if self.polarity > 0 else '负极'} "
                      f"(10 根导线, 7细+3粗)")
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        
        # XY 投影
        ax2 = fig.add_subplot(122)
        for i, (path, c) in enumerate(zip(paths, colors)):
            ax2.plot(path[:, 0], path[:, 1], 
                    color=c, linewidth=0.3, alpha=0.7)
        
        ax2.set_title('XY 投影 (导线环绕布局)')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.axis('equal')
        
        plt.tight_layout()
        plt.show()
    
    def info(self) -> Dict:
        """打印 Anu 的结构信息"""
        thin_wire = self.wires[0]  # 取一根细导线示例
        thick_wire = self.wires[7]  # 取一根粗导线示例
        
        # 计算气泡总数
        # g 级 (最低级) 含有 7 个气泡
        # 每根导线气泡数 = 1680 × 7⁶ (g级单位数) × 7 (每g级含气泡)
        n_g_per_wire = N_COILS_PER_WIRE * (7 ** (N_SPIRAL_LEVELS - 1))  # 7^6 = 117,649 个 g 级单位
        bubbles_per_thin = int(n_g_per_wire * BUBBLES_PER_G)
        bubbles_per_thick = int(n_g_per_wire * CORRECTION_THICK * BUBBLES_PER_G)
        total_bubbles = (N_WIRES_THIN * bubbles_per_thin + 
                        N_WIRES_THICK * bubbles_per_thick)
        
        info = {
            'polarity': '正极 (+)' if self.polarity > 0 else '负极 (-)',
            'n_wires_total': N_WIRES_TOTAL,
            'n_wires_thin': N_WIRES_THIN,
            'n_wires_thick': N_WIRES_THICK,
            'n_coils_per_wire': N_COILS_PER_WIRE,
            'n_spiral_levels': N_SPIRAL_LEVELS,
            '1680_source': '8! / 24 = 40320 / 24 = 1680 (二阶魔方)',
            'ratio_thin': f'{RATIO_THIN}:1 (完美 7:1)',
            'ratio_thick': f'{RATIO_THICK}:1 (704:100 偏差)',
            'g_units_per_wire': f'{n_g_per_wire:,}',
            'bubbles_per_g_unit': BUBBLES_PER_G,
            'bubbles_per_thin_wire': f'{bubbles_per_thin:,}',
            'bubbles_per_thick_wire': f'{bubbles_per_thick:,}',
            'total_bubbles': f'{total_bubbles:,}',
            '1680_x_7_per_level': [
                f'Level {chr(97+k)}: {int(N_COILS_PER_WIRE * 7**k):,}  ({"内含7气泡" if k==6 else ""})'
                for k in range(N_SPIRAL_LEVELS)
            ],
        }
        
        return info


# ========================================================================
# 第五部分：验证与力学意义
# ========================================================================

def verify_1680_combinatorics():
    """验证 1680 的数学来源"""
    print("=" * 60)
    print("验证 1680 = 8!/24 数学关系")
    print("=" * 60)
    
    # 1. 二阶魔方位置数
    n_8_factorial = math.factorial(8)
    n_cube_rotations = 24
    n_1680 = n_8_factorial // n_cube_rotations
    
    print(f"\n1. 二阶魔方组合数:")
    print(f"   8! = {n_8_factorial}")
    print(f"   8!/24 = {n_8_factorial}/{n_cube_rotations} = {n_1680}")
    print(f"   ✅ 等于 Anu 每根导线的第一级螺旋体数")
    
    # 2. 7! = 5040
    n_7_factorial = math.factorial(7)
    print(f"\n2. 7! / 3:")
    print(f"   7! = {n_7_factorial}")
    print(f"   5040/3 = {n_7_factorial // 3}")
    
    # 3. 1680 × 7ⁿ 序列 (共 7 级: a→g)
    print(f"\n3. 1680 × 7ⁿ 七级螺旋序列:")
    names = ['a (第一级)', 'b (第二级)', 'c (第三级)', 'd (第四级)', 
             'e (第五级)', 'f (第六级)', 'g (最低级,内含7气泡)']
    for k in range(7):
        val = N_COILS_PER_WIRE * (7 ** k)
        print(f"   1680 × 7^{k} = {val:>20,}  ← {names[k]}")
    print(f"\n   每根导线总气泡 = 1680 × 7⁶ × 7 = {N_COILS_PER_WIRE * (7 ** 6) * 7:,}")


def demo():
    """演示 Anu 参数化"""
    print("=" * 60)
    print("Anu 七级螺旋蛋形环参数化")
    print("=" * 60)
    
    # 1. 数学验证
    verify_1680_combinatorics()
    
    # 2. 创建正极 Anu
    print(f"\n{'='*60}")
    print("创建正极 Anu...")
    anu_pos = AnuAtom(polarity=1)
    info = anu_pos.info()
    
    print(f"\nAnu 结构参数:")
    print(f"  极性: {info['polarity']}")
    print(f"  总导线数: {info['n_wires_total']} ({info['n_wires_thin']}细+{info['n_wires_thick']}粗)")
    print(f"  每根导线螺旋体数: {info['n_coils_per_wire']} (1680 = 8!/24)")
    print(f"  螺旋嵌套级数: {info['n_spiral_levels']}")
    print(f"  1680 来源: {info['1680_source']}")
    print(f"  细导线比例: {info['ratio_thin']}")
    print(f"  粗导线比例: {info['ratio_thick']}")
    print(f"  每根细导线气泡: {info['bubbles_per_thin_wire']}")
    print(f"  每根粗导线气泡: {info['bubbles_per_thick_wire']}")
    print(f"  Anu 总气泡数: {info['total_bubbles']}")
    
    # 3. 创建负极 Anu (镜像)
    print(f"\n{'='*60}")
    print("创建负极 Anu (镜像)...")
    anu_neg = AnuAtom(polarity=-1)
    info_neg = anu_neg.info()
    print(f"  极性: {info_neg['polarity']}")
    print(f"  缠绕方向: 顺时针 (正极的完全镜像)")
    
    # 4. 七级结构
    print(f"\n{'='*60}")
    print("七级嵌套结构 (a→g, 共 7 级, 频率比 1:7:7²:...:7⁶):")
    level_names = ['a (第一级/可见线圈)', 'b (第二级)', 'c (第三级)', 
                   'd (第四级)', 'e (第五级)', 'f (第六级)', 'g (最低级螺旋)']
    for k in range(7):
        ratio_val = 7 ** k
        note = "  ← 内含 7 气泡" if k == 6 else ""
        print(f"  {level_names[k]}: 7^{k} = {ratio_val:>8,} 个次级螺旋体/每个上级{note}")
    print(f"  每根导线: a × 1680 → 7⁶ × 1680 = {7**6 * 1680:,} 个 g 级单位")
    print(f"  每根导线气泡总数: {7**6 * 1680:,} × 7 = {7**7 * 1680:,}")
    
    print(f"\n✅ Anu 参数化完成")
    print(f"   {'='*50}")
    print(f"   数学基础: 1680 = 8!/24 (二阶魔方)")
    print(f"   几何基础: Schauberger 双曲锥斜切蛋形")
    print(f"   物理基础: Occult Chemistry 神秘化学")
    print(f"   {'='*50}")


if __name__ == '__main__':
    demo()
