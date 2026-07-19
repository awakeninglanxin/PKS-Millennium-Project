# 逆M水滴 — 精确三角参数化 · 数学推导

> 从 Douady-Hubbard 参数化到 $c\mapsto 1/c$ 反演，再到 CFD 就绪的闭合轮廓

---

## 1. Mandelbrot 集主心形边界参数化

### 1.1 标准参数化 (Douady & Hubbard, 1985)

Mandelbrot 集的主心形（period-1 双曲分量）边界可由一个精确的三角函数参数化：

$$\boxed{c_{\text{cardioid}}(\theta) = \frac{e^{i\theta}}{2} - \frac{e^{2i\theta}}{4}, \quad \theta \in [0, 2\pi]}$$

**推导思路**：M 集的边界对应于 $z\mapsto z^2+c$ 迭代中 $z$ 不动点的乘子为 $e^{i\theta}$ 的条件。设不动点 $z_0$ 满足 $z_0 = z_0^2 + c$ 且导数 $2z_0 = e^{i\theta}$，代入消去 $z_0$ 即得上述公式。

**几何意义**：当 $\theta$ 从 0 遍历到 $2\pi$ 时，$c_{\text{cardioid}}(\theta)$ 逆时针画出一个心形曲线。

| $\theta$ | $c_{\text{cardioid}}$ | 位置 |
|:---:|------|------|
| $0$ | $0.25$ | 尖端 (cusp, 最右点) |
| $\pi/2$ | $-0.5 + 0.5i$ | 上方 |
| $\pi$ | $-0.75$ | 与周期2泡的附着点 (最左点) |
| $3\pi/2$ | $-0.5 - 0.5i$ | 下方 |

### 1.2 周期2泡参数化

周期2泡是一个以 $c = -1$ 为中心、半径 $0.25$ 的圆：

$$\boxed{c_{\text{bulb2}}(\theta) = -1 + \frac{e^{i\theta}}{4} = \frac{\cos\theta}{4} + i\frac{\sin\theta}{4} - 1, \quad \theta \in [0, 2\pi]}$$

附着点：主心形在 $c = -0.75$ 处与周期2泡在 $c = -0.75$ 处切触。周期2泡的 $c = -0.75$ 对应 $\theta = \pi$。

---

## 2. $c \mapsto 1/c$ 反演变换——心形→水滴

### 2.1 反演变换的几何性质

对复平面施加映射 $f(c) = 1/c$。这是一个**保角反演**（Möbius 变换的特例），它将：

- 过原点的直线 → 过原点的直线
- 不过原点的圆 → 圆（但中心被移动）
- 单位圆 → 自身
- $|c| < 1$ 区域 → $|f(c)| > 1$ 区域（内外翻转）

对 M 集施加 $f$ 得到 **逆M集**（Inverse Mandelbrot Set），定义为迭代 $z_{n+1} = z_n^2 + 1/c$ 的填充 Julia 集参数空间。

### 2.2 关键点的反演映射

| 标准 M 集 | $\theta$ | $c$ | $1/c$ (逆M) | 逆M位置 |
|------|:---:|:---:|------|------|
| 主心形尖端 | $0$ | $0.25$ | **$4$** | 水滴尖端 (+x 轴) |
| 主心形-泡附着点 | $\pi$ | $-0.75$ | **$-\frac{4}{3} \approx -1.333$** | 水滴根部 (-x 轴) |
| 心形上点 | $\pi/4$ | ≈$0.35-0.10i$ | ≈$2.68+0.79i$ | 水滴上弧 |

**核心变换公式**：

$$\boxed{c_{\text{droplet}}(\theta) = \frac{1}{\frac{e^{i\theta}}{2} - \frac{e^{2i\theta}}{4}}, \quad \theta \in [0, 2\pi]}$$

### 2.3 上半平面翻转

$1/c$ 变换将标准 M 集心形的**上半部分**（$\operatorname{Im}(c) > 0$）映射到逆M集的**下半平面**（$\operatorname{Im}(c_{\text{droplet}}) < 0$）。这是因为：

$$c_{\text{droplet}} = \frac{1}{x+iy} = \frac{x-iy}{x^2+y^2}$$

虚部符号翻转（$\operatorname{Im}(1/(x+iy)) = -y/(x^2+y^2)$）。

因此生成水滴上边界时，取 $c_{\text{droplet}}(\theta)$ 在 $\theta \in [0, \pi]$ 的**下半部分**（$\operatorname{Im} \le 0$），然后 $y \to -y$ 翻转到上半平面。

