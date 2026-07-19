# Calabi-Yau螺旋辐射 — 逆M水滴外部纹理的指数映射创新算法

> **CY-SR (Calabi-Yau Spiral Radiation)** | 2026-07-13
>
> 将 Calabi-Yau 流形的指数螺旋映射引入逆M集水滴外部着色，创造全新的螺旋臂纹理、相位干涉辐射场和指数浮雕效果。

---

## 一、数学直觉：为什么 exp(z) 引入后会发生质变

### 1.1 现有外部算法的本质局限

当前水滴外部着色算法（UF1 ext、UF21 v4c）使用的几何量：

$$\theta(p) = \arctan2(y, x), \quad \rho(p) = \log_2(|p|)$$

这是**纯线性/对数坐标**——纹理沿径向单调展开，无法产生旋转或干涉。

### 1.2 Calabi-Yau 指数螺旋的启示

Calabi-Yau 流形的 `smooth_calabi-yau` 系列用指数函数将复平面映射为三维螺旋曲面：

$$\Phi: \mathbb{C} \to \mathbb{R}^3, \quad \Phi(z) = (\operatorname{Re}(f(z)), \operatorname{Im}(f(z)), |f'(z)|)$$

其中 $f(z)$ 包含指数项 `exp(i * θ + ln(r) * K1)`，产生**连续旋转 + 径向指数拉伸**。

**核心观察**：`exp(iθ + ln(r)·K)` = `r^K · e^{iθ}`。当 $K > 1$ 时，外圈纹理随距离**加速旋转**——这正是我们需要的"向外辐射且旋转"的纹理基础。

### 1.3 与水滴外部的结合点

水滴的 c→1/c 反演将无穷远映射到原点附近，水滴边界是 $\partial M_{\text{inv}} = \iota(\partial M)$。如果我们以水滴边界为"原点"，向外构造指数螺旋场，就得到一个天然符合边界几何的向外辐射螺旋纹理。

---

## 二、新算法：CY-SR（Calabi-Yau螺旋辐射）

### 2.1 核心公式

设 $b(p)$ 为点 $p$ 到水滴边界 $\partial D$ 的最近点投影，定义：

$$p^* = p - b(p), \quad r(p) = |p^*|, \quad \theta(p) = \arg(p^*)$$

**Calabi-Yau螺旋映射**：

$$\Phi_{\text{CY}}(p) = \exp(i \cdot \theta(p) + \ln(r(p) + \varepsilon) \cdot K) \cdot S(r)$$

其中：
- $K$：螺旋密度参数（$K > 0$ 向外展开，$K < 0$ 向内收束；$|K|$ 控制旋转速率）
- $S(r) = 1 - \exp(-r / \sigma)$：渐近衰减因子，远场纹理逐渐消失
- $\varepsilon = 10^{-6}$：防止 log(0)

**纹理坐标映射**：

$$u(p) = \frac{\operatorname{Re}(\Phi_{\text{CY}}(p))}{\max|\Phi_{\text{CY}}|} \in [-1, 1], \quad v(p) = \frac{\operatorname{Im}(\Phi_{\text{CY}}(p))}{\max|\Phi_{\text{CY}}|} \in [-1, 1]$$

### 2.2 三种纹理模式

#### 模式 A：CY螺旋臂 (Calabi-Yau Spiral Arms)

$$T_A(p) = \lfloor u(p) \cdot N \rfloor \bmod 2 \;\oplus\; \lfloor v(p) \cdot M \rfloor \bmod 2$$

产生从水滴边界向外旋转的螺旋臂纹理——臂密度由 $N, M$ 控制，旋转速率由 $K$ 控制。

| K | 视觉效果 |
|:--:|------|
| 0.5 | 缓慢单臂螺旋 |
| 1.0 | 标准双曲螺旋 |
| 2.0 | 快速多臂螺旋 |
| 5.0 | 极密旋臂（类似星系） |

#### 模式 B：CY相位干涉 (Calabi-Yau Phase Interference)

Calabi-Yau 的 8 个相位 (0→2π) 合并成连续动画——将此思想应用于静态纹理：

$$T_B(p, \alpha_0) = \bigoplus_{j=0}^{7} \left\lfloor \left( u(p) \cdot N + \frac{j \cdot \pi}{4} \right) \bmod 2 \;\oplus\; \lfloor v(p) \cdot M \rfloor \bmod 2 \right)$$

