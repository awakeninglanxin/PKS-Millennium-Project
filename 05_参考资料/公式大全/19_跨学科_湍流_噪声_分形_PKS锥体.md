# 跨学科关联 4 — 流体湍流 · 噪声生成 · 分形几何

> 覆盖：NS方程 · Perlin噪声 · PKS双曲锥 · bugman123流体方法 · 光谱法CFD · 分形边界  
> 核心洞察：**湍流能量级联 = 噪声频谱 = 分形自相似 = 锥体压缩放大**

---

## 一、湍流的统一描述框架

### 1.1 NS 方程

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u} = -\nabla p + \nu\nabla^2\mathbf{u} + \mathbf{f}, \quad \nabla\cdot\mathbf{u}=0$$

### 1.2 Kolmogorov 能量级联

$$E(k) \sim k^{-5/3}$$

能量从大尺度（小 k）流向小尺度（大 k），在大尺度上注入，在小尺度上耗散。

### 1.3 湍流 → 噪声 → 分形 的频谱链

```
NS湍流                     Perlin噪声                   分形边界
E(k) ~ k^{-5/3}           noise(x,y) ~ Σ A_i·sin(f_i x)   M集边界 d_f ≈ 2
   │                           │                              │
能量级联                   多尺度叠加                   自相似
   │                           │                              │
涡量拉伸                    octave分层                   Mandelbrot迭代
```

---

## 二、Perlin 噪声 ↔ 湍流速度场

### 2.1 噪声 = 简化的湍流频谱

韩国 YouTuber 的水表面模拟：

```javascript
let z = noise(x*0.02, y*0.02, t) * 100;
```

本质上是 $k^{-5/3}$ 频谱的离散近似——用多个 octave（倍频程）叠加：

$$h(x,y,t) = \sum_{i=1}^{N} A \cdot 2^{-i} \cdot \text{noise}(2^i x, 2^i y, t)$$

每个 $2^i$ 对应 Kolmogorov 级联的一个**涡尺度**。

### 2.2 从 2D 噪声到 3D 湍流

扩展噪声到 3D + 取旋度 → 自动满足不可压缩条件：

$$\mathbf{u}(\mathbf{x}) = \nabla \times \mathbf{N}(x,y,z)$$

其中 $\mathbf{N}$ 是三个独立 Perlin 噪声分量。这个速度场天然满足 $\nabla \cdot \mathbf{u} = 0$，并且频谱近似 Kolmogorov。

### 2.3 噪声的局限

Perlin 噪声是**运动学湍流**——它看起来像湍流，但不满足 NS 方程的非线性对流项。真正的湍流需要涡量拉伸（vortex stretching），这在线性噪声叠加中不存在。

**这正是我们今天 CFD 失败的原因**：光谱法 + 噪声入口 = 运动学近似 ≠ 非线性物理。

---

## 三、bugman123 流体工具箱 ↔ PKS 问题

### 3.1 已有方法

| 方法 | bugman123 来源 | 维度 | 适用 PKS 场景 |
|------|:---:|:---:|------|
| Driven Cavity FVM | fluid_dynamics.md | 2D | 锥体截面涡流基准 |
| SPH 无网格 | fluid_dynamics.md | 2D/3D | 贴壁流无需网格 |
| Von Karman 涡街 | fluid_dynamics.md | 2D | 锥体尾流涡脱落 |
| KH 不稳定性 | fluid_dynamics.md | 2D/3D | 剪切层涡量生成 |
| CFL3D RANS | fluid_dynamics.md | 3D | 超音速锥体 |
| 激波管 JST | fluid_dynamics.md | 1D | 锥体喉部激波 |

### 3.2 最值得迁移的：SPH 无网格

SPH (Smoothed Particle Hydrodynamics) 不需要网格——粒子自带物理量，天然适合 PKS 锥体的复杂几何。粒子沿 STL 壁面滑移时自动满足无滑移边界条件。

```
光谱法：格点固定 + 壁面模糊 → 边界层不存在 ❌
SPH：   粒子自由 + 壁面排斥 → 边界层自然建立 ✅
```

---

## 四、PKS 锥体的涡量放大——为什么它应该是可能的

### 4.1 物理直觉

```
流入大截面(S₁) ──→ 收缩段 ──→ 流出小截面(S₂)
    u₁, ω₁           ∂u/∂z > 0        u₂, ω₂
    
角动量守恒：ω₁·S₁ = ω₂·S₂
涡量放大比：ω₂/ω₁ = S₁/S₂
```

PKS 双曲锥的截面比可达 100:1 → 理论上涡量可放大 100 倍。

### 4.2 为什么我们的 CFD 没看到

**不是因为不存在——是因为数值方法无法解析。**

我们要的是壁面边界层剥离（boundary layer separation）产生的涡量，但光谱法在壁面上只有"模糊的一层"。SPH 或 IBM+有限体积才是正确工具。

---

## 五、分形 ↔ 湍流的深层联系

### 5.1 Mandelbrot 集的湍流模型（Mandelbrot 1975）

Mandelbrot 本人最早提出：湍流耗散区的几何是**分形的**。湍流能量耗散集中在空间中的分形子集上——这个子集的 Hausdorff 维数 < 3。

### 5.2 我们的逆 M 水滴

逆 M 集的边界是一个**分形曲线**。在 PKS 锥体中，流体沿这个分形边界的形状流动 → 涡量在分形皱褶处被"刮"下来 → 形成离散涡丝。

```
逆M水滴边界(分形)  →  流体沿壁面  →  涡量在皱褶处剥离
                                          ↓
                                   涡丝进入主流
                                          ↓
                                   喉部压缩 → 涡量放大
```

---

## 六、完整的跨学科工具链

| 步骤 | 工具 | 来源 | 产品 |
|:--:|------|------|------|
| 几何 | PKS 双曲锥 STL | 对数螺线扫掠 | 3D 壁面 |
| 入口条件 | Perlin 噪声 + 旋度 | 韩国 YouTube | 湍流速度场 |
| 求解器 | SPH 或 IBM+FVM | bugman123 | 壁面涡量 |
| 可视化 | 3D 等值面 + 调色板循环 | Divetoxx | 涡量动画 |
| 验证 | Kolmogorov E(k) ~ k^{-5/3} | 理论 | 湍流频谱 |
| 分形分析 | M 集边界 Hausdorff 维数 | DNA_M 探索器 | 壁面粗糙度 |

---

> **下一优先**：用 bugman123 的 SPH 公式 + PKS 锥体 STL + 韩国 YouTube 的 Perlin 噪声入口 → GPU 上的无网格 CFD，解决光谱法的壁面问题。
