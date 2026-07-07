# Don Smith / Moray 天线系统 — 频率平方定律与冷电

> 来源：PJKbook Ch1 (p.43-45), Ch6 (p.581-583)
> 关联：TGFT Poynting 流、SEG 超导态、Aquino χ

---

## 一、Don Smith 的频率平方定律

PJKbook 记载了 Don Smith 的核心公式：

> "The output power is proportional to the square of the voltage and the square of the frequency."
>
> $$P_{\text{out}} \propto V^2 \cdot f^2$$

**含义**：电压翻倍 + 频率翻倍 → 输出功率 **16 倍**（$2^2 \times 2^2 = 16$）。

### 1.1 与标准物理的对比

| | 标准电路 | Don Smith |
|:---|:---|:---|
| $P_{\text{out}}$ vs $V$ | $P \propto V^2/R$（阻性负载） | $P \propto V^2$（一致） |
| $P_{\text{out}}$ vs $f$ | **无频率依赖**（阻性） | $P \propto f^2$（**异常！**） |
| 能量来源 | 驱动电源 | **环境背景场** |

### 1.2 物理机制推测

频率平方项暗示**电容性耦合**（$I = C \cdot dV/dt \propto f$）→ 功率 $\propto I^2 \propto f^2$。但 Don 的设备输出远超输入，意味着 $f^2$ 项来自**环境能量的电容耦合**——天线/线圈从背景电磁场中"整流"出可用功率。

### 1.3 与 TGFT 的对接

TGFT 泵浦项：

$$\xi \frac{\partial |\mathbf{E}|^2}{\partial t}$$

当 $\mathbf{E} = E_0 \sin(2\pi f t)$ 时：

$$\frac{\partial |\mathbf{E}|^2}{\partial t} = 2\pi f \cdot E_0^2 \sin(4\pi f t)$$

**时间平均** $\propto f \cdot E_0^2 = f \cdot (V/d)^2 \propto f \cdot V^2$。

所以 TGFT 泵浦项本质上是 **$V^2 \cdot f$** 的关系——Don Smith 的实验声称是 $V^2 \cdot f^2$，其中多出的一个 $f$ 可能来自设备的谐振 Q 值放大。

---

## 二、Moray 天线系统（1920s~1930s）

### 2.1 核心事实

| 参数 | 数据 |
|:---|:---|
| 天线 | 57 英尺（~17m），离地 8 英尺（~2.4m） |
| 输出 | **千瓦级** |
| 地点 | 任意位置，不需要靠近输电线 |
| 后果 | 被枪击、实验室被闯入、被迫停止演示 |

### 2.2 Moray 阀（Moray Valve）

PJKbook Ch6 描述了 Moray 的"阀"——一种**冷阴极检波/放大管**：

| 组件 | 描述 |
|:---|:---|
| 外壳 | 金属杯，兼作电极 |
| 内部 | 4 个 pellet（铋 ×2 + ? ×2），外两个熔接在金属壳上 |
| 接触 | 金属臂压在 pellet 上（猫须式接触） |
| 功能 | 既能**整流**也能**放大** |

### 2.3 物理机制推测

Moray 天线 + 阀系统的工作链：

```
天线（57ft, 离地8ft）
    → 捕捉地球-电离层之间的 ELF/Schumann 共振能
    → Moray 阀（冷阴极管）放大 + 整流
    → 输出 千瓦级 DC
```

**地球上全球性的电磁共振（Schumann 共振）基频 = 7.83 Hz**，与泰格坦导航的 Dzi'izi 地球基频一致。Moray 的天线本质上是一个**巨型 Schumann 共振接收器**。

---

## 三、Wimshurst 起电机 + Tesla 变压器

PJKbook Ch6 也描述了 Herman Plauson 的专利方法：

```
Wimshurst 起电机（超高电压、极低电流）
    ↓
Tesla 式降压变压器（降低电压、提升电流）
    ↓
可用工频功率
```

这本质上是 **阻抗匹配**——高阻抗的静电能源（Wimshurst）通过变压器匹配到低阻抗负载。与 Tesla 的"放大发射机"原理一脉相承。

### 3.1 与 Don Smith 的共同点

| | Don Smith | Wimshurst + Tesla |
|:---|:---|:---|
| 一次能源 | 高频 Tesla 线圈 | 静电感应 |
| 降压方式 | 电容/线圈谐振 | Tesla 变压器 |
| 频率角色 | $P \propto f^2$ | 脉冲放电频率 |

---

## 四、关系网：从 Moray 到 SEG 的完整链路

```
Moray 天线
  → 被动捕捉环境 ELF（7.83 Hz Schumann 共振）
  → 冷阴极阀放大
  → 千瓦级输出
        │
        │ 同一物理: 从环境背景场取能（被动接收）
        ↓
Don Smith
  → 主动激励 Tesla 线圈（高频）
  → 频率平方放大
  → 捕获环境电磁能
        │
        │ 同一物理: 频率 = 能量放大杠杆
        ↓
TGFT 泵浦项 ξ∂|E|²/∂t
  → 时变电场 = 从环境以太泵浦能量
        │
        │ 同一物理: 旋转 + 交变磁场 = Poynting 流发散
        ↓
SEG 三层环
  → 滚柱旋转 (12/22/32) → Bv 磁场交变
  → TGFT 三源项同时激活
  → 超导态 → 反重力
```

---

## 五、冷电（Cold Electricity）的统一解释

Moray、Tesla、Don Smith 的共同特征是输出"冷电"——**高电压、低电流、不产生焦耳热**的电力。

| 冷电特征 | 标准电 | 物理解释 |
|:---|:---|:---|
| 不加热导线 | 加热 | 电流以**位移电流**（非传导电流）为主 |
| 可点亮灯泡 | 点亮 | 灯泡负载利用的是电场而非电流 |
| 人体可接触 | 危险 | 皮肤深度 < 趋肤深度 |

**对应 PKS**：冷电 ≈ SEG 超导态的电磁等价——**W_in ≈ 0（无焦耳损耗）** 的外在表现。冷电不是"不同种类的电"，是**同一电流在零电阻环境中的行为**。

---

## 六、总结：天线/高压系统的 PKS 位置

| PJK 装置 | 物理原理 | PKS 方程覆盖 | COP 证据 |
|:---|:---|:---|:---|
| Moray 天线 | Schumann 共振接收 | TGFT η∇²\|B\|²（地球背景场梯度） | 千瓦级/零输入 |
| Don Smith | 频率平方放大 | TGFT ξ∂\|E\|²/∂t | P ∝ V²f² |
| Wimshurst+Transformer | 静电阻抗匹配 | 经典电磁学 | 低 |
| Tesla 放大发射机 | 谐振升压 | 全 Maxwell 方程 | 未完全实测 |

> **关键洞察**：Don Smith 的频率平方定律 + Moray 的千瓦零输入 = TGFT 泵浦项 ξ∂\|E\|²/∂t 的宏观实验证据。频率不是"传输速度"——它是**从环境中抽取能量的杠杆**。

---

> **关联文件**:
> - [../PJK_十装置完整映射.md](../PJK_十装置完整映射.md)
> - [../../../25_keely/06_TGFT湍动引力场理论详解.md](../../../25_keely/06_TGFT湍动引力场理论详解.md)
> - [../../../24_searl_SEG/编者个人领悟/昴宿星科技体系_星际导航与引力控制.md](../../../24_searl_SEG/编者个人领悟/昴宿星科技体系_星际导航与引力控制.md)
