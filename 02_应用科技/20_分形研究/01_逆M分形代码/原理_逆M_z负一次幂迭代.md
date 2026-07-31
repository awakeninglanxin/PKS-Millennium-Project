# ③ 逆Mandelbrot集 — z负一次幂迭代 (z⁻¹ + c)

**对应文件**：
- `分形z负一次幂迭代_gpu优化+二阶摄动+fft_4色.py`（4初值 RGB 叠加版）
- `分形z负一次幂迭代_gpu优化+二阶摄动+fft_8色.py`（8初值 HSV 着色版）

---

## 核心算法

### 迭代公式
```
z₀ = 给定的初始值（多组）
zₙ₊₁ = 1/zₙ + c
逃逸半径：R = 10
```

### 与 c 倒数法的本质区别

| 维度 | c倒数法 (前一类) | z倒数法 (本类) |
|------|:--:|:--:|
| 公式 | z → z² + (1/c) | z → 1/z + c |
| z₀ | 固定为 0 | 多组初值 |
| 数学本质 | 参数空间反演 | 迭代函数反演 |
| 视觉特征 | 水滴形 + 内部泡 | 复杂嵌套 + 四/八色交叠 |

**核心差异**：c倒数法改变"参数"（c→1/c），迭代函数仍是 z²+c。z倒数法改变"迭代函数本身"（z²→1/z），这是两个本质上不同的动力系统。

---

## 多初值机制

### 4色版：四个对称初值

```
初值1: z₀ = k + k·j    (红色 R 通道)
初值2: z₀ = -k - k·j   (绿色 G 通道)
初值3: z₀ = -k + k·j   (蓝色 B 通道)
初值4: z₀ = k - k·j    (黄色 = R+G)
默认 k = 0.5
```

每个像素计算四次，分别得到4个逃逸时间，然后分配到RGB三通道叠加为彩色图像。

**为什么要四个初值？**
- 1/z + c 的动力学高度依赖初始条件——不同的 z₀ 可能产生完全不同的有界/逃逸行为
- 四个对称初值覆盖了复平面的四个象限，给出"全方位"的动力学画像
- k 和 -k 的对偶对应 PKS 极化原理中的正负极性对称

### 8色版：k 组 + 1/k 组

在4色基础上新增"1/k 尺度"初值：

```
k 组（原始尺度）：
  z₀ = k + k·j       (红)
  z₀ = -k - k·j      (绿)
  z₀ = -k + k·j      (蓝)
  z₀ = k - k·j       (黄)

1/k 组（逆尺度）：
  z₀ = 1/k + 1/k·j   (青)
  z₀ = -1/k - 1/k·j  (品红)
  z₀ = -1/k + 1/k·j  (橙)
  z₀ = 1/k - 1/k·j   (紫)
```

**数学意义**：k 和 1/k 互为倒数——k·(1/k) = 1。这与 PKS 极化原理 c·(1/c)=1 直接对应。两组初值揭示了"尺度对偶"下动力学行为的差异。

---

## HSB → RGB 映射（8色版）

8色版不使用简单的RGB通道叠加，而是将每个初值的逃逸时间映射为 HSB (色相/饱和度/亮度)：

```python
hue = idx / 8.0                  # 8种初值均匀分配色相
saturation = 0.8                 # 高饱和度
brightness = escape_time / max_iter  # 逃逸时间控制亮度
rgb = hsv_to_rgb(hue, saturation, brightness)
```

效果：逃逸快的区域偏暗，有界区域保留鲜明的 8 色调。

---

## 技术细节

### Numba 并行计算

```python
@njit(parallel=True, fastmath=True)
def compute_inverse(xmin, xmax, ymin, ymax, width, height,
                    max_iter, escape_radius, initial_z):
    out = np.empty((height, width, len(initial_z)), dtype=np.float64)
    for j in prange(height):        # prange = 自动并行
        im = ymin + j * (ymax - ymin) / (height - 1)
        for i in range(width):
            re = xmin + i * (xmax - xmin) / (width - 1)
            for k in range(len(initial_z)):
                out[j, i, k] = smooth_inverse_point(re+1j*im, ...)
    return out
```

### 平滑逃逸

与 c 倒数法相同的公式：ν = n+1 − log₂(log|z|)

### 注意零值保护

当 z 接近 0 时 1/z → ∞，需提前 break：
```python
if abs(z) < 1e-12:
    return n
```

---

## 与 PKS 极化原理的关联

z负一次幂 z→1/z 恰好是 PKS 双锥几何 y=1/x 的复平面推广。k 和 1/k 两组初值的设定对应双锥交点 x=±1 的"极化中性面"。8色版将这一数学对称直接可视化。
