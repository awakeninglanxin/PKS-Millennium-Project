# Mandelbrot 内部纹理渲染 — 渲染工序与着色

> 基于元宝深度分析中的完整8阶段渲染管线及 Sierpinski 背景合成方案整理。

---

## 1 渲染窗口设置

### 1.1 坐标范围

| 变体 | x 范围 | y 范围 | 描述 |
|------|------|------|------|
| 标准水滴 | [-3, 7] | [-3, 3] | 包含完整逆 Mandelbrot 集 |
| 扩展窗 | [-2.5, 5.5] | [-2.5, 2.5] | 紧凑版 |
| 自定义 | 按需调整 | 按需调整 | 共轴像素，Height = Width·aspect |

### 1.2 关键参数

- 图像尺寸：建议 ≥ 800×600，等轴（aspect=1）
- 最大迭代次数：1500~2000（逆水滴需要更多迭代）
- 逃逸半径：通常 2.0（标准）或更大（如 25，用于更平滑边界）

---

## 2 完整8阶段渲染管线

### 阶段 0：生成复数网格

```python
import numpy as np

def make_grid(xmin, xmax, ymin, ymax, W, H):
    x = np.linspace(xmin, xmax, W)
    y = np.linspace(ymin, ymax, H)
    X, Y = np.meshgrid(x, y)
    return X + 1j * Y  # w = x + iy
```

逆水滴变换下参数为 w（不是 c），c = 1/w。

---

### 阶段 1：临界轨道迭代 + 逃逸检测

使用有理映射 z ← z² + 1/w，临界点 z₀ = 0：

```python
def iterate_rational(W, max_iter=1500, bailout=2.0):
    """
    W: 复数网格（参数 w）
    返回: escaped, smooth_iter, min_z_idx
    """
    H, W_shape = W.shape
    Z = np.zeros_like(W, dtype=np.complex128)
    DZ = np.ones_like(W, dtype=np.complex128)  # 导数
    escaped = np.zeros_like(W, dtype=bool)
    smooth_iter = np.zeros_like(W, dtype=float)
    min_z_idx = np.zeros_like(W, dtype=int)
    min_z_val = np.full_like(W, float('inf'), dtype=float)
    
    for n in range(1, max_iter + 1):
        # 更新未逃逸像素
        active = ~escaped
        
        # 迭代：z ← z² + 1/w
        DZ[active] = 2 * Z[active] * DZ[active]
        Z[active] = Z[active] * Z[active] + 1.0 / W[active]
        
        # 检测逃逸
        abs_z = np.abs(Z)
        newly_escaped = active & (abs_z > bailout)
        escaped[newly_escaped] = True
        
        # 平滑迭代次数（Inigo Quilez 公式）
        smooth_iter[newly_escaped] = n - np.log2(np.log(abs_z[newly_escaped]))
        
        # 跟踪 |z| 局部最小值（用于原子域检测）
        new_min = active & (abs_z < min_z_val)
        min_z_idx[new_min] = n
        min_z_val[new_min] = abs_z[new_min]
    
    return escaped, smooth_iter, min_z_idx, Z, DZ
```

> **关键**：z 初始值必须为 0。因为 0 是 z² + 1/w 的临界点（导数零点），Mandelbrot 集定义要求临界轨道有界。换其他初值会得到不同的 Julia 集。

---

### 阶段 2：内部点乘子计算

```python
def compute_interior(W, min_z_idx, max_period=256, newton_iters=30):
    """
    对未逃逸的点计算乘子 b
    """
    interior = ~escaped
    # 逐像素调用 interior_coordinates()（见文件2）
    # 或用简化的批量 Newton 法
    return b_grid, interior_mask
```

---

### 阶段 3：内部着色（条纹+环）

基于乘子 b 的极坐标 (r, θ) 进行着色：

```python
def interior_color(b):
    """
    输入: 乘子 b（复数）
    输出: RGB 颜色
    """
    r = abs(b)
    theta = np.angle(b)
    
    # 角向条纹（14条）
    stripe = 0.5 + 0.5 * np.sin(2 * np.pi * 14 * theta)
    # 径向环（10圈）
    ring = 0.5 + 0.5 * np.sin(2 * np.pi * 10 * r)
    
    # HSV 合成
    # H: 角向条纹调制色相
    # S: 径向环调制饱和度
    # V: 基础亮度
    H = stripe * 0.5 + 0.5  # 色相范围 0.5~1.0（蓝-红）
    S = 0.6 + 0.4 * ring     # 饱和度调制
    V = 0.7 + 0.3 * ring     # 亮度调制
    
    return hsv_to_rgb(H, S, V)
```

---

### 阶段 4：外部逃逸着色

利用平滑迭代次数 t = n - log₂(log₂(|z|))，使用 Inigo Quilez 余弦调色板：

```python
def exterior_color(t, max_iter):
    """
    连续（无条纹）着色方案
    """
    t_norm = t / max_iter  # [0, 1]
    
    # IQ 调色板：余弦调制的 RGB
    r = 0.5 + 0.5 * np.cos(2 * np.pi * (t_norm * 3.0 + 0.0))
    g = 0.5 + 0.5 * np.cos(2 * np.pi * (t_norm * 3.0 + 0.33))
    b = 0.5 + 0.5 * np.cos(2 * np.pi * (t_norm * 3.0 + 0.67))
    
    return np.stack([r, g, b], axis=-1)
```

---

### 阶段 5：距离估计（DEM）勾边

距离估计公式：d ≈ |z|·ln|z| / |dz|

