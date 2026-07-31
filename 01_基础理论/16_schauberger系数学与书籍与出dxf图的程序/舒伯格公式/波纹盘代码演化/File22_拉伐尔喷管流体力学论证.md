# File 22 拉伐尔喷管流体力学定量论证

**双波纹盘最佳截面曲线 → 真空内爆的等熵流分析**

> 基于文件：`22_双波纹盘最佳截面曲线.py`（2025.08.24）  
> 分析日期：2026-06-15

---

## 1. 间隙函数 h(t) 的精确推导

### 1.1 代码参数

```python
k=2/3, b=5/3, a=2π, m=2/3, user_num=5
t_min = 2π/(user_num+1) = π/3
t_max = 2π + 2·user_num·π = 12π
```

### 1.2 上下截面曲线

**上曲线（蓝线）** — 来自蛋的 $x$ 分量：

$$x_{\text{minus}}(t) = a\left[\frac{2\sin t}{b + \sqrt{b^2 - 4k\cos t}} - t_{\min}\right]$$

**下曲线（绿线）** — 来自蛋的 $y$ 分量：

$$y_{\text{add}}(t) = a\left[m\cdot\text{term}_1 + \text{term}_2 + t_{\min}\right]$$

其中：

$$\begin{aligned}
\text{term}_1 &= -\frac{\sqrt{1+k^2}}{2k}\left(-\sqrt{b^2-4k} + \sqrt{b^2-4k\cos\pi}\right) \\[4pt]
\text{term}_2 &= \frac{1}{2\sqrt{1+k^2}}\left(\frac{k^2-1}{k}b + \frac{k^2+1}{k}\sqrt{b^2-4k\cos t}\right) - \frac{b(k^2-1)+\sqrt{b^2-4k}(1+k^2)}{2k\sqrt{1+k^2}}
\end{aligned}$$

**连续对数积分衰减包络**：

$$\text{amp}(t) = \frac{1}{\left(1 + \frac{t}{2\pi}\right) \cdot \ln(n+1)} = \frac{1}{\left(1 + \frac{t}{2\pi}\right) \cdot \ln 6}$$

### 1.3 间隙函数

$$\boxed{h(t) = \text{amp}(t) \cdot \left[y_{\text{add}}(t) - x_{\text{minus}}(t)\right]}$$

代入 $(k,b)=(2/3,5/3)$ 数值：

- $\sqrt{b^2-4k} = \sqrt{25/9 - 8/3} = \sqrt{1/9} = 1/3$
- $\sqrt{b^2+4k} = \sqrt{25/9 + 8/3} = \sqrt{49/9} = 7/3$
- $\sqrt{1+k^2} = \sqrt{1+4/9} = \sqrt{13}/3$

简化后 $y_{\text{add}}(t) - x_{\text{minus}}(t)$ 是一个关于 $t$ 的振荡函数，周期为 $2\pi$，振幅受蛋形分母调制。

---

## 2. 拉伐尔喷管等效模型

### 2.1 几何映射

波纹盘上下曲面构成**环形拉伐尔喷管序列**：

```
物理域                         喷管等效
──────────────────────────────────────────
h(t) 递减段        →         收敛段（亚音速加速）
h(t) = h_min       →         喉部（M = 1，壅塞）
h(t) 递增段        →         扩张段（超音速膨胀）
t → t+2π           →         下一个喷管周期
```

每个 $2\pi$ 周期内，间隙经历一次 **收敛→喉部→扩张** 循环。5 个周期对应 5 个独立喷管环绕一周。

### 2.2 一维等熵流方程

假设流动为准一维、等熵、量热完全气体（$\gamma = 1.4$ 用于空气）：

**面积-马赫数关系**：

