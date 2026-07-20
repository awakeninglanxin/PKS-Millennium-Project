# -*- coding: utf-8 -*-
"""GPU 综合实验 — Farey时钟分相 + BSD Euler积 + Servi-Croft核"""
import cupy as cp, numpy as np, time, json, os

OUT = '/root/autodl-tmp/gpu_results'
os.makedirs(OUT, exist_ok=True)
cp.cuda.Device(0).use()

print("="*60)
print(f"GPU: RTX 4080 SUPER | CuPy {cp.__version__} | {cp.cuda.Device(0).compute_capability}")
print("="*60)

# ============================================================
# 实验一: Farey 时钟分相 — GPU 加速版
# ============================================================
print("\n[实验一] Farey 时钟分相 GPU SM 调度仿真")

def farey_sequence(max_denom):
    seq = [(0, 1), (1, 1)]
    a, b, c, d = 0, 1, 1, max_denom
    while c <= max_denom:
        k = (max_denom + b) // d
        a, b, c, d = c, d, k*c - a, k*d - b
        if b <= max_denom and d <= max_denom:
            seq.append((c, d))
    return sorted(set(seq), key=lambda x: x[0]/x[1])

farey = farey_sequence(200)
print(f"  Farey(200): {len(farey)} 个分数")

N_SM = 128
t = cp.linspace(0, 1, 2000, dtype=cp.float32)
pulse_width = 0.05  # 脉冲宽度/周期

# 三种分相方案
phases = {
    'none': cp.zeros(N_SM, dtype=cp.float32),
    'uniform': cp.linspace(0, 1, N_SM, endpoint=False, dtype=cp.float32),
}

# Farey: 取等间距的 N_SM 个分数
step = max(1, (len(farey)-2)//(N_SM-1))
indices = [min(1+i*step, len(farey)-2) for i in range(N_SM-1)]
f_phases = [0.0] + [farey[idx][0]/farey[idx][1] for idx in indices]
phases['farey'] = cp.array(f_phases[:N_SM], dtype=cp.float32)

results = {}
for label, ph in phases.items():
    t0 = time.time()
    # GPU 并行: 所有 SM 的脉冲同时计算
    ph_gpu = cp.asarray(ph).reshape(-1, 1)
    t_gpu = cp.asarray(t).reshape(1, -1)
    # 高斯脉冲: exp(-((t-phase)/width)^2)
    diff = (t_gpu - ph_gpu) / pulse_width
    # wrap around
    diff_wrap = cp.minimum(cp.abs(diff), cp.abs(diff - 1.0/pulse_width))
    pulses = cp.exp(-diff_wrap**2)
    total_current = cp.sum(pulses, axis=0)
    peak = float(cp.max(total_current))
    avg = float(cp.mean(total_current))
    dt = time.time() - t0
    results[label] = {'peak': peak, 'avg': avg, 'time_ms': dt*1000}
    print(f"  {label:10s}: peak={peak/N_SM*100:.1f}%, avg={avg/N_SM:.1f}/SM, {dt*1000:.1f}ms")

peak_reduction = (1 - results['farey']['peak']/results['none']['peak']) * 100
print(f"  Farey 峰值降低: {peak_reduction:.1f}%")

# ============================================================
# 实验二: BSD 风格 Euler 积 — GPU 批量
# ============================================================
print("\n[实验二] BSD Euler 积 — CuPy 批量素数运算")

# 筛素数 (CPU)
n_max = 5_000_000
is_prime = np.ones(n_max+1, dtype=bool); is_prime[:2] = False
for i in range(2, int(n_max**0.5)+1):
    if is_prime[i]: is_prime[i*i:n_max+1:i] = False
primes = np.flatnonzero(is_prime).astype(np.int64)
print(f"  素数: {len(primes):,} 个 (max={primes[-1]:,})")

# GPU 批量 Euler 积
p_max_values = [1000, 10000, 100000, 500000, 1000000, 5000000]
bsd_times = {}

for pmax in p_max_values:
    mask = primes <= pmax
    p_sel = primes[mask]
    n_p = len(p_sel)
    if n_p == 0: continue

    # a_p 模拟 (简化: Sato-Tate)
    np.random.seed(42)
    a_p = 2 * np.sqrt(p_sel) * np.sin(np.random.vonmises(0, 0.5, n_p))

    t0 = time.time()
    # GPU: 批量 Euler 因子
    p_gpu = cp.asarray(p_sel, dtype=cp.float64)
    a_gpu = cp.asarray(a_p, dtype=cp.float64)
    inv_p = 1.0 / p_gpu
    # factor = 1 / (1 - a_p/p + 1/p)  = p / (p - a_p + 1)
    factor = p_gpu / (p_gpu - a_gpu + 1.0)
    product = float(cp.prod(factor))
    dt = time.time() - t0
    bsd_times[pmax] = {'n_primes': n_p, 'time_s': dt, 'L': product}
    print(f"  p_max={pmax:,}: {n_p:,} primes, L={product:.6e}, {dt*1000:.1f}ms")

# ============================================================
# 实验三: GPU vs CPU 加速比对比
# ============================================================
print("\n[实验三] CPU vs GPU 加速比")

# GPU: CuPy matmul
n = 10000
a_cp = cp.random.randn(n, n, dtype=cp.float32)
b_cp = cp.random.randn(n, n, dtype=cp.float32)
cp.cuda.Stream.null.synchronize()
t0 = time.time()
c_cp = a_cp @ b_cp
cp.cuda.Stream.null.synchronize()
gpu_time = time.time() - t0
gpu_tflops = 2 * n**3 / gpu_time / 1e12

# CPU: NumPy matmul
a_np = np.random.randn(n, n).astype(np.float32)
b_np = np.random.randn(n, n).astype(np.float32)
t0 = time.time()
c_np = a_np @ b_np
cpu_time = time.time() - t0
cpu_gflops = 2 * n**3 / cpu_time / 1e9

speedup = cpu_time / gpu_time
print(f"  GPU: {gpu_time:.3f}s ({gpu_tflops:.1f} TFLOPS)")
print(f"  CPU: {cpu_time:.3f}s ({cpu_gflops:.0f} GFLOPS)")
print(f"  加速比: {speedup:.0f}x")

# ============================================================
# 保存结果
# ============================================================
report = {
    'gpu': 'RTX 4080 SUPER 32GB',
    'farey': {k: {'peak': float(v['peak']), 'time_ms': v['time_ms']} for k, v in results.items()},
    'farey_peak_reduction_pct': peak_reduction,
    'bsd': {str(k): {'n_primes': v['n_primes'], 'time_s': v['time_s']} for k, v in bsd_times.items()},
    'matmul_gpu_tflops': gpu_tflops,
    'matmul_cpu_gflops': cpu_gflops,
    'matmul_speedup': speedup,
}

with open(f'{OUT}/gpu_results.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✅ 结果保存: {OUT}/gpu_results.json")
print("="*60)
