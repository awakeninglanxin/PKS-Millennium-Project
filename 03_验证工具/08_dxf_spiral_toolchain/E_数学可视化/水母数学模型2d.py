import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from colorsys import hsv_to_rgb
import time

# 配置参数
trail_alpha = 0.1  # 拖尾效果的透明度
marker_size = 2.5  # 光点的大小
marker_alpha = 0.4  # 光点的透明度

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')
ax.set_xlim(0, 400)
ax.set_ylim(0, 400)
ax.set_aspect('equal')
ax.set_xticks([])
ax.set_yticks([])
plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)

# 创建输入坐标网格
x = np.arange(100, 300)
y = np.arange(100, 300)
X, Y = np.meshgrid(x, y)

# 预处理颜色计算
centerX = np.mean(X)
centerY = np.mean(Y)
initial_angles = np.arctan2(Y - centerY, X - centerX)

# 初始化散点图
scatter = ax.scatter([], [], s=marker_size, alpha=marker_alpha)

# 初始化时间变量
t = 0
start_time = time.time()


# 动画更新函数
def update(frame):
    global t

    # 核心公式的向量化计算
    K = X / 8 - 25
    E = Y / 8 - 25
    MAG = np.sqrt(K ** 2 + E ** 2)
    D = 5 * np.cos(MAG / 3)

    term1 = D * K + K * 2 * np.arctan(9 * np.cos(E * 2 - t / 2))
    new_X = (X + term1 * np.sin(D * 2.5 - t)) / 2 + 100

    original_Y = D * 13 + D * 3 * (3 + np.cos(D * 3 - t)) + D * E + 200

    # 将Y坐标上下颠倒
    new_Y = 400 - original_Y

    # 动态颜色计算
    hue = np.mod(initial_angles / (2 * np.pi) + t / (5 * np.pi), 1)
    saturation = np.ones_like(hue) * 0.9
    brightness = np.ones_like(hue) * 1.0

    # 将HSV颜色转换为RGB
    rgb_colors = np.apply_along_axis(
        lambda x: hsv_to_rgb(x[0], x[1], x[2]),
        2,
        np.dstack((hue, saturation, brightness))
    )
    rgb_colors = rgb_colors.reshape(-1, 3)

    # 绘制一个半透明的黑色矩形以创建拖尾效果
    ax.add_patch(plt.Rectangle((0, 0), 400, 400, facecolor='black', alpha=trail_alpha, zorder=0))

    # 更新散点图数据
    scatter.set_offsets(np.column_stack((new_X.flatten(), new_Y.flatten())))
    scatter.set_color(rgb_colors)
    scatter.set_alpha(marker_alpha)

    # 更新时间
    t += np.pi / 24

    return scatter,


# 创建动画
ani = FuncAnimation(fig, update, frames=range(1000), interval=1, blit=True)

plt.show()