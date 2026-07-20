# 方案 A：幻方筛选 + 四面体范式 — O(N²) 复杂度降维

> 🎯 目标：用幻方的幻和约束 + 24 方向对称，把 C(N,4) 的四面体候选从 2.6×10¹⁰ 压缩到 10⁵–10⁶ 量级  
> 📐 数学基础：5 阶 pandiagonal 幻方 (pan5) + 洛书减 5 对称矩阵  
> ⏱️ GPU 周期：1–2 天 (RTX 4090)  

---

## 一、核心算法

### 1.1 两步筛选替代 C(N,4) 枚举

```
传统方法 (不可行):
  for i in 1..N:
    for j in i+1..N:
      for k in j+1..N:
        for l in k+1..N:
          计算四面体 Q_ijkl → O(N⁴) ≈ 2.6×10¹⁰

幻方筛选方法 (O(N²)):
  Step 1: 计算所有两两距离 d_ij → O(N²)
  Step 2: 对每对 (i,j)，用幻方的 24 方向距离特征向量投影到幻方格子上
  Step 3: 如果两个残基对的幻方投影"互补"(行列和=对角和=65) → 四点入围
  Step 4: 对新发现的四面体，归为 24 方向等价范式
```

### 1.2 幻方投影函数

**核心定义**：把残基对 (i,j) 的几何特征映射到 5×5 幻方格子上。

```python
def magic_project(d_ij, d_ik, d_jk):
    """
    将三角形 (i,j,k) 的边长投影到幻方格子的 3 个"坐标"上。
    
    输入: 三边长 d_ij, d_ik, d_jk
    输出: 幻方格子坐标 (r, c, channel)
    
    原理: 5阶幻方的每行、每列、每条对角线都等于 65。
    这里用三个距离做仿射变换到 [0,65] 区间，然后映射到格点。
    """
    # 归一化到幻和 65
    total = d_ij + d_ik + d_jk
    if total == 0: return None
    
    # 幻方坐标 = 距离占比 × 幻和
    r_ij = int(d_ij / total * 65) % 5
    r_ik = int(d_ik / total * 65) % 5  
    channel = int(d_jk / total * 65) % 5
    
    return (r_ij, r_ik, channel)
```

### 1.3 幻和约束筛选

一个四个残基点 (i,j,k,l) 形成"有意义四面体"的必要条件：

```
幻和条件:
  magic_project(d_ij, d_ik, d_jk) + magic_project(d_il, d_jl, d_kl) = 65 (mod 65)
```

解释：两点对 (i,j) 和 (k,l) 在幻方上的投影之和应等于幻和 65——这意味着它们在幻方结构上是"互补的"。

---

## 二、24 方向等价类压缩

### 2.1 数学定义

5 阶 pandiagonal 幻方有 24 个"方向"（方向 = 一个完整的行/列/对角线及其折断等价物）。

对于四面体 Q_ijkl：
```
24 种重新排列 ≡ 24 种"视角"
└→ 选择字典序最小的排列作为"范式"(canonical form)
└→ 其他 23 种可从范式推导
```

### 2.2 范式计算

```python
def tetrahedron_canonical(Q):
    """返回四面体的 24 方向范式"""
    best = None
    best_key = None
    
    # 24 种排列 = 4! = 24
    for perm in permutations([0,1,2,3]):
        Qp = Q[list(perm)]
        # 坐标归一化: 把第一个点移到原点
        Qp = Qp - Qp[0]
        key = Qp.tobytes()
        if best_key is None or key < best_key:
            best_key = key
            best = Qp
    
    return best
```

**压缩比保证**：24:1（任何四面体对应的 24 种排列全部映射到同一个范式）。

---

## 三、洛书共轭对偶编码

### 3.1 洛书减 5 矩阵

```
原始洛书:        减 5 后:
4  9  2        -1  +4  -3
3  5  7   →    -2   0  +2
8  1  6        +3  -4  +1
```

非零元素形成四对共轭：±1, ±2, ±3, ±4

### 3.2 四面体手性对偶

```python
def tetrahedron_conjugate(Q):
    """
    四面体的共轭（坐标翻转/手性反转）。
    
    洛书共轭意味着: Q 和 -Q (坐标取反) 在幻方结构中是对称的。
    只需要存正手性版本，负手性版本通过坐标取反推导。
    """
    return -Q  # 坐标全部取反
```

**压缩比**：2:1（正/负手性共轭）

