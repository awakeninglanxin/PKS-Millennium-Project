# -*- coding: utf-8 -*-
"""GPU验证 Croft猜想: 所有素数可由 2^a·3^b ± 5^c 生成"""
import cupy as cp, numpy as np, time, os

OUT = '/root/autodl-tmp/goldbach_croft'
os.makedirs(OUT, exist_ok=True)
cp.cuda.Device(0).use()

print("="*60)
print("Croft Goldbach猜想 GPU验证: prime = 2^a·3^b ± 5^c")
print("RTX 4090 | CuPy")
print("="*60)

# 参数范围
MAX_PRIME = 1_000_000          # 验证上限
A_MAX = 22                     # 2^22 ≈ 4M
B_MAX = 14                     # 3^14 ≈ 4.8M  
C_MAX = 9                      # 5^9 ≈ 2M

# ===== Step 1: CPU筛素数 =====
t0 = time.time()
n = MAX_PRIME
is_prime = np.ones(n+1, dtype=bool); is_prime[:2] = False
for i in range(2, int(n**0.5)+1):
    if is_prime[i]: is_prime[i*i:n+1:i] = False
primes = np.flatnonzero(is_prime)
primes_over5 = primes[primes > 5]
print(f"素数: {len(primes_over5):,} 个 (7~{primes_over5[-1]:,}) | {time.time()-t0:.1f}s")

# ===== Step 2: GPU批量生成 2^a·3^b (核心) =====
print(f"\n生成 {A_MAX}×{B_MAX}={A_MAX*B_MAX} 个基底...")
t0 = time.time()

pow2 = cp.array([2**a for a in range(A_MAX)], dtype=cp.int64)
pow3 = cp.array([3**b for b in range(B_MAX)], dtype=cp.int64)
# 外积: (22, 14) → 308 个基底
bases = cp.outer(pow2, pow3).ravel()
bases = bases[bases <= MAX_PRIME * 2]  # 过滤无用大数
print(f"  有效基底: {len(bases):,} 个 (max={int(cp.max(bases)):,}) | {time.time()-t0:.1f}s")

# ===== Step 3: ± 5^c 碰撞检测 =====
print(f"\n± 5^c 碰撞检测...")
t0 = time.time()

pow5 = cp.array([5**c for c in range(C_MAX)], dtype=cp.int64)
hit = np.zeros(MAX_PRIME+1, dtype=bool)  # CPU bool array for marking

for b_idx in range(len(bases)):
    base = int(bases[b_idx])
    for p5 in pow5:
        p5_val = int(p5)
        # base + 5^c
        val_plus = base + p5_val
        if 7 <= val_plus <= MAX_PRIME and is_prime[val_plus]:
            hit[val_plus] = True
        # base - 5^c (确保>0)
        val_minus = base - p5_val
        if 7 <= val_minus <= MAX_PRIME and is_prime[val_minus]:
            hit[val_minus] = True

dt = time.time() - t0
print(f"  碰撞检测: {dt:.1f}s")

# ===== Step 4: 统计 =====
covered = np.sum(hit[primes_over5])
total = len(primes_over5)
missed_primes = primes_over5[~hit[primes_over5]]
coverage = covered / total * 100

print(f"\n{'='*60}")
print(f"结果")
print(f"{'='*60}")
print(f"素数总数 (7~{MAX_PRIME:,}): {total:,}")
print(f"被覆盖: {covered:,} ({coverage:.1f}%)")
print(f"未覆盖: {total-covered:,}")

if len(missed_primes) > 0:
    print(f"\n前30个反例:")
    for i, p in enumerate(missed_primes[:30]):
        print(f"  {p:,}", end="")
        if (i+1) % 10 == 0: print()
    if len(missed_primes) > 30:
        print(f"  ... 共 {len(missed_primes):,} 个反例")
    
    # 保存全部反例
    np.savetxt(f'{OUT}/counterexamples.csv', missed_primes, fmt='%d', 
               header='counterexample_primes')
    print(f"\n反例已保存: {OUT}/counterexamples.csv ({len(missed_primes)} primes)")

# ===== Step 5: 扩展搜索 (允许负的 5^c 组合) =====
if coverage < 99:
    print(f"\n扩展: ±5^c 组合搜索...")
    t0 = time.time()
    # 允许 base ± (5^c1 ± 5^c2) 即双重5幂校正
    hit2 = hit.copy()
    for b_idx in range(0, len(bases), 8):  # 采样加速
        base = int(bases[b_idx])
        for p5_1 in pow5:
            for p5_2 in pow5:
                val = base + int(p5_1) + int(p5_2)
                if 7 <= val <= MAX_PRIME and is_prime[val]:
                    hit2[val] = True
                val = base + int(p5_1) - int(p5_2)
                if 7 <= val <= MAX_PRIME and is_prime[val]:
                    hit2[val] = True
    
    covered2 = np.sum(hit2[primes_over5])
    missed2 = primes_over5[~hit2[primes_over5]]
    print(f"  双重5幂: {covered2:,}/{total:,} ({covered2/total*100:.1f}%) | {time.time()-t0:.1f}s")
    if len(missed2) < len(missed_primes):
        print(f"  新覆盖素数: {len(missed_primes)-len(missed2):,}")
        coverage = covered2 / total * 100

# ===== Step 6: 分析反例特征 =====
if len(missed_primes) > 0:
    print(f"\n反例分布分析:")
    gaps = np.diff(missed_primes[:100])
    print(f"  前100反例间距: min={gaps.min()}, max={gaps.max()}, mean={gaps.mean():.0f}")
    
    # 反例的模30分布
    mod30 = missed_primes % 30
    unique_mods, counts = np.unique(mod30, return_counts=True)
    print(f"  模30分布:")
    for m, c in zip(unique_mods, counts):
        print(f"    ≡{m} mod 30: {c} ({c/len(missed_primes)*100:.1f}%)")

print(f"\n✅ 全部结果: {OUT}/")
