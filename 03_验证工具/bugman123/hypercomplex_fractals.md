# 超复分形 (Hypercomplex Fractals)

> **来源**: http://www.bugman123.com/Hypercomplex/index.html
> **千禧难题关联**: 黎曼猜想（高维复动力系统）、Yang-Mills（四元数/Hopf纤维化）

---

## 一、3D Mandelbulb集

### Quadratic Mandelbulb (White/Nylander公式)
- **日期**: 2009/7/3
- **基于**: Daniel White的triplex平方公式
- **三角函数形式**:
  ```
  {x,y,z}^2 = r^2 * {cos(theta)cos(phi), sin(theta)cos(phi), -sin(phi)}
  r = sqrt(x^2+y^2+z^2), theta = 2*atan2(y,x), phi = 2*asin(z/r)
  ```
- **非三角形式**:
  ```
  r = sqrt(x^2+y^2+z^2)
  a = 1 - z^2/(x^2+y^2)
  {x,y,z}^2 = {(x^2-y^2)*a, 2*x*y*a, -2*z*sqrt(x^2+y^2)}
  ```
- **渲染方法**: Voxel marching(Mathematica), POV-Ray isosurface, C++ path tracing(GI), Volumetric subsurface scattering
- **千禧难题**: 3D复动力系统研究, 黎曼Zeta零点可视化新维度

### Power-8 Mandelbulb (8阶)
- **通用幂次公式**:
  ```
  {x,y,z}^n = r^n * {cos(theta)cos(phi), sin(theta)cos(phi), -sin(phi)}
  r = sqrt(x^2+y^2+z^2), theta = n*atan2(y,x), phi = n*asin(z/r)
  ```
- **距离估算(DE)**: d = 2*r*log(r)/dr/4 (加速渲染)

### Positive Z-Component变体
- **改进**: 去除z分量负号
  ```
  {x,y,z}^n = r^n * {cos(theta)cos(phi), sin(theta)cos(phi), sin(phi)}
  ```

### Triplex代数运算符
- **乘法** (交换但不结合):
  ```
  a = 1 - z1*z2/(r1*r2)
  {x1,y1,z1} x {x2,y2,z2} = {a*(x1*x2-y1*y2), a*(x2*y1+x1*y2), r2*z1+r1*z2}
  ```
- **已定义**: 除法、幂、开方、指数、对数、三角函数

---

## 二、3D Juliabulb集

### 二次Juliabulb
- **定义**: triplex平方的Julia集

### 4阶/6阶/10阶Juliabulb
- **一般n次幂根**: n^2个唯一有效根

### Lambdabulb
- **迭代**: p = TriplexMult[c, p - TriplexPow[p, 4]]

### 3D Glynn Juliabulb
- **幂次**: 1.5
- **根数量**: x<0时>2, x>0时>1, z^2>x^2+y^2圆锥区域3根
- **敏感性**: 初始种子值极度敏感

---

## 三、四元数分形 (Quaternion)

### 4D Quaternion Mandelbrot集 ("Mandelquat")
- **公式**:
  ```
  {x,y,z,w}^2 = {x^2-y^2-z^2-w^2, 2xy, 2xz, 2xw}
  ```
- **特性**: 轴对称(旋转对称), 视觉上相对无趣
- **变体**: 8阶幂版本

### 4D Quaternion Julia集
- **公式**: 同quaternion平方
- **渲染**: Phong shading(Mathematica), POV-Ray内置julia_fractal

### 逆4D Quaternion Julia集
- **方法**: IIM——平方根有2个值(每步2倍增长)
- **规模**: 20亿点/5亿小球渲染
- **代码**: https://www.bugman123.com/Hypercomplex/Julia-Quaternion-inverse

---

## 四、Hopf纤维化分形

### 4D Hopfbrot集
- **基础**: Hopf映射(4D球面无极点映射到3D)
- **4个3D切片**: wc=0(含Mandelbulb), zc=0, yc=0(Christmas Tree), xc=0
- **千禧难题**: ***** Hopf纤维化是Yang-Mills规范理论的核心几何结构

### 4D Mandelbulb集
- **公式**: 三个连续4D旋转
  ```
  {x,y,z,w}^2 = R_xy(2theta)R_xz(2phi)R_xw(2psi){r^2,0,0,0}
  = r^2{cos(2psi)cos(2phi)cos(2theta), cos(2psi)cos(2phi)sin(2theta), -cos(2psi)sin(2phi), sin(2psi)}
  ```
- **简化**: {(x^2-y^2)*b, 2xy*b, -2*r2*z*a, 2*r3*w}
  - a=1-w^2/r3^2, b=a*(1-z^2/r2^2), r2=sqrt(x^2+y^2), r3=sqrt(x^2+y^2+z^2)

---

## 五、Bicomplex数分形 ("Tetrabrot")

### 4D Bicomplex Mandelbrot集
- **公式**:
  ```
  {x,y,z,w}^2 = {x^2-y^2-z^2+w^2, 2(xy-zw), 2(xz-yw), 2(xw+yz)}
  ```
- **外观**: 类似铋晶体
- **应用**: TetraBrot Explorer深度缩放程序

### 4D Bicomplex Julia集 / 逆Bicomplex Julia集
- **平方根**: 4个根(每步4倍增长)

---

## 六、3D Mandelbrot/Tricorn混合

### Mandelbrot-Tricorn
- **公式**:
  ```
  {x,y,z}^2 = {x^2-y^2-z^2, 2xy, -2xz}
  ```
