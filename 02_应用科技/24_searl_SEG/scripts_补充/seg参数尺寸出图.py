import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.colors as mcolors
import colorsys
from scipy.optimize import fsolve

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认字体为黑体（支持中文）
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
"""
Searl效应发生器七种方案参数生成原理数学说明

通用符号定义：
- YrN: 第N环滚筒半径
- YhN: 第N环滚筒高度
- YvN: 第N环滚筒体积
- BrN: 第N环定子内径
- BRN: 第N环定子外径
- BhN: 第N环定子高度
- BvN: 第N环定子体积
- nN: 第N环稀疏因子
- numN: 第N环滚筒数量
- aN, bN: 定子与滚筒高度关系参数
- suN, sdN: 滚筒上下间隙
- d: 体积公差（等差数列差值）
- c: 三角函数方案公差
- base: 基础体积
- mass: 质量
- den: 密度
- t: 定子环厚度

通用几何关系：
1. 滚筒体积公式：YvN = π × YrN² × YhN
2. 定子环体积公式：BvN = π × (BRN² - BrN²) × BhN
3. 定子外径计算：BRN = (numN × nN × YrN) / 2
4. 定子滚筒高度关系：BhN = (YhN + aN) × bN 或 YhN = BhN/bN - aN
5. 嵌套关系：Br_{N+1} = suN + sdN + 2YrN + BRN
"""


def print_scheme1_math():
    """方案1数学原理说明"""
    print("""
方案1：已知几何尺寸求体积
----------------------------------------
已知参数：
- 定子高度 Bh1, Bh2, Bh3
- 滚筒半径 Yr1, Yr2, Yr3
- 滚筒数量 num1=12, num2=22, num3=32
- 稀疏因子 n1=n2=n3=1
- 间隙 su1=sd1=su2=sd2=1, sd3=1
- 定子内径 Br1=8
- 关系参数 a1=a2=a3=1.2, b1=b2=b3=1.0

求解目标：计算定子体积 BvN 和滚筒体积 YvN

数学原理：
1. 计算滚筒高度：YhN = BhN/bN - aN
2. 计算定子外径：BRN = (numN × nN × YrN)/2
3. 计算滚筒体积：YvN = π × YrN² × YhN
4. 计算嵌套内径：Br2 = su1 + sd1 + 2Yr1 + BR1
                        Br3 = su2 + sd2 + 2Yr2 + BR2
5. 计算定子体积：BvN = π × (BRN² - BrN²) × BhN

设计思想：从几何尺寸出发，计算各部件体积，验证设计方案。
""")


def print_scheme2_math():
    """方案2数学原理说明"""
    print("""
方案2：已知体积求几何尺寸
----------------------------------------
已知参数：
- 定子体积 Bv1=2293.25, Bv2=2512, Bv3=2730.75
- 滚筒体积 Yv1=Yv2=Yv3=12
- 滚筒数量 num1=12, num2=22, num3=32
- 稀疏因子 n1=n2=n3=1
- 间隙 su1=sd1=su2=sd2=1, sd3=1
- 定子内径 Br1=8
- 关系参数 a1=a2=a3=1.2, b1=b2=b3=1.0

求解目标：计算滚筒半径 YrN、滚筒高度 YhN、定子高度 BhN

数学原理：
需要解6元方程组（Yr1,Yr2,Yr3,Yh1,Yh2,Yh3）：
1. 滚筒体积方程：π × YrN² × YhN = YvN
2. 定子外径：BRN = (numN × nN × YrN)/2
3. 嵌套内径：Br2 = su1 + sd1 + 2Yr1 + BR1
                   Br3 = su2 + sd2 + 2Yr2 + BR2
4. 定子高度：BhN = BvN / [π × (BRN² - BrN²)]
5. 高度关系约束：BhN = (YhN + aN) × bN

设计思想：从目标体积反推几何尺寸，适用于有特定体积要求的优化设计。
""")


def print_scheme3_math():
    """方案3数学原理说明"""
    print("""
方案3：已知大部分参数求b系数和体积
----------------------------------------
已知参数：
- 定子高度 Bh1=Bh2=Bh3=1
- 滚筒半径 Yr1=Yr2=Yr3=1
- 滚筒高度 Yh1=Yh2=Yh3=1
- 滚筒数量 num1=12, num2=22, num3=32
- 稀疏因子 n1=n2=n3=2
- 间隙 su1=sd1=su2=sd2=1, sd3=1
- 定子内径 Br1=8
- 关系参数 a1=a2=a3=0.5

求解目标：计算b系数 bN 和定子体积 BvN

数学原理：
1. 计算b系数：bN = BhN / (YhN + aN)
2. 计算滚筒体积：YvN = π × YrN² × YhN
3. 计算定子外径：BRN = (numN × nN × YrN)/2
4. 计算嵌套内径：Br2 = su1 + sd1 + 2Yr1 + BR1
                        Br3 = su2 + sd2 + 2Yr2 + BR2
5. 计算定子体积：BvN = π × (BRN² - BrN²) × BhN

设计思想：校准b系数，建立定子与滚筒高度比例关系，完善设计参数体系。
""")


def print_scheme4_math():
    """方案4数学原理说明"""
    print("""
方案4：等差数列体积与等厚度约束
----------------------------------------
已知参数：
- 定子体积（等差数列）：Bv1=63000, Bv2=75000, Bv3=87000 (公差d=12000)
- 滚筒体积 Yv1=Yv2=Yv3=160
- 滚筒半径 Yr1=Yr2=Yr3=3.5
- 滚筒数量 num1=12, num2=22, num3=32
- 稀疏因子 n1=n2=n3=1
- 间隙 su1=sd1=su2=sd2=0.5, sd3=0.5
- 关系参数 b1=b2=b3=1.0

求解目标：计算定子高度 BhN、内径 BrN、外径 BRN、参数 aN

数学原理：
1. 计算滚筒高度：YhN = YvN / (π × YrN²)
2. 计算定子外径：BRN = (numN × nN × YrN)/2
3. 计算嵌套内径（初始）：Br2 = su1 + sd1 + 2Yr1 + BR1
                                Br3 = su2 + sd2 + 2Yr2 + BR2
4. 等厚度约束：设厚度 t = BR1 - 8 (Br1=8)
   - 修正：Br2 = BR2 - t, Br3 = BR3 - t
5. 计算定子高度：BhN = BvN / [π × (BRN² - BrN²)]
6. 计算a参数：aN = BhN/bN - YhN

设计思想：遵循"瑟尔真理表"的等差数列原则，确保三环体积呈等差数列，同时保持定子环厚度一致。
""")


