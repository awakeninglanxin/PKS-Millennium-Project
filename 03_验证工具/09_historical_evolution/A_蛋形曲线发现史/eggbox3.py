import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 设置常量
pic_size = 512  # 增加图片尺寸以增加密集度
k = (1/3)**8  # 波数
win_size =64
# dx =pic_size/win_size   # 像素大小与图像尺寸的比例
dx =win_size/pic_size
center = pic_size // 2  # 图像中心点

# 生成基础网格
x = pic_size  # x方向点的数量
y = pic_size  # y方向点的数量
x_values = np.linspace(0, 1, x)  # 在0到10之间生成x个等间距的值
y_values = np.linspace(0, 1, y)  # 在0到10之间生成y个等间距的值
x_grid, y_grid = np.meshgrid(x_values, y_values)  # 创建一个二维的网格

# 初始化透镜和透明度数组
lens = np.zeros((pic_size, pic_size), dtype=np.complex64)
alpha_channel = np.zeros((pic_size, pic_size))

# 计算透镜效果
for y in range(pic_size):
    for x in range(pic_size):
        distance_squared = ((dx * (x - center)) ** 2 + (dx * (y - center)) ** 2)
        lens[y, x] = np.exp(k * (0 - 1j) * distance_squared)
        alpha_channel[y, x] = 1

# 应用透镜效果调整z网格
# z_grid = np.abs(lens)
# z_grid = np.sqrt(lens**2)
z_grid = lens**2
# z_max = np.max(z_grid)  # 获取z_grid的最大值
# z_min = np.min(z_grid)  # 获取z_grid的最小值
z2_max = np.max(z_grid)  # 获取z_grid的最大值
z2_min = np.min(z_grid)  # 获取z_grid的最小值
# print(z_max,z_min)
print(z2_max,z2_min)

# 绘制3D曲面
fig = plt.figure(figsize=(8, 8), dpi=100)
ax = fig.add_subplot(111, projection='3d')
surface = ax.plot_surface(x_grid, y_grid, z_grid, cmap='hsv', rstride=1, cstride=1, alpha=0.8)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.view_init(elev=90, azim=0)  # 设置视图为顶视图
# ax.view_init(elev=30, azim=45)
# ax.set_zlim(1.0000002, 0.9999998)
ax.axis('off')  # 关闭轴显示
plt.show()