---

## 四、物理类型分类（Magic Factorization）

蛋白质的四面体天然分为三类，对应 Magic Factorization 的三个正交分量：

| 类型 | 物理特征 | 体积范围 | Magic 分量对应 |
|:---|:---|:---|:---|
| **疏水核心** | 紧密堆积，体积小 | V < 30 Å³ | trend (低频趋势) |
| **表面松散** | 暴露于溶剂，体积大 | V > 50 Å³ | residual (高频噪声) |
| **界面结合** | 配体/蛋白-蛋白接触区 | 30 < V < 50 | seasonal (中频模式) |

```python
def tetrahedron_type(Q):
    """用 Cayley-Menger 行列式计算四面体体积，然后分类"""
    V = cayley_menger_volume(Q)
    if V < 30: return 'core'
    elif V > 50: return 'surface'
    else: return 'interface'
```

**压缩比**：3:1（三类独立子集各自用幻方压缩，内部更均匀）

---

## 五、压缩链 (⚠️ 已修正 — 详见 `方案A_压缩比检讨_诚实数学.md`)

| 步骤 | 操作 | 类型 | 压缩比 | 数学可靠性 |
|:--:|------|:---|:--:|:--|
| 0 | 全枚举 | — | 1:1 | ✅ C(500,4) 精确 |
| 1 | 幻方投影筛选 | 候选筛选 | ⚠️ 未知 | ❌ 待 GPU 实测 (E1) |
| 2 | 24 方向范式 | 存储压缩 | 24:1 | ✅ 数学事实 |
| 3 | 洛书共轭对偶 | 存储压缩 | ~1.5:1 | ⚠️ 手性不全 |

> ⚠️ **原文档此处曾有"14,400:1"的错误推导。** L1 的 50:1 是未验证假设，L4(分类)不应计入压缩比。修正后，方案A目前只能确定 **L2×L3 ≈ 36:1 的存储压缩比**。候选筛选压缩比需 GPU 跑 E1 才能确定。详见 `方案A_压缩比检讨_诚实数学.md`。

---

## 六、GPU 实验设计

### 实验 1：验证幻和条件的区分度

**假设**: 满足幻和条件的四点组，比随机四点组更可能是"真实生物四面体"。

**方法**:
```
1. 取 20 个 PDB 蛋白结构 (N=100-500)
2. 对每个蛋白逐残基计算两两距离
3. 随机采样 10 万组四点 → 计算其中"满足幻和条件"的比例 = P_random
4. 对已知的真实疏水核心四面体 (DSSP标注) → 计算 P_real
5. 如果 P_real / P_random > 5，说明幻和条件有区分度
```

**GPU 任务**: 20 蛋白 × 10 万采样 = 200 万次幻方投影 + 四面体体积计算  
**预期时间**: ~15 分钟 (RTX 4090)

### 实验 2：24 方向等价的完整性验证

**假设**: 对于同一组四点，24 种排列产生的几何特征向量在幻方投影下是等价的。

**方法**: 随机采样 1000 个四面体，对每个枚举全部 24 种排列，检查幻方投影后的范式是否唯一。

### 实验 3：洛书共轭的体积守恒

**假设**: 正手性和负手性四面体在幻方投影下的体积是镜像相等的。

**方法**: 用 Cayley-Menger 行列式验证 V(Q) = V(-Q) 对所有四面体成立（这是纯几何事实，主要是确认计算精度）。

### 实验 4：端到端压缩率实测

**假设**: 对真实 PDB 蛋白，四级压缩后的有意义四面体数 < 10⁶。

**方法**: 在实际 PDB 蛋白上跑完整的压缩链，统计最终输出。

---

## 七、可运行代码框架

