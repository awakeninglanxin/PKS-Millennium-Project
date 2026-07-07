# PJKbook 科技关系网 — 全类别交叉索引

> 基于 PJKbook 2663 页 14 章的完整全局关系网
> 核心原则：所有自由能源装置都是同一物理原理在不同工程域的实现

---

## 一、全类别分类矩阵

PJKbook 中 ~200 种装置可收敛为 **6 大物理原理**：

| # | 物理原理 | PKS 对应方程 | PJK 装置示例 | COP 量级 |
|:---:|:---|:---|:---|:---:|
| **A** | 磁饱和 → 楞次失效 | 周治平 COP = H_X/H_S | Adams, Bedini, Flynn, Newman | 1.5~5× |
| **B** | 频率谐振 → 环境能量泵浦 | TGFT ξ∂\|E\|²/∂t | Don Smith, Kapanadze, Tesla | 5~500× |
| **C** | 被动环境梯度捕捉 | TGFT η∇²\|B\|² | Moray, Coler, Sweet VTA | 无限×（零输入） |
| **D** | 辐射诱导 → 核态改变 | Aquino χ = f(U) | Colman 管, Imris 光学 | 10~100× |
| **E** | 电解效率突破 | 周治平（化学域） | Shigeta, Boyce, Meyer | 10~12× Faraday |
| **F** | 机械梯度利用 | 经典热力学/力学 | 重力轮, Cahill 热泵 | 1× (COP=1) |

---

## 二、装置 × 装置 关系矩阵

### 2.1 强关联（同物理原理）

```
Adams ↔ Bedini ↔ Flynn ↔ Newman
  └─ 磁芯在饱和/非饱和间切换 → 楞次定律选择性失效

Don Smith ↔ Kapanadze ↔ Tesla
  └─ 高频谐振 → 频率平方放大

Moray ↔ Coler ↔ Sweet VTA
  └─ 被动永磁/天线 → 背景场能量整流

Shigeta ↔ Boyce ↔ Meyer
  └─ 电解 Faraday 极限突破
```

### 2.2 交叉关联（不同原理但共享底层）

```
Bedini SSG ────→ Boyce 脉冲电解
  │                    │
  │  同一物理：        │  同一物理：
  │  OFF阶段回收       │  OFF阶段回收
  │  场崩解能量        │  场崩解能量
  │                    │
  └────────┬───────────┘
           │
    周治平 COP = H_X/H_S
    (ON阶段输入 → OFF阶段捕获)
           │
    ┌──────┴──────┐
    ↓             ↓
  Aquino χ    TGFT ∇Φ_T
  (为何能回收)  (回收的能量从哪来)
```

### 2.3 跨尺度关联

```
纳米尺度:  Keely 40 定律 → 频率改变化学键
微观尺度:  Colman 管 → 频率改变核态
介观尺度:  Imris 光学 → 等离子体 COP>9
宏观尺度:  SEG → 旋转磁铁反重力
行星尺度:  Moray 天线 → Schumann 共振提取
```

---

## 三、"四层漏斗"统一模型

所有 PJK 装置都可以塞入这个四层漏斗（从具体到抽象）：

```
Layer 4 (具体装置):
  Adams, Bedini, Flynn, Don Smith, Kapanadze, Moray,
  Coler, Sweet, Colman, Imris, Shigeta, Boyce, Meyer...
        │
        │ 分类
        ↓
Layer 3 (物理机制):
  磁饱和失控 / 频率泵浦 / 背景场整流 / 辐射诱导 / 电解突破
        │
        │ 统一
        ↓
Layer 2 (PKS 方程):
  COP = H_X/H_S  |  χ = f(U)  |  ∇²Φ_T = κ∇·⟨E×B⟩ + ...
        │
        │ 进一步统一
        ↓
Layer 1 (宇宙原理):
  "局部物理常数可以被修改 → 环境能量可以被提取"
```

---

## 四、每条 PKS 方程覆盖的 PJK 装置（含新类别）

### 周治平 COP = H_X/H_S
| 装置 | 域 | H_S 等效 | COP |
|:---|:---|:---|:---:|
| Adams 电机 | 电磁 | 磁芯饱和场 | ~2~3× |
| Bedini SSG | 电磁 | 铁芯饱和 | ~1.2~2× |
| Boyce 电解 | 电化学 | 法拉第效率上限 | 12× |
| Shigeta 电解 | 电化学 | 法拉第效率上限 | 10× |
| Meyer 水燃料 | 电化学+电磁 | 水分子解离能 | 声称极高 |

