import numpy as np  # 导入numpy库，用于数组和数学运算
import matplotlib.pyplot as plt  # 导入matplotlib的pyplot模块，用于绘图
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# 输入参数
#清晰度，增加网格密度
a=10
b=100 # b为多少排蛋盒子
x = b*a  # 设置x方向的点数量
y = b*a  # 设置y方向的点数量
z_scale = 1 # 设置z方向的放缩系数

# 生成网格

x_values = np.linspace(0, b, b)  # 在0到1之间生成x个等间距的值
print("x:",x,"y:",y)
y_values = np.linspace(0, b, b)  # 在0到1之间生成y个等间距的值
x_grid, y_grid = np.meshgrid(x_values, y_values)  # 创建一个二维的网格
z_grid = np.sin(x_grid * np.pi) * np.sin(y_grid * np.pi) * z_scale  # 计算z网格的值（方形结构）


# 绘制曲面
fig = plt.figure(figsize=(8, 8), dpi=100)  # 创建图形，指定大小和分辨率
ax = fig.add_subplot(111, projection='3d')  # 添加一个3D子图

surface = ax.plot_surface(x_grid, y_grid, z_grid, cmap='rainbow', rstride=1, cstride=1, alpha=0.8)
# # 绘制XY平面的投影
# cset = ax.contourf(x_grid, y_grid, z_grid, zdir='z', offset=-z_scale-1, cmap='viridis', alpha=0.5)
# # 绘制XZ平面的投影
# cset = ax.contourf(x_grid, z_grid, y_grid, zdir='y', offset=-1, cmap='viridis', alpha=0.5)
# # 绘制YZ平面的投影
# cset = ax.contourf(z_grid, y_grid, x_grid, zdir='x', offset=-1, cmap='viridis', alpha=0.5)
# 设置轴的显示范围
ax.set_xlabel('X')
ax.set_xlim(0, b+ 1)
ax.set_ylabel('Y')
ax.set_ylim(0, b + 1)
ax.set_zlabel('Z')
ax.set_zlim(-z_scale*3, z_scale*3) # 设置z轴的显示范围，如果需要
ax.view_init(elev=0, azim=90)  # elev设置为0, azim设置为90
# 初始化函数：设置图形的初始状态
def init():
    ax.view_init(elev=10, azim=0)  # elev设置为10提供稍微倾斜的视角
    return fig,

# 更新函数：每一帧调用一次
def update(frame):
    ax.view_init(elev=10, azim=frame)  # 旋转角度为 frame
    return fig,

# 创建动画
ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 2), init_func=init, blit=True)
# 关闭轴显示
ax.axis('off')
plt.show()


