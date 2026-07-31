import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

# Chen吸引子参数
a = 35
b = 3
c = 28


def chen(x, y, z, dt):
    dx = a * (y - x)
    dy = (c - a) * x - x * z + c * y
    dz = x * y - b * z
    return x + dx * dt, y + dy * dt, z + dz * dt


def inverse_transform(x, y, z):
    # 反映射：内外翻转
    return -x, -y, -z


def scale_factor(t, alpha=0.001):
    # 随时间增长的缩放因子
    return 1 + alpha * t


# 时间参数
dt = 0.001  # 更小的时间步长
t_max = 50
steps = int(t_max / dt)

# 初始化
x, y, z = 5., 10., 15.  # 更适合的初始值
trajectory = []
colors = []

for i in range(steps):
    t = i * dt
    trajectory.append((x, y, z))

    # 每50步进行内外翻转
    if i % 50 == 0:
        x, y, z = inverse_transform(x, y, z)

    # Chen系统的时间步进
    x, y, z = chen(x, y, z, dt)

    # 颜色变化：基于时间t映射到颜色空间
    colors.append(t / t_max)  # 标准化时间到0-1

trajectory = np.array(trajectory)

# 应用空间缩放因子
scaled_trajectory = []
for i in range(steps):
    t = i * dt
    S = scale_factor(t, alpha=0.001)  # 更小的缩放速度
    scaled_trajectory.append(trajectory[i] * S)

scaled_trajectory = np.array(scaled_trajectory)

# 可视化
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制轨迹，使用颜色映射表示时间变化
for i in range(len(scaled_trajectory) - 1):
    ax.plot(
        scaled_trajectory[i:i + 2, 0],
        scaled_trajectory[i:i + 2, 1],
        scaled_trajectory[i:i + 2, 2],
        color=cm.plasma(colors[i])  # 使用颜色映射
    )

ax.set_title("Chen Attractor with Inverse Transformation and Scaling")
plt.show()
