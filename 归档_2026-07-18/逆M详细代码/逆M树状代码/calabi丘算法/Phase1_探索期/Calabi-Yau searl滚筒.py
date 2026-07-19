import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib

# 指定默认字体
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'  # 或者其他支持全角冒号的字体

# 参数定义
n =2
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
# 调整视角
ax.view_init(elev=0, azim=90)  # 仰角为0度，方位角为90度 （俯视图）
# ax.view_init(elev=30, azim=-60)  # 仰角为30度，方位角为-60度（系统默认设置侧视图）
# ax.view_init(elev=0, azim=-45)  # 仰角为0度，方位角为-45度
# ax.view_init(elev=90, azim=-180)  # 仰角为90度，方位角为-180度 （侧正视图）
def update(frame):
    ax.cla()
    alpha = (frame/9) * np.pi  # 修改alpha的计算方式
    u = np.linspace(-1, 1,3)
    v = np.linspace(0, np.pi / 2, 3)
    U, V = np.meshgrid(u, v)

    for k1 in range(n):
        for k2 in range(n):
            X, Y, Z = np.array([calabi_yau(x + 1j * y, k1, k2, alpha) for x, y in zip(np.ravel(U), np.ravel(V))]).T
            ax.plot_surface(X.reshape(U.shape), Y.reshape(V.shape), Z.reshape(V.shape), cmap='turbo', alpha=0.5)
    # ax.set_xlim([-1.5, 1.5])
    # ax.set_ylim([-1.5, 1.5])
    # ax.set_zlim([-1.5, 1.5])
    # ax.set_xlabel('X')
    # ax.set_ylabel('Y')
    # ax.set_zlabel('Z')
        # 在图形上标记n的值
    ax.text2D(0.05, 0.95, f"n = {n}，仰角，方位角：{ax.elev, ax.azim}", transform=ax.transAxes, fontsize=12, color='red')

    ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长
    ax.axis('off')

update(0)
plt.show()
# ani = FuncAnimation(fig, update, frames=np.linspace(0, 9, 9), repeat=False)
# # labelfn="侧视图"
# labelfn="searl滚筒"
# filename = f'({labelfn}){n}极{ax.elev,ax.azim}.gif'  # 使用 f-string 动态生成文件名
# ani.save(filename, writer=PillowWriter(fps=2))
# plt.close()