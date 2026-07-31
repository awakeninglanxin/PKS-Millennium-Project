
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 定义变量和参数
a, b, c = 161.8, 100, 0.5  # 示例参数值
theta = np.linspace(0, 2*np.pi, 100)
z = np.linspace(0.1, 0.3, 30)  # z的范围是0到1

Theta, Z = np.meshgrid(theta, z)
# R = np.pi*((1/a)-(1/b))/((Z-(1/a))*(Z-(1/b)*np.sin(Theta)*np.exp(Theta)) + (((1/b)**3 -(1/a)**3)*np.cos(Theta)**2 *np.exp(Theta))/3)
R = np.pi*((1/a)-(1/b))/((Z-(1/a))*(Z-(1/b)*np.sin(c*Theta)*np.exp(np.log(np.e)*c*Theta)) + (((1/b)**3 -(1/a)**3)*c*(np.cos(c*Theta))**2 *np.exp(np.log(np.e)*c*Theta))/3)

# 创建3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
# 绘制3D曲面
surf = ax.plot_surface(Theta, Z, R, cmap='viridis', alpha=0.6)

# 添加在xy, xz, yz平面的投影
ax.contour(Theta, Z, R, zdir='z', offset=-2, cmap='viridis')  # xy平面投影
ax.contour(Theta, Z, R, zdir='y', offset=1.2, cmap='viridis')  # xz平面投影
ax.contour(Theta, Z, R, zdir='x', offset=-1, cmap='viridis')   # yz平面投影

# 设置图形的界限
ax.set_xlim(-1, 2*np.pi)
ax.set_ylim(0, 1)
ax.set_zlim(-2, 2)

# 设置标签
ax.set_xlabel('Theta (rad)')
ax.set_ylabel('Z')
ax.set_zlabel('R')

plt.show()
