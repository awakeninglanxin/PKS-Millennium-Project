# 逆M RouteB — 完整数学工序 (v5最终版)

> 日期：2026-07-29  
> GPU：RTX 4090 + CuPy (TIA全场0.9s@3000², 2.3s@6000²)  
> 最终输出：6000×6000 素描等高线  
> 锚点：360个TIA自动检测超吸引中心, 半径1200→96px自然缩放

---

## 一、工序总览

```
GPU TIA计算 (2500²像素, 200轮迭代, 0.7s)
  └→ TIA有界mask (ext = 水滴外部)
       └→ 双尺度局部极小检测 (size=5+3)
            └→ 取前80个最强TIA中心
                 ├─ 合并27个已知泡中心 → 107锚点
                 └─ 每锚点独立距离场棋盘
                      └→ 调制金涟漪
                           └→ 白底藏青纹 + 醇金涟漪 + 紫色轮廓
```

---

## 二、TIA（三角不等式平均）— 核心数学

### 2.1 定义

在标准M集迭代 $z_{n+1} = z_n^2 + c_{\text{eff}}$ 中，每一步计算轨道的相对步长：

$$
r_n = \frac{|z_{n+1} - z_n|}{|z_{n+1}|}
$$

对所有 $N$ 次迭代累积平均：

$$
\operatorname{TIA}(c) = \frac{1}{N}\sum_{n=0}^{N-1} r_n
$$

### 2.2 逆M适配

逆M集用 $c_{\text{eff}} = 1/c$ 代入迭代：

$$
z_{n+1} = z_n^2 + \frac{1}{c}
$$

**关键发现（修正 2026-07-29）**：在逆M集中：

| 变量 | 数学意义 | 视觉位置 |
|------|:--------:|:--------:|
| `ext` = 有界区（`alive`） | 400轮未逃逸 | **水滴外部** |
| `interior` = 逃逸区（`~alive`） | 中途逃逸 | **水滴内部** |

UF11 标准版着色于 `ext`（有界区 = 水滴外部），TIA场在该区域呈现出各Farey泡中心的极小值。

### 2.3 TIA在泡中心的极小值原理

超吸引中心 $c^*$ 处乘数 $\lambda = 0$，轨道以二次收敛速度逼近不动点：

$$
|z_{n+1} - z_n| \approx |z_n|^2, \quad r_n \approx |z_n| \to 0
$$

因此 TIA 在 $c^*$ 处取全域极小值。非中心点的乘数 $\lambda \neq 0$，收敛为线性，TIA值更高。

### 2.4 UF11 标准参数

```
bailout = 50   (逃逸半径√2500, 非1024!)
max_iter = 200 (非400!)
```

**重要性**：较小的 bailout 创造更锐利的 TIA 梯度 → 极小值可检测。大 bailout (=1024) 导致梯度模糊 → 极小值被淹没。

---

## 三、TIA 自动检测 Farey 中心

### 3.1 搜索区域

TIA 检测限定在逆M水滴的有界区 = `ext` 区域，再用水滴边界框裁剪：

$$
\operatorname{Re} \in [-1.5,\; 4.2], \quad |\operatorname{Im}| < 1.8
$$

### 3.2 双尺度局部极小检测

**第一尺度**（size=5）：捕捉明显的大泡中心
**第二尺度**（size=3）：补充捕捉边界小泡

$$
\text{local\_min} = \left(\operatorname{TIA} = \min_{N_5}(\operatorname{TIA})\right) \lor \left(\operatorname{TIA} = \min_{N_3}(\operatorname{TIA})\right)
$$

对极小值像素做连通域标记（`scipy.ndimage.label`），提取连通域质心。

### 3.3 TIA值排序截断

原始双尺度检测产生 ~1258 个候选中心，按 TIA 值升序排列（越小越强），**取前80个**：

$$
\mathcal{C}_{\text{TIA}} = \operatorname{sort}(\{c_1, c_2, \ldots, c_{1258}\}, \text{by TIA})[:80]
$$

### 3.4 已知泡中心补充

合并已知32个上半平面超吸引中心（含实轴对称镜像）：

- 心形外扩采样 + P1~P9 泡中心
- 补充TIA检测遗漏的小泡
- 共27个已知中心（含实轴上的无需镜像）

---

## 四、每泡独立局部棋盘格

### 4.1 局部距离场

对每个锚点 $(x_k, y_k)$，计算局部距离场：

$$
d_k(x,y) = \sqrt{(x - x_k)^2 + (y - y_k)^2}
$$

### 4.2 棋盘参数（按泡层级递减）

| 参数 | 公式 | 效果 |
|------|------|------|
| 截止半径 | $R_k = \max\left(15,\; \dfrac{60}{1 + \operatorname{period}_k \times 0.4}\right)$ | 高周期泡半径小 |
| 环数 | $N_k = \max\left(2,\; \operatorname{int}\left(\dfrac{8}{1 + \operatorname{period}_k \times 0.2}\right)\right)$ | 高周期泡环少 |
| 波长 | $\lambda_k = R_k / N_k$ | — |

