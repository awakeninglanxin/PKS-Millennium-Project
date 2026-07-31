# Mandelbrot 内部纹理渲染 — 总览与数学背景

> 基于 Claude Heiland-Allen（mathr.co.uk）2013年博客 "Interior coordinates in the Mandelbrot set" 及元宝深度分析整理。

---

## 1 问题起源

Mandelbrot 集的标准着色方式是用迭代逃逸次数对外部着色，而**内部**（即集合内部的黑色区域）通常被统一填黑。但如果能对内部进行"纹理映射"——把任意图片贴到每个 hyperbolic component（双曲分支/bulb）的内部——就能产生极具美感的渲染效果。

Claude Heiland-Allen 在看到一张 Mandelbrot 内部纹理图后，思考能否**反算乘子 b** 作为极坐标纹理坐标，使得每个 bulb 内部都能贴上图片纹理。答案是肯定的。

---

## 2 核心数学概念

### 2.1 Mandelbrot 集定义

Mandelbrot 集 M 定义为使得临界轨道有界的参数 c 的集合：

```
M = { c ∈ ℂ : |F^n(0, c)| ↛ ∞ as n → ∞ }
```

其中 F(z, c) = z² + c，F^n 表示 n 次迭代。

### 2.2 双曲分支与乘子

对 Mandelbrot 集内部的每个参数 c，如果 c 落在周期为 p 的双曲分支（hyperbolic component）内部，则存在一个**吸引周期轨道**：存在 z₀ 使得

```
F^p(z₀, c) = z₀
```

乘子（multiplier）b 定义为导数：

```
b = ∂/∂z F^p(z₀, c)
```

| 乘子性质 | 含义 |
|------|------|
| |b| < 1 | c 在周期p双曲分支内部（吸引周期点） |
| |b| = 1 | c 在双曲分支边界上 |
| |b| > 1 | 排斥周期点（不在该分支内部） |
| b = r·e^(2πiθ) | 极坐标表示：r=|b|，θ=arg(b)/(2π) |

### 2.3 乘子作为局部坐标

乘子 b 是整个分支内部的**共形坐标**（conformal coordinate）。在动力学平面的 Möbius 变换下，b 保持不变，这意味着：

- r = |b| 可作为"径向"纹理坐标——从中心（b=0）到边界（|b|=1）
- θ = arg(b)/(2π) 可作为"角向"纹理坐标——绕分支一圈到起点

**关键洞察**：利用 (r, θ) 作为 (u, v) 纹理坐标，双线性采样任意图片，就能将图片"贴入"每个 bulb。

### 2.4 正问题 vs 反问题

| 方向 | 已知 | 求解 | 用途 |
|------|------|------|------|
| 正问题 | p, θ（内部角度） | c（边界点坐标） | 定位边界点 |
| **反问题** | c（参数坐标） | b（乘子） | **纹理映射** |

反问题实际上比正问题更简单——因为只需要单变量 Newton 法求解 F^p(z, c) - z = 0，而不需要两变量系统。

---

## 3 反算乘子的算法概述

### 3.1 核心流程

```
对每个参数 c：
  迭代轨道 z_n = z_{n-1}² + c，跟踪 |z_n| 的局部最小值（atom domain）
  在每个新最小值处，猜测周期 p = n
    用 Newton 法从初值 z_n 出发，求解 F^p(z₀, c) = z₀ 得到 z₀
    计算导数 b = ∂/∂z F^p(z₀, c)
    若 |b| ≤ 1 → 返回 b（c 在此分支内部）
    否则 → 继续下一个周期
```

### 3.2 为什么原子域猜测有效

- 临界轨道 z_n 在迭代过程中会周期性地接近 0（当 c 在某个分支内部时）
- 每次 |z_n| 达到新的局部最小值，n 就是该点所在原子域的周期
- 这个猜测极大地减少了 Newton 法的迭代次数

### 3.3 逆水滴变换：c ↦ 1/w

作参数平面反演变换 c = 1/w，Mandelbrot 集变成水滴形（"逆 Mandelbrot 集"）。迭代变为有理映射：

```
z ← z² + 1/w
```

这个变换将原 Mandelbrot 集"内部翻转"，产生独特的视觉效果，也是后续合成渲染的关键步骤。

---

## 4 原始参考来源

- **博客文章**：Claude Heiland-Allen, "Interior coordinates in the Mandelbrot set", 2013-04-01
  - 地址：`https://mathr.co.uk/blog/2013-04-01_interior_coordinates_in_the_mandelbrot_set.html`
- **C99 实现**：`https://mathr.co.uk/web/m-interior-coordinates.html`
- **完整 Mandelbrot 博客索引**：`https://mathr.co.uk/blog/mandelbrot.html`

> 作者 Claude Heiland-Allen 是 Mandelbrot 分形渲染领域的核心贡献者，开发了 mdz、mightymandel、fractal-bits 等工具，提出了原子域、扰动理论等多种关键算法。

---

## 5 三个文件的结构

| 文件 | 内容 |
|------|------|
| `_1_总览与数学背景.md`（本文件） | 定义、乘子概念、总览 |
| `_2_算法与代码.md` | 反算算法详解、C99/Python 实现、Newton 法 |
| `_3_渲染工序与着色.md` | 完整8阶段渲染管线、逆水滴变换、Sierpinski 背景 |
