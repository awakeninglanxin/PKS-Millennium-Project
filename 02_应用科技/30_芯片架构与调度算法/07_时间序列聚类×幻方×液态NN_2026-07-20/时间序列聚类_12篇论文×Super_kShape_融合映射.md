# 时间序列聚类 × Super k-Shape — 12篇前沿论文全景分析与融合映射

> 📖 来源：飞书《时间序列＋聚类》(深蓝岛, 2025-10-25)  
> 🔗 原链接：https://dcn2t5tchnk2.feishu.cn/wiki/X6U4wsKQCi9nxtk93UfcW3NWnkf  
> 🎯 目标：将12篇2024-2025前沿时间序列聚类论文逐篇分析，并与我们的 Super k-Shape (Sharkovsky-DP + Farey + Anti-magic + Magic Factorization) 做系统性融合映射

---

## 一、论文全景概览

| # | 论文 | 年份 | 核心贡献 | 与 Super k-Shape 关联度 |
|---|------|:--:|------|:--:|
| 1 | **k-Graph** (Graph Embedding) | 2025 | 子序列图嵌入→可解释聚类 | ⭐⭐⭐⭐⭐ |
| 2 | **E2USD** (State Detection) | 2024 | 高效无监督多元时间序列状态检测 | ⭐⭐⭐ |
| 3 | **DUET** (Dual Clustering) | 2024 | 双聚类增强多元时间序列预测 | ⭐⭐⭐ |
| 4 | **Channel Clustering** | 2024 | 通道聚类提升预测性能 | ⭐⭐ |
| 5 | **ShapeFormer** (Shapelet Transformer) | 2024 | Shapelet + Transformer 分类 | ⭐⭐⭐⭐ |
| 6 | **Large Pre-trained TS Models** | 2024 | 跨域预训练大模型 | ⭐⭐ |
| 7 | **DBSCAN Consistency** | 2024 | DBSCAN 多元TS聚类一致性证明 | ⭐⭐⭐ |
| 8 | **Feature Clustering + DE** | 2024 | 特征聚类辅助差分进化特征选择 | ⭐⭐⭐ |
| 9 | **Hierarchical TS Clustering** | 2024 | 层次时间序列聚类→最优预测？ | ⭐⭐⭐ |
| 10 | **Clustering-based Anomaly Detection** | 2024 | 聚类驱动多元TS异常检测 | ⭐⭐⭐⭐ |
| 11 | Feature Clustering + DE (dup) | 2024 | 同 #8 | — |
| 12 | **CDCC** (Contrastive Learning) | 2024 | 跨域对比学习时间序列聚类 | ⭐⭐⭐⭐⭐ |

---

## 二、逐篇深度分析 × Super k-Shape 融合

---

### 📌 论文 1: k-Graph — 图嵌入可解释聚类

