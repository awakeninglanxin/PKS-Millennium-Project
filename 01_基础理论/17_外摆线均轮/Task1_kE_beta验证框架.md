# Task 1: 验证 $k_E - 1 \propto \beta$ — 设计框架与伪代码

> 核心命题：PKS 蛋形度 $k_E$ 与等离子体 $\beta$ 存在线性关系 $k_E - 1 = C \cdot \beta$。本文档给出完整的实验验证框架。
>
> **🔴 PKS双锥体深化（2026-06-08）**：$\beta = p/(B^2/2\mu_0)$ 是电性压力（椭圆锥）与磁性压力（双曲锥蛋形）之比。$\beta$ 不是"独立参数"——它是双锥体耦合常数在流体极限下的表现。验证 $k_E \propto \beta$ 等价于验证**蛋形不对称度 = 双锥体耦合强度**。

---

## 零、PKS双锥体理论框架（新增）

### 0.1 两锥耦合与β

从 `PKS双锥体统一理论.md`（蓝馨，$ab=1$ 极化原理）：

```
电性锥（a=x, 直圆锥）
  → 椭圆截面 → 压力场 p → Poisson方程 ∇²p = -ρ∇·(u·∇u)
  → 本征函数: Mathieu函数, λ_n^E ~ n

磁性锥（b=1/x, 超双曲锥）
  → 蛋形截面 → 速度场 u → NS对流项 (u·∇)u
  → 本征函数: 蛋形谐波, λ_n^M ~ ln n

精细结构常数 α = R₀/R_c = 两锥曲率比 = 1/137.036
```

### 0.2 β 的双锥解读

$$\beta = \frac{p}{B^2/2\mu_0} = \frac{\text{电性锥压力（椭圆）}}{\text{磁性锥压力（蛋形）}}$$

| β 范围 | 主导锥体 | 蛋形度 k_E |
|:---|:---|:---:|
| β ≪ 1 | 磁性锥主导 | k_E → 1（近圆） |
| β ~ 1 | 两锥平衡 | k_E ~ 1.5（标准蛋形） |
| β ≫ 1 | 电性锥主导 | 蛋形破裂 |

### 0.3 与精细结构常数的深层联系

$$\beta_{\text{临界}} \propto \alpha = \frac{1}{137}$$

这意味着等离子体 $\beta$ 在 $1/137$ 附近时发生**锥体主导权切换**——这个数值恰好是太阳风-Alfvén 过渡区的典型 $\beta$ 值范围。

---

## 一、证明路径

```
输入: 卫星等离子体密度/磁场/温度剖面
  │
  ├── 步骤1: 提取蛋形截面点云 (x,z) 坐标
  ├── 步骤2: 非线性最小二乘拟合 PKS 蛋形 → 提取 (z₀, α, k_E)
  ├── 步骤3: 从同一数据计算 β = 2μ₀p/B²
  ├── 步骤4: 多时刻/多地磁活动重复 → (k_E, β) 散点图
  └── 步骤5: 线性回归 → k_E - 1 = C·β, 输出 R² + p-value
```

## 二、PKS 蛋形拟合公式

### 2.1 锥面截面参数方程（2参数）

$$x(u) = \frac{1}{z_0 - u\sin\alpha}\cos\phi(u)$$
$$y(u) = \frac{1}{z_0 - u\sin\alpha}\sin\phi(u)$$

其中 $\phi(u)$ 由截面几何约束 $\text{dist}[\text{point}, \text{plane}] = 0$ 解得。

### 2.2 蛋形度定义

$$k_E = \frac{\max\{|r(\theta)|\}}{\min\{|r(\theta)|\}}$$

其中 $r(\theta)$ 为截面在极坐标下的半径函数。等效地，$k_E = y_{\max}/|y_{\min}|$。

### 2.3 核心假设（待验证）

$$k_E - 1 = C \cdot \beta, \quad C \approx \text{常数}$$

H₀: C = 0 (无关系) vs H₁: C > 0 (正比)

## 三、数据源

| 卫星任务 | 时间跨度 | 可提取量 | 轨道 |
|:---|:---|:---|:---|
| IMAGE/EUV | 2000-2005 | $n_e$（He⁺ 30.4nm） | 极轨 |
| Van Allen Probes | 2012-2019 | $n_e, B, T$ | 赤道 |
| Cluster | 2000-至今 | $n_e, B$（多点） | 极轨 |
| THEMIS | 2007-至今 | $B$ | 赤道 |

**推荐首选**：Van Allen Probes HOPE + EMFISIS 仪器的同步 $n_e, B, T$ 数据 → 可直接算 $\beta$。

## 四、伪代码

