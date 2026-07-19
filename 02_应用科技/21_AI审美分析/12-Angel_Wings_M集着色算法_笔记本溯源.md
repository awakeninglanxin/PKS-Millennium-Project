# "Angel Wings" M集渲染算法 + Sutherland Creek 笔记本溯源

> 来源：Paul Bourke mandelbrot 页 + Klaus Messner 贡献 + Amazon 产品分析
> 日期：2026-07-19

---

## 一、Sutherland Creek 笔记本：只是 POD 商品

| 项 | 内容 |
|:---|:---|
| ASIN | 1719829101 |
| 出版社 | Sutherland Creek (Amazon KDP 按需印刷) |
| 页面 | 200页 College Ruled, 7.5"×9.75" |
| 封面 | 标准 Deep Zoom M集渲染（非独门算法） |
| 设计名 | "Ashir" / "Angel Wings" |
| 链接 | amazon.com/dp/1719829101 |

**本质**：Amazon KDP 的 POD 笔记本，封面图来自公共领域的 M 集渲染。不是某本书或某位艺术家的专有算法。"Ashir"只是设计命名，不是作者名。

---

## 二、真正的 "Angel Wings" 效果：Klaus Messner 着色法

Paul Bourke 在其 Mandelbrot 页面（paulbourke.net/fractals/mandelbrot）的 "Wings" 节记录了这种独特的着色技术：

> *"A relatively unexplored variation is to shade the plane based upon when the series decreases three times in succession. The Mandelbrot grow 'wings' and discs at the peripheral points."*

### 2.1 算法核心

不按迭代次数着色——按 **|z| 连续下降次数** 着色。

```python
def angel_wings_mandelbrot(width, height, x_min, x_max, y_min, y_max, max_iter=500):
    """
    Klaus Messner 'Wings' 着色法
    着色依据：逃逸前 |z| 连续下降的次数
    """
    wings = np.zeros((height, width), dtype=np.int32)
    final_iter = np.zeros((height, width), dtype=np.int32)
    
    dx = (x_max - x_min) / width
    dy = (y_max - y_min) / height
    
    for py in range(height):
        c_imag = y_max - py * dy
        for px in range(width):
            c_real = x_min + px * dx
            
            z_real, z_imag = 0.0, 0.0
            prev_mag = 0.0
            decrease_streak = 0
            max_streak = 0
            iter_count = 0
            
            for n in range(max_iter):
                # 标准 M 集迭代
                z_real_new = z_real * z_real - z_imag * z_imag + c_real
                z_imag_new = 2.0 * z_real * z_imag + c_imag
                z_real, z_imag = z_real_new, z_imag_new
                
                current_mag = z_real * z_real + z_imag * z_imag
                
                # ★ 关键：检测连续下降 ★
                if n > 0 and current_mag < prev_mag:
                    decrease_streak += 1
                    if decrease_streak > max_streak:
                        max_streak = decrease_streak
                else:
                    decrease_streak = 0
                
                prev_mag = current_mag
                
                if current_mag > 4.0:
                    iter_count = n
                    break
            else:
                iter_count = max_iter  # 在M集内部
            
            wings[py, px] = max_streak
            final_iter[py, px] = iter_count
    
    return wings, final_iter


def wings_color_map(wings, final_iter, max_iter):
    """
    Wings着色方案：
    - 下降streak >= 3 → 金色"翅膀"色调
    - streak = 1-2   → 过渡色
    - streak = 0     → 标准逃逸时间色（蓝色调）
    - 在M集内部       → 黑色
    """
    height, width = wings.shape
    rgb = np.zeros((height, width, 3), dtype=np.float64)
    
    for py in range(height):
        for px in range(width):
            streak = wings[py, px]
            iteration = final_iter[py, px]
            
            if iteration >= max_iter:
                # M集内部 = 黑
                rgb[py, px] = [0, 0, 0]
            elif streak >= 3:
                # "翅膀"区域 = 金/橙色
                intensity = min(1.0, streak / 10.0)
                rgb[py, px] = [0.95, 0.7, 0.1 + 0.3 * intensity]
            elif streak >= 1:
                # 过渡 = 暖色
                rgb[py, px] = [0.6, 0.3, 0.5]
            else:
                # 标准逃逸 = 冷色
                t = iteration / max_iter
                rgb[py, px] = [0.1, 0.2 + 0.5 * t, 0.3 + 0.7 * t]
    
    return np.clip(rgb, 0, 1)


# ─── 使用示例：渲染 Angel Wings 效果 ───
def render_angel_wings():
    # Klaus Messner 记录的三个 Wing 出现位置之一
    x_center, y_center = -1.04180483110546, 0.346342664848392
    zoom = 0.05  # 小范围放大
    
    width, height = 1200, 900
    x_min = x_center - zoom
    x_max = x_center + zoom
    y_min = y_center - zoom * height / width
    y_max = y_center + zoom * height / width
    
    print(f"Rendering Angel Wings at {x_center} + {y_center}i...")
    wings, iters = angel_wings_mandelbrot(width, height, x_min, x_max, y_min, y_max, max_iter=800)
    rgb = wings_color_map(wings, iters, 800)
    
    plt.figure(figsize=(12, 9))
    plt.imshow(rgb, extent=[x_min, x_max, y_min, y_max])
    plt.title("Mandelbrot Angel Wings (Klaus Messner method)")
    plt.savefig('mandelbrot_angel_wings.png', dpi=150)
    print("Saved: mandelbrot_angel_wings.png")
```

