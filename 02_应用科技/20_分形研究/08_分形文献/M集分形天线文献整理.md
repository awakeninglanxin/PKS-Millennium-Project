# M 集分形天线与频率映射 — 相关文献整理

> 2026-06-25 | 蓝馨健康工作室

---

## 一、M 集分形天线（IEEE）

### 1.1 3D Mandelbrot 宽带天线 (2024)

| 项目 | 内容 |
|------|------|
| 标题 | A Novel Broadband Antenna Based on Three-Dimensional Mandelbrot Fractal Geometry |
| 作者 | Huang, Boag et al. |
| 来源 | IEEE ISAP 2024 |
| DOI | 10.1109/ISAP62502.2024.10666216 |
| 要点 | 首次将 M 集 3D 几何结构直接用作天线物理形状，利用"芽状"自相似特征延长电长度，实现宽带响应 |

### 1.2 3D Mandelbrot 多频天线 (2026)

| 项目 | 内容 |
|------|------|
| 标题 | A Novel Multiband Fractal Antenna Based on Three-Dimensional Mandelbrot |
| 来源 | IEEE OJAP 2026 |
| DOI | 10.1109/OJAP.2026.11396943 |
| 要点 | 系统研究迭代阶数和幂指数对天线多频性能的影响，不同阶数的"泡"结构对应不同谐振频段 |

### 1.3 Mandelbrot 偶极子 UWB 天线 (2023)

| 项目 | 内容 |
|------|------|
| 标题 | A Multiband Dipole Antenna Based on Mandelbrot Fractal Geometry |
| 来源 | IEEE 2023 |
| DOI | 10.1109/ACES-China60289.2023.10221480 |
| 要点 | M 集分形贴片偶极子天线，UWB 应用，仿真验证多频谐振特性 |

### 1.4 Mandelbrot 微型化 UWB 天线 (2024)

| 项目 | 内容 |
|------|------|
| 标题 | A Miniaturized Ultra-wideband Antenna Based on Mandelbrot Fractal |
| 来源 | IEEE 2024 |
| DOI | 10.1109/ACES-China62502.2024.10618743 |
| 要点 | 利用 M 集分形边界实现微型化和超宽带 |

### 1.5 Mandelbrot 边界贴片天线 (IET 2017)

| 项目 | 内容 |
|------|------|
| 标题 | Mandelbrot fractal boundary microstrip antenna |
| 来源 | IET Microwaves, Antennas & Propagation |
| DOI | 10.1049/iet-map.2017.0649 |
| 要点 | 对比 M 集分形边界 vs 矩形贴片天线，证明分形边界显著提升带宽 |

---

## 二、基础理论支撑

### 2.1 斐波那契链 → M 集分形 (2019)

| 项目 | 内容 |
|------|------|
| 标题 | The Unexpected Fractal Signatures in Fibonacci Chains |
| 作者 | Fang Fang, Raymond Aschheim, Klee Irwin (Quantum Gravity Research) |
| 来源 | Fractal and Fractional, 2019, 3, 49 |
| 要点 | ✅ 已获取。斐波那契链傅里叶空间呈 M 集心形，缩放因子=1/√φ，奇偶迭代镜像翻转 |
| 与本项目关系 | 提供"离散序列 → 傅里叶变换 → M 集结构"的数学桥梁 |

### 2.2 分形电动力学概论 (Springer)

| 项目 | 内容 |
|------|------|
| 标题 | Fractal Electrodynamics: From Super Antennas to Superlattices |
| 作者 | Jaggard et al. |
| 来源 | Springer, 2002 |
| 要点 | 系统总结分形几何在天线/阵列/孔径中的应用，自相似 → 多频响应的基本原理 |

### 2.3 M 集泡周期与 Fibonacci 数 (标准教材)

| 要点 |
|------|
| M 集实轴上泡的周期序列遵循 Farey 加法 |
| 周期泡直径与 Feigenbaum 常数 δ=4.669 相关 |
| 泡之间天线辐条数 = 周期数 |
| 泡的直径近似比例于 1/F_n²（F_n 为 Fibonacci 数） |

---

## 三、与本项目的关系总结

| 论文 | 给我们什么 | 用法 |
|------|------|------|
| 3D M 集天线 (2024/2026) | M 集"芽泡"结构 → 对应不同频率谐振 | 验证"泡直径 → 频率"的物理可实现性 |
| M 集偶极子 UWB | 分形边界提升多频带宽 | 解释 NLS 宽频扫描覆盖 1.4-2.1 范围 |
| M 集贴片天线 (IET) | 分形边界 vs 矩形对比 | 证明分形结构的频率优势非偶然 |
| Fib→M 集 (2019) | 缩放因子 1/√φ | 层级间泡直径比例的理论基础 |
| Fractal Electrodynamics | 自相似 → 多频响应的通论 | 为原创提供公认的理论框架 |

---

## 四、待下载

| 优先级 | 论文 | DOI |
|:--:|------|------|
| P0 | 3D M 集宽带天线 (2024) | 10.1109/ISAP62502.2024.10666216 |
| P0 | 3D M 集多频天线 (2026) | 10.1109/OJAP.2026.11396943 |
| P1 | M 集偶极子 UWB (2023) | 10.1109/ACES-China60289.2023.10221480 |
| P1 | M 集贴片天线 (IET 2017) | 10.1049/iet-map.2017.0649 |
| P2 | Fractal Electrodynamics | Springer ISBN |

---

蓝馨健康工作室 | 2026-06-25 | 分形天线文献整理 v1.0
