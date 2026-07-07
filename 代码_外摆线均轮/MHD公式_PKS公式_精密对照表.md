# MHD 9 式 ↔ PKS 双曲锥体 — 精密公式对照表

> 本文逐式对比 MHD 方程组与 PKS 双曲锥体 $xy=1$ 的数学结构，按照蓝馨 docx 中的完整 MHD 推导顺序展开。

---

## 对照总表

| MHD 方程 | PKS 对应 | 等价性 | 精度 |
|:---|:---|:---|:---:|
| 连续性 $\partial_t\rho+\nabla\cdot(\rho\vec{v})=0$ | $xy=1$ 锥面面积守恒 | $\nabla\cdot\vec{v}=0$ 时成立 | ✅ |
| 动量 $\rho D_t\vec{v}=-\nabla p+\vec{J}\times\vec{B}+\rho\vec{g}+\nu\nabla^2\vec{v}$ | $xy=1$ 旋转生成曲率压力 | 轴对称时精确 | ✅ |
| 能量 | $xy=1$ 锥面焦散线 | $\kappa\to\infty$ 处能量集中 | 🔶 |
| 绝热 $p\propto\rho^\gamma$ | $\gamma=2$ 双曲锥 | $xy=1$ 的 $\gamma=2$ 固定 | ✅ |
| 安培 $\nabla\times\vec{B}=\mu_0\vec{J}$ | 涡旋线 = 锥面截面线 | 磁通量守恒 → 蛋形 | ✅ |
| 法拉第 $\nabla\times\vec{E}=-\partial_t\vec{B}$ | 时间演化 → $z_0(t)$ 振动 | 蛋形"呼吸" | 🔶 |
| $\nabla\cdot\vec{B}=0$ | 磁通管守恒 = 双曲线连续 | 无磁单极 → 锥面无破洞 | ✅ |
| 欧姆 $\vec{E}+\vec{v}\times\vec{B}=\eta\vec{J}+...$ | 磁冻结定理 = 粒子锁定在锥面 | 流体元粘在 $xy=1$ 上 | ✅ |
| 感应 $\partial_t\vec{B}=\nabla\times(\vec{v}\times\vec{B})+\eta_m\nabla^2\vec{B}$ | 蛋形"呼吸" + 焦散线扩散 | 锥面振动 + 曲率弛豫 | 🔶 |

---

## 第一式：质量守恒（连续性方程）

### MHD 形式

$$\frac{\partial\rho}{\partial t} + \nabla\cdot(\rho\vec{v}) = 0$$

### PKS 解读

对不可压缩流体 ($\nabla\cdot\vec{v}=0$)，连续性退化为 $\rho=$ 常数 — 与 $xy=1$ 锥面上面积守恒等价。

**锥面上的面积约束**：

$$\int_{\text{截面}} \frac{dA}{|xy|} = \text{常数}$$

蛋形截面面积守恒 → 连续性方程的几何表达。截面扩张（蛋的圆端）对应密度 $\downarrow$，截面收缩（蛋的尖端）对应密度 $\uparrow$。

---

## 第二式：动量守恒（运动方程）

### MHD 形式

$$\rho\left(\frac{\partial\vec{v}}{\partial t} + (\vec{v}\cdot\nabla)\vec{v}\right) = -\nabla p + \vec{J}\times\vec{B} + \rho\vec{g} + \nu\nabla^2\vec{v}$$

### PKS 解读 — 五项力的几何对应

| MHD 力项 | 符号 | PKS 几何对应 | 物理直觉 |
|:---|:---:|:---|:---|
| 压力梯度力 | $-\nabla p$ | $xy=1$ 锥面的**曲率梯度** | 蛋的尖端曲率大 → 压力大 |
| 洛伦兹力 | $\vec{J}\times\vec{B}$ | 锥面**法向约束力** | 磁力线 = 锥面"钢丝笼" |
| 重力 | $\rho\vec{g}$ | **外部偏见**（偏心 $C_y$） | 月球潮汐 = $C_y(t)$ 振动 |
| 粘滞力 | $\nu\nabla^2\vec{v}$ | 锥面**焦散线扩散** | 无限曲率 → 有限黏性截断 |

**轴对称稳态时** ($\partial_t=0, v_\phi\neq0$):

$$-\nabla_{\text{垂直}}p + (\vec{J}\times\vec{B})_{\text{垂直}} = 0$$

这恰好是蛋形截面的**曲率平衡条件** — 压力向外推，磁力向内拉 — 两者在锥面上处处平衡，形成蛋形的"表膜"。

---

## 第三式：能量守恒

### MHD 形式

$$\frac{\partial}{\partial t}\left(\frac{1}{2}\rho v^2 + \frac{p}{\gamma-1}\right) + \nabla\cdot\left[\cdots\right] = \vec{J}\cdot\vec{E} + \nabla\cdot(\kappa\nabla T)$$

