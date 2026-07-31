# Calabi-Yau 流形算法 — 四阶段迭代演进全览

> 源目录: `E:\pythonProject\pythonProject\program\`
> 归档日期: 2026-07-13
> 总计: 39 个 Python 文件，跨越 4 个 phase（2024-05 → 2025-10）

---

## 一、演进时间线

```
2024-05-08 ─── Phase 1: 探索期 (6 files)
  calabi_yauK1K2.py 的 K1/K2 参数定义
  ↓
2024-05-16 ─── Phase 2: 组合与顶点 (12 files)
  多对象合并 (obj8in1) + 顶点提取 (vertices) + play系列交互
  ↓
2024-09-22 ─── Phase 3: tower塔系列 (13 files)
  3D塔楼可视化 · 丝滑几何 · 花形 · spin旋转
  ↓
2025-02-28 ─── Phase 4: 逆时针与蛋形 (8 files)
  逆时针旋转 · 蛋形投影 · 相位合并 · 差分合并器
```

---

## 二、各 Phase 文件清单与关联

### Phase 1：探索期 (2024-05-08 ~ 2024-05-15, 6 files)

| 文件 | 日期 | 大小 | 作用 |
|------|------|:--:|------|
| `calabi_yauK1K2.py` | 05-08 | 1.5KB | **起点** — 定义 Calabi-Yau 流形的 K1/K2 参数，基础拓扑 |
| `Calabi-Yau searl滚筒.py` | 05-09 | 2.5KB | Searl 效应的滚筒形变 |
| `Calabi-YauManifold.py` | 05-09 | 2.6KB | 流形数学定义（曲面参数化） |
| `playcalabi2.py` | 05-12 | 5.4KB | **交互式探索** — 第一版 play 系列 |
| `calabi-Yau_stl.py` | 05-12 | 1.8KB | STL 文件导出（3D 打印就绪） |
| `playcalabi.py` | 05-15 | 2.0KB | play 系列精简版 |

**迭代逻辑**：`calabi_yauK1K2`(参数定义) → `Manifold`(流形公式) → `playcalabi` 系列(交互可视化) → `stl`(实体导出)

---

### Phase 2：组合与顶点 (2024-05-16 ~ 2024-08-31, 12 files)

| 文件 | 日期 | 大小 | 作用 |
|------|------|:--:|------|
| `play_calabi2.py` | 05-16 | 2.3KB | play 系列 v2，改进交互 |
| `calabi-yau_obj8in1.py` | 05-16 | 3.1KB | **8合1** — 多对象合并为单个 OBJ |
| `play_calabi7.py` | 05-18 | 3.3KB | play v7 — 多视角渲染 |
| `calabi_vertices.py` | 05-19 | 3.4KB | **顶点提取** — 从网格中提取顶点拓扑 |
| `play_calabi9.py` | 05-20 | 0.3KB | play v9（最简版） |
| `play_calabi3.py` | 05-20 | 1.3KB | play v3 — 缩放/平移 |
| `calabi-Yau_simple2.py` | 05-21 | 2.5KB | **简化版** — 剥离复杂参数 |
| `play_calabi5.py` | 05-22 | 3.3KB | play v5 — 旋转动画 |
| `play_calabi8.py` | 05-22 | 5.1KB | play v8 — 最大最完整的 play |
| `play_calabi6.py` | 05-23 | 4.9KB | play v6 — 着色优化 |
| `horn_calabi.py` | 05-23 | 4.8KB | **喇叭形变** — 流形拓扑变为喇叭 |
| `play_calabi4.py` | 08-31 | 2.1KB | play v4（较晚补充） |

**迭代逻辑**：`obj8in1`(多对象) → `vertices`(顶点提取) → `simple2`(简化) → `horn_calabi`(拓扑变形) → play 系列并行迭代(v2→v9)

---

### Phase 3：tower 塔系列 (2024-09-22 ~ 2024-09-28, 13 files)

| 文件 | 日期 | 大小 | 作用 |
|------|------|:--:|------|
| `calabi-Yau_simple.py` | 09-22 | 2.5KB | **Phase 3 起点** — 继承 Phase 2 简化版 |
| `calabi-yau_obj.py` | 09-22 | 2.3KB | OBJ 导出（通用版） |
| `calabi-yau_obj圆台.py` | 09-22 | 2.4KB | **圆台形变** — 流形收束为圆台 |
| `tower_calabi - 丝滑.py` | 09-22 | 5.7KB | **丝滑几何** — 曲面平滑算法 |
| `tower_calabi - 花.py` | 09-24 | 5.8KB | **花形塔** — 多层花瓣叠加 |
| `tower_calabi - 花 - 副本.py` | 09-24 | 5.8KB | 花的副本（备份/对照） |
| `tower_calabi.py` | 09-25 | 5.7KB | **标准塔** — 基础宝塔造型 |
| `tower_calabi - spin 3 prt文件.py` | 09-27 | 6.2KB | spin 旋转 v3 + PRT 文件导出 |
| `tower_calabi - 花2.py` | 09-27 | 5.9KB | 花形 v2 — 改进花瓣密度 |
| `tower_calabi - spin 2.py` | 09-27 | 6.3KB | spin v2 — 旋转参数优化 |
| `tower_calabi - spin 2 - 无体积.py` | 09-27 | 5.3KB | spin v2 无线框图版本 |
| `tower_calabi - spin - 副本.py` | 09-28 | 5.3KB | spin 备份 |
| `tower_calabi - spin.py` | 09-28 | 5.3KB | **spin 最终版** — 旋转核心算法 |

**迭代逻辑**：`obj圆台`(收束) → `丝滑`(平滑) → `花`(多层) → `tower`(标准塔) → `spin` 系列(旋转 × 4 迭代: spin→spin2→spin3→无体积)

---

### Phase 4：逆时针与蛋形 (2025-02-28 ~ 2025-10-24, 8 files)

| 文件 | 日期 | 大小 | 作用 |
|------|------|:--:|------|
| `tower_calabi - 逆时针.py` | 02-28 | 5.7KB | **逆时针旋转** — 改变 spin 方向 |
| `tower_calabi - 逆时针 -丝滑几何无颜色 - 有厚度.py` | 10-12 | 7.7KB | 丝滑几何 + 厚度参数（**最大文件**） |
| `tower_calabi - 逆时针 -丝滑几何无颜色 -蛋.py` | 10-12 | 4.4KB | **蛋形投影** — 流形映射为蛋形 |
| `tower_calabi - 逆时针 -丝滑几何无颜色 -蛋 - 不同相位合一.py` | 10-12 | 4.7KB | **相位合并** — 8 个相位(0→2π)合成一张图 |
| `tower_calabi - 逆时针 -丝滑几何无颜色 -蛋 - 不同相位合一 - 花.py` | 10-12 | 4.7KB | 相位合并 + 花形叠加 |
| `calabi_dif_a_merger.py` | 10-24 | 4.7KB | **差分合并器** — 通用两流形融合算法 |
| `tower_calabi - 逆时针 -丝滑几何无颜色.py` | 10-24 | 3.3KB | 最终精简版 |
| `calabi - 逆时针 -丝滑几何无颜色 -多个相位合并.py` | 10-24 | 4.2KB | **多个相位合并通用版** |

**迭代逻辑**：`逆时针`(方向改变) → `有厚度`(物理参数) → `蛋形`(投影变换) → `相位合一`(8相融合) → `花形叠加` → `dif_a_merger`(通用融合器)

---

## 三、核心算法演进脉络

```
K1/K2 参数定义
  ↓
