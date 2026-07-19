# Farey Graph 论文集

> 收录6篇Farey图相关核心论文。Farey图由Farey分数序列构造，具有小世界、哈密顿、外平面、完美图等优良性质。

---

## 论文清单

### 1. Farey Graphs as Models for Complex Networks (2011)
- **作者**: Zhongzhi Zhang (Fudan), Francesc Comellas (UPC Barcelona)
- **期刊**: Theoretical Computer Science, vol.412, pp.865-875
- **DOI**: 10.1016/j.tcs.2010.11.034
- **链接**: https://arxiv.org/abs/1105.0575
- **核心发现**: 首次系统提出Farey图作为复杂网络模型。证明Farey图具有小世界性、指数型度分布、高聚类系数、直径≈t+1。

### 2. Label-based Routing for Farey Graphs (2016)
- **作者**: Yinhu Zhai, Yinhe Wang (Guangdong Univ. of Tech)
- **期刊**: Scientific Reports, vol.6, 25621
- **DOI**: 10.1038/srep25621
- **本地**: `2016_Zhai_Farey_Label_Routing_SciRep.pdf` (594KB)
- **核心发现**: 提出基于标签的Farey图最短路径路由算法，时间复杂度O(n)。所有最短路径由两个Fibonacci数的乘积决定。

### 3. Generalized Farey Graphs (2018)
- **作者**: Wenchao Jiang, Yinhu Zhai, Paul Martin, Zhiming Zhao
- **期刊**: Scientific Reports, vol.8, 12194
- **DOI**: 10.1038/s41598-018-30712-2
- **本地**: `2018_Jiang_Generalized_Farey_NatureSciRep.pdf` (1334KB)
- **核心发现**: 推广Farey图至广义Farey图G_{m,t}，使得模型同时拥有小世界+无标度+高聚类三性质。度分布指数γ∈[2,3]。

### 4. Counting Spanning Trees of Generalized Farey Graphs (2020)
- **期刊**: Physica A, vol.556, 124775
- **DOI**: 10.1016/j.physa.2020.124775
- **链接**: https://www.sciencedirect.com/science/article/pii/S0378437120303745
- **核心发现**: 给出广义Farey图生成树数量的闭合公式。

### 5. Spanning Trees in Farey Graphs (2012)
- **作者**: Zhang et al.
- **期刊**: Physica A
- **核心发现**: 首次给出Farey图生成树的精确计数公式。

### 6. Random Walks on Farey Graphs (相关)
- **来源**: Physical Review E, Journal of Physics A等
- **内容**: Farey图上的随机游走、同步、谱分析等动力学过程

---

## 与Farey-Native AI芯片的关系

| 论文发现 | 芯片应用 |
|------|------|
| 小世界性 (直径≈t+1) | 互联延迟下界 ~log_φ(N) |
| 度分布 (幂律) | φ(n)加权带宽分配 |
| 标签路由 (O(n)) | Farey邻接查找硬件实现 |
| 外平面性 | 2D中介层可布线 |
| 3-可着色 | 3时钟域无干扰调度 |
| 唯一哈密顿性 | 单周期全遍历测试路径 |

---

> **注意**: 当前所有Farey图研究均为复杂网络建模用途。将其用于AI芯片互联拓扑设计是本项目的首创贡献。