def print_scheme5_math():
    """方案5数学原理说明"""
    print("""
方案5：等差数列体积与等厚度等间距约束
----------------------------------------
已知参数：
- 定子体积（等差数列）：Bv1=63000, Bv2=75000, Bv3=87000 (公差d=12000)
- 滚筒体积 Yv1=Yv2=Yv3=200
- 滚筒半径 Yr1=Yr2=Yr3=3.5
- 滚筒数量 num1=12, num2=22, num3=32
- 稀疏因子 n1=n2=n3=1
- 关系参数 b1=b2=b3=1.0

求解目标：计算间隙 suN,sdN、定子内径 BrN、厚度 t、高度 BhN、参数 aN

数学原理：
核心约束：BR1 - Br1 = Br2 - BR1 = BR2 - Br2 = Br3 - BR2 = BR3 - Br3 = t
1. 计算滚筒高度：YhN = YvN / (π × YrN²)
2. 计算定子外径：BRN = (numN × nN × YrN)/2
3. 建立方程组（6个方程，6个未知数 t,Br1,su1,sd1,su2,sd2）：
   a) 间距约束：Br2 - BR1 = t, Br3 - BR2 = t
   b) 嵌套关系：su1+sd1+2Yr1+BR1 = Br2, su2+sd2+2Yr2+BR2 = Br3
   c) 间隙相等：su1 = sd1, su2 = sd2
4. 求解方程组得：t, Br1, su1, sd1, su2, sd2
5. 计算：Br2 = BR2 - t, Br3 = BR3 - t, su3=su2, sd3=sd2
6. 计算定子高度：BhN = BvN / [π × (BRN² - BrN²)]
7. 计算a参数：aN = BhN/bN - YhN

设计思想：最严格的几何约束，确保定子环厚度与环间距完全相等，实现完美的几何对称。
""")


def print_scheme6_math():
    """方案6数学原理说明"""
    print("""
方案6：基于三角函数的定子半径计算
----------------------------------------
已知参数：
- 基础体积 base=12630，公差 c=1264
- 定子内径 Br1=5
- 滚筒体积 Yv1=Yv2=Yv3=20
- 滚筒半径 Yr1=Yr2=Yr3=1
- 稀疏因子 n1=n2=n3=1
- 滚筒数量 num1=12, num2=22, num3=32
- 公差参数 d1=d2=d3=1
- 关系参数 b1=b2=b3=1.0

求解目标：计算定子外径 BRN、内径 BrN、间隙 suN,sdN、高度 BhN、参数 aN

数学原理：
1. 三角函数定子外径公式：BRN = (2YrN + nN) / [2 × sin(π/numN)]
   - 推导：考虑滚筒在圆周上排列，相邻滚筒中心夹角为 2π/numN
   - 几何关系：sin(π/numN) = (YrN + nN/2) / BRN
2. 等厚度约束：t = BR1 - Br1, 则 Br2 = BR2 - t, Br3 = BR3 - t
3. 计算间隙：su1 = sd1 = (Br2 - BR1 - 2Yr1)/2
              su2 = sd2 = (Br3 - BR2 - 2Yr2)/2, sd3=su2
4. 计算滚筒高度：YhN = YvN / (π × YrN²)
5. 计算定子体积：Bv1 = base, Bv2 = base + c, Bv3 = base + 2c
6. 计算定子高度：BhN = BvN / [π × (BRN² - BrN²)]
7. 计算a参数：aN = BhN/bN - YhN

设计思想：引入三角函数确保滚筒在圆周上的精确排列，考虑实际装配间隙。
""")


def print_scheme7_math():
    """方案7数学原理说明"""
    print("""
方案7：基于质量和密度的体积计算
----------------------------------------
已知参数：
- 总质量 mass=1504720，密度 den=3.5
- 体积公差 d=8200
- 滚筒体积 Yv1=Yv2=Yv3=160
- 滚筒半径 Yr1=Yr2=Yr3=30
- 稀疏因子 n1=n2=n3=4
- 滚筒数量 num1=12, num2=22, num3=32
- 关系参数 b1=b2=b3=1.0

求解目标：计算定子体积 BvN、内径 BrN、间隙 suN,sdN、厚度 t、高度 BhN、参数 aN

数学原理：
1. 计算定子体积：Bv1 = mass/den, Bv2 = Bv1 + d, Bv3 = Bv2 + d
2. 计算滚筒高度：YhN = YvN / (π × YrN²)
3. 计算定子外径：BRN = (numN × nN × YrN)/2
4. 等厚度等间距约束（同方案5）：
   - 核心方程：BR1 - Br1 = Br2 - BR1 = BR2 - Br2 = Br3 - BR2 = BR3 - Br3 = t
   - 建立6元方程组求解 t, Br1, su1, sd1, su2, sd2
5. 计算：Br2 = BR2 - t, Br3 = BR3 - t, su3=su2, sd3=sd2
6. 计算定子高度：BhN = BvN / [π × (BRN² - BrN²)]
7. 计算a参数：aN = BhN/bN - YhN

设计思想：从物理属性（质量、密度）出发计算体积，再推导几何尺寸，确保设计的物理可实现性。
""")


