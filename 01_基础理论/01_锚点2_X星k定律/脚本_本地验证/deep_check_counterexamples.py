# -*- coding: utf-8 -*-
"""
deep_check_counterexamples.py — 对 k=9 的 2 个候选反例做深度检查
候选: 9,734,639 和 9,982,241 (素数范围1e7、差式部件<=1e9 协议下不可表示)
本脚本: 差式部件放大到 1e12 (=1e5 倍于 p), 若仍无表示则为强候选反例
理论支撑: Tijdeman(1974) 光滑数间隙定理 => 部件不可能远超 p*polylog(p)
"""
import time

BASES = [2, 3, 5, 7, 11, 13, 17, 19, 23]
CAND = [9734639, 9982241]
LIMIT = 10 ** 12


def gen_smooth(primes, limit):
    out = [1]
    for p in primes:
        cur = []
        for n in out:
            m = n
            while m <= limit:
                cur.append(m)
                m *= p
        out = cur
    return sorted(out)


def isprime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


t0 = time.time()
sm = gen_smooth(BASES, LIMIT + 2 * 10 ** 7)
print(f"23-smooth 数量 (<=1.00002e12): {len(sm)}  生成耗时 {time.time()-t0:.1f}s",
      flush=True)
sset = set(sm)

for p in CAND:
    print(f"--- p = {p:,} ---", flush=True)
    print(f"  素性: {isprime(p)}", flush=True)
    found = []
    # 和式: a + b = p
    for a in sm:
        if a >= p:
            break
        if (p - a) in sset and a <= p - a:
            found.append(("sum", a, p - a))
    # 差式: (p+b) - b = p, b 可达 1e12
    t1 = time.time()
    for b in sm:
        if p + b > LIMIT + 2 * 10 ** 7:
            break
        if (p + b) in sset:
            found.append(("diff", p + b, b))
    print(f"  表示总数 (部件<=1e12): {len(found)}  差式扫描 {time.time()-t1:.1f}s",
          flush=True)
    if found:
        print(f"  示例: {found[:5]}", flush=True)
    else:
        print("  *** 零表示 -> 强候选反例 ***", flush=True)

# 对照: 邻近的可表示素数 (验证方法灵敏度)
print("--- 对照: 9734597 (前一个素数) ---", flush=True)
p = 9734597
if isprime(p):
    cnt = 0
    ex = []
    for a in sm:
        if a >= p:
            break
        if (p - a) in sset and a <= p - a:
            cnt += 1
            if len(ex) < 3:
                ex.append(("sum", a, p - a))
    for b in sm:
        if p + b > LIMIT:
            break
        if (p + b) in sset:
            cnt += 1
            if len(ex) < 6:
                ex.append(("diff", p + b, b))
    print(f"  表示总数: {cnt}  示例: {ex}", flush=True)
print("=== 深度检查完成 ===", flush=True)
