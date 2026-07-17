# -*- coding: utf-8 -*-
"""GPU搜索最小素数生成基底 v2 — 哈希碰撞+早退出"""
import numpy as np, time, os

MAX = 1_000_000
OUT = '/root/autodl-tmp/basis_search'
os.makedirs(OUT, exist_ok=True)

# 筛素数
is_prime = np.ones(MAX+1, dtype=bool); is_prime[:2] = False
for i in range(2, int(MAX**0.5)+1):
    if is_prime[i]: is_prime[i*i:MAX+1:i] = False
primes_over5 = np.array([p for p in range(7, MAX+1) if is_prime[p]])

def gen_smooth(basis, limit):
    """生成所有 B-smooth 数 ≤ limit"""
    smooth = {1}
    for p in basis:
        for s in list(smooth):
            v = s
            while v * p <= limit:
                v *= p
                smooth.add(v)
    return sorted(smooth)

def test_basis(label, basis, primes):
    t0 = time.time()
    
    # 生成 B-smooth 数
    smooth = gen_smooth(basis, MAX * 2)
    n_smooth = len(smooth)
    smooth_set = set(smooth)
    
    covered = 0
    miss_list = []
    
    for p in primes:
        found = False
        for s in smooth:
            # |s - p| 或 s + p 是 B-smooth?
            if s > p and (s - p) in smooth_set:
                found = True; break
            if (s + p) in smooth_set:
                found = True; break
        if found:
            covered += 1
        elif len(miss_list) < 5:
            miss_list.append(int(p))
    
    coverage = covered / len(primes) * 100
    dt = time.time() - t0
    print(f"  {label:22s} | smooth: {n_smooth:>6,} | 覆盖: {coverage:5.1f}% | 反例: {len(primes)-covered:,} | {dt:.0f}s")
    if miss_list:
        print(f"    前5反例: {miss_list}")
    return coverage, miss_list, n_smooth, dt

print("="*60)
print("素数生成基底搜索 — B-smooth 碰撞法")
print(f"素数: {len(primes_over5):,} (7~{MAX:,})")
print("="*60)

results = []
for label, basis in [
    ("{2,3,5}", [2,3,5]),
    ("{2,3,5,7}", [2,3,5,7]),
    ("{2,3,5,7,11}", [2,3,5,7,11]),
    ("{2,3,5,7,11,13}", [2,3,5,7,11,13]),
    ("{2,3,5,7,11,13,17}", [2,3,5,7,11,13,17]),
    ("primes≤23 (8个)", [2,3,5,7,11,13,17,19,23]),
    ("primes≤31 (11个)", [2,3,5,7,11,13,17,19,23,29,31]),
]:
    cov, miss, ns, dt = test_basis(label, basis, primes_over5)
    results.append({'basis': label, 'coverage': cov, 'smooth': ns, 
                     'time': dt, 'miss_count': len(primes_over5) - int(cov/100*len(primes_over5))})

# 汇总
print(f"\n{'基底':30s} {'覆盖':>8s} {'smooth数':>8s} {'反例':>8s} {'耗时':>6s}")
print("-"*65)
for r in results:
    print(f"{r['basis']:30s} {r['coverage']:6.1f}% {r['smooth']:7,} {r['miss_count']:7,} {r['time']:5.0f}s")

import json
with open(f'{OUT}/basis_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n✅ {OUT}/")
