import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# 输入参数
b = 100  # b为多少排蛋盒子
z_scale = 1 # 设置z方向的放缩系数

# 生成网格
x_values = np.linspace(0, b, b)  # 在0到b之间生成b个等间距的值
y_values = np.linspace(0, b, b)  # 在0到b之间生成b个等间距的值
x_grid, y_grid = np.meshgrid(x_values, y_values)
z_grid = np.sin(x_grid * np.pi) * np.sin(y_grid * np.pi) * z_scale

# 绘制曲面
fig = plt.figure(figsize=(8, 8), dpi=100)
ax = fig.add_subplot(111, projection='3d')
surface = ax.plot_surface(x_grid, y_grid, z_grid, cmap='rainbow', rstride=1, cstride=1, alpha=0.8)
ax.set_xlabel('X')
ax.set_xlim(0, b+1)
ax.set_ylabel('Y')
ax.set_ylim(0, b+1)
ax.set_zlabel('Z')
ax.set_zlim(-z_scale*3, z_scale*3)
# ax.view_init(elev=0, azim=90)
# ax.view_init(elev=0, azim=270)

def init():
    ax.view_init(elev=0, azim=0)
    return fig,

def update(frame):
    ax.view_init(elev=0, azim=frame)
    return fig,

ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 2), init_func=init, blit=False)
ax.axis('off')
plt.show()
