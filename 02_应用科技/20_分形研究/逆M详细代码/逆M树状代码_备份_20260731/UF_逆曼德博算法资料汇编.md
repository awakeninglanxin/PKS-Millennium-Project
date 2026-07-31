# Ultra Fractal 逆曼德博 (Inverted Mandelbrot) 完整算法与资料汇编

> 来源: Ultra Fractal 官方论坛、帮助文档、API 参考、开发者社区
> 整理日期: 2026-07-12

---

## 1. 核心公式: 三种实现途径

### 途径一: 直接修改公式 (Otto Magus, 2015)

最简洁的实现——在迭代中直接用 `1/c` 代替 `c`:

```
Mandeldrop {
init:
  z = 1/#pixel
loop:
  z = z^2 + (1/#pixel)
bailout:
  |z| < 4
default:
  title = "Mandeldrop"
  center = (1.5, 0)
  magn = 0.5
  angle = 270
}
```

**数学原理**: 标准 Mandelbrot 的 `z = z² + c` 中, 将 `c` 替换为 `1/c` (`1/#pixel`)。初始 `z` 也设为 `1/c`。

**关键参数**: `center=(1.5,0)`, `magn=0.5`, `angle=270`(旋转使水滴立起)。

### 途径二: 精炼版 (aelah)

```plaintext
Mandeldrop {
init:
  z = (0, 0)
loop:
  z = sqr(z) + 1/#pixel
bailout:
  |z| <= @bailout
default:
  title = "Mandeldrop"
  param bailout
    caption = "Bailout value"
    default = 4.0
  endparam
}
```

**与途径一的差异**: z 初始化为 `(0,0)` 而非 `1/c`。bailout 参数化。

### 途径三: Inverse 变换 + 标准 Mandelbrot (官方推荐, 所有版本适用)

使用 Mapping 标签页添加 Inverse 变换到标准 Mandelbrot 公式:

```plaintext
mapping:
  center=1.15437880685/-0.040077532 magn=0.87348074 angle=-90
  transforms=1
transform:
  filename="Fractint.uxf" entry="Inverse" p_radius=1.0 p_center=0/0 p_usecenter=no
formula:
  maxiter=250 filename="Standard.ufm" entry="Mandelbrot"
  p_start=0/0 p_power=2/0 p_bailout=128
outside:
  transfer=sqrt filename="Standard.ucl" entry="Smooth" p_power=2/0 p_bailout=128.0
inside:
  transfer=none
```

**关键对比**: `p_bailout=128` (标准), `transfer=sqrt` (Smooth 平滑着色)。`angle=-90` 逆时针90度使水滴立起。

---

## 2. Inverse 变换的数学本质

### Official API 源码 (Standard.ulb)

```cpp
class Standard_Inverse(common.ulb:UserTransform) {
public:
  complex func Iterate(complex pz)
    if @usescreen
      return #center + @radius / (pz - #center)
    else
      return @center + @radius / (pz - @center)
    endif
  endfunc
default:
  param radius caption = "Radius" default = 1.0
  param center caption = "Center" default = (0, 0)
  param usescreen caption = "Use Screen Center" default = false
}
```

**数学公式**:
$$c_{\text{transformed}} = C + \frac{R}{c_{\text{original}} - C}$$

其中 $C$ 是反演圆心, $R$ 是反演半径。当 $C=0, R=1$ 时退化为标准反演 $c' = 1/c$。

### 视觉效果

- 分形从"内向外"翻转
- 原始中心点 → 被推到无穷远
- 无穷远处的点 → 被拉到中心附近
- 以出人意料的方式改变分形形状

---

## 3. UF 参数文件完整列表

### 3.1 Otto Magus 的 Mandeldrop 参数

```plaintext
mandeldrop {
fractal:
  title="mandeldrop" width=1024 height=768 layers=1
  credits="Otto;12/7/2015"
layer:
  caption="Background" opacity=100
mapping:
  center=0.01/0.12 magn=6
formula:
  maxiter=250 filename="om.ufm" entry="f462" f_fn=ident p_var=0/1.8
inside:
  transfer=none
outside:
  transfer=linear
gradient:
  smooth=yes index=0 color=8716288 index=100 color=16121855
  index=200 color=46591 index=300 color=156
opacity:
  smooth=no index=0 opacity=255
}
```

### 3.2 Ramblingsheep (Peter) 的彩色逆M参数

```plaintext
InvertedMandelbrotColouredForForum {
fractal:
  title="Inverted Mandelbrot Coloured for Forum" width=900 height=720
  layers=1 resolution=200 credits="Peter Shepheard;12/7/2015"
layer:
  caption="Background" opacity=100 method=multipass
mapping:
  center=1.004849/0 magn=0.4 angle=270 transforms=1
transform:
  filename="Standard.uxf" entry="Inverse" p_radius=1.0 p_center=0/0 p_usescreen=no
formula:
  maxiter=100 percheck=off filename="Standard.ufm" entry="Mandelbrot"
  p_start=0/0 p_power=2/0 p_bailout=1e20
inside:
  transfer=none
outside:
  density=2 transfer=linear solid=4286722382 filename="Standard.ucl"
  entry="Basic" p_type=Iteration
gradient:
  comments="Default Ultra Fractal gradient." smooth=yes rotation=-2
  index=123 color=368977 index=170 color=65278 index=298 color=156 index=-3 color=16384000
opacity:
  smooth=no index=0 opacity=255
}
```

