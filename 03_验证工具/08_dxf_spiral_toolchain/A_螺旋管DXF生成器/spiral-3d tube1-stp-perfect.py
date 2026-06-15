import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 定义参数
a = 1  # 缩放因子，假设a为1，可以根据需要调整
phi = np.pi / 180 * np.array([180, 120, 90])  # phi对应的角度

# 定义方程
def x_t(t, a, phi, factor):
    return a * np.pi * 1.618**(-t / phi) * np.cos(t) * factor

def z_t(t, a, phi, factor):
    return a * np.pi * 1.618**(-t / phi) * -np.sin(t) * factor

def y_t(t):
    return 0  # y(t)恒等于0，因为这是旋转轴

# 定义圆锥面方程
def cone_x(t):
    return 4 * np.pi**2 / t

def cone_z(t):
    return np.log(t) / np.log(0.618) - np.log(2 * np.pi) / np.log(0.618)

# 定义时间范围
t_values_1 = np.linspace(2*np.pi, 4*np.pi, 1000)
t_values_2 = np.linspace(4*np.pi, 6*np.pi, 1000)
t_values_3 = np.linspace(6*np.pi, 8*np.pi, 1000)

# 计算原始平面曲线的 (x, y, z) 值
x_values_1 = x_t(t_values_1, a, phi[0], 2 * 1.618)
z_values_1 = z_t(t_values_1, a, phi[0], 2 * 1.618)

x_values_2 = x_t(t_values_2, a, phi[1], 2 * 1.618 * 2.618)
z_values_2 = z_t(t_values_2, a, phi[1], 2 * 1.618 * 2.618)

x_values_3 = x_t(t_values_3, a, phi[2], 2 * 1.618 * (2.618**2))
z_values_3 = z_t(t_values_3, a, phi[2], 2 * 1.618 * (2.618**2))

# 将平面曲线投影到以y轴为中轴的圆锥面上
y_proj_1 = cone_x(t_values_1)
z_proj_1 = cone_z(t_values_1)

y_proj_2 = cone_x(t_values_2)
z_proj_2 = cone_z(t_values_2)

y_proj_3 = cone_x(t_values_3)
z_proj_3 = cone_z(t_values_3)

# x直接使用原始曲线的x值
x_proj_1 = x_values_1
x_proj_2 = x_values_2
x_proj_3 = x_values_3

# 绘制结果
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 原始曲线
ax.plot(x_values_1, np.zeros_like(x_values_1), z_values_1, label='Original Curve 1', color='b')
ax.plot(x_values_2, np.zeros_like(x_values_2), z_values_2, label='Original Curve 2', color='g')
ax.plot(x_values_3, np.zeros_like(x_values_3), z_values_3, label='Original Curve 3', color='r')

# 投影后的曲线
ax.plot(x_proj_1, y_proj_1, z_proj_1, '--', label='Projected Curve 1', color='b')
ax.plot(x_proj_2, y_proj_2, z_proj_2, '--', label='Projected Curve 2', color='g')
ax.plot(x_proj_3, y_proj_3, z_proj_3, '--', label='Projected Curve 3', color='r')

# 设置图形
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()
ax.set_box_aspect([1, 1, 1])  # 设置等比例缩放

plt.show()
