import numpy as np
import cupy as cp
import math
from fractions import Fraction

# ==================== 1. Farey 序列生成 ====================
def farey_sequence(n: int):
    """
    返回所有分母 ≤ n 的最简真分数（升序），用于确定芽苞的 p/q。
    输出格式：[(p1,q1), (p2,q2), ...]
    """
    seq = []
    a, b, c, d = 0, 1, 1, n
    while True:
        k = (n + b) // d
        a, b, c, d = c, d, k*c - a, k*d - b
        if a >= b:
            break
        seq.append((a, b))
    return seq

# ==================== 2. 锚点坐标 ====================
def bud_attachment(p: int, q: int) -> complex:
    """主 cardioid 上 p/q 芽苞的头尖（attaching point）"""
    t = 2 * np.pi * p / q
    return 0.5 * np.exp(1j * t) - 0.25 * np.exp(2j * t)

def bud_center_approx(p: int, q: int) -> complex:
    """泡中心近似：沿 cardioid 内法向退 ~1/(4q²)"""
    c_tip = bud_attachment(p, q)
    t = 2 * np.pi * p / q
    normal = -np.exp(1j * t)          # 指向 cardioid 内部
    offset = 1.0 / (4 * q * q)
    return c_tip + normal * offset

# ==================== 3. GPU Mandelbrot kernel ====================
# 使用 CuPy ElementwiseKernel 进行批量迭代（每个像素一个线程）
mandel_kernel = cp.ElementwiseKernel(
    'raw T cx, raw T cy, int32 maxiter',
    'float32 out',
    '''
    T x = 0, y = 0;
    int i;
    for (i = 0; i < maxiter; ++i) {
        T x2 = x*x, y2 = y*y;
        if (x2 + y2 > 4.0f) break;
        T tmp = x2 - y2 + cx[i];
        y = 2*x*y + cy[i];
        x = tmp;
    }
    // smooth iteration count
    if (i == maxiter) {
        out = (float)maxiter;
    } else {
        float log_zn = 0.5f * log(x*x + y*y);
        float nu = log(log_zn / log(2.0f)) / log(2.0f);
        out = (float)i + 1.0f - nu;
    }
    ''',
    'mandel_smooth'
)

def mandelbrot_batch_gpu(c_points: np.ndarray, maxiter=512) -> np.ndarray:
    """
    输入：复数数组 (N,)  输出：平滑迭代次数 (N,)
    自动转换为 GPU array 并调用 kernel
    """
    cx = cp.asarray(c_points.real.astype(np.float32))
    cy = cp.asarray(c_points.imag.astype(np.float32))
    out = cp.empty(len(c_points), dtype=np.float32)
    mandel_kernel(cx, cy, maxiter, out)
    return cp.asnumpy(out)   # 搬回 CPU

# ==================== 4. 360° 角向采样 ====================
def angular_signature(c0: complex, R: float, N=512, maxiter=512) -> np.ndarray:
    """
    以 c0 为极点，半径 R，N 个角度均匀采样
    返回平滑迭代序列 (N,)
    """
    thetas = np.linspace(0, 2*np.pi, N, endpoint=False)
    points = c0 + R * np.exp(1j * thetas)
    return mandelbrot_batch_gpu(points, maxiter)

# ==================== 5. FFT 提取 p/q ====================
def fft_extract_pq(signal: np.ndarray) -> tuple:
    """
    输入：平滑迭代序列 (N,)
    输出：(p_est, q_est, magnitude_spectrum)
    """
    N = len(signal)
    S = np.fft.rfft(signal)
    mag = np.abs(S)
    # 忽略 DC 分量，找最大幅值的频率索引
    q_est = np.argmax(mag[1:]) + 1          # 基频 = q
    phase = np.angle(S[q_est])
    # 相位对应 p/q * 2π，但需处理 wrap-around
    p_est = round((phase / (2*np.pi) * q_est) % q_est)
    return p_est, q_est, mag

# ==================== 6. 完整演示 ====================
if __name__ == "__main__":
    # 参数
    QMAX = 6               # 最大分母
    N_THETA = 128          # 角向采样点数（测试时可小一点）
    MAXITER = 1024
    RADIUS_FACTOR = 0.75   # 采样半径 = RADIUS_FACTOR * 芽苞半径估

    print("=== Farey 锚点生成与角向采样 ===")
    farey_list = farey_sequence(QMAX)
    print(f"Farey 序列（分母 ≤ {QMAX}）：")
    for p,q in farey_list:
        print(f"  p/q = {p}/{q}")

    results = []
    for p,q in farey_list:
        # 头尖锚点
        c_tip = bud_attachment(p, q)
        # 估算芽苞半径（gap theory）
        radius = RADIUS_FACTOR / (4 * q * q)
        # 采样
        sig = angular_signature(c_tip, radius, N=N_THETA, maxiter=MAXITER)
        # FFT 提取
        p_est, q_est, _ = fft_extract_pq(sig)
        results.append({
            'true_p': p, 'true_q': q,
            'est_p': p_est, 'est_q': q_est,
            'match': (p == p_est and q == q_est)
        })
        print(f"\n  p/q={p}/{q}  -> 估计 p={p_est}, q={q_est}, 匹配={results[-1]['match']}")

    match_rate = sum(r['match'] for r in results) / len(results)
    print(f"\n=== 总体匹配率: {match_rate:.0%} ===")