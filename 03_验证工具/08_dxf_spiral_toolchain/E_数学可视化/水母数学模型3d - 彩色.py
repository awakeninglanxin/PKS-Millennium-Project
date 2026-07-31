import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from colorsys import hsv_to_rgb
import time

# 配置参数
num_points = 2000  # 点的数量
marker_size = 15  # 光点的大小
marker_alpha = 0.7  # 光点的透明度
d_param = 0.5  # 可调参数d，控制波形频率

# 创建3D图形和坐标轴 - 白色背景
fig = plt.figure(figsize=(10, 10), facecolor='white')
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('white')
ax.set_xlim(-15, 15)
ax.set_ylim(-15, 15)
ax.set_zlim(-15, 15)

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
num_tentacles = 8
tentacle_points = num_points // 4
for i in range(num_tentacles):
    angle = 2 * np.pi * i / num_tentacles
    tentacle_z = np.linspace(-10, -20, tentacle_points)
    tentacle_x = 0.5 * np.cos(angle) * (tentacle_z + 10) + np.random.normal(0, 0.2, tentacle_points)
    tentacle_y = 0.5 * np.sin(angle) * (tentacle_z + 10) + np.random.normal(0, 0.2, tentacle_points)

    x = np.concatenate([x, tentacle_x])
    y = np.concatenate([y, tentacle_y])
    z = np.concatenate([z, tentacle_z])

# 初始化散点图 - 使用深色默认颜色以确保在白色背景上可见
scatter = ax.scatter(x, y, z, s=marker_size, alpha=marker_alpha, c='darkblue')

# 初始化时间变量
t = 0
start_time = time.time()


# 动画更新函数
def update(frame):
    global t

    # 复制原始位置
    new_x = x.copy()
    new_y = y.copy()
    new_z = z.copy()

    # 水母主体脉动效果
    pulse = 0.2 * np.sin(t * 0.5) + 1.0

    # 应用脉动效果到水母主体
    body_mask = z > -15  # 选择水母主体部分
    radius = np.sqrt(new_x[body_mask] ** 2 + new_y[body_mask] ** 2 + (new_z[body_mask] + 10) ** 2)
    new_x[body_mask] = new_x[body_mask] * pulse / (radius + 1e-5) * 5
    new_y[body_mask] = new_y[body_mask] * pulse / (radius + 1e-5) * 5
    new_z[body_mask] = (new_z[body_mask] + 10) * pulse / (radius + 1e-5) * 5 - 10

    # 触手摆动效果
    tentacle_mask = z <= -15  # 选择触手部分
    for i in range(num_tentacles):
        tentacle_indices = np.where(tentacle_mask)[0][i * tentacle_points:(i + 1) * tentacle_points]
        wave = 0.3 * np.sin(t + i * 0.5 + new_z[tentacle_indices] * 0.5)
        angle = 2 * np.pi * i / num_tentacles
        new_x[tentacle_indices] += wave * np.cos(angle)
        new_y[tentacle_indices] += wave * np.sin(angle)

    # 应用X和Y坐标的三角调制
    new_x = new_x * np.sin(d_param * t)
    new_y = new_y * np.cos(d_param * t)

    # 应用文档2中的X轴公式到Z轴
    # 首先将x和y坐标映射到类似文档2中的范围
    mapped_x = (new_x + 15) * 200 / 30  # 将[-15,15]映射到[0,200]
    mapped_y = (new_y + 15) * 200 / 30  # 将[-15,15]映射到[0,200]

    # 文档2中的X轴公式计算
    K = mapped_x / 8 - 25
    E = mapped_y / 8 - 25
    MAG = np.sqrt(K ** 2 + E ** 2)
    D = 5 * np.cos(MAG / 3)

    term1 = D * K + K * 2 * np.arctan(9 * np.cos(E * 2 - t / 2))
    new_X = (mapped_x + term1 * np.sin(D * 2.5 - t)) / 2 + 100

    # 将X坐标映射回Z轴范围
    new_z = (new_X - 100) * 30 / 200 - 15  # 将[0,200]映射到[-15,15]

    # 动态颜色计算 - 基于位置和时间
    # 调整颜色饱和度和亮度以适应白色背景
    hue = (np.arctan2(new_y, new_x) / (2 * np.pi) + t / 10) % 1.0
    saturation = 0.9 + 0.1 * np.sin(t * 0.7)  # 增加饱和度
    value = 0.8 + 0.2 * (new_z + 15) / 30  # 增加亮度

    # 将HSV颜色转换为RGB
    colors = np.zeros((len(new_x), 3))
    for i in range(len(new_x)):
        colors[i] = hsv_to_rgb(hue[i] % 1.0, saturation, min(1.0, value[i]))

    # 更新散点图数据
    scatter._offsets3d = (new_x, new_y, new_z)
    scatter.set_color(colors)
    # scatter.set_alpha(marker_alpha)

    # 更新时间
    t += 0.1

    return scatter,


# 创建动画
ani = FuncAnimation(fig, update, frames=range(1000), interval=50, blit=True)

plt.tight_layout()
plt.show()