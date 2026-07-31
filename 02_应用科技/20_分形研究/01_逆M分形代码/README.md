# Inverse Mandelbrot Application

> 逆Mandelbrot集全栈技术体系 | 22种UF着色算法 + 9种Möbius参数变换 + DESCRIPTOR分形压缩 (50000:1)

[![Stars](https://img.shields.io/github/stars/awakeninglanxin/inverse-Mandelbrot-application?style=social)](https://github.com/awakeninglanxin/inverse-Mandelbrot-application)

---

## 一句话介绍

**将Mandelbrot集通过Möbius反演(c→1/c)翻转为"水滴分形"，实现22种Ultra Fractal标准着色算法、9种参数空间变换、以及100字节参数描述5MB图像的Kolmogorov极限压缩。从分形到AI芯片，c·1/c=1一条线打通。**

---

## 核心技术

### 1. 正逆M集数学对偶性

$$M_{\text{inv}} = \{c \in \mathbb{C} : 1/c \in M\}$$

通过 `c·1/c=1` 极化原理（ℤ₂群对合），正M心形 → 逆M水滴，ext/interior着色区域内外翻转。所有UF算法公式不变，仅着色区域互换。

**关键数值**：
- 心形尖点 c=0.25 → 水滴尖端 c=4
- 心形瓶颈 c=−0.75 → 水滴根部 c=−4/3
- |c|=1 单位圆 = 自对偶边界（正逆重合）

### 2. 22种UF标准着色算法

| 类别 | 算法 (UF#) | 核心公式 |
|------|:--|------|
| 基础 | 二分棋盘格(1) · 连续势能(2) · 外部射线(3) · 基础着色(13) · 分解着色(14) | 角度⊕势函数XOR / ν=n−log₂log₂|z| |
| 边界 | **DEM距离估计(4)** | d=ln|z|²·|z|/|dz| Mu-Ency光晕 |
| 轨道 | 轨道陷阱(5) · 直接轨道陷阱(15) · 三角不等式(11,20) | min|zₙ−trap| / Σ|Δz|/|z| |
| 纹理 | 拓扑瓦片(6) · **对偶三角网(8)** · 高斯整数(12) | K色镶嵌(UF6) / 双区域XOR+渐变(UF8★) / 复平面格点 |
| 特效 | 光照(9) · 浮雕(10) · 渐变(16) · 指数平滑(17) | Sobel梯度+3D法线 / HSV彩虹 |
| 艺术 | 多陷阱(18) · 万花筒(19) · **轨迹树枝(7)** | 心形+圆+十字 / sin×cos干涉 / 轨道逆映射外延(UF7★) |
| 混合 | **蓝白阴阳格(21)** · 图像映射(22) | XOR棋盘+DEM金边(★) / 2D纹理查色 |

> ★ = 支持水滴外部纹理/辐射/扩散效果（见 [公式对照文档](UF_水滴外部纹理_辐射_扩散_公式对照.md)）

> 完整22种算法 → 参见 `逆M树状代码/` 目录（每算法独立文件夹含main.py+算法说明.md）

### 3. 9种Möbius参数变换

对标Ultra Fractal全部参数平面 + Max Million "20种逆变换"视频：

| # | 变换 | 公式 | 几何效果 |
|:--:|------|------|------|
| 1 | 标准M | c = p | 心形 |
| 2 | 标准反演 | c = 1/p | 心形→水滴(teardrop) |
| 3 | 抛物线 | c = 0.25 + 1/p | 心形→抛物线外部 (Albert Chern) |
| 4 | 反天线 | c = −2 + 1/p | 天线尖端放大反演 |
| 5 | **Feigenbaum** | c = cf − 1/p | 7个等大双曲分支 (p=2⁰~2⁶) |
| 6 | **指数映射** | c = cf + e^p | 倍周期级联拉平 |
| 7-9 | **Logistic族** | mz(1−z), m∈{p, 1/p, 1+1/p} | λ平面全谱 |

> cf = −1.401155 (Feigenbaum/Myrberg点)

### 4. DESCRIPTOR分形压缩

```json
{"family":"c_type","projection":{"type":"inversion","k":0},
 "viewport":[-1.833,4.5,-2.124,2.124],"max_iter":200,
 "algorithm":"binary_decomposition","colormap":"plasma"}
```

| 存储方式 | 典型大小 | 压缩比 | 还原质量 |
|------|:--:|:--:|:--:|
| PNG (3600×5912) | ~3-8MB | baseline | 无损 |
| VVC Intra | ~200-400KB | ~15:1 | 高(PSNR>40dB) |
| JPEG AI (神经压缩) | ~150-300KB | ~20:1 | 感知高(但分形OOD翻车) |
| **DESCRIPTOR** | **~100-500B** | **3000-50,000:1** | **bit-exact无损** |

> DESCRIPTOR的压缩比不是"算法更快了"——而是根本不需要存像素。分形图像是公式的确定论输出，存参数即可。

### 5. PKS极化原理 × AI芯片映射

```
c·1/c=1 (ℤ₂群) → Farey分数 → M=15 Chiplet拓扑
                 → Sharkovsky序 → 无死锁MoE调度器
                 → Douglas-Peucker拐点 → 注意力头剪枝
```

- **M=15 Chiplet**：period 2-25全部24个M值中四指标夺冠的唯一最优解
- **TurboQuant↔Möbius同构**：PolarQuant旋转保内积 = c→1/c保角性
- **MLA↔DEM潜投影**：K/V→低维 = 轨道{n步}→1维边界距离d(c,M)

> 详见 `ai芯片与正逆M延伸的算法/AI压缩算法关联/` 三份分析文档

---

## 目录结构

```
逆M分形代码/
├── 分形mandelbrot.py                标准M集 (Numba JIT)
├── 分形逆M_c倒数法_z平方迭代.py     逆M基础版 (c=1/p)
├── 分形逆mandelbrot细腻.py          mpmath高精度版
├── 分形逆mandelbrot细腻_v2.py       平滑逃逸+直方图均衡
├── 分形逆mandelbrot细腻gpu优化+.py  11段组合色盘+视图缓存
├── 分形z负一次幂迭代_*4色/8色.py    逆M z倒数法 (1/z+c, 多初值)
├── 分形mandelbrot整合.py            正逆M双面板实时对比
├── 逆mandelbrot边缘曲线*.py         牛顿法边界细化+Y轴极值
│
│  🆕 5种Möbius变换 (对标Max Million视频)
├── 分形逆M_k025_抛物线.py           c=0.25+1/p
├── 分形逆M_kneg2_反天线.py          c=−2+1/p
├── 分形逆M_Feigenbaum_Myrberg.py    c=cf−1/p (MI=500, R=400)
├── 分形逆M_指数映射_Feigenbaum.py   c=cf+e^p
├── 分形逆M_logistic族.py            mz(1−z), 改MODE=3种模式
│
├── README.md                        本文件
├── DESCRIPTOR_格式标准.md           算法参数化JSON schema
├── 项目亮点_朋友圈发布.md           社交媒体文案(3版)
├── 原理_*.md (7篇)                  数学原理完整文档
└── UF22_图像映射/                   main.py + 算法说明.md
```

---

## 快速开始

```bash
# 标准Mandelbrot集
python 分形mandelbrot.py

# 逆M水滴 (标准反演, 高清版)
python 分形逆mandelbrot细腻_v2.py

# 心形→抛物线 (k=0.25)
python 分形逆M_k025_抛物线.py

# Feigenbaum点反演 (7等大双曲分支)
python 分形逆M_Feigenbaum_Myrberg.py

# 指数映射 (倍周期级联拉平)
python 分形逆M_指数映射_Feigenbaum.py

# Logistic λ平面 (改MODE切换3种模式)
python 分形逆M_logistic族.py

# 图像映射 (2D纹理查色)
cd UF22_图像映射 && python main.py
```

**依赖**: `numpy, matplotlib, numba, mpmath, scipy`

---

## 技术深度

| 层次 | 内容 |
|------|------|
| 数学 | PKS极化原理 · Möbius变换ℤ₂群 · Hausdorff维数=2 (Shishikura 1994) · Farey树×Fibonacci · Feigenbaum δ≈4.669 · Brockmoeller π定理(2025) |
| 算法 | Ultra Fractal Standard.ucl · Mu-Ency DEM/M · adammaj1 Alternate Parameter Planes · Orbit Trap · DEM/M · TIA · Binary Decomposition |
| 工程 | Numba JIT/parallel · 平滑逃逸ν=n−log₂log₂|z| · 自适应mpmath精度 · Sobel边界检测 · 2%-98%百分位归一化 |
| 独创 | c·1/c=1极化原理统一框架 · DESCRIPTOR极限压缩 · M=15 Chiplet最优拓扑 · 分形×AI压缩(JPEG AI/KV Cache)交叉映射 · 宝箧印塔5层几何抽象栈 |

---

## 关联项目

- [adammaj1/Mandelbrot-Sets-Alternate-Parameter-Planes](https://github.com/adammaj1/Mandelbrot-Sets-Alternate-Parameter-Planes) — C源码+Max Million视频技术背景
- [David E. Joyce — Alternate Parameter Planes](https://mathcs.clarku.edu/~djoyce/julia/altplane.html) — Möbius变换学术来源
- [Nikola Ubavić — Julia and Mandelbrot Set](https://ubavic.rs/work/julia_and_mandelbrot_set/) — 1/c变换数学描述
- [Alaqad et al. (2021) — On the inversion of the Mandelbrot set](https://doi.org/10.3390/fractalfract5030073) — j-average M集
- JPEG AI (IEEE TCSVT 2025) — 首个学习型图像编码标准
- TurboQuant (ICLR 2026) — KV Cache 3-bit在线量化

---

## 子项目: AI芯片与逆M延伸

👉 **[ai芯片与逆M延伸/](./ai芯片与逆M延伸/)** — 逆M数学在芯片设计中的应用

| 亮点 | 说明 |
|------|------|
| Farey-Hybrid 调度器 | 比EDA标准CPM快**38.7%**, 灾难恢复快**55.8%** |
| 8算法×3场景×500轮 | InternalAddr / FareyTree / Sharkovsky 全家族对比 |
| OpenROAD 集成 | SDC 插件, 可嵌入任何自主EDA工具链 |
| 冷邮件就绪 | 华为海思 / 普林斯顿 / Verkor / DeepSeek |
| 论文提纲 | DAC 2027, 含完整数学保证和实验数据 |

---

> `c·1/c=1` — 从小学算术到复动力系统，从分形到芯片，从混沌到秩序。如果这个项目对你有启发，请给一个 ⭐ Star！
