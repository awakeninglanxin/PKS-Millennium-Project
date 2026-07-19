# IFS L2+L3 展开研究路线图：从零到可运行

> 问题：L2(比例精评)和L3(动力学终审)目前是算法空白——如何落地？
> 日期：2026-07-19

---

## 零、核心前提：整个IFS不需要训练数据

现有AI审美需要LAION-5B。IFS只需要：
1. **MediaPipe 17个身体关键点**（提取比例向量）
2. **纯数学计算**（7族评分函数）

不需要GPU训练。本机CPU毫秒级。

---

## L2：比例精评（权重40%）—— 4个子模块

### L2.1 Feigenbaum δ 发育质量检测器

**输入**：从头顶到足底的关键点垂直坐标序列 Y = [y₀, y₁, ..., yₙ]

**算法**：

```
将身体沿垂直轴分为 N 层（推荐 N=5：头/颈肩/躯干/大腿/小腿）
对每个相邻分界点 (y_k, y_{k+1}) 计算分岔间距：
  d_k = y_{k+1} - y_k

计算间距比：
  δ_measured[k] = d_k / d_{k+1}   for k=1 to N-2

Feigenbaum 评分：
  L2_δ = exp( -Σ|δ_measured[k] - 4.669|² / (2σ²) )
```

**Python伪代码**：

```python
def feigenbaum_score(keypoints):
    # keypoints = [(x_i, y_i), ...] from MediaPipe
    y_sorted = sorted(set(k[1] for k in keypoints), reverse=True)
    # 分5层
    n_layers = 5
    bounds = np.linspace(0, len(y_sorted)-1, n_layers+1, dtype=int)
    d = [y_sorted[bounds[i]] - y_sorted[bounds[i+1]] for i in range(n_layers)]
    
    delta_measured = []
    for i in range(len(d)-2):
        if d[i+1] > 1e-6:
            delta_measured.append(d[i] / d[i+1])
    
    delta_ref = 4.669
    return np.exp(-np.mean([(dm - delta_ref)**2 / (2*0.3**2) for dm in delta_measured]))
```

**验证方法**：对已知的"发育异常"照片（如马凡综合征→肢端过长）和正常照片，检查L2_δ是否有显著差异。

---

### L2.2 Farey树 Fibonacci 链收敛检测器

**输入**：从17个关键点提取的比例向量 P = [p₁, p₂, ..., pₘ]

比例包括：
- p₁ = 身高/肚脐高
- p₂ = 上臂/前臂
- p₃ = 大腿/小腿
- p₄ = 手长/指长
- p₅ = 面长/面宽
- ...

**算法**：

```
对每个比例 pᵢ：
1. 找到 pᵢ 在 Farey 树中的最近节点 a/b（二分搜索 Farey 树）
2. 检查 a/b 是否在 Fibonacci 路径上：
   Fibonacci路径 = {1/2, 2/3, 3/5, 5/8, 8/13, 13/21, ...}
3. 计分：在Fibonacci路径上=满分，不在=Farey距离衰减

L2_φ = Σ wᵢ · exp( -min|pᵢ - F_k/F_{k+1}|² / (2σ²) )
```

**Farey树二分搜索**：

```python
def farey_nearest(target, max_denom=144):
    """在Farey树中找到最接近 target 的有理数"""
    lo_n, lo_d = 0, 1
    hi_n, hi_d = 1, 1
    best_n, best_d = 0, 1
    best_err = float('inf')
    
    while lo_d + hi_d <= max_denom:
        mid_n, mid_d = lo_n + hi_n, lo_d + hi_d
        mid_val = mid_n / mid_d
        err = abs(mid_val - target)
        if err < best_err:
            best_err = err
            best_n, best_d = mid_n, mid_d
        
        if target < mid_val:
            hi_n, hi_d = mid_n, mid_d
        else:
            lo_n, lo_d = mid_n, mid_d
    
    return best_n, best_d, best_err

def is_on_fibonacci_path(num, den):
    """检查 p/q 是否在Fibonacci路径上"""
    fib = [(1,2), (2,3), (3,5), (5,8), (8,13), (13,21), (21,34), (34,55)]
    return (num, den) in fib

def farey_fibonacci_score(proportions):
    """比例向量的Fibonacci一致性评分"""
    score = 0
    for p in proportions:
        n, d, err = farey_nearest(p)
        fib_bonus = 1.5 if is_on_fibonacci_path(n, d) else 1.0
        score += fib_bonus * np.exp(-err**2 / (2*0.05**2))
    return score / len(proportions)
```

