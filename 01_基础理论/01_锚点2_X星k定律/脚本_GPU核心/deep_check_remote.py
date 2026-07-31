# -*- coding: utf-8 -*-
"""deep_check_remote.py — 对 GPU 产出的 miss 做深检 (部件扩大到 1e13/1e14)"""
import sys, time, numpy as np

BASES = [2,3,5,7,11,13,17,19,23,29,31]
BASE9 = BASES[:9]; BASE10 = BASES[:10]; BASE11 = BASES[:11]


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


def deep_check(sset, p, Dlim):
    cnt = 0
    j = np.searchsorted(sset, p)
    for a in sset[:j]:
        if (p - a) in sset:
            cnt += 1
    for b in sset:
        if p + b > Dlim:
            break
        if (p + b) in sset:
            cnt += 1
    return cnt


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "k9_X1e8"
    miss_file = f"/root/smooth_work/miss_{tag}.txt"
    try:
        miss_all = np.loadtxt(miss_file, dtype=np.int64)
        miss_all = np.atleast_1d(miss_all)
    except:
        print(f"FAIL: cannot read {miss_file}")
        return
    first = min(40, len(miss_all))
    candidates = np.concatenate([miss_all[:first], miss_all[-min(10,len(miss_all)):]])
    candidates = np.unique(candidates)
    print(f"deep_check {tag}: total_miss={len(miss_all)} sampled={len(candidates)}", flush=True)
    k = 9 if "k9" in tag else (10 if "k10" in tag else 11)
    base = BASES[:k]
    Dlim = 10 ** 13
    sset = gen_smooth(base, Dlim + int(2e7))
    t0 = time.time()
    print(f"  base={base} |smooth|={len(sset)} D={Dlim:.0e} gen={time.time()-t0:.1f}s",
          flush=True)
    good = 0
    for p in candidates:
        reps = deep_check(sset, int(p), Dlim)
        if reps > 0:
            good += 1
            print(f"  p={p}: REPS={reps} (NOT a counterexample!)", flush=True)
        else:
            print(f"  p={p}: ZERO reps @ D=1e13", flush=True)
    print(f"deep_check {tag}: candidates={len(candidates)} confirmed_counterexamples={len(candidates)-good}",
          flush=True)


if __name__ == "__main__":
    main()
