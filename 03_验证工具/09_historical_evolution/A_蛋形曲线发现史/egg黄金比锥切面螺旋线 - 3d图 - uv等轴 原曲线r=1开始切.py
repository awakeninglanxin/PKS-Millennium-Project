import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 参数设置（保持原始）
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值
k = 1 / (2 * np.pi * ln_phi)  # 负值
D = np.sqrt(1 + k ** 2)  # 常数

# 设置波段数量
num_curves=5
num_bands = num_curves+1
total_points = 32*num_bands

# 创建连续参数 T ∈ [0, 2π * num_bands]
T = np.linspace(0, 2 * np.pi * (num_bands-1), total_points)

# 计算连续形状参数 t_s
n = np.floor(T / (2 * np.pi)).astype(int) +1 # 波段索引 n
tau = T % (2 * np.pi)  # 波段内参数
t_s = n + tau / (2 * np.pi)  # 连续形状参数

# 计算坐标
z = np.log(t_s) / ln_phi  # z坐标（保持原始计算）
r = 1 / t_s  # 半径（保持红色曲线特性）
x = -r * np.cos(T)  # x坐标（起始点x=-1）
y = -r * np.sin(T)  # y坐标

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建3D子图
ax1 = fig.add_subplot(121, projection='3d')

# 绘制螺旋线（蓝色）
ax1.plot(x, y, z, color='blue', linewidth=1.0, alpha=0.8)

# 添加红色曲线（保持原始）
t_red = np.linspace(1, num_bands, 100)
x_red_positive = 1 / t_red
x_red_negative = -1 / t_red
z_red = np.log(t_red) / ln_phi

ax1.plot(x_red_positive, np.zeros_like(z_red), z_red,
        color='red', linewidth=2, alpha=0.7)
ax1.plot(x_red_negative, np.zeros_like(z_red), z_red,
        color='red', linewidth=2, alpha=0.7)

# 添加z轴曲线
t_red = np.linspace(1, num_bands, 500)
z_red = np.log(t_red) / ln_phi

# 绘制z轴（中轴）
ax1.plot(np.zeros_like(z_red), np.zeros_like(z_red), z_red,
        color='purple', linewidth=2, alpha=0.7)

# 设置3D坐标轴标签和标题
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'3D Golden Ratio Spiral ({num_curves} Bands)')
ax1.grid(True)

# 设置等轴比例
max_range = max(np.max(x)-np.min(x),
                np.max(y)-np.min(y),
                np.max(z)-np.min(z)) / 2.0

mid_x = (np.max(x) + np.min(x)) / 2
mid_y = (np.max(y) + np.min(y)) / 2
mid_z = (np.max(z) + np.min(z)) / 2
print('z min:',np.min(z))

ax1.set_xlim(mid_x - max_range, mid_x + max_range)
ax1.set_ylim(mid_y - max_range, mid_y + max_range)
ax1.set_zlim(mid_z - max_range, mid_z + max_range)

# 设置视角
ax1.view_init(elev=30, azim=-60)

# 创建2D XY投影子图
ax2 = fig.add_subplot(122)

# 绘制螺旋线的XY投影
ax2.plot(x, y, color='blue', linewidth=1.0, alpha=0.8)

# 添加红色曲线的XY投影
# 在XY平面中，红色曲线投影为x轴上的线段
ax2.plot(x_red_positive, np.zeros_like(x_red_positive),
         color='red', linewidth=2, alpha=0.7)
ax2.plot(x_red_negative, np.zeros_like(x_red_negative),
         color='red', linewidth=2, alpha=0.7)

# 添加z轴曲线的XY投影（原点）
ax2.plot(0, 0, 'o', color='purple', markersize=5, alpha=0.7)

# 设置2D坐标轴标签和标题
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title(f'XY Plane Projection ({num_curves} Bands)')
ax2.grid(True)
ax2.set_aspect('equal')  # 保持纵横比相等

# 设置相同的XY范围，便于比较
xy_range = max(max_range, max(np.abs(x)), max(np.abs(y))) * 1.1
ax2.set_xlim(-xy_range, xy_range)
ax2.set_ylim(-xy_range, xy_range)

# 添加图例
ax2.legend(['Spiral Projection', 'Red Curve Projection', 'Z-axis Origin'])

# 调整布局
plt.tight_layout()

# 保存并显示图像
plt.savefig(f"golden_ratio_spiral_{num_curves}_bands_with_projection.png", dpi=300, transparent=True)
plt.show()