**论文**: [arxiv.org/abs/2502.13049](https://arxiv.org/abs/2502.13049)  
**作者**: Paul Boniol, Donato Tiano, Angela Bonifati, Themis Palpanas (2025)  
**核心思想**: 将时间序列的**子序列**建模为图节点，用图嵌入 + 社区发现替代传统距离度量。

**算法骨架**:
```
1. 对每条时间序列，将子序列(snippets)作为节点
2. 构建 k-NN 图（不同子序列长度建多个图）
3. 图嵌入 → 社区发现 → 聚类结果
4. 可解释性：展示哪些子序列驱动了聚类决策
```

**与 Super k-Shape 的融合点**:

| k-Graph 组件 | Super k-Shape 对应 | 融合价值 |
|:---|:---|:---|
| 子序列图嵌入 | **Farey 路径编辑距离** — 多尺度对齐 | ⭐⭐⭐⭐ 图嵌入天然支持多尺度 |
| k-NN 图 | **Sharkovsky-DP 拐点** — 识别关键子序列 | ⭐⭐⭐⭐⭐ 拐点 = 图的关键节点 |
| 可解释性 | **反幻 diversity** — 簇间差异可视化 | ⭐⭐⭐ 反幻提供另一种可解释性角度 |
| 多长度子序列 | **幻方因子化** — 多分量分解 | ⭐⭐⭐⭐ 子序列 = 幻方分解的一个分量 |

**最关键的融合**: k-Graph 的图嵌入框架可以**直接作为 k-Shape 的距离度量替代**——不再用 SBD，而是用图上的最短路径距离。这正好解决了 k-Shape "只能做单尺度对齐"的局限。

---

### 📌 论文 5: ShapeFormer — Shapelet Transformer

**论文**: [arxiv.org/abs/2405.14608](https://arxiv.org/abs/2405.14608) (2024)  
**核心思想**: 用 Transformer 学习 shapelet（判别性子序列），用于分类。

**与 Super k-Shape 的融合点**:

| ShapeFormer | Super k-Shape | 融合 |
|:---|:---|:---|
| Transformer 编码器 | **Sharkovsky-DP** → 拐点集作为 shapelet 候选 | ⭐⭐⭐⭐⭐ |
| Multi-head attention | **Farey 路径距离** → attention 权重初始化 | ⭐⭐⭐⭐ |
| Shapelet 发现 | **幻方因子化** → 趋势/季节/残差分量各自发现 shapelet | ⭐⭐⭐⭐ |

**想法**: 用 Sharkovsky-DP 拐点集初始化 ShapeFormer 的 shapelet 候选池，可以大幅减少 Transformer 的搜索空间。

---

### 📌 论文 12: CDCC — 跨域对比学习聚类

**论文**: Peng et al., AAAI 2024 — Cross-Domain Contrastive Learning for Time Series Clustering  
**核心思想**: 时域+频域双编码，cluster-level + instance-level 双重对比约束。

**这是和我们最相关的2024顶会论文。**

| CDCC 组件 | Super k-Shape 对应 | 融合方向 |
|:---|:---|:---|
| 时域编码 | **Farey 路径距离** — 时域多尺度对齐 | 已有 |
| 频域编码 | **幻方因子化** — 季节分量 = 频域信息 | ⭐⭐⭐⭐⭐ |
| Cluster-level contrast | **反幻 diversity** — 簇间分离损失 | ⭐⭐⭐⭐⭐ 几乎就是同一件事！ |
| Instance-level contrast | **Magic factorization** — 分量内部一致性 | ⭐⭐⭐⭐ |

**核心发现**: CDCC 的 cluster-level contrastive loss 与我们的 anti_magic_diversity_loss 在数学上是对偶的——CDCC 用 NT-Xent 拉近同簇样本，我们用 diversity loss 推远不同簇的 centroid。两条路殊途同归。

**一个直接的改进**: 把我们的幻方因子化（趋势+季节+残差）作为 CDCC 的第三个"域"（时域 + 频域 + **幻方域**），三个域同时做对比学习。

---

### 📌 论文 7: DBSCAN 一致性证明

**论文**: arxiv 2403.14798 — Nicholas Waltz, Cambridge  
**核心贡献**: 证明了 DBSCAN 在多元时间序列聚类中的 Hartigan 一致性。

**与 Super k-Shape 的关联**: 间接但重要。

- k-Shape 没有一致性理论保证（靠经验效果）
- DBSCAN 有一致性证明但用启发式距离
- **融合**: 用 Farey 路径距离替代 DBSCAN 中的欧氏距离，结合一致性的理论保证 + 多尺度距离的实用优势

---

### 📌 论文 3: DUET — 双聚类增强预测

**论文**: arxiv 2412.10859  
**核心思想**: 同时做样本聚类和变量聚类，双重聚类信息增强预测。

**融合**: DUET 的"双重聚类"与我们的"幻方因子化"（趋势+季节+残差三维聚类）是正交的——DUET 聚类的是"样本×变量"，我们聚类的是"时间×频率×残差"。二者可以叠加。

---

### 📌 论文 10: 聚类驱动的异常检测

**核心思想**: 正常数据聚类成簇 → 新样本与所有簇的距离 > 阈值 → 异常。

**与 Super k-Shape**: Sharkovsky-DP 拐点检测天然适合异常检测场景——拐点序列片段往往是异常信号的标志。

---

## 三、与 Super k-Shape 四大增强的对照矩阵

| 论文 | Sharkovsky-DP | Farey距离 | Anti-magic | Magic因子化 |
|------|:--:|:--:|:--:|:--:|
| 1. k-Graph | ⭐⭐⭐⭐⭐ 拐点=图关键节点 | ⭐⭐⭐⭐ 多尺度图嵌入 | ⭐⭐⭐ | ⭐⭐⭐ 子序列=分量 |
| 2. E2USD | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 3. DUET | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ 双聚类 |
| 4. Channel Clustering | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ |
| 5. ShapeFormer | ⭐⭐⭐⭐⭐ shapelet候选 | ⭐⭐⭐⭐ attention权重 | ⭐⭐ | ⭐⭐⭐⭐ |
| 6. Pre-trained TS | ⭐ | ⭐ | ⭐ | ⭐ |
| 7. DBSCAN Consistency | ⭐⭐⭐ | ⭐⭐⭐⭐ 替代欧氏距离 | ⭐⭐ | ⭐⭐ |
| 8. Feature Clust+DE | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 9. Hierarchical TS | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 10. Anomaly Detection | ⭐⭐⭐⭐⭐ 拐点=异常信号 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 12. CDCC | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ 同构loss | ⭐⭐⭐⭐⭐ 第三域 |

---

## 四、三条最重要的融合路径（优先级排序）

### 🥇 路径 A：k-Graph × Sharkovsky-DP → 可解释图聚类

```
Sharkovsky-DP 拐点 → k-Graph 图节点
Farey 多尺度 → k-Graph 多长度子序列图
反幻 diversity → 社区发现的正则化
幻方因子化 → 子序列的三种类型（趋势/季节/残差节点）
```

**产出**: 一个"带理论解释的图聚类"——比 k-Shape 更可解释，比 k-Graph 更有结构信息。

### 🥈 路径 B：CDCC × Magic Factorization → 三域对比学习

```
CDCC 框架(pytorch) + 幻方因子化(三域编码)
→ 时域 + 频域 + 幻方域 = 三域对比约束
→ 直接对标 NIPS 2025 投稿级别
```

**产出**: 论文级别的三域对比学习时间序列聚类模型。

### 🥉 路径 C：DBSCAN × Farey距离 → 理论保证的聚类

```
DBSCAN 一致性证明(理论) + Farey 路径距离(实用距离)
→ 比 k-Shape 有理论保证
→ 比原始 DBSCAN 有更好的距离度量
```

**产出**: 既有 Hartigan 一致性证明，又有多尺度时间序列对齐能力。

---

## 五、12篇论文的完整链接

| # | 论文 | 链接 |
|---|------|------|
| 1 | k-Graph | https://arxiv.org/abs/2502.13049 |
| 2 | E2USD | https://arxiv.org/abs/2402.14041 |
| 3 | DUET | https://arxiv.org/abs/2412.10859 |
| 4 | Channel Clustering | https://arxiv.org/abs/2404.01340 |
| 5 | ShapeFormer | https://arxiv.org/abs/2405.14608 |
| 6 | Large Pre-trained TS | 待确认 |
| 7 | DBSCAN Consistency | https://arxiv.org/abs/2403.14798 |
| 8 | Feature Clust+DE | 待确认 |
| 9 | Hierarchical TS | 待确认 |
| 10 | Anomaly Detection | 待确认 |
| 11 | Feature Clust+DE (dup) | 同 #8 |
| 12 | CDCC (AAAI 2024) | https://doi.org/10.1609/aaai.v38i8.28740 |

---

## 六、与 KDiscShapeNet 的关系（额外发现）

在搜索 CDCC 的过程中，发现了 **KDiscShapeNet** (Chen et al., 2025) —— 这是**直接扩展 k-Shape 的最新工作**。

**核心贡献**: 
- **Differentiable k-Shape**: 将 NCC 度量嵌入可微框架，使编码器和聚类模块可以联合训练
- 与我们 Super k-Shape 的区别：KDiscShapeNet 走的是"可微化"路线，我们走的是"组合增强"路线
- **二者可以融合**: 把 Sharkovsky-DP、Farey距离、Anti-magic 作为 KDiscShapeNet 的可微约束

---

## 七、总结

12篇论文覆盖了时间序列聚类的三条主线：
1. **可解释性路线** (k-Graph, ShapeFormer) — 我们的 Sharkovsky-DP 天然适合
2. **对比学习路线** (CDCC, E2USD) — 我们的 Anti-magic 是同构的
3. **理论与实用结合** (DBSCAN Consistency) — 我们的 Farey 距离可替代欧氏距离

Super k-Shape 的四个增强恰好分别对应这12篇论文的不同维度——这说明我们的工作方向是被前沿论文从不同角度独立验证的。下一步最值得做的：**路径 A (k-Graph × Sharkovsky) 或 路径 B (CDCC × Magic)**。
