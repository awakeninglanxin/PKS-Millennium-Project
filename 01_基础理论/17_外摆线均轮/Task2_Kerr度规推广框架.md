# Task 2: $xy=1$ → Kerr 度规推广 — 设计框架与伪代码

> 将 PKS 双曲锥体 $xy=1$ 从平直时空推广到 Kerr 旋转黑洞时空，在 Boyer-Lindquist 坐标下导出修正锥面方程，给出射影几何自洽的 CRF 补偿项。
>
> **🔴 PKS双锥体深化（2026-06-08）**：Kerr推广不是只推广 $xy=1$（磁性锥）。$ab=1$ 极化原理要求**两个锥体同时推广**：电性锥 $a=x$ 和磁性锥 $b=1/x$ 在弯曲时空中各自变形，两者的耦合系数（原为 $\alpha=1/137$）变为位置依赖的 $\alpha(r,\theta)$。

---

## 零、PKS双锥体的GR推广框架（新增）

### 0.1 双锥体的电磁分解

在 Kerr 时空中，电磁场张量 $F_{\mu\nu}$ 分解为电/磁部分：

$$F_{\mu\nu} = u_\mu E_\nu - u_\nu E_\mu + \epsilon_{\mu\nu\alpha\beta} u^\alpha B^\beta$$

| 部分 | PKS锥体 | Kerr推广 |
|:---|:---|:---|
| **电场** $E_\mu$ | 电性锥 $a=x$（直圆锥→椭圆） | $E_r \propto 1/r^2$，随 $r$ 衰减 |
| **磁场** $B_\mu$ | 磁性锥 $b=1/x$（超双曲锥→蛋形） | $B \propto aM/r^3$，拖曳增强 |
| **耦合常数** | $\alpha = 1/137$（平直） | $\alpha(r,\theta) = \alpha_0 \cdot f(a/M, r)$ |

### 0.2 坐标拖曳 = 射影变换的GR对应

Lense-Thirring 拖曳角速度 $\omega(r,\theta)$ 等价于射影群 $\text{PGL}(3)$ 中**时间依赖的剪切变换**：

$$\begin{pmatrix} X' \\ Y' \\ Z' \end{pmatrix} = \begin{pmatrix} 1 & -\omega t & 0 \\ \omega t & 1 & 0 \\ 0 & 0 & 1 \end{pmatrix} \begin{pmatrix} X \\ Y \\ Z \end{pmatrix}$$

锥面截面在每一高度 $z_0$ 上经历不同的拖曳幅度 → CRF不变量从全局常数变为局部函数。

---

## 一、证明路径

```
输入: 平直 xy=1 锥体 + Kerr 度规 g_μν
  │
  ├── 步骤1: BL坐标下的 Kerr 度规分量
  ├── 步骤2: 将 xy=1 提升为 4D 超曲面 F(x^μ)=0
  ├── 步骤3: Kerr 时空中超曲面 F 被平面 Y=kX+b 截 → 蛋形
  ├── 步骤4: 导出 GR 修正项 Δ = F_GR - F_flat
  ├── 步骤5: 射影几何自洽: 交比在 Kerr 时空中推广为 CRF
  └── 步骤6: 数值验证: → GR 蛋形 vs 平直蛋形对比
```

## 二、Kerr 度规回顾

Boyer-Lindquist 坐标 $(t, r, \theta, \phi)$:

$$ds^2 = -\left(1-\frac{2Mr}{\Sigma}\right)dt^2 - \frac{4Mar\sin^2\theta}{\Sigma}dt\,d\phi + \frac{\Sigma}{\Delta}dr^2 + \Sigma d\theta^2 + \left(r^2+a^2+\frac{2Ma^2r\sin^2\theta}{\Sigma}\right)\sin^2\theta d\phi^2$$

| 符号 | 含义 |
|:---|:---|
| $\Sigma = r^2 + a^2\cos^2\theta$ | BL 径向函数 |
| $\Delta = r^2 - 2Mr + a^2$ | 视界函数 |
| $M$ | 黑洞质量 |
| $a = J/M$ | 比角动量 ($0 \le a \le M$) |

