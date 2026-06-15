# 🔄 py 代码迭代路径说明 — 从 E 盘原始代码到 PKS_千禧难题_统一解

> **"每一个 .py 文件都有它的前世今生。"**
>
> 本文档追踪从 `E:\pythonProject\pythonProject\program\` 到 `D:\AAA我的文件\PKS_千禧难题_统一解\` 的完整代码演化路径，标注关键类继承关系、技术方案分叉点和最新版本位置。

---

## 〇、总览：四大演化线

```
E:\pythonProject\pythonProject\program\
│
├── kudo horn羚羊角nurbs.py ─────────────────────────────┐
│   (基础: NurbsSurfaceGenerator + SpiralParameters)      │
│                                                         │
│   ┌──────────────────────┬──────────────────────────────┤
│   ▼                      ▼                              ▼
│  漏斗/                   螺锥/                          (后续演化)
│  NURBS→OBJ (trimesh)    NURBS→STEP (OCC)                │
│                                                         │
│                          螺锥dxf双轨扫掠/ ──────────────┤
│                          SpiralSweepGenerator → DXF      │
│                                     │                   │
│                                     ▼                   │
│                          最简原始模版用于生成直锥螺旋管/  │
│                          SpiralSweepGenerator (扩展版)   │
│                          +质心+磁铁+G2/G4/G9+Numba JIT   │
│                                                         │
│  PKS_千禧难题_统一解/                                    │
│  ├── 01_geometry/        ← 蛋形几何 + ANU 参数化        │
│  ├── 02_mesh/            ← CFD 网格生成                  │
│  ├── 03_simulation/      ← 涡旋仿真                      │
│  ├── 10_E盘代码归档/     ← ★ 本次新增：E盘代码档案       │
│  ├── 09_historical_evolution/  ← 历史代码演化线          │
│  ├── 🏗️ 23_黎曼假设证明/     ← M1-M6 完整证明              │
│  ├── 🧩 22_霍奇猜想证明/     ← NPAR 框架                   │
│  ├── 🔗 20_杨-米尔斯质量间隙证明/ ← ANU 1680匝             │
│  ├── 🔗 13_PvsNP证明/        ← ANU 不可分解               │
│  └── 🔗 12_BSD猜想证明/       ← 辫群自由生成元              │
└─────────────────────────────────────────────────────────┘
```

---

## 一、演化线 A：NURBS 曲面生成（羚羊角管）

### 1.1 演化路径

```
根目录：kudo horn羚羊角nurbs.py (11,951 bytes)
  ├── 类: SpiralParameters (参数容器)
  ├── 类: NurbsSurfaceGenerator (trimesh 方案)
  │
  ├──→ 漏斗/kudo horn...最终版 -漏斗设置.py (14,417 bytes)
  │     【方案 A：trimesh 纯网格方案】
  │     使用 RectBivariateSpline 插值 → trimesh 网格
  │     输出: OBJ 格式
  │     无 OpenCascade 依赖
  │
  └──→ 螺锥/kudo horn...最终版-螺锥设置.py (17,984 bytes)
        【方案 B：OpenCascade STEP 方案】
        使用 GeomAPI_PointsToBSplineSurface → BRepAlgoAPI_Fuse
        输出: STEP 格式 (工业 CAD)
        新增: 多实例面融合 + SpiralParameters 增强版