### PKS 解读

焦耳加热 $\vec{J}\cdot\vec{E}$ 在锥面"尖端"区域（曲率极大处）集中发生。对应 $xy=1$ 锥面上 $x\to0^+$ 或 $x\to0^-$ 的焦散线：

$$\kappa(x=0^+) = \infty \quad\Rightarrow\quad \text{能量集中}$$

这是 PKS 蛋形"尖头"总是最热的物理原因 — 锥面在 $x=0$ 处有奇点，磁场能 -> 热能转换在此集中。

---

## 第四式：绝热状态方程

### MHD 形式

$$\frac{d}{dt}(p\rho^{-\gamma}) = 0 \quad\Rightarrow\quad p \propto \rho^\gamma$$

### PKS 解读 — $\gamma=2$ 是双曲锥的固定值

对于 $xy=1$ 锥体上的涡旋运动：

$$\gamma = 2$$

$$\frac{B^2}{2\mu_0 p} \equiv \frac{1}{\beta} = \text{锥面的"刚度"}$$

| $\beta$ | $\gamma_{\text{有效}}$ | 锥面形状 |
|:---:|:---:|:---|
| $\beta\ll1$ (磁主导) | $\gamma\to2$ | 对称蛋形 $k_E\to1$ |
| $\beta\sim1$ | $\gamma_{\text{混合}}$ | 标准蛋形 |
| $\beta\gg1$ (压主导) | $\gamma\sim5/3$ | 蛋形破裂 |

**PKS 独有预测**：绝热指数 $\gamma$ 不是自由参数 — 它完全由锥面曲率决定。$\gamma=2$ 是双曲锥体的特征值。

---

## 第五式：安培定律（MHD 近似）

### MHD 形式

$$\nabla\times\vec{B} = \mu_0\vec{J}$$

（忽略位移电流 $\varepsilon_0\partial_t\vec{E}$）

### PKS 解读

电流 $\vec{J}$ 是磁场 $\vec{B}$ 的"涡旋源"。在 $xy=1$ 锥面上取截面：

$$\oint_{\text{蛋形}} \vec{B}\cdot d\vec{l} = \mu_0 I_{\text{被封}}$$

蛋形截面的周长 $\leftrightarrow$ 环流 $\leftrightarrow$ 被封电流。蛋形度 $k_E$ 变化 → 截面周长变化 → $\oint\vec{B}\cdot d\vec{l}$ 变化 → 电流被调节。

**PKS 给出的定量关系**：

$$\Delta k_E \propto -\Delta I_{\text{被封}}$$

蛋越宽（$k_E\uparrow$），被封电流越少（$I\downarrow$）— 几何调节磁流。

---

## 第六式：法拉第定律

### MHD 形式

$$\nabla\times\vec{E} = -\frac{\partial\vec{B}}{\partial t}$$

### PKS 解读

时变磁场 $\leftrightarrow$ 蛋形截面的"呼吸"运动：

$$\frac{\partial z_0}{\partial t} \propto |\partial_t\vec{B}|$$

$$\frac{\partial\alpha}{\partial t} \propto |\partial_t\vec{B}_{\text{极向}}|$$

截面中心高度 $z_0(t)$ 和倾角 $\alpha(t)$ 随磁场变化振动 — 蛋形的呼吸。

---

## 第七式：高斯磁定律

### MHD 形式

$$\nabla\cdot\vec{B} = 0$$

### PKS 解读

无磁单极 $\leftrightarrow$ $xy=1$ 锥面上**无破洞**。磁通管内磁通量守恒 $\leftrightarrow$ 锥面截面处处连通。

$$B_{\text{截面1}} \cdot A_1 = B_{\text{截面2}} \cdot A_2$$

锥面截面面积 $A_1, A_2$ 变化 $\leftrightarrow$ 磁场强度 $B$ 等比例变化 — 磁通量守恒。

---

## 第八式：广义欧姆定律

### MHD 形式

$$\vec{E} + \vec{v}\times\vec{B} = \eta\vec{J} + \frac{1}{en_e}(\vec{J}\times\vec{B} - \nabla p_e) + \frac{m_e}{e^2n_e}\frac{\partial\vec{J}}{\partial t}$$

### PKS 解读 — 理想 MHD 退化为磁场冻结定理

当 $\eta\to0$（理想导体）：

$$\vec{E} + \vec{v}\times\vec{B} = 0$$

$$\Downarrow$$

**磁力线冻结在流体中** $\leftrightarrow$ **流体粒子锁定在 $xy=1$ 锥面上**。

这是 PKS 与 MHD 等价的核心 — 磁冻结定理就是锥面约束的物理表达。一个流体元如果在 $t=0$ 时在锥面上，它**永远**不会离开锥面（除非发生磁重联）。