## 三、$xy=1$ 的 GR 推广

### 3.1 平直空间锥面（参考）

$$F_{\text{flat}}(X,Y,Z) = XY - 1 = 0$$

其中 $(X,Y,Z)$ 是空间 Cartesian 坐标 → 截面参数 $(z_0, \alpha)$。

### 3.2 Kerr 时空中的提升

将空间 Cartesian → BL 坐标转换：

$$X = \sqrt{r^2 + a^2}\sin\theta\cos\phi$$
$$Y = \sqrt{r^2 + a^2}\sin\theta\sin\phi$$
$$Z = r\cos\theta$$

则有：

$$XY = (r^2 + a^2)\sin^2\theta\cos\phi\sin\phi$$

**GR 修正锥面方程**：

$$F_{\text{Kerr}}(r,\theta,\phi) = (r^2 + a^2)\sin^2\theta\cos\phi\sin\phi - 1 = 0$$

与平直时空的差异：

| | 平直 | Kerr |
|:---|:---|:---|
| 径向依赖 | $r^2$ | $r^2 + a^2$ |
| $r\to\infty$ | $r^2\sin^2\theta\cos\phi\sin\phi - 1 = 0$ | $(r^2 + a^2)\sin^2\theta\cos\phi\sin\phi - 1 = 0$ |
| 近视界行为 | 无奇点 | 锥面被"拖曳"旋转 |

### 3.3 截面蛋形（平面截 Kerr 锥面）

切割平面：$Z = kX + b$，代入 Kerr BL → Cartesian 转换：

$$Z = r\cos\theta = k\sqrt{r^2+a^2}\sin\theta\cos\phi + b$$

联立锥面约束 $F_{\text{Kerr}}=0$，解得 $r(\theta,\phi)$ → 截面曲线。

## 四、关键修正量：拖曳因子

### 4.1 Kerr 时空中的锥面拖曳

Kerr 时空的座标拖曳效应（Lense-Thirring）导致锥面 $\phi$ 角被"拖转"：

$$\omega(r) = \frac{2Mar}{(r^2+a^2)^2 - a^2\Delta\sin^2\theta}$$

锥面上的有效旋转角：

$$\phi_{\text{eff}} = \phi + \omega(r) \cdot \frac{\text{distance}}{\text{光速}}$$

### 4.2 拖曳对蛋形截面参数的影响

平直 $z_0, \alpha$ → Kerr $z_0^{\text{Kerr}}, \alpha^{\text{Kerr}}$:

$$z_0^{\text{Kerr}} = z_0 \cdot \sqrt{1 + \frac{a^2}{r_0^2}}$$
$$\alpha^{\text{Kerr}} = \alpha - \frac{a}{M}\tanh^{-1}\left(\frac{r - r_{\text{ISCO}}}{r}\right)$$

其中 $r_{\text{ISCO}}$ 是最内稳定圆轨道。

## 五、射影几何自洽：CRF 不变量

### 5.1 问题

平直时空的射影变换 $\text{PGL}(3)$ 保持交比不变。Kerr 时空的弯曲 → 射影群需要推广。

### 5.2 解：CRF (Cross-Ratio Function)

将交比从常数推广为位置依赖的函数：

$$\text{CRF}(z_1,z_2,z_3,z_4; g_{\mu\nu}) \equiv \frac{(z_1-z_3)(z_2-z_4)}{(z_1-z_4)(z_2-z_3)} + \delta_{\text{GR}}(r,\theta)$$

其中 GR 修正项：

$$\delta_{\text{GR}}(r,\theta) = \frac{a^2}{r^2}\cdot\frac{\sin^2\theta}{1+\cos^2\theta}$$

**意义**：$\delta_{\text{GR}} \to 0$ 当 $a\to0$（Schwarzschild）或 $r\to\infty$（渐近平坦），恢复平直交比不变性。

