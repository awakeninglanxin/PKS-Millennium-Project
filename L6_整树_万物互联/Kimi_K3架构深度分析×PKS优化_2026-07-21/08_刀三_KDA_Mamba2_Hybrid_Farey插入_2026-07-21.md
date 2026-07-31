# 刀三：KDA + Mamba-2 Hybrid — 线性层占比拉满

> **动什么**: K3 纯 attention 变体 → KDA (线性) + Mamba-2 block 插花 = 混合架构  
> **复杂度收益**: 70-80% 层用 O(n) 线性 recurrence, 只留精修层做 full attention  
> **风险**: 🟡 中等 — Jamba/Granite/Qwen3-Next 已有先例, 需重新训练

---

## 一、Hybrid 架构的 2025 共识

```
模型            比例              线性层类型       状态
─────────────────────────────────────────────────────────
Jamba 1.5       7 Mamba : 1 attn   Mamba SSM       已开源
Granite 4.0     9 Mamba-2 : 1 attn Mamba-2          已开源
Qwen3-Next 80B  —                  Gated DeltaNet   已发布
OLMo Hybrid     —                  Gated DeltaNet   已开源
MiniMax-01      —                  Lightning Attn   已发布
K3              全 KDA + MLA       KDA 近似线性     刚发布
```

**理论论证** (Allen AI OLMo Hybrid 论文): 纯 transformer 和纯线性模型各自有**表示盲区**——hybrid 可证明比任一方强。具体来说:
- Transformer 擅长精确 token-level attention (少数 token 间的精细交互)
- 线性 recurrence 擅长长程依赖 (序列级的平滑传输)

混用 = 各取所长。

## 二、为什么 K3 天然适合做 Hybrid

K3 的 block 模式已经是分层的:

```
当前 K3:  3 KDA block → 1 Gated MLA block → 3 KDA block → ...
           └─线性近似─┘   └─全注意力精修──┘

本意: KDA 扛计算, MLA 保质量

优化后: 3 KDA block → 1 Mamba-2 block → 1 Gated MLA block → ...
         └─线性近似─┘   └─状态空间─┘     └─全注意力精修──┘
```

**为什么插 Mamba-2 而不是 DeltaNet**: Mamba-2 和 KDA 的 Delta 压缩在数学上是亲戚——两者都做"状态压缩 + 线性时间递推"。但 Mamba-2 多了**对角状态矩阵**和**选择性门控**——这两样恰好能补 KDA 线性近似丢掉的"选择性"（KDA 把 QK^T 压成线性后，token 间的"选择性注意"被平均化了）。

### 数学对应表

| 组件 | KDA | Mamba-2 | 互补点 |
|:---|:---|:---|:---|
| 复杂度 | O(n) | O(n) | 同量级 |
| 状态形式 | Delta 压缩 (隐式) | 对角状态矩阵 (显式) | Mamba-2 更可解释 |
| 选择性 | 弱 (压缩丢失) | 强 (输入依赖的门控) | **Mamba-2 补 KDA 的短板** |
| 训练并行 | DEER/ELK 框架 | chunkwise parallel scan | 两套并行策略可互用 |

**核心观点**: 不需要全换——只在 K3 的 80+ 层里插 8-12 层 Mamba-2，替代部分 KDA block。这样:
- KDA 仍扛大部分计算 (50-60 层)
- Mamba-2 补选择性和长程状态 (8-12 层)
- Gated MLA 保留精修 (20 层，和现在一样)

## 三、连接 PKS 的 Farey 分相

这是 PKS 算法**唯一可能对 K3 有实际注入价值的点**——不是直接优化 KDA，而是优化 Mamba-2 的插入策略:

**问题**: Mamba-2 block 应该插在哪些层？

**PKS 方案**: 用 Farey 序列决定 Mamba-2 的插入位置

```
Farey 分数 {1/2, 1/3, 2/3, 1/4, 3/4, 1/5, 2/5, 3/5, 4/5, ...}
→ 映射到层索引: layer_i = round(L × F_n(i))
→ 插入位置天然"互素" → 任意两个 Mamba-2 block 的距离互不相同
→ 多尺度覆盖: 靠近输入端有 denser 分布, 靠近输出端 sparse

示例 (L=90, 插入 10 层 Mamba-2):
  F = {1/2, 1/3, 2/3, 1/4, 3/4, 1/5, 2/5, 3/5, 4/5, 1/6}
  → 层 {45, 30, 60, 23, 68, 18, 36, 54, 72, 15}
```

**为什么这个比 "幻方稀疏化 KDA" 靠谱**: Farey 插入位置解决的是一个真实的工程问题——"Mamba-2 block 应该怎么分布才能最大化信息流通"——而互素性恰好保证了**两层 Mamba-2 之间的距离永不重复** = 每个 Mamba-2 block 看到的历史窗口都不同。这是有数学依据的（互素 = 无冗余覆盖），不是瞎套幻方。

> ⚠️ 但仍需实验验证: Farey 插入 vs 均匀插入 vs 随机插入 vs 学出来的最优插入——哪个好，不清楚。

## 四、预期收益

| 指标 | K3 当前 | K3 + Hybrid | 来源 |
|:---|:--:|:--:|:---|
| KDA block 选择性 | 弱 | Mamba-2 补强 | 输入依赖门控 |
| 长程依赖 | KDA Delta 压缩 | Mamba-2 对角状态 | SSM 更稳 |
| 1M decode 延迟 | 6.3× (vs full attn) | 预计 8-10× | linear 层占比 ↑ |
| 参数量 | 2.8T | +~5% (Mamba-2 轻量) | 插 10 层 |

## 五、实施路径

```
第 1 步: 拿 K3 开源权重 (7/27)
第 2 步: 在 10 个 Farey 位置插 Mamba-2 block (从 mamba-2 官方权重初始化)
第 3 步: 小规模续训 (1B token) → 验证 loss 下降
第 4 步: 对比 Farey 插入 vs 均匀插入 vs 随机插入
第 5 步: 如果 Farey > 均匀 → PKS 有一条实证了
        如果均匀 ≥ Farey → Farey 没用, 但 hybrid 本身仍有效
```

---

## 六、三刀汇总

| # | 刀 | 动什么 | 数学结构 | 风险 | K3 权重需要？ |
|:--:|:---|:---|:---|:--:|:--:|
| 1 | DyT | Norm 层 | tanh 闭式缩放 | 🟢 低 | 不需要重训 |
| 2 | 闭式路由 | MoE routing | 二分图最优匹配 | 🟡 中 | 不需要重训 |
| 3 | Hybrid Mamba-2 | Block 结构 | SSM 状态空间 | 🟡 中 | 需要续训 |

**三刀递进**: 刀 1 (白捡) → 刀 2 (换 router) → 刀 3 (插 Mamba-2)。如果 K3 7/27 开源, 刀 1 当天就能验证。刀 2 需要实现 GPU 上的高效费用流。刀 3 需要 1B token 续训。

---

*文档: 2026-07-21 | 基于 Jamba/Granite/Qwen3-Next hybrid 路线 + Mamba-2 论文 + Farey 插入策略*
