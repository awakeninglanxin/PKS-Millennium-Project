# 逆Mandelbrot水滴多同心环生成原理

## 1. 坐标变换：$c \to c^{-1}$

标准 Mandelbrot 集的递推公式为：

$$z_{n+1} = z_n^2 + c,\quad z_0 = 0$$

其中 $c = x + iy$ 是复平面上的采样点。通过 Inverse 变换 $c' = 1/c$（Ultra Fractal 中称为 Fractint.uxf 的 "Inverse" entry），标准 Mandelbrot 集的心形体（cardioid）和附属球（mini-Mandelbrot bulbs）被映射为"水滴"形状的结构。

**映射几何**：标准 Mandelbrot 集的心形中心 $c \approx 0.25$ 经 $1/c$ 映射为 $1/0.25 = 4$，位于原心形的外侧。Mandelbrot 集的边界结构被**内翻外**地重排，附着球变为"气泡"嵌在水滴壳层上。

### Ultra Fractal 等效参数

| 参数 | 值 | 含义 |
|:---|:---|:---|
| mapping center | 1.2 / 0 | 视口中心 |
| magn | 0.7 | 缩放因子 |
| transform | Inverse (Fractint.uxf) | $c' = 1/c$ |
| formula | Mandelbrot (Standard.ufm) | $z_{n+1} = z_n^2 + c'$ |
| maxiter | 250 | 最大迭代次数 |
| bailout | 128 | 逃逸半径 |
| outside | BinaryDecomposition Type 1 | 按逃逸位分解着色 |

### 连续插值：$c^\alpha$ 变换（极坐标幂）

更一般的变换形式为 $c_{\text{eff}} = |c|^\alpha \cdot e^{i\alpha\cdot\arg(c)}$，其中 $\alpha = 1 - 2t$：

| $t$ | $\alpha$ | 变换 | 视觉效果 |
|:---:|:---:|:---|:---|
| 0 | +1 | $c$ | 标准 Mandelbrot |
| 0.5 | 0 | 常数1 | 单色过渡态 |
| 1 | **-1** | **$1/c$** | **逆M水滴** |

### 旋转：$\times (-i)$ 使尖朝上

标准逆M的水滴尖指向实轴正方向（右）。乘以 $(-i)$（即 $\times e^{-i\pi/2}$）逆时针旋转 90°，使尖朝上。在离散图像中通过 `np.rot90(k=3)` 实现。

---

## 2. 平滑逃逸场：连续势函数的核心

### 传统逃逸时间的问题

标准逃逸时间算法对每个像素记录迭代次数 $n$（整数），当 $|z_n| > \text{bailout}$ 时标记为逃逸。这产生**带状色阶**（banding），因为相邻像素可能逃逸时间相同（都=3），但物理上它们的逃逸速度不同。

### 连续势函数（Smooth Coloring）

引入势函数将离散逃逸时间 $n$ 转换为**连续浮点数**：

$$\nu = n + 1 - \frac{\log_2(\log_2(|z|))}{\log_2(2)} = n - \log_2(\log_2(|z|))$$

其中 $|z|$ 是逃逸瞬间的复数模长（$|z| > \text{bailout}$）。

化简为代码中的形式：

```python
smooth = escape_time - log2(log2(|z|))
```

### 数学性质

- `smooth` 是定义域上的**连续标量场**：$\mathbb{R}^2 \to [0, 250]$
- 在 Mandelbrot 集外部处处可微（除极值点）
- 等值线（level sets）= 逃逸时间等时线 = **同心环的数学来源**
- 集合内部（iter=maxiter）：$smooth = 0$（人为赋值）

---

## 3. 同心环的数学本质：等值线而非阶梯

### 关键洞察

同心环并非"画出来的"，而是 **`smooth` 场的自然等值线**。每个像素的 `smooth` 值不同，相邻像素之间每越过一个整数（或子整数）阶梯，就形成一条等值线——即一条同心环。

### 错误方法：`np.round(smooth)`

```python
ET_int = np.round(smooth).astype(int)   # 坍缩为 250 个离散阶梯
dx = np.diff(ET_int, axis=1)            # 最多检测 249 条边界
```

**问题**：`np.round()` 人为地将连续场压缩为整数阶梯，丢失了所有子整数层级的等值线信息。`smooth = 3.2` 和 `smooth = 3.7` 都被映射为同一阶梯 3，它们之间的过渡区域（$3.49 \to 3.51$）的等值线只被记录一条。

### 正确方法：子像素缩放

```python
factor = K          # K ∈ ℕ+, 分辨率倍率
ET_scaled = np.round(smooth * K).astype(int)
# smooth × K 的范围: [K, 250×K]
# 有效阶梯数: ~250K
```

**数学模型**：将 `smooth` 视为连续高度场 $h(x,y)$，构造缩放场 $h_K(x,y) = K \cdot h(x,y)$，对其取整后检测阶梯跳变。每增加 1 个缩放因子，等值线分辨率提升 K 倍。

$$
N_{\text{rings}} = (K \cdot \max(h) - K \cdot \min(h)) \approx 250K
$$

### 阶梯跳变检测

```python
dx = |diff(ET_scaled, axis=1)|  # 水平方向阶梯跳变
dy = |diff(ET_scaled, axis=0)|  # 垂直方向阶梯跳变
ring_mask = (dx >= 0.5) | (dy >= 0.5)  # 跳变≥0.5 = 等值线经过此像素
```

