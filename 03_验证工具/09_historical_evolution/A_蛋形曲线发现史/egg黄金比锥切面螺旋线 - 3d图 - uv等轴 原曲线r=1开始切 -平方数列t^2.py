import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 黄金比例常数
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值

# 计算z坐标（对数螺旋） - 使用正高度
def calculate_z_red(t):
    return -np.log(t) / ln_phi  # 红色曲线高度


def calculate_z_blue(t):
    return -2 * np.log(t) / ln_phi  # 蓝色曲线高度


# 计算半径（与t的平方成反比）
def calculate_radius(t):
    return 1 / (t ** 2)


# 参数设置
num_bands = 64  # 波段数量
t_max = np.sqrt(num_bands)  # 蓝色螺旋线的最大t值 ≈5.385
total_points = 32 * num_bands  # 总点数（用于生成初始参数范围）

# 创建连续参数t_total (0 到 2π*num_bands)
t_total = np.linspace(0, 2 * np.pi * num_bands, total_points)

# 存储螺旋线点
spiral_x = []
spiral_y = []
spiral_z = []

# 生成连续螺旋线（只到t_max）
for t_val in t_total:
    # 确定当前波段索引n和波段内参数t_band
    n = int(t_val // (2 * np.pi))  # 波段索引
    t_band = t_val % (2 * np.pi)  # 波段内参数 (0 到 2π)

    # 计算t_shape（连续变化的t值）
    t_shape = n + 1 + t_band / (2 * np.pi)

    # 如果t_shape超过t_max，则停止生成点
    if t_shape > t_max:
        continue  # 跳过超出范围的点

    # 计算z坐标（蓝色曲线）
    z = calculate_z_blue(t_shape)

    # 计算半径（与t_shape的平方成反比）
    r = calculate_radius(t_shape)

    # 计算x和y坐标（围绕z轴的螺旋）
    x = r * np.cos(t_val)
    y = r * np.sin(t_val)

    spiral_x.append(x)
    spiral_y.append(y)
    spiral_z.append(z)

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建3D子图
ax1 = fig.add_subplot(121, projection='3d')

# 添加红色曲线（保持原始）
t_red = np.linspace(1, num_bands, 100)
x_red_positive = 1 / t_red
x_red_negative = -1 / t_red
z_red = calculate_z_red(t_red)  # 使用正高度

ax1.plot(x_red_positive, np.zeros_like(z_red), z_red,
         color='red', linewidth=2, alpha=0.7)
ax1.plot(x_red_negative, np.zeros_like(z_red), z_red,
         color='red', linewidth=2, alpha=0.7)

# 绘制蓝色螺旋线
ax1.plot(spiral_x, spiral_y, spiral_z, color='blue', linewidth=1.0, alpha=0.8)

# 设置3D坐标轴标签和标题
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'3D Logarithmic Spiral with r=1/(t_s^2) up to Red Curve Max Height (t_max={t_max:.3f})')
ax1.grid(True)

# 设置等轴比例
if spiral_x:  # 确保有点存在
    max_range = max(max(spiral_x) - min(spiral_x),
                    max(spiral_y) - min(spiral_y),
                    max(spiral_z) - min(spiral_z)) / 2.0

    mid_x = (max(spiral_x) + min(spiral_x)) / 2
    mid_y = (max(spiral_y) + min(spiral_y)) / 2
    mid_z = (max(spiral_z) + min(spiral_z)) / 2

    ax1.set_xlim(mid_x - max_range, mid_x + max_range)
    ax1.set_ylim(mid_y - max_range, mid_y + max_range)
    ax1.set_zlim(mid_z - max_range, mid_z + max_range)
else:
    # 如果没有点，设置默认范围
    ax1.set_xlim(-1, 1)
    ax1.set_ylim(-1, 1)
    ax1.set_zlim(0, 10)

# 设置3D视角
ax1.view_init(elev=30, azim=-60)

# 创建2D XY投影子图
ax2 = fig.add_subplot(122)
# 绘制螺旋线的XY投影
ax2.plot(spiral_x, spiral_y, color='blue', linewidth=1.0, alpha=0.8)

# 添加红色曲线的XY投影
ax2.plot(x_red_positive, np.zeros_like(x_red_positive),
         color='red', linewidth=2, alpha=0.7)
ax2.plot(x_red_negative, np.zeros_like(x_red_negative),
         color='red', linewidth=2, alpha=0.7)

# 设置2D坐标轴标签和标题
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title(f'XY Plane Projection with r=1/(t_s^2) (t_max={t_max:.3f})')
ax2.grid(True)
ax2.set_aspect('equal')  # 保持纵横比相等

# 设置XY范围
if spiral_x:
    xy_range = max(max(np.abs(spiral_x)), max(np.abs(spiral_y))) * 1.1
    ax2.set_xlim(-xy_range, xy_range)
    ax2.set_ylim(-xy_range, xy_range)
else:
    ax2.set_xlim(-1, 1)
    ax2.set_ylim(-1, 1)

# 添加图例
ax2.legend(['Spiral Projection', 'Red Curve Projection'])

# 调整布局
plt.tight_layout()

# 保存并显示图像
plt.savefig(f"3d_log_spiral_with_t_max_{t_max:.3f}.png", dpi=300, transparent=True)
plt.show()