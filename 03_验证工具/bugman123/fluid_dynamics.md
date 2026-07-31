# 流体动力学模拟 (Fluid Dynamics Simulations)

> **来源**: http://www.bugman123.com/FluidMotion/index.html
> **千禧难题关联**: ***** 极高 - Navier-Stokes方程存在性与光滑性

---

## 一、粘性不可压Navier-Stokes方程模拟

### 1. Driven Cavity（有限体积法）
- **方程**: 稳态不可压粘性层流NS方程
- **方法**: 有限体积法(FVM), SIMPLE类迭代
- **参数**: 雷诺数 Re=1000, 松弛因子=0.4
- **渲染**: Mathematica ContourPlot（流线+涡量等值线）
- **参考**: Ghia et al. 基准结果
- **千禧难题**: 经典NS验证基准算例

### 2. Driven Cavity（涡量-流函数ADI方法）
- **方程**: 非稳态不可压粘性层流涡量输运方程
- **方法**: 有限差分法(FDM), 交替方向隐式(ADI)
- **参数**: Re=1000
- **渲染**: ListContourPlot(流函数)
- **Fortran代码参考**: Zheming Zheng

### 3. Von Karman涡街
- **方程**: 非稳态不可压粘性层流NS方程
- **方法**: 傅里叶谱方法 + Jos Stam稳定流体方法(半拉格朗日对流+涡扩散)
- **参数**: mu=0.001（物理粘性）
- **渲染**: ListDensityPlot(涡量, Hue区分方向)
- **千禧难题**: 层流涡脱落是理解转捩为湍流的关键
- **Jos Stam参考代码**: http://www.acm.org/jgt/papers/Stam01/solver.html

### 4. Jet
- **方程**: 不可压NS方程
- **方法**: Jos Stam稳定流体方法(2003 GDC论文)
- **C++代码**: http://www.dgp.toronto.edu/people/stam/reality/Research/zip/CDROM_GDC03.zip
- **千禧难题**: 射流是研究湍流转捩的重要流动构型

---

## 二、无粘流动 (Euler方程)

### 5. 1D激波管 (Shock Tube)
- **方程**: 可压缩无粘Euler方程(一维)
- **方法**: 有限体积法, Jameson-Schmidt-Turkel(JST)中心格式 + 人工粘性, Runge-Kutta时间步进
- **渲染**: ListPlot(密度/压力), POV-Ray动画
- **千禧难题**: 可压缩Euler方程的激波结构是NS方程研究的简化模型

### 6. 2D Euler方程涡动力学
- **方程**: 2D不可压无粘Euler方程(涡量守恒)
- **方法**: 点涡Biot-Savart叠加, Adams-Bashforth多步法
- **参数**: rcore=0.1(涡核心平滑)
- **代码**: https://www.bugman123.com/FluidMotion/Euler.txt (Matlab)
- **数学参考**: Stephen Montgomery-Smith论文

---

## 三、势流 (Potential Flow)

### 7. Joukowski翼型
- **方程**: 无粘不可压势流, 保角映射(Joukowski变换)
- **条件**: Kutta条件(尖后缘), 环量
- **渲染**: ContourPlot(流线), DensityPlot(压力/伯努利)
- **参数**: 攻角可调

### 8. NACA翼型
- **方法**: 涡板法(线性分布涡强度), 离散涡板+线性代数方程组
- **渲染**: ListPlot(压力系数Cp), DensityPlot(压力场)

### 9. 扑翼 (Flapping Wing)
- **方法**: 涡板法, Alan Lai Fortran代码改编
- **千禧难题**: 非定常空气动力学

### 10. Magnus效应/曲球
- **方法**: 解析势流绕旋转圆柱, Runge-Kutta 4阶跟踪流体质点
- **渲染**: ContourPlot(流线), ListDensityPlot(分形图案)

### 11. 周期稳态涡 (Stagnation Point Flow)
- **方法**: 无粘势流背景叠加周期涡, Runge-Kutta跟踪路径线

---

## 四、涡动力学

### 12. 不稳定涡丝 (Vortex Filaments)
- **方程**: 不可压无粘势流, Biot-Savart定律(涡段)
- **参数**: 涡核尺寸rcore（平滑奇点）
- **渲染**: POV-Ray动画, Mathematica Graphics3D线框

### 13. 跳跃气泡环 (Leap-Frogging Bubble Rings)
- **原理**: 涡环相互作用——前环收缩加速、后环扩张减速
- **方法**: 涡环运动解析解/简化涡动力学

