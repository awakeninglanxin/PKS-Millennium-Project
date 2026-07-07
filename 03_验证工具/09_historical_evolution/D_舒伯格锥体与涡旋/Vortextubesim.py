import numpy as np
import matplotlib.pyplot as plt  # 确保此行已被正确导入
from matplotlib.animation import FuncAnimation

# 设置参数
n = 64
dt = 0.3
mu = 0.001
v = np.zeros((n, n, 2))

# 初始化速度场
for i in range(n):
    for j in range(n):
        if i < 5:
            v[i, j] = [0.1, 0]
        if (i - n/4)**2 + (j - n/2)**2 < 16:
            v[i, j] = [0, 0]

# 创建动画
fig, ax = plt.subplots()

def update(frame):
    global v
    v_new = np.zeros_like(v)
    for i in range(1, n-1):
        for j in range(1, n-1):
            # 计算下一个时间步的速度
            i2, j2 = np.clip(np.array([i, j]) - n * dt * v[i, j], 0, n-1).astype(int)
            v_new[i, j] = v[i2, j2]

    # 应用傅里叶变换
    v_fft = np.fft.fft2(v_new, axes=(0, 1))
    kx, ky = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n))
    k_squared = kx**2 + ky**2 + 1e-10
    decay = np.exp(-k_squared * dt * mu)
    decay_expanded = decay[..., np.newaxis]

    radial_component = np.stack((-ky, kx), axis=-1) * v_fft / (k_squared[..., np.newaxis])
    v_new = np.real(np.fft.ifft2(v_fft * decay_expanded - radial_component, axes=(0, 1)))

    # 计算涡度
    vorticity = (np.roll(v_new[..., 1], -1, axis=0) - np.roll(v_new[..., 1], 1, axis=0) -
                 (np.roll(v_new[..., 0], -1, axis=1) - np.roll(v_new[..., 0], 1, axis=1))) / 2
    ax.clear()
    ax.imshow(vorticity, origin='lower', cmap='twilight', interpolation='bilinear')
    ax.set_title(f"Time step: {frame}")
    v = v_new

ani = FuncAnimation(fig, update, frames=1550, interval=5, repeat=False)
plt.show()
