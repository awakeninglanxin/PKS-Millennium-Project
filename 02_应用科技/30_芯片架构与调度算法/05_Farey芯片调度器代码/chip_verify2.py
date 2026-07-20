"""
芯片分形 GPU验证 第二波：纯数学/逻辑实验
Exp4: Siamese反演公式正确性
Exp5: 泛幻方折断对角线和守恒
Exp6: 幻方层级Feigenbaum间距比
Exp7: Farey bc−ad=1 全验证
Exp8: 幻方路由表压缩比
"""
import numpy as np
import json, time, os

OUT = '/root/results2'
os.makedirs(OUT, exist_ok=True)
results = {}

# ═══════════════════════════════════
# Exp4: Siamese反演公式验证
# ═══════════════════════════════════
print("[Exp4] Siamese反演公式验证...")

def siamese_direct(n):
    """直接迭代法构造幻方"""
    M = np.zeros((n,n), dtype=int)
    i, j = 0, n//2
    for a in range(1, n*n+1):
        M[i,j] = a
        ni, nj = (i-1)%n, (j+1)%n
        if M[ni,nj] != 0: i = (i+1)%n
        else: i, j = ni, nj
    return M

def siamese_inverse_formula(i, j, n):
    """反演公式: a(i,j) = n·mod(i+j-m,n) + mod(i+2j-2m,n) + 1"""
    m = (n+1)//2
    return n * ((i + j - m) % n) + ((i + 2*j - 2*m) % n) + 1

errors = 0
for n in [3,5,7,9,11,13]:
    M_direct = siamese_direct(n)
    err_n = 0
    for i in range(n):
        for j in range(n):
            a_formula = siamese_inverse_formula(i, j, n)
            if a_formula != M_direct[i,j]:
                err_n += 1
    errors += err_n
    print(f"  n={n}: {err_n} errors")

results['siamese_formula'] = {
    'total_errors': errors,
    'tested_positions': sum(n*n for n in [3,5,7,9,11,13]),
    'pass': errors == 0
}
print(f"  => {'PASS' if errors==0 else 'FAIL'} ({results['siamese_formula']['tested_positions']} positions)")

# ═══════════════════════════════════
# Exp5: 泛幻方折断对角线和守恒
# ═══════════════════════════════════
print("\n[Exp5] 泛幻方折断对角线验证...")

def check_pandiagonal(M):
    n = M.shape[0]
    S = n*(n*n+1)//2  # 幻和
    broken_ok = 0
    broken_total = 0
    
    # 所有折断对角线 (wrapping)
    for start in range(n):
        # 方向1: 右下 (↘)
        s = sum(M[(start+k)%n, k%n] for k in range(n))
        if s == S: broken_ok += 1
        broken_total += 1
        
        # 方向2: 左下 (↙)  
        s = sum(M[(start+k)%n, (n-1-k)%n] for k in range(n))
        if s == S: broken_ok += 1
        broken_total += 1
    
    return broken_ok, broken_total

# 测试标准幻方 vs 泛幻方
for n, label in [(3,'普通'), (5,'泛幻方?'), (7,'泛幻方?')]:
    M = siamese_direct(n)
    ok, total = check_pandiagonal(M)
    print(f"  {n}阶{label}: {ok}/{total} 折断对角线守恒")
    results[f'pandiagonal_{n}'] = {'ok': ok, 'total': total, 'rate': ok/total}

# ═══════════════════════════════════
# Exp6: 幻方层级Feigenbaum间距比
# ═══════════════════════════════════
print("\n[Exp6] 幻方层级间距比...")

# 层级: L0(3)→L1(5)→L2(7)→L3(8)
# tile数: 9→25→49→64
tiles = [9, 25, 49, 64]
for i in range(len(tiles)-2):
    d1 = tiles[i+1] - tiles[i]
    d2 = tiles[i+2] - tiles[i+1]
    if d2 > 0:
        ratio = d1/d2
        print(f"  ({tiles[i+1]}-{tiles[i]})/({tiles[i+2]}-{tiles[i+1]}) = {d1}/{d2} = {ratio:.3f}")
    else:
        ratio = float('inf')
        print(f"  ratio = inf (d2=0)")

