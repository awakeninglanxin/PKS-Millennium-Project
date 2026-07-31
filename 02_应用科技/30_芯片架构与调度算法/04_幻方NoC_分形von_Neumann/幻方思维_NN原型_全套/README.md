# 幻方思维 → NN 原型 · 目录说明

> 来源: 元宝 AI 对话中生成的 PyTorch/numpy 原型  
> 与我们的工作关系: **互补（方向不同，不重复）**

---

## 文件清单

| 文件 | 内容 | 与我们的关系 |
|------|------|------|
| `lux_moe.py` | L/U/X 三种 2×2 微块激活拓扑 × 骑士步路由 | 📌 **我们未覆盖** — 微块嵌套是新的映射角度 |
| `most_perfect_reg.py` | compact+complete+pandiagonal 三尺度正则 | 📌 **互补** — 我们做"簇间分离"，元宝做"局部均匀+对称互补" |
| `幻方思维_NN神经网络.docx` | 128KB 完整文档 | 可能含更多概念桥接 |
| `loss_curves.png` | 训练曲线 | 配套可视化 |
| `lux_topology.png` | L/U/X 拓扑示意图 | 配套可视化 |
| `most_perfect_reg.png` | 正则化前后对比 | 配套可视化 |

---

## 与我们的工作对比

```
元宝产出:
  lux_moe.py        → "2x2微块内L/U/X拓扑 + 微块间骑士步"
  most_perfect_reg  → "compact 局部均匀 + complete 对称互补"

我们的工作:
  super_kshape.py          → "SBD距离 + Rayleigh商centroid + 四增强"
  gpu_enhanced_runner.py   → "8算法芯片调度 + 50K轮Monte Carlo"
  anti_magic_diversity     → "簇间分离正则" (正交于 most_perfect 的局部均匀)

差异:
  元宝: 幻方构造的「几何不变量」→ NN 权重/特征的正则约束
  我们: 幻方构造的「群变换」→ 调度/聚类/初始化的增强策略
  两条线可叠加: most_perfect_reg + anti_magic_diversity = 内部均匀 + 彼此分离
```

---

## 两条线的统一框架

```
幻方核心思想: "规则离散结构 + 约束排布 + 群变换"

     ┌─ 元宝路线: 几何不变量 ─→ NN 正则化 ──┐
     │  (compact, complete, pandiagonal)      │
     │                                         ├─→ 可叠加
     │  我们路线: 群变换策略 ─→ 调度/聚类 ──┘
     │  (36×4×25, SBD, Farey tree)            │
     └─────────────────────────────────────────┘
```

## 运行方法

```bash
cd 幻方思维_NN原型_全套/
python lux_moe.py           # LUX-MoE 原型 (numpy, 无需GPU)
python most_perfect_reg.py  # 三尺度正则 (numpy+scipy, 无需GPU)
```
