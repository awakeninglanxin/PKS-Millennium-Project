# Koch-8段/32段有理维数曲线 → 平替六角帕斯卡

> 来源: 张大少《分形——雪花与上帝的指纹1》图6.1.10~12
> 核心亮点: 产生有理数分形维数 (D=1.5, D=1.667)，可精确调节

---

## 一、八段曲线 (D = log(8)/log(4) = 1.5)

### 1.1 构造规则

一条线段分4等份 → 中间两段擦去 → 一段向外作正方形，另一段向内作正方形 → 4段变8段。

```
原始: ___ ___ ___ ___   (4段)
      ↑ 外正方 ↑ 内正方
结果: 8段折线 (4 → 8)

迭代: 对每条新线段重复上述操作
```

### 1.2 分形属性

| 属性 | 值 |
|------|------|
| 自相似部分数 | 8 |
| 缩放比 | 1/4 |
| 分形维数 D | log(8)/log(4) = **1.5** |
| 特点 | D 为有理数——这是罕见的 |
| 迭代n次段数 | 8^n |

### 1.3 4条拼接

将4条八段曲线拼接（回旋镖形），形成旋转对称的封闭图案（图6.1.10）。适合 C4 正方形平铺。

---

## 二、三十二段曲线 (D = log(32)/log(8) = 5/3 ≈ 1.667)

### 2.1 构造规则

一条线段分8等份 → 用 32 条折线段替代 → 8段变32段。迭代后形成回旋镖图案（图6.1.11）。

| 属性 | 值 |
|------|------|
| 自相似部分数 | 32 |
| 缩放比 | 1/8 |
| 分形维数 D | log(32)/log(8) = 5/3 ≈ **1.667** |
| 特点 | D 也是有理数 |

---

## 三、五十段曲线 (D ≈ 1.699)

一条线段分10等份 → 用50条折线段替代 → 10段变50段。图6.1.12。

| 属性 | 值 |
|------|------|
| 自相似部分数 | 50 |
| 缩放比 | 1/10 |
| 分形维数 D | log(50)/log(10) ≈ **1.699** |

---

## 四、通用 N→M 段曲线框架

**核心公式**：一条线段分 N 等份，用 M 条折线段替代。

$$\text{分形维数 } D = \frac{\log(M)}{\log(N)}$$

| N | M | D | 视觉效果 |
|------|------|------|------|
| 3 | 4 | 1.262 | 经典 Koch 雪花 |
| 4 | 8 | 1.500 | 哥特式十字条纹 |
| 8 | 32 | 1.667 | 回旋镖 |
| 10 | 50 | 1.699 | 二维码纹样 |
| 4 | 6 | 1.292 | — |
| 5 | 9 | 1.365 | — |
| 6 | 12 | 1.386 | — |

**关键：N 和 M 可自由选择 → D 值可连续逼近任意目标！**

相比 Pascal mod P 的 D(P) = log(P(P+1)/2)/log(P) 只能取离散值，N-M 段曲线提供了**更精细的 D 值选择**。

---

## 五、集成到逆M渲染

### 5.1 LUT 生成

```python
def koch_variant_lut(N_segments, M_segments, pattern_func, depth, N_ROWS):
    """
    通用 Koch 变种 LUT 生成
    N_segments: 原始分段数
    M_segments: 替换后段数
    pattern_func: 折线段形状描述函数 → [(dx0,dy0), (dx1,dy1), ...]
    depth: 迭代深度
    N_ROWS: LUT 尺寸
    """
    # L-system 生成最终线段集合
    segments = generate_l_system(N_segments, M_segments, pattern_func, depth)
    
    # 缩放到 N_ROWS×N_ROWS
    # 离散化: Bresenham 画线到 LUT
    lut = np.zeros((N_ROWS, N_ROWS), dtype=np.int16)
    for (x1,y1),(x2,y2) in segments:
        for (x,y) in bresenham_line(x1,y1,x2,y2):
            if 0 <= x < N_ROWS and 0 <= y < N_ROWS:
                lut[y, x] = 1
    return lut

def generate_l_system(N, M, pattern, depth):
    """
    生成折线曲线段
    pattern: M 个方向向量 [(dx₁,dy₁), ...] (相对坐标, 每段前进1/N)
    """
    segments = [((0,0), (1,0))]  # 初始线段
    for d in range(depth):
        new_segments = []
        for (x1,y1),(x2,y2) in segments:
            dx = x2 - x1; dy = y2 - y1
            # 在 (x1,y1)→(x2,y2) 上应用 pattern
            for pdx, pdy in pattern:
                nx1 = x1 + pdx * dx / N
                ny1 = y1 + pdy * dy / N
                nx2 = nx1 + (dx/N) * (pdx if pdx else 1)
                ny2 = ny1 + (dy/N) * (pdy if pdy else 1)
                new_segments.append(((nx1,ny1), (nx2,ny2)))
        segments = new_segments
    return segments
```

### 5.2 八段曲线的 pattern 定义

```python
# 八段曲线: 4→8, 中间两段替换为向外/向内正方形
pattern_8 = [
    (1, 0),   # 第1段: 保持
    (0, 2),   # 第2段: 上半方 (向外)
    (1, 0),   # — 续
    (0, -2),  # 第3段: 下半方 (向内)
    (1, 0),   # 第4段: 保持
]  # 实际需要精确坐标, 此处示意
```

### 5.3 旋转对称选择

| 曲线 | 拼接数 | 旋转群 | M |
|------|------|------|------|
| 八段 (4条拼) | 4 | C4 | 4 |
| 三十二段 | 4 | C4 | 4 |
| 直角 Koch (4条拼) | 4 | C4 | 4 |
| 皇冠曲线 (图6.1.13) | 6 | C6 | 6 |

---

## 六、调参策略

| 目标 | 操作 |
|------|------|
| 提高 Fill | 增加线宽、减少 depth、增大 N_ROWS 相对缩放 |
| 提高 D | 选择更大的 M/N 比 |
| 降低 D | 选择更小的 M/N 比 |
| 精确控制 D | 选择 N 和 M 使 log(M)/log(N) 接近目标 |
| 纹理更密 | 减小 depth → 段更长更粗 |
| 纹理更细 | 增大 depth → 段更多更细 |
| 避免 Möbius 拉伸失真 | 正方形LUT → 映射到 interior 前预先拉伸补偿 |

---

## 七、与 Pascal 的互补优势

| 维度 | Pascal mod P | Koch N→M 段 |
|------|------|------|
| D 值连续性 | 离散 (只有素数 P 可用) | **准连续** (N,M 自由选择) |
| 有理数 D | 罕见 | **大量有理 D** |
| 纹理类型 | 三角孔洞 | 折线/条纹 |
| LUT 生成速度 | 极快 (O(N²)递推) | 较慢 (L-system O(M^depth)) |
| 视觉多样性 | 一种基底 | **无限种** (pattern 自由定义) |

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
