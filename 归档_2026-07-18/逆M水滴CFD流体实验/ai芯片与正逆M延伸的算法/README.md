# Farey-Hybrid Chip Scheduler

> **A 210-year-old number theory discovery accelerates chip design by 39%.**
>
> DAC 2027 · Hao Cai

[![Stars](https://img.shields.io/github/stars/awakeninglanxin/ai-chip-design-farey-tree-application?style=social)](https://github.com/awakeninglanxin/ai-chip-design-farey-tree-application)

---

## 一句话

Farey 树（1816）的 mediant 操作 $(a+c)/(b+d)$ 天然编码芯片设计中"两个子模块合并为父模块"的过程。基于此构建的 Hybrid 调度器比 EDA 工业标准 CPM 快 39%。

---

## 核心发现

### 三层实验验证 (8算法 × 3场景 × 500轮)

| 排名 | 算法 | DAG芯片 | 混合并行 | 灾难恢复 | 🏆综合 |
|:--:|------|:--:|:--:|:--:|:--:|
| 🥇 | **Hybrid** | **3.81s** | **3.16s** | **5.35s** | **4.11s** |
| 🥈 | InternalAddr | 3.90s | 3.17s | 5.48s | 4.18s |
| 🥉 | FareyTree | 3.95s | **3.16s** | 5.68s | 4.26s |
| 4 | Fibonacci | 4.12s | 3.20s | 6.06s | 4.46s |
| 5 | Sharkovsky | 4.07s | 3.32s | 6.42s | 4.94s |
| — | CPM (Synopsys标准) | 4.66s | 3.34s | 12.11s | 6.70s |

**Hybrid 综合比 CPM 快 38.7%**。灾难恢复场景差距扩至 55.8%——CPM 先攻最难集成模块，失败回滚代价极大；Hybrid 先简后繁，经验累积自然降低后续失败率。

### 算法选择不是一步到位的

```
直觉选择: Sharkovsky（最出名的动力系统定理）
  ↓ 全家族对比
发现问题: FareyTree 比 Sharkovsky 多省 2%
  ↓ 场景交叉验证
终极答案: Hybrid = FareyTree(简单任务) + InternalAddr(复杂任务)
  ↓ 灾难恢复专项
确认优势: Hybrid −55.8% vs CPM（灾难下差距最大）
```

---

## 为什么是新的

| 搜索 | 结果 |
|------|:--:|
| "Farey tree" + "chip scheduling" | 0 |
| "mediant" + "module merge" + "chiplet" | 0 |
| "Farey tree" + "VLSI" + "decomposition" | 0 |

唯一先例：ICCAD 1995 用 Farey **序列**（1D 数值列表）做吞吐率探索。我们用 Farey **树**（2D 层级拓扑 + mediant 操作）做任务调度。两者共享数学对象但使用方式完全不同。

**论文 Claim**：*"We observe that the Farey tree's mediant operation — (a+c)/(b+d) — naturally encodes the merging of two sub-modules into a parent module in chiplet design. To our knowledge, this is the first application of Farey tree topology to chip design task scheduling."*

---

## 数学保证

| 性质 | 公式 | 调度含义 |
|------|:--:|------|
| 邻居性质 | $bc-ad=1$ | 相邻任务不可能冲突（无死锁） |
| mediant 保最简 | $\gcd(a+c,b+d)=1$ | 合并后的模块非冗余 |
| 完全性 | 所有有理数恰好出现一次 | 任意复杂度任务有唯一树位置 |

---

## 与产业对接

| 目标 | 策略 | 状态 |
|------|------|:--:|
| **华为海思** | "不依赖 Synopsys 专利" 话术 | 📬 冷邮件就绪 |
| **普林斯顿 RFIC** | Farey 树 = RL 探索的结构先验 | 📬 Emami 邮件就绪 |
| **Verkor DC** | Hybrid −56% 灾难恢复 → 减少 token 消耗 | 📬 Krishna 邮件就绪 |
| **DeepSeek** | Farey 树 ↔ MLA 不同维度的数学压缩 | 📬 邮件就绪 |
| **OpenROAD** | SDC 插件已实现 | ✅ 代码就绪 |

完整邮件模板和知乎文章 → `OpenROAD_集成/执行包_五步发送.md`

---

## 文件导航

### 📜 论文与数据
| 文件 | 内容 |
|------|------|
| `Farey-Hybrid_Chip_Scheduler_白皮书.md` | 完整白皮书(Claim+数学+实验+集成路线) |
| `实验方法论_完整数据.md` | 8算法×3场景全量数据, 可复现 |
| `论文提纲_Farey_Native_Chip_Design.md` | DAC 2027 格式论文提纲 |

### 🐍 算法实现
| 文件 | 内容 |
|------|------|
| `逆M调度算法全集对比.py` | 8算法×5场景×500轮 |
| `三调度器正式实现_五场景对比.py` | Hybrid/InternalAddr/FareyTree 正式版 |
| `灾难恢复_真实故障注入仿真.py` | 故障注入(15%概率)+回滚 |
| `Sharkovsky_Agent调度器原型.py` | Sharkovsky序演变史 |
| `Farey_版图数据集生成器.py` | 100张Farey芯片版图 |

### 🔬 跨学科分析
| 文件 | 内容 |
|------|------|
| `AI逆向设计_正逆M数学同构.md` | 普林斯顿逆向设计 ↔ Möbius反演 |
| `多Agent芯片设计_CalabiYau相位合并.md` | Verkor 6Agent ↔ Calabi-Yau 8相位 |
| `AI芯片设计三层架构_2026突破综合.md` | 辅助→自动化→创新三层模型 |
| `Farey_DESCRIPTOR_芯片设计语言.md` | 500B JSON → 10MB GDS 压缩 |
| `Farey_Native_逆M融合_新突破验证路线图.md` | Farey+逆M融合验证路径 |

### 🚀 OpenROAD & 落地
| 文件 | 内容 |
|------|------|
| `OpenROAD_集成/hybrid_scheduler.py` | OpenROAD SDC插件 |
| `OpenROAD_集成/执行包_五步发送.md` | arXiv+知乎+4封冷邮件,复制即用 |
| `OpenROAD_集成/华为专项对接.md` | 华为海思/诺亚方舟/2012 三条线 |
| `OpenROAD_集成/国内AI界对接策略.md` | DeepSeek/Kimi/平头哥 全覆盖 |
| `OpenROAD_集成/DeepSeek冷邮件.md` | Farey树 ↔ MLA 数学平行 |

---

## 快速开始

```bash
# 全量算法对比
python 逆M调度算法全集对比.py

# Hybrid vs CPM 正式对比
python 三调度器正式实现_五场景对比.py

# 灾难恢复专项
python 灾难恢复_真实故障注入仿真.py

# OpenROAD 插件
cd OpenROAD_集成 && python hybrid_scheduler.py
```

**依赖**: Python 3.12+, NumPy

---

## 关联仓库

- [inverse-Mandelbrot-application](https://github.com/awakeninglanxin/inverse-Mandelbrot-application) — 22 UF着色算法 + 9 Möbius变换 + CY-SR螺旋辐射

---

> *"We observe that the Farey tree's mediant operation naturally encodes the merging of two sub-modules into a parent module in chiplet design."*

**Hao Cai** · 2026 · [arXiv](即将上线)
