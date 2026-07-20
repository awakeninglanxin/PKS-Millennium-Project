# 方案 B：幻方因子化编码器 — 深度学习版

> 🎯 目标：把幻方正交分解 M = 5A + B + 1 嵌入 Transformer 编码器，三个注意力头分别编码趋势/细节/交互分量  
> 🧠 方法：Magic-Factorized Attention — 比普通 Multi-Head Attention 多一个"幻方约束层"  
> ⏱️ GPU 周期：3–5 天 (RTX 4090)  

---

## 一、核心思想

### 1.1 从幻方到注意力

5 阶幻方 M₅ = 5A + B + 1 的分解暗示：**任何结构化数据都可以分解为"正交基础层"(A) + "扰动细节层"(B) + "交互项"(AB交叉)**。

把这个思想搬进 Transformer：

```
标准 Multi-Head Attention:
  Q, K, V = XW_q, XW_k, XW_v    ← 全部八头独立学习
  Output = concat(head_1, ..., head_8)W_o

Magic-Factorized Attention (我们的):
  Q_A, K_A, V_A = XW_qA, XW_kA, XW_vA  ← "基础"分量 (对应幻方 A)
  Q_B, K_B, V_B = XW_qB, XW_kB, XW_vB  ← "细节"分量 (对应幻方 B)
  Q_AB, K_AB, V_AB = Q_A⊙Q_B, ...      ← "交互"分量 (对应 A×B 交叉)
  
  幻方约束: ||head_A ⊗ head_B||_F → 正交 (A 和 B 互不干扰)
```

### 1.2 为什么三个头就够了

```
标准 8 头: 自由度 = 8 × d_k × d_v, 无结构约束 → 容易过拟合
幻方 3 头: 自由度 = 3 × d_k × d_v, 但受幻方正交约束 → 更紧凑, 更具物理可解释性
```

而且 3 = 幻方分解的自然维度数（A, B, AB），不是随便选的。

---

## 二、架构详图

```
输入序列 X ∈ R^{N×d}
         │
    ┌────┼────┐
    ▼    ▼    ▼
  Head_A Head_B Head_AB       ← 三个幻方注意力头
  (趋势) (细节) (交互)
    │    │    │
    └────┼────┘
         ▼
   幻方约束层 (Magic Constraint)
   ||A⊗B||_F → min  ← A 和 B 正交
   ||AB - A⊙B||_F → min  ← 交互项 = A 和 B 的外积
         │
         ▼
   Feed-Forward → LayerNorm → 输出
```

### 2.3 幻方约束的损失函数

```python
def magic_constraint_loss(head_A, head_B, head_AB):
    """
    让注意力头遵守幻方正交结构。
    
    head_A: [B, N, d]  — 趋势分量
    head_B: [B, N, d]  — 细节分量
    head_AB: [B, N, d] — 交互分量
    """
    # 1. 正交约束: A 和 B 的内积应 → 0
    ortho_loss = torch.norm(torch.bmm(head_A, head_B.transpose(1,2)), p='fro')
    
    # 2. 交互约束: AB 应 ≈ A 的外积 × B
    #    类似幻方 M = 5A + B + 1 中 A 和 B 的正交叠加
    interaction = torch.bmm(head_A, head_B.transpose(1,2))
    ab_approx = torch.bmm(interaction, head_B) / head_B.size(-1)
    consistency_loss = F.mse_loss(head_AB, ab_approx)
    
    return ortho_loss + consistency_loss
```

---

## 三、与 SimplexFold 的集成方案

### 3.1 插入位置

SimplexFold 的 EvoFormer 有 48 个 Transformer block。我们把**其中最后 8 个 block 的注意力层**替换为 Magic-Factorized Attention。

```
EvoFormer (48 blocks):
  block_0  ... block_39: 标准 Multi-Head Attention (不变)
  block_40 ... block_47: Magic-Factorized Attention ← 我们的插入点
```

原因：前 40 层做标准特征提取，后 8 层做"幻方结构化压缩"——压缩四面体状态。

### 3.2 四面体状态的幻方编码

