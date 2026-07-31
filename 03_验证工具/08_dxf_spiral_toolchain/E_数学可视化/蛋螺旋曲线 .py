import numpy as np
import matplotlib.pyplot as plt

# 定义参数范围
t = np.linspace(-np.pi/3, 2*np.pi/3, 660)
degree_rad = 100 * np.pi / (3 * 180)

# 定义方程
d = 64  # 假设d=64
phi = (1 + np.sqrt(5)) / 2
sqrt_term = 1 / (phi - t*np.sin(degree_rad))**2 - (t * np.cos(degree_rad))**2

# 跳过负数的点
valid_indices = sqrt_term >= 0
t_valid = t[valid_indices]
sqrt_term_valid = sqrt_term[valid_indices]

# 计算 x, y, z
x = np.sin(d * t_valid) * np.sqrt(sqrt_term_valid)
y = np.cos(d * t_valid) * np.sqrt(sqrt_term_valid)
z = -t_valid

# 绘制图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(x, y, z, label='Non-linear transformed curve')

# 添加标签
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')
ax.axis('equal')
ax.legend()

plt.show()
