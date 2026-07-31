"""
Prototype A: 单偶阶 LUX 嵌套思维 → MoE 难样本动态嵌套调度
===========================================================
纯 numpy 实现（无 torch 环境），用数值梯度演示核心思想。

LUX 核心思想（单偶阶 4k+2 专用）：
  1) 把 (4k+2) 阶格拆成 2x2 微块，每块标 L/U/X 三种朝向
  2) 微块内部用 4 阶 most-perfect 的小结构（闭式）
  3) 微块之间用奇阶骑士步调度

映射到 MoE：
  - 2x2 微块 = 一个 Expert 小组（4 个 expert 的局部 clique）
  - L/U/X 朝向 = 小组内 4 个 expert 的"激活拓扑"（顺/逆/交叉）
  - 微块间骑士步 = 跨组的 token 路由（dr, dc 步长）
  - 单偶阶"难" = 某些 token 在 shallow 路由下 loss 下不去 → 触发嵌套
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter

np.random.seed(0)

# ===== 1. LUX 微块拓扑（4 个 expert 的 3 种激活朝向） =====
# 4 个 expert 的激活顺序（0..3 标量索引）
LUX = {
    'L': [0, 1, 2, 3],  # 逆时针
    'U': [3, 0, 1, 2],  # 顺时针
    'X': [0, 2, 3, 1],  # 交叉
}

def make_lux_block_topology(k, seed=0):
    """生成 (2k+1)x(2k+1) 个 2x2 微块的 L/U/X 布局，模仿奇阶骑士步填 LUX 标记"""
    rng = np.random.RandomState(seed)
    n_blocks = 2*k+1
    grid = [['L' for _ in range(n_blocks)] for _ in range(n_blocks)]
    r, c = 0, 0
    marks = ['U','X']
    m = 0
    visited = set()
    for _ in range(n_blocks**2):
        if (r,c) not in visited:
            grid[r][c] = marks[m % 2]
            m += 1
            visited.add((r,c))
        r = (r+1) % n_blocks
        c = (c+2) % n_blocks
    return grid

# ===== 2. 简易 "Expert"：线性变换 + GELU =====
class LinearExpert:
    def __init__(self, dim):
        self.W = np.random.randn(dim, dim) * 0.1
        self.b = np.zeros(dim)
    def __call__(self, x):
        z = x @ self.W + self.b
        # GELU 近似
        return z * 0.5 * (1 + np.tanh(0.7978845608 * (z + 0.044715 * z**3)))

class LUXExpertClique:
    """对应一个 2x2 微块：4 个 expert，按 L/U/X 拓扑激活"""
    def __init__(self, dim, topo='L'):
        self.experts = [LinearExpert(dim) for _ in range(4)]
        self.topo = topo
    def forward(self, x):
        order = LUX[self.topo]
        out = x.copy()
        # 按拓扑序依次叠加 4 个 expert 的变换（残差）
        for idx in order:
            out = out + self.experts[idx](x)
        return out

# ===== 3. LUX-MoE 整体 =====
class LUXMoE:
    def __init__(self, dim, k=2, num_classes=4):
        self.k = k
        self.n_blocks = 2*k+1
        self.dim = dim
        self.topo_grid = make_lux_block_topology(k, seed=42)
        n_cliques = self.n_blocks**2
        self.cliques = []
        for i in range(self.n_blocks):
            for j in range(self.n_blocks):
                t = self.topo_grid[i][j]
                self.cliques.append(LUXExpertClique(dim, topo=t))
        # 分类头
        self.W_cls = np.random.randn(dim, num_classes) * 0.1
        self.b_cls = np.zeros(num_classes)
        # 骑士步路由参数（软）
        self.dr = 1.0
        self.dc = 2.0

    def knight_route(self, clique_idx, difficulty):
        n = self.n_blocks
        r = clique_idx // n
        c = clique_idx % n
        dr = int(np.clip(round(self.dr), 1, n-1))
        dc = int(np.clip(round(self.dc), 1, n-1))
        # 难度高才跳转
        if difficulty > 1.2:
            nr = (r + dr) % n
            nc = (c + dc) % n
            return nr * n + nc
        return clique_idx

    def __call__(self, X, labels=None):
        L = X.shape[1]
        n_cliques = self.n_blocks**2
        clique_ids = np.arange(L) % n_cliques
        outs = []
        diffs = np.linalg.norm(X, axis=-1).mean(axis=0)  # (L,)
        for i, cid in enumerate(clique_ids):
            tok = X[:, i, :]
            target = self.knight_route(cid, diffs[i])
            outs.append(self.cliques[target].forward(tok))
        stacked = np.stack(outs, axis=1)  # (B,L,D)
        pooled = stacked.mean(axis=1)      # (B,D)
        logits = pooled @ self.W_cls + self.b_cls
        if labels is not None:
            # softmax cross entropy
            exp = np.exp(logits - logits.max(axis=-1, keepdims=True))
            probs = exp / exp.sum(axis=-1, keepdims=True)
            ce = -np.mean(np.log(probs[np.arange(len(labels)), labels] + 1e-12))
            return logits, ce, probs
        return logits, None, None

# ===== 4. 数值梯度 + SGD 训练演示 =====
def collect_all_params(model):
    params = []
    for cl in model.cliques:
        for ex in cl.experts:
            params.append(ex.W); params.append(ex.b)
    params.append(model.W_cls); params.append(model.b_cls)
    return params

def flat_params(params):
    return np.concatenate([p.ravel() for p in params])

def unflat_params(params, flat_grad):
    idx = 0
    grads = []
    for p in params:
        n = p.size
        grads.append(flat_grad[idx:idx+n].reshape(p.shape))
        idx += n
    return grads

def forward_full(model, X, labels):
    """重新跑一遍 forward 拿 loss"""
    logits, ce, _ = model(X, labels)
    return ce

def numerical_gradient(model, X, labels, eps=1e-4):
    params = collect_all_params(model)
    flat = flat_params(params)
    grads = np.zeros_like(flat)
    base_loss = forward_full(model, X, labels)
    for i in range(len(flat)):
        flat[i] += eps
        # 写入
        idx = 0
        for p in params:
            n = p.size
            p[:] = flat[idx:idx+n].reshape(p.shape)
            idx += n
        loss_p = forward_full(model, X, labels)
        grads[i] = (loss_p - base_loss) / eps
        flat[i] -= eps
        idx = 0
        for p in params:
            n = p.size
            p[:] = flat[idx:idx+n].reshape(p.shape)
            idx += n
    return grads

def demo_lux_moe():
    dim, k = 16, 2  # 5x5=25 cliques, 100 experts
    model = LUXMoE(dim=dim, k=k, num_classes=4)
    n_params = sum(p.size for p in collect_all_params(model))
    print(f"[LUX-MoE] dim={dim}, k={k}, cliques={5*5}, experts={100}, params={n_params}")

    # 数据
    X = np.random.randn(1, 12, dim)
    y = np.random.randint(0, 4, (1,))
    logits, loss, _ = model(X, y)
    print(f"  init loss = {loss:.4f}")

    # 训练几步（数值梯度慢，只跑 3 步演示）
    losses = [loss]
    for step in range(3):
        params = collect_all_params(model)
        grads_flat = numerical_gradient(model, X, y, eps=1e-3)
        grads = unflat_params(params, grads_flat)
        lr = 0.05
        for p, g in zip(params, grads):
            p -= lr * g
        l = forward_full(model, X, y)
        losses.append(l)
        print(f"  step {step+1}: loss={l:.4f}  (∇norm={np.linalg.norm(grads_flat):.3f})")

    # 拓扑统计
    topo_cnt = Counter([t for row in model.topo_grid for t in row])
    print(f"  L/U/X 拓扑分布: {dict(topo_cnt)}")
    print(f"  骑士步 (dr,dc) = ({model.dr:.0f},{model.dc:.0f})")
    print("  ✓ LUX 嵌套调度原型跑通")
    return losses

if __name__ == "__main__":
    demo_lux_moe()