def print_common_mathematical_framework():
    """通用数学框架说明"""
    print("""
Searl效应发生器设计的通用数学框架
========================================

一、核心设计原则：
1. 谐波原则：三环体积呈等差数列 Bv1, Bv2, Bv3 = base, base+d, base+2d
2. 几何对称：定子环厚度相等，环间距相等
3. 装配可行：滚筒与定子间留有适当间隙
4. 运动协调：滚筒数量按等差数列增加（12,22,32）

二、关键数学关系：
1. 周长约束：2π × BRN = numN × (2YrN + nN)
   - 简化：BRN = (numN × nN × YrN) / 2
2. 体积关系：
   - 滚筒：YvN = π × YrN² × YhN
   - 定子：BvN = π × (BRN² - BrN²) × BhN
3. 高度比例：BhN = (YhN + aN) × bN
   - 当bN=1时，BhN = YhN + aN
   - 用户引用公式：YhN = BhN/bN - aN

三、设计变量分类：
1. 独立变量：YrN, numN, nN, suN, sdN, Br1, aN, bN, d
2. 依赖变量：YhN, BRN, Br2, Br3, BhN, BvN, YvN
3. 约束变量：t（厚度）

四、求解策略：
1. 直接计算：方案1,3,4,6
2. 方程求解：方案2,5,7（使用fsolve等数值方法）
3. 迭代优化：通过调整独立变量满足所有约束

五、物理意义：
1. 稀疏因子nN：反映滚筒排列的紧密程度，nN越大排列越稀疏
2. 间隙suN,sdN：确保滚筒自由运动的最小空间
3. 参数aN：定子与滚筒的高度差调节因子
4. 参数bN：高度比例系数，通常设为1.0

六、设计验证：
1. 体积检查：BvN > 0, YvN > 0
2. 尺寸检查：BRN > BrN > 0, BhN > 0, YhN > 0
3. 间隙检查：suN > 0, sdN > 0
4. 运动检查：滚筒在轨道上不相互干涉
""")


