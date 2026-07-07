import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import os

# 黄金比例常数
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值

# 添加旋转、衰减和圆周阵列功能
polar_array = 3  # 圆周阵列数量

# 参数设置
num_bands = 29  # 波段数量
total_points = 120 * num_bands  # 总点数


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

# 转换为numpy数组以提高性能
spiral_x = np.array(spiral_x)
spiral_y = np.array(spiral_y)
spiral_z = np.array(spiral_z)
t_shape_values = np.array(t_shape_values)

# 计算漏斗曲线高度的一半
half_high = (spiral_z.max() + spiral_z.min()) / 2


# 连续对数积分衰减因子
def amp_continuous(t_shape):
    return 1  # 原始螺旋


# 对每条曲线分别应用旋转和衰减
def apply_rotation_and_decay(x_data, y_data, amp_factor, rotation_angles_rad):
    cos_angles = np.cos(rotation_angles_rad)
    sin_angles = np.sin(rotation_angles_rad)

    # 向量化计算旋转
    x_rotated = x_data * cos_angles - y_data * sin_angles
    y_rotated = x_data * sin_angles + y_data * cos_angles

    # 应用衰减
    return x_rotated * amp_factor, y_rotated * amp_factor


# 计算衰减因子
amp_factor = amp_continuous(t_shape_values)

# 创建红色曲线数据
t_red = np.linspace(1, num_bands, 100)
x_red_positive = 1 / t_red
x_red_negative = -1 / t_red
z_red = np.log(t_red) / ln_phi

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建3D子图 - 调整视图中心
ax1 = fig.add_subplot(121, projection='3d')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title('3D Logarithmic Spiral Animation')
ax1.grid(True)

# 创建2D XY投影子图
ax2 = fig.add_subplot(122)
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title('XY Plane Projection')
ax2.grid(True)
ax2.set_aspect('equal')  # 保持纵横比相等

# 使用HSV颜色空间生成均匀分布的颜色
colors = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))

# 创建空的曲线对象用于动画
spiral_lines_3d = []
spiral_lines_2d = []

for i in range(polar_array):
    # 3D子图
    line_3d, = ax1.plot([], [], [], color=colors[i], linewidth=1.0, alpha=0.8)
    spiral_lines_3d.append(line_3d)

    # 2D子图
    line_2d, = ax2.plot([], [], color=colors[i], linewidth=1.0, alpha=0.8)
    spiral_lines_2d.append(line_2d)

# 添加红色曲线（保持原始）到3D图
red_line1, = ax1.plot([], [], [], color='red', linewidth=2, alpha=0.7)
red_line2, = ax1.plot([], [], [], color='red', linewidth=2, alpha=0.7)
purple_line, = ax1.plot([], [], [], color='purple', linewidth=2, alpha=0.7)

# 添加红色曲线到2D图
red_line1_2d, = ax2.plot([], [], color='red', linewidth=2, alpha=0.7)
red_line2_2d, = ax2.plot([], [], color='red', linewidth=2, alpha=0.7)
purple_point, = ax2.plot([0], [0], 'o', color='purple', markersize=5, alpha=0.7)  # 固定为原点

# 计算并设置固定的坐标轴范围
x_min, x_max = spiral_x.min(), spiral_x.max()
y_min, y_max = spiral_y.min(), spiral_y.max()
z_min, z_max = spiral_z.min(), spiral_z.max()

# 使用最大的范围来保持比例 - 将3D图形的范围放大两倍
max_range = max(np.abs(x_min), np.abs(x_max), np.abs(y_min), np.abs(y_max), np.abs(z_min), np.abs(z_max)) * 1.1
max_range_3d = max_range /3  # 缩小3倍

# 设置3D子图的固定范围 - 使用放大后的范围，并调整中心点
ax1.set_xlim(-max_range_3d, max_range_3d)
ax1.set_ylim(-max_range_3d, max_range_3d)
ax1.set_zlim(half_high - max_range_3d, half_high + max_range_3d)  # 以half_high为中心

# 设置3D视角 - 聚焦到(0,0,half_high)
ax1.view_init(elev=30, azim=-60)
ax1.set_box_aspect([1, 1, 1])  # 保持比例

# 设置2D子图固定范围
xy_range = max(np.abs(spiral_x).max(), np.abs(spiral_y).max()) * 1.1
ax2.set_xlim(-xy_range, xy_range)
ax2.set_ylim(-xy_range, xy_range)


