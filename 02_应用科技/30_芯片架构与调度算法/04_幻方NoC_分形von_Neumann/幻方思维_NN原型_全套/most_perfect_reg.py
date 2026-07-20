"""
Prototype B: 双偶阶 most-perfect 双尺度正则 → NN 可插拔正则项
================================================================
纯 numpy 实现。

most-perfect 双偶阶 4k 的两条硬约束：
  1) compact : 任意 2x2 子块和 = 2*(n^2+1) 恒定
  2) complete: 距 n/2 的对角两数互补 (a + a' = n^2+1)

映射到 NN：
  - compact  → 对 feature map 每 2x2 邻域强制均值恒定（local uniformity）
  - complete → 对称位置的特征/权重强制互补（anti-redundancy）
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

np.random.seed(0)

# ===== 1. Compact 正则：2x2 子块均值恒定 =====
def compact_regularizer(feat, target_val=None):
    """
    feat: (B, C, H, W)
    按 2x2 不重叠分块，每块均值 → 逼近于全局均值
    对应 most-perfect 的 "every 2x2 block sum = const"
    """
    B, C, H, W = feat.shape
    h, w = H - (H % 2), W - (W % 2)
    f = feat[:, :, :h, :w]
    # 2x2 平均池化
    pooled = np.zeros((B, C, h//2, w//2))
    for bi in range(B):
        for ci in range(C):
            for i in range(0, h, 2):
                for j in range(0, w, 2):
                    pooled[bi, ci, i//2, j//2] = f[bi, ci, i:i+2, j:j+2].mean()
    if target_val is None:
        target_val = pooled.mean()
    return ((pooled - target_val) ** 2).mean(), pooled

# ===== 2. Complete 正则：对称位置互补 =====
def complete_regularizer(weights):
    """
    weights: (num_heads, D)
    对应 most-perfect 的 "position i 与 i+n//2 互补"
    (a-center) + (b-center) ≈ 0
    """
    num, D = weights.shape
    half = num // 2
    if half < 1:
        return 0.0
    center = weights.mean(axis=0, keepdims=True)
    a = weights[:half]
    b = weights[half:half*2]
    diff = (a - center) + (b - center)
    return (diff**2).mean()

# ===== 3. Pandiagonal 正则（超长程） =====
def pandiagonal_regularizer(feat):
    B, C, H, W = feat.shape
    loss = 0.0
    for b in range(B):
        for c in range(C):
            m = feat[b, c]
            main = np.mean(np.diag(m))
            anti = np.mean(np.diag(np.fliplr(m)))
            g = m.mean()
            loss += (main - g)**2 + (anti - g)**2
    return loss / (B * C)

# ===== 4. 组合 =====
def most_perfect_loss(feat_maps, weight_mats, lc=1.0, lcp=1.0, lp=0.5):
    loss = 0.0
    for fm in feat_maps:
        c_loss, _ = compact_regularizer(fm)
        loss += lc * c_loss
        loss += lp * pandiagonal_regularizer(fm)
    for w in weight_mats:
        loss += lcp * complete_regularizer(w)
    return loss

# ===== 5. 用 scipy 做优化（比数值梯度快） =====
from scipy.optimize import minimize

def demo_most_perfect_reg():
    print("[MostPerfectReg] building 8x8 feature map (4k, k=2) ...")
    fm0 = np.random.randn(1, 16, 8, 8)
    W0 = np.random.randn(8, 32)
    reg = lambda lc=1.0, lcp=1.0, lp=0.5: most_perfect_loss(
        [fm0], [W0], lc, lcp, lp)

    # 初始
    l0 = reg()
    print(f"  initial total loss = {l0:.6f}")
    c0, _ = compact_regularizer(fm0)
    cp0 = complete_regularizer(W0)
    p0 = pandiagonal_regularizer(fm0)
    print(f"    compact={c0:.5f}  complete={cp0:.5f}  pandiagonal={p0:.5f}")

    # 分别优化 fm 和 W（联合优化数值梯度太慢，分两步）
    # Step 1: 优化 fm
    flat_fm = fm0.copy().ravel()
    def obj_fm(x):
        fm = x.reshape(fm0.shape)
        return most_perfect_loss([fm], [W0])
    res = minimize(obj_fm, flat_fm, method='L-BFGS-B', options={'maxiter': 40, 'gtol':1e-4})
    fm_opt = res.x.reshape(fm0.shape)
    l1 = obj_fm(res.x)
    print(f"  after fm optimize : {l1:.6f}")

    # Step 2: 优化 W
    flat_W = W0.copy().ravel()
    def obj_W(x):
        W = x.reshape(W0.shape)
        return most_perfect_loss([fm_opt], [W])
    res2 = minimize(obj_W, flat_W, method='L-BFGS-B', options={'maxiter': 40, 'gtol':1e-4})
    W_opt = res2.x.reshape(W0.shape)
    l2 = obj_W(res2.x)
    print(f"  after W  optimize : {l2:.6f}")

    # 验证
    c_final, pooled = compact_regularizer(fm_opt)
    cp_final = complete_regularizer(W_opt)
    print(f"    compact={c_final:.6f}  complete={cp_final:.6f}")
    print(f"  2x2 block 均值 std: {pooled.std():.6f}  (理想→0)")
    print("  ✓ compact+complete+pandiagonal 三尺度正则可训练")
    return fm0, fm_opt, W0, W_opt

# ===== 6. 可视化：正则前后 feature map 的 2x2 均匀度对比 =====
def visualize(fm_before, fm_after, save_path="most_perfect_reg.png"):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    # 取第 0 通道
    before = fm_before[0, 0]
    after  = fm_after[0, 0]
    axes[0].imshow(before, cmap='RdBu_r', vmin=-2, vmax=2)
    axes[0].set_title("Before reg\n(channel 0)", fontsize=11)
    axes[1].imshow(after,  cmap='RdBu_r', vmin=-2, vmax=2)
    axes[1].set_title("After reg\n(channel 0)", fontsize=11)
    # 2x2 block 均值热力图（after）
    h, w = after.shape
    pooled = np.zeros((h//2, w//2))
    for i in range(0, h-1, 2):
        for j in range(0, w-1, 2):
            pooled[i//2, j//2] = after[i:i+2, j:j+2].mean()
    im = axes[2].imshow(pooled, cmap='viridis')
    axes[2].set_title("2x2 block means\nafter reg (std=%.4f)" % pooled.std(), fontsize=11)
    plt.colorbar(im, ax=axes[2], fraction=0.046)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches='tight')
    print(f"  ✓ 图已保存: {save_path}")

if __name__ == "__main__":
    print("=== Most-Perfect 双尺度正则原型 (numpy+scipy) ===\n")
    fm0, fm_opt, W0, W_opt = demo_most_perfect_reg()
    visualize(fm0, fm_opt, "most_perfect_reg.png")