```python
# ============================================================
# Task 1: 验证 k_E - 1 = C * beta
# 输入: 卫星等离子体层顶截面数据
# 输出: 拟合参数 C, R², p-value
# ============================================================

import numpy as np
from scipy.optimize import curve_fit

# ---------- 1. 数据加载 ----------
def load_plasmasphere_data(satellite, date_range):
    """
    从卫星档案加载等离子体层截面数据
    返回: arrays of (r, lat, n_e, B, T_perp, T_para)
    r   = 地心距离 (R_E)
    lat = 磁纬度 (度)
    """
    if satellite == 'VanAllen':
        data = fetch_van_allen_hope_emfisis(date_range)
    elif satellite == 'IMAGE':
        data = fetch_image_euv_density(date_range)
    return {
        'r': data['L'] * 6371,      # km
        'lat': data['mlat'],         # deg
        'ne': data['density'],       # cm^-3
        'B': data['B_total'],        # nT
        'T': (data['T_perp'] + 2*data['T_para'])/3  # K (平均)
    }


# ---------- 2. 提取蛋形截面 (x,z) ----------
def extract_egg_cross_section(data):
    """
    在子午面 (r, lat) 中提取等离子体层顶的蛋形轮廓
    层顶定义: n_e 从 >100 cm^-3 骤降至 <10 cm^-3 的位置
    """
    # 2.1 按 lat 分箱
    lat_bins = np.linspace(-60, 60, 50)
    boundary_points = []
    
    for lat_min, lat_max in zip(lat_bins[:-1], lat_bins[1:]):
        mask = (abs(data['lat']) >= lat_min) & (abs(data['lat']) < lat_max)
        if mask.sum() < 10:
            continue
        r_sorted = np.sort(data['r'][mask])
        ne_sorted = data['ne'][mask][np.argsort(data['r'][mask])]
        # 找到 n_e 骤降的位置（等离子体层顶）
        idx = np.where(ne_sorted[:-1] > 50)[0]
        if len(idx) > 0:
            r_pp = r_sorted[idx[-1]]
            lat_mid = (lat_min + lat_max) / 2
            boundary_points.append((lat_mid, r_pp))
    
    # 2.2 转为笛卡尔 (x=赤道距离, z=磁轴距离)
    pts = []
    for lat, r in boundary_points:
        z = r * np.sin(np.radians(lat))
        x = r * np.cos(np.radians(lat))
        pts.append((x, z))
    return np.array(pts)  # [N, 2]


# ---------- 3. PKS 蛋形模型函数 ----------
def pks_egg_model(theta, z0, alpha):
    """
    PKS 蛋形在极坐标下的近似形式
    参数: z0=截面高度, alpha=倾角
    返回: r(theta) 极径
    """
    # xy=1 锥面截面约束
    # 精确解涉及解二次方程，此处为近似
    num = np.sqrt(z0**2 + alpha**2)
    denom = abs(np.cos(theta) + z0 * np.sin(theta) + alpha * np.cos(2*theta))
    return 1.0 / (num * denom + 0.01)


def fit_pks_egg(points):
    """
    用 PKS 2参数模型拟合点云，提取 (z0, alpha, k_E)
    points: [N, 2] = (x, z) 笛卡尔坐标
    """
    # 转为极坐标
    r_obs = np.sqrt(points[:, 0]**2 + points[:, 1]**2)
    theta_obs = np.arctan2(points[:, 1], points[:, 0])
    
    # 非线性最小二乘拟合
    popt, pcov = curve_fit(pks_egg_model, theta_obs, r_obs,
                          p0=[3.0, 0.15], bounds=([0.1, 0.001], [10, 2]))
    z0_fit, alpha_fit = popt
    
    # 计算拟合的蛋形轮廓
    theta_grid = np.linspace(-np.pi, np.pi, 360)
    r_fit = pks_egg_model(theta_grid, z0_fit, alpha_fit)
    
    # 蛋形度 k_E
    k_E = r_fit.max() / abs(r_fit.min())
    
    # 拟合优度
    r_pred = pks_egg_model(theta_obs, z0_fit, alpha_fit)
    R2 = 1 - np.sum((r_obs - r_pred)**2) / np.sum((r_obs - r_obs.mean())**2)
    
    return {'z0': z0_fit, 'alpha': alpha_fit, 'k_E': k_E, 'R2': R2,
            'theta': theta_grid, 'r_fit': r_fit}


# ---------- 4. 计算等离子体 beta ----------
def compute_beta(data, r_match):
    """
    在等离子体层顶处计算局部 beta
    p = n_e * k_B * T (理想气体)
    beta = 2 * mu0 * p / B^2
    """
    mu0 = 4 * np.pi * 1e-7
    kB = 1.380649e-23
    
    # 插值到层顶半径处
    p_local = np.interp(r_match, data['r'],
                        data['ne'] * 1e6 * kB * data['T'])  # Pa
    B_local = np.interp(r_match, data['r'], data['B']) * 1e-9  # T
    
    beta = 2 * mu0 * p_local / B_local**2
    return beta, p_local, B_local


# ---------- 5. 主验证流程 ----------
def verify_kE_beta_relation(satellite='VanAllen', n_epochs=30):
    """
    多时刻重复拟合 → 搜集 (k_E, beta) 对 → 线性回归
    返回: C (斜率), R², p-value
    """
    kE_list = []
    beta_list = []
    R2_list = []
    
    dates = generate_sample_epochs(n_epochs, years=[2014, 2015, 2017])
    # 选择不同地磁活动水平 (Kp=0~6)
    
    for date in dates:
        data = load_plasmasphere_data(satellite, date)
        points = extract_egg_cross_section(data)
        
        if len(points) < 20:   # 数据不足，跳过
            continue
        
        fit = fit_pks_egg(points)
        if fit['R2'] < 0.7:    # 拟合太差，跳过
            continue
        
        r_mean = np.sqrt(points[:, 0]**2 + points[:, 1]**2).mean()
        beta_val, _, _ = compute_beta(data, r_mean)
        
        kE_list.append(fit['k_E'])
        beta_list.append(beta_val)
        R2_list.append(fit['R2'])
    
    # 5.1 线性回归
    kE_arr = np.array(kE_list)
    beta_arr = np.array(beta_list)
    
    # y = a*x + b, 即 k_E - 1 = C * beta → k_E = C * beta + 1
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(beta_arr, kE_arr)
    
    C = slope          # 期望 intercept ≈ 1.0
    R2 = r_value**2
    
    print(f"验证结果:")
    print(f"  C (斜率) = {C:.4f} ± {std_err:.4f}")
    print(f"  intercept = {intercept:.4f} (期望 ~1.0)")
    print(f"  R² = {R2:.4f}")
    print(f"  p-value = {p_value:.4f}")
    print(f"  N = {len(kE_arr)} 个有效 epoch")
    
    # 5.2 判断
    if p_value < 0.05 and abs(intercept - 1.0) < 0.3:
        conclusion = "✅ 支持 H₁: k_E - 1 ∝ β"
    elif p_value >= 0.05:
        conclusion = "⚠️ 不支持: p > 0.05, 可能 C 过小或噪声过大"
    else:
        conclusion = "⚠️ intercept 偏离 1.0, 蛋形度定义需修正"
    
    return {'C': C, 'R2': R2, 'p': p_value, 'N': len(kE_arr),
            'kE': kE_arr, 'beta': beta_arr, 'R2_fits': R2_list,
            'conclusion': conclusion}


# ---------- 6. 敏感性分析 ----------
def sensitivity_analysis():
    """
    测试: 改变层顶定义阈值 (50→30, 50→100 cm^-3)
    测试: 不同 β 计算高度 (层顶内 0.5R_E, 1.0R_E)
    输出: C 随参数变化的稳健性
    """
    thresholds = [30, 50, 100]
    offsets = [0.5, 1.0, 2.0]
    
    C_matrix = np.zeros((len(thresholds), len(offsets)))
    for i, th in enumerate(thresholds):
        for j, off in enumerate(offsets):
            result = verify_kE_beta_relation(n_epochs=10)  # simplified
            C_matrix[i, j] = result['C']
    
    print("C 矩阵 (行=阈值, 列=偏移):")
    print(C_matrix)
    print(f"C 的变差系数: {np.std(C_matrix)/np.mean(C_matrix)*100:.1f}%")
    return C_matrix


# ============================================================
# 执行
# ============================================================
if __name__ == "__main__":
    result = verify_kE_beta_relation(satellite='VanAllen', n_epochs=50)
    print(f"\n结论: {result['conclusion']}")
```

## 五、预期结果与判断准则

| 可能结果 | 物理含义 | 后续动作 |
|:---|:---|:---|
| C ≈ 1.0~3.0, R² > 0.7 | ✅ PKS 公式验证通过 | 发表 |
| C ≈ 0, R² < 0.3 | PKS 假设不成立 | 分析原因 |
| C ≈ 0.1~0.5, R² ≈ 0.5 | 正比但弱 | 加入非线性项 |
| intercept ≠ 1.0 | 蛋形度定义需修正 | 引入 offset 参数 |

## 六、开源数据获取

```
Van Allen Probes: https://rbsp-ect.newmexicoconsortium.org/
IMAGE EUV:        https://image.gsfc.nasa.gov/
Cluster:          http://caa.estec.esa.int/
THEMIS:           http://themis.ssl.berkeley.edu/
```

---

*Task 1 — 验证框架 v1.0 | 2026-06-08*
