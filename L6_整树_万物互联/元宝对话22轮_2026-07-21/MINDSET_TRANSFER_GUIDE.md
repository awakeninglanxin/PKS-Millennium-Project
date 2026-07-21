# 🧠 Mandelbrot 分形聚类思维 → K 线分析 · 迁移指南

> 核心理念：**不要"把 K 线塞进 M 集迭代"**，而是把"我们在 M 集里找同类型结构的 5 条思维操作"抽出来，迁到金融序列上。载体从 `z²+c` 换成 `return` 的尾部+长记忆+cascade，5 条动作一字不改。

## 一、5 条思维映射表（M 集 ↔ 金融）

| # | M 集版（你已经会了） | K 线同位体（本文落地） | 为什么是同构 |
|---|---|---|---|
| 1 | Farey 头尖/泡心**几何地标** | **结构地标**：顶底分型 + 成交量突增 + 布林松脱日 | 拒绝均匀盲扫，用领域知识钉"有理点" |
| 2 | 2D 芽苞 → 4 条 1D 签名（径向/角向/密度/周期） | **4 通道签名**：MF-DFA h(q) / tail-α / wavelet / vol-MF | 单条信息不够，多投影互补 |
| 3 | 360° FFT 读 p/q（**变换域读机制**） | **MF-DFA 谱 + Hurst + Hill-α**（读"生成机制"） | 时域长得像 ≠ 同机制，频/标度域才分得开 |
| 4 | 多尺度 L0→L7 **Agglomerative 切树** | **1d / 1h / 1min 三粒度** Ward 切树 | 单一切片会低估/高估簇数，必须层级 |
| 5 | Farey (p,q) **ground truth 校验** | **行业标签 + Hurst-regime** 算 ARI/NMI | 无监督 type=1,2,3 没语义，要靠先验锚定 |

## 二、消融实验结论（已实跑，64 票 / 8 行业 / 800 日）

| 配置 | 含义 | NMI vs 行业 | ARI vs Hurst-regime |
|---|---|---|---|
| **A 纯收益率** | 基线（DTW/K-Shape 直接吃 return） | **0.031** ❌ | 0.001 |
| **B +h(q)+α** | 思维 2+3：MF-DFA 谱 + Lévy 尾 | **0.379** ✅ | 0.319 |
| C +wavelet+H | 思维 2+3 加强 | 0.367 | 0.359 |
| D +anchor | 思维 1：事件地标特征 | 0.367 | 0.359 |
| **E 三粒度融合** | 思维 4：1d/1h/1min 拼签名 | 0.310 | **0.367** ✅ |

**关键发现**：
- 纯收益率聚类 ≈ 随机（NMI=0.03），证明"DTW/K-Shape 直接吃 K 线"这条路在行业分类上基本无效
- **加上 h(q)+α 两条分形签名，NMI 立刻翻 12 倍到 0.38**——这就是"M 集思维"的贡献，收益全在"变换域读机制"
- 多粒度融合对 **regime 对齐**最有用（ARI=0.37），对应 Mandelbrot 棉花线的"长记忆态切换"

## 三、落地代码清单

| 文件 | 作用 |
|---|---|
| `financial_fractal_clustering_v2.py` | 主流程：合成面板 → 锚点 → 4 签名 → 三粒度 Ward → ARI 校验 → 跨粒度分裂表 |
| `mindset_ablation.py` | 5 档消融：A→E 逐条加思维，量化每条贡献 |
| 产物 `finance_output_v2/` | performance.png / hq_spectra.png / cluster_industry.png / pca_signature.png / split_chart.png / fractal_finance_report.json |
| 产物 `ablation.png` | 5 档 NMI/ARI 柱状对比（这张图是灵魂） |

## 四、怎么接到真实数据

```python
# 替换 generate_panel() 即可，签名提取/聚类全链路不用动
import akshare as ak  # 或 westock API
def load_real_panel(symbols, start, end):
    panel = {}
    for s in symbols:
        df = ak.stock_zh_a_hist(symbol=s, start_date=start, end_date=end)
        ret = np.diff(np.log(df['收盘'].values))  # 对数收益率
        vol = df['成交量'].values[1:]
        panel[s] = {'return': ret, 'volume': vol}
    return panel
```

真实数据注意三点：
1. **停牌/停牌补 0 会污染 MF-DFA** → 用交易日对齐后丢 0 收益日
2. **复权价**必须前复权，否则分红除权制造假"跳点"被当成 tail
3. **行业标签**用申万一级（akshare `stock_board_industry_name_em`）

## 五、接 Mandelbrot 正统金融线（棉花→Lévy→MMAR）

本文 B 档的 `tail-α`（Hill 估计）就是 Mandelbrot 1963 棉花原味。要继续深挖：
- 把 **MMAR (multifractal model of asset returns)** 的"时间乘子 cascades"当**生成模型**，
  合成数据从"AR(1)+厚尾"升级成"真正多重分形 cascades"，再跑聚类，看 ARI 能不能再上台阶
- 用 **DA-MFDFA (2025, Physica A)** 把成交量当 exogenous 第二不对称源，
  对应 M 集"多通道 channel clustering (DUET 那篇)"
- **regime 切换**用 HMM 在 return 上切牛/熊/震，再在每个 regime 内算多重分形谱，
  对应 M 集"不同缩放深度 L 的簇分裂"

## 六、一张图记住迁移路径

```
M 集思维空间                    金融同位体空间
─────────────                    ─────────────────
Farey 头尖 c(t)   ──→         分型/突增/松脱 地标
360° 角向采样     ──→         MF-DFA q 谱扫描
FFT 幅谱 → (p,q)  ──→         Hurst + Hill-α → regime
径向/角向/密度/周期 ──→       h(q)/α/wavelet/vol-h(q)
L0→L7 多尺度切树  ──→         1d/1h/1min Ward 切高度
Farey GT 校验      ──→         行业 + HMM-regime ARI
```

> **思维操作不变，只是载体从复平面 `z²+c` 换成了价格 `return` 的尾部+长记忆+cascade。**
> 这就是"间接应用"的正确打开方式——比"K 线画进 M 集"高级两个量级。
