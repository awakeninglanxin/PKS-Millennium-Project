# 多Agent芯片设计 × Calabi-Yau相位合并 — Verkor论文深度映射

> 2026-07-13 | Verkor Design Conductor 论文 + Calabi-Yau 8相位/逆M Sharkovsky序

---

## 一、Verkor Design Conductor 核心

**219 词需求 → 12 小时 → 7nm CPU 版图 (VerCore)**，工程师全程没碰键盘。

### 1.1 多 Agent 架构

| Agent | 职责 | 工具 |
|------|------|------|
| **Design Planning Agent** | 需求分析、微架构设计、实施计划 | LLM + RISC-V spec |
| **Design Review Agent** | 逐场景审查方案 | 检查清单 |
| **Module Implementation Subagent** | 实现每个模块 + 测试台 | Verilog + 仿真器 |
| **System Integration Agent** | RTL 整合 + 端到端测试 | OpenROAD |
| **Root Cause Analysis Subagent** | VCD 波形分析 → 根因定位 → 修复方案 | Python + Spike模拟器 |
| **PPA Closure Subagent** | 时序/面积/功耗收敛 | OpenROAD |

### 1.2 自主 Debug 实例

论文记录了一个典型自主修复流程：

```
1. 测试发现: 寄存器写入不匹配 (预期 x2, 实际 x5)
2. VCD→CSV: Python 逐行提取时间戳+寄存器
3. 与 Spike 参考逐条比对 → 定位 PC=0x2008
4. 发现: JAL 跳转后 0x200c 的 AUIPC x5 未冲刷
5. 根因: 流水线 flush 逻辑缺陷
6. 生成 RTL 修复方案 → 重跑测试 → 通过
```

全程无人工介入。

---

## 二、与逆M分形体系的精确映射

### 2.1 多 Agent 协作 ↔ Calabi-Yau 8相位合并

Verkor 的 6 个 Agent 各司其职 → Calabi-Yau 的 8 个相位 ($\alpha = 0 \to 2\pi$) 各生成一个流形切片。

**同构逻辑**：

| 维度 | Verkor 多 Agent | Calabi-Yau 8相位 | 逆M 8初值 z 倒数法 |
|------|------|------|------|
| 并行度 | 6 Agent 并行 | 8 phase 独立计算 | 8 初值并行迭代 |
| 融合方式 | System Integration Agent 合并 | `calabi_dif_a_merger` 合并 | 8初值取最大逃逸步数 |
| 冲突检测 | Root Cause Analysis 找错 | 差分合并器找不匹配面 | 轨道不一致 = 不同收敛路径 |
| 优化方向 | PPA Closure 收敛 | 花形叠加增强纹理 | 不同初值覆盖不同的内向收敛区域 |

**新思路**：Verkor 的 Root Cause Analysis Agent（从 VCD 波形反查根因）→ 在我们体系中等价于**从渲染图反推 DESCRIPTOR 参数**（K(x) 逼近器概念）。两者都是"从现象反推生成机制"。

### 2.2 Sharkovsky 序 ↔ Agent 调度协议

| Sharkovsky 周期 | Agent 角色 | 调度规则 |
|:--:|:--:|------|
| Period 1 (稳定不动点) | Design Planning Agent | 定义全局目标 |
| Period 2 (往复) | Design Review Agent | 迭代审查 |
| Period 3 (混沌门槛) | Module Implementation | 最复杂、最不可预测 |
| Period 5,7,... | Root Cause Analysis | 稀有但关键 |
| Period 4,8,... (2^n) | PPA Closure | 嵌套优化 |

**无死锁保证**：Sharkovsky 序确保 Agent 间不会互相等待形成死锁——因为序定义了**必然出现的顺序**，违反此序的等待必然存在更早触发条件。

### 2.3 Verkor 的"算力换经验" ↔ DESCRIPTOR 的"公式换像素"

Verkor 工程副总裁："我们在用算力换经验" —— AI Agent 用试错次数弥补人类直觉。

我们的 DESCRIPTOR："我们在用公式换像素" —— 100 字节参数替代 5MB 渲染。

| | Verkor | DESCRIPTOR | 共同本质 |
|------|------|------|------|
| 输入 | 219 词需求 | JSON 参数 | 极小信息量 |
| 输出 | 7nm 版图 (.gds) | 5MB 图像 (.png) | 极富结构输出 |
| 中间过程 | Agent 试错迭代 | 迭代引擎重算 | 从规则→结构的展开 |
| 压缩逻辑 | 存设计意图，不存版图 | 存公式参数，不存像素 | **Kolmogorov 复杂度极限** |

---

## 三、新应用路径

### 3.1 Farey 分数 ↔ MoE Agent 路由

Verkor 的 6 Agent 在 MoE（混合专家）架构下的最优路由：

```
输入 token → Farey 分数复杂度评估
  ├── 简单需求 (period 1-2) → Design Planning Agent (低 FLOPs)
  ├── 中等需求 (period 3-4) → Module Implementation Agent (中 FLOPs)
  ├── 复杂需求 (period 5+) → Root Cause Analysis Agent (高 FLOPs)
  └── 收敛需求 → PPA Closure Agent (嵌套优化)
```

### 3.2 Calabi-Yau "相位"动态调试

Calabi-Yau 的 8 个相位 (α=0→2π) 提供了**同一个流形的 8 个不同视角**。

对应芯片设计调试：
- α=0.00 → 功能验证视角 (逻辑正确)
- α=1.05 → 时序视角 (setup/hold)
- α=2.09 → 功耗视角 (power density)
- α=3.14 → 面积视角 (floorplan)
- ...
- α=6.28 → 集成视角 (full chip)

每个相位 = 设计审查的不同维度，合并后 = 完整的设计验证。

---

## 四、预判：Verkor 架构的逆M优化方向

| 当前痛点 | 逆M数学解法 | 预期收益 |
|------|------|:--:|
| Agent 随机试错效率低 | Sharkovsky 序约束探索路径 | 减少无效试错 30-50% |
| 多个 Agent 冲突 | Farey 树层级仲裁 | 无死锁保证 |
| 时序收敛盲目搜索 | Douglas-Peucker 拐点定位瓶颈 | 精准定位 1-2 个关键路径 |
| 需求→架构映射模糊 | DESCRIPTOR JSON → spec template | 输入标准化 |
| 算力成本高(数百亿token) | DESCRIPTOR 压缩→减少推理长度 | token 消耗减半 |

---

**参考文献**
- Verkor (2026). Design Conductor: A Fully Autonomous CPU Design Agent. arXiv:2603.08716.
- Emami, H. et al. (2023-2026). Princeton RFIC AI Design. IEEE.
- 本项目的 Calabi-Yau 8相位算法 (Phase 4, 逆时针与蛋形).