```python
def dem_edge(Z, DZ, bailout=2.0):
    """
    Z: 逃逸时的 z 值
    DZ: 逃逸时的 dz 值
    """
    abs_z = np.abs(Z)
    d = abs_z * np.log(abs_z) / np.abs(DZ)
    
    # 归一化到像素宽度
    d_norm = d * 800  # 假设 800px 宽
    
    # 暗边：d < 1 处变暗
    edge_dark = np.clip(1.0 - np.exp(-d_norm * 3), 0, 1)
    
    # 光晕：d < 0.5 处加亮
    edge_glow = np.exp(-d_norm * 6)
    
    return edge_dark, edge_glow
```

---

### 阶段 6：Sierpinski 背景（帕斯卡三角 mod 2）

独立于参数平面 w，在像素空间直接生成：

```python
def sierpinski_background(H, W, scale=20.0, x_offset=0.0, y_offset=0.0):
    """
    帕斯卡三角 mod 2 作为背景纹理
    
    参数:
        scale: 缩放因子（越大三角越小）
    """
    # 像素坐标归一化
    y_idx = np.arange(H).reshape(-1, 1)
    x_idx = np.arange(W).reshape(1, -1)
    
    # 三角格坐标映射
    s = scale
    y_rel = (y_idx - H/2) / H * scale + y_offset
    x_rel = (x_idx - W/2) / H * scale + x_offset  # 注意用 H 保持等轴
    
    b = 2 * y_rel / (s * np.sqrt(3))
    a = (x_rel - s * b / 2) / s
    
    n = np.round(a + b).astype(int)
    k = np.round(b).astype(int)
    
    # Lucas 定理：C(n,k) mod 2 = 1 当且仅当 (k & ~n) == 0
    valid = (n >= 0) & (k >= 0) & (k <= n)
    mask = valid & ((k & ~n) == 0)
    
    # 着色
    background = np.zeros((H, W, 3))
    background[mask] = [0.0, 0.8, 0.8]     # 青色填充
    
    # 边框检测（相邻像素不同→三角形边缘）
    from scipy.ndimage import binary_dilation
    border = mask ^ binary_dilation(mask, iterations=1)
    background[border] = [1.0, 0.84, 0.0]   # 金色边缘
    
    return background
```

> 当视图范围过小时，三角格坐标被压缩，round 后全为0 → 需要引入独立的 SIERPINSKI_SCALE 进行坐标放大。

---

### 阶段 7：合成最终图像

```python
def compose(interior_mask, interior_rgb, exterior_rgb,
            edge_dark, edge_glow, sierpinski_bg):
    """
    按优先级合成：
    1. 内部区域 → 内部着色
    2. 非内部 + Sierpinski→背景纹理
    3. 外部区域 → 外部着色
    4. DEM边缘 → 暗边+光晕叠加
    """
    result = np.zeros_like(interior_rgb)
    
    # 内部点着内部颜色
    result[interior_mask] = interior_rgb[interior_mask]
    
    # 非内部点采用 Sierpinski 背景 + 外部着色混合
    bg_mask = ~interior_mask
    result[bg_mask] = sierpinski_bg[bg_mask]
    
    # DEM 边缘叠加
    result = result * edge_dark[..., None]
    result = result + edge_glow[..., None] * 0.3
    
    # 外部着色覆盖非 Sierpinski 区域
    non_sierp = bg_mask & ~sierpinski_filled
    result[non_sierp] = exterior_rgb[non_sierp]
    
    return np.clip(result, 0, 1)
```

---

## 3 渲染参数调优

### 3.1 迭代次数

| 场景 | 推荐值 |
|------|------|
| 逆水滴全景 | 1500~2000 |
| 标准 Mandelbrot | 500~1000 |
| 深放大 | 5000+ |

### 3.2 内部着色参数

| 参数 | 默认值 | 效果 |
|------|------|------|
| 角向条纹数 | 14 | 更多=更密条纹 |
| 径向环数 | 10 | 更多=更密同心环 |
| 条纹函数 | sin | 可用 sawtooth 或 triangle wave |

### 3.3 Sierpinski 缩放

```python
SIERPINSKI_SCALE = 20.0  # 基础值
# 视窗范围越小 → SIERPINSKI_SCALE 越大
# 视窗范围越大 → SIERPINSKI_SCALE 越小
```

---

## 4 重要边界情况

### 4.1 最右端黑色区域

w > 4 的区域对应原 M 集中 c ∈ (0, 0.25)（主心脏线的右端），是 M 集外部经反演后的像，因此无内部纹理。解决方案：该区域改用逃逸色带填充。

### 4.2 Sierpinski 背景失效

当视图范围过小时，三角格坐标被过度压缩，导致 `round` 后全为 0，模运算失效。解决方案：引入 `SIERPINSKI_SCALE` 因子放大坐标。

### 4.3 周期检测失败

在分支边界附近 |b|≈1 时，Newton 法可能发散。解决方案：增加 Newton 迭代次数或放宽 |b|≤1 的判断阈值（如 ≤1.001）。

---

## 5 完整渲染流程总结

```
解析参数 → 生成 w 网格
    ↓
阶段0: w = x + iy 复数网格
    ↓
阶段1: z ← z² + 1/w 迭代（临界点 z₀=0）
        记录逃逸状态、平滑迭代次数、原子域位置
    ↓
阶段2: 对未逃逸点 → Newton法求周期点 → 计算乘子b
    ↓
阶段3: 内部着色 = f(|b|, arg(b)) 极坐标纹理
    ↓
阶段4: 外部着色 = f(smooth_iter) IQ调色板
    ↓
阶段5: DEM距离估计 → 暗边+光晕
    ↓
阶段6: 独立渲染 Sierpinski 帕斯卡三角背景
    ↓
阶段7: 合成 = where(interior, interior_color, 
               where(sierpinski, sierpinski_bg, exterior_color))
        叠加DEM边缘
    ↓
    输出最终图像
```
