# -*- coding: utf-8 -*-
"""
verify_9base_smooth_coverage.py — PKS 锚点2 独立复核
命题: 素数 p 可由基底 B 生成 <=> 存在 B-smooth 数 a,b 使 p = a+b 或 |a-b|
复核: k=3..9 覆盖率曲线 / 协议敏感性 / 缺失分布 / 1e7 范围首反例搜索 / E(p) 实测 / k(X) 外推
"""
import numpy as np, math, time
from pathlib import Path

BASES = [2, 3, 5, 7, 11, 13, 17, 19, 23]
OUT = Path(r"D:\AAA我的文件\PKS_千禧难题_GitHub版")


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


def sieve_mask(n):
    s = np.ones(n + 1, dtype=bool)
    s[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return s


def coverage(k, PR, DIFF, pmask):
    t0 = time.time()
    base = BASES[:k]
    ss = gen_smooth(base, PR)
    sb = gen_smooth(base, DIFF) if DIFF > PR else ss
    cov = np.zeros(PR + 1, dtype=bool)
    # 和式: a + b <= PR
    for a in ss:
        j = np.searchsorted(ss, PR - a, side='right')
        if j:
            cov[a + ss[:j]] = True
    # 差式: sb[i] - sb[j] <= PR (窗口式)
    for i in range(1, len(sb)):
        lo = np.searchsorted(sb, sb[i] - PR, side='left')
        if lo < i:
            cov[sb[i] - sb[lo:i]] = True
    hit = int((cov & pmask).sum())
    tot = int(pmask.sum())
    miss = np.where(pmask & ~cov)[0]
    return hit, tot, miss, len(ss), len(sb), time.time() - t0


def ln_vol(t, primes_k):
    """B-smooth 计数体积公式 (Ennola): ln[ t^k / (k! * prod ln p) ]"""
    k = len(primes_k)
    return k * math.log(t) - math.lgamma(k + 1) - sum(math.log(math.log(p)) for p in primes_k)


def main():
    S9_1e6 = None

    # ============ Stage 1: 素数范围 1e6 ============
    PR1, DIFF1 = 10 ** 6, 10 ** 8
    pm1 = sieve_mask(PR1)
    print("=== Stage 1: 素数范围 1e6, 协议A(差式部件<=1e8) ===", flush=True)
    miss7 = None
    for k in range(3, 10):
        hit, tot, miss, nss, nsb, dt = coverage(k, PR1, DIFF1, pm1)
        print(f"k={k} base={BASES[:k]}: {hit}/{tot} = {hit/tot*100:.4f}%  "
              f"缺失{len(miss)}  S(1e6)={nss} S(1e8)={nsb}  {dt:.1f}s", flush=True)
        if k == 7:
            miss7 = miss
        if k == 9:
            S9_1e6 = nss

    print("=== Stage 1b: 协议B(差式部件也<=1e6) ===", flush=True)
    for k in (7, 9):
        hit, tot, miss, nss, nsb, dt = coverage(k, PR1, PR1, pm1)
        print(f"k={k}: {hit/tot*100:.4f}%  缺失{len(miss)}", flush=True)

    if miss7 is not None and len(miss7):
        qs = np.percentile(miss7, [0, 10, 25, 50, 75, 90, 100]).astype(int)
        print(f"k=7 缺失素数分位[0/10/25/50/75/90/100%]: {qs.tolist()}", flush=True)
        print(f"k=7 前10缺失: {miss7[:10].tolist()}", flush=True)
        frac_hi = (miss7 > 5 * 10 ** 5).mean() * 100
        print(f"k=7 缺失中 >5e5 占比: {frac_hi:.1f}%", flush=True)
        np.savetxt(OUT / "锚点2_k7缺失素数_1e6范围_协议A.txt", miss7, fmt="%d")

    # ============ Stage 2: 素数范围 1e7, 首反例搜索 ============
    PR2, DIFF2 = 10 ** 7, 10 ** 9
    pm2 = sieve_mask(PR2)
    print("=== Stage 2: 素数范围 1e7, 差式部件<=1e9 ===", flush=True)
    for k in (7, 8, 9):
        hit, tot, miss, nss, nsb, dt = coverage(k, PR2, DIFF2, pm2)
        print(f"k={k}: {hit}/{tot} = {hit/tot*100:.5f}%  缺失{len(miss)}  "
              f"S(1e7)={nss} S(1e9)={nsb}  {dt:.1f}s", flush=True)
        if len(miss):
            print(f"  k={k} 前10缺失: {miss[:10].tolist()}  末3: {miss[-3:].tolist()}",
                  flush=True)
            np.savetxt(OUT / f"锚点2_k{k}缺失素数_1e7范围.txt", miss, fmt="%d")

    # ============ Stage 3: E(p) 实测 (k=9 表示数) ============
    print("=== Stage 3: k=9 每素数平均表示数 E(p) ===", flush=True)
    sb9 = gen_smooth(BASES, 10 ** 9)
    set_b = set(sb9.tolist())
    ss9 = gen_smooth(BASES, PR2)
    set_s = set(ss9.tolist())
    prime_idx = np.where(pm2)[0]

    def reps(p):
        c = 0
        j = np.searchsorted(ss9, p)
        for a in ss9[:j].tolist():          # 和式 (有序计)
            if (p - a) in set_s:
                c += 1
        for b in sb9.tolist():              # 差式 p = (p+b) - b
            if p + b > 10 ** 9:
                break
            if (p + b) in set_b:
                c += 1
        return c

    for scale in (10 ** 5, 10 ** 6, 5 * 10 ** 6, 10 ** 7):
        ps = prime_idx[prime_idx <= scale][-20:]
        vals = [reps(int(p)) for p in ps]
        print(f"p≈{scale:.0e}: E均值={np.mean(vals):.1f}  最小={min(vals)}  "
              f"(样本=尾部20素数)", flush=True)

    # ============ Stage 4: k(X) 需求外推 ============
    print("=== Stage 4: 覆盖到 X 所需基底数 k(X) (体积公式+实测校准, 数量级估计) ===",
          flush=True)
    small_primes = [p for p in range(2, 500)
                    if all(p % q for q in range(2, int(p ** 0.5) + 1))]
    t_cal = math.log(10 ** 6)
    lnF = math.log(S9_1e6) - ln_vol(t_cal, BASES)   # 校准因子(体积公式低估修正)
    print(f"  校准: S9(1e6)实测={S9_1e6}, 体积公式={math.exp(ln_vol(t_cal, BASES)):.0f}, "
          f"修正因子={math.exp(lnF):.1f}x", flush=True)

    # k=9 的配对数 < 素数数 交叉尺度
    for ex10 in np.arange(6, 40, 0.5):
        t = math.log(10.0 ** ex10)
        lhs = 2 * (ln_vol(t, BASES) + lnF)          # ln(配对数)
        rhs = t - math.log(t)                        # ln(pi(X))
        if lhs < rhs:
            print(f"  k=9 计数交叉尺度(配对数<素数数): ≈ 1e{ex10:.1f} "
                  f"(此前必然出现反例)", flush=True)
            break
    else:
        print("  k=9 在 1e40 内未出现计数交叉", flush=True)

    for ex in (8, 10, 12, 14, 16, 18):
        X = 10.0 ** ex
        t = math.log(X)
        lnpi = t - math.log(t)
        need = None
        for k in range(2, 150):
            pk = small_primes[:k]
            if 2 * (ln_vol(t, pk) + lnF) >= lnpi:
                need = k
                break
        pk_val = small_primes[need - 1] if need else -1
        print(f"  X=1e{ex}: 需基底数 k≈{need} (基底最大素数≈{pk_val})", flush=True)

    print("=== 完成 ===", flush=True)


if __name__ == "__main__":
    main()
