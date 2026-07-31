# Popel Report 1952 — 螺旋管摩擦实验完整数据表

> **来源**: `SchaubergerEnergyEvolution能源革命英文.pdf` pp. 232-249
> **机构**: 斯图加特工业大学卫生研究所 (Institute of Hygiene, Stuttgart University of Technology)
> **主任**: Prof. Dr.-Ing. habil. Franz Popel
> **日期**: 1952年2月9日 - 3月15日
> **数据转写日期**: 2026-06-15

---

## 一、8 根试验管规格

> 📖 **原书出处**: TABLE 1 位于 PDF **p.248**，标题 "Output of straight and spiral pipes"。管型原文描述来自 pp. 244-246。

| 管号 | 类型 | 材质 | 截面形状 | 原书英文描述（逐字还原） |
|:---:|:---|:---|:---|:---|
| 1 | 试验台自身 | 橡胶 19mm ID | 圆形（半弯） | "Test Stand without pipes but with conical inlet and outlet of the test pipe and rubber hose of 19 mm ID" |
| 2 | **螺旋铜管** | 铜 | 圆形 | "Spiral Helicoid Copper Pipe roughly 1.45 m long with a 5.05 cm² cross-section of the below form" |
| 3 | 直铜管 | 铜 | 圆形 | "Straight Copper Pipe, 2.54 cm ID, 1.45 m long" |
| 4 | 直玻璃管 | 玻璃 | 圆形 | "Straight Glass Pipe, 2.54 cm ID, 1.45 m long" |
| 5 | 直锥形铜管 | 铜 | 锥形（渐变圆形） | "Smooth Conical Copper Pipe, 1.45 m long" |
| 6 | **锥形螺旋铜管** | 铜 | 🔴 **蛋形咬一口**（非对称） | "Conical Spiral Helicoid Copper Pipe 1.45 m long" |
| 7 | 直锥形螺旋管（大） | 铜 | 🔴 **蛋形咬一口**（非对称，大截面） | "Straight Conical Helicoid Copper Pipe of larger cross-section, 1.45 m long" |
| 8 | 直锥形螺旋管（小） | 铜 | 🔴 **蛋形咬一口**（非对称，小截面） | "Straight Conical Helicoid Copper Pipe of smaller cross-section, 1.45 m long" |

> 🔑 所有管统一长度 **1.45 m**（除试验台橡胶管外）。等截面圆形管（No.2/3/4）：内径 2.54 cm。

> 🔴 **蛋形 vs 蛋咬一口**：普通蛋形（=双曲锥 $xy=1$ 斜切面）只有钝端+尖端的平滑不对称。**蛋咬一口**（Apple 公司 logo 形状）在圆形轮廓上额外有一个凹缺（concave notch）——这是更高级的不对称。No.6/7/8 的截面是蛋咬一口，不是普通蛋形。圆形截面管（No.1-5）$n$ 最低只能到 1.67；只有蛋咬一口截面管才能突破到 1.57 和 1.51。

---

## 二、摩擦指数实测结果

> 📖 **原书出处**: **p.244**（PDF页码）。Popel 用双对数图测量了每条管的 $q$-$h$ 关系。标准水力学公式为 $h = c \cdot q^2$（湍流），此时水头损失随流量的平方增长。Popel 测量了指数对标准值 2 的偏离。以下数值是 Popel 原文直接给出的指数值——不作任何加工，不引入我自己的变量名。

| 管号 | 类型 | 截面 | 指数（Popel 原文） |
|:---:|:---|:---|:---:|
| 3 | 直铜管 | 圆形 | **2.00** |
| 5 | 直锥形铜管 | 渐变圆形 | **2.00** |
| 1 | 试验台（橡胶U弯） | 圆形 | **1.67** |
| 2 | 螺旋铜管 | 圆形 | **1.67** |
| 4 | 直玻璃管 | 圆形 | **1.67** |
| 7 | 直锥形螺旋管（大） | 🔴 **蛋咬一口**（大） | **1.67** |
| 6 | 锥形螺旋管 | 🔴 **蛋咬一口** | **1.57** |
| **8** | **直锥形螺旋管（小）** | 🔴 **蛋咬一口**（小） | **1.51** |

> 原文（p.244）：*"...the smooth, straight copper pipes ... best follow the hydraulic postulate h = c × q². ... the exponent would be reduced to 1.67. ... decreases to 1.57 ... attains the lowest value of 1.51."*

> **截面决定论**：圆形截面（No.1-5）无论直/弯/锥/螺旋，指数最低 1.67。只有 **蛋咬一口** 截面（Apple logo 形状：圆形轮廓 + 一个凹缺/notch）的管才能突破到 1.57 和 1.51。

> **物理解读**：$n$ 是 $q$ 的指数（不是 $q$ 的系数）。$h = c \cdot q^n$，$q = (h/c)^{1/n}$。$n$ 从 2.0 降到 1.51 意味着 $q \propto h^{0.5} \to h^{0.662}$——**高水头时 8 号管多流 32%**。阈值反转 h=10.5cm：低水头螺旋阻力 > 收益，高水头 $n$ 差异被放大。

---

## 三、阈值反转点 — 管No.2 vs 管No.3

> 📖 **原书出处**: **p.246**（PDF页码）。"up to a difference in height of 10.5 cm Test Pipe 3 delivers more than the spiral helicoid pipe (No. 2). From here onwards, however, the performance of the spiral helicoid pipe is always superior."

