import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import time

# 配置参数 - 进一步优化性能
num_points = 800  # 进一步减少点的数量
marker_size = 6  # 进一步减小点的大小
marker_alpha = 0.1  # 设置透明度为0.1
d_param = 0.5  # 可调参数d，控制波形频率

# 创建3D图形和坐标轴 - 白色背景
fig = plt.figure(figsize=(10, 10), facecolor='white')
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('white')
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_zlim(-5, 5)

# 添加3D坐标轴
ax.set_xlabel('X axis', fontsize=12)
ax.set_ylabel('Y axis', fontsize=12)
ax.set_zlabel('Z axis', fontsize=12)
ax.xaxis.label.set_color('black')
ax.yaxis.label.set_color('black')
ax.zaxis.label.set_color('black')

# 设置坐标轴颜色
ax.tick_params(axis='x', colors='black')
ax.tick_params(axis='y', colors='black')
ax.tick_params(axis='z', colors='black')

# 初始化水母点的位置
np.random.seed(42)
theta = np.random.uniform(0, 2 * np.pi, num_points)
phi = np.random.uniform(0, np.pi, num_points)
r = np.random.uniform(5, 8, num_points)  # 水母主体半径

x = r * np.sin(phi) * np.cos(theta)
y = r * np.sin(phi) * np.sin(theta)
z = r * np.cos(phi) - 10  # 向下移动水母主体

# 添加触手点
num_tentacles = 6  # 减少触手数量
tentacle_points = num_points // 4
for i in range(num_tentacles):
    angle = 2 * np.pi * i / num_tentacles
    tentacle_z = np.linspace(-10, -20, tentacle_points)
    tentacle_x = 0.5 * np.cos(angle) * (tentacle_z + 10) + np.random.normal(0, 0.2, tentacle_points)
    tentacle_y = 0.5 * np.sin(angle) * (tentacle_z + 10) + np.random.normal(0, 0.2, tentacle_points)

    x = np.concatenate([x, tentacle_x])
    y = np.concatenate([y, tentacle_y])
    z = np.concatenate([z, tentacle_z])

# 更新点的数量
num_points = len(x)

# 预计算一些常量
tentacle_mask = z <= -15
body_mask = z > -15
tentacle_indices = []
for i in range(num_tentacles):
    start_idx = i * tentacle_points
    end_idx = min((i + 1) * tentacle_points, np.sum(tentacle_mask))
    if start_idx < end_idx:
        tentacle_indices.append(np.where(tentacle_mask)[0][start_idx:end_idx])

# 预计算角度和余弦值
angles = np.array([2 * np.pi * i / num_tentacles for i in range(num_tentacles)])
cos_angles = np.cos(angles)
sin_angles = np.sin(angles)

# 初始化散点图 - 使用固定蓝色
scatter = ax.scatter(x, y, z, s=marker_size, alpha=marker_alpha, c='blue')

# 初始化时间变量
t = 0

# 预计算映射常量
map_factor = 200 / 30
map_offset = 15


# 动画更新函数 - 进一步优化版本
def update(frame):
    global t

    # 复制原始位置
    new_x = x.copy()
    new_y = y.copy()
    new_z = z.copy()

    # 水母主体脉动效果 - 简化计算
    pulse = 0.2 * np.sin(t * 0.5) + 1.0

    # 应用脉动效果到水母主体
    if np.any(body_mask):
        radius = np.sqrt(new_x[body_mask] ** 2 + new_y[body_mask] ** 2 + (new_z[body_mask] + 10) ** 2)
        # 避免除零错误
        radius_safe = np.where(radius == 0, 1e-5, radius)
        scale_factor = pulse / radius_safe * 5
        new_x[body_mask] = new_x[body_mask] * scale_factor
        new_y[body_mask] = new_y[body_mask] * scale_factor
        new_z[body_mask] = (new_z[body_mask] + 10) * scale_factor - 10

    # 触手摆动效果 - 简化计算
    if np.any(tentacle_mask):
        for i, indices in enumerate(tentacle_indices):
            if len(indices) > 0:
                wave = 0.3 * np.sin(t + i * 0.5 + new_z[indices] * 0.5)
                new_x[indices] += wave * cos_angles[i]
                new_y[indices] += wave * sin_angles[i]

    # 应用X和Y坐标的三角调制
    sin_dt = np.sin(d_param * t)
    cos_dt = np.cos(d_param * t)
    new_x = new_x * sin_dt
    new_y = new_y * cos_dt

    # 应用文档2中的X轴公式到Z轴
    # 首先将x和y坐标映射到类似文档2中的范围
    mapped_x = (new_x + map_offset) * map_factor
    mapped_y = (new_y + map_offset) * map_factor

    # 文档2中的X轴公式计算 - 简化版本
    K = mapped_x / 8 - 25
    E = mapped_y / 8 - 25
    MAG = np.sqrt(K ** 2 + E ** 2)
    D = 5 * np.cos(MAG / 3)

    term1 = D * K + K * 2 * np.arctan(9 * np.cos(E * 2 - t / 2))
    new_X = (mapped_x + term1 * np.sin(D * 2.5 - t)) / 2 + 100

    # 将X坐标映射回Z轴范围
    new_z = (new_X - 100) * 30 / 200 - 15

    # 更新散点图数据 - 只更新位置，不更新颜色
    scatter._offsets3d = (new_x, new_y, new_z)


    # 更新时间
    t += 0.1

    return scatter,


# 创建动画 - 提高速度
ani = FuncAnimation(fig, update, frames=range(300), interval=20, blit=False, cache_frame_data=False)

plt.tight_layout()
plt.show()