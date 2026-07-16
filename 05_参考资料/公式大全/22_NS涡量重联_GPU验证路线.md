# GPU 验证路线 — 涡量重联"安全阀"假说

> 目标：用 GPU 数值实验积累涡量重联的统计证据  
> 方法：伪谱法 3D 各向同性湍流 + 涡管检测 + 重联事件追踪  
> 关键指标：重联前 |ω|_max 的增长是否总在爆炸前被打断

---

## 一、避开之前的坑：为什么这次能成

| 之前 CFD 失败 | 这次方案的差异 |
|------|------|
| 光谱法 + 锥体壁面 | **伪谱法 + 周期边界**（没有壁面！） |
| 关注宏观涡量 Growth | 关注**微观涡管重联事件** |
| 需要壁面边界层 | 不需要——涡管在自由空间中自行演化 |
| STL 几何 + IBM | 不需要——周期盒子 |

**伪谱法在周期边界下是无条件稳定的**。我们的 FFT 求解器代码已经验证过（CFD 实验 A1-A4 的引擎部分是对的，错的是壁面处理）。这次去掉壁面，只跑自由湍流中的涡管碰撞。

---

## 二、实验一：涡管碰撞中的重联时间分布

### 2.1 初值设定

两根**反向旋转**的涡管，初始间距 d，初始涡量 ω₀：

```
涡管1: center=(L/2-d/2, L/2, L/2), 轴向=z, ω_max=ω₀
涡管2: center=(L/2+d/2, L/2, L/2), 轴向=z, ω_max=-ω₀
```

### 2.2 扫描参数

| 参数 | 扫描值 | 目的 |
|------|------|------|
| d（间距） | 2, 4, 8, 16 grid | 碰撞时间 vs 初始间距 |
| ω₀（初始涡量） | 1, 2, 4, 8 | 是否 ∃ω₀ 导致爆炸前无重联 |
| ν（粘性） | 0.001, 0.0005, 0.0001 | 接近无粘极限的行为 |

### 2.3 测量指标

```
每一步记录：
├── |ω|_max(t)        → 涡量峰值的演化
├── H(t) = ∫u·ω dx    → helicity（拓扑不变量）
├── ΔH 跳变时刻       → 重联发生的时间标签
└── |ω|_max 在重联前的最大值 → 是否总在有限值就"刹车"
```

### 2.4 统计目标

画出 $\max_t |\omega|_\infty$ 随 $1/\nu$ 的缩放图。如果：

- $|\omega|_{\max}$ 上界不随 $1/\nu$ 发散 → 重联提供了**粘性无关的刹车** → 支持"永不炸"
- $|\omega|_{\max}$ 随 $1/\nu$ 幂增长 → 无粘极限下可能炸 → 支持"存在爆炸"

**这个实验就是直接回答 Clay 问题。**

---

## 三、实验二：PKS 锥体是否加速重联

### 3.1 初值

在 PKS 锥体入口放置涡环，追踪其在收缩段中的演化。

### 3.2 测量

```
锥体收缩段中：
├── 涡环是否被压缩成更紧密的涡管对？
├── 压缩后的涡管对是否更早重联？
└── 重联释放的涡量 vs 收缩带来的涡量浓缩 → 谁赢？
```

如果锥体壁面**加速重联**（把涡管挤压到一起 → 更快碰上 → 更早释放涡量），那 PKS 锥体就是天然的"安全阀增强器"。

---

## 四、实验三：涡管网络的重联频率谱

### 4.1 设定

从随机初值出发，跑一段时间的 3D 各向同性湍流（256³ 伪谱法），让湍流自然演化出涡管网络。

### 4.2 检测每一帧

用 **λ₂ 准则**识别涡管：

$$\lambda_2(\mathbf{S}^2 + \mathbf{\Omega}^2) < 0$$

其中 $\mathbf{S} = (\nabla\mathbf{u} + \nabla\mathbf{u}^T)/2$ 为应变率，$\mathbf{\Omega} = (\nabla\mathbf{u} - \nabla\mathbf{u}^T)/2$ 为旋转率。

