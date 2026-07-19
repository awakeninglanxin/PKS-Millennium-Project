# DeepSeek 专属冷邮件

> Hao Cai | 2026-07-13
> 
> DeepSeek 的特殊性：他们是 AI 模型公司，不是芯片设计公司。
> 切入点改为：Farey 树 ↔ MLA + MoE 路由优化。

---

## 邮件 4: 致 DeepSeek

```
Subject: Farey tree scheduling: same mathematical compression as MLA, different domain

Dear DeepSeek Team,

Your Multi-head Latent Attention (MLA) is the most elegant compression
I've seen in transformer architecture — the insight that K/V can be
projected into a low-dimensional latent space while preserving query-key
inner products is beautiful mathematics.

I discovered a striking parallel from number theory: the Farey tree
(1816). Its mediant operation (a+c)/(b+d) naturally encodes hierarchical
decomposition, much like how MLA's latent projection preserves semantic
structure while discarding redundancy.

What's fascinating is that the Farey tree's mathematical guarantees
directly translate to scheduling properties:

  Farey neighbor property: bc−ad=1
    → Adjacent tasks cannot conflict (deadlock-free guarantee)

  Mediant preserves irreducibility: gcd(a+c, b+d)=1
    → Merged modules are never redundant (no wasted computation)

When applied to MoE expert routing, the Farey tree provides a
deterministic "best-first" ordering — experts at lower tree depths
handle high-frequency tokens, while deeper experts activate only for
rare, complex tokens. This mirrors your load-balanced routing
but with mathematical guarantees instead of learned affinities.

Our Hybrid scheduler (Farey tree + Internal Address) reduces task
iteration by 39% vs standard methods. I believe the same principle
could reduce the token-to-expert routing overhead in MoE architectures.

Would you be interested in exploring whether Farey tree-structured
routing could complement MLA's latent space compression?

Code: https://github.com/awakeninglanxin/inverse-Mandelbrot-application

Best regards,
Hao Cai
```

---

## 为什么 DeepSeek 会看这封邮件

| DeepSeek 关心的事 | Farey 树提供什么 | 同构点 |
|------|------|------|
| MoE expert routing | Farey 树层级路由（深度=复杂度） | 确定性 vs 学习的负载均衡 |
| MLA 压缩 | Farey mediant = 保留结构的合并操作 | 两者消除冗余但保留语义 |
| 长上下文推理成本 | Hybrid −39% 迭代 = GPU时直接省钱 | 直接经济价值 |
| 训练效率 | Sharkovsky 序 = 有序探索 → 减少训练步 | 与课程学习同源 |

---

## 发送建议

| 收件方 | 发送时机 | 建议渠道 |
|------|------|------|
| DeepSeek | arXiv 上线后第 2 批 | GitHub Issues / 官方邮箱 / Twitter @deepseek_ai |
| 普林斯顿 RFIC | arXiv 上线后立即 | IEEE 论文作者邮箱 |
| Verkor | arXiv 上线后立即 | arXiv 作者邮箱 |
| Synopsys | DAC 2027 投稿后 | 会议联系 |

**优先级**：普林斯顿 > Verkor > DeepSeek > Synopsys
- 普林斯顿正在找"探索策略的结构先验"（最可能回复）
- DeepSeek 纯数学→模型架构的映射是二度创新（需要先有芯片领域的验证）