流形曲面公式 (Calabi-YauManifold)
  ↓
交互可视化 (play 系列 v2→v9, 12个迭代)
  ↓
STL/OBJ 3D 导出 (calabi-Yau_stl / calabi-yau_obj)
  ↓
多对象组合 (obj8in1) + 顶点拓扑 (vertices)
  ↓
tower 塔楼结构 (tower_calabi 系列)
  ├── 丝滑几何平滑
  ├── 花形多层叠加
  └── spin 旋转 (5个迭代版本)
  ↓
逆时针方向反转
  ↓
蛋形投影变换
  ↓
相位合并 (0→2π 连续融合)
  └── dif_a_merger 通用差分融合
```

---

## 四、关键文件之间的引用关系

| 子文件 | 继承自 |
|------|------|
| `Calabi-YauManifold.py` | `calabi_yauK1K2.py` (参数) |
| `playcalabi2.py` → `play_calabi9.py` | `Calabi-YauManifold.py` (流形基类) |
| `calabi-yau_obj8in1.py` | `calabi-yau_obj.py` (导出基类) |
| `tower_calabi.py` | `calabi-Yau_simple.py` (简化流形) |
| `tower_calabi - spin.py` → `spin 3` | `tower_calabi.py` (塔结构) |
| `tower_calabi - 逆时针.py` | `tower_calabi - spin.py` (旋转算法) |
| `calabi_dif_a_merger.py` | 全部 tower / egg 系列 (通用融合) |

---

## 五、与逆M分形项目的关联

Calabi-Yau 流形是代数几何中 $\mathbb{C}^6$ 上的 Calabi-Yau 3 流形 的实数截面可视化。其数学结构与逆 Mandelbrot 集的关联点：

1. **复流形投影**：两个项目都涉及 $\mathbb{C}$ 上的高维几何 → $\mathbb{R}^2$ 或 $\mathbb{R}^3$ 的截面渲染
2. **参数空间探索**：K1/K2 参数扫描 ⇔ Möbius k 值平移扫描
3. **相位概念**：Phase 4 的 8 相位合并 ⇔ 逆M的 8 初值 z 倒数法
4. **3D 塔结构**：tower_calabi 的层级堆叠 ⇔ 宝箧印塔的 5 层几何抽象栈
5. **smooth/丝滑算法**：曲面平滑 → DEM 距离估计的连续光晕映射

---

## 七、创新延伸：CY-SR 螺旋辐射算法

基于 Phase 3/4 的指数螺旋映射，提出全新算法：

👉 [CY-SR_Calabi-Yau螺旋辐射_水滴外部创新算法.md](CY-SR_Calabi-Yau螺旋辐射_水滴外部创新算法.md)

将 `exp(iθ + ln(r)·K)` 引入水滴外部纹理，创造：
- **模式A**：星系旋臂——螺旋密度 K 控制臂数
- **模式B**：相位干涉——8相位(0→2π)莫尔纹 = Calabi-Yau α扫掠
- **模式C**：指数浮雕——3D高度场 + DEM金边

与逆M本质共鸣：指数映射⇔倍周期级联连续化，相位⇔Farey锚点。

---

## 六、文件统计

| Phase | 时间跨度 | 文件数 | 时段 |
|:--:|------|:--:|------|
| 1 | 2024-05-08 ~ 2024-05-15 | 6 | 8 天 |
| 2 | 2024-05-16 ~ 2024-08-31 | 12 | 107 天 |
| 3 | 2024-09-22 ~ 2024-09-28 | 13 | 7 天（密集开发） |
| 4 | 2025-02-28 ~ 2025-10-24 | 8 | 238 天（长期间歇） |
| **总计** | 2024-05 ~ 2025-10 | **39** | 536 天 |
