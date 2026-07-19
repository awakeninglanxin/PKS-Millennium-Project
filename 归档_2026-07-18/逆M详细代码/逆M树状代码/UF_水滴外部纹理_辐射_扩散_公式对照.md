# 逆Mandelbrot集水滴外部着色算法 — 专业公式与工程手册

> **Inverse Mandelbrot Set: Exterior Droplet Coloring Algorithms — Formulae and Implementation Guide**
>
> 版本 1.0 | 2026-07-13 | Senior Developer
>
> 聚焦于在逆M集水滴的几何外部（即参数空间 interior 区域）产生纹理、辐射与扩散视觉效果的着色算法。

---

## 目录

1. [理论基础：逆M集的着色区域反转](#1-理论基础逆m集的着色区域反转)
2. [A类：原生外部着色算法](#2-a类原生外部着色算法)
3. [B类：边界双向辐射算法](#3-b类边界双向辐射算法)
4. [C类：可扩展的外部着色算法](#4-c类可扩展的外部着色算法)
5. [约束条件：不可外部化的算法群](#5-约束条件不可外部化的算法群)
6. [工程参考：DESCRIPTOR 序列化参数](#6-工程参考descriptor-序列化参数)

---

## 1. 理论基础：逆M集的着色区域反转

### 1.1 定义

设标准 Mandelbrot 集为 $M = \{c \in \mathbb{C} : \sup_{n \ge 0} |z_n| < \infty\}$，其中 $z_{n+1} = z_n^2 + c, z_0 = 0$。

逆 Mandelbrot 集通过 Möbius 反演 $\iota(c) = 1/c$ 定义：

$$M_{\text{inv}} = \iota(M \setminus \{0\}) = \{c \in \mathbb{C} \setminus \{0\} : 1/c \in M\}$$

等价于直接迭代 $z_{n+1} = z_n^2 + 1/c, z_0 = 0$。

### 1.2 着色区域的反转规则

在标准 M 集中，逃逸区 $E_M = \{c \notin M : \exists n, |z_n| > R\}$ 占据几何外部；在逆 M 集中，逃逸区 $E_{\text{inv}} = \{c : \exists n, |z_n| > R \text{ with } c_{\text{eff}} = 1/c\}$ 经 $1/c$ 映射后占据**水滴形状的几何内部**。

因此：

$$\begin{aligned}
\text{逆M ext} &= E_{\text{inv}} \subset \text{水滴几何内部} \\
\text{逆M interior} &= \mathbb{C} \setminus E_{\text{inv}} \supset \text{水滴几何外部}
\end{aligned}$$

**推论**：要在水滴几何外部产生可视化效果，需着色于 `interior` 区域，或使用不依赖逃逸判据的着色量。

### 1.3 不可逃逸区的数学约束

对于 $c \in \text{interior}$（水滴外部）：

- 逃逸步数恒为 `max_iter`（未逃逸）
- 轨道 $\{z_n\}$ 有界，且不存在"最终逃逸"的 $z_{\text{final}}$
- 平滑势函数 $\nu = n - \log_2(\log_2|z|)$ 在 $\mathbb{R}$ 上无定义
- 逃逸外部角 $\theta = \arg(z)/(2\pi \cdot 2^n)$ 无法计算

---

## 2. A类：原生外部着色算法

以下算法在原始设计中已支持水滴外部着色，无需修改。

### 2.1 UF8 — 对偶三角网扩散 (Dual Triangulation Diffusion)

**设计特性**：唯一同时着色 ext 和 interior 两个区域的标准 UF 算法。

#### 内部着色 (ext = 水滴内)

基于逃逸数据的 XOR 三角网：

$$T(c) = \left\lfloor \theta_e(c) \cdot R_d \right\rfloor \bmod 2 \;\oplus\; \left\lfloor \frac{\text{pot}(c)}{\Delta_p} \right\rfloor \bmod 2$$

其中 $\theta_e = \arg(z_{\text{final}})/(2\pi \cdot 2^n) \bmod 1$ 为逃逸外部角，$R_d = 256$ 为角度量化级数，$\Delta_p = 0.04$ 为势能步长。

颜色：$T(c)=1 \to [0.08, 0.35, 0.65]$（蓝紫暗调）；$T(c)=0 \to$ 深底色。

#### 外部着色 (interior = 水滴外)

基于复参数模长的平滑渐变：

$$G(c) = \begin{bmatrix}
0.02 + 0.10 \cdot \frac{|c| - |c|_{\min}}{|c|_{\max} - |c|_{\min}} \\
0.35 + 0.45 \cdot \frac{|c|}{|c|_{\max}} \\
0.75 + 0.25 \cdot \frac{|c|}{|c|_{\max}}
\end{bmatrix}$$

形成从深蓝（近水滴边界）到浅蓝（远场）的径向衰减。

#### 边界金边

$$\text{gold}(c) = \begin{cases}
[1.0, \; 0.65 + 0.35 \cdot \text{pot}(c)/0.05, \; 0.08] & \text{if } \text{pot}(c) < 0.05 \\
\text{透明} & \text{otherwise}
\end{cases}$$

| 参数 | 值 | 说明 |
|:---|:---|:---|
| $R_d$ | 256 | 角度量化（高≈三角鳞片） |
| $\Delta_p$ | 0.04 | 势能步长（细密等势） |
| bailout | 50 | 逃逸半径 |

---

### 2.2 UF7 — 轨迹排斥树枝 (Trajectory Repulsion Trees)

**设计特性**：唯一不依赖逐像素逃逸判据的可视化方法。轨道不受 ext/interior 约束。

#### 核心机制

对稀疏采样点执行完整迭代，保存轨道序列 $\{z_0, z_1, \ldots, z_n\}$。通过逆映射将轨道点投影回屏幕坐标空间：

$$w_k = \frac{1}{z_k}, \quad (x_{\text{scr}}, y_{\text{scr}}) = (\operatorname{Re}(w_k), \operatorname{Im}(w_k))$$

每条轨道的屏幕坐标直接累加到图像像素缓冲区，形成密度图。

#### 排斥分支扩展

在轨道曲率突变点（$|\angle(z_{k+1}) - \angle(z_k)| > \tau$）植入微小扰动种子：

$$b_0 = z_k + \varepsilon, \quad b_{m+1} = b_m^2 + c_{\text{eff}}, \quad m = 0,1,\ldots,B_{\text{max}}$$

分支轨迹同样经 $w = 1/z$ 逆映射回屏幕空间绘制。

| 参数 | 值 | 说明 |
|:---|:---|:---|
| STEP | 8 | 采样步长 |
| MAXITER | 120 | 最大迭代 |
| bailout | 50 | 逃逸半径 |
| $\tau$ | 经验阈值 | 角度变化触发分支 |

#### 着色策略

迭代早期点 → 深色（靠近水滴边界），迭代晚期点 → 浅色（远场延伸），形成树枝从水滴向外自然生长的视觉效果。

---

### 2.3 UF21 — 蓝白阴阳格辉光 (Blue-White Chess + DEM Glow)

**设计特性**：混合 UF1 棋盘逻辑（改写为极坐标）与 UF4 DEM 金边。支持 3 种外部纹理模式。

#### 棋盘公式（外部版）

由于 interior 区无法使用逃逸势能与外部角，改用复平面固有几何量：

$$\theta(c) = \arctan2(\operatorname{Im}(c), \operatorname{Re}(c)), \quad \rho(c) = \log_2(|c|)$$

$$C(c) = \left\lfloor \frac{\theta(c)}{2\pi} \cdot N_\theta \right\rfloor \bmod 2 \;\oplus\; \left\lfloor \frac{\rho(c)}{\Delta_\rho} \right\rfloor \bmod 2$$

| 版本 | $N_\theta$ | $\Delta_\rho$ | 效果 |
|------|:--:|:--:|------|
| v4b (基准) | 24 | 0.35 | 粗格 ~17 环 |
| **v4c (细密)** | **240** | **0.035** | 面积 1/100 |

#### DEM 边界金边

仅在边界附近激活（对 interior 侧也生效）：

$$d(c) = \frac{\log(|z|^2) \cdot |z|}{|dz|}, \quad dz_{n+1} = 2z_n \cdot dz_n + 1$$

$$g(d) = [0.9 \cdot \hat{d}, \; 0.6 \cdot \hat{d}, \; 0.1 \cdot \hat{d}], \quad \hat{d} = \frac{d}{\max(d)}$$

#### 模式切换参数

| CHESS_MODE | 纹理公式 | 视觉效果 |
|:--:|------|------|
| A | XOR `θ⊕ρ` | 蓝白阴阳瓷砖 + 同心环纹 |
| B | 纯角度 `⌊θ·N/(2π)⌋ % M` | 扇形辐射（披萨切片） |
| C | 纯环带 `⌊ρ/Δ⌋ % M` | 同心靶心环纹 |

| 参数 | v4b | v4c | 说明 |
|:---|:--:|:--:|:---|
| ANG_DIV | 24 | 240 | 角度分区 |
| DIST_LOG_STEP | 0.35 | 0.035 | 对数距离步长 |
| DEM_SCALE | 15 | 20 | 辉光强度 |
| MAXITER | 200 | 200 | 最大迭代 |

---

## 3. B类：边界双向辐射算法

### 3.1 UF4 — 距离估计壳线 (Distance Estimator Method)

**设计特性**：唯一在逃逸区边界两侧均产生光晕的算法。DEM 值从边界向两侧同等衰减。

#### Mu-Ency 距离估计

同步追踪复导数 $dz$：

$$z_{n+1} = z_n^2 + c_{\text{eff}}, \quad dz_{n+1} = 2 \cdot z_n \cdot dz_n + 1, \quad dz_0 = 0$$

逃逸后的连续距离估计：

$$d(c, \partial M_{\text{inv}}) = \frac{\log(|z_n|^2) \cdot |z_n|}{|dz_n|}$$

#### 连续光晕映射

$$s(d) = \operatorname{clip}\left(-\frac{\log(d)}{3}, \; 0, \; 1\right)$$

颜色（绿色渐变，边界高亮）：

$$\text{color}(d) = \begin{bmatrix}
s \cdot 0.15 + 0.02 \\
s \cdot 0.60 + 0.10 \\
s \cdot 0.20 + 0.02
\end{bmatrix}$$

边界极近处叠加亮白细线：$d < \text{pixel\_width} \to [0.8, 1.0, 0.7]$。

#### 双向性证明

DEM 公式 $d(c)$ 仅依赖逃逸后的 $z_n$ 和 $dz_n$，与几何方向无关。光晕在 $\partial M_{\text{inv}}$ 两侧对称衰减——水滴内壁（ext 侧）和水滴外缘（interior 侧）均受光晕覆盖。

| 参数 | 值 |
|:---|:---|
| bailout | 100000 |
| 色板 | 绿色渐变 (Mu-Ency) |
| 光晕映射 | $s = -\log(d)/3$ |

---

## 4. C类：可扩展的外部着色算法

### 4.1 UF1 — 二分棋盘格 (Binary Decomposition)

**默认行为**：着色于 ext（水滴内部）。需交换 mask 至 interior 方可外部着色。

#### 外部版公式

原始公式中逃逸外部角 $\theta_e$ 和势能 $\text{pot}$ 在 interior 区均无效，需替换为复平面几何量：

$$\theta(c) = \arctan2(\operatorname{Im}(c), \operatorname{Re}(c)), \quad \rho(c) = \log_2(|c|)$$

$$C(c) = \left\lfloor \frac{\theta(c)}{2\pi} \cdot N_\theta \right\rfloor \bmod 2 \;\oplus\; \left\lfloor \frac{\rho(c)}{\Delta_\rho} \right\rfloor \bmod 2$$

**工程实现**（已验证 v4b）：

```python
chess = C(c) & interior     # interior = 水滴几何外部
img[chess] = LIGHT_BLUE    # [0.78, 0.84, 0.96]
img[interior & ~chess] = DARK_BLUE  # [0.12, 0.18, 0.45]
img[ext] = BG_DEEP_BLUE    # [0.03, 0.06, 0.18]
```

### 4.2 UF3 — 有理外部射线 (External Rays)

**默认行为**：射线限于水滴内部。可扩展至外部。

射线公式在复平面上处处有定义（基于 arg(z) 而非逃逸状态），通过共形映射 $c \to 1/c$ 连续性可外推到 interior 区：

$$\theta_r = \frac{\arg(z)}{2\pi \cdot 2^n} \bmod 1, \quad \text{ray} = |\theta_r \cdot N - \operatorname{round}(\theta_r \cdot N)| < \varepsilon$$

需在边界处做角度连续性插值以无缝延伸到外部。

---

## 5. 约束条件：不可外部化的算法群

以下 UF 算法因数学约束**无法**产生水滴外部视觉效果。根本原因：着色量依赖逃逸行为，而 interior 区不逃逸。

| 类别 | UF# | 依赖的逃逸量 | 在 interior 区状态 |
|------|:--:|------|------|
| 势能系 | 2, 6, 9, 10, 13, 16, 17 | $\nu = n - \log_2(\log_2|z|)$ | 恒为零或 NaN |
| 轨道系 | 5, 11, 12, 15, 18, 20 | $\min|z_n - \text{trap}|, \sum|\Delta z|/|z|$ | 轨道不存在 |
| 特效系 | 14, 19 | $\arg(z_{\text{final}}), |z_{\text{final}}|$ | 无"最终逃逸"的 z |

**唯一的替代方案**：使用不依赖逃逸的纯几何量替代——如极坐标 $(|c|, \arg(c))$、对数距离 $\log_2(|c|)$、或复平面格点（UF12 高斯整数可扩展到 exterior）。

---

## 6. 工程参考：DESCRIPTOR 序列化参数

以下为每种外部着色算法的 JSON DESCRIPTOR 最小表示（用于分发而非存储像素）。

### UF1 外部版

```json
{
  "algorithm": "binary_decomposition",
  "projection": {"type": "inversion", "k": 0},
  "exterior_mode": true,
  "algo_params": {"ANG_DIV": 24, "DIST_LOG_STEP": 0.35},
  "colormap": "blue_white_chess"
}
```

### UF7 轨迹树枝

```json
{
  "algorithm": "trajectory_trees",
  "projection": {"type": "inversion", "k": 0},
  "algo_params": {"STEP": 8, "branch_angle_threshold": 0.3},
  "render_mode": "trajectory_density"
}
```

### UF8 对偶三角网

```json
{
  "algorithm": "dual_triangulation",
  "projection": {"type": "inversion", "k": 0},
  "algo_params": {"RAY_DIV": 256, "POT_STEP": 0.04},
  "dual_coloring": true
}
```

### UF21 v4c 细格版

```json
{
  "algorithm": "chess_dem_hybrid",
  "projection": {"type": "inversion", "k": 0},
  "algo_params": {"ANG_DIV": 240, "DIST_LOG_STEP": 0.035, "DEM_SCALE": 20},
  "chess_mode": "A",
  "exterior_chess": true
}
```

---

**参考文献**

- Drakopoulos, V. (2010). Sequential visualisation methods for the Mandelbrot set. *J. Comp. Meth. Sci. Eng.*, 10, 37–45.
- Alaqad, H., Ibrahim, R., & Salleh, Z. (2021). On the inversion of the Mandelbrot set. *Fractal and Fractional*, 5(3), 73.
- adammaj1. Mandelbrot-Sets-Alternate-Parameter-Planes. GitHub repository.
- Ultra Fractal 6. Standard.ucl / Standard.ulb — BinaryDecomposition, DEM/M, Orbit Traps.
