import matplotlib.pyplot as plt
import numpy as np

def hexagon(ax, center, size):
    """绘制单个六边形"""
    angles = np.linspace(0, 2 * np.pi, 7)
    x = center[0] + size * np.cos(angles)
    y = center[1] + size * np.sin(angles)
    ax.plot(x, y, color='black')

def draw_fractal(ax, center, size, k, max_k):
    """递归绘制分形六边形"""
    if k > max_k:
        return
    hexagon(ax, center, size)
    new_size = size / 3
    # 为每个边的中点绘制新的六边形
    for i in range(6):
        new_center = (center[0] + size * np.cos(np.pi / 3 * i),
                      center[1] + size * np.sin(np.pi / 3 * i))
        draw_fractal(ax, new_center, new_size, k + 1, max_k)

# 绘制图形
fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.set_xticks([])
ax.set_yticks([])

# 初始大小与位置
center = (0, 0)
size = 1

# 绘制分形
max_k = 3  # 设置递归的最大深度
draw_fractal(ax, center, size, 0, max_k)

plt.show()