delta_ref = 4.669
ratios = [(25-9)/(49-25), (49-25)/(64-49)]  # 0.667, 1.6
results['feigenbaum_spacing'] = {
    'ratios': ratios,
    'delta_ref': delta_ref,
    'deviation_pct': [abs(r-delta_ref)/delta_ref*100 for r in ratios]
}
print(f"  Feigenbaum δ=4.669, 实测比={ratios}, 偏离={results['feigenbaum_spacing']['deviation_pct']}%")
print(f"  => 不满足Feigenbaum收敛（层级数太少，需要5+层才有意义）")

# ═══════════════════════════════════
# Exp7: Farey bc−ad=1 全验证
# ═══════════════════════════════════
print("\n[Exp7] Farey bc−ad=1 验证...")

def farey_sequence(N):
    a, b, c, d = 0, 1, 1, N
    seq = [(a,b)]
    while c <= N:
        k = (N + b) // d
        a, b, c, d = c, d, k*c - a, k*d - b
        seq.append((a,b))
    return seq

farey_errors = 0
farey_pairs = 0
for N in range(2, 21):
    F = farey_sequence(N)
    for k in range(len(F)-1):
        a,b = F[k]; c,d = F[k+1]
        if b*c - a*d != 1:
            farey_errors += 1
        farey_pairs += 1

print(f"  测试 N=2..20, {farey_pairs}对相邻分数")
print(f"  bc−ad=1 违反次数: {farey_errors}")
results['farey_bcad'] = {
    'pairs_tested': farey_pairs,
    'errors': farey_errors,
    'pass': farey_errors == 0
}
print(f"  => {'PASS' if farey_errors==0 else 'FAIL'}")

# ═══════════════════════════════════
# Exp8: 幻方路由表压缩比
# ═══════════════════════════════════
print("\n[Exp8] 幻方路由表压缩比...")

for n in [3, 5, 7, 8]:
    N_tiles = n * n
    # 传统全表: 每个tile存储N_tiles个路由项, 每项16B(坐标+距离)
    traditional_bytes = N_tiles * N_tiles * 16
    # 幻方Siamese: 6个参数, 每个4B, 不分tile(全局)
    magic_bytes = 6 * 4
    compression = traditional_bytes / magic_bytes if magic_bytes > 0 else float('inf')
    
    print(f"  {n}阶({N_tiles}tiles): 传统{traditional_bytes/1024:.1f}KB vs 幻方{magic_bytes}B "
          f"= 压缩{compression:.0f}x")
    
    results[f'route_compression_{n}'] = {
        'tiles': N_tiles,
        'traditional_KB': round(traditional_bytes/1024, 1),
        'magic_B': magic_bytes,
        'compression_ratio': round(compression, 0)
    }

# ═══════════════════════════════════
# 保存结果
# ═══════════════════════════════════
with open(f'{OUT}/results2.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n全部完成! {OUT}/results2.json")
print(f"\n核心发现:")
print(f"  Exp4: Siamese反演公式 {'PASS' if results['siamese_formula']['pass'] else 'FAIL'}")
print(f"  Exp5: 泛幻方折断对角线守恒率: {results['pandiagonal_3']['rate']:.0%}/{results['pandiagonal_5']['rate']:.0%}/{results['pandiagonal_7']['rate']:.0%}")
print(f"  Exp6: 层级间距比 = {ratios}, 偏离δ={results['feigenbaum_spacing']['deviation_pct']}%")
print(f"  Exp7: Farey bc−ad=1 {'PASS' if results['farey_bcad']['pass'] else 'FAIL'}")
print(f"  Exp8: 7阶路由压缩 = {results['route_compression_7']['compression_ratio']:.0f}x")
