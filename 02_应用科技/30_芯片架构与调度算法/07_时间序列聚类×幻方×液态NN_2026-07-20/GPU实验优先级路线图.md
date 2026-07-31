# 时间序列聚类 12篇论文 × GPU 实验可行性评估

> 🎯 从前面的12篇论文中，选出最适合用 GPU 验证、与 Super k-Shape 结合度最高的 5 篇，给出可执行的实验方案。

---

## 一、GPU 实验候选排序

| 排名 | 论文 | 可 GPU 验证？ | 已有代码基础？ | 实验周期 | 论文价值 |
|:--:|------|:--:|:--:|:--:|:--:|
| 🥇 | CDCC (对比学习) | ✅ PyTorch原生 | ⚠️ 需实现 | 2-3天 | AAAI 2024 |
| 🥈 | k-Graph (图嵌入) | ⚠️ 图计算 | ❌ 全新 | 3-5天 | 2025 新方向 |
| 🥉 | ShapeFormer (Transformer) | ✅ Transformer | ⚠️ 部分 | 2-3天 | 2024 |
| 4 | DBSCAN Consistency | ✅ 可并行 | ✅ 距离替换 | 1天 | 2024 |
| 5 | E2USD (状态检测) | ✅ 编码器 | ❌ 全新 | 3-5天 | 2024 |
| 6 | DUET (双聚类) | ✅ | ❌ | 3-5天 | 2024 |
| 7-11 | 其余 | — | — | — | — |
| 12 | CDCC (已覆盖) | — | — | — | — |

---

## 二、🥇 第一优先：CDCC × Super k-Shape 融合实验

### 为什么排第一

- CDCC 是 AAAI 2024 顶会论文，有公开 PyTorch 实现
- 它的 cluster-level contrastive loss 与我们的 anti_magic_diversity_loss **数学同构**
- 实验只需改 loss 函数 + 加幻方因子化编码器
- 40 个 UCR 数据集可直接复用

### 实验方案

**消融对比**: 在 5 个代表性 UCR 数据集上跑 6 组对照

| # | 模型 | 说明 |
|---|------|------|
| 基线 | k-Shape (2015) | 传统 SBD |
| A | CDCC (原始) | AAAI 2024 基线 |
| B | CDCC + Anti-magic λ=0.01 | 替换 cluster contrastive loss |
| C | CDCC + Magic Factor | 三域编码(时域/频域/幻方域) |
| D | CDCC + Anti-magic + Magic | 双增强 |
| E | Super k-Shape (我们) | 全部四个增强 |

**预期**: B 组应与 A 组持平或略优（loss 同构），C 组应有显著提升（三域 > 双域），D 组应是最优。

### GPU 需求

```bash
# 估计：RTX 4090, ~2-3 小时完成全部 6 组 × 5 数据集
# 内存：~4GB (UCR 数据集很小)
# 框架：PyTorch + CuPy 加速 k-Shape centroid 计算
```

---

## 三、🥈 第二优先：DBSCAN × Farey 距离

### 为什么

- 最简单：只需替换 DBSCAN 的距离函数
- DBSCAN 有理论保证 (Hartigan 一致性)
- Farey 距离我们已经实现
- 1 天内可出结果

### 实验方案

在 UCR 5 个数据集上对比：

| # | 距离度量 | 聚类算法 |
|---|---------|----------|
| 1 | 欧氏距离 | DBSCAN (原始) |
| 2 | DTW | DBSCAN |
| 3 | SBD (k-Shape距离) | DBSCAN |
| 4 | **Farey 路径距离** | DBSCAN |
| 5 | k-Shape | k-Shape (2015) |

### 代码量

```python
# 只需修改 DBSCAN 的 metric 参数
from sklearn.cluster import DBSCAN
from super_kshape import farey_path_distance

# 原始
dbscan = DBSCAN(eps=0.5, metric='euclidean')

# Farey 版本
dbscan = DBSCAN(eps=0.5, metric=farey_path_distance)
```

---

## 四、🥉 第三优先：ShapeFormer × Sharkovsky-DP

### 为什么

- Sharkovsky-DP 拐点天然适合做 shapelet 候选
- 可以大幅减少 Transformer 的自注意力搜索空间
- 有现成的 Transformer 骨架 (只需加拐点掩码)

### 实验方案

ShapeFormer 的标准流程是"Transformer 发现 shapelet → 分类"。
加 Sharkovsky-DP 后变成："Sharkovsky 拐点预选 shapelet → Transformer 精修 → 分类"。

对照组：
1. ShapeFormer 标准版 (self-attention 全搜索)
2. ShapeFormer + Sharkovsky 掩码 (只注意拐点附近)
3. ShapeFormer + Sharkovsky + Farey 注意力初始化

---

## 五、第四优先：k-Graph × Super k-Shape

### 为什么排后

- 图嵌入需要 networkx / PyTorch Geometric，代码量最大
- 但学术潜力最高（2025 新方向 + 可解释性热点）

### 实验方案

把 Sharkovsky 拐点作为图的"重要节点"，在 k-NN 图构建时给拐点更高的连接权重。这不是简单替换距离函数，而是修改图构建算法本身。

---

## 六、推荐执行顺序

```
Day 1: 实验 2 (DBSCAN × Farey) — 快速出结果，验证多尺度距离在 DBSCAN 中的价值
Day 2-3: 实验 1 (CDCC × Super k-Shape) — 核心论文实验
Day 4: 写报告，整理对比表格
Day 5+: 实验 3 (ShapeFormer × Sharkovsky) — 如果前两个效果好
```

---

## 七、GPU 资源需求汇总

| 实验 | 时间 (RTX 4090) | 显存 | 主要库 |
|------|:--:|:--:|------|
| DBSCAN × Farey | ~30 min | <1GB | sklearn, numpy |
| CDCC × Super k-Shape | ~2-3 hrs | ~4GB | PyTorch, CuPy |
| ShapeFormer × Sharkovsky | ~3-4 hrs | ~8GB | PyTorch, einops |
| k-Graph | ~5-8 hrs | ~16GB | PyTorch Geometric |
| **总计** | **~12-16 hrs** | **~16GB** | — |
