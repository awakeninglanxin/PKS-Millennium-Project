# -*- coding: utf-8 -*-
"""GPU 基准测试 + 文件上传"""
import paramiko

HOST, PORT, USER, PASS = 'connect.nmb1.seetacloud.com', 12014, 'root', 'Ubso9y4t4Vl1'

def ssh(cmd, timeout=60):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    c.close()
    return o, e

# CuPy 矩阵乘法基准
mm_test = """
import cupy as cp, time
cp.cuda.Device(0).use()
for n in [2000, 5000, 10000]:
    a = cp.random.randn(n, n, dtype=cp.float32)
    b = cp.random.randn(n, n, dtype=cp.float32)
    cp.cuda.Stream.null.synchronize()
    t = time.time()
    c = a @ b
    cp.cuda.Stream.null.synchronize()
    dt = time.time() - t
    gflops = 2 * n**3 / dt / 1e9
    print(f"{n}x{n}: {dt*1000:.0f}ms, {gflops:.0f} GFLOPS")
"""

print("=== CuPy 矩阵乘法 (RTX 4080 SUPER) ===")
o, e = ssh(f"python3 -c '{mm_test}'", 120)
print(o)
if e: print("ERR:", e[:200])

# PyTorch 状态
print("\n=== PyTorch ===")
o, e = ssh("python3 -c 'import torch; print(torch.__version__)' 2>&1", 10)
print(o or "还在安装中...")

# 素数筛 CPU vs GPU
sieve_test = """
import cupy as cp, numpy as np, time

def cpu_sieve(n):
    is_prime = np.ones(n+1, dtype=bool)
    is_prime[:2] = False
    lim = int(n**0.5)+1
    for i in range(2, lim):
        if is_prime[i]:
            is_prime[i*i:n+1:i] = False
    return np.flatnonzero(is_prime).astype(np.int64)

n = 10_000_000
t0 = time.time()
p = cpu_sieve(n)
dt = time.time() - t0
print(f"CPU素数筛 n={n:,}: {len(p):,} primes, {dt:.1f}s")
"""

print("\n=== CPU 素数筛基准 ===")
o, e = ssh(f"python3 -c '{sieve_test}'", 120)
print(o)
