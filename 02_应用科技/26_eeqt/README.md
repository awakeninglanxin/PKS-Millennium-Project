# EEQT 分形可视化 — 项目说明

> **EEQT 作为元操作系统**：Q（量子/连续/潜在态）↔ C（经典/离散事件/显式模式）↔ g_{αβ}（耦合/信息跳跃）
> 三个组件统一描述所有算法（机器人控制、AI、量化交易、生物）。
> 本项目的球面分形混沌博弈，就是这个元操作系统的**最底层的可视化证明**。

---

## 一、项目定位

本项目实现 **Event-Enhanced Quantum Theory (EEQT)** 在球面上的混沌博弈（Chaos Game）可视化。它展示了量子自旋态在检测器方向之间随机跳跃形成的**分形吸引子**。

### EEQT 与 PKS 项目的深度关联

| EEQT 概念 | PKS 项目对应 | 本项目位置 |
|:---|:---|:---|
| ε 跳跃阈值 | SEG 的磁饱和开关（H > H_S） | `epsilon` 滑块 |
| Bloch 球面游走 | 滚柱在环内的公转/自转 | 球面点云 |
| 多检测器方向 | 12/22/32 滚柱的环形分割 | 几何体顶点 |
| 分形吸引子 | 三环的 Poynting 能流自组织图案 | 渲染结果 |

---

## 二、目录结构与文件清单

```
26_eeqt/
│
├── core/           ← 唯一核心可执行文件
│   └── EEQT_ChaosGame_SelectedGeometries.html   (30KB, 打开即玩)
│
├── theory/         ← 4 份必读理论 PDF
│   ├── Event-Enhanced Quantum Theory.pdf         (215KB, EEQT 原始论文)
│   ├── EEQT.pdf                                  (341KB, 混沌博弈算法)
│   ├── On_Quantum_Iterated_Function_Systems.pdf  (385KB, QIFS 理论)
│   └── quantum jump eeqt.pdf                     (255KB, 量子跳跃机制)
│
├── docs/           ← 6 份理解项目的说明文档
│   ├── EEQT数学原理说明.md                       (28KB, 全套数学公式)
│   ├── EEQT_关系网索引_对比分析.md                (9.8KB, 功能对比+函数调用)
│   ├── EEQT_版本迭代路程.md                       (11KB, 版本演进全史)
│   ├── EEQT_几何体坐标推导路径.md                  (7.4KB, 坐标数学推导)
│   ├── BUG_ANALYSIS.md                            (2.5KB, Bug 记录)
│   └── multi_ai_eeqt.txt                          (1.9KB, 多AI哲学分析)
│
├── dev/            ← 5 个开发/验证辅助脚本
│   ├── quaternion_rotation.py                     (6.7KB, 四元数验证+JS生成)
│   ├── quaternion_module.js                       (2.3KB, 前端旋转模块)
│   ├── extract_nb.py                              (1.1KB, NB代码提取)
│   ├── read_nb.py                                 (1.9KB, 关键词扫描)
│   └── read_nb2.py                                (1.2KB, 核心函数提取)
│
├── archive/        ← 4 份参考存档
│   ├── Demonstration-Quantum-*.definition.nb      (913KB, Mathematica 原始演示)
│   ├── deepseek+智谱完善eeqt宇宙真相论文.docx     (43KB, AI生成论文)
│   ├── eeqt解释eplison解决0时出现跳跃模糊是算法问题.docx (21KB)
│   └── 宇宙真相与eeqt导读.docx                    (20KB)
│
├── README.md       ← ⬅ 你现在正在读的
└── desktop.ini     ← (已删除，Windows 系统文件)
```

---

## 三、最终版 HTML 的完整特性

`EEQT_ChaosGame_SelectedGeometries.html` 包含了 **211 行 JS 代码**，集成以下全部功能：

### 3.1 9 种几何体

| 几何体 | 顶点数 | 说明 |
|:---|:---:|:---|
| Tetrahedron | 4 | 四面体 — 最少顶点，分形最稀疏 |
| Octahedron | 6 | 八面体 — ε=0.1 低阈值才能看到清晰分形 |
| Cube | 8 | 立方体 |
| Merkaba | 8 | 双四面体（Star Tetrahedron）— 两个三棱锥反向嵌套 |
| Icosahedron | 12 | 正二十面体 — **最优 ε=0.9** |
| Dodecahedron | 20 | 正十二面体 |
| **Compound 32** | **32** | **二十面体+十二面体复合** — 双层结构 |
| **C60 Full** | **60** | **富勒烯** — 带 3D 旋转支持 |
| Rhombic Dodecahedron | 14 | 菱形十二面体 |

