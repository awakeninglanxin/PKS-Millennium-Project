import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D

# 参数定义
n = 5
alpha = 2 * np.pi  # 固定alpha值，观察k1和k2变化的效果


# 复数运算工具函数
def complex_mult(z1, z2):
    return z1 * z2

def complex_exp(z):
    return np.exp(z)


def complex_cosh(z):
    return np.cosh(z)


def complex_sinh(z):
    return np.sinh(z)


def complex_pow(z, power):
    return z ** power


# Calabi-Yau流形的参数方程
def calabi_yau(z, k1, k2, alpha):
    z1 = complex_mult(complex_exp(2 * np.pi * 1j * k1 / n), complex_pow(complex_cosh(z), 2 / n))
    z2 = complex_mult(complex_exp(2 * np.pi * 1j * k2 / n), complex_pow(complex_sinh(z), 2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)


# 创建动画
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')


def update(frame):
    k1, k2 = frame % n, frame // n  # 生成k1和k2的组合
    ax.cla()
    u = np.linspace(-1, 1, 30)
    v = np.linspace(0, np.pi / 2, 30)
    U, V = np.meshgrid(u, v)
    X, Y, Z = np.array([calabi_yau(x + 1j * y, k1, k2, alpha) for x, y in zip(np.ravel(U), np.ravel(V))]).T
    ax.plot_surface(X.reshape(U.shape), Y.reshape(V.shape), Z.reshape(V.shape), cmap='turbo', alpha=0.5)
    ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长
    ax.axis('off')

ani = FuncAnimation(fig, update, frames=np.linspace(0, n*n, n*n), repeat=False)
ani.save('calabiyau_K1K2.gif', writer=PillowWriter(fps=5))
plt.close()

