# 双曲几何 (Hyperbolic Geometry)

> **来源**: http://www.bugman123.com/Hyperbolic/index.html
> **千禧难题关联**: 黎曼猜想（双曲几何与自守形式、L-函数零点的谱联系）

---

## 一、(12,4) Poincare球

### 基本信息
- **日期**: 2011/10/11 (POV-Ray版)
- **渲染**: 3D双曲空间的共形投影——4个十二面体汇聚在每个顶点
- **数学**: 双曲空间(H^3), sphairahedron(球面构成的多面体在欧氏空间的投影)
- **内部视图**: 光线在双曲十二面体(二面角=90度)内折射
- **千禧难题**: Poincare球是3D双曲空间的共形模型，与Rankin-Selberg方法、自守L-函数有关
- **海报**: http://www.zazzle.com/12_4_poincare_ball_poster-228109456565939376

### 相关链接
- Vladimir Bulatov: 3D双曲平铺论文
- Jos Leys: 3D双曲镶嵌画廊
- Jeff Weeks: Curved Spaces 3D程序
- Charlie Gunn: Not Knot视频

---

## 二、(7,3) Poincare双曲平铺

### 核心公式
```
n = 7; m = 3;
dt = 2Pi/n; dtm = 2Pi/m;
r = 1.0/(1 - Sin[dt/2]/Cos[dtm/2]);
R = r Cos[(dt + dtm)/2]/Cos[dtm/2];
```

### 生成方法
- **反演(Homography)矩阵**:
  ```
  ToMatrix[z_, r_] := (I/r) {{z, r^2 - z Conjugate[z]}, {1, -Conjugate[z]}};
  homography[{{a_,b_},{c_,d_}}, z_] := (a z + b)/(c z + d);
  ```
- **算法**: 初始3个反演矩阵 -> 群运算(Tlist) -> 递归生成整个平铺

### 可视化变体
- **表面纽结**: 多面体棱边沿测地线编织
- **气泡**: 120度相交圆(仅(7,3)型)
- **编织/环/辫子**: 多面体对称编结
- **球纹理映射**: push forward / pull back方法

---

## 三、共形映射变形

### Poincare (7,3)平铺的变形

| 映射类型 | 形状 | 公式参考 |
|----------|------|----------|
| Murl (多弧) | 多弧花瓣形 | Zueuk deviantart |
| 环形 | Ringworld | Jos Leys |
| 正方形 | Quincuncial map (Peirce投影) | Wikipedia |
| 五边形 | 规则五边形保角映射 | PhysicsForums |
| 心形 | 心形保角映射 | Gadl/Flickr |

### Poincare (6,4)平铺的变形

- **螺旋心形/硅藻**: 详细子页面 https://www.bugman123.com/Hyperbolic/SpiralDiatom/index.html
- **Drost Effect**: Jos Leys 无限递归

### 共形映射数学
- Schwarz-Christoffel映射: 将上半平面映射到多边形内部
- 超几何函数: 积分表达式

---

## 四、双曲十二面体

### 基本信息
- **日期**: 2009/9/24 (新版)
- **工具**: Mathematica 4.2, POV-Ray 3.6.1 (isosurface + recursion)
- **数学**: 二面角可调(72度->90度), 双曲空间八面体蜂巢结构
- **代码**: https://www.bugman123.com/Hyperbolic/HyperbolicDodecahedron.zip

### 镜像内部版本
- **双曲版**: 90度二面角, 光线在20个镜面间无限次反射
- **欧几里得版**: 普通十二面体(116.57度二面角), 单面镜

---

## 五、Breather伪球面

### 参数化公式
```
d = a * ((w * Cosh[a*u])^2 + (a * Sin[w*v])^2)
x = -u + 2*w^2*Cosh[a*u]*Sinh[a*u]/d
y = 2*w*Cosh[a*u]*(-w*Cos[v]*Cos[w*v] - Sin[v]*Sin[w*v])/d
z = 2*w*Cosh[a*u]*(-w*Sin[v]*Cos[w*v] + Cos[v]*Sin[w*v])/d
其中 w = Sqrt[1 - a^2]
```

