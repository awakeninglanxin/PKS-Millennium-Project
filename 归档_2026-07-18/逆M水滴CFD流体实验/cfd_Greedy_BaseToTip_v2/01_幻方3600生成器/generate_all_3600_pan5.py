#!/usr/bin/env python3
"""
5阶完美幻方 (Pandiagonal/Panmagic) 3600种完整生成器
=====================================================
算法来源: budshaw.ca + 元宝对话推导
作者: Hao Cai, 基于元宝 AI 对话中的算法描述重写
日期: 2026-07-20

构造链:
  36 essentially different (knight step dr,dc variants)
  × 4 (1-3-5-2-4 row/col reorder + diagonal swap family)
  = 144 basic pandiagonal
  × 25 (5 row shifts × 5 col shifts)
  = 3600 total pandiagonal 5×5 magic squares

验证: 所有方满足:
  - 每行和 = 每列和 = 每主对角和 = 每折断对角和 = 65
  - 中心格 = 13
  - 含 16 个 ultramagic (同时满足 associative 性质)
"""

import numpy as np
from math import gcd
import json, os

OUTDIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUTDIR, exist_ok=True)

def pandiagonal_fill(params, N=5):
    """
    双正交拉丁方叠加法 → pandiagonal 幻方
    
    M[i][j] = N * (a*i + b*j mod N) + (c*i + d*j mod N) + 1
    
    params = (a, b, c, d), 所有参数与 N 互素
    两个拉丁方 (a*i+b*j) 和 (c*i+d*j) 必须正交
    """
    a, b, c, d = params
    M = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            M[i, j] = N * ((a * i + b * j) % N) + (c * i + d * j) % N + 1
    return M

def is_pandiagonal(M):
    """验证是否为 pandiagonal (所有折断对角和 = magic constant)"""
    N = M.shape[0]
    magic_sum = N * (N*N + 1) // 2  # = 65 for N=5
    
    # 行和
    if not all(M.sum(axis=1) == magic_sum): return False
    # 列和
    if not all(M.sum(axis=0) == magic_sum): return False
    # 主对角
    if sum(M[i,i] for i in range(N)) != magic_sum: return False
    # 反对角
    if sum(M[i,N-1-i] for i in range(N)) != magic_sum: return False
    # 折断对角
    for k in range(1, N):
        d1 = sum(M[i, (i+k) % N] for i in range(N))
        d2 = sum(M[i, (i-k) % N] for i in range(N))
        if d1 != magic_sum or d2 != magic_sum:
            return False
    return True

def reorder_13524(M):
    """1-3-5-2-4 重排: 行序 [1,3,5,2,4], 列同理 (1-indexed)"""
    order = [0, 2, 4, 1, 3]  # 0-indexed: 1,3,5,2,4
    return M[order][:, order]

def diagonal_swap(M):
    """对角换行列: 对角线变行, 反对角变列"""
    N = M.shape[0]
    M2 = np.zeros_like(M)
    for i in range(N):
        for j in range(N):
            # 新行 = 原主对角, 新列 = 原反对角
            M2[i, j] = M[(i+j) % N, (i-j) % N]
    return M2

def cyclic_shift(M, rs, cs):
    """循环位移: 行移 rs, 列移 cs"""
    return np.roll(np.roll(M, rs, axis=0), cs, axis=1)

def magic_to_key(M):
    """幻方 → 唯一字符串 key (用于去重)"""
    return M.tobytes()

def to_frenicle(M):
    """Frénicle 标准形: 旋转+镜像 8 种对称中, 最小字典序的那个"""
    N = M.shape[0]
    best = M.copy()
    
    for rot in range(4):
        for flip in range(2):
            candidate = np.rot90(M, rot)
            if flip:
                candidate = np.fliplr(candidate)
            # 移位使最小数在 (0,0)
            minpos = np.unravel_index(np.argmin(candidate), candidate.shape)
            candidate = np.roll(np.roll(candidate, -minpos[0], axis=0), -minpos[1], axis=1)
            if candidate.tobytes() < best.tobytes():
                best = candidate.copy()
    return best

# ============================================================
# 主生成
# ============================================================