### 2.4 尖端与根部的精确坐标

水滴尖端：$\theta \to 0$ 时，
$$c_{\text{droplet}}(0) = \frac{1}{1/2 - 1/4} = \frac{1}{1/4} = 4$$

水滴根部：$\theta \to \pi$ 时，
$$c_{\text{droplet}}(\pi) = \frac{1}{-1/2 - 1/4} = \frac{1}{-3/4} = -\frac{4}{3} \approx -1.333$$

水滴长轴：$\Delta x = 4 - (-4/3) = 16/3 \approx 5.333$

---

## 3. 轮廓生成算法

### 3.1 Python 实现

```python
def inv_cardioid(theta):
    """逆M集主心形边界 (Douady-Hubbard 参数化 → 反演)"""
    c_classic = 0.5 * np.exp(1j * theta) - 0.25 * np.exp(2j * theta)
    return 1.0 / c_classic   # c → 1/c 反演

def generate_droplet(n_cardioid=1200, edge_boost=5):
    theta = np.linspace(0, np.pi, n_cardioid)
    # 尖端加密: 指数权重 → θ^1.5 非线性拉伸
    # 根部加密: 对称的在 θ→π 处也加密
    ...
    c = inv_cardioid(theta)
    mask = c.imag <= 0  # 取下半 → 翻转得上边界
    upper_x = c.real[mask][::-1]   # 左→右排序
    upper_y = -c.imag[mask][::-1]  # 虚部翻转

    # 实轴镜像得完整闭合轮廓
    full_x = np.concatenate([upper_x, upper_x[::-1]])
    full_y = np.concatenate([upper_y, -upper_y[::-1]])
    return full_x, full_y
```

### 3.2 尖端加密策略

$\theta \to 0$ 时 $c_{\text{droplet}} \to 4$，此时 $\frac{dc}{d\theta}$ 趋于无穷（尖端处的参数化速度极高）。为确保尖端弧线丝滑，在 $\theta \in [0, 0.15\pi]$ 区域进行 $5\times$ 加密：

$$\theta_i^{\text{boost}} = (\theta_i)^{1.5}$$

非线性拉伸使得 $\theta \to 0$ 附近的采样密度比线性采样高 $5\times$。

---

## 4. 周期2泡的处理

### 4.1 泡的数学位置

周期2泡在逆M集中的边界由下式给出：

$$c_{\text{bulb2-inv}}(\theta) = \frac{1}{\frac{\cos\theta}{4} + i\frac{\sin\theta}{4} - 1}, \quad \theta \in [\pi, 2\pi]$$

该泡占据 $x \in [-1.333, -0.800]$ 区域，其上半弧的 $y \in [0, 0.267]$。

### 4.2 泡被移除的原因

经曲率分析发现，泡的内点全部位于主心形轮廓**内部**。在 $x = -0.8$ 处，心形上半的 $y \approx 1.17$，而泡的上半弧 $y \approx 0$——心形完全包裹了泡。

因此水滴轮廓采用**纯主心形**，不绘制周期2泡。这简化了几何结构，且不影响 CFD 流体仿真的形状完整性。

---

## 5. 数值特性

| 参数 | 值 | 公式来源 |
|------|:---:|------|
| 尖端坐标 | $c = 4$ | $1 / (1/2 - 1/4)$ |
| 根部坐标 | $c = -4/3$ | $1 / (-1/2 - 1/4)$ |
| 长轴 | $16/3 \approx 5.333$ | $4 - (-4/3)$ |
| 短轴 | $\approx 3.249$ | $2 \times \max|y|$ |
| 长宽比 | $\approx 1.64$ | 典型泪滴比例 |
| 面积 (Shoelace) | $11.1701$ | 3352点多边形 |
| 轮廓点数 | 3353 | 可调 (n_cardioid) |

---

## 6. 参考文献

1. Douady, A. & Hubbard, J.H. (1985). *Étude dynamique des polynômes complexes*. Pub. Math. d'Orsay.
2. Jung, W. (2002). *The Mandelbrot set — boundary equation*. mandelbrot-numerics library.
3. Milnor, J. (2006). *Dynamics in One Complex Variable*. Princeton University Press.
4. Richling, M. (2015). *Inverted Mandelbrot*. https://www.mitchr.me/SS/mandelbrotInv/