**关键**：这个算法不检测"pᵢ是否等于φ"——它检测的是"pᵢ的有理近似是否在Fibonacci路径上"。这解决了"统计找不到φ"的问题——因为检测目标从"无理数收敛"改为"有理逼近路径的一致性"。

---

### L2.3 Kneading序列生成器

**输入**：比例向量 P = [p₁, p₂, ..., pₘ]

**算法**：

```
对每个比例 pᵢ：
  if |pᵢ - φ| < ε → 符号 = ★ (恰好)
  elif pᵢ > φ   → 符号 = 1 (偏大)
  else           → 符号 = 0 (偏小)

得到 Kneading 序列 K = [k₁, k₂, ..., kₘ]  每个 kᵢ ∈ {★, 1, 0}

理想序列 = ★★★★★★★★★★★★ (全部恰好)
周期序列 = ★101̄ (规则交替，有风格)
混沌序列 = 101101011... (无规律)

L2_K = ★的占比 × 规律性得分
```

**规律性检测**（用Lempel-Ziv复杂度）：

```python
def kneading_score(proportions, phi=1.618, eps=0.03):
    """生成Kneading序列并评分"""
    seq = ''
    for p in proportions:
        if abs(p - phi) < eps:
            seq += '*'
        elif p > phi:
            seq += '1'
        else:
            seq += '0'
    
    # ★占比
    star_ratio = seq.count('*') / len(seq)
    
    # 用LZ复杂度检测规律性（排除★后）
    binary = seq.replace('*', '')
    if len(binary) > 3:
        lz = lempel_ziv_complexity(binary)
        lz_norm = lz / (len(binary) / np.log2(len(binary)))
        regularity = 1.0 - min(lz_norm, 1.0)
    else:
        regularity = 1.0
    
    return 0.5 * star_ratio + 0.5 * regularity

def lempel_ziv_complexity(s):
    """Lempel-Ziv复杂度"""
    i, n = 0, len(s)
    C = 1
    while i < n:
        l = 1
        while i + l <= n and s[i:i+l] in s[:i+l-1]:
            l += 1
        if i + l > n:
            break
        C += 1
        i += l
    return C
```

---

### L2.4 Internal Address 比较器

**输入**：从17个关键点构建的层级比例树

**算法**：

```
1. 构建身体比例树（根=整体比例，第1层=躯干/头部，第2层=上肢/下肢/面/颅...）
2. 对每一层每个节点的比例，找到它的Farey分数
3. 按层拼接成 Internal Address 字符串
4. 与理想 Internal Address 的编辑距离 = L2_IA得分
```

```python
def internal_address(proportion_tree):
    """
    比例树: {
      'root': {'overall': 1.618},
      'layer1': {
        'trunk': {'upper': 1.58, 'lower': 1.62},
        'head': {'face': 1.60, 'cranium': 1.55}
      },
      'layer2': { ... }
    }
    """
    address = ['1']  # 根节点
    
    def traverse(node, depth):
        for key, val in node.items():
            if isinstance(val, dict):
                n, d, _ = farey_nearest(val.get('ratio', 1.5))
                address.append(f"{n}/{d}")
                traverse(val, depth+1)
    
    traverse(proportion_tree, 0)
    return '→'.join(address)

def ia_score(actual_address, ideal_address):
    """Internal Address 编辑距离评分"""
    # 理想地址 = "1→1/2→1/3→2/5→3/8→5/13→..."
    dist = levenshtein(actual_address, ideal_address)
    max_len = max(len(actual_address), len(ideal_address))
    return 1.0 - dist / max_len
```

---

## L3：动力学终审（权重25%）—— 3个子模块

### L3.1 Misiurewicz不对称扭点检测器

**输入**：关键点的左右差值向量

**算法**：

```
对每个双侧关键点对 (L_i, R_i)：
  d_i = |L_i.position - R_i.position|  # 不对称量
  
按从上到下的顺序排列 d_i：
  扫描 d 序列，找到第一个 d_i > 阈值的位置 → 前周期 k
  继续扫描，看后续的 d 是否周期性重复 → 周期 p
  
L3_M = 1 / (1 + k·p/10)
```

