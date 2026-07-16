# 物理模拟 (Physics Simulations)

> **来源**: http://www.bugman123.com/Physics/index.html
> **千禧难题关联**: Navier-Stokes(波方程/连续介质力学)、Yang-Mills(量子力学/量子场论)

---

## 一、量子力学

### 2D Schrodinger波粒模拟
- **方程**: Schrodinger波动方程
- **方法**: Crank-Nicolson + 时间分裂法
- **场景**: 双缝干涉, 晶格(Lattice), 圆柱(Cylinder), 搅拌(Stir)
- **外部参考**: Advanced Visual Quantum Mechanics, Dennis Hejhal(双曲空间量子本征函数 - 黎曼猜想相关!)
- **千禧难题**: 量子力学是Yang-Mills理论的基础

### 氢原子电子轨道 (2D截面)
- **公式**:
  ```
  P = 4*pi*r^2 * psi_r^2 * psi_theta^2
  psi_r = e^(-rho) * rho^l * L_{n-1-l}^{2l+1}(rho)
  psi_theta = Y_lm(theta, phi)
  rho = 2r/n
  ```
- **包含**: Laguerre多项式 L(), 球谐函数 Y_lm

### 氢4f电子轨道 (3D体素)
- **方法**: 体素渲染(Krzysztof Marczak技术), DF3密度文件
- **体积**: POV-Ray internal函数, subsurf scattering
- **千禧难题**: 量子轨道是量子场论的原型

### 球形膜振动 (球谐函数)
- **公式**: SphericalHarmonicY(8, 4, theta, phi)
- **应用**: 量子力学角动量、分子轨道

### 圆膜第31阶振动
- **公式**: J_3(k_43 r) cos(3*theta)
- **频率比**: f_31/f_1 = 6.74621
- **数学**: Bessel函数

---

## 二、广义相对论

### 地球黑洞模拟
- **概念**: Schwarzschild半径(R_s = 2GM/c^2), 光子球(1.5*R_s)
- **内置求解**: Schwarzschild测度微分方程, 4阶Runge-Kutta
- **效果**: 引力透镜, 爱因斯坦环, 光子球

### 爱因斯坦环 (弱场近似)
- **原理**: 广义相对论引力透镜的简化模型

### 光子球
- **方法**: 4阶Runge-Kutta积分Schwarzschild测度
- **关键发现**: 光子球半径 = 1.5 * Schwarzschild半径
- **图片来源**: https://www.bugman123.com/Physics/BlackHoleEquation.gif

### 狭义相对论模拟
- **概念**: Lorentz收缩, 相对论畸变, 多普勒效应
- **外部参考**: Space Time Travel, Penrose-Terrell旋转

---

## 三、电磁学

### 螺线管磁场
- **方程**: Biot-Savart定律(2D点源叠加)
- **渲染**: Mathematica DensityPlot(磁场密度)
- **代码**: https://www.bugman123.com/Physics/Solenoid.zip

### 马蹄形磁铁
- **方法**: Biot-Savart定律
- **场景**: 同极排斥/异极吸引, 平移/旋转

### 磁性台球
- **物理**: 均匀磁化球体外部磁场
- **公式参考**: 磁力+扭矩(Wikipedia)
- **协作**: Daniel Walsh磁化球网络

---

## 四、经典力学与振动

### N节摆 (Lagrangian力学)
- **方法**: Lagrangian + 4阶Runge-Kutta
- **混沌**: 鞭梢效应(Whip), 链(Chain)

### 双摆与三摆
- **方法**: Lagrangian + 4阶Runge-Kutta
- **混沌**: 典型的混沌动力系统

### 球面摆
- **方法**: Lagrangian + 4阶Runge-Kutta
- **相关**: 磁摆分形

### 树木模拟 (风中)
- **方法**: 同N节摆算法, 多分支

### 布模拟
- **方法**: 弹簧-质量网络模型
- **参考**: Hugo Elias布料教程, Pixar研究

### 阻尼弦振动
- **方法**: 分离变量法解析解
- **公式**: 波方程分离变量

---

## 五、碰撞与多体

### 台球模拟
- **工具**: Mathematica(C#/POV-Ray)
- **发现**: 30mph可清台, 偏离中心开球效果最佳

### 台球分形 (100万局统计)
- **可视化**: 开球速度/角度分形图案
- **图片**: https://www.bugman123.com/Physics/PoolFractal-large.jpg

### 3D碰撞 (无摩擦弹跳球+重力)
- **参考**: Box2D, Phun, Crayon Physics

### 银河引力模拟 (N体)
- **方程**: 牛顿万有引力定律
- **场景**: 单星系, 星系对, 星系碰撞
- **3D模型**: https://www.bugman123.com/3D/Galaxy.html
- **参考**: GADGET SPH, Volker Springel, Millennium Simulation

---

## 六、光学

### 雨滴折射与色散
- **方程**: Snell定律 n1 sin(theta1) = n2 sin(theta2), Fresnel反射系数
- **代码**: https://www.bugman123.com/Physics/Raindrop.zip
- **效果**: 彩虹形成

### 钻石折射与色散
- **方程**: Sellmeier方程(波长依赖折射率)
- **标准**: Marcel Tolkowsky理想钻石切工

### 水焦散
- **方法**: 频率滤波随机噪声 + 光子映射(Henrik Jensen)
- **参考**: Phong着色

### 夫琅禾费圆孔衍射
- **公式**: i(rho) = (2*pi*a*J_1(k*a*rho)/(k*rho))^2
- **验证**: 绿激光单缝衍射实验

---

## 七、弦理论与高维物理

### Calabi-Yau流形3D截面
- **方程**: 五次Calabi-Yau流形
- **代码**: https://www.bugman123.com/Physics/Calabi-Yau.zip
- **千禧难题**: ***** Yang-Mills理论与Calabi-Yau紧化
- **外部参考**: The Elegant Universe(NOVA), Andrew Hanson, Stewart Dickson

---

## 八、其他

### 光晕轨道 (Lagrange点L4)
- **方法**: 限制三体问题L4点周围的小振幅轨道

### 瑞利表面波
- **方程**: 地震波, 海洋波
- **代码**: 改编自Daniel Russell Mathematica代码

### 波干涉
- **概念**: 双源波叠加(双缝光干涉类比)

### 放大镜
- **光学**: 折射与色散, 抛物面交叠

---

## 九、与千禧难题的关联

### Yang-Mills理论与质量间隙
- **氢原子轨道/球谐函数**: 量子力学基础, Yang-Mills理论中使用
- **Calabi-Yau流形**: 弦理论紧化流形, Yang-Mills超对称
- **Schrodinger方程**: 量子场论的基本方程

### Navier-Stokes
- **波动方程**: NS方程中的波动现象
- **阻尼弦/膜振动**: 连续介质力学基础
- **银河引力模拟**: 天体物理流体动力学(N体SPH)

### 黎曼猜想
- **Hejhal量子本征函数**: 双曲空间中的量子混沌与Zeta零点
- **Bessel函数/特殊函数**: L-函数理论的核心工具

---

*文件大小: 约4KB*
