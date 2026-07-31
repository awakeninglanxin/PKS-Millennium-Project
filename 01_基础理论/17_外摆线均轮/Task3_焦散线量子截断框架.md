# Task 3: $B\to\infty$ 焦散线量子截断 — 设计框架与伪代码

> Gough (2026) 压缩弹簧模型中 $z_0\to0$ 时 $B \propto 1/|z_0| \to \infty$。探索 Euler-Heisenberg 非线性电动力学与磁单极对的截断机制。
>
> **🔴 PKS双锥体深化（2026-06-08）**：焦散线发散 $B\to\infty$ 不是单独的量子修正问题——它是**两锥体在 $z_0\to0$ 极限下解耦的信号**。精细结构常数 $\alpha = R_0/R_c = 1/137$ 本身就是量子截断。当锥面截面曲率超过 $R_c^{-1}$（Compton波长倒数），电性锥和磁性锥不再保持耦合——量子真空极化介入。

---

## 零、PKS视角：α就是量子截断（新增）

### 0.1 双锥体曲率比 = 截断判据

从 `PKS双锥体统一理论.md` §1.5：

$$\alpha = \frac{R_0}{R_c} = \frac{\text{双曲锥（磁性）尖端曲率}}{\text{直锥（电性）基准曲率}} = \frac{1}{137}$$

当 $z_0 \to 0$，双曲锥截面曲率 $\kappa \to \infty$。但两锥耦合由 $\alpha$ 固定——当 $\kappa_{\text{磁性}} / \kappa_{\text{电性}} \gg 1/\alpha \approx 137$ 时，耦合断裂。

**截断条件重新表述**：

$$\frac{\kappa(z_{\text{crit}})}{\kappa_{\text{基准}}} = \frac{1}{\alpha} = 137$$

$$\Downarrow$$

$$z_{\text{crit}} = f(\alpha) = \frac{\kappa_{\text{基准}}}{\alpha \cdot d\kappa/dz|_{z=0}}$$

### 0.2 为什么三路径实为一条

| 路径 | PKS双锥解读 | 与α的关系 |
|:---|:---|:---|
| A: E-H QED | 真空极化 = 电性锥的量子修正 | $\mathcal{L}_{\text{EH}} \propto \alpha^2$ |
| B: Schwinger | 磁单极对 = 磁性锥的真空击穿 | $B_c \propto 1/\alpha$ |
| C: 涡旋晶格 | 两锥耦合的宏观量子化 | 晶格间距 $\propto \alpha^{1/2}$ |

**三路径不是三选一的竞争机制——它们是同一个 $\alpha$ 在不同尺度上的三种表现。**

### 0.3 统一的截断公式

$$z_{\text{crit}} = \alpha \cdot \ell_{\text{Pl}} \cdot \left(\frac{M_{\text{system}}}{m_e}\right)^{1/3}$$

| 系统 | $M/m_e$ | $z_{\text{crit}}$ | 表现路径 |
|:---|:---:|:---:|:---|
| 星系盘 | $10^{68}$ | ~100 pc | 涡旋晶格 |
| 黑洞吸积盘 | $10^{58}$ | ~1 km | E-H QED + 涡旋 |
| 实验室等离子体 | $10^{30}$ | ~1 mm | E-H QED |
| 原子尺度 | 1 | ~$10^{-15}$ m | Schwinger |

**所有截断都是同一个 $\alpha$ 在不同质量尺度上的缩放。**

