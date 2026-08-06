# UF22+ 帕斯卡三角 Mobius 映射 — 算法说明

> 基于元宝《维度数学漫步》5层拆解 → 逆M逃逸区纹理填充

---

## 核心思路

逆Mandelbrot集（蓝色水滴）的**逃逸区域**用帕斯卡三角 mod 2（Sierpinski分形）填充，通过Mobius变换将纹理弯曲到复平面。

```
像素w → Mobius f_M(w) → 三角格(n,k) → Lucas (k&~n)==0 → 金/钢蓝双色
```

## 知识链 (元宝5层拆解)

| 层 | 概念 | 在本算法中的应用 |
|------|------|------|
| 1 复平面升维 | 实数→复数 (x+iy) | 像素坐标→复数w |
| 2 线性变换 | 旋转+缩放 | — |
| 3 非线性 | z² 和 1/z 反演 | c_eff = 1/w (逆M)；Mobius f(z)=(az+b)/(cz+d) |
| 4 Mandelbrot | 迭代 z←z²+c | 逆M逃逸检测 |
| 5 欧拉公式 | e^(iθ) 旋转 | (未来可加入角向着色) |

## Mobius 变换

$$f_M(z) = \frac{az + b}{cz + d}$$

| 方案 | a,b,c,d | 效果 |
|------|------|------|
| A 纯反演 | 0,1,1,0 → f(z)=1/z | 内外翻转 |
| **B z/(z-2)** | **1,0,1,-2** | **极点拉伸 (推荐)** |
| C Cayley | 1,-i,1,i | 半平面映射 |

推荐方案B: f(z)=z/(z-2) 将点2映射到∞，产生极向拉伸。

## 帕斯卡三角 (Sierpinski gasket)

### 三角格坐标

将复平面坐标 (x,y) 映射到等边三角形格 (n,k):

```
b = 2*(y+oy) / (scale * sqrt(3))
a = (x+ox) / scale - b/2
n = round(a+b),  k = round(b)
```

### Lucas 定理

二项式系数 C(n,k) mod 2 = 1 ⇔ (k & ~n) == 0

### 填充率

帕斯卡三角 mod 2 形成Sierpinski gasket，填充密度随行数增加递减：

| 行数范围 | 填充率 |
|------|------|
| 0~10 | ~50% |
| 0~30 | ~35% |
| 0~50 | ~25% |
| 0~100 | ~18% |

## 关键参数

| 参数 | 推荐值 | 说明 |
|------|------|------|
| Mobius方案 | B: z/(z-2) | 最有趣的空间扭曲 |
| scale | 0.06~0.12 | 越小=三角越大=越稀疏 |
| offset_x/y | 0.15~0.3 | 使有效三角区域覆盖更多逃逸像素 |
| bailout | 50 | 逆M需要较大逃逸半径 |
| max_iter | 300 | 逆M需要更多迭代 |

## 着色方案

| 区域 | 颜色 | RGB |
|------|------|------|
| 逆M内部(水滴) | 深蓝 | (0.02,0.04,0.14) |
| Pascal填充 | 暖金 | (0.95,0.70,0.10) |
| Pascal空白 | 钢蓝 | (0.06,0.12,0.35) |
| Mobius奇点 | 极暗 | (0.03,0.03,0.10) |

## 文件清单

| 文件 | 说明 |
|------|------|
| `main.py` | 原始UF22图像映射(日落渐变) |
| `main_pascal_mobius.py` | 初版 (scale太大,全图归0) |
| `main_pascal_mobius_v2.py` | 三方案并行对比 |
| `main_pascal_mobius_v3.py` | 单一方案精细调参 |
| `main_pascal_mobius_v4.py` | **当前版本** — 高对比度修复 |
| `UF22_帕斯卡Mobius_v4.png` | 最终渲染结果 |

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
