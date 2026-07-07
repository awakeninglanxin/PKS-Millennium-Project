# 📜 PKS_千禧难题_统一解 历史代码演化档案

> 这里存放从 `E:\pythonProject\pythonProject\` 整理出来的45个历史Python文件，
> 记录从2025年9月的原始探索到当前PKS模块化体系的完整演化路径。

---

## 演化全景图

```
2025年9月 ~ 2026年5月：六条并行的演化线路

原始探索 ──────────────────────────────────────────→ 模块化PKS体系

  A: 蛋形曲线   ○──→ 参数化 → 八度公式 → 模块化(egg_curve.py)
                        ↓
  B: 羚羊角管    ○──→ F-S标架 → 多螺旋 → OOP+NURBS → DXF双轨
                        ↓
  C: 蛋→Sin波   ○──→ 摆线调制 → 对数衰减 → 卍字符 → 3D阴阳合一
                        ↓
  D: 锥体涡旋    ○──→ 纯螺旋 → 对数高度 → 斐波那契序列
                        ↓
  E: 谱方法      ○──→ Chebyshev + FEM → 蛋形-圆环对偶性
```

---

## A. 蛋形曲线发现史 (15 files)

### 演化时间线

| 阶段 | 文件 | 核心突破 | PKS对应 |
|------|------|---------|---------|
| **A1 几何构造** | `黄金比五边形蛋形构造法.py` | 用圆和五边形纯几何构造蛋形 | PKS无等价（启蒙阶段） |
| **A2 隐式验证** | `舒伯格蛋交线螺旋方程.py` | 用contour验证隐式蛋形方程 | `egg_curve.py`的explicit_form |
| **A3 t-参数化** | `Walter蛋形曲线.py` | x=t, y=±√(1/(b+t·sinα)²-(t·cosα)²) | `egg_curve.py`的get_curve_points_t() |
| **A4 平滑改进** | `Walter蛋形曲线_平滑版.py` | 正负分支连续绘制 | PKS中的左右半合并逻辑 |
| **A5 解析公式** | `舒伯格蛋我的参数方程.py` | 完整x(t),y(t)参数方程(k=2/3,b=5/3,m=2/3) | `schauberger_egg_family.py`的八度公式族 |
| **A6 交互引擎** | `舒伯格蛋Die Ei-Kurve.py` | z0\tan_α双向转换+动画导出 | `egg_curve.py`核心参数体系 |
| **A7 黄金比锥** | `egg黄金比锥切面螺旋线...py` | r=1/t漏斗母线+z=ln(t)\ln(φ) | `egg_3d_spiral.py`的直接前身 |
| **A8 斐波那契族** | `舒伯格蛋Die Ei-Kurve -蛋螺旋 缩放1除n - 副本.py` | F_n相邻项比值驱动蛋形参数 | PKS无等价（正弦方案vs八度方案） |
| **A9 蛋+环** | `Hyperbolic Egg Curve蛋+环公式.py` | 2D蛋形→3D环面缠绕 | PKS无等价（拓扑复合结构） |
| **A10 3D锥面** | `Schaubergercone.py` | 黄金比(a=161.8,b=100)3D曲面 | `egg_3d_spiral.py`概念继承但公式不同 |

### 关键公式演进

```
阶段A1-A2: 隐式方程 1/(z0+y·sinα)² - (x²+(y·cosα)²) = 0
     ↓ contour验证 → 转向显式
阶段A3-A4: x=t, x̄=±√(1/(z0+y·sinα)²-(y·cosα)²)  (Walter蛋形t-参数化)
     ↓ 转向解析参数化
阶段A5:    x(t)=a·2sin(t)/(b+√(b²-4k·cos(t))),
           y(t)=a·(m·term1+term2)  (我的参数方程)
     ↓ 泛化到多八度
阶段A6-A8: z0, tan_α参数体系 + 斐波那契/黄金比缩放
     ↓ 结构化封装
PKS:      EggCurve dataclass → get_curve_points_t() → 3D扫掠
```

---

## B. 羚羊角管→螺旋管进化 (8 files)

### 演化时间线

| 阶段 | 文件 | 核心突破 | PKS对应 |
|------|------|---------|---------|
| **B1 原始数学** | `舒伯格蛋单边交线螺旋方程.py` | xy=1斜切方程+3D螺旋投影(85行) | `funnel_surface.py`的egg_golden_funnel() |
| **B2 初始原型** | `kudo horn羚羊角.py` | 对数螺旋+2D旋转+双蛋截面+OBJ | PKS无1:1等价 |
| **B3 F-S突破** | `kudo horn羚羊角 new.py` | **Frenet-Serret标架+Rordrigues旋转** | `egg_3d_geometry.py`的核心方法 |
| **B4 多螺旋阵列** | `kudo horn羚羊角 new 4 - best.py` | 3D叶形截面+连续缩放+3实例120°阵列 | PKS中分散在多个文件 |
| **B5 数值优化** | `kudo horn羚羊角底逆时针内进水锥顺转 (2.53上下比) - 正解.py` | 数值TNB+2.53上下比精调 | `egg_3d_geometry.py` |
| **B6 OOP重构** | `kudo horn羚羊角nurbs网格最终版 - 副本.py` | 类架构+NURBS平滑+CSV驱动 | `egg_3d_geometry.py`+`egg_fsolve_spline.py` |
| **B7 DXF双轨** | `羚羊角管中心线与蛋尖双轨-dxf样条线最终.py` | 中心线+蛋尖线双轨样条导出 | `egg_3d_spiral.py`的export_dxf |

### 技术跃迁

```
B1(85行,极简) → B2(+对数螺旋+OBJ) → B3(+F-S标架,Rodrigues旋转)
  → B4(+3实例阵列+3D截面) → B5(+数值TNB+2.53调优)
  → B6(+OOP类架构+NURBS+CSV) → B7(+DXF双轨导出)
  