class SearlGeneratorComplete:
    def __init__(self, scheme_number=4):
        """
        初始化Searl效应发生器求解器

        参数:
        - scheme_number: 方案编号 (1-7)
        """
        self.scheme_number = scheme_number
        self.params = self.solve_selected_scheme()

    def solve_selected_scheme(self):
        """根据选择的方案编号调用对应的求解函数"""
        scheme_functions = {
            1: self.solve_parameters_scheme1,
            2: self.solve_parameters_scheme2,
            3: self.solve_parameters_scheme3,
            4: self.solve_parameters_scheme4,
            5: self.solve_parameters_scheme5,
            6: self.solve_parameters_scheme6,
            7: self.solve_parameters_scheme7
        }

        if self.scheme_number in scheme_functions:
            return scheme_functions[self.scheme_number]()
        else:
            print(f"方案 {self.scheme_number} 不存在，使用默认方案4")
            return self.solve_parameters_scheme4()

    def solve_parameters_scheme1(self):
        """
        方案1数学逻辑: 给定定子和滚筒高度，滚筒直径，滚筒活动间隙，滚筒个数，一环定子内径，求体积

        核心约束:
        - Bh1 = (Yh1 + a1) * b1
        - BR1 = num1 * n1 * Yr1 / 2
        - Yv1 = π * Yr1² * Yh1
        - Bv1 = π * (BR1² - Br1²) * Bh1
        - Br2 = su1 + sd1 + 2Yr1 + BR1
        """
        # 固定参数
        params = {
            'su1': 1.0, 'sd1': 1.0, 'su2': 1.0, 'sd2': 1.0, 'sd3': 1.0,
            'n1': 1, 'n2': 1, 'n3': 1,
            'num1': 12, 'num2': 22, 'num3': 32,
            'Bh1': 4.25 * 2.54, 'Bh2': 4.25 * 2.54, 'Bh3': 4.25 * 2.54,
            'Yr1': 1.5, 'Yr2': 1.5, 'Yr3': 1.5,
            'a1': 1.2, 'a2': 1.2, 'a3': 1.2,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
            'Br1': 8.0
        }

        # 计算滚筒高度
        params['Yh1'] = params['Bh1'] / params['b1'] - params['a1']
        params['Yh2'] = params['Bh2'] / params['b2'] - params['a2']
        params['Yh3'] = params['Bh3'] / params['b3'] - params['a3']

        # 计算定子外径
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        # 计算滚筒体积
        params['Yv1'] = np.pi * params['Yr1'] ** 2 * params['Yh1']
        params['Yv2'] = np.pi * params['Yr2'] ** 2 * params['Yh2']
        params['Yv3'] = np.pi * params['Yr3'] ** 2 * params['Yh3']

        # 计算嵌套关系
        params['Br2'] = params['su1'] + params['sd1'] + 2 * params['Yr1'] + params['BR1']
        params['Br3'] = params['su2'] + params['sd2'] + 2 * params['Yr2'] + params['BR2']

        # 计算定子体积
        params['Bv1'] = np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2) * params['Bh1']
        params['Bv2'] = np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2) * params['Bh2']
        params['Bv3'] = np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2) * params['Bh3']

        # 计算公差（等差数列的差值）
        params['d'] = params['Bv2'] - params['Bv1']

        return params

    def solve_parameters_scheme2(self):
        """
        方案2数学逻辑: 给定定子体积，滚筒直径，滚筒活动间隙，滚筒个数，一环定子内径，求高度

        核心约束: 已知体积求高度，需要解方程组
        """
        # 固定参数
        params = {
            'su1': 1.0, 'sd1': 1.0, 'su2': 1.0, 'sd2': 1.0, 'sd3': 1.0,
            'n1': 1, 'n2': 1, 'n3': 1,
            'num1': 12, 'num2': 22, 'num3': 32,
            'Yv1': 12.0, 'Yv2': 12.0, 'Yv3': 12.0,
            'Bv1': 2293.25, 'Bv2': 2512.0, 'Bv3': 2730.75,
            'a1': 1.2, 'a2': 1.2, 'a3': 1.2,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
            'Br1': 8.0
        }

        # 设定初始猜测值
        initial_guess = [1.5, 1.5, 1.5, 1.0, 1.0, 1.0]  # Yr1, Yr2, Yr3, Yh1, Yh2, Yh3

        def equations(vars):
            Yr1, Yr2, Yr3, Yh1, Yh2, Yh3 = vars

            # 滚筒体积方程
            eq1 = np.pi * Yr1 ** 2 * Yh1 - params['Yv1']
            eq2 = np.pi * Yr2 ** 2 * Yh2 - params['Yv2']
            eq3 = np.pi * Yr3 ** 2 * Yh3 - params['Yv3']

            # 定子外径
            BR1 = (params['num1'] * params['n1'] * Yr1) / 2
            BR2 = (params['num2'] * params['n2'] * Yr2) / 2
            BR3 = (params['num3'] * params['n3'] * Yr3) / 2

            # 嵌套关系
            Br2 = params['su1'] + params['sd1'] + 2 * Yr1 + BR1
            Br3 = params['su2'] + params['sd2'] + 2 * Yr2 + BR2

            # 定子高度
            Bh1 = params['Bv1'] / (np.pi * (BR1 ** 2 - params['Br1'] ** 2))
            Bh2 = params['Bv2'] / (np.pi * (BR2 ** 2 - Br2 ** 2))
            Bh3 = params['Bv3'] / (np.pi * (BR3 ** 2 - Br3 ** 2))

            # Bh与Yh的关系
            eq4 = Bh1 - (Yh1 + params['a1']) * params['b1']
            eq5 = Bh2 - (Yh2 + params['a2']) * params['b2']
            eq6 = Bh3 - (Yh3 + params['a3']) * params['b3']

            return [eq1, eq2, eq3, eq4, eq5, eq6]

        # 使用数值方法求解方程组
        solution = fsolve(equations, initial_guess)
        params['Yr1'], params['Yr2'], params['Yr3'], params['Yh1'], params['Yh2'], params['Yh3'] = solution

        # 计算其他参数
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        params['Br2'] = params['su1'] + params['sd1'] + 2 * params['Yr1'] + params['BR1']
        params['Br3'] = params['su2'] + params['sd2'] + 2 * params['Yr2'] + params['BR2']

        params['Bh1'] = params['Bv1'] / (np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2))
        params['Bh2'] = params['Bv2'] / (np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2))
        params['Bh3'] = params['Bv3'] / (np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2))

        # 计算公差
        params['d'] = params['Bv2'] - params['Bv1']

        return params

    def solve_parameters_scheme3(self):
        """
        方案3数学逻辑: 给定所有可见参数，除了b1,b2,b3，求定子体积

        已知大部分参数，求b系数和定子体积
        """
        # 固定参数
        params = {
            'su1': 1.0, 'sd1': 1.0, 'su2': 1.0, 'sd2': 1.0, 'sd3': 1.0,
            'num1': 12, 'num2': 22, 'num3': 32,
            'n1': 2.0, 'n2': 2.0, 'n3': 2.0,
            'Yr1': 1.0, 'Yr2': 1.0, 'Yr3': 1.0,
            'Yh1': 1.0, 'Yh2': 1.0, 'Yh3': 1.0,
            'Bh1': 1.0, 'Bh2': 1.0, 'Bh3': 1.0,
            'Br1': 8.0,
            'a1': 0.5, 'a2': 0.5, 'a3': 0.5
        }

        # 计算b系数
        params['b1'] = params['Bh1'] / (params['Yh1'] + params['a1'])
        params['b2'] = params['Bh2'] / (params['Yh2'] + params['a2'])
        params['b3'] = params['Bh3'] / (params['Yh3'] + params['a3'])

        # 计算滚筒体积
        params['Yv1'] = np.pi * params['Yr1'] ** 2 * params['Yh1']
        params['Yv2'] = np.pi * params['Yr2'] ** 2 * params['Yh2']
        params['Yv3'] = np.pi * params['Yr3'] ** 2 * params['Yh3']

        # 计算定子外径
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        # 计算嵌套关系
        params['Br2'] = params['su1'] + params['sd1'] + 2 * params['Yr1'] + params['BR1']
        params['Br3'] = params['su2'] + params['sd2'] + 2 * params['Yr2'] + params['BR2']

        # 计算定子体积
        params['Bv1'] = np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2) * params['Bh1']
        params['Bv2'] = np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2) * params['Bh2']
        params['Bv3'] = np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2) * params['Bh3']

        # 计算公差
        params['d'] = params['Bv2'] - params['Bv1']

        return params

    def solve_parameters_scheme4(self):
        """
        方案4数学逻辑: 体积参数用等差数列，采用瑟尔真理表算出，令定子环厚度相等，高度自由

        核心约束: 定子体积呈等差数列，定子环厚度相等
        """
        # 固定参数
        params = {
            'su1': 0.5, 'sd1': 0.5, 'su2': 0.5, 'sd2': 0.5, 'sd3': 0.5,
            'num1': 12, 'num2': 22, 'num3': 32,
            'n1': 1, 'n2': 1, 'n3': 1,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
            'd': 12000,
            'Bv1': 63000, 'Bv2': 75000, 'Bv3': 87000,
            'Yr1': 3.5, 'Yr2': 3.5, 'Yr3': 3.5,
            'Yv1': 160, 'Yv2': 160, 'Yv3': 160
        }

        # 计算滚筒高度
        params['Yh1'] = params['Yv1'] / (np.pi * params['Yr1'] ** 2)
        params['Yh2'] = params['Yv2'] / (np.pi * params['Yr2'] ** 2)
        params['Yh3'] = params['Yv3'] / (np.pi * params['Yr3'] ** 2)

        # 计算定子外径
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        # 计算定子内径（基于嵌套关系）
        params['Br2'] = params['su1'] + params['sd1'] + 2 * params['Yr1'] + params['BR1']
        params['Br3'] = params['su2'] + params['sd2'] + 2 * params['Yr2'] + params['BR2']

        # 计算厚度
        thickness = params['BR1'] - 8

        # 重新计算Br1, Br2, Br3确保等厚度
        params['Br1'] = 8
        params['Br2'] = params['BR2'] - thickness
        params['Br3'] = params['BR3'] - thickness

        # 计算定子高度
        params['Bh1'] = params['Bv1'] / (np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2))
        params['Bh2'] = params['Bv2'] / (np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2))
        params['Bh3'] = params['Bv3'] / (np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2))

        # 计算a参数
        params['a1'] = params['Bh1'] / params['b1'] - params['Yh1']
        params['a2'] = params['Bh2'] / params['b2'] - params['Yh2']
        params['a3'] = params['Bh3'] / params['b3'] - params['Yh3']

        return params

    def solve_parameters_scheme5(self):
        """
        方案5数学逻辑: 体积参数用等差数列，定子环厚度与环间距都相等，高度自由

        核心约束: 定子体积等差数列，厚度与间距都相等
        """
        # 固定参数
        params = {
            'num1': 12, 'num2': 22, 'num3': 32,
            'n1': 1, 'n2': 1, 'n3': 1,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
            'd': 12000,
            'Bv1': 63000, 'Bv2': 75000, 'Bv3': 87000,
            'Yr1': 3.5, 'Yr2': 3.5, 'Yr3': 3.5,
            'Yv1': 200, 'Yv2': 200, 'Yv3': 200
        }

        # 计算滚筒高度
        params['Yh1'] = params['Yv1'] / (np.pi * params['Yr1'] ** 2)
        params['Yh2'] = params['Yv2'] / (np.pi * params['Yr2'] ** 2)
        params['Yh3'] = params['Yv3'] / (np.pi * params['Yr3'] ** 2)

        # 计算定子外径
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        # 等厚度和等间距约束
        # BR1 - Br1 = Br2 - BR1 = BR2 - Br2 = Br3 - BR2 = BR3 - Br3 = t
        # 设厚度为t

        def equations(vars):
            t, Br1, su1, sd1, su2, sd2 = vars

            Br2 = params['BR2'] - t
            Br3 = params['BR3'] - t

            # 间距约束
            eq1 = Br2 - params['BR1'] - t
            eq2 = Br3 - params['BR2'] - t

            # 嵌套关系约束
            eq3 = su1 + sd1 + 2 * params['Yr1'] + params['BR1'] - Br2
            eq4 = su2 + sd2 + 2 * params['Yr2'] + params['BR2'] - Br3

            # 假设su和sd相等
            eq5 = su1 - sd1
            eq6 = su2 - sd2

            return [eq1, eq2, eq3, eq4, eq5, eq6]

        # 初始猜测值
        initial_guess = [10.0, 8.0, 0.5, 0.5, 0.5, 0.5]
        solution = fsolve(equations, initial_guess)

        t, params['Br1'], params['su1'], params['sd1'], params['su2'], params['sd2'] = solution
        params['Br2'] = params['BR2'] - t
        params['Br3'] = params['BR3'] - t
        params['thickness'] = t
        params['su3'] = params['su2']
        params['sd3'] = params['sd2']

        # 计算定子高度
        params['Bh1'] = params['Bv1'] / (np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2))
        params['Bh2'] = params['Bv2'] / (np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2))
        params['Bh3'] = params['Bv3'] / (np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2))

        # 计算a参数
        params['a1'] = params['Bh1'] / params['b1'] - params['Yh1']
        params['a2'] = params['Bh2'] / params['b2'] - params['Yh2']
        params['a3'] = params['Bh3'] / params['b3'] - params['Yh3']

        return params

    def solve_parameters_scheme6(self):
        """
        方案6数学逻辑: 定子半径基于三角函数计算，考虑滚筒间隙

        核心公式: BR = (2Yr + n) / (2sin(π/num))
        """
        # 固定参数
        params = {
            'c': 1264, 'base': 12630,
            'Br1': 5.0,
            'd1': 1.0, 'd2': 1.0, 'd3': 1.0,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
            'num1': 12, 'num2': 22, 'num3': 32,
            'n1': 1.0, 'n2': 1.0, 'n3': 1.0,
            'Yr1': 1.0, 'Yr2': 1.0, 'Yr3': 1.0,
            'Yv1': 20.0, 'Yv2': 20.0, 'Yv3': 20.0
        }

        # 计算定子外径（基于三角函数）
        params['BR1'] = (2 * params['Yr1'] + params['n1']) / (2 * np.sin(np.pi / params['num1']))
        params['BR2'] = (2 * params['Yr2'] + params['n2']) / (2 * np.sin(np.pi / params['num2']))
        params['BR3'] = (2 * params['Yr3'] + params['n3']) / (2 * np.sin(np.pi / params['num3']))

        # 等厚度约束
        t = params['BR1'] - params['Br1']  # 厚度
        params['Br2'] = params['BR2'] - t
        params['Br3'] = params['BR3'] - t

        # 计算嵌套关系
        params['su1'] = params['sd1'] = (params['Br2'] - params['BR1'] - 2 * params['Yr1']) / 2
        params['su2'] = params['sd2'] = (params['Br3'] - params['BR2'] - 2 * params['Yr2']) / 2
        params['sd3'] = params['su2']

        # 计算滚筒高度
        params['Yh1'] = params['Yv1'] / (np.pi * params['Yr1'] ** 2)
        params['Yh2'] = params['Yv2'] / (np.pi * params['Yr2'] ** 2)
        params['Yh3'] = params['Yv3'] / (np.pi * params['Yr3'] ** 2)

        # 计算定子体积
        params['Bv1'] = params['base']
        params['Bv2'] = params['base'] + params['c']
        params['Bv3'] = params['base'] + 2 * params['c']

        # 计算定子高度
        params['Bh1'] = params['Bv1'] / (np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2))
        params['Bh2'] = params['Bv2'] / (np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2))
        params['Bh3'] = params['Bv3'] / (np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2))

        # 计算a参数
        params['a1'] = params['Bh1'] / params['b1'] - params['Yh1']
        params['a2'] = params['Bh2'] / params['b2'] - params['Yh2']
        params['a3'] = params['Bh3'] / params['b3'] - params['Yh3']

        # 计算公差
        params['d'] = params['c']

        return params

    def solve_parameters_scheme7(self):
        """
        方案7数学逻辑: 基于质量和密度计算体积，定子环厚度与环间距相等
        """
        # 固定参数
        params = {
            'd': 8200, 'mass': 1504720, 'den': 3.5,
            'n1': 4, 'n2': 4, 'n3': 4,
            'num1': 12, 'num2': 22, 'num3': 32,
            'Yr1': 30.0, 'Yr2': 30.0, 'Yr3': 30.0,
            'Yv1': 160.0, 'Yv2': 160.0, 'Yv3': 160.0,
            'b1': 1.0, 'b2': 1.0, 'b3': 1.0
        }

        # 计算定子体积（基于质量和密度）
        params['Bv1'] = params['mass'] / params['den']
        params['Bv2'] = params['Bv1'] + params['d']
        params['Bv3'] = params['Bv2'] + params['d']

        # 计算滚筒高度
        params['Yh1'] = params['Yv1'] / (np.pi * params['Yr1'] ** 2)
        params['Yh2'] = params['Yv2'] / (np.pi * params['Yr2'] ** 2)
        params['Yh3'] = params['Yv3'] / (np.pi * params['Yr3'] ** 2)

        # 计算定子外径
        params['BR1'] = (params['num1'] * params['n1'] * params['Yr1']) / 2
        params['BR2'] = (params['num2'] * params['n2'] * params['Yr2']) / 2
        params['BR3'] = (params['num3'] * params['n3'] * params['Yr3']) / 2

        # 等厚度和等间距约束
        def equations(vars):
            t, Br1, su1, sd1, su2, sd2 = vars

            Br2 = params['BR2'] - t
            Br3 = params['BR3'] - t

            # 间距约束
            eq1 = Br2 - params['BR1'] - t
            eq2 = Br3 - params['BR2'] - t

            # 嵌套关系约束
            eq3 = su1 + sd1 + 2 * params['Yr1'] + params['BR1'] - Br2
            eq4 = su2 + sd2 + 2 * params['Yr2'] + params['BR2'] - Br3

            # 假设su和sd相等
            eq5 = su1 - sd1
            eq6 = su2 - sd2

            return [eq1, eq2, eq3, eq4, eq5, eq6]

        # 初始猜测值
        initial_guess = [10.0, 8.0, 0.5, 0.5, 0.5, 0.5]
        solution = fsolve(equations, initial_guess)

        t, params['Br1'], params['su1'], params['sd1'], params['su2'], params['sd2'] = solution
        params['Br2'] = params['BR2'] - t
        params['Br3'] = params['BR3'] - t
        params['thickness'] = t
        params['su3'] = params['su2']
        params['sd3'] = params['sd2']

        # 计算定子高度
        params['Bh1'] = params['Bv1'] / (np.pi * (params['BR1'] ** 2 - params['Br1'] ** 2))
        params['Bh2'] = params['Bv2'] / (np.pi * (params['BR2'] ** 2 - params['Br2'] ** 2))
        params['Bh3'] = params['Bv3'] / (np.pi * (params['BR3'] ** 2 - params['Br3'] ** 2))

        # 计算a参数
        params['a1'] = params['Bh1'] / params['b1'] - params['Yh1']
        params['a2'] = params['Bh2'] / params['b2'] - params['Yh2']
        params['a3'] = params['Bh3'] / params['b3'] - params['Yh3']

        return params

    # 以下是3D可视化相关的方法，与原始代码保持一致
    def create_cylinder(self, radius, height, center=(0, 0, 0), resolution=32):
        """创建圆柱体网格"""
        z = np.linspace(-height / 2, height / 2, 2)
        theta = np.linspace(0, 2 * np.pi, resolution)
        theta_grid, z_grid = np.meshgrid(theta, z)

        x = radius * np.cos(theta_grid) + center[0]
        y = radius * np.sin(theta_grid) + center[1]
        z = z_grid + center[2]

        return x, y, z

    def create_hollow_cylinder(self, inner_radius, outer_radius, height, center=(0, 0, 0), resolution=32):
        """创建空心圆柱体（定子环）"""
        # 创建侧面
        theta = np.linspace(0, 2 * np.pi, resolution)
        z = np.array([-height / 2, height / 2])

        theta_grid, z_grid = np.meshgrid(theta, z)

        # 外侧面
        x_outer = outer_radius * np.cos(theta_grid) + center[0]
        y_outer = outer_radius * np.sin(theta_grid) + center[1]
        z_outer = z_grid + center[2]

        # 内侧面
        x_inner = inner_radius * np.cos(theta_grid) + center[0]
        y_inner = inner_radius * np.sin(theta_grid) + center[1]
        z_inner = z_grid + center[2]

        # 创建顶面和底面环
        r = np.linspace(inner_radius, outer_radius, 2)
        r_grid, theta_grid_top = np.meshgrid(r, theta)

        # 顶面
        x_top = r_grid * np.cos(theta_grid_top) + center[0]
        y_top = r_grid * np.sin(theta_grid_top) + center[1]
        z_top = np.ones_like(x_top) * height / 2 + center[2]

        # 底面
        z_bottom = np.ones_like(x_top) * -height / 2 + center[2]

        return {
            'outer_side': (x_outer, y_outer, z_outer),
            'inner_side': (x_inner, y_inner, z_inner),
            'top_ring': (x_top, y_top, z_top),
            'bottom_ring': (x_top, y_top, z_bottom)
        }

    def create_roller_assembly(self, orbit_radius, roller_radius, roller_height, num_rollers, phase=0):
        """创建滚筒装配体"""
        rollers = []

        for i in range(num_rollers):
            # 计算滚筒位置（极坐标转直角坐标）
            angle = phase + 2 * np.pi * i / num_rollers
            x = orbit_radius * np.cos(angle)
            y = orbit_radius * np.sin(angle)
            z = 0

            # 创建滚筒
            roller = self.create_cylinder(roller_radius, roller_height, (x, y, z))
            rollers.append(roller)

        return rollers

    def calculate_orbit_radii(self):
        """计算滚筒轨道半径"""
        p = self.params
        orbit1 = (p['BR1'] + p['Br2']) / 2
        orbit2 = (p['BR2'] + p['Br3']) / 2
        orbit3 = (p['Br3'] - orbit2) + p['BR3']

        return orbit1, orbit2, orbit3

    def generate_hsv_colors(self, num_colors, start_hue=0.0, end_hue=0.8,
                            saturation=0.8, value=0.9, mode='linear'):
        """生成HSV渐变颜色"""
        colors = []

        for i in range(num_colors):
            if mode == 'linear':
                # 线性渐变
                hue = start_hue + (end_hue - start_hue) * (i / (num_colors - 1))
            elif mode == 'sinusoidal':
                # 正弦渐变，中心颜色更丰富
                t = i / (num_colors - 1)
                hue = start_hue + (end_hue - start_hue) * (0.5 - 0.5 * np.cos(np.pi * t))
            elif mode == 'quadratic':
                # 二次渐变
                t = i / (num_colors - 1)
                hue = start_hue + (end_hue - start_hue) * t ** 2
            else:
                hue = start_hue + (end_hue - start_hue) * (i / (num_colors - 1))

            # 确保hue在0-1范围内
            hue = hue % 1.0

            # 转换为RGB
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append(rgb)

        return colors

    def generate_complementary_colors(self, num_pairs, base_hue=0.0,
                                      saturation_range=(0.7, 0.9),
                                      value_range=(0.7, 0.9)):
        """生成互补颜色对"""
        primary_colors = []
        complementary_colors = []

        for i in range(num_pairs):
            # 计算当前色相
            hue = (base_hue + i * 0.3) % 1.0

            # 计算饱和度渐变
            sat_primary = saturation_range[0] + (saturation_range[1] - saturation_range[0]) * (i / (num_pairs - 1))
            sat_complementary = saturation_range[1] - (saturation_range[1] - saturation_range[0]) * (
                        i / (num_pairs - 1))

            # 计算明度渐变
            val_primary = value_range[0] + (value_range[1] - value_range[0]) * (i / (num_pairs - 1))
            val_complementary = value_range[1] - (value_range[1] - value_range[0]) * (i / (num_pairs - 1))

            # 生成主颜色
            primary_rgb = colorsys.hsv_to_rgb(hue, sat_primary, val_primary)
            primary_colors.append(primary_rgb)

            # 生成互补颜色（色相+0.5）
            complementary_hue = (hue + 0.5) % 1.0
            complementary_rgb = colorsys.hsv_to_rgb(complementary_hue, sat_complementary, val_complementary)
            complementary_colors.append(complementary_rgb)

        return primary_colors, complementary_colors

    def plot_3d_model(self, phase_angle=0, color_scheme='hsv_gradient'):
        """创建3D可视化"""
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111, projection='3d')

        p = self.params

        # 计算轨道半径
        orbit1, orbit2, orbit3 = self.calculate_orbit_radii()

        # 根据选择的颜色方案生成颜色
        if color_scheme == 'hsv_gradient':
            # HSV渐变方案
            stator_colors = self.generate_hsv_colors(3, start_hue=0.0, end_hue=0.8,
                                                     saturation=0.8, value=0.8, mode='sinusoidal')
            roller_colors = self.generate_hsv_colors(3, start_hue=0.6, end_hue=0.2,
                                                     saturation=0.6, value=0.9, mode='sinusoidal')
        elif color_scheme == 'complementary':
            # 互补色方案
            stator_colors, roller_colors = self.generate_complementary_colors(
                3, base_hue=0.2, saturation_range=(0.7, 0.9), value_range=(0.7, 0.9))
        elif color_scheme == 'warm_cool':
            # 暖色-冷色对比方案
            stator_colors = self.generate_hsv_colors(3, start_hue=0.0, end_hue=0.1,
                                                     saturation=0.8, value=0.8, mode='linear')
            roller_colors = self.generate_hsv_colors(3, start_hue=0.5, end_hue=0.7,
                                                     saturation=0.7, value=0.9, mode='linear')
        else:
            # 默认方案
            stator_colors = self.generate_hsv_colors(3, start_hue=0.0, end_hue=0.8,
                                                     saturation=0.8, value=0.8, mode='sinusoidal')
            roller_colors = self.generate_hsv_colors(3, start_hue=0.6, end_hue=0.2,
                                                     saturation=0.6, value=0.9, mode='sinusoidal')

        # 创建定子环
        # 第一环定子
        stator1 = self.create_hollow_cylinder(p['Br1'], p['BR1'], p['Bh1'])
        self._plot_hollow_cylinder(ax, stator1, stator_colors[0], alpha=0.8)

        # 第二环定子
        stator2 = self.create_hollow_cylinder(p['Br2'], p['BR2'], p['Bh2'])
        self._plot_hollow_cylinder(ax, stator2, stator_colors[1], alpha=0.8)

        # 第三环定子
        stator3 = self.create_hollow_cylinder(p['Br3'], p['BR3'], p['Bh3'])
        self._plot_hollow_cylinder(ax, stator3, stator_colors[2], alpha=0.8)

        # 创建滚筒
        # 第一环滚筒
        rollers1 = self.create_roller_assembly(orbit1, p['Yr1'], p['Yh1'], p['num1'], phase_angle)
        for roller in rollers1:
            self._plot_cylinder(ax, roller, roller_colors[0], alpha=0.9)

        # 第二环滚筒
        rollers2 = self.create_roller_assembly(orbit2, p['Yr2'], p['Yh2'], p['num2'], phase_angle * 2.5)
        for roller in rollers2:
            self._plot_cylinder(ax, roller, roller_colors[1], alpha=0.9)

        # 第三环滚筒
        rollers3 = self.create_roller_assembly(orbit3, p['Yr3'], p['Yh3'], p['num3'], phase_angle * 6.25)
        for roller in rollers3:
            self._plot_cylinder(ax, roller, roller_colors[2], alpha=0.9)

        # 设置图形属性
        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        ax.set_zlabel('Z轴')
        ax.set_title(
            f'Searl效应发生器3D模型 - 方案{self.scheme_number} (颜色方案: {color_scheme})\n(定子环 + 滚筒装配)',
            fontsize=14, fontweight='bold')

        # 设置相等的缩放比例
        max_dim = max(p['BR3'], p['Bh3'])
        ax.set_xlim([-max_dim * 1.2, max_dim * 1.2])
        ax.set_ylim([-max_dim * 1.2, max_dim * 1.2])
        ax.set_zlim([-max_dim * 0.6, max_dim * 0.6])

        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=stator_colors[0], alpha=0.8, label='第一环定子'),
            Patch(facecolor=stator_colors[1], alpha=0.8, label='第二环定子'),
            Patch(facecolor=stator_colors[2], alpha=0.8, label='第三环定子'),
            Patch(facecolor=roller_colors[0], alpha=0.9, label='第一环滚筒'),
            Patch(facecolor=roller_colors[1], alpha=0.9, label='第二环滚筒'),
            Patch(facecolor=roller_colors[2], alpha=0.9, label='第三环滚筒')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))

        plt.tight_layout()
        return fig, ax

    def _plot_hollow_cylinder(self, ax, hollow_cylinder, color, alpha=0.8):
        """绘制空心圆柱体"""
        # 绘制外侧面
        x, y, z = hollow_cylinder['outer_side']
        ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

        # 绘制内侧面
        x, y, z = hollow_cylinder['inner_side']
        ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

        # 绘制顶面环
        x, y, z = hollow_cylinder['top_ring']
        ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

        # 绘制底面环
        x, y, z = hollow_cylinder['bottom_ring']
        ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

    def _plot_cylinder(self, ax, cylinder, color, alpha=0.9):
        """绘制圆柱体"""
        x, y, z = cylinder
        ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

    def print_parameters(self):
        """打印计算出的参数"""
        print(f"=== Searl效应发生器参数 (方案{self.scheme_number}) ===")
        p = self.params

        print("\n--- 定子参数 ---")
        print(f"第一环: 内径={p['Br1']:.2f}, 外径={p['BR1']:.2f}, 高度={p['Bh1']:.2f}")
        print(f"第二环: 内径={p['Br2']:.2f}, 外径={p['BR2']:.2f}, 高度={p['Bh2']:.2f}")
        print(f"第三环: 内径={p['Br3']:.2f}, 外径={p['BR3']:.2f}, 高度={p['Bh3']:.2f}")

        print("\n--- 滚筒参数 ---")
        print(f"第一环: 半径={p['Yr1']:.2f}, 高度={p['Yh1']:.2f}, 数量={p['num1']}")
        print(f"第二环: 半径={p['Yr2']:.2f}, 高度={p['Yh2']:.2f}, 数量={p['num2']}")
        print(f"第三环: 半径={p['Yr3']:.2f}, 高度={p['Yh3']:.2f}, 数量={p['num3']}")

        print("\n--- 间隙参数 ---")
        print(f"su1={p.get('su1', 0):.2f}, sd1={p.get('sd1', 0):.2f}")
        print(f"su2={p.get('su2', 0):.2f}, sd2={p.get('sd2', 0):.2f}")
        print(f"sd3={p.get('sd3', 0):.2f}")

        print("\n--- 体积参数 ---")
        print(f"定子体积: Bv1={p.get('Bv1', 0):.2f}, Bv2={p.get('Bv2', 0):.2f}, Bv3={p.get('Bv3', 0):.2f}")
        print(f"滚筒体积: Yv1={p.get('Yv1', 0):.2f}, Yv2={p.get('Yv2', 0):.2f}, Yv3={p.get('Yv3', 0):.2f}")
        print(f"公差: d={p.get('d', 0):.2f}")

        orbit1, orbit2, orbit3 = self.calculate_orbit_radii()
        print("\n--- 轨道半径 ---")
        print(f"第一环轨道半径: {orbit1:.2f}")
        print(f"第二环轨道半径: {orbit2:.2f}")
        print(f"第三环轨道半径: {orbit3:.2f}")