### 3.2 核心控件

| 控件 | 范围 | 默认值 | 说明 |
|:---|:---:|:---:|:---|
| epsilon | 0.005~0.999 | 0.800 | 量子跳跃阈值（内置 SOLID_EPS 预设表自动切换） |
| points | 50,000~2,000,000 | 500,000 | 采样点数 |
| rot-X / rot-Y / rot-Z | -180°~+180° | 0 | **四元数连续旋转** — 最终版独有 |
| projection | stereo/lambert/ortho | stereo | 三种球面投影方式 |
| **formula mode** | Standard / Smooth | Smooth | **Standard** = P=(1+⟨n,r⟩)/2N；**Smooth** = P=(1+ε²+2ε⟨n,r⟩)/(N(1+ε²)) |

### 3.3 显示特性

- **Hausdorff 维数**：6 尺度 box-counting 实时计算，带 log-log 拟合信息
- **群论对称性**：显示当前几何体的对称群（Oh, Td, Ih 等）
- **5 项实时指标**：跳数/投影质量/有效面积/角分布熵/各向异性
- **图例**：底部色块标注当前几何体
- **公式显示**：实时显示当前使用的概率公式

---

## 四、文件依赖链

```
┌─ 理论核心 ─────────────────────────────────────────────────┐
│  Event-Enhanced Quantum Theory.pdf     ← EEQT 原始论文     │
│  On_Quantum_Iterated_Function_Systems.pdf  ← QIFS 背景     │
│  quantum jump eeqt.pdf               ← 量子跳跃机制        │
│  EEQT.pdf                           ← 混沌博弈数学基础      │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌─ 数学推导 ──────────────────────────────────────────────────┐
│  EEQT数学原理说明.md      ← 整套公式 + 几何体坐标          │
│  EEQT_几何体坐标推导路径.md  ← C60/半球体/缩放因子推导      │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌─ 可执行产物 ────────────────────────────────────────────────┐
│  EEQT_ChaosGame_SelectedGeometries.html  ✅ 打开即玩       │
│  （内嵌 Quaternion 模块，无需外部依赖）                     │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌─ 开发支撑 ──────────────────────────────────────────────────┐
│  quaternion_rotation.py  ← Python 验证 + JS 生成            │
│  quaternion_module.js    ← 独立 JS 模块参考                 │
│  extract_nb.py / read_nb.py / read_nb2.py ← NB 提取工具    │
└──────────────────────────────────────────────────────────────┘
```

---

## 五、使用方法

### 5.1 直接打开

```bash
# 双击 HTML 文件，或在命令行：
start "" "D:\AAA我的文件\PKS_千禧难题_统一解\26_eeqt\core\EEQT_ChaosGame_SelectedGeometries.html"
```

无需任何服务器，纯前端。

### 5.2 推荐操作流程

1. 先选 **Octahedron**，调 epsilon 到 **0.1** → 看到八面体星型分形
2. 选 **Icosahedron**，调 epsilon 到 **0.9** → 黄金比例的分形花瓣
3. 切到 **C60 Full**，拖拽 **rot-X/rot-Y/rot-Z** → 看分形在球面旋转
4. 切到 **Compound 32** → 二十面体+十二面体复合结构的干涉
5. 切换 **formula mode**（Standard vs Smooth）→ 感觉跳变行为的差异
6. 选 **Merkaba** → 双四面体的八卦分形结构
7. 看右下角 **Hausdorff 维数** → 数值越大，空间填充越密

---

## 六、版本遗留问题

当前文件夹只包含**最终版** `EEQT_ChaosGame_SelectedGeometries.html`。历史版本的 HTML 文件（如 `REF_plus_hemi_v3.html`、`EEQT_fixed_c60.html`、C60半球体研究等）不在此处——它们在旧的工作区 `C:\Users\ThinkPad\WorkBuddy\20260425104509\eeqt\`。

如果想恢复 C60 半球体（Pentagon/Hegagon Hemisphere）功能，需要从旧工作区复制 `REF_plus_hemi_v3.html` 回来。

| 最终版已有 | 最终版没有（如需恢复） |
|:---|:---|
| 9 种几何体 | C60 五边形/六边形半球体（30+30顶点） |
| 四元数旋转 | 预计算对齐模式表（align 0/1/2） |
| Standard/Smooth 双模式 | 多几何体叠加渲染 |
| Hausdorff + 群论 + 5 指标 | 亮度/点大小控制 |

---

> *最后更新：2026-06-03 — 全面重写，正确定义文件角色*
