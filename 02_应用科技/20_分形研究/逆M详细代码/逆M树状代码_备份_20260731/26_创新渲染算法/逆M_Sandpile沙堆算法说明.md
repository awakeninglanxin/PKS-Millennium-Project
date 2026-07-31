# 逆M_Sandpile沙堆算法说明

> 灵感来源：Wikimedia Commons [Backtang2 (Sandpile)](https://commons.wikimedia.org/wiki/File:Backtang2.png)
> 改编适配：逆曼德博水滴分形（逃逸迭代数驱动）
> 日期：2026-07-17

---

## 一、原始算法原理

沙堆自组织临界模型（Bak-Tang-Wiesenfeld Sandpile Model）是一种经典的自组织临界现象模型：

```
规则：
- 每个格子有一个"高度"值 h
- 当 h ≥ 4 时，格子"崩塌"，将4个单位分配给四个邻居
- h = h - 4, neighbor += 1 （上/下/左/右各+1）
```

经过多次崩塌后，系统达到自组织临界状态，形成分形图案——这就是著名的沙堆分形。

---

## 二、逆M适配思路

**关键改进**：用逆M的**逃逸迭代数 (ic)** 作为"沙堆高度"，而不是随机初始化的沙粒。这样沙堆纹理就与逆M水滴形状绑定。

### 2.1 逆M数据的选用

- **逃逸迭代数 (ic)**: 每个点逃逸前的迭代次数，反映点的"深度"
- ic 值在 interior 区域有丰富分布，适合作为沙堆高度

### 2.2 数据映射

```python
# 逃逸迭代数 → 沙堆高度
height[interior] = ic[interior] / MAX_ITER * 30  # 缩放后作为初始高度
```

---

## 三、算法实现流程

### 3.1 初始化沙堆高度

```python
def render_sandpile(ic, w, h, interior):
    img = np.zeros((h, w, 3), dtype=np.float64)
    
    # 只用 interior 的 ic 值作为高度
    height = np.zeros_like(ic, dtype=np.float32)
    height[interior] = ic[interior].astype(np.float32) / float(MAX_ITER) * 30
    
    # 沙堆松弛迭代（扩散模拟）
    kernel = np.array([[0, 0.2, 0], [0.2, -1, 0.2], [0, 0.2, 0]], dtype=np.float32)
    for _ in range(15):
        relaxed = convolve2d(height, kernel, mode='same', boundary='symm')
        height = np.maximum(relaxed, 0)
```

### 3.2 四色映射

将高度值映射到四种颜色（白、红、绿、蓝）：

```python
co = height * 4              # 缩放
i0 = (co.floor() % 4).astype(int)  # 0-3 索引颜色

colors = np.array([
    [1,1,1],  # 0=白
    [1,0,0],  # 1=红
    [0,1,0],  # 2=绿
    [0,0,1]   # 3=蓝
])
img[:] = colors[i0]

# 黑色背景处理
img = apply_interior_mask(img, interior)
return np.rot90(img, k=2)     # 水滴朝上
```

### 3.3 边界处理修正

原代码使用 `boundary='reflect'` 不被 `convolve2d` 接受，已修复为：

```python
boundary='symm'  # 对称边界
```

---

## 四、关键技术要点

### 4.1 逃逸迭代数驱动 ✓

- 用 `ic` 值初始化沙堆高度，而非随机数值
- 高迭代数的区域（更靠近水滴内部）沙堆更高
- 沙堆扩散过程产生自然的纹理过渡

### 4.2 自组织临界模拟 ✓

- 使用松弛迭代模拟沙粒扩散
- 最终形成类似 Bak-Tang-Wiesenfeld 模型的图案
- 四色系统增强视觉对比度

### 4.3 黑底与水滴方向 ✓

- exterior 区域设为纯黑
- `np.rot90(k=2)` 旋转使水滴朝上
- 等轴视图，水滴比例正确

---

## 五、参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| MAX_ITER | 250 | 最大迭代次数 |
| 初始高度缩放 | ×30 | ic 映射到合适范围 |
| 松弛次数 | 15 | 沙堆扩散迭代 |
| 卷积核 | [[0,0.2,0],[0.2,-1,0.2],[0,0.2,0]] | 中心减邻加 |
| 边界条件 | symm | 对称填充 |
| 颜色数 | 4 (白红绿蓝) | 四色系统 |
| 旋转 | np.rot90(k=2) | 水滴朝上 |

---

## 六、输出结果

- 文件：`逆M_Sandpile沙堆.png`
- 尺寸：1024×1024px（可调整）
- 格式：PNG（无损压缩）
- 特点：黑底 + 水滴内部沙堆自组织临界四色图，水滴朝上
