import numpy as np
import matplotlib.pyplot as plt

# 参数设置
user_num, amp = 49,1
a, m = 2* np.pi,2/3
spiral_deg, polar_array =45, 12
T=2 * np.pi
t_min = 2 * np.pi
t_max = (2 * np.pi + 1) * user_num
t = np.linspace(t_min, t_max, 81 * user_num)
phi=(np.sqrt(5)-1)/2
L_w=0.5

# 连续对数积分衰减因子
def amp_continuous(t, user_num):
    # return 1.0 / ((1.0 + t / (2 * np.pi)) * np.log(user_num + 1))  #注意除t
    return np.log(t)/(np.log(phi)*(2*t/ (np.sqrt(t)))) #基于直螺旋管+黄金比锥，但除t  这个是默认设置
    # return 1/(2 / (np.sqrt(t)))  #直螺旋管但注意不除t
    # return 1/(2*t / (np.sqrt(t)))  #直螺旋管但注意除t

# 原函数定义
def x_fun(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))


def y_fun(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) +
                                      np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) *
             (((k ** 2 - 1) / k) * b + ((k ** 2 + 1) / k) *
              np.sqrt(b ** 2 - 4 * k * np.cos(t)))) - \
            ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) /
             (2 * k * np.sqrt(1 + k ** 2)))
    return a * (m * term1 + term2)


def x_minus(t, b, k, a):
    return a * ((2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))) - amp)


def y_add(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) +
                                      np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) *
             (((k ** 2 - 1) / k) * b + ((k ** 2 + 1) / k) *
              np.sqrt(b ** 2 - 4 * k * np.cos(t)))) - \
            ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) /
             (2 * k * np.sqrt(1 + k ** 2)))
    return a * ((m * term1 + term2) + amp)

def b_fun(t):
    return 2*t /(T*np.sqrt(t))# 化简后的公式

def k_fun():
    return 1/T  # 化简后的公式

# 计算曲线k、b随时间t变化
x_vals = x_fun(t, b_fun(t), k_fun(), a)
y_vals = y_fun(t, b_fun(t), k_fun(), a, m)
x_vals_add = x_minus(t, b_fun(t), k_fun(), a)
y_vals_minus = y_add(t, b_fun(t), k_fun(), a, m)

# 应用spiral_deg°连续旋转
total_rotation_degrees = user_num * spiral_deg
rotation_angles = np.linspace(0, total_rotation_degrees, len(t))
rotation_angles_rad = np.radians(rotation_angles)

# 应用衰减因子
amp_factor = amp_continuous(t, user_num)
# amp_factor = 1

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


# 应用旋转和衰减到所有曲线
x_vals_rot, y_vals_rot = apply_rotation_and_decay(x_vals, y_vals, amp_factor, rotation_angles_rad)
x_vals_add_rot, y_vals_minus_rot = apply_rotation_and_decay(x_vals_add, y_vals_minus, amp_factor, rotation_angles_rad)

# 修正的旋转函数 - 使用正确的角度旋转
def rotate_degrees(x, y, angle_deg):
    """旋转点(x, y)指定角度（度）"""
    angle_rad = np.radians(angle_deg)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    x_rot = x * cos_angle - y * sin_angle
    y_rot = x * sin_angle + y * cos_angle
    return x_rot, y_rot

# 创建所有方向的曲线 - 使用已经应用了spiral_deg°旋转和衰减的曲线
curves = []
for rotation in range(polar_array):
    angle_deg = rotation * (360 / polar_array)  # 计算每个阵列的旋转角度

    x_rotated = np.zeros_like(x_vals_add_rot)
    y_rotated = np.zeros_like(y_vals_minus_rot)

    for i in range(len(x_vals_add_rot)):
        # 应用旋转到已经应用了spiral_deg°旋转和衰减的曲线上
        x_rot, y_rot = rotate_degrees(x_vals_add_rot[i], y_vals_minus_rot[i], angle_deg)
        x_rotated[i] = x_rot
        y_rotated[i] = y_rot

    curves.append((x_rotated, y_rotated))

# 绘制阵列结构
plt.figure(figsize=(12, 12))

# 使用HSV颜色空间生成均匀分布的颜色
colors = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))

# 绘制所有曲线
for i, (x_curve, y_curve) in enumerate(curves):
    plt.plot(x_curve, y_curve, color=colors[i], linewidth=L_w,
             label=f'Rotation {i * (360 / polar_array):.0f}°', alpha=0.8)

# 标记原点和关键点
plt.scatter(0, 0, color='Gold', s=50, label='Origin (0,0)', zorder=5)

# 添加坐标轴
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.title(f'spiral polar array ({polar_array} array)')
plt.axis('equal')
plt.legend()
plt.grid(True, alpha=0.3)

# 设置对称的坐标轴范围
all_x = np.concatenate([curve[0] for curve in curves])
all_y = np.concatenate([curve[1] for curve in curves])
max_range = max(np.max(np.abs(all_x)), np.max(np.abs(all_y))) * 1.1
if np.isnan(max_range) or np.isinf(max_range):
    max_range = 10  # 设置一个默认的范围
plt.xlim(-max_range, max_range)
plt.ylim(-max_range, max_range)

plt.show()

# 绘制原始曲线和修改后的曲线对比
plt.figure(figsize=(14, 8))
plt.plot(t, x_vals_add_rot, color='blue', label='x_add(t)', alpha=0.8)
plt.plot(t, y_vals_minus_rot, color='red', label='y_minus(t)', alpha=0.8)
plt.xlabel('t')
plt.ylabel('Value')
plt.title('Curves Continuous Rotation and Decay')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
