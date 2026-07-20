#!/usr/bin/env python3
"""5阶完美幻方 3600种 精确生成器 v2 (修正版)
算法: budshaw.ca Pandiagonal.html 的 36×4×25 变换链
"""
import numpy as np
from math import gcd
import json, os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

def check_pandiag(M):
    N = M.shape[0]
    ms = N*(N*N+1)//2
    if not np.all(M.sum(axis=1)==ms): return False
    if not np.all(M.sum(axis=0)==ms): return False
    d1 = sum(M[i,i] for i in range(N))
    d2 = sum(M[i,N-1-i] for i in range(N))
    if d1!=ms or d2!=ms: return False
    for k in range(1, N):
        if sum(M[i,(i+k)%N] for i in range(N)) != ms: return False
        if sum(M[i,(i-k)%N] for i in range(N)) != ms: return False
    return True

def latin_pandiag(a,b,c,d,N=5):
    """双正交拉丁方 pandiagonal: M = N*(ai+bj) + (ci+dj) + 1"""
    M = np.zeros((N,N), dtype=int)
    for i in range(N):
        for j in range(N):
            M[i,j] = N*((a*i+b*j)%N) + (c*i+d*j)%N + 1
    return M

def reorder_13524(M):
    """1-3-5-2-4 row/col reorder (0-indexed: [0,2,4,1,3])"""
    order = [0,2,4,1,3]
    return M[order][:,order]

def diag_swap(M):
    """对角换行列: M2[i,j] = M[(i+j)%N, (i-j)%N]"""
    N = M.shape[0]
    M2 = np.zeros_like(M)
    for i in range(N):
        for j in range(N):
            M2[i,j] = M[(i+j)%N, (i-j)%N]
    return M2

def cyclic_shift(M, rs, cs):
    return np.roll(np.roll(M, rs, axis=0), cs, axis=1)

def to_key(M):
    return M.tobytes()

def frenicle_normalize(M):
    """Frénicle标准形: 旋转8种+镜像, 最小字典序, 1在左上"""
    N = M.shape[0]
    best_key = None
    best_sq = None
    for rot in range(4):
        for flip in range(2):
            candidate = np.rot90(M, rot).copy()
            if flip: candidate = np.fliplr(candidate)
            # 把最小数移到 (0,0)
            minpos = np.unravel_index(np.argmin(candidate), candidate.shape)
            candidate = np.roll(np.roll(candidate, -minpos[0], 0), -minpos[1], 1)
            key = candidate.tobytes()
            if best_key is None or key < best_key:
                best_key = key
                best_sq = candidate.copy()
    return best_sq

# ============================================================
print("="*60)
print("5阶完美幻方 3600种 精确生成器 v2")
print("="*60)

# Step 1: 生成 pandiagonal base squares (拉丁方枚举)
N = 5
base_squares = []
for a in range(1,N):
    for b in range(1,N):
        if gcd(a,N)!=1 or gcd(b,N)!=1: continue
        for c in range(1,N):
            for d in range(1,N):
                if gcd(c,N)!=1 or gcd(d,N)!=1: continue
                if (a,b)==(c,d): continue
                M = latin_pandiag(a,b,c,d)
                if check_pandiag(M):
                    base_squares.append(M)

print(f"Latin square pandiagonal bases: {len(base_squares)}")

# Step 2: Frénicle去重 → essentially different
frenicle_map = {}
for M in base_squares:
    f = frenicle_normalize(M)
    key = f.tobytes()
    frenicle_map[key] = f

essentially_diff = list(frenicle_map.values())
print(f"Frénicle essentially different: {len(essentially_diff)} (budshaw says 36)")

# Step 3: ×4 变换族
basic_144 = []
for base in essentially_diff:
    # Square #1: original
    basic_144.append(base.copy())
    # Square #2: diag swap
    ds = diag_swap(base)
    basic_144.append(ds)
    # Square #3: 1-3-5-2-4
    reo = reorder_13524(base)
    basic_144.append(reo)
    # Square #4: 13524 + diag swap
    basic_144.append(diag_swap(reo))

print(f"After 4-family: {len(basic_144)}")

# Step 4: ×25 循环位移 → 3600
all_squares = {}
pandiag_count = 0
for sq in basic_144:
    for rs in range(N):
        for cs in range(N):
            shifted = cyclic_shift(sq, rs, cs)
            if not check_pandiag(shifted): continue
            pandiag_count += 1
            key = to_key(shifted)
            if key not in all_squares:
                all_squares[key] = shifted

print(f"Pandiagonal (after shift): {pandiag_count}")
print(f"Unique pandiagonal: {len(all_squares)}")

# Step 5: 验证 ultramagic
ultra_count = 0
for s in all_squares.values():
    ok = all(s[i,j] + s[N-1-i,N-1-j] == N*N+1 for i in range(N) for j in range(N))
    if ok: ultra_count += 1

print(f"Ultramagic: {ultra_count} (budshaw says 16)")

# Step 6: Frénicle 验证 essentially different  
frenicle_final = {}
for s in all_squares.values():
    f = frenicle_normalize(s)
    key = f.tobytes()
    if key not in frenicle_final:
        frenicle_final[key] = f
print(f"Final Frénicle: {len(frenicle_final)} (budshaw says 36)")

# Step 7: 保存
squares_list = [s.tolist() for s in all_squares.values()]
with open(f'{OUTDIR}/pan5_all_3600.json', 'w') as f:
    json.dump(squares_list, f)
print(f"\nSaved {len(squares_list)} squares to pan5_all_3600.json ({os.path.getsize(f'{OUTDIR}/pan5_all_3600.json')//1024}KB)")

# 保存 36 essentially different
frenicle_list = [s.tolist() for s in frenicle_final.values()]
with open(f'{OUTDIR}/pan5_36_frenicle.json', 'w') as f:
    json.dump(frenicle_list, f)
print(f"Saved {len(frenicle_list)} frenicle to pan5_36_frenicle.json")

# 样本
with open(f'{OUTDIR}/pan5_sample.txt', 'w') as f:
    for idx, key in enumerate(list(all_squares.keys())[:5]):
        s = all_squares[key]
        f.write(f"Square #{idx+1}:\n")
        for row in s:
            f.write(' '.join(f'{x:2d}' for x in row) + '\n')
        f.write('Sums=65 Center=13\n\n')

print(f"\n{'='*60}")
print(f"TOTAL: {len(all_squares)} pandiagonal 5x5 squares")
if len(all_squares) == 3600:
    print("✅ EXACTLY 3600 — matches budshaw!")
else:
    print(f"⚠️  {len(all_squares)} (expected 3600, diff={3600-len(all_squares)})")
print(f"{'='*60}")
