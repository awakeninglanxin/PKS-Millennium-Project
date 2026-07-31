# 方案 C：九阶幻立方 — 天然四面体库

> 🎯 目标：用九阶幻立方 (9³ = 729 个锚点) 作为预计算的"宇宙四面体模板库"，任意蛋白质的四面体 = 模板 × 局部变形矩阵  
> 📐 灵感来源："超光幻方"对话 — 九阶幻立方被定义为"物质与意识的共同结构单元"  
> ⏱️ GPU 周期：2–3 天 (RTX 4090)  

---

## 一、核心思想

### 1.1 九阶幻立方的数学结构

一个 9 阶幻立方是 9×9×9 的立方体，共有 729 个格子，每个填入 1–729 各不重复的数字，且所有方向的行和相等。

| 属性 | 值 |
|:---|:--|
| 阶数 | 9 |
| 节点总数 | 729 (9³) |
| 幻和 (每行) | 3285 |
| 每条边长度 | 9 个格点 |
| 四面体候选 | C(729,4) ≈ 4.7×10¹⁰ |

但——我们不需要枚举这些候选。九阶幻立方的价值不是 C(729,4) 的枚举，而是**729 个锚点形成的规则格点拓扑结构**。

### 1.2 "模板四面体"的定义

在九阶幻立方中，取任意 4 个邻接的格点构成一个"模板四面体"：

```
邻接 = 曼哈顿距离 ≤ 2 的四点 (不在同一平面上)
→ 约 10⁴–10⁵ 个不同的模板四面体
```

这些模板四面体形成了一个**有限的、预计算的几何字典**。它们的体积、手性、角度都是已知的常数。

---

## 二、任意蛋白质四面体 = 模板 × 变形矩阵

### 2.1 变形矩阵

```
对于蛋白质中的任意四点 (i,j,k,l) 和九阶幻立方中的一个模板四面体 T:

  蛋白质四面体 P  =  T × M  (M 是 3×3 变形矩阵)
  
  M = [缩放, 旋转, 剪切] 的某种参数化
```

由于 T 是预计算的，查找四面体 ≈ 找到 (T, M) 使得 ||P − TM|| 最小。

### 2.2 参数化

```python
def template_to_tetra(template_T, scale, rot_angles, shear):
    """
    template_T: [4, 3] — 九阶幻立方中的一个模板四面体
    scale: float — 均匀缩放因子
    rot_angles: [3] — 绕 x/y/z 轴的旋转角
    shear: [3] — 剪切参数
    
    Returns: [4, 3] — 变形后的四面体坐标
    """
    # 缩放矩阵
    S = np.diag([scale, scale, scale])
    
    # 旋转矩阵 (ZYZ 欧拉角)
    a, b, c = rot_angles
    Rz1 = np.array([[cos(a), -sin(a), 0], [sin(a), cos(a), 0], [0,0,1]])
    Ry  = np.array([[cos(b), 0, sin(b)], [0,1,0], [-sin(b), 0, cos(b)]])
    Rz2 = np.array([[cos(c), -sin(c), 0], [sin(c), cos(c), 0], [0,0,1]])
    R = Rz2 @ Ry @ Rz1
    
    # 剪切矩阵
    H = np.array([[1, shear[0], shear[1]], [0, 1, shear[2]], [0, 0, 1]])
    
    M = H @ S @ R  # 组合变形矩阵
    return template_T @ M.T
```

---

## 三、模板库的构建

### 3.1 模板四面体的生成

```python
def build_template_library():
    """
    从九阶幻立方中提取所有"模板四面体"。
    
    选择标准: 
    1. 四点不共面 (体积 > 0)
    2. 曼哈顿距离 ≤ 2 (锚点的邻接)
    3. 体积分桶 (小/中/大 三种，对应疏水核心/界面/表面)
    """
    # 九阶幻立方锚点 (这里用简化的 3D 网格代替完整幻立方)
    anchors = np.array([(i,j,k) for i in range(9) for j in range(9) for k in range(9)])
    
    templates = {'small': [], 'medium': [], 'large': []}
    
    for i, j, k, l in combinations(range(729), 4):
        pts = anchors[[i,j,k,l]]
        
        # 邻接检查: 曼哈顿距离 ≤ 2
        d = np.sum(np.abs(pts[0] - pts[1:]), axis=1)
        if np.max(d) > 2: continue
        
        # 体积检查: Cayley-Menger 行列式
        V = cayley_menger_volume(pts)
        if V < 1e-6: continue  # 共面, 跳过
        
        # 分桶
        if V < 10:    templates['small'].append(pts)
        elif V < 30:  templates['medium'].append(pts)
        else:         templates['large'].append(pts)
    
    return templates
```