```python
class MagicTetraEncoder(nn.Module):
    """
    把四个残基的特征编码为一个"幻方规范四面体状态"。
    
    输入: R_i, R_j, R_k, R_l ∈ R^d  (四个残基的 d 维特征)
    输出: Q_ijkl ∈ R^d               (压缩后的四面体状态)
    """
    def __init__(self, d_model=128):
        super().__init__()
        self.head_A = nn.Linear(d_model * 4, d_model)  # 趋势分量
        self.head_B = nn.Linear(d_model * 4, d_model)  # 细节分量
        self.head_AB = nn.Linear(d_model * 4, d_model) # 交互分量
        self.fusion = nn.Linear(d_model * 3, d_model)   # 融合
        
    def forward(self, R_i, R_j, R_k, R_l):
        x = torch.cat([R_i, R_j, R_k, R_l], dim=-1)
        a = self.head_A(x)   # "幻方 A 分量"
        b = self.head_B(x)   # "幻方 B 分量"
        ab = self.head_AB(x) # "幻方 AB 交互"
        
        # 正交正则化 (在损失函数中施加)
        Q = self.fusion(torch.cat([a, b, ab], dim=-1))
        return Q
```

---

## 四、与 CDCC 的融合 — 幻方三域对比学习

方案 B 和我们的 CDCC × Magic 三域对比学习框架一脉相承：

```
             时域编码 (Temporal)
            /
CDCC 框架 ─── 频域编码 (Frequency)
            \
             幻方域编码 (Magic Domain) ← 方案 B 新增
             
三域对比损失 = L_temp + L_freq + L_magic + L_cross
```

**新增的"幻方域"编码 = 方案 B 的 Magic-Factorized Attention 输出**，专门捕获四面体的正交结构。

---

## 五、GPU 实验设计

### 实验 1：幻方注意力 vs 标准注意力 (消融)

**假设**: Magic-Factorized Attention (3 头) 在蛋白质几何任务上优于或持平标准 Multi-Head Attention (8 头)，但参数量减少 62.5%。

**数据集**: PDBBind (蛋白-配体结合) / ProteinNet  
**任务**: 残基间距离预测 (d_ij)、接触图预测

| 模型 | 注意力 | 参数量 | MAE (距离) | Precision (接触) |
|:---|:---|:--:|:--:|:--:|
| 基线 | 标准 8-head | 100% | ? | ? |
| 变体A | 幻方 3-head | 37.5% | ? | ? |
| 变体B | 幻方 3-head + 正交约束 | 37.5% | ? | ? |

**GPU 需求**: RTX 4090, ~4 小时训练 (PDBBind ≈ 19K 结构)

### 实验 2：四面体状态压缩后的信息保真度

**假设**: 幻方编码后的四面体状态 Q_ijkl 能保留原始四面体的≥90% 几何信息。

**方法**:
1. 用蛋白质的真实四面体坐标训练一个"编码-解码"网络
2. 编码器: MagicTetraEncoder → 128 维向量
3. 解码器: 128 维 → 3D 坐标重建
4. 度量: 重建后的四面体体积与原始体积的相对误差

```
预期: |V_recon - V_orig| / V_orig < 10%
```

### 实验 3：幻方约束的鲁棒性

**假设**: 施加 magic_constraint_loss 后，模型对噪声蛋白质结构 (PDB 实验误差 1-3Å) 的泛化更好。

**方法**: 在干净的 AlphaFold 预测结构上训练，在有噪声的实验 PDB 结构上测试。

---