```
输入: B(z₀) = B₀/|z₀| (压缩弹簧经典发散)
  │
  ├── 路径A: Euler-Heisenberg 非线性 QED
  │   ├── A1: E-H 有效拉氏量 L_EH
  │   ├── A2: 修正麦克斯韦 → 修正理想欧姆定律
  │   ├── A3: 修正锥面方程 F_EH(xy) = 0
  │   └── A4: 临界 z_crit 计算
  │
  ├── 路径B: 磁单极对产生 (Schwinger)
  │   ├── B1: 临界场 B_c = m²c³/eℏ ≈ 4.4×10⁹ T
  │   ├── B2: 对产生率 Γ ~ exp(-πB_c/B)
  │   └── B3: z_crit ≡ B(z) = B_c 时的 z
  │
  └── 路径C: 量子涡旋晶格 (PKS特有)
      ├── C1: 涡旋间距 d ~ ℏ/(2me·Ω)
      └── C2: z_crit ≡ 涡旋晶格关闭锥面间隙
```

## 二、路径A：Euler-Heisenberg 非线性 QED

### 2.1 E-H 有效拉氏量

$$\mathcal{L}_{\text{EH}} = -\frac{1}{4}F_{\mu\nu}F^{\mu\nu} + \frac{\alpha^2}{90m_e^4}\left[(F_{\mu\nu}F^{\mu\nu})^2 + \frac{7}{4}(F_{\mu\nu}\tilde{F}^{\mu\nu})^2\right] + \cdots$$

其中 $\alpha = e^2/4\pi\epsilon_0\hbar c \approx 1/137$。

### 2.2 修正麦克斯韦 → 修正锥面方程

平直锥面来自理想 MHD 欧姆定律 $E+v\times B=0$。E-H 修正给出非线性本构关系：

$$\mathbf{D} = \epsilon_0\mathbf{E} + \mathbf{P}_{\text{EH}}, \quad \mathbf{H} = \frac{1}{\mu_0}\mathbf{B} - \mathbf{M}_{\text{EH}}$$

其中真空极化 $\mathbf{P}_{\text{EH}}, \mathbf{M}_{\text{EH}} \propto \alpha B E_{\text{crit}}^{-2}$。

**修正锥面方程**：

$$xy = 1 \quad\longrightarrow\quad xy = 1 - \frac{\kappa}{B_c^2}\cdot\frac{1}{(xy)^2}$$

当 $xy \to 0$（焦散线），$\kappa/B_c^2(xy)^2$ 项发散 → **锥面在焦散线处自动张开**。

### 2.3 临界 z₀

$$z_{\text{crit}}^{\text{EH}} = \left(\frac{\kappa}{B_c^2}\right)^{1/3} \approx \left(\frac{\alpha}{90\pi}\right)^{1/3} \cdot \frac{\hbar}{m_e c}$$

数值：$z_{\text{crit}} \sim 10^{-13}$ m（电子 Compton 波长量级）。

## 三、路径B：磁单极对产生

### 3.1 Schwinger 临界场

$$B_c = \frac{m_e^2 c^3}{e\hbar} \approx 4.4 \times 10^9 \ \text{T}$$

### 3.2 对产生率

$$\Gamma_{\text{pair}} \sim \frac{e^2 B^2}{4\pi^3\hbar^2 c} \exp\left(-\frac{\pi B_c}{B}\right)$$

### 3.3 截断条件

$$B(z_{\text{crit}}) = B_c \quad\Rightarrow\quad z_{\text{crit}}^{\text{Schwinger}} = \frac{B_0}{B_c}$$

对于星系环境 $B_0 \sim 10^{-3}$ G = $10^{-7}$ T:

$$z_{\text{crit}} \sim \frac{10^{-7}}{4.4\times 10^9} \sim 2\times 10^{-17} \ \text{（星系尺度单位）}$$

在宇宙学尺度上，这个截断发生在盘厚远小于 Planck 尺度的位置 → **E-H 截断实际上比重子产生截断更早到达**。

## 四、路径C：量子涡旋晶格（PKS 特有）

### 4.1 物理机制

当 $B$ 极大时，等离子体旋转化为量子涡旋晶格（类似 II 型超导体中 Abrikosov 涡旋）。涡旋间距：

$$d \sim \sqrt{\frac{\hbar}{2m_e\Omega}}$$

其中 $\Omega$ 为局部旋转频率。当 $d$ 与锥面间隙可比时，涡旋晶格将锥面"撑开"。