```python
def misiurewicz_score(keypoints_left, keypoints_right, threshold=0.03):
    """Misiurewicz不对称扭点评分"""
    n = len(keypoints_left)
    diffs = [np.linalg.norm(L[i] - R[i]) / body_height 
             for i in range(n)]
    
    # 找前周期k：第一个显著不对称点
    k = n  # 默认=完全对称
    for i in range(n):
        if diffs[i] > threshold:
            k = i
            break
    
    # 找周期p：后续不对称是否周期性重复
    p = 1  # 默认=无周期(仅一次偏移)
    if k < n:
        remaining = diffs[k:]
        # 自相关检测周期
        p = detect_period(remaining)
    
    # k·p 越小=偏差越早越明显
    return 1.0 / (1.0 + k * p / 10.0)
```

---

### L3.2 逆M水滴收敛检测器

**输入**：身体轮廓的二值化剪影（从关键点插值生成）

**算法（五公理瀑布）**：

```
公理1 紧致性：检测轮廓是否连续闭合
  → Euler示性数 χ = V-E+F = 1（单连通）=通过

公理2 层级自相似：不同尺度的轮廓Hausdorff维数是否一致
  → 全长尺(1:1) vs 半身尺(1:2) vs 局部尺(1:4)的 d_H 标准差
  → std越小 = 自相似越好

公理3 曲率平滑：沿轮廓的曲率变化速率
  → κ'(s) 的积分 = 曲率变化总量
  → 越小 = 越平滑

公理4 Kolmogorov简约：用最少的Farey参数描述轮廓
  → 轮廓可以用多少Farey节点精确拟合？
  → 越少的节点 = 越简约

公理5 物理可嵌入：轮廓是否在人体力学约束内
  → 关节角度 ∈ [生理范围]？
  → 全部通过 = 1.0

L3_waterdrop = 五项乘积
```

```python
def waterdrop_five_axioms(contour_points, joint_angles):
    """逆M水滴五公理综合评分"""
    scores = {}
    
    # 公理1: 紧致性
    chi = euler_characteristic(contour_points)
    scores['compactness'] = 1.0 if chi == 1 else 0.0
    
    # 公理2: 层级自相似
    d_h_full = hausdorff_dim(contour_points, scale=1.0)
    d_h_half = hausdorff_dim(contour_points[:len(contour_points)//2], scale=0.5)
    d_h_quarter = hausdorff_dim(contour_points[:len(contour_points)//4], scale=0.25)
    dh_std = np.std([d_h_full, d_h_half, d_h_quarter])
    scores['self_similarity'] = np.exp(-dh_std**2 / (2*0.05**2))
    
    # 公理3: 曲率平滑
    curvatures = compute_curvature(contour_points)
    curvature_variation = np.sum(np.abs(np.diff(curvatures)))
    scores['smooth_curvature'] = np.exp(-curvature_variation / (len(contour_points)*0.1))
    
    # 公理4: Kolmogorov简约
    n_farey_nodes = count_farey_fit(contour_points)
    scores['minimality'] = np.exp(-(n_farey_nodes - 7)**2 / (2*3**2))
    
    # 公理5: 物理可嵌入
    phys_ok = all(angle_min <= a <= angle_max for a in joint_angles)
    scores['embeddability'] = 1.0 if phys_ok else 0.5
    
    return np.prod(list(scores.values())), scores
```

---

### L3.3 全局 Lyapunov 敏感度调整

```python
def lyapunov_adjustment(proportions, attractor_basin=1):
    """
    attractor_basin: 1=希腊经典, 2=文艺复兴, 3=唐风, ...
    不同盆地的λ不同 → 相同偏差在不同风格下扣分不同
    """
    lambda_map = {1: 0.15, 2: 0.10, 3: 0.05, 4: 0.18, 5: 0.03, 6: 0.08, 7: 0.06}
    lam = lambda_map.get(attractor_basin, 0.10)
    
    # 偏差被λ放大
    total_deviation = sum(abs(p - 1.618) for p in proportions) / len(proportions)
    return np.exp(-lam * total_deviation**2 / (2*0.02**2))
```

---

## 完整IFS评分流水线

