import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 参数设置（保持原始）
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值
k = 1 / (2 * np.pi * ln_phi)  # 负值
D = np.sqrt(1 + k ** 2)  # 常数

# 设置波段数量
num_bands = 29  # 对应原始 num_curves=29
total_points = 60 * num_bands
# 添加旋转、衰减和圆周阵列功能
spiral_deg = 45  # 螺旋旋转度数
polar_array = 3  # 圆周阵列数量
# 创建连续参数 T ∈ [0, 2π * num_bands]
T = np.linspace(0, 2 * np.pi * num_bands, total_points)

# 计算连续形状参数 t_s
n = np.floor(T / (2 * np.pi)).astype(int) + 1  # 波段索引 n
tau = T % (2 * np.pi)  # 波段内参数
t_s = n + tau / (2 * np.pi)  # 连续形状参数

# 计算坐标
z = np.log(t_s) / ln_phi  # z坐标（保持原始计算）
r = 1 / t_s  # 半径（保持红色曲线特性）
x = -r * np.cos(T)  # x坐标（起始点x=-1）
y = -r * np.sin(T)  # y坐标




# 连续对数积分衰减因子
def amp_continuous(t_shape):
    n = t_shape
    return 1  # 原始螺旋线

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
amp_factor = amp_continuous(t_s)

# 应用spiral_deg°连续旋转
total_rotation_degrees = num_bands * spiral_deg
rotation_angles = np.linspace(0, total_rotation_degrees, len(T))
rotation_angles_rad = np.radians(rotation_angles)

# 应用旋转和衰减到基础曲线
x_rot, y_rot = apply_rotation_and_decay(x, y, amp_factor, rotation_angles_rad)

# 创建所有方向的曲线 - 圆周阵列
curves = []
for rotation in range(polar_array):
    angle_deg = rotation * (360 / polar_array)  # 计算每个阵列的旋转角度

    # 应用旋转到已经应用了spiral_deg°旋转和衰减的曲线上
    x_rotated = []
    y_rotated = []
    for i in range(len(x_rot)):
        angle_rad = np.radians(angle_deg)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        x_rot_val = x_rot[i] * cos_angle - y_rot[i] * sin_angle
        y_rot_val = x_rot[i] * sin_angle + y_rot[i] * cos_angle
        x_rotated.append(x_rot_val)
        y_rotated.append(y_rot_val)

    curves.append((x_rotated, y_rotated, z))

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
t_red = np.linspace(1, num_bands, 100)
z_red = np.log(t_red) / ln_phi

# 绘制z轴（中轴）
ax1.plot(np.zeros_like(z_red), np.zeros_like(z_red), z_red,
         color='purple', linewidth=2, alpha=0.7)

# 设置3D坐标轴标签和标题
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'3D Golden Ratio Spiral with Polar Array ({polar_array} spirals, spiral_deg={spiral_deg}°)')
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

# 设置视角
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
plt.savefig(f"golden_ratio_spiral_{num_bands}_bands_with_polar_array_{polar_array}_deg_{spiral_deg}.png",
            dpi=300, transparent=True)
plt.show()