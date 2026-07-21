#!/usr/bin/env python3
"""5阶泛对角幻方 完整3600种 — Siamese + 4-family + 25 cyclic"""
import numpy as np, os, json
from math import gcd

OUTDIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\02_应用科技\30_芯片架构与调度算法\04_幻方NoC_分形von_Neumann\幻方3600_元宝对话归档"
N = 5; MS = N*(N*N+1)//2

def pdiag(M):
    if (M.sum(0) != MS).any() or (M.sum(1) != MS).any(): return False
    if sum(M[i,i] for i in range(N))!=MS: return False
    if sum(M[i,N-1-i] for i in range(N))!=MS: return False
    for k in range(1,N):
        if sum(M[i,(i+k)%N] for i in range(N))!=MS: return False
        if sum(M[i,(i-k)%N] for i in range(N))!=MS: return False
    return True

def siamese(dr, dc, sc=2):
    """Siamese method: 1 at (0,sc), step (dr,dc), drop if occupied"""
    M = np.zeros((N,N), int)
    r, c = 0, sc
    for v in range(1, N*N+1):
        while M[r,c]: r = (r+1)%N
        M[r,c] = v
        nr, nc = (r+dr)%N, (c+dc)%N
        if M[nr,nc]: r = (r+1)%N
        else: r, c = nr, nc
    return M

def frenicle(M):
    bk, bs = None, None
    for ro in range(4):
        for f in range(2):
            c = np.rot90(M, ro).copy()
            if f: c = np.fliplr(c)
            mn = np.unravel_index(np.argmin(c), c.shape)
            c = np.roll(np.roll(c, -mn[0], 0), -mn[1], 1)
            k = c.tobytes()
            if bk is None or k < bk: bk, bs = k, c.copy()
    return bs

def dswap(M):
    M2 = np.zeros_like(M)
    for i in range(N):
        for j in range(N): M2[i,j] = M[(i+j)%N, (i-j)%N]
    return M2

def r13524(M):
    o = np.array([0,2,4,1,3])
    return M[o][:,o]

def shift(M, rs, cs):
    return np.roll(np.roll(M, rs, 0), cs, 1)

# ═══ Step 1: Siamese bases ═══
bases = {}
for dr in range(1, N):
    for dc in range(1, N):
        if gcd(dr,N)!=1 or gcd(dc,N)!=1 or dr==dc: continue
        for sc in range(N):
            M = siamese(dr, dc, sc)
            if pdiag(M):
                fr = frenicle(M); k = fr.tobytes()
                if k not in bases: bases[k] = fr

print(f"Siamese Frenicle bases: {len(bases)}")

# ═══ Step 2: 4-family ═══
all_squares = []
seen = set()
for M in bases.values():
    for Mf in [M, dswap(M), r13524(M), r13524(dswap(M))]:
        for rs in range(N):
            for cs in range(N):
                S = shift(Mf, rs, cs)
                if not pdiag(S): continue
                k = S.tobytes()
                if k not in seen:
                    seen.add(k)
                    all_squares.append(S.tolist())

print(f"4-family ×25 cyclic: {len(all_squares)} pandiagonal")

# ═══ Frenicle reduction ═══
fset = {}
for s in all_squares:
    fr = frenicle(np.array(s)); fset[fr.tobytes()] = fr
ess = [v.tolist() for v in list(fset.values())]
ultra = [s for s in all_squares if all(s[r][c]+s[N-1-r][N-1-c]==26 for r in range(N) for c in range(N))]
print(f"Essentially different: {len(ess)}  Ultramagic: {len(ultra)}")

# ═══ Save ═══
p = OUTDIR
json.dump(all_squares, open(os.path.join(p,'pan5_all_3600.json'),'w'))
json.dump(ess[:36], open(os.path.join(p,'pan5_36_frenicle.json'),'w'))
json.dump(ultra[:96], open(os.path.join(p,'pan5_16_ultramagic.json'),'w'))
print(f"\nSaved. 3600={os.path.getsize(os.path.join(p,'pan5_all_3600.json'))//1024}KB")
with open(os.path.join(p,'pan5_sample.txt'),'w') as f:
    for i,s in enumerate(all_squares[:5]):
        f.write(f"#{i+1}:\n")
        for r in s: f.write(' '.join(f'{v:2d}' for v in r)+'\n')
        f.write('\n')
print("Done!")
