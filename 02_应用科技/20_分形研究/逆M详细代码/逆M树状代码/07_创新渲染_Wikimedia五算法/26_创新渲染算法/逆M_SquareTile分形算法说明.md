# 逆M_SquareTile分形算法说明

> 灵感来源：Wikimedia Commons [Square Tile Fractal](https://commons.wikimedia.org/wiki/File:Square_tile_fractal.png)
> 改编适配：逆曼德博水滴分形（轨道陷阱驱动）
> 日期：2026-07-17

---

## 一、原始算法原理

Square Tile 分形算法利用位运算生成交互的方形网格图案。典型的计算公式为：

```
g(i, j) = (i & (j - 2*(i ^ j) + j) & i) % 255
```

这个公式通过位与（&）、位异或（^）、减法等多种运算，产生复杂而规则的几何图案，类似瓷砖拼接的效果。

---

## 二、逆M适配思路

**关键改进**：从使用全局像素坐标改为使用**逆M轨道陷阱数据**驱动。轨道陷阱记录了迭代过程中 |z|² 的最小值，这反映了轨道接近原点的程度，是逆M分形中非常重要的特征量。

### 2.1 轨道陷阱 (Orbit Trap)

在逆M迭代过程中，记录每个点的最小轨道值：

$$trap_n = \min(|z_n|^2, \text{trap}_{n-1})$$

- 轨道越接近原点，`trap` 值越小
- 水滴内部的点具有不同的轨道分布

### 2.2 数据映射

```python
# 原始坐标 → 逆M轨道陷阱
# 旧版（错误）: 用全局像素坐标 (ii, jj) 做位运算 → 与水滴无关
# 新版（正确）: 用逆M轨道陷阱 trap 做位运算 → 纹理依附于水滴形状
```

---

## 三、算法实现流程

### 3.1 迭代引擎与陷阱记录

```python
# 在 compute_inverse_m 中记录 trap
trap = np.full(ce.shape, 1e30, dtype=np.float64)
for i in range(MAX_ITER):
    ...
    m2 = za.real**2 + za.imag**2
    trap[idx] = np.minimum(trap[idx], m2)  # 轨道陷阱更新
```

### 3.2 Square Tile 纹理生成

```python
def render_square_tile(ic, co, w, h, interior):
    img = np.zeros((h, w, 3), dtype=np.float64)
    
    # 只在 interior 区域处理，用轨道陷阱
    safe_log = np.abs(np.log(trap[interior] + 1e-30))  # 对数拉伸 + 保号
    trap_norm = safe_log / safe_log.max()              # 归一化到 [0,1]
    trap_int = (trap_norm * 255).astype(np.int32)      # 映射到 0-255
    
    # 高位与低位交互做位运算
    hi = (trap_int >> 8) & 0xFF    # 高8位
    lo = trap_int & 0xFF           # 低8位
    xor_hl = (hi ^ lo) / 255.0     # XOR归一化
    
    # HSV色彩映射
    hue = xor_hl * 4               # 多周期色相
    sat = 0.8
    val = 0.1 + 0.9 * xor_hl
    rgb = hsv_to_rgb(hue, sat, val)
    
    img[interior] = rgb
    img[~interior] = 0             # exterior 黑底
    return np.rot90(img, k=2)      # 水滴朝上
```

### 3.3 数值安全处理

原始代码中 `log1p(-log(trap+1e-30))` 会导致负数输入产生 NaN，已修复为：

```python
safe_log = np.abs(np.log(trap + 1e-30))  # 取绝对值保证正值
```

---

## 四、关键技术要点

### 4.1 轨道陷阱驱动 ✓

- 使用逆M迭代过程中的 `trap` 值，而非全局像素坐标
- 轨道值反映点与迭代轨道的接近程度
- 产生与水滴形状紧密相关的纹理

### 4.2 位运算纹理 ✓

- 高8位与低8位做XOR，产生细密纹理
- 对数拉伸增强低值区的对比度
- 纹理随轨道陷阱值变化而自然分布

### 4.3 黑底与水滴方向 ✓

- exterior 区域设为纯黑 (0,0,0)
- `np.rot90(k=2)` 旋转180°使水滴朝上
- 等轴视图，水滴比例正确

---

## 五、参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| MAX_ITER | 250 | 最大迭代次数 |
| 陷阱记录 | min(|z|²) | 轨道陷阱 |
| 对数拉伸 | |log(trap)| | 增强细节 |
| 位运算 | (trap>>8) ^ (trap&255) | 高低8位XOR |
| 色相周期 | hue * 4 | 多周期变化 |
| 旋转 | np.rot90(k=2) | 水滴朝上 |

---

## 六、输出结果

- 文件：`逆M_SquareTile分形.png`
- 尺寸：1024×1024px（可调整）
- 格式：PNG（无损压缩）
- 特点：黑底 + 水滴内部SquareTile位运算纹理，水滴朝上
