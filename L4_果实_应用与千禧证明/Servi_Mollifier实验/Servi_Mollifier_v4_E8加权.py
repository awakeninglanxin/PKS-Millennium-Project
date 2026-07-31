"""
Servi-Croft kernel v4 — E8 根向量加权
对比: T_30 binary filter vs E8 continuous weights
Hypothesis: E8 root system provides mathematically optimal prime-selective filter
"""
import numpy as np, math, os, time
from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. Prime / Non-prime classification
# ============================================================
def sieve_primes(N):
    is_p = np.ones(N+1, dtype=bool); is_p[:2] = False
    for i in range(2, int(N**0.5)+1):
        if is_p[i]: is_p[i*i:N+1:i] = False
    return is_p

# ============================================================
# 2. Kernel builders
# ============================================================
def servi_kernel(t, n, N_max):
    """Original Servi kernel: K(s;t) = cos(-t log n) n^{-1/2}"""
    return np.cos(-t * np.log(n)) * n**(-0.5)

def totative_30(n):
    """Croft T_30 totative filter: binary"""
    return 1.0 if (n % 30) in {1,7,11,13,17,19,23,29} else 0.0

def e8_weight(n):
    """
    E8 root vector weight: continuous spectral weight
    Based on E8 Coxeter number h=30 and root system Phi(E8)
    
    The 8 totatives of mod 30 correspond to the 8 simple roots of E8.
    Each root vector has a Coxeter exponent e_i, and the weight is:
      w(n) = sum_i cos(2*pi * e_i * dr(n) / h)
    where e_i are the Coxeter exponents: {1,7,11,13,17,19,23,29}
    """
    exponents = np.array([1,7,11,13,17,19,23,29])
    h = 30
    dr = n % 9
    if dr == 0: dr = 9  # digital root mapping
    # Projection: how well does dr(n) align with E8 root structure?
    phases = 2 * np.pi * exponents * dr / h
    return np.abs(np.sum(np.cos(phases))) / len(exponents)

def e8_weight_fast(n):
    """Vectorized E8 weight (handles scalar and array)"""
    if np.isscalar(n):
        n = np.array([n])
    exponents = np.array([1,7,11,13,17,19,23,29])
    h = 30
    dr = n % 9
    dr[dr == 0] = 9
    w = np.zeros_like(n, dtype=float)
    for e in exponents:
        w += np.cos(2*np.pi * e * dr / h)
    w = np.abs(w) / len(exponents)
    return w[0] if len(w) == 1 else w

# ============================================================
# 3. Prime-detection ratio (vectorized)
# ============================================================
def compute_ratio(t_values, N_max, weight_func, label):
    """Vectorized: compute Var_t[K, prime] / Var_t[K, nonprime]"""
    is_p = sieve_primes(N_max)
    n_arr = np.arange(1, N_max+1)
    
    # Vectorized kernel
    # K[t,n] = cos(-t * log n) * n^{-1/2} * w(n)
    log_n = np.log(n_arr)
    n_half = n_arr**(-0.5)
    w = weight_func(n_arr)
    
    # K[t,n] matrix: (n_t, N)
    K = np.outer(np.cos(np.outer(t_values, log_n)), np.ones(1)).reshape(len(t_values), -1)
    # Actually: K[t,n] = cos(t * log n) * n^{-1/2} * w(n)
    # cos(t*log_n) = [n_t x N]
    cos_term = np.cos(np.outer(t_values, -log_n))
    K = cos_term * n_half[np.newaxis, :] * w[np.newaxis, :]
    
    # Projection: mean over n
    K_prime = K[:, is_p[1:]]
    K_nonp = K[:, ~is_p[1:]]
    
    proj_p = np.mean(K_prime, axis=1)
    proj_np = np.mean(K_nonp, axis=1)
    
    var_p = np.var(proj_p)
    var_np = np.var(proj_np)
    
    return var_p / max(var_np, 1e-15), var_p, var_np

