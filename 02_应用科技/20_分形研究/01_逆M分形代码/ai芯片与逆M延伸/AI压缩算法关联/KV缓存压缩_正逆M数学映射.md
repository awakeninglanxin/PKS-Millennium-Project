# KV缓存压缩 × 正逆M数学映射 — 深度同构分析

> 2026-07-13 | TurboQuant/MLA/GQA × Möbius反演/Sharkovsky序/Farey分数

---

## 1. 问题定义

KV Cache 是 LLM 推理的最大内存瓶颈。2025-2026年间涌现出10+种压缩技术。本文从**逆M分形数学**的视角审视这些技术，揭示底层同构。

---

## 2. 十种KV压缩技术的数学分类

### 2.1 量化族（精度压缩）

| 方法 | 原理 | 位宽 | 内存节省 |
|------|------|:--:|:--:|
| FP8 KV-cache | 硬件原生FP8 TensorCore | 8-bit | 2× |
| KIVI (ICML 2024) | 非对称per-channel+per-token量化 | 2-4 bit | 2.6× |
| KVQuant | 校准混合精度 + 密-稀分解 | sub-4 bit | 3-4× |
| **TurboQuant** (ICLR 2026) | PolarQuant+QJL在线向量量化 | **3 bit** | **6×** |
| KVTC (NVIDIA) | PCA+自适应量化+熵编码 | 可变 | 20×(离线) |

### 2.2 驱逐族（选择性遗忘）

| 方法 | 原理 | 保留策略 |
|------|------|------|
| H2O (重击者) | 保留累积注意力分数最高token | Top-K |
| SnapKV | 对prompt聚类后采样 | 聚类中心 |
| StreamingLLM | 保留开头+sink token | 固定位置 |
| ChunkKV | 语义chunk压缩单元 | 按语义块 |
| PyramidKV | 金字塔层递减 | 底层多保留 |

### 2.3 架构族（结构重构）

| 方法 | 原理 | 节省 |
|------|------|:--:|
| GQA (Grouped-Query Attention) | 多Q头共享K/V头 | 2-8× |
| MQA (Multi-Query Attention) | 所有Q共享K/V | 16×+ |
| **MLA** (DeepSeek Multi-head Latent Attention) | K/V→低维潜向量 | **93.3%** |

---

## 3. 逆M数学的精确映射

### 3.1 TurboQuant ↔ Möbius 保角量化

TurboQuant的核心是两层变换：

```
Stage 1: PolarQuant
  v → v' = R·v     (R = 随机正交矩阵)
  目的：让向量分量均匀分布，消除量化偏差

Stage 2: QJL (Quantized Johnson-Lindenstrauss)
  v' → v_q = round(v'/Δ)·Δ
  目的：3-bit量化，保内积近似
```

**Möbius对应**：

```
Stage 1: c → 1/c
  1/c = |c|^{-1} · e^{-i·arg(c)}  = 保角旋转 + 模长反演
  = 复平面版本的"分量均匀化"（消除原点附近的聚集）

Stage 2: z → z² + 1/c
  迭代 = 非线性变换 = 类似QJL的"投影+量化"
  每步迭代把连续轨道离散化为 |z_n| 序列

性质对应：
  TurboQuant保内积   ←→ Möbius保角
  TurboQuant无偏估计 ←→ Möbius对合性 (1/(1/c)=c)
  3-bit量化         ←→ 离散逃逸步数 n
  6×内存压缩         ←→ ext/interior二分（大幅减少"内部"像素）
```

### 3.2 MLA ↔ DEM潜空间投影

MLA 核心：将 K/V 从高维投影到低维潜空间：

$$c_t^{KV} = W^{DKV} h_t, \quad k_t^C = W^{UK} c_t^{KV}, \quad v_t^C = W^{UV} c_t^{KV}$$

DEM 核心：将逃逸轨道从 n 维迭代序列投影到 1 维边界距离：

$$d(c,M) = 2\ln|z_n| \cdot \frac{|z_n|}{|dz_n|}$$

| MLA | DEM |
|------|------|
| 输入: h_t (hidden state, ~7168维) | 输入: {z₀,...,z_n} (n步轨道) |
| 投影: W^{DKV} (压缩) | 投影: dz 导数追踪 |
| 潜向量: c_t^{KV} (~512维) | 潜标量: d(c,M) (1维) |
| 上投影: W^{UK}/W^{UV} (展开) | 上投影: pot(c)+θ(c) (势能+角度) |
| 压缩比: 93.3% | 压缩比: ~99% (n→1) |

**DEM 的极致压缩**：DEM 把 n 维轨道压缩为 1 维边界距离 d，且保持了全部**边界结构信息**（d 小 = 边界，d 大 = 外部）。MLA 同样把高维 hidden state 压缩为低维潜向量，且保持了**语义结构信息**。

两者的根本原理一致：**用微分/投影在低维空间保持高维流形的拓扑结构**。

### 3.3 GQA ↔ Farey分数共享

GQA：多个 Query head 共享同一组 Key/Value head。

```
head_1: Q1, head_2: Q2, head_3: Q3  → 共享 →  K_g, V_g (只有一组)
```

逆M的 Farey 锚点：多个不同 zoom 级别的微型 Mandelbrot 集（来自不同的 c 值），共享同一组**Farey 分数**编码的结构。

