import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib

# 指定默认字体
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'

# 参数定义
n = 1

# 预先计算exp_k1, exp_k2
exp_k1_k2 = []
for k1 in range(n):
    for k2 in range(n):
        exp_k1_k2.append((np.exp(2 * np.pi * 1j * k1 / n), np.exp(2 * np.pi * 1j * k2 / n)))

# Calabi-Yau流形的参数方程，向量化版本
def calabi_yau(z, exp_k1, exp_k2, alpha):
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

# 创建动画
fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(8, 8))
ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长

# 调整视角
ax.view_init(elev=0, azim=135)  # 仰角为0度，方位角为135度

# 更新函数
def update(frame):
    ax.cla()  # 清除轴
    alpha = frame * np.pi
    slices = frame + 1
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)

    vertices_count = 0

    # 向量化处理
    for exp_k1, exp_k2 in exp_k1_k2:
        Z = np.array([calabi_yau(x + 1j * y, exp_k1, exp_k2, alpha) for x, y in zip(np.ravel(U), np.ravel(V))]).T
        vertices_count += Z.shape[1]
        ax.plot_surface(Z[0].reshape(U.shape), Z[1].reshape(V.shape), Z[2].reshape(V.shape), cmap='hsv', alpha=0.5)

        # 画顶点之间的线
        for i in range(U.shape[0]):
            ax.plot(Z[0, i * slices:(i + 1) * slices], Z[1, i * slices:(i + 1) * slices],
                    Z[2, i * slices:(i + 1) * slices], color='k', linewidth=0.5)
        for j in range(U.shape[1]):
            ax.plot(Z[0, j::slices], Z[1, j::slices], Z[2, j::slices], color='k', linewidth=0.5)

        # 突出显示顶点
        ax.scatter(Z[0], Z[1], Z[2], color='blue', s=10)

    # 在图中标记顶点的数量
    ax.text2D(0.5, 0.95, f"点数量: {vertices_count} slice：{slices}", transform=ax.transAxes, fontsize=12, color='red',
              horizontalalignment='center')
    ax.text2D(0.5, 0.9, f"n = {n}，仰角，方位角：{ax.elev, ax.azim}", transform=ax.transAxes, fontsize=12, color='red',
              horizontalalignment='center')
    ax.set_box_aspect([1, 1, 1])
    ax.axis('off')

# 创建动画对象
ani = FuncAnimation(fig, update, frames=12, repeat=True)

# 保存动画为gif文件
ani.save("calabi_yau_animation_highlighted.gif", writer=PillowWriter(fps=2))

plt.show()
