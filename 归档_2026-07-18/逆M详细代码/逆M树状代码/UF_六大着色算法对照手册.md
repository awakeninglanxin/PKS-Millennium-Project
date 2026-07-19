# UF 逆M 六大着色算法对照手册

> 对应 Ultra Fractal Standard.ucl 着色算法体系
> 已在 Python/NumPy 中完整复现

---

## 算法总览

| # | UF 着色入口 | 视觉效果 | Python 实现 |
|:---:|:---|:---|:---|
| 1 | BinaryDecomposition Type 1 | 黑白棋盘格三角网 | `1_二分棋盘格素描/main.py` |
| 2 | Smooth (Continuous Potential) | 蓝紫丝滑流光 | `2_连续势能流光/main.py` |
| 3 | External Rays | 树状分叉叶脉 | `3_有理外部射线/main.py` |
| 4 | DEM (Distance Estimator) | 钢笔墨线白描 | `4_距离估计壳线/main.py` |
| 5 | Orbit Traps | 环形几何纹理 | `5_轨道陷阱网格/main.py` |
| 6 | Topological Decomposition | 教堂穹顶镶嵌 | `6_拓扑交错瓦片/main.py` |

---

## 1. Binary Decomposition

**UF等效**: `Standard.ucl entry="BinaryDecomposition" p_type="Type 1"`

**数学**: $\lfloor\theta \cdot N\rfloor \bmod 2$ XOR $\lfloor\text{pot}/\Delta\rfloor \bmod 2$

| 参数 | 推荐值 | 效果 |
|:---|:---|:---|
| RAY_DIV | 64 | 外圈粗格; 32=更粗 |
| POT_STEP | 0.12 | 等势圈密度 |

---

## 2. Smooth Potential

**UF等效**: `Standard.ucl entry="Smooth" p_power=2/0`

**数学**: $\nu = n - \log_2(\log_2(|z|))$ 映射到连续色板

---

## 3. External Rays

**数学**: $\theta = \arg(z) / (2\pi \cdot 2^n) \bmod 1$, 检查 $|\theta N - \text{round}(\theta N)| < \varepsilon$

| 参数 | 推荐值 |
|:---|:---|
| RAY_CNT | 32 |
| LTH | 0.03 |

---

## 4. Distance Estimator (DEM)

**数学**: $z_{n+1}=z_n^2+c$, $dz_{n+1}=2z_n\cdot dz_n+1$, 逃逸后 $d = |z|\ln|z|/(2|dz|)$

---

## 5. Orbit Traps

**数学**: $d_{\min} = \min_n ||z_n| - R|$, 频率 ×8.0 映射到 sin 渐变

---

## 6. Topological Decomposition

**数学**: $u = \lfloor\theta N\rfloor$, $v = \lfloor\text{pot}/\Delta\rfloor$, $i = (u+v)\bmod K$, 用 $i$ 索引调色板

| 参数 | 值 |
|:---|:---|
| RAY_DIV | 64 |
| POT_STEP | 0.06 |
| K (色数) | 6 |

---

## 通用反演空间处理

```python
interior |= (np.abs(w) < 0.02)  # w≈0 → 强制 interior (消除葫芦残影)
```

| bailout | 适用算法 |
|:---|:---|
| 128 | 1, 2, 6 |
| 100000 | 3, 4, 5 |
