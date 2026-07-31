# 逆M创新渲染算法总述

> 灵感来源：Wikimedia Commons 5种渲染算法
> 改编适配：逆曼德博水滴分形
> 日期：2026-07-17

---

## 一、项目概述

本项目将 Wikimedia Commons 上的5种经典渲染算法灵感，全部改编到逆曼德博（Inverse Mandelbrot）水滴分形的渲染中，生成全新的视觉效果。

### 1.1 灵感来源

| # | 算法名称 | Wikimedia文件 | 逆M改编版本 |
|---|----------|---------------|------------|
| 1 | XOR 纹理 | XOR_texture.png | 逆M_XOR位运算纹理 |
| 2 | Square Tile 分形 | Square_tile_fractal.png | 逆M_SquareTile分形 |
| 3 | 域着色 | Color_complex_plot.jpg | 逆M_DomainColoring域着色 |
| 4 | 沙堆模型 | Backtang2.png | 逆M_Sandpile沙堆 |
| 5 | 双曲镶嵌 | Poincare_h7.svg | 待实现 |

### 1.2 核心原则

- **全部基于逆M数据驱动**：只用逆M迭代产生的 `ic`（逃逸迭代）、`trap`（轨道陷阱）、`z`（最终值）等数据，**不使用全局像素坐标**作为纹理源
- **等轴视图**：RE轴和IM轴物理尺度一致，`RES×RES` 正方形视图
- **水滴朝上**：所有图使用 `np.rot90(img, k=2)` 旋转180°
- **黑底突出水滴**：exterior 区域设为纯黑色，只显示 interior 水滴区域

---

## 二、逆M迭代引擎

### 2.1 数学公式

逆M集的迭代公式为：

$$z_{n+1} = z_n^2 + c_{\text{eff}}, \quad c_{\text{eff}} = \frac{1}{c}$$

其中 `c` 是复平面上的像素点，`1/c` 是反演变换。

### 2.2 引擎参数

```python
# 逆M取景（等轴比调整后的版本）
RE_MIN = -0.79;  RE_MAX = 3.46   # 跨度 = 4.25
IM_MIN = -2.12;  IM_MAX = 2.12   # 跨度 = 4.25  → 等轴 ✓
MAX_ITER = 250;  BAILOUT_SQ = 256**2
```

### 2.3 返回数据

`compute_inverse_m(w, h)` 返回：

| 变量 | 类型 | 说明 |
|------|------|------|
| ic | (w,h) float | 逃逸迭代次数 |
| trap | (w,h) float | 轨道陷阱最小值 |
| z | (w,h) complex | 迭代最终z值 |
| dz | (w,h) complex | 导数（用于DEM） |
| interior | (w,h) bool | interior掩码 |
| co | (w,h) complex | 反演空间坐标 |

---

## 三、四种渲染算法实现

### 3.1 XOR 位运算纹理

**原理**：用逃逸迭代数 `ic` 做高位-低位XOR运算，生成位图纹理。

**关键代码**：
```python
ic_int = (ic[interior] / MAX_ITER * 127).astype(np.int32)
hi = (ic_int >> 4) & 0xF
lo = ic_int & 0xF
xor_val = (hi ^ lo) / 15.0
```

**算法文件**：`逆M_XOR位运算纹理算法说明.md`

### 3.2 Square Tile 分形

**原理**：用轨道陷阱 `trap` 做高低8位XOR，产生方格纹理。

**关键代码**：
```python
trap_int = (trap_norm * 255).astype(np.int32)
hi = (trap_int >> 8) & 0xFF
lo = trap_int & 0xFF
xor_hl = (hi ^ lo) / 255.0
```

**算法文件**：`逆M_SquareTile分形算法说明.md`

### 3.3 Domain Coloring 域着色

**原理**：对最终 `z` 值做域着色，色相=辐角，饱和度/明度=模长。

**关键代码**：
```python
arg = np.angle(zi)
hue = (arg + np.pi) / (2*np.pi)
mag = np.sqrt(zi.real**2 + zi.imag**2 + 1e-30)
log_mag = np.log(mag) / 8.0
```

**算法文件**：`逆M_DomainColoring域着色算法说明.md`

### 3.4 Sandpile 沙堆

**原理**：用逃逸迭代数初始化沙堆高度，做松弛迭代模拟自组织临界。

**关键代码**：
```python
height[interior] = ic[interior] / MAX_ITER * 30
kernel = [[0,0.2,0],[0.2,-1,0.2],[0,0.2,0]]
relaxed = convolve2d(height, kernel, boundary='symm')
```

**算法文件**：`逆M_Sandpile沙堆算法说明.md`

---

## 四、通用处理流程

### 4.1 黑底掩膜

```python
def apply_interior_mask(img, interior):
    img[~interior] = 0   # exterior 设为黑色
    return img
```

所有渲染器最后都调用此函数，确保只有水滴内部有颜色。

### 4.2 水滴朝上旋转

```python
return np.rot90(img, k=2)   # 旋转180°
```

### 4.3 等轴比设置

通过统一 RE 和 IM 轴的跨度实现 `axis_equal`：

```python
uni_span = min(re_span, im_span)   # 取较小跨度为统一尺度
```

---

## 五、执行与输出

### 5.1 执行方式

```bash
# 本地执行
python 逆M_algorithm_innovation_suite_gpu.py 1024

# 或通过GPU服务器（如可用）
ssh -p 27341 root@connect.nmb1.seetacloud.com "python 逆M_algorithm_innovation_suite_gpu.py 1024"
```

### 5.2 输出文件

| 文件 | 尺寸 | 格式 | 特点 |
|------|------|------|------|
| 逆M_XOR位运算纹理.png | 1024×1024 | PNG | 黑底+XOR位运算纹理 |
| 逆M_SquareTile分形.png | 1024×1024 | PNG | 黑底+SquareTile分形 |
| 逆M_DomainColoring域着色.png | 1024×1024 | PNG | 黑底+复数域着色 |
| 逆M_Sandpile沙堆.png | 1024×1024 | PNG | 黑底+沙堆自组织临界 |

所有图片均：
- ✅ 等轴视图（像素长宽比1:1）
- ✅ 水滴朝上（旋转180°）
- ✅ 黑色背景（exterior=黑）
- ✅ 仅 interior 着色

### 5.3 性能数据（1024×1024）

- 计算逆M集：约 0.5s
- 4种渲染总计：约 16-25s
- 全部输出大小：约 1.2MB

---

## 六、后续扩展计划

| # | 计划 | 状态 |
|---|------|------|
| 1 | Poincare 双曲镶嵌 | 待实现 |
| 2 | 增加高分辨率（2048/4096） | 待实现 |
| 3 | 调整纹理参数（XOR移位、SquareTile对数系数等） | 待实现 |
| 4 | 增加更多配色方案 | 待实现 |
| 5 | 批量生成不同参数组合的对比图 | 待实现 |

---

## 七、相关参考文献

1. Wikimedia Commons - [XOR Texture](https://commons.wikimedia.org/wiki/File:XOR_texture.png)
2. Wikimedia Commons - [Square Tile Fractal](https://commons.wikimedia.org/wiki/File:Square_tile_fractal.png)
3. Wikimedia Commons - [Color Complex Plot](https://commons.wikimedia.org/wiki/File:Color_complex_plot.jpg)
4. Wikimedia Commons - [Backtang2 Sandpile](https://commons.wikimedia.org/wiki/File:Backtang2.png)
5. Ultra Fractal Forum - Formula Question (2015)
6. MIT OpenCourseWare - Complex Analysis: Domain Coloring