### Aquino χ = f(U)
| 装置 | U 来源 | χ 效果 | 证据 |
|:---|:---|:---|:---|
| Colman 管 | 高频辐射能 | 核态改变 | 千瓦级/零燃料 |
| Imris 光学 | 等离子体能 | 气体电离态改变 | COP>9 (专利) |
| Moray 阀 | RF 电磁能 | 冷阴极放大 | 千瓦/57ft 天线 |
| Sweet VTA | 永磁体预磁化能 | 自激振荡 | 23μW→19W |

### TGFT ∇²Φ_T = κ∇·⟨E×B⟩ + η∇²\|B\|² + ξ∂\|E\|²/∂t
| 装置 | 主控源项 | 物理对应 |
|:---|:---|:---|
| Don Smith | ξ 泵浦 | 高频 Tesla 线圈 |
| Kapanadze | κ + ξ | 火花隙 + 地线 |
| Coler | η 稳定 | 6 永磁体静态配置 |
| SEG | 三者全有 | 三层环对应三源项 |

---

## 五、PJKbook 中"缺席"的重要 PJK/PKS 交叉

以下是我们项目中有、但 PJKbook 未涉及（或仅简要提及）的领域：

| 技术 | PJKbook 覆盖 | 本项目覆盖 |
|:---|:---:|:---:|
| 反重力 (SEG/IGV) | ❌ 未涉及 | ✅ 核心 (24_searl) |
| 中微子凝聚态 (NFC) | ❌ 未涉及 | ✅ Neutrinic Elixirs |
| 昴宿星科技 (AHCS) | ❌ 未涉及 | ✅ AHCS 全息量子 |
| 蛋形几何 + Laplace 谱 | ❌ 未涉及 | ✅ PKS 核心 |
| 非对称电机 (Ufopolitics) | ❌ 仅 Bedini | ✅ 深度分析 |
| EEQT 分形 | ❌ 未涉及 | ✅ 26_eeqt |
| TGFT 数学框架 | ❌ 未涉及 | ✅ 赵山虎 2025 |

---

## 六、PJKbook 方法论贡献与局限

### 贡献
1. **实验主义态度**："构建它、测试它"——比理论推导更有说服力
2. **诚实标注**：Ch13 明确标注 "questionable devices"
3. **复现优先**：给出具体的电路图、绕线数据、材料清单

### 局限
1. **缺乏统一理论**：200+ 种装置各自独立描述，从未尝试统一解释
2. **物理深度不足**：多数装置停留在"怎么做"而非"为什么"
3. **缺乏数学框架**：没有微分方程、没有场论推导
4. **分类混乱**：将标准热泵（COP=3~5）与 Don Smith 装置（COP 可能 >100）混为一谈

### PJKbook 的不可替代性
**它是"实验数据库"而非"理论教科书"**。PJKbook 为 PKS 统一理论提供了 200+ 条独立的实验证据线。每一条证据线都可以用来验证 PKS 三大方程。

---

## 七、学习路径（从 PJKbook 到 PKS 统一）

```
Step 1: 读 PJKbook Ch1 (磁性装置)
  → 理解 Adams/Bedini → 对应周治平 COP 的电磁域

Step 2: 读 PJKbook Ch3 (辐射/离子)
  → 理解 Sweet/Imris → 对应 Aquino χ 的辐射域

Step 3: 读 PJKbook Ch6 (天线系统)
  → 理解 Moray/Don Smith → 对应 TGFT 的频率域

Step 4: 读 PJKbook Ch10 (氢氧)
  → 理解 Boyce/Shigeta → 对应周治平 COP 的化学域

Step 5: 对比 PKS 三大方程
  → 验证每个 PJK 装置是否符合 COP/χ/TGFT 的至少一条

Step 6: 找"三线交汇"装置
  → SEG 是唯一同时满足三条方程的地球工程装置
```

---

> 本关系网覆盖 PJKbook 全部 14 章 + 本项目全部 6 大模块。
> 新建的 4 个子文件夹中各有深度解读 MD。