### 4.3 取模二值棋盘

$$
P_k(x,y) = \left\lfloor \frac{d_k \bmod \lambda_k}{\lambda_k / 2} \right\rfloor \in \{0, 1\}
$$

- $P_k = 0$：亮格，金涟漪强度不变
- $P_k = 1$：暗格，金涟漪压制至 **25%**

### 4.4 多泡调制合并

全局调制场取各泡调制的逐像素取最小值（最暗生效）：

$$
\operatorname{modulation}(x,y) = \min_{k=1}^{107} \operatorname{mod}_k(x,y)
$$

（实际实现：$\operatorname{modulation} \leftarrow \min(\operatorname{modulation}, 0.25)$ 对暗格）

---

## 五、金涟漪干涉场

### 5.1 涟漪源阵容

| 类型 | 数量(上半) | 镜像后 | 说明 |
|------|:---------:|:------:|------|
| 心形外扩(5深度层) | 91×5=455 | ~910 | P0基底 |
| 已知泡中心 | 32 | ~64 | P1~P9 |
| TIA检测中心 | 80 | ~160 | P? (TIA推断) |

### 5.2 级联波叠加

每个源 $(x_k, y_k)$ 产生衰减正弦波：

$$
W_{\text{gold}}(x,y) = \sum_{k} \sin\left(\frac{2\pi d_k}{\lambda_k}\right) \cdot \frac{A_k}{1 + d_k/(R_k/3)} \cdot e^{-d_k/(0.5R_k) \times 1.8}
$$

5层级联参数：

| Level | 外扩 $\alpha$ | $R$ (像素) | $A$ | $\lambda$ |
|:-----:|:------------:|:----------:|:---:|:---------:|
| 0 | 1.12 | 2500 | 1.00 | 180 |
| 1 | 1.30 | 1667 | 0.69 | 120 |
| 2 | 1.55 | 1111 | 0.48 | 80 |
| 3 | 1.80 | 741 | 0.33 | 55 |
| 4 | 2.10 | 494 | 0.23 | 37 |

---

## 六、双场叠加渲染

### 6.1 棋盘调制金涟漪

$$
\text{ripple}(x,y) = W_{\text{gold}}(x,y) \times \operatorname{modulation}(x,y)
$$

### 6.2 醇金渐变着色

$$
I(x,y) = (1 - \alpha) \cdot \text{white} + \alpha \cdot \begin{pmatrix}218 + 37(1-r) \\ 165 + 90(1-r) \\ 32 + 223(1-r)\end{pmatrix}
$$

其中 $\alpha = \text{ripple}^{0.6} \times 0.6$，$r$ 为归一化涟漪强度。

### 6.3 轮廓标记

| 元素 | 颜色 | RGB |
|------|------|-----|
| 主心形轮廓 | 紫色 | (120, 40, 150) |
| 周期2泡 | 深橙 | (180, 120, 40) |
| TIA检测中心 | 红点 | (255, 80, 80) |
| 已知泡中心 | 绿点 | (80, 200, 80) |

### 6.4 朝向

旋转90° CCW使实轴正半轴朝上 → 水滴尖朝上。

---

## 七、性能参数 (RTX 4090)

| 阶段 | 耗时 | 硬件 |
|------|:----:|:----:|
| GPU TIA 全场迭代 | **0.7s** | CuPy/CUDA |
| TIA 极小值检测 | ~1s | CPU |
| 棋盘调制 (107锚点) | ~12s | CPU |
| 金涟漪场 (951源) | ~14s | CPU |
| 渲染 | ~2s | CPU |
| **总计** | **~30s** | |

---

## 八、版本演变索引

| 版本 | 文件 | 核心变化 |
|:----:|------|---------|
| v1 | `archive_v1_3depth/` | 3层心形, 蓝底红涟漪 |
| v2 | `archive_v2_5depth/` | 5层级联, 白底金涟漪 |
| v3 | `archive_v3/` | 6配色对比, 藏青波选中 |
| v4A | `draw_v4_RouteA.py` | 全局pot模棋盘 × 金涟漪 |
| v4B | `gpu_routeB.py` | TIA自动检测(初版, 失败) |
| **v5** | `gpu_routeB_corrected.py` | **RouteB修正: UF11参数×双尺度检测×80TIA中心** |

---

## 九、参考

1. **Douady & Hubbard** (1985). *Étude dynamique des polynômes complexes*. — 心形边界参数化
2. **Wolf Jung** (2002). *mandelbrot-numerics*. — Farey泡对应, 外部角度
3. **UF11 TIA 算法** — 三角不等式平均, 轨道收敛速率测量
4. **UF1 取模棋盘** — `floor((pot%1)/0.5)` 二值棋盘, 环带不累积
5. **Milnor** (2006). *Dynamics in One Complex Variable*. — 超吸引中心, 乘数理论
6. **Richling** (2015). *Inverted Mandelbrot*. — 逆M渲染

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