---

## 4. 像素分辨率的物理约束

### 梯度分析

同心环的物理间距由 `smooth` 场的梯度决定：

$$\Delta x_{\text{ring}} = \frac{1}{|\nabla \text{smooth}| \cdot K}$$

其中 $|\nabla \text{smooth}|$ 是 smooth 场的局部梯度幅值。

| 区域 | $|\nabla \text{smooth}|$ | 环间距（K=1） | 环间距（K=12） | 可见性 |
|:---|:---|:---|:---|:---|
| 外圈（低 escape_time） | ~0.02 | 50 px | 4.2 px | 稀疏清晰 |
| 中圈（过渡带） | ~0.1–1 | 1–10 px | 0.08–0.83 px | 密集可辨 |
| 壳层边界 | **~163** | 0.006 px | **0.0005 px** | 全部合并 |

### 分辨率上限公式

给定图像分辨率 $W \times H$ 和视口范围 $[-4,4] \times [-4,4]$：

$$\text{最大可分辨因子} \quad K_{\max} \approx \frac{W/8}{\max|\nabla \text{smooth}|}$$

当 $K$ 超过此值时，壳层边界区域的环间距 < 1 像素，增环不再提升视觉质量。

---

## 5. 渲染管线：多层灰度交替染色

### 5.1 Sobel 壳体主干

对 `smooth` 场做 Sobel 算子提取最大梯度区域（top 2%），经 `binary_opening` 和 `binary_dilation` 平滑为连续的黑色壳层主线。

### 5.2 同心环阶梯检测

对缩放场 `ET_scaled` 做逐像素差分，检测阶梯跳变。

### 5.3 交替循环染色

为避免相邻环合并成一团黑，采用**5色交替循环**：

$$\text{gray}(p) = \text{palette}[\; \text{ET\_scaled}(p) \bmod 5\;]$$

$$\text{palette} = [0.00,\; 0.20,\; 0.40,\; 0.60,\; 0.82]$$

相邻环的颜色至少差 0.20 灰度值，人眼可清晰分辨。5色一组循环 50 次（factor=1）或 250 次（factor=5），形成连续的等高水平线纹理。

### 5.4 内部留白

`interior` 区域（escape_time = maxiter → 从未逃逸）置为纯白（RGB=1,1,1），表示水滴内部空心。

### 5.5 外围枝杈

对壳体做有限次膨胀，每次膨胀的新层用淡灰色填充，逐级变淡直至消失。

---

## 6. 参数对照表

| 版本 | factor | 有效环层数 | 跳边像素 | 壳层环间距 |
|:---|:---:|:---:|:---:|:---|
| v22 原始 | 1 | 250 | 172,495 | 宽 |
| v1 增强 | 5 | 1,246 | 319,969 | 中 |
| v1 高倍 | 12 | **2,991** | 456,106 | 细 |

---

## 7. 与 Ultra Fractal 的对应关系

| Ultra Fractal 参数 | 本实现等效 |
|:---|:---|
| `entry="Inverse"` (Fractint.uxf) | `c_eff = 1/c` |
| `entry="Mandelbrot"` (Standard.ufm) | `z = z² + c_eff` |
| `p_bailout=128` | `bailout = 128` |
| `maxiter=250` | `maxiter = 250` |
| `entry="BinaryDecomposition"` Type 1 | `smooth = escape - log₂(log₂(|z|))` + 阶梯检测 |
| `gradient: smooth=yes, rotation=1` | rot90(k=3) + 循环灰度 |
| `inside: transfer=none` | `img[interior] = 白色` |

---

## 8. 核心代码摘要

```python
# 1. c^α 变换 + Mandelbrot 迭代
c_eff = |c|^α · exp(i·α·arg(c))    # α=-1 → 1/c
z = z² + c_eff, 迭代直至 |z|>128

# 2. 连续势函数
smooth = escape_time - log₂(log₂(|z|))

# 3. rot90 → 尖朝上
smooth = np.rot90(smooth, k=3)

# 4. 子像素缩放 → 无限等值线
ET_scaled = np.round(smooth × K)    # K = 5, 12, ...

# 5. 阶梯跳变检测
jump_mask = |diff(ET_scaled)| ≥ 0.5

# 6. 5色交替循环
gray = palette[ET_scaled % 5]       # [0.00, 0.20, 0.40, 0.60, 0.82]
```

---

## 9. 总结

| 层级 | 原理 |
|:---|:---|
| 数学层 | $z_{n+1}=z_n^2+1/c$ 的 Julia-逃逸势函数 $\nu = n - \log_2(\log_2(\|z\|))$ |
| 物理层 | $\nu$ 的等值线 = 天然同心环，等值线密度由 $\|\nabla\nu\|$ 决定 |
| 算法层 | $\nu \times K$ 缩放 → 子像素取整 → 阶梯跳变检测 → 250K 条环 |
| 渲染层 | Sobel提取壳体 + 5色交替循环染色 + 内部留白 + 外围枝杈膨胀 |
| 瓶颈 | 壳层边界 $\|\nabla\nu\| \approx 163$ → 即使 $K=100$ 环间距仍 < 0.01px |