- **特性**: Mandelbrot + Mandelbar(Tricorn)结合
- **变体**: 3-8次幂高阶版本

---

## 七、各数学家公式变体

### Rudy Rucker公式
- **公式** (phi使用atan2(z,x)而非asin(z/r)):
  ```
  {x,y,z}^n = r^n{cos(theta)cos(phi), sin(theta)cos(phi), sin(phi)}
  r=sqrt(x^2+y^2+z^2), theta=n*atan2(y,x), phi=n*atan2(z,x)
  ```
- **变体**: 8次幂版本

### Christmas Tree Mandelbrot集
- **公式** (球面等距旋转):
  ```
  {x,y,z}^n = r^n{cos(theta), sin(theta)cos(phi), sin(theta)sin(phi)}
  r=sqrt(x^2+y^2+z^2), theta=n*acos(x/r), phi=n*atan2(z,y)
  ```
- **特性**: z=0时退化为标准2D Mandelbrot

### David Makin公式
- {x,y,z}^2 = {x^2-y^2-z^2, 2xy, 2(x-y)z}

### Bristorbrot (Doug Bristor)
- {x,y,z}^2 = {x^2-y^2-z^2, y(2x-z), z(2x+y)}

### Combo Mandelbrot集
- {x,y,z}^n = r^n{cos(theta)cos(phi), sin(theta)cos(phi), cos(theta)sin(phi)}
- **特性**: 结合forward method和reversed method

---

## 八、4D变体

### "Roundy" 4D Mandelbrot集
- {x,y,z,w}^2 = {x^2-y^2-z^2-w^2, 2(xy+zw), 2(xz+yw), 2(xw+yz)}
- **变体**: Minibrot (imax=21)

### "Squarry" 4D Mandelbrot集
- {x,y,z,w}^2 = {x^2-y^2-z^2-w^2, 2(xy+zw), 2(xz+yw), 2(xw-yz)}

### "Mandy Cousin" 4D
- {x,y,z,w}^2 = {x^2-y^2-z^2+w^2, 2(xy+zw), 2(xz+yw), 2(xw+yz)}

### 4D变体 v2
- {x,y,z,w}^2 = {x^2-y^2-z^2-w^2, 2(xy+zw), 2(xz-yw), 2(xw+yz)}

---

## 九、Mandelbox (非严格超复分形)

- **日期**: 2011/2/22
- **基于**: Tom Lowe公式
- **算法**:
  ```
  BoxFold[p]: |x|>1时折叠每个分量
  BallFold[r0,p]: 球折叠
  主迭代: p = scale * BallFold[r0, f*BoxFold[p]] + c
  ```
- **参数**: scale=2, r0=0.5, f=1

---

## 十、3D轨道陷阱

- **球体轨道陷阱**: 2D轨道陷阱的3D扩展
- **变体**: Mandelbulb版, Mandelbrot-Tricorn版, Roundy版

### 3D Pickover茎
- **方法**: 螺旋轨道陷阱, Triplex版, Bicomplex版

---

## 十一、其他特殊分形

### 3D Nebulabrot
- **方法**: Buddhabrot技术3D变体
- **渲染**: 20亿点, 体积渲染
- **变体**: Roundy, Triplex, Tricorn版本

### 4D Julibrot集
- **定义**: 所有可能Julia集的集合
- **特性**: Mandelbrot集是它的2D切片
- **3D切片**: 变化实部或虚部起始值

### Quadray Quaternion Julia集
- **方法**: 3D点->4D quaternion(四面体空间) -> quaternion Julia -> quadrays映射回3D -> isosurface

---

## 十二、渲染算法

| 算法 | 用途 |
|------|------|
| Voxel Marching | 深度图渲染 |
| Distance Estimation (DE) | 加速边界检测 |
| Path Tracing (Kajiya) | GI渲染(Monte Carlo积分) |
| Volumetric Subsurface Scattering | 体积次表面散射 |
| Phong Shading | 快速3D外观 |
| Inverse Julia Set Method | 点集生成 |
| MIIM | 剪枝优化逆迭代 |
| GPU Ray Tracing | GPU加速光线追踪 |

---

## 十三、与千禧难题的关联

### 黎曼猜想
- 超复分形是高维复动力系统的可视化，与黎曼Zeta函数的复平面动力学直接相关
- Bicomplex数和四元数是复数的两种不同高维推广
- Mandelbrot集轨道与黎曼Zeta零点分布的统计联系

### Yang-Mills理论
- **Hopf纤维化分形**: So(4)→So(3)的Hopf映射是Yang-Mills规范理论的核心数学结构
- **四元数分形**: 四元数与SU(2)规范群的关系
- **Calabi-Yau分形**: 已另见physics_sims.md

### Navier-Stokes
- 超复分形的多尺度自相似结构与湍流结构函数的相似性

---

## 十四、关键贡献者

| 贡献者 | 贡献 |
|--------|------|
| Daniel White (Skytopia) | 原始3D Mandelbulb公式 |
| Paul Nylander (bugman) | 本页面作者, Hybridean公式优化 |
| Krzysztof Marczak | 体积渲染技术, Mandelbulber |
| Tom Lowe | Mandelbox发明 |
| Iñigo Quilez | 距离估算/光线追踪 |
| David Makin | 多种4D变体公式 |
| Eric Baird | Mandelbrot-Tricorn建议 |
| Jos Leys | 超复分形画廊 |
| Dominic Rochon | Bicomplex数学 |

---

*文件大小: 约6KB*
