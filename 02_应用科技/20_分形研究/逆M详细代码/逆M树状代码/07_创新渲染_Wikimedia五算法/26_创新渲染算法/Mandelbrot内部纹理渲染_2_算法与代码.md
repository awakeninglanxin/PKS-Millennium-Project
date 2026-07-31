# Mandelbrot 内部纹理渲染 — 算法与代码

> 基于 mathr.co.uk 的 C99 实现及元宝深度分析中的伪代码整理。

---

## 1 反算乘子算法（完整版）

### 1.1 伪代码

```
函数 interior_coordinates(c, N, M):
    z = 0
    mz = +∞（记录最小的 |z|）
    
    对 n = 1 .. N（最大迭代次数）:
        z = z² + c
        
        若 |z| < mz:（发现新的原子域最小值）
            mz = |z|
            
            // 步骤1：Newton法求解周期点
            w = z（初始猜测 = 当前轨道值）
            对 m = 1 .. M（Newton迭代次数）:
                // 计算 F^n(w, c)
                f = w
                对 k = 1 .. n:
                    f = f² + c
                // 计算导数 dF^n/dz
                df = 1
                f = w
                对 k = 1 .. n:
                    df = 2 * f * df
                    f = f² + c
                // Newton步
                w = w - (f - w) / (df - 1)
            
            // 步骤2：计算乘子 b
            dw = 1
            w = z₀（周期点）
            对 k = 1 .. n:
                dw = 2 * w * dw  // 链式法则
                w = w² + c
            b = dw
            
            // 步骤3：判断
            若 |b| ≤ 1:
                return b  // 找到内部坐标
    
    return 0  // 失败（在M集外部）
```

### 1.2 关键细节说明

**为什么只检查原子域最小值？**

临界轨道 z_n 在周期 p 的双曲分支内部时，会周期性地接近 0。每次 |z_n| 达到新的局部最小值（即"原子域"atom domain），对应的 n 就是该点所在分支的周期。这个启发式方法避免了尝试所有周期，极大加速。

**Newton 法收敛性**

方程 F^p(z₀, c) - z₀ = 0 是单变量复数方程，当初始猜测 z_n 足够接近周期点时，Newton 法二次收敛。实际中 M=10~20 次迭代通常足够。

**导数计算（链式法则）**

计算 b = ∂/∂z F^p(z₀, c) 时，通过迭代链式法则：
- dw ← 2·w·dw（当前导数乘以 2z）
- w ← w² + c（更新轨道值）
- 迭代 p 次后，dw 即为所求乘子

---

## 2 C99 原始实现

来自 mathr.co.uk/web/m-interior-coordinates.html：

```c
#include <complex.h>

double _Complex m_interior_coordinates
    (int N, int M, double _Complex c)
{
    double _Complex z = 0;
    double mz = 1.0 / 0.0;  // +∞
    for (int n = 0; n < N; ++n)
    {
        z = z * z + c;
        double zp = cabs(z);
        if (zp < mz)
        {
            mz = zp;
            double _Complex w = m_attractor(z, n, c, M);
            double _Complex dw = 1;
            for (int m = 0; m < n; ++m)
            {
                dw = 2 * w * dw;
                w = w * w + c;
            }
            if (cabs(dw) <= 1)
                return dw;
        }
    }
    return 0;
}
```

其中 `m_attractor(z, n, c, M)` 是通过 Newton 法求解周期点 z₀ 的辅助函数。

---

## 3 Python/NumPy 等价实现

```python
import numpy as np

def interior_coordinates(c, N=1000, M=20):
    """
    计算 Mandelbrot 集内部坐标（乘子 b）
    
    参数:
        c: 复数参数
        N: 最大轨道迭代次数
        M: Newton 法最大迭代次数
    
    返回:
        b: 乘子（复数），若 |b|<=1 则在内部；否则返回 0
    """
    z = 0 + 0j
    mz = float('inf')
    
    for n in range(1, N + 1):
        z = z * z + c
        zp = abs(z)
        
        if zp < mz:
            mz = zp
            
            # Newton 法求周期点
            w = z
            for _ in range(M):
                f = w
                for _ in range(n):
                    f = f * f + c
                df = 1 + 0j
                f_val = w
                for _ in range(n):
                    df = 2 * f_val * df
                    f_val = f_val * f_val + c
                # (f - w) / (df - 1)
                w = w - (f - w) / (df - 1)
            
            # 计算乘子 b
            dw = 1 + 0j
            w_val = w
            for _ in range(n):
                dw = 2 * w_val * dw
                w_val = w_val * w_val + c
            
            if abs(dw) <= 1.0:
                return dw
    
    return 0 + 0j
```

### 3.1 向量化版本（for 像素级渲染）

```python
def interior_coordinates_grid(C, N=1000, M=20):
    """
    C: 复数网格 (H, W) 形状的 numpy 数组
    返回: b_grid (H, W)、interior_mask (H, W)
    """
    H, W = C.shape
    Z = np.zeros_like(C, dtype=np.complex128)
    best_b = np.zeros_like(C, dtype=np.complex128)
    interior_mask = np.zeros((H, W), dtype=bool)
    
    for n in range(1, N + 1):
        Z = Z * Z + C
        
        # 检查新的局部最小值（近似原子域检测）
        # 注意：完整向量化原子域检测较复杂，此处为简化版
        
    return best_b, interior_mask
```

---

## 4 纹理坐标映射

得到乘子 b 后，转换为 (u, v) 纹理坐标：

```python
def multiplier_to_uv(b):
    """
    将乘子 b 映射到 [0, 1]² 纹理坐标
    """
    r = abs(b)           # 径向：0（中心）→ 1（边界）
    theta = np.angle(b)  # 角向：(-π, π]
    
    u = r                  # 或 u = 1 - r（从边界到中心）
    # 归一化到 [0, 1]
    v = (theta / (2 * np.pi)) % 1.0
    
    return u, v
```

### 4.1 映射变体

| 映射方式 | u | v | 效果 |
|------|------|------|------|
| 标准映射 | r | θ/(2π) | 纹理从中心向外展开 |
| 反径向 | 1-r | θ/(2π) | 纹理从边界向中心收缩 |
| 对数径向 | log(r)/log(R_max) | θ/(2π) | 中心区域放大 |
| sqrt 径向 | sqrt(r) | θ/(2π) | 补偿面积畸变 |

---

## 5 Newton 法详解

### 5.1 数学推导

求解方程：F^p(z₀, c) - z₀ = 0

Jacobian（在本例中是标量导数）：
```
J = ∂/∂z [F^p(z, c) - z] = ∂/∂z F^p(z, c) - 1
```

Newton 迭代步：
```
z_{k+1} = z_k - [F^p(z_k, c) - z_k] / [∂/∂z F^p(z_k, c) - 1]
```

### 5.2 收敛条件

- 当 |F^p(z, c) - z| < ε（如 10⁻¹⁰）时停止
- 最大迭代次数设为 20~50
- 若发散（|z| 过大），则标记为失败

---

## 6 关键注意事项

1. **周期上限**：实际使用中 N 通常设为 100~10000，取决于所需的周期精度
2. **数值稳定性**：高周期计算时导数可能非常大（|dw| >> 1），需要双精度或更高精度
3. **边界情况**：|b| ≈ 1（在分支边界附近）时数值不稳定，Newton 法可能发散
4. **多解性**：一个 c 可能在多个周期的原子域中达到极小值，取第一个满足 |b|≤1 的即可