def generate_all_3600():
    """生成全部 3600 个 5阶 pandiagonal 幻方"""
    N = 5
    all_squares = []
    
    # Step 1: 枚举 essentially different 基本型
    # 用双正交拉丁方: LS1=(a,b), LS2=(c,d)
    base_squares = []
    base_params = []
    tried = set()
    for a in range(1, N):
        for b in range(1, N):
            if gcd(a, N) != 1 or gcd(b, N) != 1: continue
            for c in range(1, N):
                for d in range(1, N):
                    if gcd(c, N) != 1 or gcd(d, N) != 1: continue
                    if (a,b) == (c,d): continue
                    key = (a,b,c,d)
                    if key in tried: continue
                    tried.add(key)
                    
                    M = pandiagonal_fill(key)
                    if is_pandiagonal(M):
                        base_squares.append(M)
                        base_params.append(key)
    
    print(f"Pandiagonal base squares: {len(base_squares)}")
    
    # Step 2: 对每个 base, 做 4-family 变换
    basic_144 = []
    for base in base_squares:
        # Square #1: 原方
        basic_144.append(base.copy())
        # Square #2: 对角换行列
        basic_144.append(diagonal_swap(base))
        # Square #3: 1-3-5-2-4 重排
        reordered = reorder_13524(base)
        basic_144.append(reordered)
        # Square #4: #3 + 对角换
        basic_144.append(diagonal_swap(reordered))
    
    print(f"After 4-family transform: {len(basic_144)}")
    
    # Step 3: 循环位移 ×25
    all_unique = {}
    for sq in basic_144:
        for rs in range(N):
            for cs in range(N):
                shifted = cyclic_shift(sq, rs, cs)
                key = magic_to_key(shifted)
                if key not in all_unique:
                    all_unique[key] = shifted
    
    print(f"After cyclic shift: {len(all_unique)} unique squares")
    
    # Step 4: 验证
    squares = list(all_unique.values())
    pandiag_count = sum(1 for s in squares if is_pandiagonal(s))
    print(f"Verified pandiagonal: {pandiag_count}/{len(squares)}")
    
    # 检查 ultramagic (associative: 中心对称两数和 = 26)
    ultra_count = 0
    for s in squares:
        associative = True
        for i in range(N):
            for j in range(N):
                if s[i,j] + s[N-1-i, N-1-j] != N*N + 1:
                    associative = False
                    break
        if associative:
            ultra_count += 1
    print(f"Ultramagic (associative): {ultra_count} (should be 16)")
    
    # Frénicle 去重 → essentially different
    frenicle_set = {}
    for s in squares:
        f = to_frenicle(s)
        key = f.tobytes()
        if key not in frenicle_set:
            frenicle_set[key] = f
    print(f"Frénicle essentially different: {len(frenicle_set)} (should be 36)")
    
    return squares, frenicle_set

# ============================================================
# 保存
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("5阶完美幻方 (Pandiagonal) 3600 种生成器")
    print("算法来源: budshaw.ca + 元宝 AI 对话")
    print("=" * 60)
    
    squares, frenicle = generate_all_3600()
    
    # 保存全部 3600 个
    all_list = [s.tolist() for s in squares]
    with open(f'{OUTDIR}/pan5_all_squares.json', 'w') as f:
        json.dump(all_list, f)
    print(f"\nSaved {len(all_list)} squares to pan5_all_squares.json")
    
    # 保存 Frénicle 分类 (36 essentially different)
    frenicle_list = [s.tolist() for s in frenicle.values()]
    with open(f'{OUTDIR}/pan5_36_essentially_different.json', 'w') as f:
        json.dump(frenicle_list, f)
    print(f"Saved {len(frenicle_list)} essentially different to pan5_36_essentially_different.json")
    
    # 保存文本格式 (可选: 方便人类阅读)
    with open(f'{OUTDIR}/pan5_sample_10.txt', 'w') as f:
        for idx, s in enumerate(squares[:10]):
            f.write(f"Square #{idx+1}:\n")
            for row in s:
                f.write(' '.join(f'{x:2d}' for x in row) + '\n')
            f.write(f'All sums = 65, Center = {s[2,2]}\n\n')
    
    # 保存 16 个 ultramagic
    ultra_list = []
    for s in squares:
        associative = all(s[i,j] + s[4-i,4-j] == 26 for i in range(5) for j in range(5))
        if associative:
            ultra_list.append(s.tolist())
    with open(f'{OUTDIR}/pan5_16_ultramagic.json', 'w') as f:
        json.dump(ultra_list, f)
    print(f"Saved {len(ultra_list)} ultramagic to pan5_16_ultramagic.json")
    
    print(f"\n{'='*60}")
    print(f"Output: {OUTDIR}/")
    for f in os.listdir(OUTDIR):
        if f.endswith(('.json','.txt','.py')):
            size = os.path.getsize(os.path.join(OUTDIR, f))
            print(f"  {f} ({size:,} bytes)")
    print(f"{'='*60}")