$\bigoplus$ = 逐像素最大值（取各相位中最亮的格），形成多层螺旋叠加的干涉莫尔纹。

#### 模式 C：CY指数浮雕 (Calabi-Yau Exponential Emboss)

将螺旋高度场映射为光照亮度：

$$H(p) = \operatorname{Re}(\Phi_{\text{CY}}(p)) \cdot \exp(-r/\sigma)$$

$$L(p) = \max(0, -\nabla H(p) \cdot \vec{l})$$

其中 $\vec{l}$ 为光源方向。产生3D浮雕般的螺旋纹理，配合 DEM 金边产生"立体旋转雕塑"效果。

### 2.3 伪代码框架

```python
import numpy as np

def calabi_yau_spiral(points, boundary_mask, K=1.5, sigma=10.0, N=64, M=32):
    """
    CY-SR 核心渲染器
    
    Args:
        points: complex array, 复平面坐标
        boundary_mask: bool array, 水滴边界像素 (d < threshold)
        K: float, 螺旋密度 (1.5=标准双曲螺旋)
        sigma: float, 远场衰减尺度
        N, M: int, u/v方向的量化级数
    """
    # 1. 计算每个exterior点偏离边界的极坐标
    #    简化版: 用点到原点的极坐标 (替代严格的边界投影)
    r = np.abs(points)
    theta = np.angle(points)
    
    # 2. Calabi-Yau指数螺旋映射
    eps = 1e-6
    z_cy = np.exp(1j * theta + np.log(r + eps) * K)
    
    # 3. 渐近衰减: 远场纹理会消失
    decay = 1 - np.exp(-r / sigma)
    z_cy *= decay
    
    # 4. 纹理坐标归一化
    z_max = np.max(np.abs(z_cy)) + eps
    u = np.real(z_cy) / z_max
    v = np.imag(z_cy) / z_max
    
    # 5. XOR螺旋臂纹理
    u_idx = np.floor(u * N).astype(int)
    v_idx = np.floor(v * M).astype(int)
    texture = (u_idx % 2 == 0) != (v_idx % 2 == 0)
    
    return texture, u, v
```

### 2.4 参数空间探索（对标 UF21 v4c 的 ANG_DIV/DIST_LOG_STEP）

| 参数 | 物理意义 | 推荐范围 | 效果 |
|:---|------|:--:|------|
| $K$ | 螺旋密度 | 0.5 ~ 5.0 | 旋转臂数目 |
| $N$ | u方向量化 | 64 ~ 512 | 臂的切线分辨率 |
| $M$ | v方向量化 | 32 ~ 256 | 臂的法线分辨率 |
| $\sigma$ | 远场衰减 | 2.0 ~ 50.0 | 纹理在哪消失 |
| 光源 $\vec{l}$ | 仅模式 C | — | 浮雕光影方向 |

---

## 三、从现有算法进化到 CY-SR 的路径

### 3.1 UF1 ext (极坐标棋盘) → CY-SR 模式A

```diff
- chess = (⌊θ·N⌋%2) ⊕ (⌊log₂|p|/Δ⌋%2)     # 现有: 平直网格
+ chess = (⌊u·N⌋%2) ⊕ (⌊v·M⌋%2)              # CY-SR: 螺旋网格
+ where u+iv = exp(iθ + ln(r)·K) * (1-e^(-r/σ))
```

只需替换坐标映射，其余管线不变。

### 3.2 UF21 v4c (CHESS_MODE切换) → CY-SR 模式B

```diff
  CHESS_MODE 'A': XOR(⌊θ·N⌋, ⌊log|p|/Δ⌋)    # 保留原有
  CHESS_MODE 'B': 纯角度扇形                    # 保留原有
  CHESS_MODE 'C': 纯环带                        # 保留原有
+ CHESS_MODE 'D': CY-SR模式A (K=1.5)           # 新增
+ CHESS_MODE 'E': CY-SR模式B (8相位干涉)        # 新增
+ CHESS_MODE 'F': CY-SR模式C (指数浮雕)         # 新增
```

### 3.3 tower_calabi 塔层堆叠 → 多层螺旋密度

Calabi-Yau `tower_calabi` 用多层叠加产生复杂3D结构。类似地：