```
zoom_1, zoom_2, zoom_3  → 共享 →  Farey分数的周期泡拓扑结构
```

| GQA | Farey共享 |
|------|------|
| 4个Q头 → 1组K/V | 多个M集微缩副本 → 1个Farey树的同构结构 |
| 节省 = (heads/Q_heads)× | 节省 = 用Farey分数编码而非逐泡描点 |
| 代价 = 表达能力下降 | 代价 = 不保所有微缩副本的细节差异 |

### 3.4 StreamingLLM ↔ Farey锚点保留

StreamingLLM：保留头几个tokens + "attention sink"（注意力沉没点），中间的token可以丢弃。

逆M等价：保留几个固定的 Farey 锚点（Period 1, Period 2, Period 3）+ 边界尖点（c=1/4），中间的泡虽然小但结构自相似，不需要每个都显式存储。

```
StreamingLLM: [tok0, tok1, tok2, ..., sink_token]
Farey版本:   [P1锚点, P2锚点, P3锚点, 尖点c=1/4]
              ↑开头保留    ↑高注意力    ↑关键转折
```

---

## 4. 新思路：用逆M数学改进KV压缩

### 4.1 Möbius量化（MuQuant）

**灵感**：TurboQuant 用正交旋转保证内积无偏 → Möbius 旋转变换能做得更好吗？

```
TurboQuant: v' = R·v  (R ∈ SO(d), 保Euclidean内积)
MuQuant:    v' = M·v  (M ∈ PGL(2,C), 保复内积 + 模长比)

优势：
1. Möbius 保圆 → 量化后相邻token的关系结构不丢失
2. 对合性 1/(1/v)=v → 可逆性保证，解码无信息丢失
3. |c|=1 自对偶边界 → 自然提供"零失真圆"，在此圆上量化=无损
```

实验方向：用 Möbius 旋转变换替代 PolarQuant 的正交旋转，测试 TurboQuant 的 3-bit → 2.5-bit 是否可行。

### 4.2 Douglas-Peucker 选择性保留

**灵感**：DP算法从 3353 个轮廓点中找出 **19 个拐点**，这些拐点保留了 95.7% 的宏观结构信息。

KV版本：
```
1. 对长序列的所有token计算"注意力权重曲线"
2. DP算法找出曲线上的拐点（权重突变的token位置）
3. 这些拐点 = 不可丢弃的"sink tokens"
4. 拐点之间的token = 可安全丢弃/降精度

预期：保留 15-20% 的tokens，保持 95%+ 的注意力质量
```

### 4.3 Sharkovsky序的预取调度

**灵感**：Sharkovsky序告诉我们周期出现的必然顺序（3→5→7→...），在推理中：

```
当前生成了 n 个token
→ 预测接下来会出现"等效周期 3"的复杂推理块
→ 预先分配高精度KV缓存
→ 当前生成的是"周期 1"的简单token
→ 用低精度缓存即可

实现：
  - token复杂度检测器（轻量分类器）
  - 根据检测结果动态切换缓存精度
  - Sharkovsky序指导的"预取-降级"循环
```

### 4.4 Farey树的层级压缩

**灵感**：Farey树的每一层比上一层多约 φ(n)/2 个节点，类似 KV 缓存的层级增长。

```
Farey树层级      KV缓存方案
L1 (P1): 1个节点 → 全精度缓存
L2 (P2): 1个节点 → 全精度
L3 (P3): 2个节点 → FP8
L4 (P4): 2个节点 → FP8
L5 (P5): 4个节点 → INT4
L6 (P6): 2个节点 → INT4
L7+    : 多个节点 → INT3 (TurboQuant)
```

越深层的token（越老的缓存），精度越低（因为它们对当前注意力的影响衰减类似 Farey 泡的半径递减）。

---

## 5. 可行性评估矩阵

| 思路 | 理论基础 | 实现难度 | 预期收益 | 优先级 |
|------|:--:|:--:|:--:|:--:|
| MuQuant (Möbius量化) | Möbius保角 ↔ 保内积 | 中 | 0.5-1 bit更多压缩 | 🔴 高 |
| DP选择性保留 | M=15 最优性 | 低 | 3-5× 内存省 | 🔴 高 |
| Sharkovsky预取 | 周期序 ↔ 预取序 | 中 | 15-30% 延迟降 | 🟡 中 |
| Farey层级压缩 | 层级↔精度衰减 | 低 | 2-3× 内存省 | 🟡 中 |
| DEM投影 = MLA类比 | d(c,M) ↔ c_t^{KV} | 理论阶段 | 待验证 | 🟢 探索 |

---

## 6. 与 M=15 Chiplet 的联合设计

M=15 在 period 2-25 所有候选值中是**四指标夺冠**的唯一最优解。这意味着：

```
KV缓存拓扑:
  15个存储节点 (对应15个Farey锚点)
  - 节点1-2: 高频基础token (Period 1-2) → 全精度
  - 节点3-6: 推理复杂token (Period 3-6) → FP8
  - 节点7-15: 长尾/长程token (Period 7-9) → INT4/TurboQuant

互联拓扑:
  - φ(n) → 节点间带宽权重
  - Farey分数坐标 → 物理布局映射
  - Sharkovsky序 → 无死锁仲裁协议
```

这个设计直接复用 M=15 Chiplet 验证结论，将数学最优性从芯片移植到 KV 缓存架构。
