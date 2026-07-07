import matplotlib.pyplot as plt
import numpy as np


def hexagon(ax, center, size):
    """绘制单个六边形"""
    angles = np.linspace(0, 2 * np.pi, 7)
    x = center[0] + size * np.cos(angles)
    y = center[1] + size * np.sin(angles)
    ax.plot(x, y, color='black')


def draw_fractal(ax, center, size, k, max_k, n, m):
    """递归绘制分形六边形"""
    if k > max_k:
        return

    # 绘制当前层的六边形
    hexagon(ax, center, size)

    # 在每个六边形的邻接点继续绘制六边形
    angle_offset = np.pi / 3  # 60度角
    new_size = size / 3  # 下一层六边形的大小
    for i in range(n):
        # 计算新中心点的位置
        new_center = (center[0] + size * np.cos(i * angle_offset),
                      center[1] + size * np.sin(i * angle_offset))
        draw_fractal(ax, new_center, new_size, k + 1, max_k, n, m)

    # 每层的总六边形数会增多
    if k == max_k:
        ax.text(center[0], center[1], f'N={m}', fontsize=8, ha='center', va='center')


# 绘制图形
fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.set_xticks([])
ax.set_yticks([])

# 初始大小与位置
center = (0, 0)
size = 1

# 设定递归的参数
k = 0  # 初始递归层数
max_k = 3  # 设置递归的最大深度
n = 6  # 每层六边形数量
m = 6  # 总六边形数

# 绘制分形
draw_fractal(ax, center, size, k, max_k, n, m)

plt.show()
