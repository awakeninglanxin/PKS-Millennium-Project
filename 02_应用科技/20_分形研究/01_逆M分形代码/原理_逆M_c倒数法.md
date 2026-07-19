# ② 逆Mandelbrot集 — c倒数法 (z² + 1/c)

**对应文件**：
- `分形逆M_c倒数法_z平方迭代.py`（基础版）
- `分形逆mandelbrot细腻.py`（mpmath 高精度版）
- `分形逆mandelbrot细腻_v2.py`（Numba 平滑版 + 直方图均衡 + 环形色盘）
- `分形逆mandelbrot细腻gpu优化+二阶摄动+fft z^2.py`（多段色盘 + 视图缓存版）

---

## 核心算法

### 迭代公式
```
z₀ = 0
zₙ₊₁ = zₙ² + (1/c)      其中 c ≠ 0
逃逸半径：R = 50
```

**与标准M的关键区别**：参数空间做了复反演 c → 1/c。

### 数学原理

逆Mandelbrot集 M_inv 定义为标准 M 在 1/c 映射下的像：
```
M_inv = { c ∈ ℂ : 1/c ∈ M }
```

等价地，可以通过直接迭代 z → z² + (1/c) 计算。

**拓扑效应**：
- 原点 0+0i ∈ M → 1/0 = ∞ ∈ M_inv（原点被"翻到无穷远"）
- 心形线外部变为水滴内部，心形线变为水滴外部边界
- |c|=1 是自对偶边界

---

## 四个版本的技术演进

### v1：基础版 (`分形逆M_c倒数法_z平方迭代.py`)

```
算法：逐像素 c→1/c→z²+(1/c)
Numba @jit 加速
逃逸半径 = 50
hsv 色图
```

### v2：高精度版 (`分形逆mandelbrot细腻.py`)

引入三重大幅升级：

**① mpmath 自适应精度**：根据放大级别自动提升 `mp.dps`。深度缩放时 double 精度不足导致的像素错位被消除

**② 平滑逃逸计数（Smooth Iteration Count）**：
```
ν = n + 1 − log₂(log|z|)
```
将逃逸时间从整数变为连续浮点数，消除色带阶梯效应：
```python
if abs(z) > escape_radius:
    return n + 1 - log(log(abs(z)), 2)
```

**③ nearest 插值**：关闭 bilinear 平滑，确保像素级别的精准显示

### v3：Numba 平滑版 (`分形逆mandelbrot细腻_v2.py`)

用 Numba 替代 mpmath，速度大幅提升但仍保留平滑逃逸：

| 特性 | 计量 |
|------|------|
| 平滑逃逸 | `n+1 − log₂(log|z|)` |
| Numba parallel | `@njit(parallel=True)` |
| 逃逸半径 | 50 |
| 插值 | bilinear（兼顾速度与画质） |

**直方图均衡化**：将逃逸时间重新映射，使得每层结构的可见度均等。算法：
```python
hist, bins = np.histogram(escaped[escaped < max_iter], bins=max_iter)
cdf = np.cumsum(hist) / np.sum(hist)
equalized = cdf[escaped.astype(int)] * max_iter
```

**环形色盘**：色图首尾颜色相连，使迭代层循环着色：
```python
cmap_cyclic = plt.cm.hsv  # 或其他 cyclic colormap
```

### v4：多段色盘+缓存版 (`分形逆mandelbrot细腻gpu优化+二阶摄动+fft z^2.py`)

**① 11段组合色盘**：不依赖单一 colormap，而是拼接 11 段不同 cmap 的片段，每段 23 色，组合成 256 色自定义色盘。包括 spring/summer/autumn/winter/cool/hot/magma/inferno/plasma/gist_rainbow/hsv/gist_ncar 的交替排列。

**② Gamma 幂律映射**：
```python
data_scaled = np.power(data, gamma)  # gamma=0.5
```
压缩高值区（内部）、拉伸低值区（边界），使得细丝和边界细节更突出。

**③ 视图缓存**（view_stack）：放大前将当前渲染存入栈，Backspace 直接 pop 缓存的 NumPy 数组，避免重算。

---

## 四版技术矩阵

| 技术 | v1基础 | v2 mpmath | v3 Numba | v4 多段色盘 |
|------|:--:|:--:|:--:|:--:|
| 加速 | Numba | 无(纯Python) | Numba parallel | Numba parallel |
| 平滑逃逸 | ✗ | ✓ (mpmath) | ✓ | ✓ |
| 直方图均衡 | ✗ | ✗ | ✓ | ✓ |
| 环形色盘 | ✗ | rainbow | hsv | 11段组合 |
| Gamma映射 | ✗ | ✗ | ✗ | ✓ |
| 视图缓存 | ✗ | ✗ | ✗ | ✓ |
| 自适应精度 | ✗ | ✓ | ✗ | ✗ |
| 用途 | 快速预览 | 深度缩放 | 高质量渲染 | 最高画质 |