```

### 1.2 关键分叉点

| 特性 | 方案 A (漏斗/trimesh) | 方案 B (螺锥/OCC) |
|------|-------------------|-----------------|
| 内核 | scipy + trimesh | pythonocc-core (OpenCascade) |
| 输出格式 | OBJ | STEP |
| 多实例 | ❌ | ✅ (num_instances) |
| 曲面融合 | ❌ | ✅ (BRepAlgoAPI_Fuse) |
| 工业兼容 | 低（仅可视化） | 高（CAD/CAM 加工） |
| 归档位置 | `10_E盘代码归档/01_NURBS_Funnel_Trimesh/` | `10_E盘代码归档/02_NURBS_SpiralCone_OCC/` |

### 1.3 在 PKS 项目中的位置

- `09_historical_evolution/B_羚羊角管to螺旋管进化/` — 包含 F-S 标架方案（PKS 项目自己的 NURBS 路线）
- 方案 B (OCC) 的 STEP 输出仍未集成到 PKS 主流程——这是待做事项

---

## 二、演化线 B：DXF 双轨扫掠（螺旋管生成）

### 2.1 演化路径

```
根目录：羚羊角管中心线与蛋尖双轨+多断面 -dxf 样条线来连.py (6,776 bytes)
  │  基础双轨扫掠概念
  │
  └──→ 螺锥dxf双轨扫掠/ (69个变体文件)
        │  核心类: SpiralSweepGenerator
        │  黄金比衰减: phi = (√5-1)/2
        │  对数螺旋: h2 = log(0.5)\log(phi)
        │  输出: DXF 样条线 (ezdxf)
        │
        ├── 舒式螺旋斜流泵系列 (~18个)
        │   ├── 单螺旋 / 双螺旋
        │   ├── 非线性扭转 (2^n / 2^(-n) / t^e)
        │   ├── locas外 + sun内蛋面 双截面
        │   └── 蛋面镜像
        │
        ├── 羚羊角管+蛋尖双轨系列 (~12个)
        │   ├── 阴阳 / t平方
        │   └── 等距/非等距偏移
        │
        ├── 旋叶发电机系列 (~6个)
        │   └── 最新: 2025-10-03 优化曲线版
        │
        ├── 黎曼zeta应用系列 (~5个)
        │   └── 流体力学叶片截面
        │
        └── 电子波/驻波/舒曼频率系列 (~6个)
            └── 非线性驻波分析

            ↓ 继承 + 大幅扩展

最简原始模版用于生成直锥螺旋管/ (76个变体文件)
  │  核心类: SpiralSweepGenerator (扩展版)
  │  新能力:
  │  ├── Numba JIT 加速 (贝塞尔 + 旋转矩阵)
  │  ├── 质心约束 (带孔 + 质心在中)
  │  ├── 磁铁配置
  │  ├── 蓝线混接多线多规扫掠 (G2/G4/G9 连续性)
  │  ├── 管壁波动纹 (滑滑梯波)
  │  ├── 多曲线混合 (2/3 曲线)
  │  ├── 曲率求导不变优化
  │  └── DXF 断面加载 + 渐变过渡
  │
  ├── 直锥非线性螺旋管系列 (~15个)
  ├── 舒伯格蛋 + 螺旋系列 (~8个)
  ├── anu蛋形场约束系列 (~8个)
  ├── 螺锥盒子 + Fibonacci 叶序系列 (~7个)
  └── 黄金比 schauberger 蓝线混接系列 (~6个)
```

### 2.2 关键版本速查

| 版本 | 文件 | 修改时间 | 亮点 |
|------|------|---------|------|
| **最完整 DXF** | 舒式螺旋斜流泵+...蛋面镜像.py (12,979B) | 2024-12-26 | 所有特征合一 |
| **最新优化** | 旋叶发电机+...优化曲线.py (9,744B) | 2025-10-03 | 顶上不干涉 |
| **圆盘变体** | 舒式螺旋羚羊角管圆盘.py (12,978B) | 2025-02-14 | 圆盘形式 |
| **最复杂直锥** | 直锥非线性...质心在中 单管.py (38,645B) | 2025-11-12 | 全特征集大成 |
| **最新蛋螺旋** | 舒伯格蛋...缩放sqrt(n)-倒序.py (14,655B) | 2026-02-01 | Schauberger 蛋参数化 |
| **基础模板** | 最简原始模版用于生成直锥螺旋管.py | — | 入门模板 |

### 2.3 类继承关系

```
SpiralSweepGenerator (基础版 — 螺锥dxf双轨扫掠/)
  ├── 黄金比衰减: phi = (√5-1)/2
  ├── 对数螺旋参数化
  ├── DXF 样条输出 (ezdxf)
  │
  └──→ SpiralSweepGenerator (扩展版 — 最简原始模版/)
        ├── + Numba JIT 加速
        ├── + 质心约束
        ├── + 磁铁配置
        ├── + G2/G4/G9 混接扫掠
        ├── + 管壁波动纹
        ├── + 多曲线混合
        ├── + DXF 断面加载
        └── + 曲率求导不变优化
```

---

## 三、演化线 C：蛋形曲线参数化

### 3.1 演化路径

```
双曲锥斜切 (Schauberger 原始几何)
  ↓
k_E 参数族 (PKS 项目定义)
  ├── k_E = 2.0: 八度蛋 (Fibonacci 离散谱)
  └── k_E ≈ 1.9371: 黄金极限蛋 (KAM 稳定流形)
  ↓
