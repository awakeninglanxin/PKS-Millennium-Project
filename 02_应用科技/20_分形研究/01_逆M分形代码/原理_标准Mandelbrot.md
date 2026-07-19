# ① 标准Mandelbrot集渲染器

**对应文件**：`分形mandelbrot.py`

---

## 核心算法

### 迭代公式
```
z₀ = 0
zₙ₊₁ = zₙ² + c
逃逸半径：R = 4
```

### Numba JIT 加速
`@jit(nopython=True)` 将Python循环编译为机器码，避免解释器开销：

```python
@jit(nopython=True)
def mandelbrot(c, max_iter):
    z = 0j
    for n in range(max_iter):
        if abs(z) > 4:      # 逃逸半径=4（标准M常用）
            return n
        z = z * z + c
    return max_iter
```

### 像素循环
双层for遍历每个像素的复坐标，逐点计算逃逸时间：
```python
re = xmin + x * (xmax - xmin) / width
im = ymin + y * (ymax - ymin) / height
result[y, x] = mandelbrot(re + 1j * im, max_iter)
```

---

## 核心优化技术（与逆M文件对比基准）

| 技术 | 标准M | 逆M(c倒数法) | 逆M(z倒数法) |
|------|:--:|:--:|:--:|
| 迭代公式 | z²+c | z²+(1/c) | 1/z+c |
| 逃逸半径 | 4 | 50 | 10 |
| Numba | ✓ | ✓ | ✓ (parallel) |
| 平滑逃逸 | ✗ | ✓ | ✓ |
| 直方图均衡 | ✗ | ✓ (v2) | ✗ |
| 多初值 | ✗ | ✗ | 4色/8色 |
| 视图缓存 | ✗ | ✓ (细腻gpu) | ✗ |
| mpmath高精度 | ✗ | ✓ (细腻) | ✗ |

---

## 交互功能

| 操作 | 功能 |
|------|------|
| 左键拖框 | 放大选中区域 |
| 右键 / Backspace | 返回上一级视图 |
| 1-9 | 设置迭代次数（256→2304） |

---

## 关键数学性质

1. **逃逸半径 R=4**：对标准M集，|c|≤2 时 |zₙ|>2 确保发散。R=4 提供了安全余量，且不影响集合判定
2. **原点必然在M内**：z₀=0，若 c=0，zₙ 恒为0→never escapes
3. **实轴截距 [-2, 1/4]**：M ∩ ℝ 的精确范围
