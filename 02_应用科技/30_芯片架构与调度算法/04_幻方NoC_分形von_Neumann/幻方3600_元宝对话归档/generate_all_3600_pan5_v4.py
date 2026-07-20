#!/usr/bin/env python3
"""5阶完美幻方 3600种 v4 — 从已知 pandiagonal base 生成
策略: 用一个已验证的 pandiagonal square, 枚举所有合法 (dr,dc) 填充,
      保留 pandiagonal 的 → 4-family → 25 cyclic → 3600
"""
import numpy as np; from math import gcd; import json, os
OUTDIR = os.path.dirname(os.path.abspath(__file__))

def pdiag(M):
    N=5;ms=65
    for k in range(N):
        if M[k].sum()!=ms or M[:,k].sum()!=ms: return False
    if sum(M[i,i] for i in range(N))!=ms: return False
    if sum(M[i,N-1-i] for i in range(N))!=ms: return False
    for k in range(1,N):
        if sum(M[i,(i+k)%N] for i in range(N))!=ms: return False
        if sum(M[i,(i-k)%N] for i in range(N))!=ms: return False
    return True

def key(M): return M.tobytes()

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

def reorder_13524(M):
    o=np.array([0,2,4,1,3]); return M[o][:,o]

def diag_swap(M):
    N=5; M2=np.zeros_like(M)
    for i in range(N):
        for j in range(N): M2[i,j]=M[(i+j)%N,(i-j)%N]
    return M2

def shift(M,rs,cs): return np.roll(np.roll(M,rs,0),cs,1)

# ============================================================
print("="*60)
print("5阶 Pandiagonal 3600 v4 — 已知square扩展法")
print("="*60)

# THE canonical pandiagonal 5x5 (from budshaw, knight step 1,2)
CANONICAL = np.array([
    [ 1,  7, 13, 19, 25],
    [14, 20, 21,  2,  8],
    [22,  3,  9, 15, 16],
    [10, 11, 17, 23,  4],
    [18, 24,  5,  6, 12]
])
print(f"Canonical pandiagonal: {pdiag(CANONICAL)}")

# Step 1: 从 canonical 生成所有 base — 对每个合法 (dr,dc) 用 Siamese 方法填
# Siamese: 1 at center top, move (dr,dc), if occupied drop down 1
def siamese_fill(dr, dc, start_r=0, start_c=2):
    """Siamese method for 5x5. 1 goes at (start_r, start_c)"""
    N=5; M=np.zeros((N,N),dtype=int)
    r,c=start_r,start_c
    for v in range(1,N*N+1):
        while M[r,c]!=0:  # occupied → drop down
            r=(r+1)%N
        M[r,c]=v
        nr,nc=(r+dr)%N,(c+dc)%N
        if M[nr,nc]!=0:  # next occupied → drop instead
            r=(r+1)%N; c=c
        else:
            r,c=nr,nc
    return M

N=5
bases={}
for dr in range(1,N):
    for dc in range(1,N):
        if gcd(dr,N)!=1 or gcd(dc,N)!=1 or dr==dc: continue
        for sc in range(N):
            M=siamese_fill(dr,dc,start_c=sc)
            if pdiag(M):
                f=frenicle(M); k=key(f)
                if k not in bases: bases[k]=f

print(f"Siamese Frenicle bases: {len(bases)}")

# Also add known canonical
f=frenicle(CANONICAL); bases[key(f)]=f
print(f"+ canonical → {len(bases)} bases (budshaw=36)")

# Step 2: ×4
fam4=[]
for b in bases.values():
    fam4.extend([b.copy(), diag_swap(b), reorder_13524(b), diag_swap(reorder_13524(b))])
print(f"×4 family: {len(fam4)}")

# Step 3: ×25
all_sq={}
for sq in fam4:
    for rs in range(N):
        for cs in range(N):
            s=shift(sq,rs,cs)
            if pdiag(s):
                k=key(s)
                if k not in all_sq: all_sq[k]=s

print(f"Total pandiagonal: {len(all_sq)}")

# Frenicle
ff={}
for s in all_sq.values():
    f=frenicle(s); k=key(f)
    if k not in ff: ff[k]=f
print(f"Final Frenicle: {len(ff)}")

# Ultra
ultra=sum(1 for s in all_sq.values() if all(s[i,j]+s[4-i,4-j]==26 for i in range(5) for j in range(5)))
print(f"Ultramagic: {ultra}")

# Save
out=f'{OUTDIR}/pan5_{len(all_sq)}.json'
sqlist=[s.tolist() for s in all_sq.values()]
with open(out,'w') as fj: json.dump(sqlist,fj)
print(f"\nSaved → {os.path.getsize(out)//1024}KB")

if len(all_sq)==3600: print("✅ 3600!")
else: print(f"⚠️ {len(all_sq)}/3600")