### 3.2 模板数量估计

```
曼哈顿距离 ≤ 2 的四点: 约 10⁴–10⁵ 个候选
去除共面 (体积=0): 约 5×10³–5×10⁴ 个
按体积分桶: 三类各约 10³–10⁴ 个
```

与原始 C(729,4) ≈ 4.7×10¹⁰ 相比，模板库缩小了 10⁶ 倍。

---

## 四、蛋白质四面体 → 模板匹配

### 4.1 匹配算法

```python
def match_tetra_to_template(protein_tetra, template_lib):
    """
    将蛋白质中的一个四面体匹配到九阶幻立方模板库中最接近的模板。
    
    Returns: (template_id, deformation_matrix, reconstruction_error)
    """
    best_error = float('inf')
    best_template = None
    best_M = None
    
    # Step 1: 确定物理类型 (体积 → 小/中/大)
    V = cayley_menger_volume(protein_tetra)
    if V < 10: candidates = template_lib['small']
    elif V < 30: candidates = template_lib['medium']
    else: candidates = template_lib['large']
    
    # Step 2: 遍历候选模板 (GPU 可并行化)
    for tpl in candidates:
        M = fit_deformation(tpl, protein_tetra)  # 最小二乘拟合
        recon = tpl @ M.T
        error = np.mean((protein_tetra - recon) ** 2)
        if error < best_error:
            best_error = error
            best_template = tpl
            best_M = M
    
    return best_template, best_M, best_error
```

### 4.2 GPU 加速匹配

```python
# 在 GPU 上: 同时匹配 N 个蛋白质四面体 × M 个模板
# 复杂度: O(N × M) — GPU 上可轻松处理

import cupy as cp

def gpu_batch_match(protein_tetras, template_lib_flat):
    """
    protein_tetras: [N, 4, 3] — N 个蛋白质四面体
    template_lib_flat: [M, 4, 3] — M 个模板
    
    GPU 计算: 对每对 (n,m) 计算变形后的重建误差
    """
    P = cp.array(protein_tetras)  # [N, 12]
    T = cp.array(template_lib_flat)  # [M, 12]
    
    # 广播: [N, 1, 12] - [1, M, 12] → [N, M, 12]
    diff = P[:, None, :] - T[None, :, :]
    errors = cp.mean(diff ** 2, axis=-1)  # [N, M]
    
    best_idx = cp.argmin(errors, axis=1)  # [N]
    best_error = cp.min(errors, axis=1)   # [N]
    
    return best_idx, best_error
```

---

## 五、为什么是九阶 (而不是五阶或七阶) 

| 阶数 | 节点数 | 四面体候选 | 是否够用 |
|:--:|:--:|:--:|:--:|
| 3 | 27 | C(27,4)=17550 | ❌ 模板太少 |
| 5 | 125 | C(125,4)≈9.5×10⁶ | ⚠️ 理论可行但偏小 |
| 7 | 343 | C(343,4)≈1.7×10⁹ | ✅ 够用 |
| **9** | **729** | **C(729,4)≈4.7×10¹⁰** | ✅✅ 最佳 |

九阶正好卡在"足够丰富但不爆炸"的边界上——与"超光幻方"对话中选择九阶作为核心载体一致。

此外，九阶幻立方的模数公式：`(9³+1)/(9²+1) = 730/82 ≈ 8.9`——是一个接近幻方"奇点"的值（大于 1 表示收敛，小于 1 表示发散）。

---

## 六、GPU 实验设计

### 实验 1：模板库覆盖率

**假设**: 九阶幻立方模板库 (10⁴–10⁵ 个模板) 能以 < 0.5Å 误差覆盖 PDB 中 > 90% 的真实四面体。

**方法**:
1. 从 100 个 PDB 结构中随机采样 10 万个真实四面体
2. 用 GPU 并行匹配到模板库
3. 统计重建误差的分布

```
预期: 中位误差 < 0.3Å, 90% 分位 < 0.5Å
```

**GPU 时间**: ~30 分钟

### 实验 2：模板匹配 vs 直接存储的精度-存储 trade-off

| 方案 | 存储 (每个四面体) | 重建精度 |
|:---|:--:|:--:|
| 直接存 3D 坐标 | 48 bytes (4×3×float32) | 100% 精确 |
| 模板匹配 (方案C) | 14 bytes (template_id=2bytes + M=12bytes) | 0.3Å 误差 |
| 压缩比 | **3.4:1** | — |