**注意**: `p_bailout=1e20` (超大bailout), `angle=270`。

### 3.3 Velvet--Glove 的 UF 4.04 兼容版

```plaintext
Fractal1 {
fractal:
  title="Fractal1" width=364 height=480 layers=1
  credits="Frederik Slijkerman;7/23/2002"
layer:
  caption="Background" opacity=100
mapping:
  center=1.15437880685/-0.040077532 magn=0.87348074 angle=-90 transforms=1
transform:
  filename="Fractint.uxf" entry="Inverse" p_radius=1.0 p_center=0/0 p_usecenter=no
formula:
  maxiter=250 filename="Standard.ufm" entry="Mandelbrot" p_start=0/0
  p_power=2/0 p_bailout=128
inside:
  transfer=none
outside:
  transfer=sqrt filename="Standard.ucl" entry="Smooth" p_power=2/0 p_bailout=128.0
gradient:
  smooth=no rotation=43 index=0 color=3278080 index=182 color=13701632
  index=229 color=16777215 index=258 color=16777215 index=399 color=0
opacity:
  smooth=no index=0 opacity=255
}
```

---

## 4. 着色算法参考

### 4.1 UF 着色方法速查表

| UF 参数 | 着色类型 | 视觉效果 |
|:---|:---|:---|
| `transfer=linear` | 线性映射 | 基础色阶, 无平滑 |
| `transfer=sqrt` (entry="Smooth") | 平方根平滑 | 消除离散阶梯 |
| `transfer=log` | 对数映射 | 连续渐变 |
| `density=N` | 密度控制 | 颜色重复密度 |
| `entry="BinaryDecomposition"` | 二进制分解 | 黑白棋盘格交替 |
| `entry="Basic" p_type=Iteration` | 基础迭代着色 | 按迭代次数 |

### 4.2 Binary Decomposition 的 UF 实现位置

在 `Standard.ucl` 中作为 `entry="BinaryDecomposition"` 提供:

```plaintext
outside:
  transfer=sqr
  filename="Standard.ucl"
  entry="BinaryDecomposition"
  p_type="Type 1"
```

Type 1 = 按辐角的虚部正负交替着色。与棋盘格 XOR 等效。

### 4.3 Smooth (连续势能) 的 UF 实现

```plaintext
outside:
  transfer=sqrt
  filename="Standard.ucl"
  entry="Smooth"
  p_power=2/0
  p_bailout=128.0
```

---

## 5. 第三方参考实现

### Mitch Richling 的 C++ 实现

视口范围: `IM∈[-1.5, 4.25], RE∈[-2.875, 2.875]`, bailout=50, maxiter=1024。

```cpp
c = 1.0 / c;  // 反演变换
z = z^2 + c;  // 标准迭代
// 着色: csCColdeFireRamp::c(count * 15)
```

### StackOverflow Q&A 关键发现

扭曲根源: 不能做 `complex(1/x, 1/y)`——必须做复数除法 `1/complex(x,y)`:

```python
# 正确:
c = 1 / complex(real, imaginary)

# 错误 (产生扭曲):
c = complex(1/real, 1/imaginary)
```

---

## 6. 论坛讨论摘要 (2015-2019)

### 主题: Formula Question (2015年12月)
- **发起人**: Otto Magus — 寻求逆M的公式实现
- **Frederik Slijkerman (UF作者)**: 直接使用标准Mandelbrot公式 + Mapping标签添加Inverse变换
- **aelah**: 提供了精炼版 Mandeldrop 公式
- **Ramblingsheep (Peter)**: 分享了完整的彩色参数文件, 演示了Inverse变换的使用
- **Velvet--Glove**: 确认 Inverse 变换在 UF 4.04 (早于 Creative Edition) 就可用
- **版本兼容**: Express 版本不支持 Transformations; 直接写公式在所有版本可用

---

## 7. 完整映射参数速查

| 创作者 | center | magn | angle | bailout | 着色 |
|:---|:---|:---|:---|:---|:---|
| Otto Magus | 0.01/0.12 | 6 | — | 4 | linear |
| Peter Shepheard | 1.004849/0 | 0.4 | 270 | 1e20 | linear+Basic |
| Velvet--Glove | 1.154/-0.04 | 0.873 | -90 | 128 | Smooth(sqrt) |
| Mitch Richling | — | — | — | 50 | FireRamp |

---

## 8. 几何映射关系

逆M水滴边框的精确坐标 (基于心形体 $c(\theta) = \frac{1}{2}e^{i\theta} - \frac{1}{4}e^{i2\theta}$ 的 $1/c$ 像):

| 极点 | 坐标 | 原像 |
|:---|:---|:---|
| 尖端 | $y = +4$ | $c=1/4$ (cusp) |
| 底部 | $y = -4/3$ | $c=-3/4$ (neck) |
| 右端 | $x \approx +1.624$ | $\theta\approx98.7^\circ$ |
| 左端 | $x \approx -1.624$ | 共轭对称 |