egg_curve.py (PKS 核心)
  ├── parametric_form(): z₁,z₂ → 参数方程
  ├── implicit_F(): 隐式蛋形方程
  └── k_E_scan(): 参数扫描
  ↓
舒伯格蛋Die Ei-Kurve 系列 (最简原始模版/)
  ├── 蛋螺旋 缩放sqrt(n).py
  ├── 蛋螺旋 缩放sqrt(n) - 倒序.py  ← 最新 (2026-02-01)
  └── 蛋螺旋 缩放1除n - 副本.py
  ↓
anu蛋形场约束系列 (最简原始模版/)
  ├── anu蛋形场约束曲线.py
  ├── anu蛋形场约束曲线3.py
  ├── anu蛋形+椭圆场约束曲线.py
  └── anu3d曲线.py
```

### 3.2 在 PKS 项目中的位置

- `01_geometry/egg_curve.py` — PKS 核心蛋形参数化
- `01_geometry/golden_ratio_cone.py` — 黄金比双曲锥
- `01_geometry/anu_parameterization.py` — ANU 七级螺旋参数化
- `09_historical_evolution/A_蛋形曲线发现史/` — 历史演化档案

---

## 四、命名体系关键词解读

帮助理解 E 盘代码中的创建者命名习惯：

| 关键词 | 含义 |
|------|------|
| **舒式** | 创建者命名体系（Shu 风格） |
| **locas** | Lucas 数列参数 |
| **sun** | Sun 数列参数 |
| **阴阳** | Yin-Yang 对称/反对称模式 |
| **t平方** | 参数使用 t² 缩放 |
| **2的n / 2的-n / t的e次方** | 不同缩放速度曲线 |
| **蛋面 / 蛋尖** | 蛋形截面或蛋形尖端约束 |
| **非线性扭转** | 非均匀螺旋扭转 |
| **滑滑梯波** | 管壁波纹形态 |
| **蓝线G4/G9混接** | Rhino 风格连续性级别（G2=曲率连续, G4=更高阶, G9=极高阶光滑） |
| **质心** | 截面质心约束 |
| **磁铁** | 磁场/力场约束 |
| **叶序fibonacci / 137.5°** | 植物叶序黄金角 |

---

## 五、从 E 盘到 PKS_千禧难题_统一解 的迁移对照

| E 盘原始位置 | PKS 归档位置 | 迁移状态 |
|------------|------------|---------|
| `漏斗/` | `10_E盘代码归档/01_NURBS_Funnel_Trimesh/` | ✅ 已迁移 (2个py) |
| `螺锥/` | `10_E盘代码归档/02_NURBS_SpiralCone_OCC/` | ✅ 已迁移 (2个py) |
| `螺锥dxf双轨扫掠/` | `10_E盘代码归档/03_DXF_DualRail_Sweep/` | ✅ 核心3个已迁移 |
| `最简原始模版用于生成直锥螺旋管/` | `10_E盘代码归档/04_Straight_Cone_Spiral/` | ✅ 核心4个已迁移 |
| 根目录 `kudo horn羚羊角nurbs.py` | `10_E盘代码归档/00_根目录核心参照/` | ✅ 已迁移 |
| 根目录 250+ 早期实验 .py | (未迁移，按需查阅E盘原始位置) | ⏸️ 保留原位 |

---

## 六、与 PKS 主项目的集成路线图

### 6.1 已集成

- `egg_curve.py` — 蛋形核心参数化 ✅
- `anu_parameterization.py` — ANU 螺旋参数化 ✅
- `anu_geometry.py` — ANU 3D 几何生成 ✅
- `anu_milnor_framework.py` — Milnor 7 维框架 ✅
- `egg_3d_spiral.py` — 3D 螺旋可视化 + DXF/VTK 导出 ✅

### 6.2 待集成

- [ ] OCC NURBS → STEP 输出（方案 B）→ `02_mesh/`
- [ ] DXF 双轨扫掠 → 螺旋管 CFD 网格 → `02_mesh/`
- [ ] 直锥螺旋管质心约束 → 涡旋稳定性分析 → `03_simulation/`
- [ ] Schauberger 蛋参数化 → k_E 扫描 → `01_geometry/`
- [ ] Numba JIT 加速 → 合并到 PKS 计算管线

---

> 📅 创建日期：2026-05-28
>
> 📎 归档根目录：`D:\AAA我的文件\PKS_千禧难题_统一解\10_E盘代码归档\`
>
> 📎 E 盘原始位置：`E:\pythonProject\pythonProject\program\`
