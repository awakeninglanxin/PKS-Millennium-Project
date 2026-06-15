# -*- coding: utf-8 -*-
"""
素数生成算法全集 — 6 种算法横向对比
=====================================
1. Croft 螺旋筛      O(n/4 · log log n)        — 模30轮筛, 仅筛26.67%自然数
2. 埃拉托色尼筛       O(n log log n)            — 经典基准
3. Sundaram 筛        O(n log n)                — 仅生成奇数素数
4. Atkin 筛           O(n / log log n)          — 理论最优渐进
5. 试除法             O(n√n)                    — 最朴素的朴素
6. 6k±1 优化试除      O(n√n / 3)                — 仅测 6k±1 候选
"""

import math

# ============================================================
# 1. Croft 螺旋筛 — 模30 外循环优化埃拉托色尼筛
# ============================================================
def sieve_croft(limit):
    """
    Croft 螺旋筛: 仅在模30候选数上迭代外循环
    - 外循环跳过 73.33% 的数 (只遍历与30互质的数)
    - 内循环与埃拉托色尼相同 (步进 p)
    - 比埃拉托色尼快 ~2-3x (取决于范围)
    """
    if limit < 2:
        return []
    if limit < 7:
        return [p for p in [2, 3, 5] if p <= limit]

    s = [True] * (limit + 1)
    s[0] = s[1] = False

    # 仅遍历与30互质的候选数
    deltas = [6, 4, 2, 4, 2, 4, 6, 2]
    n, di = 7, 1  # 从 7 开始 (2,3,5 已处理)
    while n * n <= limit:
        if s[n]:
            for m in range(n * n, limit + 1, n):
                s[m] = False
        n += deltas[di]
        di = (di + 1) % 8

    # 收集结果 (同样只遍历候选数来减少内循环)
    result = [2, 3, 5]
    n, di = 7, 1
    while n <= limit:
        if s[n]:
            result.append(n)
        n += deltas[di]
        di = (di + 1) % 8

    return result


# ============================================================
# 2. 经典埃拉托色尼筛
# ============================================================
def sieve_eratosthenes(limit):
    if limit < 2: return []
    s = [True] * (limit + 1)
    s[0] = s[1] = False
    for p in range(2, int(limit ** 0.5) + 1):
        if s[p]:
            for m in range(p * p, limit + 1, p):
                s[m] = False
    return [i for i, v in enumerate(s) if v]


# ============================================================
# 3. Sundaram 筛
# ============================================================
def sieve_sundaram(limit):
    if limit < 2: return []
    if limit < 3: return [2]
    k = (limit - 1) // 2
    s = [True] * (k + 1)
    for i in range(1, k + 1):
        j = i
        while i + j + 2*i*j <= k:
            s[i + j + 2*i*j] = False
            j += 1
    r = [2]
    for i in range(1, k + 1):
        if s[i]:
            r.append(2 * i + 1)
    return r


# ============================================================
# 4. Atkin 筛
# ============================================================
def sieve_atkin(limit):
    if limit < 2: return []
    s = [False] * (limit + 1)
    if limit >= 2: s[2] = True
    if limit >= 3: s[3] = True
    sqlim = int(limit ** 0.5) + 1
    for x in range(1, sqlim):
        x2 = x * x
        for y in range(1, sqlim):
            y2 = y * y
            n = 4*x2 + y2
            if n <= limit and (n % 12 == 1 or n % 12 == 5):
                s[n] = not s[n]
            n = 3*x2 + y2
            if n <= limit and n % 12 == 7:
                s[n] = not s[n]
            n = 3*x2 - y2
            if x > y and n <= limit and n % 12 == 11:
                s[n] = not s[n]
    for n in range(5, sqlim):
        if s[n]:
            n2 = n * n
            for k in range(n2, limit + 1, n2):
                s[k] = False
    return [i for i in range(limit + 1) if s[i]]


# ============================================================
# 5. 试除法
# ============================================================
def primes_trial_division(limit):
    r = []
    for n in range(2, limit + 1):
        ok = True
        for d in range(2, int(n ** 0.5) + 1):
            if n % d == 0:
                ok = False
                break
        if ok:
            r.append(n)
    return r


# ============================================================
# 6. 6k±1 优化试除法
# ============================================================
def primes_6k_optimized(limit):
    if limit < 2: return []
    r = []
    if limit >= 2: r.append(2)
    if limit >= 3: r.append(3)
    for n in range(5, limit + 1, 6):
        for c in (n, n + 2):
            if c > limit: break
            ok = True
            d, delta = 5, 2
            while d * d <= c:
                if c % d == 0:
                    ok = False
                    break
                d += delta
                delta = 6 - delta
            if ok:
                r.append(c)
    return r


# ============================================================
# 注册表
# ============================================================
SIEVE_REGISTRY = {
    "Croft 螺旋筛": (sieve_croft, "O(n/4 log log n)", "O(0.27n)"),
    "埃拉托色尼筛": (sieve_eratosthenes, "O(n log log n)", "O(n)"),
    "Sundaram 筛": (sieve_sundaram, "O(n log n)", "O(n/2)"),
    "Atkin 筛": (sieve_atkin, "O(n / log log n)", "O(n)"),
    "试除法": (primes_trial_division, "O(n√n)", "O(1)"),
    "6k±1 试除法": (primes_6k_optimized, "O(n√n / 3)", "O(1)"),
}


if __name__ == "__main__":
    import time
    from math import isqrt
    def is_prime_ref(n):
        if n < 2: return False
        for d in range(2, int(isqrt(n)) + 1):
            if n % d == 0: return False
        return True

    for limit in [100, 1000, 10_000]:
        ref = [n for n in range(2, limit+1) if is_prime_ref(n)]
        print(f"\npi({limit}) = {len(ref)}")
        for name, (fn, comp, space) in SIEVE_REGISTRY.items():
            t0 = time.perf_counter()
            r = fn(limit)
            t1 = time.perf_counter()
            ok = "OK" if r == ref else f"FAIL ({len(r)} primes)"
            print(f"  {ok:20s} {name:16s}  {t1-t0:.5f}s")
