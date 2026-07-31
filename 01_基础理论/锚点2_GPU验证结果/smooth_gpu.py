# -*- coding: utf-8 -*-
"""smooth_gpu.py — GPU 加速 B-smooth 碰撞覆盖验证 (PKS 锚点2)
p 可表示 <=> 存在 B-smooth a,b: p = a+b (部件<=X) 或 p = a-b (部件<=D)
用法: python3 smooth_gpu.py --k 9 --X 1e8 --D 1e12
"""
import argparse
import json
import time

import numpy as np
import cupy as cp

BASES_ALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
OUT = "/root/smooth_work"


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
    return np.array(sorted(out), dtype=np.int64)


def gpu_sieve(n):
    s = cp.ones(n + 1, dtype=cp.uint8)
    s[:2] = 0
    limit = int(n ** 0.5)
    small = np.ones(limit + 1, dtype=bool)
    small[:2] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if small[i]:
            small[i * i::i] = False
    for i in np.nonzero(small)[0]:
        i = int(i)
        s[i * i::i] = 0
    return s


def mark_pairs(covered, A, B, lo, hi, mode, chunk=150_000_000):
    """标记 op(A[i], B[j]), j in [lo_i, hi_i). mode: 'sum'/'diff'"""
    L = (hi - lo).astype(cp.int64)
    L = cp.maximum(L, 0)
    csum = cp.cumsum(L)
    csum_h = cp.asnumpy(csum)
    total = int(csum_h[-1]) if len(csum_h) else 0
    if total == 0:
        return 0
    n = len(L)
    done = 0
    start_i = 0
    while start_i < n:
        base = int(csum_h[start_i - 1]) if start_i > 0 else 0
        end_i = int(np.searchsorted(csum_h, base + chunk, side='right'))
        end_i = min(max(end_i, start_i + 1), n)
        Lb = L[start_i:end_i]
        tb = int(Lb.sum())
        if tb > 0:
            owner = cp.repeat(cp.arange(start_i, end_i, dtype=cp.int64), Lb)
            local_start = csum[start_i:end_i] - Lb - base
            inner = cp.arange(tb, dtype=cp.int64) - cp.repeat(local_start, Lb)
            j = lo[owner] + inner
            if mode == 'sum':
                vals = A[owner] + B[j]
            else:
                vals = A[owner] - B[j]
            covered[vals] = 1
            done += tb
            del owner, local_start, inner, j, vals
        start_i = end_i
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--X", type=str, required=True)
    ap.add_argument("--D", type=str, required=True)
    args = ap.parse_args()
    k = args.k
    X = int(float(args.X))
    D = int(float(args.D))
    base = BASES_ALL[:k]

    t0 = time.time()
    ss_np = gen_smooth(base, X)
    sb_np = gen_smooth(base, D)
    t_gen = time.time() - t0

    ss = cp.asarray(ss_np)
    sb = cp.asarray(sb_np)
    covered = cp.zeros(X + 1, dtype=cp.uint8)

    # 和式: a + b <= X
    hi_s = cp.searchsorted(ss, X - ss, side='right')
    lo_s = cp.zeros(len(ss_np), dtype=cp.int64)
    n_sum = mark_pairs(covered, ss, ss, lo_s, hi_s, 'sum')

    # 差式: sb[i] - sb[j] <= X, j < i
    lo_d = cp.searchsorted(sb, sb - X, side='left')
    hi_d = cp.arange(len(sb_np), dtype=cp.int64)
    n_diff = mark_pairs(covered, sb, sb, lo_d, hi_d, 'diff')

    pm = gpu_sieve(X)
    prime_total = int(cp.count_nonzero(pm))
    miss_mask = (pm == 1) & (covered == 0)
    miss = cp.asnumpy(cp.nonzero(miss_mask)[0])
    hit = prime_total - len(miss)

    summary = dict(
        k=k, X=X, D=D, S_X=int(len(ss_np)), S_D=int(len(sb_np)),
        primes=prime_total, covered=hit, miss=int(len(miss)),
        cov_pct=round(100.0 * hit / prime_total, 6),
        first_miss=(int(miss[0]) if len(miss) else None),
        last_miss=(int(miss[-1]) if len(miss) else None),
        pairs_sum=int(n_sum), pairs_diff=int(n_diff),
        t_gen=round(t_gen, 1), t_total=round(time.time() - t0, 1))
    print(json.dumps(summary), flush=True)

    tag = f"k{k}_X{X:.0e}".replace("+", "")
    save = miss[:200000]
    np.savetxt(f"{OUT}/miss_{tag}.txt", save, fmt="%d",
               header=f"total_miss={len(miss)} (saved first {len(save)})")
    with open(f"{OUT}/summary.jsonl", "a") as f:
        f.write(json.dumps(summary) + "\n")


if __name__ == "__main__":
    main()
