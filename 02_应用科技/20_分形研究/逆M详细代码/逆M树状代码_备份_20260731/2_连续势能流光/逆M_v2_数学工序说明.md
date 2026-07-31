# 逆Mandelbrot 水滴 v2 — 完整数学工序

## 0. 总览

`v2.py` 是一套自包含的逆 Mandelbrot 水滴可视化管线，输出三要素叠加的 PNG 图像：

1. **~3000 条同心环** — escape_time 连续势场的子像素等值线
2. **Sobel 外壳主干** — 梯度检测的壳层黑线
3. **解析轮廓线** — 心形体 $c(\theta)$ 经 $1/c$ 的精确外边界

无任何外部文件依赖（numpy + scipy + matplotlib 仅需）。

---

## 1. 坐标变换链

### 1.1 采样域 → 变换域

视口基于水滴四边框的精确值外扩 $+0.5$：

$$
\begin{aligned}
\text{Re}(c_{\text{orig}}) &\in [-\tfrac{4}{3}-0.5,\; 4+0.5] = [-1.833,\;4.500] \\
\text{Im}(c_{\text{orig}}) &\in [-1.6243-0.5,\; 1.6243+0.5] = [-2.124,\;2.124]
\end{aligned}
$$

网格 $W=2400,\;H=W\cdot\text{(Re范围}/\text{Im范围}) \approx 3577$。

### 1.2 $c^\alpha$ 极坐标幂变换

$$\boxed{c_{\text{eff}} = |c|^\alpha \cdot e^{i\alpha\cdot\arg(c)}}$$

当 $\alpha = -1$ 时退化为标准 Inverse 变换 $c_{\text{eff}} = 1/c$。

奇点保护：$|c| < 10^{-12}$ 时 $c_{\text{eff}} = 10^6$（$\alpha<0$）。

### 1.3 Mandelbrot 迭代

$$\boxed{z_{n+1} = z_n^2 + c_{\text{eff}},\quad z_0 = 0}$$

逃逸判定：$|z_n| > 128$（bailout = 128，匹配 Ultra Fractal 原始设置），最大迭代次数 $N_{\max}=250$。

### 1.4 rot90 旋转

```python
smooth = np.rot90(smooth, k=3)
```

$k=3$ = 顺时针 $90^\circ$ = 逆时针 $270^\circ$。效果：原 Re 轴变为新 y 轴（竖直向上），原 Im 轴变为新 x 轴（水平展开）。水滴尖端 $c=1/4 \to 1/c=4$ 映射到图像顶部 $y=+4$。

---

## 2. 连续势函数（Smooth Coloring）

### 2.1 定义

对于在第 $n$ 次迭代逃逸的像素，其逃逸瞬间的模长为 $|z_n| > 128$：

$$\boxed{\nu = n - \log_2\!\big(\log_2(|z_n|)\big)}$$

代码等价形式：

```python
smooth = escape_time - log2(log2(|z_n|))
```

### 2.2 数学性质

- $\nu$ 是**连续标量场**：$\mathbb{R}^2 \to [-\epsilon, 250]$（在视口范围内）
- 在 Mandelbrot 集外部处处可微
- $\nu$ 的**等值线**（水平集 $\{\nu = \text{const}\}$）是天然的同心环
- 集合内部（$n = N_{\max}$，从未逃逸）：强制 $\nu = 0$

### 2.3 与传统阶梯式的对比

| 方法 | 数据类型 | 环数上限 | 信息损失 |
|:---|:---|:---|:---|
| `escape_time` 原始 | 整数 $\in \{1,\dots,250\}$ | 250 | 子整数层全丢 |
| 平滑势函数 $\nu$ | 连续实数 $\in \mathbb{R}$ | 无上限 | 零损失 |

---

## 3. 同心环生成：子像素等值线提取

### 3.1 原理

$\nu$ 是连续场，等值线有无限多条。传统 `np.round(ν)` 将连续场坍缩为 250 个离散阶梯，最多提取 249 条边界。

突破：缩放后取整。

$$\boxed{\nu_{\text{scaled}} = \lfloor \nu \times K + 0.5 \rfloor}$$

其中 $K$ 是子像素因子。默认 $K=12$，产生 $\approx 250 \times 12 = 3000$ 个离散阶梯。

### 3.2 阶梯跳变检测

```python
dx = |diff(ν_scaled, axis=1)|   # 水平邻域跳变
dy = |diff(ν_scaled, axis=0)|   # 垂直邻域跳变
ring_mask = (dx ≥ 0.5) | (dy ≥ 0.5)
```

每个 $|\nu_{\text{scaled}}| \geq 0.5$ 的像素就是一个等值线经过的位置。

