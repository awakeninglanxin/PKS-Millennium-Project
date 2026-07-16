# 分形生成工具 (Fractal Tools)

> **来源**: http://www.bugman123.com/Fractals/index.html
> **千禧难题关联**: 黎曼猜想（Mandelbrot集与Zeta零点的视觉联系）、BSD（数论分形）

---

## 1. Kleinian群极限集

### Double 1/15 Cusp Group
- **数学**: 矩阵生成元群论，反演/反射Moebius变换
- **参数**: ta = 1.958591030 - 0.011278560I; tb = 2; tab = 0.5(ta tb - Sqrt[ta^2tb^2 - 4(ta^2+tb^2)])
- **工具**: Mathematica 4.2, POV-Ray 3.6.1
- **代码**: https://www.bugman123.com/Fractals/DoubleCusp.zip
- **千禧难题**: Kleinian群与数论、自守形式的深层联系（黎曼猜想相关）
- **参考**: Indra's Pearls (David Mumford等)

### Quasifuchsian Limit Set
- **参数**: ta = tb = 1.91 + 0.05I
- **外观**: 蝴蝶形极限集
- **相关**: 3D version, sphairahedrons
- **千禧难题**: Fuchsian群与模形式、自守L-函数的联系

---

## 2. Mandelbrot集系