PKS吸收了B3的F-S方法、B5的数值TNB、B7的DXF导出
```

---

## C. 蛋形→Sin波进化 (9 files)

### 演化时间线

| 阶段 | 文件 | 核心突破 | PKS对应 |
|------|------|---------|---------|
| **C1 基础投影** | `螺旋蛋公式转成sin波 正.py` | 蛋形→sin波一维展开 | `07_archived/01_basic...` |
| **C2a 摆线调制** | `螺旋蛋公式转成sin波 正 -摆线.py` | 外摆线调制(死胡同) | PKS无等价 |
| **C2b 对数衰减** | `螺旋蛋公式转成sin波 负 -ln2开始递减.py` | amp=1/((1+t/2π)·ln(n+1))粘性耗散 | `07_archived/01_basic...` |
| **C3 卍字符** | `螺旋蛋公式转成sin波 负 ...万字符.py` | 衰减+旋转+阵列→卍字形 | `07_archived/04_swastika.py` |
| **C4 黄金比锥** | `重点-螺旋蛋逐渐变圆...万字符.py` | 动态k(t),b(t)使蛋逐渐变圆 | `03_simulation/hyperbolic_phi_...` |
| **C5 3D阴阳** | 阳/阴/阴阳合一3个文件 | 2^n白银比+φ^n黄金比+3D | `03_simulation/`中完全等价 |
| **C6 多谐波** | `不同n组蛋公式转成sin波.py` | 7节点2^n谐波级联 | `schauberger_egg_family.py` |
| **C7 混合谐波** | `不同n组蛋公式转成sin波 黄金比加2n次方.py` | Fibonacci(b)+2^n(k)混合 | `egg_octave_family.py` |

> **注意**: C5中的阳/阴/阴阳合一3个文件与PKS `03_simulation/` 中对应文件逐行代码等价，未复制入此档案。

---

## D. 舒伯格锥体与涡旋 (7 files)

| 文件 | 核心内容 | PKS等价 |
|------|---------|---------|
| `vortexSchauberger.py` | 斐波那契高度序列涡旋(r=a/(x+1)) | 无直接等价 |
| `vortexSchauberger_log.py` | 对数高度涡旋(2π·log(i)) | 概念呼应漏斗z=ln(t)\ln(φ) |
| `vortexSchaubergerlogvsfib.py` | 对数vs斐波那契高度对比 | 无 |
| `schauberger水龙头.py` | 舒式水流设计 | 无 |
| `schauberger-gini.py` | Gini指数分析 | 无 |
| `4个舒伯格公式花洒.py` | 4公式花洒设计 | 无 |
| `vortextubeschuaberger.py` | 涡旋管数值模拟 | 无 |

---

## E. 谱方法与场约束 (6 files)

| 文件 | 核心突破 | PKS等价 |
|------|---------|---------|
| `anu蛋形场约束曲线.py` | Chebyshev+FEM+BEM+CG曲率优化 | `egg_3d_spiral.py`(精神等价) |
| `anu蛋形+椭圆场约束曲线.py` | **蛋形-圆环对偶性发现** | PKS无等价(独特拓扑视角) |
| `anu蛋形场约束曲线3.py` | 三阶场约束扩展 | 无 |
| `anu3d曲线.py` | 基础3D Anu曲线 | 无 |
| `舒伯格蛋Die Ei-Kurve -蛋螺旋 缩放sqrt(n).py` | √n缩放方案 | 无 |

---

## 核心演化洞察

1. **从几何直觉到解析公式**: A1(五边形画图)→A3(t-参数化)→A5(解析x(t),y(t))
2. **从2D旋转到Frenet-Serret**: B2(简单2D旋转)→B3(完整3D标架)
3. **从单蛋到蛋形族**: C1(单个蛋)→C6(7节点谐波)→C7(Fibonacci/2^n混合)
4. **从脚本到模块**: A6(交互式170行)→`egg_curve.py`(结构化dataclass)
5. **从美学到数学**: C2a摆线(视觉实验)→C4黄金比(精确公式)→C5(NS方程联系)

---

*整理时间: 2026-05-28*
*数据来源: E:\pythonProject\pythonProject\program\ (2025年8月25日-9月1日)*