### 14. 跳跃涡 (2D势流)
- **方法**: 2D点涡叠加, Runge-Kutta 4阶
- **涡核心平滑**: 指数衰减函数
- **渲染**: ListDensityPlot(颜色=Arg[z], Sign[Im[z]])

### 15. Kelvin-Helmholtz不稳定性波
- **方法**: 涡团法(vortex blob), 周期点涡, 预测-校正积分
- **参数**: rcore(涡团尺寸, 涡粘作用)
- **渲染**: ListPlot(涡位置), ContourPlot(流线+路径线)
- **Fortran参考**: Zheming Zheng周期性点涡程序

---

## 五、粒子方法

### 16. 2D SPH (光滑粒子流体动力学)
- **方程**: 可压弱可压SPH, 状态方程 p = k(rho - rho_0)
- **方法**: SPH插值, 显式时间积分(leapfrog/Euler)
- **参数**: 人工粘性系数 mu=0.2
- **千禧难题**: SPH是无网格方法的代表, 处理自由表面流动
- **参考**: Maciej Matyka Fluid v1.0

### 17. 3D SPH (液滴冲击/皇冠)
- **方程**: 3D可压SPH + 人工粘性
- **渲染**: POV-Ray高质量光线追踪
- **千禧难题**: 3D自由表面复杂流动

---

## 六、其他方法

### 18. 水波纹 (Water Ripple)
- **方程**: 线性波动方程 d^2u/dt^2 = c^2 nabla^2 u, 含阻尼项 b=5
- **方法**: 有限差分法(FDM), Dirichlet边界(实际建议Neumann)
- **渲染**: Mathematica ListPlot3D(无网格)

### 19. Schwarz-Christoffel流
- **方法**: 复变函数保角映射——半平面到阶梯+点涡
- **渲染**: Graphics line grid(变形网格)

### 20. 超音速流 (CFL3D)
- **模型**: 3D RANS (Reynolds-Averaged Navier-Stokes)
- **湍流模型**: Spalart-Allmaras或k-omega SST
- **可视化**: Tecplot 360(马赫数云图)

### 21. 通道流 (Fluent)
- **模型**: RANS湍流模型
- **工具**: Fluent + Gambit网格 + Mathematica后处理

---

## 七、核心数值方法汇总

| 方法 | 类型 | 应用场景 |
|------|------|----------|
| **有限体积法(FVM)** | 欧拉方法 | Driven Cavity, 激波管 |
| **有限差分法(FDM)** | 欧拉方法 | 涡量-流函数ADI, 水波纹 |
| **涡团法/点涡法** | 拉格朗日方法 | KH不稳定性, 涡动力学 |
| **SPH** | 拉格朗日无网格 | 自由表面, 液滴冲击 |
| **半拉格朗日** | 混合方法 | 稳定流体(Stam), Von Karman |
| **谱方法(Fourier投影)** | 欧拉方法 | 去散度(Von Karman) |
| **涡板法** | 边界方法 | 翼型, 扑翼 |
| **保角映射** | 解析方法 | Joukowski, Schwarz-Christoffel |
| **JST格式** | 有限体积 | 激波管(可压缩Euler) |

---

## 八、湍流模型

| 模拟 | 湍流处理 |
|------|----------|
| Driven Cavity | 层流, Re=1000(无湍流模型) |
| Von Karman | 层流, mu=0.001 |
| SPH | 人工粘性(数值/亚格子型) |
| 激波管 | 人工粘性(激波捕捉, 非物理湍流) |
| CFL3D | RANS(SA或SST湍流模型) |
| Fluent | RANS湍流模型 |
| 其余 | 无粘/层流 |

---

## 九、与Navier-Stokes千禧难题的关联

### 核心验证工具
1. **Driven Cavity**: 标准基准算例, Re=1000 — 验证NS数值求解器
2. **Von Karman涡街**: 层流到湍流转捩的入口点研究
3. **Kelvin-Helmholtz不稳定性**: 剪切流转捩机制
4. **1D激波管**: 可压缩流动基础
5. **SPH**: 无网格方法处理复杂边界和自由表面

### 研究潜力
- 将这些简化模型扩展到高雷诺数湍流
- SPH方法可研究Navier-Stokes方程的正则性问题
- 涡动力学方法提供NS方程的拉格朗日视角

---

*文件大小: 约5KB*