```python
# 多层不同K值的螺旋叠加
K_layers = [0.5, 1.0, 1.5, 2.0, 3.0]  # 从缓慢→快速
texture = np.zeros_like(u)
for k in K_layers:
    z_k = np.exp(1j * theta + np.log(r + eps) * k) * (1 - np.exp(-r / sigma))
    u_k, v_k = normalize(z_k)
    texture ^= (⌊u_k·N⌋%2) ⊕ (⌊v_k·M⌋%2)  # XOR叠加
```

产生**多尺度嵌套螺旋**——宏观慢旋 + 微观快旋 + 中观中旋，视觉复杂度指数级提升。

---

## 四、与逆M数学本质的共鸣

### 4.1 指数映射 = 倍周期级联的连续化

指数映射 $c = cf + e^p$ 已经将离散的倍周期级联（$2^0, 2^1, 2^2, ...$）拉平成等间距的7个双曲分支。

CY-SR 的螺旋公式 $\exp(i\theta + \ln(r) \cdot K)$ 是这个思想的**自然外推**：
- 指数映射把 Feigenbaum 点附近的离散结构**空间化**
- CY-SR 把水滴外部的离散棋盘**旋转连续化**

两者都利用 $\exp$ 函数的天然性质：将加法（离散步长）变为乘法（连续旋转）。

### 4.2 相位0→2π循环 = Farey级联的另一种编码

Calabi-Yau 从 phase1(α=0.00) → phase8(α=6.28) 的8个切片，恰好对应 M 集心形边界上 Farey 分数的 8 个周期锚点 (period 2-9, φ(n)/2 个锚点)。

将 8 相位映射到 8 个 Farey 锚点的角度位置：

$$\alpha_j = 2\pi \cdot \frac{p_j}{q_j}, \quad (p_j, q_j) \in \text{Farey fractions on cardioid}$$

则相位于涉 $T_B$ 直接编码了 Farey 级联的拓扑结构——纹理图案 = Farey 树的可视化。

---

## 五、预期效果与瓶颈

### 5.1 视觉预期

| 模式 | 预期效果 | 类比 |
|:--:|------|------|
| A (螺旋臂) | 星系旋臂从水滴向外延伸 | 仙女座星系 dust lanes |
| B (相位干涉) | 多层螺旋叠加莫尔纹 | 光栅衍射 + 万花筒 |
| C (指数浮雕) | 3D浮雕螺旋 + DEM金边 | 希腊爱奥尼柱头卷涡 |
| 多层叠加 | 多尺度嵌套结构 | Mandelbrot集自相似但向外展开 |

### 5.2 计算瓶颈

- $\exp$ 计算比简单的 $\arctan2$ 慢约 3-5×，但对 $N \times M$ 像素仍是一次性计算
- 边界投影 $b(p)$ 的严格计算需要解 $d(c, \partial M_{\text{inv}})$ 的最小值——可用 DEM 近似
- 多层螺旋叠加时计算量线性增长

**工程实现建议**：先用 DEM 值近似 $\partial M_{\text{inv}}$ 距离，然后只对边界外 $d < \sigma$ 范围内的点应用 CY-SR，超远场直接做减法（远场衰减到0）。

---

## 六、创新性评估

| 维度 | 已有方案 | CY-SR 方案 | 创新点 |
|------|------|------|------|
| 坐标映射 | 极坐标 $(r, \theta)$ | 指数螺旋 $\exp(i\theta + \ln(r)·K)$ | 旋转连续性 |
| 纹理生成 | 单一尺度 XOR | 多层K值嵌套 XOR | 多尺度螺旋 |
| 相位概念 | 无 | 8相位干涉莫尔纹 | 仿 Calabi-Yau α扫掠 |
| 3D效果 | DEM独立金边 | 指数浮雕 + DEM 混合 | 高度场+光晕 |
| 与M集本质关联 | 分离 | Farey分数 → 相位映射 | 深层数学统一 |

---

## 七、DESCRIPTOR 示例

```json
{
  "algorithm": "calabi_yau_spiral",
  "projection": {"type": "inversion", "k": 0},
  "cy_params": {
    "spiral_density": 1.5,
    "n_phases": 8,
    "decay_sigma": 10.0,
    "N_quant": 128,
    "M_quant": 64,
    "layers": [0.5, 1.0, 1.5, 2.0, 3.0]
  },
  "mode": "A",
  "dem_glow": true
}
```
