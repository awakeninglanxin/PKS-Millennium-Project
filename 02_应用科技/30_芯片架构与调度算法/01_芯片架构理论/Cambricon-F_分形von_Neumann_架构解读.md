# Cambricon-F 分形 von Neumann 架构解读

> 来源：元宝对话 + 中科院计算所 Cambricon 系列
> 核心：递归处理单元——整个芯片是 von Neumann 机，每个处理单元本身又是小型 von Neumann 机
> 日期：2026-07-19

---

## 一、一句话理解

**Cambricon-F 的核心理念**：处理单元 (PE) 本身又是另一个 Cambricon 机。同质递归——每个 PE 内部结构与其父级相同，软件栈复用。

```
Cambricon-F 的分形 = von Neumann 架构的"自相似"
  Die 级 (von Neumann 机)
    └─ 每个 PE 也是 von Neumann 机
        └─ 每个 PE 内的子单元也是 von Neumann 机
            └─ ...
```

---

## 二、与传统架构的对比

| | 传统 GPU/SIMD | Cambricon-F |
|:---|:---|:---|
| 顶层 | von Neumann | von Neumann |
| PE 结构 | 简化 ALU（无独立取指） | **完整 von Neumann**（有独立取指+译码） |
| 递归 | 无 | **PE 内部也是 von Neumann** |
| 负载均衡 | 编译器/调度器负责 | 递归结构天然的负载分形 |
| 软件栈 | 每级不同 | **同构——软件可跨级复用** |

---

## 三、与幻方九宫 tile 的结合

Cambricon-F 的递归 PE = "九宫 tile" 的天然载体：

```
L0: 3×3 九宫 tile（9个ALU, 每个ALU是小型 von Neumann）
  → 9个 tile 的幻和=15 约束功耗/算力
    中心 tile（幻方值5）作为调度核
    调度核本身又是 3×3 的子九宫

L1: 5×5 的 L0 tile（25个完整 von Neumann core）
  → 每个 core 内部是 3×3 ALU（又是递归的子九宫）
    5阶幻和=65 约束 core 间负载

L2: 7×7 的 L1 cluster（49个 core）
  → 每个 cluster 内是 5阶幻方
    7阶幻和=175 约束 cluster 间负载
```

**关键**：Cambricon-F 的同构递归保证了软件栈可以跨级复用。L0 的 ALU 调度算法 = L1 的 core 调度算法 = L2 的 cluster 调度算法——因为它们在数学上是同构的（只差幻方阶数）。

---

## 四、分形 von Neumann 的三个数学性质

### 4.1 自相似性（分形核心）

每一级 PE 的内部结构与父级相似：都有取指、译码、执行、写回。只是数据宽度和规模不同。

形式化：若 f(x) 表示 x 级 PE 的结构，则：

$$f(L_n) \cong f(L_{n+1}) \text{ 在 } \mathbb{Z}/k \text{ 尺度变换下}$$

其中 k 是幻方阶数的比值。例如从 3阶→5阶，k=5/3。

### 4.2 工作量再分配能力

传统架构中，PE 之间的任务分配完全由编译器/调度器负责。在分形架构中，因为每层都是完整的 von Neumann 机：

- L0 ALU 可以独立决定是否将子任务下发给它的子 PE
- L1 core 可以独立决定是否将子任务下发给它的子 ALU
- 不需要中央调度器——**分形的自相似保证了负载的自然再分配**

### 4.3 软件栈同构复用

Cambricon-F 的编译器只需生成一种指令格式。因为所有级别的 PE 都共享同一 ISA 的子集/超集，同一个二进制可以在不同级执行（性能不同，但正确性不变）。

这在幻方架构中意味着：**D 系数线性公式 a·M[r][c]+b 在所有级别上复用**——只需改参数 a 和 b，不需要重新设计调度算法。

---

## 五、与幻方 + Farey + PWM 的对接

```
Cambricon-F 分形 von Neumann
    │
    ├── 架构层：每级 tile 用幻方行列守恒做负载均衡
    │         （Cambricon-F 提供递归载体，幻方提供负载约束）
    │
    ├── 器件层：每个 PE 的 P/N 对称传输门 + Farey 分相
    │         （分形 PE = Farey phase 的自然分配单位）
    │
    └── 热层：每级 tile 背面走分形微通道
              （分形 PE 的物理布局与分形流道天然对齐）
```

---

## 六、Cambricon-F 的已知局限 + 幻方的补全

| Cambricon-F 的局限 | 幻方方案的补全 |
|:---|:---|
| 递归但无负载均衡约束 | 每级幻和 = 负载硬上限 |
| PE 间无热管理 | AC-TEC + 分形流道 |
| 时钟同步无分相 | Farey 分相降 di/dt |
| 无 chiplet 间约束 | 泛幻方 Torus 拓扑 |

---

## 七、与中科院后续工作的关系

Cambricon-F 之后还有：
- **Cambricon-S**：稀疏计算加速
- **Cambricon-Q**：量化推理
- 但递归分形架构的思想可能已被放弃（后续系列更注重专用加速）

幻方方案可以视为 **Cambricon-F 的分形思想的集成电路热管理层**——把"结构递归"扩展到"负载递归+热递归"。

---

## 八、可验证方向

| # | 方向 | 方法 |
|:---:|:---|:---|
| 1 | Cambricon-F 论文中是否已有分形负载均衡 | 搜 "Cambricon fractal load balance" |
| 2 | Siamese 参数是否可用于 Cambricon 的 PE 间路由 | 模拟: 6参数 vs 全表路由的延迟对比 |
| 3 | 分形 von Neumann 的热仿真 | 用 PyTorch 模拟多级幻方的热传导 |