| 水头差 h (cm) | 直铜管(No.3) 流量 | 螺旋铜管(No.2) 流量 | 胜者 |
|:---|:---:|:---:|:---|
| < 10.5 | 更大 | 更小 | 直管 |
| **= 10.5** | 相等 | 相等 | **临界点** |
| > 10.5 | 更小 | **更大** | 🔴 螺旋管 |

> 对应流速 ~0.17 m/s (计算值 1.6-1.68 dm/s)

---

## 四、摩擦损失对比 — Table 2

> 📖 **原书出处**: TABLE 2 位于 **p.249**（PDF页码），标题："Output and Friction Losses of Straight and Spiral Test Pipes of Glass and Copper"。原始数据表为图像格式嵌入，以下为数值转写。

管道长度: 1.45 m | 等截面管内径: **2.54 cm** (No.3/4) | 螺旋管截面积: **5.05 cm²** (No.2) | 流量单位: L/s | 水头损失单位: cm

| 流量 q (L/s) | 直铜管(No.3) dh | 螺旋铜管(No.2) dh | 差值 |
|:---|:---:|:---:|:---:|
| 0.10 | ~0.8 | ~1.0 | +25% (螺旋更大) |
| 0.15 | ~1.8 | ~1.8 | 0% (临界) |
| 0.20 | ~3.0 | ~2.8 | -7% (螺旋更小) |
| 0.25 | ~4.5 | ~3.8 | **-16%** 🔴 |
| 0.30 | ~6.5 | ~5.0 | **-23%** 🔴🔴 |

> 低流量区螺旋管摩擦损失**更大**（附加的螺旋阻力不可忽略）。高流量区螺旋管摩擦损失**显著更小**——螺旋几何的收益在高速区体现。

---

## 五、零摩擦点 🔴

> 📖 **原书出处**: **p.253**（PDF页码）

Popel 测量到螺旋管在特定流量下摩擦损失 **趋近于零**：

| 流量 q (L/s) | 流速 v (m/s) | 备注 |
|:---|:---:|:---|
| **0.14** | **0.28** | 零摩擦第一点 |
| **0.19** | **0.39** | 零摩擦第二点 |
| **0.38** | ~0.76 | 零摩擦第三点 |

> 原文: "The amount of friction in the spiral helicoid pipe approaches zero when q = 0.14 l/s or v = 0.28 m/s and when q = 0.19 l/s or v = 0.39 m/s and when q = 0.38 l/s"

---

## 六、铜 vs 玻璃 — 材质吸力对比

> 📖 **原书出处**: **p.254, 256**（PDF页码）

| 管材 | 吸力容量 A (cm·g/s, q=300 cm³/s) | 相对倍率 |
|:---|:---:|:---:|
| 玻璃管 (No.4) | 850 | 1.0× |
| 直铜管 (No.3) | 1,860 | 2.2× |
| **螺旋铜管 (No.2)** | **3,450** | **4.1× (玻璃) / 1.9× (直铜)** |

> 原文 (p.256): "the suction capacity of the spiral helicoid pipe reaches its maximum value... A = 310 × 11.1 = 3450 cm g/s. It is therefore 4.05 times as large as that of the glass pipe and 1.85 times larger than that of the straight copper pipe."

> (p.254): "copper is more favourable to the formation of the in-winding flow process than glass" — 铜催化向心旋流。

---

## 七、实验基本参数

| 参数 | 值 |
|:---|:---|
| 测试管道内径 | **2.54 cm** (等截面管 No.2/3/4) |
| 螺旋管截面积 (No.2) | **5.05 cm²** |
| 测试管道长度 | 1.45 m |
| 流量范围 | 0.1 - 0.3 L/s |
| 流速范围 (计算) | 0.08 - 0.24 m/s |
| 测量容器 | 15 L |
| 计时方法 | 秒表 |
| 测压方式 | 锥形出口管 + 差压接头 |
| 连接软管 | 橡胶 19 mm 内径 |
| 供水方式 | 恒定水位容器 (levelling vessel) |

---

## 八、关键结论 (Popel 原文)

| # | 原文引用 | 出处 | PKS 含义 |
|:---:|:---|:---:|:---|
| 1 | "the exponent of the output q is smaller than 2" | **p.244** | β_eff < 2 — 螺旋管偏离湍流平方律 |
| 2 | "the frictional losses usually occurring in straight pipes could be reduced to zero in the case of the helicoid pipe" | **p.253** | 摩擦可归零 — 对应 gcd=1 磁静音的流体版 |
| 3 | "centripetally acting forces greater than the centrifugal force" | **p.240** (丝线实验) | 向心力 > 离心力 — 等价于 $xy=1$ 锥面约束 |
| 4 | "the change from the unfavourable to the favourable effects ... already took place within the area of measurement" | **p.246** | 阈值反转 — h=10.5cm ~ SEG 临界转速 |
| 5 | "copper is more favourable to the formation of the in-winding flow process than glass" | **p.254** | 铜催化向心旋流 — SEG 铜合金层选材依据 |
| 6 | "suction capacity ... 4.05 times as large as that of the glass pipe" | **p.256** | 螺旋管吸力 4× 直管 — 对应蛋形截面的自吸效应 |

---

*文档: Popel_Report_1952_实验数据表.md | 来源: Schauberger Energy Evolution (Callum Coats 译) | PDF页码: §一-§二 p.244 | §三 p.246 | TABLE 1 p.248 | TABLE 2 p.249 | §五 p.253 | §六 pp.254-256 | 签字 p.260 | 日期: 2026-06-15 (v2.0 精确页码修正)*