## 六、可运行训练代码框架

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MagicFactorizedAttention(nn.Module):
    """幻方因子化注意力 — 三头替代八头"""
    
    def __init__(self, d_model=128, dropout=0.1):
        super().__init__()
        d_k = d_model // 3  # 每个头的大小 = d_model/3 (≈42)
        
        # 三个幻方分量头
        self.Wq_A = nn.Linear(d_model, d_k)  # 趋势
        self.Wk_A = nn.Linear(d_model, d_k)
        self.Wv_A = nn.Linear(d_model, d_k)
        
        self.Wq_B = nn.Linear(d_model, d_k)  # 细节
        self.Wk_B = nn.Linear(d_model, d_k)
        self.Wv_B = nn.Linear(d_model, d_k)
        
        self.Wq_AB = nn.Linear(d_model, d_k) # 交互
        self.Wk_AB = nn.Linear(d_model, d_k)
        self.Wv_AB = nn.Linear(d_model, d_k)
        
        self.fc_out = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.scale = d_k ** -0.5
        
    def _attention(self, q, k, v, mask=None):
        attn = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        if mask is not None:
            attn = attn.masked_fill(mask == 0, -1e9)
        return torch.matmul(F.softmax(attn, dim=-1), v)
    
    def forward(self, x, mask=None):
        # 三个分量独立做注意力
        out_A = self._attention(
            self.Wq_A(x), self.Wk_A(x), self.Wv_A(x), mask)
        out_B = self._attention(
            self.Wq_B(x), self.Wk_B(x), self.Wv_B(x), mask)
        out_AB = self._attention(
            self.Wq_AB(x), self.Wk_AB(x), self.Wv_AB(x), mask)
        
        # 拼接三头
        out = torch.cat([out_A, out_B, out_AB], dim=-1)
        return self.fc_out(self.dropout(out))
    
    def magic_loss(self):
        """计算幻方正交约束"""
        # 用当前权重矩阵计算
        WqA, WqB = self.Wq_A.weight, self.Wq_B.weight
        ortho = torch.norm(torch.mm(WqA, WqB.T), p='fro')
        return ortho


class MagicTetraFormer(nn.Module):
    """
    幻方四面体 Transformer — 专门为蛋白质四面体状态设计的轻量编码器
    """
    def __init__(self, d_model=128, n_layers=4):
        super().__init__()
        self.embed = nn.Linear(12, d_model)  # 4点×3坐标 = 12维输入
        
        self.layers = nn.ModuleList([
            MagicFactorizedAttention(d_model) for _ in range(n_layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(d_model) for _ in range(n_layers)])
        self.ffns = nn.ModuleList([
            nn.Sequential(nn.Linear(d_model, d_model*4), nn.GELU(), 
                         nn.Linear(d_model*4, d_model))
            for _ in range(n_layers)
        ])
        
        self.output = nn.Linear(d_model, 128)  # 压缩到 128 维四面体状态
        
    def forward(self, tetra_coords):
        """
        tetra_coords: [B, 4, 3] — 四个点的 3D 坐标
        """
        B = tetra_coords.shape[0]
        x = self.embed(tetra_coords.view(B, -1))  # [B, 12] → [B, d_model]
        x = x.unsqueeze(1)  # [B, 1, d_model]
        
        magic_losses = []
        for layer, norm, ffn in zip(self.layers, self.norms, self.ffns):
            attn_out = layer(x)
            x = norm(x + attn_out)
            ffn_out = ffn(x)
            x = norm(x + ffn_out)
            magic_losses.append(layer.magic_loss())
        
        return self.output(x.squeeze(1)), sum(magic_losses)
```

---

## 七、GPU 实验总台

| # | 实验 | 验证什么 | 时间 | 如果成功说明 |
|---|------|---------|:--:|------------|
| 1 | 幻方注意力消融 | 3头 vs 8头：参数少但精度持平？ | 4h | 幻方结构 = 更高效的归纳偏置 |
| 2 | 四面体编码保真度 | 重建误差 < 10%？ | 2h | 幻方编码不丢关键几何信息 |
| 3 | 噪声鲁棒性 | 魔法约束提升泛化？ | 3h | 幻方正则化 = 去噪 |
| 4 | 与 CDCC 融合 | 三域对比优于双域？ | 6h | 幻方域有额外信息增益 |

---

## 八、论文方向

如果实验 1 成功（3 头≤8 头精度 + 参数少 62%）：论文核心贡献 = **幻方正交结构 = Transformer 注意力头的天然压缩方案**。

如果实验 4 成功（三域 > 双域）：论文 = **CDCC 的幻方域扩展 = AAAI 2024 方法的升级版**。

---

> 📁 配套代码：`magic_tetra_former.py` (待 GPU 实现)  
> 🔗 参考：`CDCC` (Peng et al., AAAI 2024) + `MagicFactorization` (我们的 Super k-Shape)
