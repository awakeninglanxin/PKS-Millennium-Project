# 1. Farey 锚点生成（主 cardioid 上 p/q ≤ Qmax）
def bud_attachment(p, q):
    t = 2*np.pi * p/q
    return 0.5*np.exp(1j*t) - 0.25*np.exp(2j*t)   # 头尖

def bud_center_approx(p, q):
    """粗估：沿 cardioid 法向内退 ~1/(4q²)"""
    c_tip = bud_attachment(p, q)
    normal = -np.exp(1j*t)  # cardioid 内法向
    return c_tip + normal * (1/(4*q*q))

# 2. 360° 角向采样 + smooth iter
def angular_signature(c0, R, N=512, maxiter=512):
    thetas = np.linspace(0, 2*np.pi, N, endpoint=False)
    pts = c0 + R * np.exp(1j*thetas)
    iters = gpu_mandelbrot_batch(pts, maxiter)     # CUDA kernel 一把出
    # smooth
    smoothed = iters + 1 - np.log(np.log(np.abs(z_final))) / np.log(2)
    return thetas, smoothed

# 3. FFT 读 p,q
def fft_read_pq(sig, N):
    S = np.fft.rfft(sig)
    mag = np.abs(S)
    q_est = np.argmax(mag[1:]) + 1          # 跳过 dc
    phase = np.angle(S[q_est])
    p_est = (phase / (2*np.pi) * q_est) % q_est
    return p_est, q_est, mag

# 4. 接上一轮的 DTW 聚类：每个样本的 (type_id, p_fft, q_fft) 三元组
#    → 做交叉表：type_X 是否全集中在某 (p,q) 带？