# ============================================================
# 4. Multi-scale test
# ============================================================
def test_all(N_list, n_t=200):
    t_set = np.linspace(10, 50, n_t)
    results = {'T_30_binary': [], 'E8_weighted': [], 'Vanilla_Servi': []}
    
    for N in N_list:
        print(f'  N={N:4d}...', end=' ', flush=True)
        t0 = time.time()
        
        # Vanilla (weight=1)
        def w_vanilla(n): return np.ones_like(n, dtype=float)
        r_v, vp, vnp = compute_ratio(t_set, N, w_vanilla, 'vanilla')
        results['Vanilla_Servi'].append((N, r_v))
        
        # T_30 binary
        def w_t30(n): return np.array([totative_30(int(x)) for x in n])
        r_t, _, _ = compute_ratio(t_set, N, w_t30, 'T30')
        results['T_30_binary'].append((N, r_t))
        
        # E8 weighted
        r_e, _, _ = compute_ratio(t_set, N, e8_weight_fast, 'E8')
        results['E8_weighted'].append((N, r_e))
        
        print(f'r_v={r_v:.2f} r_t={r_t:.1f} r_e={r_e:.1f} ({time.time()-t0:.1f}s)')
    
    return results

# ============================================================
# 5. Main
# ============================================================
def main():
    print('='*65)
    print('Servi-Croft v4: E8 Root Vector Weighted Kernel')
    print('='*65)
    
    # Quick test N=100
    Ns_quick = [40, 60, 80, 100]
    print('\nQuick test (N=40-100):')
    res_quick = test_all(Ns_quick, n_t=100)
    
    # Medium test N=200,300,500
    Ns_medium = [200, 300, 500]
    print('\nMedium test (N=200-500):')
    res_medium = test_all(Ns_medium, n_t=150)
    
    # Merge
    all_Ns = []
    all_data = {'T_30_binary': [], 'E8_weighted': [], 'Vanilla_Servi': []}
    for key in all_data:
        for N, r in res_quick[key] + res_medium[key]:
            all_data[key].append(r)
        if key == 'T_30_binary':
            all_Ns = [N for N, _ in res_quick[key] + res_medium[key]]
    
    all_data = {k: np.array(v) for k, v in all_data.items()}
    all_Ns = np.array(all_Ns)
    
    # ---- Plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    colors = {'Vanilla_Servi': 'gray', 'T_30_binary': 'forestgreen', 'E8_weighted': 'darkorange'}
    markers = {'Vanilla_Servi': 's', 'T_30_binary': 'o', 'E8_weighted': 'D'}
    
    for label, data in all_data.items():
        ax1.semilogy(all_Ns, data, marker=markers[label], color=colors[label],
                     label=label, linewidth=2, markersize=8)
    ax1.axhline(y=1.2, color='red', linestyle='--', alpha=0.5, label='Loiseau B-class threshold')
    ax1.set_xlabel('N_max'); ax1.set_ylabel('Prime-detection ratio (log)')
    ax1.set_title('E8 Weighted vs T_30 Binary Prime Detection')
    ax1.legend(); ax1.grid(True, alpha=0.3)
    
    # Bar plot at N=100
    x = np.arange(3)
    ax2.bar(x, [all_data[k][2] for k in ['Vanilla_Servi','T_30_binary','E8_weighted']],
            color=[colors[k] for k in ['Vanilla_Servi','T_30_binary','E8_weighted']])
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Vanilla Servi', 'T_30 Binary', 'E8 Weighted'])
    ax2.set_ylabel('Ratio @ N=100')
    ax2.set_title(f'N=100 Comparison')
    for i, (k, v) in enumerate([(k, all_data[k][2]) for k in ['Vanilla_Servi','T_30_binary','E8_weighted']]):
        ax2.text(i, v + 5, f'{v:.1f}', ha='center', fontweight='bold', fontsize=12)
    
    fig.suptitle('Servi-Croft v4: E8 Root Vector Weighted Kernel\n'
                 f'E8 Coxeter h=30, 240 root vectors → continuous T_30 weights',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_dir = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明'
    out_png = os.path.join(out_dir, 'Servi_Mollifier_v4_E8加权.png')
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
    print(f'\n[Saved] {out_png}')
    
    # Summary
    print('\n' + '='*65)
    print('v4 E8 Weighted Summary')
    print('='*65)
    for k in ['Vanilla_Servi', 'T_30_binary', 'E8_weighted']:
        d = all_data[k]
        print(f'  {k:15s}: N=100 ratio={d[2]:.1f}  '
              f'range=[{d.min():.1f}, {d.max():.1f}]  '
              f'stability: {"stable" if d[-1]/d[0]>0.1 else "decaying"}')

if __name__ == '__main__':
    main()
