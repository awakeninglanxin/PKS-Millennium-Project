import numpy as np
import matplotlib.pyplot as plt

# 参数设置
k, b, a, m, user_num, amp = 2/3, 5/3, 2 * np.pi, 2/3, 81, 9
t_min = 2 * np.pi / (user_num + 1)
t_max = 2 * np.pi + (2 * user_num) * np.pi
t = np.linspace(t_min, t_max, 81*user_num)

# 连续对数积分衰减因子
def amp_continuous(t, user_num):
    return 1.0 / ((1.0 + t / (2 * np.pi)) * np.log(user_num + 1))

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

def x_minus(t, b, k, a, t_min):
    return a * ((2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))) - amp * t_min)

def y_add(t, b, k, a, m, t_min):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) +
                                      np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) *
             (((k ** 2 - 1) / k) * b + ((k ** 2 + 1) / k) *
              np.sqrt(b ** 2 - 4 * k * np.cos(t)))) - \
            ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) /
             (2 * k * np.sqrt(1 + k ** 2)))
    return a * ((m * term1 + term2) + amp * t_min)

# 计算所有曲线（先不应用衰减）
x_vals = x_fun(t, b, k, a)
y_vals = y_fun(t, b, k, a, m)
x_vals_add = x_minus(t, b, k, a, t_min)
y_vals_minus = y_add(t, b, k, a, m, t_min)

total_rotation_degrees = -user_num * 9
rotation_angles = np.linspace(0, total_rotation_degrees, len(t))
rotation_angles_rad = np.radians(rotation_angles)

# 应用衰减因子
amp_factor = amp_continuous(t, user_num)

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

# 修正：中间曲线应该是修改后曲线的平均值
middle_curve = (x_vals_add_rot +y_vals_minus_rot) / 2

# 绘制所有曲线随时间变化
plt.figure(figsize=(14, 8))
# plt.plot(t, x_vals_rot, color='green', linestyle='--', label='x(t) rotated', alpha=0.8)
# plt.plot(t, y_vals_rot, color='orange', linestyle='--', label='y(t) rotated', alpha=0.8)
plt.plot(t, x_vals_add_rot, color='blue', label='x_add(t) rotated', alpha=0.8)
plt.plot(t, y_vals_minus_rot, color='red', label='y_minus(t) rotated', alpha=0.8)
plt.plot(t, middle_curve, color='purple', linestyle='--', label='middle_curve', alpha=0.8)

plt.xlabel('t')
plt.ylabel('Value')
plt.title(f'All Curves with Rotation and Decay ({user_num / 2} full rotations)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# 绘制螺旋曲线（2D平面）
plt.figure(figsize=(12, 12))

# 原始曲线
plt.plot(x_vals_rot, y_vals_rot, color='green', linewidth=0.5, label='Original Curve', alpha=0.8)
plt.plot(x_vals_add_rot, y_vals_minus_rot, color='purple', linewidth=0.5, label='Modified Curve (x_add, y_minus)', alpha=0.8)

# 标记原点和关键点
plt.scatter(0, 0, color='black', s=30, label='Origin (0,0)', zorder=5)

# 添加坐标轴
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.title(f'Rotating Spiral Curves with {user_num / 2} full rotations around Origin\n(All curve types)')
plt.axis('equal')
plt.legend()
plt.grid(True, alpha=0.3)

# 设置对称的坐标轴范围
all_x = np.concatenate([x_vals_rot, x_vals_add_rot])
all_y = np.concatenate([y_vals_rot, y_vals_minus_rot])
max_range = max(np.max(np.abs(all_x)), np.max(np.abs(all_y))) * 1.1
plt.xlim(-max_range, max_range)
plt.ylim(-max_range, max_range)

plt.show()