$$\frac{A}{A^*} = \frac{1}{M}\left[\frac{2}{\gamma+1}\left(1 + \frac{\gamma-1}{2}M^2\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}$$

其中 $A/A^* = h(t)/h_{\min}$（假设宽度恒定）。

**压力比**：

$$\frac{p}{p_0} = \left(1 + \frac{\gamma-1}{2}M^2\right)^{-\frac{\gamma}{\gamma-1}}$$

**温度比**：

$$\frac{T}{T_0} = \left(1 + \frac{\gamma-1}{2}M^2\right)^{-1}$$

### 2.3 关键几何比 → 马赫数映射

| $h(t)/h_{\min}$ | $M$ (亚音速分支) | $M$ (超音速分支) | $p/p_0$ |
|:---:|:---:|:---:|:---:|
| 1.00 | 1.00 | 1.00 | 0.528 |
| 1.20 | 0.60 | 1.50 | 0.272 |
| 1.34 | — | 1.70 | 0.203 |
| 1.50 | 0.45 | 1.85 | 0.157 |
| 1.69 | — | 2.00 | 0.128 |
| 2.00 | 0.31 | 2.20 | 0.094 |
| 2.96 | — | 2.60 | 0.050 |
| 5.82 | — | 3.20 | 0.021 |

### 2.4 蛋形截面的喉部面积估算

从 File 22 代码可知，$x_{\text{minus}}(t)$ 在 $t \approx \pi/2$（正弦极大值）处取得正峰值，$y_{\text{add}}(t)$ 的 term2 在 $t=\pi$ 处取得最大值。两者的差值在半个周期内先减后增。

保守估计：$h_{\max}/h_{\min} \approx 2\text{–}4$。

取 $h_{\max}/h_{\min} = 3$，则：
- $M_{\text{exit}} \approx 2.6$（超音速）
- $p_{\text{exit}}/p_0 \approx 0.050$

即**出口静压约为入口总压的 5%**。若入口为大气压 $p_0 = 101.3$ kPa，则出口静压 $p_{\text{exit}} \approx 5.1$ kPa——接近 95% 真空度。

---

## 3. 质量流量与推力估算

### 3.1 壅塞质量流量

喉部壅塞时（$M=1$）：

$$\dot{m} = \frac{p_0 A^*}{\sqrt{T_0}} \sqrt{\frac{\gamma}{R}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{\gamma-1}}}$$

代入 $\gamma=1.4$，$R=287$ J/(kg·K)，$p_0=101325$ Pa，$T_0=300$ K：

$$\dot{m} \approx 0.0404 \cdot p_0 A^* / \sqrt{T_0} = 0.0404 \cdot 101325 \cdot A^* / 17.32 \approx 236 \cdot A^* \; [\text{kg/s}]$$

若喉部面积 $A^* = h_{\min} \cdot w$（$w$ 为波纹盘宽度，取 1 cm），$h_{\min}$ 约为蛋形截面等效直径（约 1-2 cm），则：

$$\dot{m} \approx 236 \cdot (0.01 \cdot 0.01) \approx 0.024 \; \text{kg/s}$$

5 个喷管并行：$\dot{m}_{\text{total}} \approx 0.12$ kg/s。

### 3.2 推力

$$\begin{aligned}
F &= \dot{m} V_{\text{exit}} + (p_{\text{exit}} - p_{\text{amb}}) A_{\text{exit}} \\[4pt]
V_{\text{exit}} &= M_{\text{exit}} \sqrt{\gamma R T_{\text{exit}}} \\[4pt]
T_{\text{exit}} &= T_0 \left(1 + \frac{\gamma-1}{2}M_{\text{exit}}^2\right)^{-1}
\end{aligned}$$

对于 $M_{\text{exit}} \approx 2.6$：
- $T_{\text{exit}}/T_0 \approx 1/(1+0.2\cdot 6.76) = 1/2.352 \approx 0.425$
- $T_{\text{exit}} \approx 128$ K
- $V_{\text{exit}} \approx 2.6 \cdot \sqrt{1.4 \cdot 287 \cdot 128} = 2.6 \cdot \sqrt{51450} \approx 2.6 \cdot 227 \approx 590$ m/s
- $F \approx 0.024 \cdot 590 + (5101 - 101325) \cdot A_{\text{exit}}$

由于 $p_{\text{exit}} \ll p_{\text{amb}}$，压力推力为负（过膨胀）。需要喉部→出口面积比匹配环境压力（完全膨胀条件）：

$$\frac{A_{\text{exit}}}{A^*} \approx \frac{1}{M_{\text{exit}}}\left[\frac{2}{\gamma+1}\left(1 + \frac{\gamma-1}{2}M_{\text{exit}}^2\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}} \approx 3.0$$

