# PKS 蛋形曲线公式摘录 — 来自 Walter Schauberger 原著

> 来源：元宝对话提取自《Die Ei-Kurve als Schnitt des Hyperbolischen Kegels》
> 摘录日期：2026-07-02

---

## 公式 1：Tongesetz（音律法则）

$$
l \cdot f = 1
$$

**出处**：Pythagoras 单弦琴 → Walter Schauberger 推广为宇宙基本法则
**含义**：弦长(l) × 频率(f) = 常数。这是 `x·y=1` 的物理原型。
**股票对应**：`price · turnover_rate ≈ const` — 价格与换手率在趋势段满足反比。

---

## 公式 2：等轴双曲线

$$
y = \frac{1}{x} \quad \text{即} \quad x \cdot y = 1
$$

**推导**：将 Tongesetz 的 l→x, f→y
**股票对应**：`momentum · time = const` — 动量与时间成反比，涨得快的时间短。

---

## 公式 3：蛋形曲线显式形式（极坐标）

$$
\boxed{ r(\varphi) = \frac{1}{2\cos\varphi \cdot \sin\alpha} \left[ z_0 \pm \sqrt{ z_0^2 - \frac{4\cos\varphi \cdot \sin\alpha}{\sqrt{\sin^2\varphi + \cos^2\varphi \cdot \cos^2\alpha}} } \right] }
$$

**参数**：
- z₀：切割平面与 z 轴交点高度
- α：切割平面与水平面夹角
- φ：极角
- ±：正号=锥管部分，负号=扁平山脉部分

**判别式**：根号内 `z₀² - 4cosφ·sinα/√(sin²φ+cos²φ·cos²α) ≥ 0` 决定蛋形存在性。

**股票对应**：之前用的 R² 公式是这个的简化投影。极坐标形式更适合计算蛋形的"偏离度"指标。

---

## 公式 4：两点形式（Zwei-Punkte-Form）★ 关键

$$
\boxed{ z_0 = \frac{z_1^2 + z_2^2}{z_1 + z_2} }
$$

$$
\boxed{ \tan\alpha = -\frac{z_1 z_2 (z_2 - z_1)}{z_1 + z_2} }
$$

**推导**：给定蛋形的两个主顶点 z₁(尖端) 和 z₂(钝端)，利用它们在双曲线 y=1/z 上的位置，反推切割参数。

**z₁·z₂ > 0 的物理含义**：z₁ 和 z₂ 必然同号（都在 y=1/x 的正半支），这意味着：
- 两顶点不可能跨越原点 → 蛋形总有明确的方向性
- |z₂| > |z₁|（钝端离原点更远）

**股票对应**：这是最关键的公式——**可以直接从 K 线数据中计算 z₀ 和 α**：
- z₁ = 60日内最低价/MA60（归一化到双曲线坐标系）
- z₂ = 60日内最高价/MA60
- 代入公式直接得到 z₀ 和 tan(α)

之前手动构造的 `compute_adaptive_alpha()` 和 `compute_adaptive_z0()` 可以用这两个公式替代——它们来自 Schauberger 原著的精确推导，不是近似。

---

## 公式 5：蛋体积公式

$$
\boxed{ V = \frac{\pi}{\cos\alpha} \left[ \frac{z_1 + z_2}{(z_1 z_0 - \tan\alpha)(z_2 z_0 + \tan\alpha)} - \frac{1}{3} \left( \frac{1}{z_1^3} + \frac{1}{z_2^3} \right) \right] }
$$

**股票对应**：蛋形体积 V 可以类比为"价格波动包络的总体积"——大 V = 大波动范围，小 V = 窄幅整理。

---

## 公式 6：判别式统一形式

从显式公式根号内项，蛋形存在的必要条件是：

$$
z_0^2 \geq \frac{4\cos\varphi \cdot \sin\alpha}{\sqrt{\sin^2\varphi + \cos^2\varphi \cdot \cos^2\alpha}} \quad \forall \varphi \in [0, 2\pi]
$$

最严格的约束发生在 φ=0 时：

$$
z_0^2 \geq \frac{4\sin\alpha}{\cos\alpha} = 4\tan\alpha
$$

即 **`z₀ > 2√(tan(α))`** — 这正是之前代码中实现的判别式。来自原著的 φ=0 边界条件。

---

## 公式间推导关系

```
Tongesetz (l·f=1)
    ↓ l→x, f→y
等轴双曲线 (y=1/x)
    ↓ 绕y轴旋转
双曲锥 (3D)
    ↓ 斜切面(z₀, α)
蛋形显式 r(φ) ──→ 蛋形参数式
    ↓ 代入两顶点
两点形式 z₀, tan(α) ← z₁, z₂
    ↓ 旋转体积分
蛋体积 V
```

---

## 之前代码需要替换的地方

| 旧实现 | 新实现（来自原著） |
|--------|-------------------|
| `compute_adaptive_alpha(er, slope_sign)` — 手动映射 | 直接用 `tan(α) = -z₁z₂(z₂-z₁)/(z₁+z₂)` 从高点/低点精确计算 |
| `compute_adaptive_z0(nvol)` — 基于波动率估算 | 直接用 `z₀ = (z₁²+z₂²)/(z₁+z₂)` 从高点/低点精确计算 |
| `enforce_egg_existence(alpha, z0)` — 强制抬高 z₀ | 原著中 z₁,z₂ 自然满足约束，不需要强制 |

**关键差异**：旧代码从波动率反推 z₀，原著从几何顶点正推——正推更精确。