# 初始化函数：设置初始数据
def init():
    # 设置初始旋转为0度
    rotation_angles = np.zeros_like(t_total)
    rotation_angles_rad = np.radians(rotation_angles)

    # 应用旋转和衰减到基础曲线
    spiral_x_rot, spiral_y_rot = apply_rotation_and_decay(spiral_x, spiral_y, amp_factor, rotation_angles_rad)

    # 创建所有方向的曲线 - 圆周阵列
    curves = []
    for rotation in range(polar_array):
        angle_deg = rotation * (360 / polar_array)  # 计算每个阵列的旋转角度

        # 应用旋转到已经应用了spiral_deg°旋转和衰减的曲线上
        angle_rad = np.radians(angle_deg)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)

        x_rotated = spiral_x_rot * cos_angle - spiral_y_rot * sin_angle
        y_rotated = spiral_x_rot * sin_angle + spiral_y_rot * cos_angle

        curves.append((x_rotated, y_rotated, spiral_z))

    # 更新3D螺旋线
    for i, (x_curve, y_curve, z_curve) in enumerate(curves):
        spiral_lines_3d[i].set_data(x_curve, y_curve)
        spiral_lines_3d[i].set_3d_properties(z_curve)

    # 更新2D螺旋线
    for i, (x_curve, y_curve, _) in enumerate(curves):
        spiral_lines_2d[i].set_data(x_curve, y_curve)

    # 更新红色曲线（保持原始）
    red_line1.set_data(x_red_positive, np.zeros_like(z_red))
    red_line1.set_3d_properties(z_red)

    red_line2.set_data(x_red_negative, np.zeros_like(z_red))
    red_line2.set_3d_properties(z_red)

    purple_line.set_data(np.zeros_like(z_red), np.zeros_like(z_red))
    purple_line.set_3d_properties(z_red)

    # 更新2D红色曲线
    red_line1_2d.set_data(x_red_positive, np.zeros_like(x_red_positive))
    red_line2_2d.set_data(x_red_negative, np.zeros_like(x_red_negative))

    return spiral_lines_3d + spiral_lines_2d + [red_line1, red_line2, purple_line,
                                                red_line1_2d, red_line2_2d, purple_point]


# 动画更新函数
def update(frame):
    spiral_deg = frame  # 当前旋转度数

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
        angle_rad = np.radians(angle_deg)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)

        x_rotated = spiral_x_rot * cos_angle - spiral_y_rot * sin_angle
        y_rotated = spiral_x_rot * sin_angle + spiral_y_rot * cos_angle

        curves.append((x_rotated, y_rotated, spiral_z))

    # 更新3D螺旋线
    for i, (x_curve, y_curve, z_curve) in enumerate(curves):
        spiral_lines_3d[i].set_data(x_curve, y_curve)
        spiral_lines_3d[i].set_3d_properties(z_curve)

    # 更新2D螺旋线
    for i, (x_curve, y_curve, _) in enumerate(curves):
        spiral_lines_2d[i].set_data(x_curve, y_curve)

    # 更新标题显示当前旋转度数
    ax1.set_title(f'3D Logarithmic Spiral Animation\nRotation: {spiral_deg:.1f}°')
    ax2.set_title(f'XY Plane Projection\nRotation: {spiral_deg:.1f}°')

    # 强制保持坐标轴范围不变 - 以half_high为中心
    ax1.set_xlim(-max_range_3d, max_range_3d)
    ax1.set_ylim(-max_range_3d, max_range_3d)
    ax1.set_zlim(half_high - max_range_3d, half_high + max_range_3d)

    ax2.set_xlim(-xy_range, xy_range)
    ax2.set_ylim(-xy_range, xy_range)

    return spiral_lines_3d + spiral_lines_2d + [red_line1, red_line2, purple_line,
                                                red_line1_2d, red_line2_2d]


# 创建输出文件夹（如果不存在）
output_folder = "spiral_rotation_frames"
os.makedirs(output_folder, exist_ok=True)

# 定义要保存的帧
frames = np.linspace(0, 360, 9)  # 从0到360度，共9帧
# 在创建图形后，添加以下代码来固定子图布局
fig.subplots_adjust(left=0.05, right=0.95, wspace=0.3)  # 调整左右边距和子图间距

# 在保存PNG的循环中，添加以下代码确保布局不变
for i, frame in enumerate(frames):
    update(frame)
    plt.tight_layout()

    # 强制固定子图位置
    fig.subplots_adjust(left=0.05, right=0.95, wspace=0.3)  # 与上面相同的参数

    filename = os.path.join(output_folder, f'spiral_rotation_frame_{i:03d}.png')
    plt.savefig(filename, dpi=100, bbox_inches='tight')

print("All frames saved successfully!")

# 创建动画（但不显示）
ani = FuncAnimation(fig, update, frames=frames,
                    init_func=init, interval=3, blit=True)

# 显示动画
plt.tight_layout()
plt.show()

# 关闭图形释放内存
plt.close(fig)