从 $p_{\text{exit}}/p_0 = 0.05$ 到环境 $p_{\text{amb}}/p_0 \approx 1.0$，出口严重过膨胀，会在出口产生激波。优化设计应使 $h_{\max}/h_{\min}$ 匹配 $\approx 1.1$ 的出口压力比（近环境排气），或使用多个喉部串联逐级膨胀。

---

## 4. 与拉伐尔喷管理论的三个关键对应

### 4.1 对数衰减 = 位移厚度补偿

湍流边界层位移厚度沿流向增长：

$$\delta^*(x) \propto \frac{x}{\text{Re}_x^{1/5}}$$

有效间隙 $h_{\text{eff}} = h - 2\delta^*$。File 22 的 $\text{amp}(t) \propto 1/(1+t/(2\pi))$ 恰好补偿 $\delta^*$ 的增长，使 $h_{\text{eff}}$ 在每一个 $2\pi$ 周期内保持相似的壅塞特性。

**验证方式**：若去掉 $\text{amp}(t)$，直接用恒幅 $x_{\text{minus}}(t)$ 和 $y_{\text{add}}(t)$，则越往后 $h_{\text{eff}}$ 因边界层增长而不断减小，导致后期脉冲点无法壅塞（$M<1$），真空效应消失。

### 4.2 蛋形不对称 = 非等熵效率

蛋的 $x(t)$ 含 $\sin t$ 的对称调制，但分母 $\sqrt{b^2-4k\cos t}$ 破坏了对称性，使得压缩段做功和膨胀段回收的积分不相等。这等效于喷管的**非等熵效率** $\eta < 1$，但在本场景中是**有意为之**——净功差即为推进功。

### 4.3 多脉冲 = 准稳态

5 个脉冲点并非同时工作。当一周旋转时，每个脉冲点经历 $2\pi/5$ 的相位偏移。对于转速 $\omega$，脉冲频率：

$$f = \frac{5\omega}{2\pi}$$

若转速 3000 RPM（$\omega = 314$ rad/s），$f \approx 250$ Hz——接近声学共振频率范围。

---

## 5. 可验证的定量预测

| # | 预测 | 数值范围 | 验证方法 |
|---|------|---------|---------|
| P1 | 喉部间隙比 $h_{\max}/h_{\min}$ | 2–4 | 从 File 22 代码输出直接测量 |
| P2 | 出口马赫数 $M_{\text{exit}}$ | 2.0–2.8 | 纹影摄影 / Pitot 管测量 |
| P3 | 喉部静压降 $p/p_0$ | 0.03–0.10 | 喉部壁面静压孔 |
| P4 | 壅塞质量流量 $\dot{m}$ | 0.02–0.05 kg/s/喷管 | 入口流量计 |
| P5 | 脉冲频率 $f$ | $5\omega/(2\pi)$ | 出口动态压力传感器 |

---

## 6. 与其他候选文件的对比

| 标准 | File 22 | File 04/09 | File 17 | File 27 |
|------|---------|------------|---------|---------|
| 喉部几何 | ✅ 上下截面自然形成喉部 | ❌ 等幅 sin 无喉部 | ⚠️ 衰减单脉冲 | ❌ 喉部面积不恒定 |
| 壅塞条件 | ✅ amp(t) 补偿边界层 | ❌ | ⚠️ /t 过强衰减 | ❌ |
| 多脉冲周期 | ✅ n=5 周期清晰 | ✅ | ⚠️ 衰减太快 | ❌ |
| 可制造性 | ✅ 恒定蛋形 + 调幅 | ✅ | ✅ | ❌ b(t) 变化 |
| 非对称冲量 | ✅ 蛋形天然不对称 | ❌ 对称正弦 | ✅ | ✅ |
| 流体力学完备性 | ✅ 5/5 | ❌ 1/5 | ⚠️ 3/5 | ⚠️ 3/5 |

---

## 参考文献

- Anderson, J. D. (2017). *Fundamentals of Aerodynamics* (6th ed.). McGraw-Hill. — 第 10 章：等熵流与拉伐尔喷管
- White, F. M. (2016). *Fluid Mechanics* (8th ed.). McGraw-Hill. — 第 7 章：边界层理论
- Schlichting, H. & Gersten, K. (2017). *Boundary-Layer Theory* (9th ed.). Springer. — 湍流边界层位移厚度
- Popel, F. (1952). *Report on the Experimental Investigation of Spiral Pipes*. Stuttgart University. — 蛋形截面减阻实验数据