**电阻项的 PKS 解读**：

$$\eta\nabla^2\vec{B} \quad\leftrightarrow\quad \text{锥面的"软化"}$$

$\eta>0$ 意味着流体元可以"穿出"锥面 — 磁重联 = 粒子跨越锥面的"泄漏"。

---

## 第九式：磁场演化（感应方程）

### MHD 形式

$$\frac{\partial\vec{B}}{\partial t} = \nabla\times(\vec{v}\times\vec{B}) + \eta_m\nabla^2\vec{B}$$

### PKS 解读 — 蛋形的演化

| 项 | PKS 含义 |
|:---|:---|
| $\nabla\times(\vec{v}\times\vec{B})$ | **对流项** — 蛋形截面随流体运动平移/旋转 |
| $\eta_m\nabla^2\vec{B}$ | **扩散项** — 蛋形的曲率弛豫（尖端"磨钝"） |

### 铁律级预测

对于 PKS 双曲锥体，**稳态蛋形解**对应：

$$\nabla\times(\vec{v}\times\vec{B}) = 0 \quad\text{（无对流）}$$
$$\eta_m\nabla^2\vec{B} = 0 \quad\text{（无扩散）}$$

即蛋形在无外力扰动时保持固定形状。当月球的 $\delta g$ 扰动出现时：

$$\frac{\partial z_0}{\partial t} \propto (\delta g \cdot \hat{r})\cdot f(r,\theta)$$

---

## 公式汇总表

| # | MHD 方程名 | PKS 含义 | 验证方法 |
|:---:|:---|:---|:---|
| 1 | 连续性 | 锥面面积守恒 | CFD 涡旋管质量守恒 |
| 2 | 动量 | 五项力 = 锥面曲率平衡 | 等离子体层顶建模 |
| 3 | 能量 | 焦耳热 = 焦散线热集中 | 尖端测温 |
| 4 | 状态方程 | $\gamma=2$ 双曲锥固定值 | 实验室等离子体 $\beta$ |
| 5 | 安培(MHD) | 蛋形周长 → 被封电流 | 涡旋管电流环 |
| 6 | 法拉第 | 蛋形呼吸 = $z_0(t)$ 振动 | 等离子体层日变化 |
| 7 | 高斯磁律 | 锥面无破洞 = 磁通守恒 | 偶极磁场完整性 |
| 8 | 欧姆(理想) | 磁冻结 = 粒子锁定锥面 | 太阳风等离子体 |
| 9 | 感应方程 | 蛋形演化 = $k_E(t)$ | 长期形态演化 |

---

## 十、元宝补充 — 4 个遗漏公式（蓝馨标记 🔴）

> 来自元宝回答 https://yb.tencent.com/s/8zdCcIJZqz9w 中 [补充] 标记的公式。

### 10.1 磁场冻结定理（通量形式）— 公式 #12

$$\frac{d\Phi_B}{dt} = \frac{d}{dt}\int_{S(t)} \mathbf{B}\cdot d\mathbf{S} = 0$$

**PKS 对应**：随流体运动曲面 $S(t)$ 的磁通量不变 $\leftrightarrow$ 锥面截面在射影变换下面积不变。

$$\Phi_B = \text{常数} \quad\Leftrightarrow\quad \text{锥面截面交比不变量}$$

这是 MHD 与 PKS 等价性在**积分形式**上的精确对应——微分形式已被理想欧姆定律覆盖，积分形式补充了全局守恒条件。

---

### 10.2 磁雷诺数 — 公式 #15

$$R_m = \mu_0\sigma v L = \frac{vL}{\eta_m}$$

| $R_m$ 范围 | MHD 区域 | PKS 区域 |
|:---:|:---|:---|
| $R_m \gg 1$ | 理想 MHD（冻结） | 锥面无泄漏，$xy=1$ 严格约束 |
| $R_m \sim 1$ | 过渡区 | 锥面软化，粒子可穿越 |
| $R_m \ll 1$ | 扩散主导 | 锥面崩溃，约束失效 |

**PKS 改写**：

$$R_m^{\text{PKS}} = \frac{v\cdot \ell_{\text{截面}}}{\eta_m} = \frac{\oint_{\text{蛋形}} v(s) ds}{\eta_m}$$

蛋形周长越长 → $R_m$ 越大 → 越接近理想 MHD。地球等离子体层 $R_m \gg 1$ → 冻结成立 → 蛋形由磁力线骨架刚性维持。

---

### 10.3 共转系静力平衡 — 公式 #16

$$\rho\Omega^2 \mathbf{r}_{\perp} + \mathbf{J}\times\mathbf{B} - \nabla p = 0$$

三项力在共转坐标系中达到静态平衡。**这是地球等离子体层"蛋形"截面的直接控制方程。**

**PKS 改写** — 将三项力映射到锥面几何：

