import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 黄金比例常数
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值
# 添加旋转、衰减和圆周阵列功能
spiral_deg = 0  # 螺旋旋转度数
polar_array = 3  # 圆周阵列数量
# 参数设置
num_bands = 29  # 波段数量
total_points = 60 * num_bands  # 总点数
# 计算z坐标（对数螺旋）
def calculate_z(t):
    return np.log(t) / ln_phi

# 计算半径（与t成反比）
def calculate_radius(t):
    return 1 / t



# 创建连续参数t_total (0 到 2π*num_bands)
t_total = np.linspace(0, 2 * np.pi * num_bands, total_points)

# 存储螺旋线点
spiral_x = []
spiral_y = []
spiral_z = []
t_shape_values = []  # 存储t_shape值用于衰减计算

# 生成连续螺旋线
for t_val in t_total:
    # 确定当前波段索引n和波段内参数t_band
    n = int(t_val // (2 * np.pi))  # 波段索引
    t_band = t_val % (2 * np.pi)  # 波段内参数 (0 到 2π)

    # 计算t_shape（连续变化的t值）
    t_shape = n + 1 + t_band / (2 * np.pi)
    t_shape_values.append(t_shape)

    # 计算z坐标
    z = calculate_z(t_shape)

    # 计算半径（与t_shape成反比）
    r = calculate_radius(t_shape)

    # 计算x和y坐标（围绕z轴的螺旋）
    x = r * np.cos(t_val)
    y = r * np.sin(t_val)

    spiral_x.append(x)
    spiral_y.append(y)
    spiral_z.append(z)


# 连续对数积分衰减因子
def amp_continuous(t_shape):
    n = t_shape
    return 1  # 原始螺旋


# 对每条曲线分别应用旋转和衰减
def apply_rotation_and_decay(x_data, y_data, amp_factor, rotation_angles_rad):
    x_rotated = np.zeros_like(x_data)
    y_rotated = np.zeros_like(y_data)

    for i in range(len(x_data)):
        cos_angle = np.cos(rotation_angles_rad[i])
        sin_angle = np.sin(rotation_angles_rad[i])

        # 围绕原点旋转
        x_rotated[i] = x_data[i] * cos_angle - y_data[i] * sin_angle
        y_rotated[i] = x_data[i] * sin_angle + y_data[i] * cos_angle

    # 应用衰减
    return x_rotated * amp_factor, y_rotated * amp_factor


# 计算衰减因子
amp_factor = [amp_continuous(t_shape) for t_shape in t_shape_values]

# 应用spiral_deg°连续旋转
total_rotation_degrees = num_bands * spiral_deg
rotation_angles = np.linspace(0, total_rotation_degrees, len(t_total))
rotation_angles_rad = np.radians(rotation_angles)

# 应用旋转和衰减到基础曲线
spiral_x_rot, spiral_y_rot = apply_rotation_and_decay(spiral_x, spiral_y, amp_factor, rotation_angles_rad)

# 创建所有方向的曲线 - 圆周阵列
curves = []
for rotation in range(polar_array):
    angle_deg = rotation * (360 / polar_array)  # 计算每个阵列的旋转角度

    # 应用旋转到已经应用了spiral_deg°旋转和衰减的曲线上
    x_rotated = []
    y_rotated = []
    for i in range(len(spiral_x_rot)):
        angle_rad = np.radians(angle_deg)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        x_rot = spiral_x_rot[i] * cos_angle - spiral_y_rot[i] * sin_angle
        y_rot = spiral_x_rot[i] * sin_angle + spiral_y_rot[i] * cos_angle
        x_rotated.append(x_rot)
        y_rotated.append(y_rot)

    curves.append((x_rotated, y_rotated, spiral_z))

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建3D子图
ax1 = fig.add_subplot(121, projection='3d')

# 使用HSV颜色空间生成均匀分布的颜色
colors = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))

# 绘制所有螺旋线
for i, (x_curve, y_curve, z_curve) in enumerate(curves):
    ax1.plot(x_curve, y_curve, z_curve, color=colors[i], linewidth=1.0, alpha=0.8)

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
ax1.plot(np.zeros_like(z_red), np.zeros_like(z_red), z_red,
         color='purple', linewidth=2, alpha=0.7)

# 设置3D坐标轴标签和标题
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'3D Logarithmic Spiral with Polar Array ({polar_array} spirals)')
ax1.grid(True)

# 设置等轴比例
all_x = np.concatenate([curve[0] for curve in curves])
all_y = np.concatenate([curve[1] for curve in curves])
all_z = np.concatenate([curve[2] for curve in curves])

x_min, x_max = min(all_x), max(all_x)
y_min, y_max = min(all_y), max(all_y)
z_min, z_max = min(all_z), max(all_z)

x_range = x_max - x_min
y_range = y_max - y_min
z_range = z_max - z_min

max_range = max(x_range, y_range, z_range) / 2.0

mid_x = (x_min + x_max) / 2
mid_y = (y_min + y_max) / 2
mid_z = (z_min + z_max) / 2

ax1.set_xlim(mid_x - max_range, mid_x + max_range)
ax1.set_ylim(mid_y - max_range, mid_y + max_range)
ax1.set_zlim(mid_z - max_range, mid_z + max_range)

# 设置3D视角
ax1.view_init(elev=30, azim=-60)

# 创建2D XY投影子图
ax2 = fig.add_subplot(122)

# 绘制所有螺旋线的XY投影
for i, (x_curve, y_curve, z_curve) in enumerate(curves):
    ax2.plot(x_curve, y_curve, color=colors[i], linewidth=1.0, alpha=0.8)

# 添加红色曲线的XY投影
ax2.plot(x_red_positive, np.zeros_like(x_red_positive),
         color='red', linewidth=2, alpha=0.7)
ax2.plot(x_red_negative, np.zeros_like(x_red_negative),
         color='red', linewidth=2, alpha=0.7)

# 添加z轴曲线的XY投影（原点）
ax2.plot(0, 0, 'o', color='purple', markersize=5, alpha=0.7)

# 设置2D坐标轴标签和标题
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title(f'XY Plane Projection with Polar Array ({polar_array} spirals)')
ax2.grid(True)
ax2.set_aspect('equal')  # 保持纵横比相等

# 设置相同的XY范围，便于比较
xy_range = max(np.abs(all_x).max(), np.abs(all_y).max()) * 1.1
ax2.set_xlim(-xy_range, xy_range)
ax2.set_ylim(-xy_range, xy_range)

# 调整布局
plt.tight_layout()

# 保存并显示图像
plt.savefig(f"3d_log_spiral_{num_bands}_bands_with_polar_array_{polar_array}.png", dpi=300, transparent=True)
plt.show()