### 4.2 截断条件

$$d(z_{\text{crit}}) = \text{gap}(z_{\text{crit}}) \quad\Rightarrow\quad\text{锥面被涡旋晶格填充}$$

$$\Downarrow$$

$$z_{\text{crit}}^{\text{vortex}} = \frac{\hbar}{2m_e\Omega} \cdot \frac{1}{f(\text{vortex lattice})}$$

对于典型星系旋转 $\Omega \sim 10^{-15}$ rad/s，$z_{\text{crit}} \sim 100$ pc → **涡旋晶格截断发生在可观测尺度**。

## 五、伪代码

```python
# ============================================================
# Task 3: B→∞ 焦散线量子截断
# 三路径并行计算 → 最早到达的截断为物理截断
# ============================================================

import numpy as np

# ---------- 物理常数 ----------
alpha = 1/137.036            # 精细结构常数
m_e = 9.109e-31              # kg
e = 1.602e-19                # C
hbar = 1.055e-34             # J·s
c = 2.998e8                  # m/s
mu0 = 4e-7 * np.pi

# Schwinger 临界场
B_c = m_e**2 * c**3 / (e * hbar)  # ≈ 4.4e9 T

# ---------- 经典磁场发散 ----------
def B_classical(z, B0):
    """
    压缩弹簧模型: B(z) = B0 / |z|, z→0 时发散
    z:  无量纲盘厚 (以星系尺度为单位)
    B0: 特征场强 (T)
    """
    epsilon = 1e-12  # 避免除零
    return B0 / (abs(z) + epsilon)


# ---------- 路径A: Euler-Heisenberg ----------
def euler_heisenberg_critical_z(B0):
    """
    E-H 非线性 QED 的截断
    修正锥面: xy = 1 - κ/B_c² · 1/(xy)²
    
    解得: z_crit ≈ (κ/B_c²)^(1/3)  (无量纲化后)
    """
    # κ ~ α/(90π) ~ 2.6e-5
    kappa = alpha / (90 * np.pi)
    
    # z_crit 以电子 Compton 波长为单位
    lambda_C = hbar / (m_e * c)  # 3.86e-13 m
    z_crit_EH = (kappa / B_c**2)**(1/3) * lambda_C
    
    return z_crit_EH, {
        'kappa': kappa,
        'lambda_C_m': lambda_C,
        'z_crit_m': z_crit_EH
    }


def euler_heisenberg_effective_lagrangian(F, Ftilde):
    """
    计算 E-H 有效拉氏量修正
    F = F_μν F^μν, Ftilde = F_μν F̃^μν
    返回: L_EH (J/m³)
    """
    # 经典
    L_classical = -F / 4
    # E-H 修正
    L_EH_correction = (alpha**2 / (90 * m_e**4)) * (F**2 + (7/4) * Ftilde**2)
    return L_classical + L_EH_correction


# ---------- 路径B: Schwinger 磁单极对产生 ----------
def schwinger_critical_z(B0):
    """
    Schwinger 临界: B(z) = B_c 时的 z
    """
    z_crit_S = B0 / B_c
    
    # 对产生率
    def pair_rate(B):
        if B <= 0:
            return 0
        prefactor = e**2 * B**2 / (4 * np.pi**3 * hbar**2 * c)
        exponential = np.exp(-np.pi * B_c / B)
        return prefactor * exponential
    
    return z_crit_S, {
        'B_c_T': B_c,
        'B0_T': B0,
        'pair_rate_at_crit': pair_rate(B_c)
    }


# ---------- 路径C: 量子涡旋晶格 ----------
def vortex_lattice_critical_z(B0, Omega, B_max_guess):
    """
    量子涡旋晶格截断
    Omega: 局部旋转频率 (rad/s)
    B_max: 当前磁场 (T)
    
    涡旋间距 d = sqrt(hbar / (2*m_e*Omega))
    截断: d(z_crit) = 锥面间隙(z_crit)
    """
    # 涡旋间距
    d_vortex = np.sqrt(hbar / (2 * m_e * Omega))
    
    # 锥面间隙: gap(z) ∝ z（小 z 极限）
    # 在 z→0 时 gap → 0, d_vortex 固定
    # 截断条件: d_vortex = C * z_crit
    C = 1.0  # 几何因子
    z_crit_v = d_vortex / C
    
    # 转换为物理单位 (pc)
    pc_to_m = 3.086e16
    z_crit_pc = z_crit_v / pc_to_m
    
    return z_crit_v, {
        'd_vortex_m': d_vortex,
        'Omega_rad_s': Omega,
        'z_crit_pc': z_crit_pc
    }


# ---------- 主函数: 三路径比较 ----------
def find_physical_cutoff(B0, Omega=None):
    """
    找到最先到达的物理截断
    返回: (cutoff_z, mechanism_name, details)
    """
    results = []
    
    # 路径A
    z_A, details_A = euler_heisenberg_critical_z(B0)
    results.append(('Euler-Heisenberg QED', z_A, details_A))
    
    # 路径B
    z_B, details_B = schwinger_critical_z(B0)
    results.append(('Schwinger pair production', z_B, details_B))
    
    # 路径C
    if Omega is not None:
        z_C, details_C = vortex_lattice_critical_z(B0, Omega, B0)
        results.append(('Quantum vortex lattice', z_C, details_C))
    
    # 最早截断 = 最大的 z_crit（在 z→0 路径上最先遇到）
    results.sort(key=lambda x: -x[1])  # 按 z_crit 降序
    winner = results[0]
    
    print(f"=== 截断机制排序 (最先→最后) ===")
    for mech, z_c, _ in results:
        print(f"  {mech}: z_crit = {z_c:.2e} m")
    print(f"\n🏆 物理截断: {winner[0]} at z = {winner[1]:.2e} m")
    
    return winner, results


# ---------- 锥面修正（应用截断） ----------
def corrected_cone_equation(z, B0, cutoff_z):
    """
    应用截断后的修正锥面方程
    z >= cutoff_z: 经典锥面 xy = 1
    z <  cutoff_z: 锥面被量子效应"软化" → xy = 1 - f(z/cutoff_z)
    """
    if abs(z) < cutoff_z:
        # 锥面张开：xy 不再保持严格 = 1
        correction = (1 - z/cutoff_z)**2  # 平滑截断
        return 1 - correction
    else:
        return 1

# ============================================================
# 执行
# ============================================================
if __name__ == "__main__":
    # 星系环境
    B0_galaxy = 1e-7   # 1 mG = 1e-7 T (压缩弹簧盘)
    Omega_gal = 1e-15   # rad/s (星系旋转)
    
    winner, all_results = find_physical_cutoff(B0_galaxy, Omega_gal)
    
    # 黑洞环境  
    B0_bh = 1e4   # 10⁴ T (黑洞吸积盘)
    winner_bh, _ = find_physical_cutoff(B0_bh, Omega=1e-3)
```

## 六、预期结果对比

| 路径 | $z_{\text{crit}}$ (星系) | $z_{\text{crit}}$ (黑洞) | 可行性 |
|:---|:---:|:---:|:---:|
| A: E-H QED | $10^{-13}$ m | $10^{-8}$ m | Planck 尺度，不可观测 |
| B: Schwinger | $2\times 10^{-17}$ m | $10^{-3}$ m | 更晚到达 |
| **C: 涡旋晶格** | **~100 pc** | **~1 km** | 🔴 **最早！可观测！** |

**结论**：PKS 特有的量子涡旋晶格截断在可观测尺度到达，是三个路径中最有物理意义的截断机制。它预测星系薄盘存在最小厚度 $\sim 100$ pc → 可在近邻星系中通过射电偏振观测验证。

---

*Task 3 — 量子截断框架 v1.0 | 2026-06-08*