# 主程序
if __name__ == "__main__":
    # 测试所有方案
    for scheme_num in range(1, 8):
        print(f"\n{'=' * 60}")
        print(f"正在求解方案 {scheme_num}...")
        print('=' * 60)

        try:
            # 创建Searl发生器实例
            searl_gen = SearlGeneratorComplete(scheme_number=scheme_num)

            # 打印参数
            searl_gen.print_parameters()

            # 创建3D模型
            print("\n正在生成3D模型...")
            fig, ax = searl_gen.plot_3d_model(phase_angle=0, color_scheme='hsv_gradient')

            # 保存图像
            plt.savefig(f'searl_generator_scheme_{scheme_num}.png', dpi=300, bbox_inches='tight')
            print(f"已保存: searl_generator_scheme_{scheme_num}.png")
            plt.close(fig)

        except Exception as e:
            print(f"方案 {scheme_num} 求解失败: {e}")

    print("\n所有方案求解完成！")
    # 使用方案4（默认）
    # 打印所有方案的数学原理
    print("=" * 80)
    print("SEARL效应发生器七种方案参数生成原理数学说明")
    print("=" * 80)

    print_scheme1_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme2_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme3_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme4_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme5_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme6_math()
    print("\n" + "-" * 80 + "\n")

    print_scheme7_math()
    print("\n" + "-" * 80 + "\n")

    print_common_mathematical_framework()
    generator = SearlGeneratorComplete(scheme_number=1)
    fig, ax = generator.plot_3d_model(phase_angle=0, color_scheme='hsv_gradient')
    plt.show()


