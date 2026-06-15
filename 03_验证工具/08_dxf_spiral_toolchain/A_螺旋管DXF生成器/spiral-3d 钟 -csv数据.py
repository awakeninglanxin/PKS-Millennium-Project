import numpy as np
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 定义参数
a = 0.588
b = 1.6
c = 2 * np.pi
u_range = np.linspace(0, 2 * np.pi, 100)
v_range = np.linspace(0, 7 / 3, 50)

# 初始化坐标列表
valid_points = []

# 准备 CSV 文件
with open('curve_points.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['X', 'Y', 'Z'])

    for u in u_range:
        if u == 0:  # 特殊处理 u 为零的情况，避免除以零错误
            continue
        for v in v_range:
            expression = (b - v * np.sin(a)) ** 2 - (v * np.cos(a)) ** 2
            if expression > 0:
                x = c * np.sqrt(1 / expression) * np.cos(u) / u
                # else:
                #     x = -c*np.sqrt(1 / np.abs(expression)) * np.cos(u)
                y = -v * c * np.sin(u) / u
                z = u
                if z > 0.5:  # 只保留 z > 0.5 的数据点
                    valid_points.append([x, y, z])
                    writer.writerow([x, y, z])

# 提取有效点的坐标
x_coords = np.array([p[0] for p in valid_points])
y_coords = np.array([p[1] for p in valid_points])
z_coords = np.array([p[2] for p in valid_points])

# 使用 plt.show 可视化散点
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 使用 scatter 生成散点图
ax.scatter(x_coords, y_coords, z_coords, c=z_coords, cmap='viridis', marker='o')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
# ax.axis('equal')

plt.show()
