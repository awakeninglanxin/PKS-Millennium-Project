# 逆Mandelbrot 水滴边框精确求解

## 0. 坐标系统约定

原始复平面：$c_{\text{orig}} = x + iy$，视口 $[-4,4]\times[-4,4]$。

**变换链**：

$$c_{\text{orig}} \xrightarrow{c_{\text{eff}}=c_{\text{orig}}^{-1}} c_{\text{eff}} \xrightarrow{z_{n+1}=z_n^2+c_{\text{eff}}} \text{Mandelbrot 判定} \xrightarrow{\text{rot90}(k=3)} \text{尖朝上}$$

`rot90(k=3)` = 顺时针 90° = 原 Re 轴 → 新 y 轴（竖直向上），原 Im 轴 → 新 x 轴（水平展开）。

**水滴边界** = Mandelbrot 集边界 $\partial M$ 在 $1/c$ 映射下的像：

$$\partial D = \left\{ \frac{1}{c} \;\middle|\; c \in \partial M \right\}$$

将 $\partial M$ 近似为其主体——心形体（cardioid）的边界：

$$c(\theta) = \frac{1}{2}e^{i\theta} - \frac{1}{4}e^{i2\theta},\quad \theta \in [0, 2\pi)$$

此近似略去了附着球（period-2 bulb 等）在 $1/c$ 映射下的贡献。数值验证表明附着球的像内嵌于水滴内部，不影响外壳边框。

---

## 1. 尖端（Top Extent）

### 问题表述

在 rot90 后的 y 轴上求水滴最高点：$\max \text{Re}(1/c)$。

### 推导

$$\text{Re}\!\left(\frac{1}{c}\right) = \frac{\text{Re}(c)}{|c|^2}$$

对实数 $c > 0$，$1/c$ 为正实数。心形体与正实轴的交点：

$$c(0) = \frac{1}{2}(1) - \frac{1}{4}(1) = \frac{1}{4}$$

$$\frac{1}{c(0)} = \frac{1}{1/4} = 4$$

对于 $\theta \neq 0$ 的复数值 $c$，$|c|$ 增大 → $1/|c|^2$ 缩小 → $\text{Re}(1/c)$ 的模长不可能超过 $4$。

### 结论

$$\boxed{y_{\max} = +4}$$

**对应 Mandelbrot 原像**：心形体 cusp（$c = 1/4$），周期-1 的不动点双重根处。

---

## 2. 底部（Bottom Extent）

### 问题表述

在 rot90 后的 y 轴上求水滴最低点：$\min \text{Re}(1/c)$。

### 推导

对实数 $c < 0$，$1/c$ 为负实数。心形体与负实轴的唯一切点：

$$c(\pi) = \frac{1}{2}(-1) - \frac{1}{4}(1) = -\frac{3}{4}$$

$$\frac{1}{c(\pi)} = \frac{1}{-3/4} = -\frac{4}{3}$$

需证此确为全局最小值。对心形体上任意点 $c(\theta) = a(\theta) + ib(\theta)$：

$$\text{Re}\!\left(\frac{1}{c}\right) = \frac{a}{a^2 + b^2}$$

对 $a < 0$ 的点，$\text{Re}(1/c) < 0$。最小值要求 $|a|/r^2$ 最大，即 $|a|$ 大且 $r$ 小。瓶颈点 $c = -3/4$ 是心形体上 $|c|$ 的最小值点（$r_{\min} = 0.75$），同时 $|a| = r$（因为 $b = 0$），故取得最大比值 $0.75/0.5625 = 4/3$。

### 结论

$$\boxed{y_{\min} = -\frac{4}{3}}$$

**对应 Mandelbrot 原像**：瓶颈 neck（$c = -3/4$），心形体与 period-2 球 $|c+1| = 1/4$ 的相切点。

---

## 3. 水平跨距（Horizontal Span = 左右两端）

### 问题表述

在 rot90 后的 x 轴上求水滴最宽处：$\max |\text{Im}(1/c)|$。

### 推导