### 4.3 追踪

标记每一条涡管的"生命周期"——从诞生（λ₂ 首次 < 0）到消亡（λ₂ → 0，即重联或被耗散掉）。

### 4.4 统计

```
涡管生命周期分布 P(T_life)
重联间隔分布 P(Δt_reconnect)
重联前 |ω|_max 分布 P(|ω|_crit)
```

如果 $P(|\omega|_{\text{crit}})$ 是指数衰减的——即高涡量事件**极其罕见**——则爆炸的概率为零。

---

## 五、技术实现路线

### 5.1 GPU 代码框架

```python
# Pseudo-spectral 3D NS solver — CuPy, no walls
import cupy as cp

N = 256  # grid resolution
nu = 0.001

# wave numbers
k = cp.fft.fftfreq(N) * 2*pi*N
Kx, Ky, Kz = cp.meshgrid(k, k, k, indexing='ij')
K2 = Kx**2 + Ky**2 + Kz**2
K2[0,0,0] = 1  # avoid division by zero

# Initial condition: two anti-parallel vortex tubes
u_hat = init_vortex_tubes(Kx, Ky, Kz)

# Time stepping: 2nd-order Adams-Bashforth + Crank-Nicolson
for step in range(N_STEPS):
    # Convection term in physical space
    u = cp.fft.ifftn(u_hat).real
    omega = compute_vorticity(u)
    N = convection_term(u, omega)
    N_hat = cp.fft.fftn(N)
    
    # Project to divergence-free
    N_hat = project_divfree(N_hat, Kx, Ky, Kz, K2)
    
    # Update with integrating factor
    u_hat = (u_hat + dt*N_hat) / (1 + nu*K2*dt)
    
    # Detect reconnection events
    H = helicity(u_hat, Kx, Ky, Kz)
    if abs(H - H_prev) > threshold:
        log_reconnection(step, |omega|_max, H)
```

### 5.2 预估 GPU 时间

| 网格 | 步数 | GPU 耗时 |
|:---:|:---:|:---:|
| 128³ | 2000 | ~5 min |
| 256³ | 2000 | ~30 min |
| 512³ | 1000 | ~3 h (需要 A100) |

### 5.3 依赖

```bash
pip install cupy-cuda12x numpy
# 不需要 PyTorch, 不需要 scipy, 不需要外部 CFD 库
```

---

## 六、如果实验结果有利——能写出什么结论

| 实验结果 | 能写出的结论 |
|------|------|
| $|\omega|_{\max}$ 对所有 $(\nu, d, \omega_0)$ 组合均保持有界 | 重联在所有测试参数下均发生 → 支持"涡量重联是通用安全阀" |
| $|\omega|_{\max}$ 与 $1/\nu$ 无关 | Onsager 反常耗散 → 无粘极限仍安全 |
| PKS 锥体中重联频率更高 | 几何约束是重联增强器 |
| $P(|\omega|_{\text{crit}})$ 指数衰减 | 高涡量事件概率为零 → 爆炸几乎不可能 |

**如果 256³ × 4 组参数 × 3 组粘度 = 12 次实验全部显示重联先于爆炸发生——这就是一篇可发表的数值证据论文。**

---

## 七、优先级

| # | 实验 | GPU时间 | 风险 | 优先级 |
|:--:|------|:---:|:---:|:---:|
| 1 | 双涡管碰撞 128³, 单参数 | 5 min | 低 | 🔴 立即 |
| 2 | 双涡管碰撞 256³, 全参数扫描 | 2 h | 低 | 🔴 |
| 3 | 各向同性湍流涡管网络 256³ | 30 min | 中 | 🟡 |
| 4 | PKS 锥体 + 伪谱+IBM 混合 128³ | 1 h | 高 | 🟢 |

---

> **一句话**：不跟 NS 的 PDE 理论硬碰硬。用 GPU 做物理学家做的事——在数值世界里找"安全阀总是在爆炸前跳闸"的统计铁证。积少成多，就是通往严格证明的探照灯。