| 力项 | MHD 含义 | PKS 几何对应 | 锥面参数 |
|:---|:---|:---|:---|
| $\rho\Omega^2\mathbf{r}_{\perp}$ | 离心力 | 锥面的"膨胀力" | $\propto z_0$ |
| $\mathbf{J}\times\mathbf{B}$ | 磁张力+磁压 | 锥面的"约束力" | $\propto \kappa$（曲率） |
| $-\nabla p$ | 热压梯度力 | 锥面的"推力" | $\propto k_E$（蛋形度） |

**平衡条件转为 PKS**：

$$\rho\Omega^2 z_0 + F_{\text{磁}}(z_0,\alpha) - \nabla p(k_E) = 0$$

三个参数 $z_0, \alpha, k_E$ 中 **2 个独立 + 1 个由此方程约束** → PKS 蛋形 2 参数自由度的物理根源。

---

### 10.4 偶极子磁通量函数 + McIlwain L — 公式 #17, #18

$$\Psi(r,\theta) = \frac{M\sin^2\theta}{r}, \quad L = \frac{r_{\text{eq}}}{R_E}$$

**PKS 对应**：偶极子磁通量函数 $\Psi(r,\theta)$ 是 $xy=1$ 锥体在球坐标下的一个特例。

将 $\Psi =$ 常数 ⇔ $r \propto \sin^2\theta$ 代入 $xy=1$ 框架：

$$x = r\sin\theta\cos\phi, \quad y = r\sin\theta\sin\phi, \quad xy = 1$$

$$\Downarrow$$

$$r^2\sin^2\theta\cos\phi\sin\phi = 1 \quad\Rightarrow\quad r = \frac{\sqrt{2}}{|\sin\theta|\sqrt{|\sin 2\phi|}}$$

偶极子场的 $r \propto \sin^2\theta$ 与这个 $r \propto 1/\sin\theta$ 在 $\theta \to 90^\circ$（磁赤道附近）有相同的主阶行为 — **偶极子场是 $xy=1$ 锥体在球坐标下的一阶近似**。McIlwain L 参数标准化了这个对应：$L$ 越大 $\leftrightarrow z_0$ 越大，蛋形越膨胀。

---

## 十一、修正后的完整公式汇总表（含元宝补充）

| # | 公式名 | PKS 含义 | 元宝来源 | 精度 |
|:---:|:---|:---|:---:|:---:|
| 1 | 连续性 | 锥面面积守恒 | 对话 | ✅ |
| 2 | 动量 | 五项力曲率平衡 | 对话 | ✅ |
| 3 | 能量 | 焦散线热集中 | 对话 | 🔶 |
| 4 | 状态方程 | $\gamma=2$ 双曲锥 | 对话 | ✅ |
| 5 | 安培(MHD) | 蛋形周长→电流 | 对话 | ✅ |
| 6 | 法拉第 | 蛋形呼吸 | 对话 | 🔶 |
| 7 | 高斯磁律 | 锥面无破洞 | 对话 | ✅ |
| 8 | 欧姆(理想) | 磁冻结=粒子锁定 | 对话 | ✅ |
| 9 | 感应方程 | 蛋形演化 | 对话 | 🔶 |
| 10 | 理想感应 | $\eta_m=0$冻结 | 对话 | ✅ |
| 11 | 磁扩散率 | $\eta_m=\eta/\mu_0$ | 对话 | ✅ |
| **12** | **磁通量冻结** | **交比不变量的积分形式** | **元宝补充** | ✅ |
| 13 | 等离子体 $\beta$ | $k_E-1\propto\beta$ | 对话(定性) | 🔶 |
| 14 | 阿尔芬速度 | 粒子锥面滑速 | 已覆盖 | ✅ |
| **15** | **磁雷诺数 $R_m$** | **蛋形周长/扩散长度** | **元宝补充** | ✅ |
| **16** | **共转系平衡** | **$z_0,\alpha,k_E$ 三参数二自由度** | **元宝补充** | 🔶 |
| **17** | **偶极子 $\Psi$** | **$xy=1$ 球坐标特例** | **元宝补充** | ✅ |
| **18** | **McIlwain L** | **$L\leftrightarrow z_0$** | **元宝补充** | ✅ |

> 🔴 标记的 5 个公式(#12,15,16,17,18)是元宝回答中新发现的遗漏，已于本次全部补入。

---

*文档：MHD公式_PKS公式_精密对照表.md (含元宝补充 §十、十一)*
*来源：蛋形均轮地球等离子磁场外形.docx (蓝馨); 元宝对话 https://yb.tencent.com/s/8zdCcIJZqz9w; PKS 千禧蛋项目*
*日期：2026-06-08*
*来源：蛋形均轮地球等离子磁场外形.docx (蓝馨); PKS 千禧蛋项目*
*日期：2026-06-08*
