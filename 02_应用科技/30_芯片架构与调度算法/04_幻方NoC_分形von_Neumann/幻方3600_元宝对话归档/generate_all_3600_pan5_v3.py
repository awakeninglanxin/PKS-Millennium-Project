#!/usr/bin/env python3
"""5阶完美幻方 3600种 精确生成器 v3 — 骑士步双网格法
算法: budshaw.ca Pandiagonal.html Method I (Margossian cavaliere)
核心: 分组填充 + 4-family + 25 cyclic shift
"""
import numpy as np
from math import gcd
import json, os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

def check_pandiag(M):
    N=5; ms=65
    for k in range(N):
        if M[k].sum()!=ms or M[:,k].sum()!=ms: return False
    if sum(M[i,i] for i in range(N))!=ms: return False
    if sum(M[i,N-1-i] for i in range(N))!=ms: return False
    for k in range(1,N):
        if sum(M[i,(i+k)%N] for i in range(N))!=ms: return False
        if sum(M[i,(i-k)%N] for i in range(N))!=ms: return False
    return True

def knight_group_fill(dr, dc, start_r=0, start_c=0, N=5):
    """
    骑士步分组填充法 (正确的 Margossian 方法)
    
    不是逐格走 (那会5步绕回原点), 而是分 5 组:
    第 0 组: start at (start_r, start_c), fill values 1,6,11,16,21
    第 1 组: start at (start_r+1, start_c), fill values 2,7,12,17,22
    ...
    每组内用骑士步走 N 次覆盖整行/列
    """
    M = np.zeros((N, N), dtype=int)
    for group in range(N):
        r = (start_r + group) % N
        c = start_c
        for step in range(N):
            val = group + step * N + 1  # 1,2,3,4,5 for group0; 6,7,8,9,10 for group1...
            M[r, c] = val
            r = (r + dr) % N
            c = (c + dc) % N
    return M

def reorder_13524(M):
    o = np.array([0,2,4,1,3])
    return M[o][:,o]

def diag_swap(M):
    N=5; M2=np.zeros_like(M)
    for i in range(N):
        for j in range(N):
            M2[i,j]=M[(i+j)%N,(i-j)%N]
    return M2

def cyclic(M, rs, cs):
    return np.roll(np.roll(M,rs,0),cs,1)

def keyof(M): return M.tobytes()

def frenicle(M):
    N=5; bk=None; bs=None
    for r in range(4):
        for f in range(2):
            c=np.rot90(M,r).copy()
            if f:c=np.fliplr(c)
            mn=np.unravel_index(np.argmin(c),c.shape)
            c=np.roll(np.roll(c,-mn[0],0),-mn[1],1)
            k=c.tobytes()
            if bk is None or k<bk: bk=k; bs=c.copy()
    return bs

# ============================================================
print("="*60)
print("5阶完美幻方 3600种 v3 — 骑士步双网格填充")
print("="*60)

N=5

# Step 1: 枚举所有合法 (dr,dc) + 所有起始位置 → base
# dr,dc 与 5 互素, dr≠dc, dr≠0, dc≠0
legal_steps = []
for dr in range(1,N):
    for dc in range(1,N):
        if gcd(dr,N)==1 and gcd(dc,N)==1 and dr!=dc:
            legal_steps.append((dr,dc))
print(f"Legal knight steps: {len(legal_steps)} ({legal_steps})")

# 所有 (dr,dc) 组合 × 5种起始组偏移
bases = {}
for dr,dc in legal_steps:
    for g in range(N):  # 起始组偏移
        M = knight_group_fill(dr, dc, start_r=0, start_c=g)
        if check_pandiag(M):
            f = frenicle(M)
            k = f.tobytes()
            if k not in bases:
                bases[k] = f

print(f"Frénicle-distinct base squares: {len(bases)} (budshaw=36)")

# Step 2: ×4 family
family_4 = []
for base in bases.values():
    family_4.append(base.copy())           # #1
    family_4.append(diag_swap(base))       # #2
    family_4.append(reorder_13524(base))   # #3
    family_4.append(diag_swap(reorder_13524(base)))  # #4
print(f"After 4-family: {len(family_4)}")

# Step 3: ×25 cyclic shift → and only keep pandiagonal
all_sq = {}
for sq in family_4:
    for rs in range(N):
        for cs in range(N):
            s = cyclic(sq, rs, cs)
            if not check_pandiag(s): continue
            k = keyof(s)
            if k not in all_sq:
                all_sq[k] = s

print(f"Unique pandiagonal: {len(all_sq)} (expected 3600)")

# Verify ultramagic
ultra = sum(1 for s in all_sq.values() if all(
    s[i,j]+s[N-1-i,N-1-j]==N*N+1 for i in range(N) for j in range(N)))
print(f"Ultramagic: {ultra} (budshaw=16)")

# Frenicle final
ff = {}
for s in all_sq.values():
    f = frenicle(s); k = f.tobytes()
    if k not in ff: ff[k]=f
print(f"Final Frenicle: {len(ff)} (budshaw=36)")

# Save
total = len(all_sq)
out_json = f'{OUTDIR}/pan5_all_{total}.json'
sqlist = [s.tolist() for s in all_sq.values()]
with open(out_json,'w') as fj: json.dump(sqlist, fj)
print(f"\nSaved {total} squares → {os.path.getsize(out_json)//1024}KB")

if total==3600: print("✅ EXACTLY 3600 — matches budshaw!")
else: print(f"⚠️ {total}/3600 (off by {3600-total})")