### 经典Mandelbrot集 (Escape Time Algorithm)
- **公式**: z_{n+1} = z_n^2 + c
- **参数**: 最大迭代=100, 逃逸半径=2, 视窗 xc:[-2,1], yc:[-1.5,1.5]
- **算法**: 逃逸时间算法(ETA)、连续逃逸时间(CET)、距离估算(DE)
- **代码**: Java Applet (https://www.bugman123.com/Fractals/Mandelbrot.html)
- **千禧难题**: Mandelbrot集边界与黎曼Zeta函数零点的统计性质有惊人相似

### Mandelbrot Pearls (轨道可视化)
- **方法**: 周期n=1..5轨道，导数条件 D[F[z],z] = Exp[I*theta]
- **角度步长**: Pi/18
- **千禧难题**: 轨道理论与动力系统的联系

### Nebulabrot (Buddbabrot 3D变体)
- **方法**: 20亿点累积渲染
- **颜色映射**: Hue2[Arg[#]/Pi, Min[Abs[#]/18,1]]
- **3D版本**: 体积渲染(volumetric subsurface scattering)

### Mandelbrot集高度场
- **算法**: 归一化迭代计数(NICA): cet = n + log_2(ln R) - log_2(ln|z|)

### 逆Mandelbrot集
- **方法**: 解F_n(0)=0的c根（Durand-Kerner同时求根法）
- **精度**: imax=8层, 2^(imax-1)=128个多项式根
- **千禧难题**: 多项式根分布与L-函数零点

---

## 3. Julia集系

### 二次Julia集
- **公式**: z_{n+1} = z_n^2 + c, c = -0.63 - 0.407I

### 三次Julia集
- **公式**: z_{n+1} = z_n^3 + c, c = -0.5 - 0.05I

### Glynn Julia集
- **公式**: z_{n+1} = z_n^{1.5} + c, c = -0.2
- **非整数幂**: 需要修改的逆迭代(MIIM)，种子值极度敏感

### 逆Julia集 (IIM/MIIM)
- **方法**: 逆迭代法 + 累计导数剪枝
- **2次幂**: 2个逆（每步2倍增长）
- **3次幂**: 3个逆
- **MIIM阈值**: dzmax=250

### Burning Ship分形
- **公式**: z_{n+1} = (|x_n| + i|y_n|)^2 - c
- **展开**: x_{n+1} = x_n^2 - y_n^2 + c_x, y_{n+1} = 2|x_n y_n| + c_y
- **参数**: 最大迭代250, xc:[1.71,1.8], yc:[-0.01,0.08]

---

## 4. 动力系统吸引子

### 磁摆奇异吸引子
- **方程** (NDSolve):
  z''(t) = sum_i [(z_i - z(t)) / (h^2 + |z_i - z(t)|^2)^(1.5)] - g z(t) - mu z'(t)
- **磁铁位置**: {sqrt(3)+i, -sqrt(3)+i, -2i}
- **参数**: h=0.25, g=0.2, mu=0.07, tmax=25
- **数值方法**: Beeman预测-校正法, dt=0.1
- **5磁铁版本**: 混沌边界分形

### Lorenz吸引子
- **方程**:
  x' = sigma(y-x), y' = rho x - xz - y, z' = xy - beta z
- **参数**: sigma=3, rho=26.5, beta=1
- **初值**: (0,1,1), t=0..100, dt=0.01
- **数值方法**: Runge-Kutta 4阶
- **代码**: https://www.bugman123.com/Fractals/LorenzAttractor.zip

### Clifford吸引子
- **方程**:
  x_{n+1} = sin(a*y_n) + c*cos(a*x_n)
  y_{n+1} = sin(b*x_n) + d*cos(b*y_n)
- **参数插值**: a:1.6->1.3, b:-0.6->1.7, c:-1.2->0.5, d:1.6->1.4

### Henon映射逃逸时间
- **方程**:
  x_{n+1} = 1 - a*x_n^2 + y_n
  y_{n+1} = b*x_n
- **参数**: a=0.2, b=1.01
- **逃逸半径**: >100, 最大迭代=1000

---

## 5. 迭代函数系统 (IFS)

### Barnsley蕨类
- **方法**: Digraph IFS, 概率: 3%, 73%, 13%, 11%
- **千禧难题**: IFS与测度论、分形维数

### Flame分形
- **方法**: 广义IFS + 非线性变体
- **权重**: w1=0.65, w2=0.29, w3=w4=0.03
- **渲染**: POV-Ray代码 (https://www.bugman123.com/Fractals/FlameFractal.zip)

---

## 6. L-系统 (Lindenmayer System)

### 2D树分形
- **参数**: 初始角度 Pi/2, r=1, 分支角 -Pi/6, +Pi/4, 缩放 0.8, 0.7, 深度12

### 3D树分形
- **参数**: 分支角 Ry[-Pi/4], 三分支旋转 0, 120度, 240度, 缩放 0.6, 深度8

### 体素3D树
- **体素数**: 1.75亿

---

## 7. 扩散限制凝聚 (DLA)

- **方法**: 随机游走, 种子圆环, 周期边界, 100x100图像, 360时间步
- **3D DLA**: 大量外部参考 (Andy Lomas, Mark Stock, Paul Bourke)
- **千禧难题**: DLA与随机过程、分形生长模型

---

## 8. 其他分形

### 多项式根分布
- **方法**: order=12, +/-1系数, n=275分辨率, Durand-Kerner同时求根
- **千禧难题**: 多项式根与黎曼Zeta零点的分布

### 分岔图 (Feigenbaum分形)
- **方程**: x_{n+1} = a*x_n*(1-x_n) (Logistic方程)
- **参数**: a:[2.8,4], 步长=0.01, 预热100次, 绘制100次

### Weierstrass函数
- **公式**: sum_{k=1..50} sin(pi*k^a*x)/(pi*k^a), a:[2,3]

### Newton-Raphson分形
- **公式**: z_{n+1} = z_n - f(z_n)/f'(z_n), f(z)=z^5-1, 最大迭代=30

### Wada盆地
- **方法**: 光线追踪(Wada Basin), 4个球体, 深度50, 光源{0,0,1}
- **代码**: https://www.bugman123.com/Fractals/WadaBasin.zip

### Apollonian Gasket
- **数学**: Descartes定理, 圆反演递归, 7层递归
- **3D版本**: Soddy-Gosset定理, 球体堆积
- **代码**: https://www.bugman123.com/Fractals/Apollonian.zip

### 分形皇冠 (Fractal Crown)
- **公式**: w = sum_{k=1..14} e^{i*(-a)^k*t} / a^{b*k}
- **参数**: a=5, b=log(2)/log(3)

---

## 9. 轨道陷阱 (Orbit Traps)

| 类型 | 方法 | 参数 |
|------|------|------|
| 圆形 | 陷阱半径=0.3, x=\|z\|^2/0.3^2 | -- |
| 日落蛾 | 图像"Picture.bmp"作陷阱 | 透明黑色 |
| 齿轮 | 齿轮图案映射 | -- |
| 黄金螺旋 | phi=(1+sqrt(5))/2, f[z]=18 Abs[r-Round[r]] | r=Log[\|z\|]/(4Log[phi])-Arg[z]/(2Pi) |
| Pickover茎 | f[z]=Min[Abs[{Re[z],Im[z]}]]/0.03 | 阈值=1 |

---

## 10. 纹理噪声

### 频率滤波随机噪声
- **方法**: 傅里叶变换滤波（高斯滤波器标准差0.025, n=275）

### Perlin噪声
- **方法**: 5倍频程, a=2, b=2, m=14, 三次插值
- **应用**: 地形、云、水、火、大理石、花岗岩

### Crackle分形 (Voronoi)
- **方法**: 100个随机节点, 第二近邻减最近邻距离

---

## 与千禧难题的具体关联

### 黎曼猜想
- Mandelbrot集的分形边界与黎曼Zeta函数零点的统计分布相似性
- Kleinian群的极限集与自守形式理论
- 多项式根分布可视化

### BSD猜想
- 椭圆曲线与模形式的双重性（通过纽结和镶嵌的拓扑直观）
- 数论分形的可视化

### Navier-Stokes
- 磁摆/混沌摆的奇异吸引子（与湍流吸引子类比）

---

*文件大小: 约6KB*