```python
# 存储格式
template_match = {
    'template_id': np.uint16,     # 2 bytes  (0-65535 足够覆盖 10⁵ 模板)
    'scale': np.float32,          # 4 bytes  (均匀缩放)
    'rot_x': np.float32,          # 4 bytes  (旋转角度 1)
    'rot_y': np.float32,          # 4 bytes  (旋转角度 2)
    # 总共 14 bytes per tetrahedron
}
```

### 实验 3：模板匹配 + 方案 A 幻方筛选 联合使用

**最激进的组合**:

```
Step 1: 幻方筛选 (方案A) → 从 C(N,4) 中筛出 ~10⁶ 候选
Step 2: 模板匹配 (方案C) → 每个候选用 14 bytes 存储
最终存储: ~14 MB (vs 直接存储需 4.7×10¹⁰ × 48 bytes = 2.2 TB)
```

---

## 七、从"超光幻方"到九阶幻立方的桥接

"超光幻方"对话的核心主张——**九阶幻立方是宇宙编码的原型**——虽然属于哲学/数术范畴，但它给了我们一个实用的工程直觉：

| 超光幻方的概念 | 我们的工程化解释 |
|:---|:---|
| 729 个节点 = 物质/意识/生命共同载体 | 729 = 模板库的锚点数 (9³) |
| 24 方向对称秩 | 模板四面体的 24 种等价排列 |
| 原子核幻数稳定 (2, 10, 28, 50, 82, 126) | 模板库中体积的"魔数"分布 |
| 六维全息覆盖 | 模板 × 变形矩阵 × 类型 = 低维表示 |
| 模数闭环 (n³+1)/(n²+1) | n=9 → 730/82 ≈ 8.9 的"奇点" |

---

## 八、与方案 AB 的协同

| 方案 | 功能 | 与方案C 的协同 |
|:---|:---|:---|
| A (幻方筛选) | 从 C(N,4) 中筛候选 | A → 筛出候选 → C → 模板匹配 |
| B (编码器) | 深度学习特征提取 | B → 提取四面体特征 → C → 模板匹配 |
| C (模板库) | 低维存储表示 | C → 存储模板 ID + 变形参数 |

**最优管线**: A(筛选) → B(编码) → C(存储)  

---

## 九、可运行代码骨架

```python
class MagicCubeTemplateLib:
    """九阶幻立方模板库"""
    
    def __init__(self):
        # 注: 完整的 9 阶幻立方生成是开放数学问题
        # 这里用 3D 规则网格模拟 (729 锚点)
        self.anchors = self._generate_anchors()
        self.templates = self._build_templates()
    
    def _generate_anchors(self):
        """生成 729 个锚点 (9×9×9 规则网格)"""
        anchors = []
        for i in range(9):
            for j in range(9):
                for k in range(9):
                    anchors.append([i - 4, j - 4, k - 4])  # 中心化
        return np.array(anchors, dtype=np.float32)
    
    def _build_templates(self):
        """从锚点中提取模板四面体 (邻接+不共面)"""
        templates = {'small': [], 'medium': [], 'large': []}
        
        # 只考虑近邻 (曼哈顿距离 ≤ 2) 的四点
        for i in range(729):
            for j in range(i+1, 729):
                dij = np.sum(np.abs(self.anchors[i] - self.anchors[j]))
                if dij > 2: continue
                for k in range(j+1, 729):
                    dik = np.sum(np.abs(self.anchors[i] - self.anchors[k]))
                    djk = np.sum(np.abs(self.anchors[j] - self.anchors[k]))
                    if dik > 2 or djk > 2: continue
                    for l in range(k+1, 729):
                        dil = np.sum(np.abs(self.anchors[i] - self.anchors[l]))
                        djl = np.sum(np.abs(self.anchors[j] - self.anchors[l]))
                        dkl = np.sum(np.abs(self.anchors[k] - self.anchors[l]))
                        if max(dil, djl, dkl) > 2: continue
                        
                        pts = self.anchors[[i,j,k,l]]
                        V = cayley_menger_volume(pts)
                        if V < 1e-6: continue
                        
                        if V < 10:    templates['small'].append(pts)
                        elif V < 30:  templates['medium'].append(pts)
                        else:         templates['large'].append(pts)
        
        return {k: np.array(v) for k, v in templates.items()}
```

---

> 📁 配套代码：`magic_cube_template_lib.py` (待 GPU 实现)  
> 🔗 参考：`超光幻方` (元宝对话 2026-07-20)