- **数学**: 恒负曲率 -1, Kuen曲面
- **代码**: https://www.bugman123.com/Hyperbolic/Breather.zip
- **AutoLisp**: https://www.bugman123.com/Hyperbolic/Breather.lsp
- **千禧难题**: 伪球面是双曲几何在R^3中的嵌入，与黎曼Zeta函数的Hilbert-Polya猜测有关

---

## 六、双曲镶嵌（恐龙图案）

### (6,4)恐龙铺排
- **工具**: AutoCAD 2000, AutoLisp, Adobe Photoshop
- **方法**: 用反同调变换将恐龙图案递归映射到庞加莱圆盘

---

## 七、(3,∞)理想三角形铺排

### 基本信息
- **特征**: 所有角在圆盘边界趋于0
- **生成**: 初始3个反演矩阵递归
- **上半平面图**: 另一个保角模型

### 数学联系
- **理想三角形**(3,inf) - 双曲平面最对称的铺排
- **M.C. Escher**: Circle Limit III, Reducing Lizards

---

## 八、双曲纹理映射

### Push Forward方法
- 将庞加莱圆盘纹理映射到球面
- Mathematica notebook: http://egl.math.umd.edu/software/HyperbolicTextureRayTracing.zip
- C++代码: https://www.bugman123.com/Programs/EGL.zip

### Pull Back方法
- 从3D曲面反算到庞加莱圆盘

---

## 九、POV-Ray (3,∞)理想铺排渲染

- **代码**: https://www.bugman123.com/Hyperbolic/Poincare.zip
- **方法**: POV-Ray isosurface渲染庞加莱平铺

---

## 十、Hyperboloid (双曲菱面体)

### POV-Ray公式
```
quadric{<1,1,-1>,<0,0,0>,<0,0,0>,1}
```
- **代码**: https://www.bugman123.com/Hyperbolic/Hyperboloid.zip
- **参考**: Xiao Gang代数曲面画廊

---

## 十一、外部工具

| 工具 | 用途 | 链接 |
|------|------|------|
| HypEngine | 3D双曲迷宫 | Bernie Freidin |
| MagicTile | 双曲魔方 | Roice Nelson |
| Curved Spaces | 3D多连通空间可视化 | Jeff Weeks |

---

## 十二、与千禧难题的关联

### 黎曼猜想 (核心)
- **双曲几何与谱理论**: 双曲空间上的拉普拉斯算子的谱与黎曼Zeta函数零点的直接联系!
- **Selberg迹公式**: 双曲曲面上的测地线长度谱与拉普拉斯本征值谱之间的对偶性——与黎曼Zeta零点的显式公式惊人相似
- **量子混沌**: 双曲曲面上的量子台球——BGS猜想说量子混沌系统的能级间距遵循随机矩阵理论(GUE)，与黎曼Zeta零点相同!
- **Hejhal/量子本征函数**: 已备注于physics_sims.md的Schrodinger模拟部分
- **自守形式**: (7,3)平铺使用的反同调变换群就是模群Gamma(2,3,7)的离散子群

### Yang-Mills
- CCSFT(共形场论)与双曲3-流形的联系
- 双曲空间中的规范场

### BSD
- 模形式与（超）椭圆曲线在双曲几何中的嵌入
- (3,inf)理想三角形的理想边界点对应于Q∪inf——与模曲线的cusp点对应

---

## 十三、关键贡献者

| 贡献者 | 贡献 |
|--------|------|
| Vladimir Bulatov | 3D双曲平铺理论 |
| Jos Leys | Ringworld, 双曲画廊, Drost Effect |
| Matthias Weber | 双曲多面体数学 |
| Jeff Weeks | Curved Spaces程序 |
| Charlie Gunn | Not Knot双曲空间视频 |
| M.C. Escher | Circle Limit系列 |
| Roice Nelson | MagicTile, Gravitation3D |
| Bernie Freidin | HypEngine双曲迷宫 |

---

*文件大小: 约4KB*