```python
def ifs_score(image_path):
    """
    输入：一张人体照片
    输出：IFS评分(0-100) + 七维分量
    """
    # Step 0: 关键点提取（MediaPipe）
    keypoints = mediapipe_extract(image_path)
    proportions = compute_proportions(keypoints)
    contour = build_contour(keypoints)
    joints = extract_joint_angles(keypoints)
    
    # L0: 拓扑粗筛
    topo_ok = check_topology(keypoints)  # 手指数/四肢数/五官数
    if not topo_ok:
        return {'score': 0, 'reason': 'L0 topology fail'}
    
    # L1: 结构检测（现有AI，简化版）
    l1_sym = symmetry_score(keypoints)       # Z₂双侧
    l1_clarity = laplacian_variance(image_path)
    l1_color = hsv_entropy(image_path)
    L1 = 0.40 * l1_sym + 0.30 * l1_clarity + 0.30 * l1_color
    
    # L2: 比例精评（IFS新增）
    l2_delta = feigenbaum_score(keypoints)
    l2_farey = farey_fibonacci_score(proportions)
    l2_kneading = kneading_score(proportions)
    l2_ia = ia_score(build_address(proportions), IDEAL_ADDRESS)
    L2 = 0.25 * l2_delta + 0.35 * l2_farey + 0.20 * l2_kneading + 0.20 * l2_ia
    
    # L3: 动力学终审（IFS新增）
    l3_mis = misiurewicz_score(keypoints['left'], keypoints['right'])
    l3_waterdrop, _ = waterdrop_five_axioms(contour, joints)
    l3_lyap = lyapunov_adjustment(proportions)
    L3 = 0.35 * l3_mis + 0.40 * l3_waterdrop + 0.25 * l3_lyap
    
    # 总分
    IFS = 100 * (0.35 * L1 + 0.40 * L2 + 0.25 * L3)
    
    return {
        'score': round(IFS, 1),
        'components': {
            'L1_structure': round(L1, 3),
            'L2_proportion': round(L2, 3),
            'L3_dynamics': round(L3, 3),
        },
        'details': {
            'delta': round(l2_delta, 3),
            'farey_fib': round(l2_farey, 3),
            'kneading_seq': kneading_sequence(proportions),
            'misiurewicz_kp': (k, p),
            'waterdrop_axioms': {k: round(v, 3) for k, v in scores.items()},
        }
    }
```

---

## 分阶段实施计划

| 阶段 | 内容 | 依赖 | 产出 | 预计 |
|:---|:---|:---|:---|:---:|
| P0 | MediaPipe关键点提取+比例向量计算 | opencv+mediapipe | `extract_proportions.py` | 1h |
| P1 | L2.2 Farey树Fibonacci检测器 | P0 | `farey_fib_scorer.py` | 2h |
| P2 | L2.3 Kneading序列生成器 | P0 | `kneading_scorer.py` | 1h |
| P3 | L2.1 Feigenbaum δ检测器 | P0 | `feigenbaum_scorer.py` | 1h |
| P4 | L2.4 Internal Address比较器 | P0+P1 | `ia_scorer.py` | 2h |
| P5 | L3.1 Misiurewicz扭点检测器 | P0 | `misiurewicz_scorer.py` | 1h |
| P6 | L3.2 逆M水滴五公理 | P0+contour | `waterdrop_scorer.py` | 3h |
| P7 | 完整流水线+可视化报告 | P0-P6 | `ifs_pipeline.py` + HTML | 3h |
| P8 | 对照实验: IFS vs CLIP在30张图中 | P7 | `ifs_vs_clip_benchmark.md` | 2h |

---

## 与现有AI的集成方式

不替代——嵌入：

```python
# 现有AI评分（慈海九宫格式）
ai_score = quality_pipeline(image)  # 0.70合格

# 仅在通过L0+L1后启用IFS
if ai_score >= 0.70:
    ifs_result = ifs_score(image)
    # 合并到最终报告
    final_report = {
        'ai_score': ai_score,          # 结构完整性
        'ifs_score': ifs_result['score'],  # 比例优美度
        'ifs_breakdown': ifs_result['components'],
        'recommendation': 'excellent' if ifs_result['score'] > 90 else 'good'
    }
```

---

## 核心创新：零数据依赖

| | CLIP/FID | IFS |
|:---|:---:|:---:|
| 训练数据 | LAION-5B (5B张图) | **0张** |
| GPU需求 | A100 × 8 | **不需要** |
| 运行时间 | 秒级(推理) | 毫秒级(纯数学) |
| 可解释性 | 768维隐向量 | 7维明确指标 |
| 文化偏见 | 训练数据分布 | Farey树是普适数学 |
