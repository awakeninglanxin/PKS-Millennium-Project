import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib
# 指定默认字体
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'  # 或者其他支持全角冒号的字体
# 参数定义
n = 3
# Calabi-Yau流形的参数方程
def calabi_yau(z, k1, k2, alpha):
    # 函数内部进行预计算
    exp_k1 = np.exp(2 * np.pi * 1j * k1 / n)
    exp_k2 = np.exp(2 * np.pi * 1j * k2 / n)
    # 应用复数运算
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    # 计算结果
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)
# 创建动画
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长
# 调整视角
# ax.view_init(elev=0, azim=90)  # 仰角为0度，方位角为90度 （俯视图）
ax.view_init(elev=0, azim=135)  # 仰角为0度，方位角为90度 （俯视图）
# ax.view_init(elev=30, azim=-60)  # 仰角为30度，方位角为-60度（系统默认设置侧视图）
# ax.view_init(elev=90, azim=0)  # 仰角为0度，方位角为90度 （俯视图）
# ax.view_init(elev=0, azim=-45)  # 仰角为0度，方位角为-45度
slices=6  #不要小于6谢谢
def update(frame):
    ax.cla()
    alpha = (frame) * np.pi  # 修改alpha的计算方式
    # u = np.linspace(-1, 1)  #默认50个点数
    u = np.linspace(-1, 1, slices)  # 100个点数
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)

    for k1 in range(n):
        for k2 in range(n):
            X, Y, Z = np.array([calabi_yau(x + 1j * y, k1, k2, alpha) for x, y in zip(np.ravel(U), np.ravel(V))]).T
            ax.plot_surface(X.reshape(U.shape), Y.reshape(V.shape), Z.reshape(V.shape), cmap='hsv', alpha=0.5)
    # 在图形上标记n的值以及仰角和方位角，居中并尽量靠近图形上方
    ax.text2D(0.5, 0.9, f"n = {n}，仰角，方位角：{ax.elev, ax.azim}", transform=ax.transAxes, fontsize=12,
                  color='red', horizontalalignment='center')
    ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长
    ax.axis('off')
    # 调整布局
plt.subplots_adjust(left=0, right=1, bottom=0, top=1)  # 这会调整子图的外边距
fig.tight_layout(pad=0)  # 减少图形周围的空白

# update(0)
# plt.show()
ani = FuncAnimation(fig, update, frames=np.linspace(0, 1, slices), repeat=True)
# labelfn="侧视图"
labelfn="正侧视图frame30 30点数 hsv"
filename = f'({labelfn}){n}极{slices}片.gif'  # 使用 f-string 动态生成文件名
ani.save(filename, writer=PillowWriter(fps=slices//6))
plt.close()