## 六、伪代码

```python
# ============================================================
# Task 2: xy=1 → Kerr 度规推广
# 输入: 黑洞参数 (M, a), 切割参数 (z0, alpha)
# 输出: Kerr 蛋形截面 + CRF 比较 + GR 修正量
# ============================================================

import numpy as np
from scipy.integrate import solve_ivp

# ---------- 1. Kerr 度规辅助函数 ----------
def Sigma(r, theta, a):
    return r**2 + a**2 * np.cos(theta)**2

def Delta(r, M, a):
    return r**2 - 2*M*r + a**2

def frame_drag_omega(r, theta, M, a):
    """Lense-Thirring 坐标拖曳角速度"""
    return 2 * M * a * r / ( (r**2 + a**2)**2 - a**2 * Delta(r,M,a) * np.sin(theta)**2 )


# ---------- 2. Kerr锥面定义 ----------
def kerr_cone_equation(r, theta, phi, a):
    """
    Kerr 时空中的双曲锥面: F_Kerr = (r²+a²)sin²θ·cosφ·sinφ - 1 = 0
    返回: 残差 (0 = 在锥面上)
    """
    return (r**2 + a**2) * np.sin(theta)**2 * np.cos(phi) * np.sin(phi) - 1


# ---------- 3. 平直→Kerr 蛋形参数映射 ----------
def flat_to_kerr_params(z0_flat, alpha_flat, M, a, r0):
    """
    将平直蛋形参数映射到 Kerr 时空
    
    z0_flat:  平直截面高度
    alpha_flat: 平直倾角
    M, a:     黑洞参数
    r0:       特征半径（截面中心到黑洞的距离）
    
    返回: (z0_kerr, alpha_kerr)
    """
    drag_factor = np.sqrt(1 + a**2 / r0**2)
    z0_kerr = z0_flat * drag_factor
    
    # 倾角修正: 拖曳使有效倾角变小（锥面被"拉直"）
    r_ISCO = M * (3 + Z2 - np.sign(a) * np.sqrt((3 - Z1) * (3 + Z1 + 2*Z2)))
    # Z1, Z2 是 ISCO 辅助量 (略)
    alpha_kerr = alpha_flat * (1 + a/M * np.tanh((r0 - r_ISCO) / M))
    
    return z0_kerr, alpha_kerr


# ---------- 4. Kerr蛋形截面计算 ----------
def kerr_egg_section(M, a, z0, alpha, n_theta=360):
    """
    在 Kerr 时空中计算切割平面 Z = kX + b 的截面蛋形
    
    M, a:   黑洞参数
    z0, alpha: 切割参数（经过 flat_to_kerr_params 映射后）
    n_theta: 角度采样数
    """
    k = np.tan(alpha)
    b = z0
    
    # 4.1 Kerr BL → Cartesian
    theta_grid = np.linspace(0.01, np.pi - 0.01, n_theta)
    points = []
    
    for theta in theta_grid:
        for phi_guess in np.linspace(-np.pi, np.pi, 20):
            # 用 Newton 法求解锥面方程 + 切割平面
            # F(r,theta,phi) = 0 ∧ Z = kX + b
            # 此处简化：先解 r 再回代
            pass
    
    # 4.2 简化：在 r >> M 的远场近似下
    # Kerr蛋形 ≈ 平直蛋形 × (1 + a²/r₀²)
    r_flat = 1.0 / (z0 - np.sin(theta_grid) * np.sin(alpha))
    r_kerr = r_flat * np.sqrt(1 + a**2 / (M * 10)**2)  # r₀ ≈ 10M
    
    # Cartesian
    X = r_kerr * np.sin(theta_grid) * np.cos(np.pi/4)  # φ_peak = π/4
    Z = r_kerr * np.cos(theta_grid)
    
    return {'X': X, 'Z': Z, 'r_kerr': r_kerr, 'theta': theta_grid}


# ---------- 5. CRF 不变量检验 ----------
def compute_CRF(z1, z2, z3, z4, M, a, r_ref):
    """
    计算 Kerr 时空中的推广交比函数
    4个z = 锥面上4个截面的z坐标（沿同一φ的θ采样）
    """
    # 5.1 平直交比
    flat_CR = ((z1 - z3) * (z2 - z4)) / ((z1 - z4) * (z2 - z3))
    
    # 5.2 GR修正
    theta_ref = np.arctan(np.mean([z1, z2, z3, z4]) / r_ref)
    delta_GR = (a**2 / r_ref**2) * (np.sin(theta_ref)**2 / (1 + np.cos(theta_ref)**2))
    
    CRF = flat_CR + delta_GR
    
    return flat_CR, delta_GR, CRF


# ---------- 6. GR蛋形 vs 平直蛋形 对比 ----------
def compare_flat_vs_kerr(M=1.0, a=0.9, z0=10.0, alpha=0.15):
    """
    对比平直和 Kerr 蛋形的差异
    输出: Δ_kE = k_E,kerr - k_E,flat
          截面重叠图数据
    """
    # 6.1 平直
    z0_flat, alpha_flat = z0, alpha
    r_flat = 1.0 / (z0_flat - np.linspace(-2, 2, 200) * np.sin(alpha_flat))
    kE_flat = r_flat.max() / abs(r_flat.min())
    
    # 6.2 Kerr
    z0_kerr, alpha_kerr = flat_to_kerr_params(z0_flat, alpha_flat, M, a, z0)
    r0 = z0  # 截面中心
    result = kerr_egg_section(M, a, z0_kerr, alpha_kerr)
    kE_kerr = max(result['r_kerr']) / abs(min(result['r_kerr']))
    
    Delta_kE = kE_kerr - kE_flat
    pct = Delta_kE / kE_flat * 100
    
    print(f"平直蛋形度: {kE_flat:.4f}")
    print(f"Kerr蛋形度: {kE_kerr:.4f}")
    print(f"Δk_E:       {Delta_kE:.4f} ({pct:.2f}%)")
    print(f"GR修正方向: {'蛋更扁' if Delta_kE < 0 else '蛋更鼓'}")
    
    return Delta_kE, kE_flat, kE_kerr


# ---------- 7. 参数扫描 ----------
def scan_kerr_parameter_space():
    """扫描 a/M ∈ [0, 0.998] 的 GR 修正量"""
    a_vals = np.linspace(0, 0.998, 20)
    Delta_kE_list = []
    
    for a in a_vals:
        dkE, _, _ = compare_flat_vs_kerr(M=1.0, a=a, z0=10.0, alpha=0.15)
        Delta_kE_list.append(dkE)
    
    # 拟合 Δk_E ∝ (a/M)² （预期的 scaling）
    from scipy import stats
    slope, _, r_val, _, _ = stats.linregress(a_vals**2, Delta_kE_list)
    print(f"\nΔk_E ∝ (a/M)^² 斜率: {slope:.4f} (R={r_val:.3f})")
    
    return a_vals, Delta_kE_list


# ============================================================
# 执行
# ============================================================
if __name__ == "__main__":
    # 标准黑洞 (M=1, a=0.9)
    dkE, kE_f, kE_k = compare_flat_vs_kerr()
    print(f"\n标准 Kerr (a=0.9): Δk_E = {dkE:.4f}")
    
    # 扫描
    a_vals, dkE_vals = scan_kerr_parameter_space()
```

## 七、预期结论

| 场景 | $a/M$ | Δk_E | 可观测？ |
|:---|:---:|:---:|:---:|
| Schwarzschild | 0 | 0 | 基准 |
| 慢旋转 | 0.3 | ~2% | 需 VLBI |
| 快旋转 | 0.9 | ~15% | EHT 可测 |
| 极端旋转 | 0.998 | ~30% | 明显 |

---

*Task 2 — Kerr 推广框架 v1.0 | 2026-06-08*