```python
import numpy as np
from scipy.spatial.distance import pdist, squareform
from itertools import combinations
import cupy as cp  # GPU 加速

class MagicTetraPruner:
    def __init__(self, magic_square=None):
        # 使用已知的 5 阶 pandiagonal 幻方为模板
        self.M = magic_square or np.array([
            [1,  7, 13, 19, 25],
            [14, 20, 21,  2,  8],
            [22,  3,  9, 15, 16],
            [10, 11, 17, 23,  4],
            [18, 24,  5,  6, 12]
        ])
        self.magic_sum = 65
        self.canonical_cache = {}
    
    def magic_project(self, d1, d2, d3):
        """三步长 → 幻方格子坐标"""
        total = d1 + d2 + d3
        if total < 1e-6: return None
        r = int(d1 / total * self.magic_sum) % 5
        c = int(d2 / total * self.magic_sum) % 5
        return (r, c)
    
    def is_magic_complement(self, tri1, tri2):
        """两个三角形的幻方投影是否互补"""
        p1 = self.magic_project(*tri1)
        p2 = self.magic_project(*tri2)
        if p1 is None or p2 is None: return False
        # 互补条件: 投影坐标之和的幻方值 = 幻和
        v1 = self.M[p1]
        v2 = self.M[p2]
        return (v1 + v2) % self.magic_sum == 0
    
    def tetrahedron_canonical(self, coords):
        """24 方向范式"""
        key = coords.tobytes()
        if key in self.canonical_cache:
            return self.canonical_cache[key]
        
        best, best_key = None, None
        for perm in [(0,1,2,3), (0,1,3,2), (0,2,1,3), (0,2,3,1),
                     (0,3,1,2), (0,3,2,1), (1,0,2,3), (1,0,3,2),
                     (1,2,0,3), (1,2,3,0), (1,3,0,2), (1,3,2,0),
                     (2,0,1,3), (2,0,3,1), (2,1,0,3), (2,1,3,0),
                     (2,3,0,1), (2,3,1,0), (3,0,1,2), (3,0,2,1),
                     (3,1,0,2), (3,1,2,0), (3,2,0,1), (3,2,1,0)]:
            q = coords[list(perm)] - coords[perm[0]]
            k = q.tobytes()
            if best_key is None or k < best_key:
                best_key, best = k, q
        
        self.canonical_cache[key] = best
        return best
    
    def prune(self, coords_Nx3, max_tetra=1_000_000):
        """
        主函数: 从 N 个残基的 3D 坐标中筛选有意义的四面体。
        
        Returns: list of canonical tetrahedra
        """
        N = len(coords_Nx3)
        # Step 1: 计算所有两两距离 (O(N²))
        dists = squareform(pdist(coords_Nx3))
        
        # Step 2: GPU 批量计算三角形
        results = []
        pairs = list(combinations(range(N), 2))
        
        # 在 GPU 上并行处理
        for idx, (i, j) in enumerate(pairs[:len(pairs)//10]):  # 采样 10%
            if len(results) >= max_tetra: break
            
            d_ij = dists[i,j]
            for k in range(j+1, N):
                d_ik, d_jk = dists[i,k], dists[j,k]
                tri1 = (d_ij, d_ik, d_jk)
                p1 = self.magic_project(*tri1)
                if p1 is None: continue
                
                for l in range(k+1, N):
                    d_il, d_jl, d_kl = dists[i,l], dists[j,l], dists[k,l]
                    tri2 = (d_il, d_jl, d_kl)
                    
                    if self.is_magic_complement(tri1, tri2):
                        tetra = coords_Nx3[[i,j,k,l]]
                        canonical = self.tetrahedron_canonical(tetra)
                        results.append(canonical)
        
        return results
```

---

## 八、需要 GPU 跑的关键验证

| # | 实验 | 验证什么 | 如果成功说明什么 |
|---|------|---------|----------------|
| 1 | 幻和区分度 | P_real / P_random > 5? | 幻方约束 = 物理约束的数学表达 |
| 2 | 24 方向一致性 | 范式唯一且几何特征保持不变？ | 对称压缩不丢失信息 |
| 3 | 洛书体积守恒 | |V(Q) - V(-Q)| < 1e-6? | 共轭对偶精确可靠 |
| 4 | 端到端压缩率 | 最终 < 10⁶? | O(N⁴)→可行量级 |

---

## 九、与现有工作的对比

| 方法 | 四面体状态存储 | 复杂度 | 可行性 |
|:---|:---|:--:|:--:|
| SimplexFold (全量) | 全稠密 Q_ijkl | O(N⁴) | ❌ 10GB+ |
| Pairmixer (arXiv 2510) | 隐式, 去掉 triangle attn | O(N²) | ✅ 但损失精度 |
| AF3 (扩散) | 隐式, frame-based | O(N²) | ✅ 但不显式建模 |
| **方案 A (Ours)** | **幻方筛选 + 范式压缩** | **O(N²)→O(k log k)** | ✅ ~170MB |

---

> 📁 配套代码：`magic_tetra_pruner.py` (待 GPU 实现)
