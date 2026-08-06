# 逆M_DomainColoring域着色算法说明

> 灵感来源：Wikimedia Commons [Color Complex Plot](https://commons.wikimedia.org/wiki/File:Color_complex_plot.jpg)
> 改编适配：逆曼德博水滴分形（基于最终z值）
> 日期：2026-07-17

---

## 一、原始算法原理

Domain Coloring（域着色）是一种复变函数的可视化技术，将复平面上的每个点映射为颜色：

- **色相 (Hue)** = arg(z) / 2π （辐角 → 颜色）
- **饱和度 (Saturation)** = f(|z|) （模长 → 饱和度）
- **明度 (Value)** = f(|z|) （模长 → 亮度）

这种方法可以清晰地显示复变函数的零点、极点和分支切割。

---

## 二、逆M适配思路

**核心思想**：对逆M迭代后的最终 `z` 值进行域着色，将复平面上的每个点的性质映射为颜色。

### 2.1 使用最终z值

逆M迭代结束后，每个点的 `z` 值蕴含了丰富的信息：
- 内部点：z 保持有界（收敛）
- 外部点：z 逃逸到无穷大

我们只对 interior 区域（水滴内部）进行着色。

### 2.2 数据映射

```python
def render_domain_coloring(z, w, h, interior):
    img = np.zeros((h, w, 3), dtype=np.float64)
    
    # 只在 interior 区域处理
    zi = z[interior]
    
    # 计算辐角和模长
    arg = np.angle(zi)              # 辐角 (-π, π)
    mag = np.sqrt(zi.real**2 + zi.imag**2 + 1e-30)  # 模长
    
    # 域着色映射
    hue = (arg + np.pi) / (2 * np.pi)   # 映射到 [0,1]
    log_mag = np.log(mag) / 8.0         # 对数模长
    sat = 0.6 + 0.4 * (1 - np.clip(log_mag, 0, 1))
    val = 0.3 + 0.7 * np.clip(log_mag, 0, 1)
    
    rgb = hsv_to_rgb(hue, sat, val)
    img[interior] = rgb
    img[~interior] = 0                  # exterior 黑底
    return np.rot90(img, k=2)           # 水滴朝上
```

---

## 三、算法实现流程

### 3.1 迭代引擎

使用标准逆M迭代公式，返回最终的 `z` 值：

```python
ic, trap, z, dz, interior, co = compute_inverse_m(RES, RES)
```

### 3.2 域着色细节

| 映射 | 公式 | 说明 |
|------|------|------|
| 色相 | `(arg + π) / (2π)` | 辐角均匀分布在整个色相环 |
| 饱和度 | `0.6 + 0.4 * (1 - clip(log_mag, 0, 1))` | 模长越大，饱和度越低 |
| 明度 | `0.3 + 0.7 * clip(log_mag, 0, 1)` | 模长越大，明度越高 |

### 3.3 黑色背景处理

```python
def apply_interior_mask(img, interior):
    img[~interior] = 0  # exterior 设为黑色
    return img
```

---

## 四、关键技术要点

### 4.1 复数域着色 ✓

- 使用迭代后的最终 `z` 值
- 色相由辐角决定，展示复平面方向信息
- 饱和度和明度由模长决定，展示"深度"信息

### 4.2 只对 interior 着色 ✓

- 水滴外部区域保持纯黑
- 突出逆M水滴的形状
- 符合水滴分形的视觉特征

### 4.3 等轴比视图 ✓

- 使用 `RES×RES` 正方形数组
- RE轴和IM轴物理尺度相等
- 水滴比例真实

---

## 五、参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| MAX_ITER | 250 | 最大迭代次数 |
| 色相映射 | (arg+π)/(2π) | 辐角→色相 |
| 模长缩放 | log(mag)/8.0 | 对数压缩 |
| 饱和度 | 0.6+0.4*(1-clipped) | 模大则饱和度低 |
| 明度 | 0.3+0.7*clipped | 模大则亮度高 |
| 旋转 | np.rot90(k=2) | 水滴朝上 |

---

## 六、输出结果

- 文件：`逆M_DomainColoring域着色.png`
- 尺寸：1024×1024px（可调整）
- 格式：PNG（无损压缩）
- 特点：黑底 + 水滴内部复数域着色彩色图，水滴朝上

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