$$\text{Im}\!\left(\frac{1}{c}\right) = -\frac{\text{Im}(c)}{|c|^2}$$

令 $g(\theta) = |\text{Im}(1/c(\theta))|$。代入参数方程：

$$
\begin{aligned}
c(\theta) &= \frac{1}{2}e^{i\theta} - \frac{1}{4}e^{i2\theta} \\[4pt]
a(\theta) &= \frac{2\cos\theta - \cos 2\theta}{4} = \frac{2\cos\theta - 2\cos^2\theta + 1}{4} \\[4pt]
b(\theta) &= \frac{2\sin\theta - \sin 2\theta}{4} = \frac{\sin\theta(1 - \cos\theta)}{2} \\[4pt]
r^2(\theta) &= a^2 + b^2
\end{aligned}
$$

目标函数：

$$g(\theta) = \frac{|b(\theta)|}{r^2(\theta)} = \frac{|\sin\theta|(1 - \cos\theta) / 2}{a^2(\theta) + b^2(\theta)}$$

### 极值条件

求 $\frac{dg}{d\theta} = 0$ 的根。由于 $g(\theta)$ 偶对称且周期为 $2\pi$，只需在 $\theta \in (0, \pi)$ 内求解。

数值解（Newton 法，初值 $\theta_0 = 1.7$）：

$$\theta_* \approx 1.72274097496395\ \text{rad} \approx 98.71^\circ$$

代入：

$$
\begin{aligned}
c(\theta_*) &\approx 0.1628646 + 0.5690477i \\[4pt]
\frac{1}{c(\theta_*)} &\approx 0.4648757 - 1.6242719i
\end{aligned}
$$

### 结论

$$\boxed{x_{\max} \approx +1.6242719100,\quad x_{\min} \approx -1.6242719100}$$

此值来自心形体边界 $g(\theta)$ 极值的数值解，非有理数。与黄金比 $\varphi = 1.61803\ldots$ 的差异为 $0.00624$（$0.39\%$），属于数值巧合。

**对应 Mandelbrot 原像**：心形体边界上 $\theta \approx 98.7^\circ$ 处的点，该点在心形体右上方，$|c| \approx 0.592$。

---

## 4. 结果总表

| 边框极值 | rot90 后坐标 | 精确解析值 | 数值近似 | Mandelbrot 原像 | 原像性质 |
|:---|:---|:---|:---|:---|:---|
| **尖端** | $y_{\max}$ | **$+4$** | 4.0000 | $c = +\frac{1}{4}$ | 心形体 cusp |
| **底部** | $y_{\min}$ | **$-\dfrac{4}{3}$** | −1.3333 | $c = -\frac{3}{4}$ | 心形体 neck |
| **右端** | $x_{\max}$ | 数值解 | +1.6243 | $c \approx 0.163+0.569i$ | 心形体 $\theta\approx98.7^\circ$ |
| **左端** | $x_{\min}$ | 数值解 | −1.6243 | 共轭对称 | — |

### 水滴的纵横比

$$\frac{\text{高度}}{\text{宽度}} = \frac{y_{\max} - y_{\min}}{2\,|x_{\max}|} = \frac{4 - (-4/3)}{2 \times 1.6243} = \frac{16/3}{3.2485} \approx 1.642$$

---

## 5. 推导源码

```python
import numpy as np

# 心形体参数方程
def cardioid(theta):
    return 0.5 * np.exp(1j*theta) - 0.25 * np.exp(2j*theta)

# 1. 尖端
c_cusp = cardioid(0)
tip = 1.0 / c_cusp  # = 4

# 2. 底部
c_neck = cardioid(np.pi)
bottom = 1.0 / c_neck  # = -4/3

# 3. 水平跨距 (数值求解)
theta = np.linspace(0, 2*np.pi, 100000)
c_all = cardioid(theta)
inv_im = np.abs(np.imag(1.0 / c_all))
max_idx = np.argmax(inv_im)
span = inv_im[max_idx]  # ≈ 1.6242719100
theta_span = theta[max_idx]  # ≈ 1.72274 rad
```