### 3.3 环数上限

$$N_{\text{rings}} \approx (N_{\max} - 1) \cdot K = 249K$$

$K=12$ 时 $\approx 2988$ 条环。理论上 $K \to \infty$ 时 $N_{\text{rings}} \to \infty$，实际由像素分辨率约束。

### 3.4 5色交替循环染色

环的颜色按 $\nu_{\text{scaled}} \bmod 5$ 映射到 5 灰度级：

$$\text{palette} = [0.00,\;0.20,\;0.40,\;0.60,\;0.82]$$

相邻环的灰度差最小为 $0.20$，人眼可清晰分辨。

---

## 4. 外壳主干：Sobel 梯度检测

### 4.1 原理

壳层 = $\nu$ 场中梯度最陡的带状区域（Mandelbrot 集边界在 $1/c$ 映射下的像）。

### 4.2 步骤

1. **Sobel 算子**求 $\nabla\nu = (g_x, g_y)$，梯度幅值 $|\nabla\nu| = \sqrt{g_x^2 + g_y^2}$
2. 取外部区域的 **top 1.5%** 梯度像素（`np.percentile(grad_mag[ext], 98.5)`）
3. **binary_opening**（十字核）去噪 → 连续壳层线
4. **binary_dilation**（3×3 全核）加粗 1px → 可见黑线

```python
shell_sobel[i,j] = (|∇ν[i,j]| > 98.5%-ile) & ~interior[i,j]
shell_thick = binary_dilation(shell_sobel)
```

---

## 5. 解析轮廓线：$c(\theta)$ 的直接映射

### 5.1 数学基础

Mandelbrot 集的主体边界是心形体（cardioid）：

$$\boxed{c(\theta) = \frac{1}{2}e^{i\theta} - \frac{1}{4}e^{i2\theta},\quad \theta \in [0, 2\pi)}$$

经 $1/c$ 变换并 rot90 旋转后：

$$\boxed{\begin{aligned}
c &= c(\theta) \\
c_{\text{inv}} &= 1/c \\
(x,\;y)_{\text{rot}} &= (-\text{Im}(c_{\text{inv}}),\; \text{Re}(c_{\text{inv}}))
\end{aligned}}$$

### 5.2 实现

```python
theta = linspace(ε, 2π-ε, 6000)
c = 0.5*exp(iθ) - 0.25*exp(2iθ)
inv_c = 1.0 / c
ox, oy = -inv_c.imag, inv_c.real
```

6000 个采样点 → 连续闭曲线，作为 `matplotlib.plot()` 叠加到同心环图上。

### 5.3 边框精确值

| 极点 | 坐标 | $\theta$ | $c$ | 精确值 |
|:---|:---|:---|:---|:---|
| 尖端 $y_{\max}$ | $y=+4$ | $0$ | $1/4$ | 有理 |
| 底部 $y_{\min}$ | $y=-4/3$ | $\pi$ | $-3/4$ | 有理 |
| 右端 $x_{\max}$ | $x\approx+1.62427$ | $\approx98.7^\circ$ | $\approx0.163+0.569i$ | 非有理 |

---

## 6. 渲染管线总览

```
输入: 视口范围, 网格 W×H, factor K
 │
 ├─[1] 采样 → c^α 变换 → Mandelbrot 迭代 → rot90
 │     输出: smooth (连续势场 ν), interior (内部mask)
 │
 ├─[2] 同心环: ν × K → 取整 → diff → 跳边 → 5色交替
 │     输出: img[jump_edges] = 灰度数组
 │
 ├─[3] 外壳: Sobel(ν) → top1.5% → 开运算 → 膨胀 → 纯黑
 │     输出: img[shell_thick] = 黑色
 │
 ├─[4] 枝杈: 外壳膨胀2层 → 避开环区 → 开运算 → 淡灰
 │     输出: img[branches] = 淡灰
 │
 ├─[5] 内部留白: img[interior] = 白色
 │
 ├─[6] 解析轮廓: c(θ) → 1/c → rot90 → plot叠加
 │
 └─ 输出: PNG 300dpi
```

## 7. 关键参数速查

| 参数 | 值 | 含义 |
|:---|:---|:---|
| `alpha` | -1 | $c^{-1}$ 逆变换 |
| `max_iter` | 250 | Ultra Fractal 原始 |
| `bailout` | 128 | Ultra Fractal 原始 |
| `SUB_FACTOR` | 12 | 子像素缩放因子 |
| `WIDTH` | 2400 | 水平分辨率 |
| `thresh` | 98.5%-ile | Sobel 梯度阈值 |
| `grays` | [0.00,0.20,0.40,0.60,0.82] | 5色循环调色板 |
