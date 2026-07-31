import numpy as np
import matplotlib.pyplot as plt
from mpmath import mp

# 设置高精度
mp.dps = 10  # 设置50位精度

# 定义黄金比例的精确值
phi = (1 + mp.sqrt(5)) / 2

# 定义参数范围
t = np.linspace(2*np.pi/3, -np.pi/3, 4410)

# 使用 mpmath 的高精度计算
degree_rad = 100 * np.pi / (3 * 180)

d = 64

sqrt_term = 1 / (phi - t*mp.sin(degree_rad))**2 - (t * mp.cos(degree_rad))**2

# 使用 mpmath 的 sqrt 函数计算平方根
sqrt_term = [mp.fabs(x) for x in sqrt_term]  # 逐个计算绝对值
sqrt_term = [mp.sqrt(x) for x in sqrt_term]  # 逐个计算平方根

# 计算 x, y, z
x = [mp.sin(d * val) * val for val in sqrt_term]
y = [mp.cos(d * val) * val for val in sqrt_term]
z = [val for val in t]

# 将结果转换回 numpy 数组以便绘图
x = np.array([float(val) for val in x])
y = np.array([float(val) for val in y])
z = np.array(z)

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
