# 分形大盘预警 · 02 Mandelbrot 分形结构聚类与算法详解

> 来源：元宝分享链接全盘阅读（第 1-8 轮：Mandelbrot 本体研究部分）
> 整理：Senior Developer ｜ 日期：2026-08-03

## 一、问题设定：给 Mandelbrot 分形结构做聚类

对 Mandelbrot 图形放大后产生的**不同涡旋/泡芽结构**做聚类分析：每多一种封闭结构就多加一个 dict 字典，统计每放大一个级别会产生多少种不同类型结构。

## 二、4 条形态签名（特征提取核心）

| 签名 | 含义 | 金融映射 |
|------|------|----------|
| **radial（径向轮廓）** | 从锚点向外扫描的迭代数剖面 | → 收益率序列形态 |
| **angular（角向轮廓）** | 360° 绕锚点扫一圈的迭代数剖面 | → 多角度/多因子剖面 |
| **boundary_density（边界密度）** | 结构边界的复杂度密度 | → 波动率聚集程度 |
| **period_orbit（周期轨道）** | 周期点的轨道特征 | → regime 状态 |

## 三、算法链路（Mandelbrot 版）

```
Farey 锚点生成（头尖/泡中心坐标）
   ↓
8 个缩放深度 L0~L7 × 每级 5 窗口 = 40 个样本视口
   ↓
每个视口抽 4 条 1D 签名
   ↓
DTW 距离 + k-medoids（silhouette 自动选 k=3）
   ↓
复合码 → level_stats dict（每级新增结构类型统计）
   ↓
L0(全局3种) → L5(200x, 新类型首次出现) → L7(3333x, 更深螺旋)
   = 8 种结构类型，L5/L7 是"结构多样性爆发"层级（对应倍周期分岔点）
```

## 四、Farey 序列锚点（数学核心，可抄的公式）

### 4.1 头尖（attaching point）坐标公式

```
c(t) = e^(2πi·p/q)/2 − e^(4πi·p/q)/4

主盘 p/q=1/2 → c = −1
north bud 1/3 → c ≈ −0.125 ± 0.6495i
```

### 4.2 泡中心近似

```
解 f_c^p(0)=0 的周期点方程，或沿法向退 1/(4q²)
```

### 4.3 360° 扫描 → FFT 频谱解读（⭐ 最精妙的洞察）

```
对锚点 360° 扫描平滑迭代数 → rfft
  幅谱基频 = q（Farey 分母）
  相位    = 颈方向角 = 2πp/q（Farey 分子）
→ 一次 FFT 同时读出 p 和 q！
→ 聚类结果可锚回 Douady-Hubbard ground truth
```

**3 个坑**：
1. R 半径选 0.8×芽苞半径估算
2. spiral 涡旋 FFT 会糊（chirp 状）→ 切去 spiral 段只用 DTW
3. 深 zoom >10¹⁴ 要 float64 或扰动理论

## 五、GPU + FFT 加速方案

| 环节 | 加速比 | 方法 |
|------|--------|------|
| 渲染 | 50-100x | CuPy ElementwiseKernel + smooth iteration count |
| 角向抽点 | 10-20x | 锚点坐标+半径预存 device，kernel 内 polar_fetch |
| FFT | 5-10x | cuFFT batch |

**避坑**：别每帧 readback——锚点坐标+半径预存 GPU，一次性搬回。

## 六、首创性判断（诚实结论）

| 对比对象 | 差异 |
|----------|------|
| GitHub 现有 repo（AntoniosBarotsis/limdingwen/gcollombet/ishiikurisu） | 全是渲染+zoom，**无一是对芽苞/涡旋聚类+层级统计** |
| 学术传统（Douady-Hubbard 1980s 内部地址+周期分类） | ①按周期硬分 vs 按形态无监督聚 ②不关心每级新增种类 ③不混聚涡旋+芽苞 |
| **结论** | 应用创新（novel application）成立，**别 claim 算法创新（novel algorithm）** |

**可抄的零件**：tslearn 的 `KShape` 和 `TimeSeriesKMeans(distance="dtw")`；rtavenar/blog/dtw.html
**要自己写（novelty）**：Farey 锚点生成器、360°角向采样→cuFFT batch、(p_fft,q_fft)反推、层级多尺度 dict、交叉验证

## 七、多尺度分析的正确做法

- **全样本（L0~L7 所有视口）Agglomerative 一次性聚** → 切不同高度 = 不同 granularity 的簇树（3簇→6簇→8簇）
- 能回答"结构怎么分叉的"（L0 簇A → L5 裂成 A1+A2），单尺度给不了

## 八、性能评估（多尺度增益）

- 监督分类基线（ChatPaper《Learning with Mandelbrot and Julia》）：Mandelbrot 全集 KNN≈95%，**边界附近传统阈值法≈17%**（最难处恰是芽苞附着区）
- 计算效率：瓶颈只在渲染（2000×2000×500iter×40视口 ≈ 单机 10-30 min），聚类+FFT 在 40 样本规模几乎免费
- **独有坑**：R 必须与 Farey q 联动（R≈0.8/(4q²)）；spiral 要分亚集报指标；用 Farey (p,q) 当 GT 算 ARI/Purity 自验

## 九、与最新 AI 的关联（对话第 12 轮）

- **Liquid 液态神经网络 vs Mandelbrot**：非直系血缘，是 **DS（非线性动力系统）祖辈同源**
  - Mandelbrot = 离散二次 DS（z²+c）的参数空间分形（数学展示柜）
  - Liquid = 连续高阶 ODE DS（线虫解剖约束，时序架构工程）
  - 3 个共同祖先：非线性 DS 家族、多尺度时间常数↔多尺度 zoom、Farey 锚点↔线虫回路硬接线稀疏性
- 关联路径：A（Liquid 参数空间画 M 集同位体）、B1（Liquid 替换时序编码器——**已实践**）、C（5 条思维映射到 ODE 参数空间）

## 十、电影《The Bank》的真实算法对应

- 片名更正：不是 The Banker (2020)，是**澳洲 2001《The Bank》**（数学家 Jim Doyle，软件 B.T.S.E.，基于 Mandelbrot 分形几何）
- 现实算法：Hurst R/S 分析 + 分形市场假说 FMH（Peters 1991）+ MMAR（Calvet-Fisher-Mandelbrot 1997）+ 相空间重构/Lyapunov + MF-DFA
- **LTCM 1998 教训**：模型外有"罕见事件+流动性蒸发"，分形对厚尾刻画好，但对 0→1 外生冲击一样跪
