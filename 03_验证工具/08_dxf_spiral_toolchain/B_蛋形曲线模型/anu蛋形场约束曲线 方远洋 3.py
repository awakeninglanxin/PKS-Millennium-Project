import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

# 设置参数范围，避开0和1的奇点
lambda_vals = np.linspace(0.001, 0.999, 100000)

# 预计算一些常用值
pi = np.pi
sqrt5 = np.sqrt(5)
constant = np.log((sqrt5 - 1) / 2)  # 方程中的常数项

# 计算权重因子
weight = 1 - np.exp(-1 / (lambda_vals * (1 - lambda_vals)))

# 计算分母项 N
theta = 5 * pi * lambda_vals
floor_part = np.floor(theta / (2 * pi))
mod_part = np.mod(theta, 2 * pi)
N = floor_part + 1 + mod_part / (2 * pi)

# 计算坐标
x = weight * np.cos(theta) / N
z = weight * np.sin(theta) / N
y = (1 - weight) * 1 + weight * np.log(1 / N) / constant

# 创建图形
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# 使用颜色映射表示参数λ的变化
colors = cm.viridis(lambda_vals)

# 绘制曲线
scatter = ax.scatter(x, y, z, c=lambda_vals, cmap='viridis', s=1, alpha=0.8)

# 添加颜色条
cbar = fig.colorbar(scatter, ax=ax, shrink=0.5, aspect=20)
cbar.set_label('λ Value')

# 设置标签和标题
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Parametric Curve')

# 调整视角以便更好地观察
ax.view_init(elev=20, azim=45)

# 显示图形
plt.tight_layout()
plt.show()