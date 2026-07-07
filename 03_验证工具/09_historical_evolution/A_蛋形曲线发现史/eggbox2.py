import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize

# 设置常量
pic_size = 441  # 图片尺寸
k = 1  # 波数
win_size=5
dx = win_size / pic_size  # 像素大小与图像尺寸的比例
center = pic_size // 2  # 图像中心点

# 生成基础网格
x = pic_size  # x方向点的数量
y = pic_size  # y方向点的数量
x_values = np.linspace(0, 10, x)  # 在0到10之间生成x个等间距的值
y_values = np.linspace(0, 10, y)  # 在0到10之间生成y个等间距的值
x_grid, y_grid = np.meshgrid(x_values, y_values)  # 创建一个二维的网格

# 初始化透镜和透明度数组
lens = np.zeros((pic_size, pic_size), dtype=np.complex64)  # 初始化透镜数组
alpha_channel = np.zeros((pic_size, pic_size))  # 初始化透明度数组

# 计算透镜效果
for y in range(pic_size):
    for x in range(pic_size):
        distance_squared = ((dx * (x - center)) ** 2 + (dx * (y - center)) ** 2)  # 计算距离中心的平方距离
        lens[y, x] = np.exp(k * (0 - 1j) * distance_squared)  # 应用透镜相位调整
        alpha_channel[y, x] = 1  # 设置透明度为1，完全不透明

# 应用透镜效果调整z网格
z_grid = np.abs(lens**2)  # 使用透镜的绝对值调整z网格的高度
z_max = np.max(z_grid)  # 获取z_grid的最大值
z_min = np.min(z_grid)  # 获取z_grid的最小值
print(z_max,z_min)

# 绘制3D曲面
fig = plt.figure(figsize=(8, 8), dpi=100)  # 创建图形，指定大小和分辨率
ax = fig.add_subplot(111, projection='3d')  # 添加一个3D子图
surface = ax.plot_surface(x_grid, y_grid, z_grid, cmap='rainbow', rstride=1, cstride=1, alpha=0.8)  # 绘制3D曲面
ax.set_xlabel('X')  # 设置X轴标签
ax.set_ylabel('Y')  # 设置Y轴标签
ax.set_zlabel('Z')  # 设置Z轴标签
ax.set_zlim(1.0000002, 0.9999998) # 设置z轴的显示范围，如果需要
# ax.axis('off')  # 关闭轴显示
plt.show()  # 显示图形