### 2.2 三个效果最佳的坐标

Klaus Messner 贡献了三个 Wing 效果最明显的位置：

| # | c 坐标 | 描述 |
|:---|:---|:---|
| 1 | **-1.0418 + 0.3463i** | 经典 "天使之翼" — 外围点长出的羽状结构 |
| 2 | -0.7511 − 0.1168i | Seahorse Valley 附近的 Wing 变体 |
| 3 | -0.8122 − 0.1855i | 与 Seahorse 螺旋交替的 Wing 纹理 |

---

## 三、"最美渲染"到底指什么算法？

### 3.1 如果是说 Sutherland Creek 封面 → 就是标准逃逸时间 + 渐变调色板

笔记本封面是市面上最常见的"成品 M 集渲染"，使用的就是最基础的 Escape Time Algorithm + 平滑着色：

```python
# 市面上 99% 的 M 集装饰画用这个
nu = n + 1 - log2(log2(|z|))  # Normalized Iteration Count
color = palette[nu / max_iter * len(palette)]
```

没有 DEM，没有 Wings，没有特殊算法。**你觉得好看是因为颜色配得好，不是算法特殊。**

### 3.2 如果是说 Angel Wings 效果 → 就是 Klaus Messner 的 streak-counting

这是几十年来几乎没人复现的独特着色法。视觉上会在 M 集的"外围点"处产生羽状/翅膀状的纹理结构，完全不同于标准渲染。**算法极简单，效果极独特。**

### 3.3 如果是说 Peitgen 封面 → 就是 DEM/M

上一份文档已详细拆解。DEM 用浮点距离代替整数迭代计数，消除了 banding，细丝结构全可见。

---

## 四、三者的对比

| 算法 | 创始人 | 年份 | 视觉特征 | 适合什么 |
|:---|:---|:---:|:---|:---|
| Escape Time (标准) | Brooks/Matelski | 1978 | 色带(banding)，粗丝线 | 入门、快速预览 |
| **DEM/M** | Thurston → Peitgen/Richter | 1986 | 无banding，任意细丝可见 | **出版级"最美"渲染** |
| **Angel Wings** | Klaus Messner | ~2000s | 外围羽状翅膀纹理 | **独特的艺术效果** |
| Normalized Iteration | 多人 | 1990s | 去banding但不如DEM精确 | 中等质量 |

**你最可能在"最美M分形渲染.jpg"中看到的算法**：

如果不是 Peitgen 封面（橙色渐变 + Seahorse Valley），那大概率是 **DEM/M + 精心调色**的结果。Angel Wings 太独特（羽状纹理很显眼），容易辨认。

---

## 五、如何鉴别你那张图的算法

如果有这张图在手，看三个特征：

| 特征 | = DEM/M | = Angel Wings | = 标准Escape Time |
|:---|:---:|:---:|:---:|
| 边界处有可见色带(banding)？ | ❌ 无 | ❌ 无 | ✅ 有 |
| 有羽状/翅膀状的纹理？ | ❌ 无 | ✅ 有 | ❌ 无 |
| 极细丝线(触须)可见？ | ✅ 全部可见 | ✅ 部分 | ❌ 丢失 |
| 内部纯黑？ | ✅ | ✅ | ✅ |

---

## 六、对你的逆M代码的建议

**如果你追求的是"最美"视觉效果** → 用 DEM/M（前一份文档已给代码）

**如果你想尝试独一无二的艺术效果** → 用 Angel Wings 着色法。改编到逆M也很简单：

```python
# 逆M Angel Wings 改编版
z = c
prev_mag = abs(z)
streak = 0

for n in range(max_iter):
    z = cmath.sqrt(z - c)  # 逆迭代
    current_mag = abs(z)
    
    if current_mag < prev_mag:
        streak += 1
    else:
        streak = 0
    prev_mag = current_mag
    
    if current_mag < 1e-6:
        # 收敛到中心 = M集内部
        break

# streak >= 3 = "逆M翅膀"着色
```
