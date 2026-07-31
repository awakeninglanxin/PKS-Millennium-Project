# -*- coding: utf-8 -*-
"""
整理要点：
- 按模块化/分节排版：参数区 / 公共函数 / 计算基曲线 / 连续旋转与衰减 / 圆周阵列 / 作图
- 圆周阵列：for rotation in range(polar_array), angle_deg = rotation * (360 / polar_array)
- 不保存 PNG；每张图均显示图例；最后统一 plt.tight_layout(); plt.show()

你可以直接调整“参数区”里的变量（如 polar_array、spiral_deg、amp_continuous 等）。
"""

# ===================== 导入与基础设置 =====================
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (确保 3D 可用)

# ===================== 参数区（可按需调整） =====================
T = 2 * np.pi
user_num = 21
shift_radian = 0.0

# 原函数参数
a, m = np.pi, 2/3

# 连续自转设置：每个周期自转角度（度）；以及圆周阵列数量
spiral_deg = 45            # 每一整个周期 T 内自旋转的角度（度），0 表示不随 t 自转
polar_array = 9            # 圆周阵列个数（等分 360°）

# 采样
t_min = T
t_max = T + T * user_num
t = np.linspace(t_min, t_max, 81 * user_num)

# 画图外观
LINE_W = 1.0
ALPHA = 0.9

# ===================== 连续对数积分衰减因子（保持你给的默认） =====================
def amp_continuous(t):
    # 扁平 2^n 递增：return 1
    # 螺旋扁直管：return (2 ** (t / T)) / (np.sqrt(9 + 2 ** (4 * (t / T) - 2)))
    # 双曲线（你的默认）：
    return (2 ** (t/T)) / (np.sqrt(9 + 2 ** (4 * (t/T) - 2))) / t

# ===================== 原始函数族 =====================
def x_fun(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t))))

def y_fun(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) +
              np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) *
             (((k**2 - 1)/k) * b + ((k**2 + 1)/k) *
              np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) /
             (2*k*np.sqrt(1 + k**2)))
    return a * (m*term1 + term2)

def x_minus(t, b, k, a, shift_radian):
    return a * (2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t)))) - shift_radian

def y_add(t, b, k, a, m, shift_radian):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) +
              np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) *
             (((k**2 - 1)/k) * b + ((k**2 + 1)/k) *
              np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) /
             (2*k*np.sqrt(1 + k**2)))
    return a * (m*term1 + term2) + shift_radian

def z_fun(t):
    return t / T

def k_fun(t):
    return (4 ** (t / T)) / 6

def b_fun(t):
    return (5 * (2 ** (t / T)) / 6)

# ===================== 计算“基曲线” =====================
# 注意：这里保留你原有的四条中用到的两条：x_minus, y_add
x_vals     = x_fun(t, b_fun(t), k_fun(t), a)
y_vals     = y_fun(t, b_fun(t), k_fun(t), a, m)
x_vals_add = x_minus(t, b_fun(t), k_fun(t), a, shift_radian)
y_vals_min = y_add(t,   b_fun(t), k_fun(t), a, m, shift_radian)
middle_curve = (x_vals_add + y_vals_min) / 2  # 供你对比/调试（未参与绘制）

# ===================== 连续自转角与衰减（逐点） =====================
# 自转角：从 0 累计到 user_num * spiral_deg（度），并映射到每个采样点
total_rotation_degrees = user_num * spiral_deg
rotation_angles_deg = np.linspace(0.0, total_rotation_degrees, len(t))
rotation_angles_rad = np.radians(rotation_angles_deg)

# 衰减
amp_factor = amp_continuous(t)

def apply_rotation_and_decay(x_data, y_data, amp_factor, rotation_angles_rad):
    """对整条曲线：逐点绕原点旋转（角度随 t 变），再乘以衰减幅度。"""
    x_rot = np.zeros_like(x_data)
    y_rot = np.zeros_like(y_data)
    for i in range(len(x_data)):
        ca = np.cos(rotation_angles_rad[i]); sa = np.sin(rotation_angles_rad[i])
        x_rot[i] = x_data[i] * ca - y_data[i] * sa
        y_rot[i] = x_data[i] * sa + y_data[i] * ca
    return x_rot * amp_factor, y_rot * amp_factor

x_vals_rot, y_vals_rot = apply_rotation_and_decay(x_vals,     y_vals,     amp_factor, rotation_angles_rad)
x_add_rot,  y_min_rot  = apply_rotation_and_decay(x_vals_add, y_vals_min, amp_factor, rotation_angles_rad)

# ===================== 圆周阵列工具 =====================
def rotate_degrees(x, y, angle_deg):
    """整体刚体旋转曲线（度）。用于把“已自转&衰减”的曲线复制到不同方向。"""
    ang = np.radians(angle_deg)
    ca, sa = np.cos(ang), np.sin(ang)
    xr = x * ca - y * sa
    yr = x * sa + y * ca
    return xr, yr

# ===================== 生成 2D 圆周阵列（基于 x_add_rot / y_min_rot） =====================
curves = []
for rotation in range(polar_array):
    angle_deg = rotation * (360.0 / polar_array)
    xr, yr = rotate_degrees(x_add_rot, y_min_rot, angle_deg)
    curves.append((xr, yr))

# ===================== 图 A：2D 圆周阵列（HSV 颜色） =====================
fig_a, ax_a = plt.subplots(figsize=(10, 10))
colors = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))

for i, (xc, yc) in enumerate(curves):
    ax_a.plot(xc, yc, color=colors[i], linewidth=LINE_W, alpha=ALPHA,
              label=f'Rotation {i * (360 / polar_array):.0f}°')

ax_a.scatter(0, 0, color='black', s=10, zorder=5, label='Origin (0,0)')
ax_a.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax_a.axvline(0, color='gray', linestyle='--', alpha=0.5)
ax_a.set_title(f'Spiral Polar Array (N={polar_array})')
ax_a.set_xlabel('x(t)'); ax_a.set_ylabel('y(t)')
ax_a.set_aspect('equal', adjustable='box')
ax_a.grid(True, alpha=0.3)

# 自动对称坐标范围
all_x = np.concatenate([c[0] for c in curves])
all_y = np.concatenate([c[1] for c in curves])
max_r = max(np.max(np.abs(all_x)), np.max(np.abs(all_y))) * 1.1
ax_a.set_xlim(-max_r, max_r)
ax_a.set_ylim(-max_r, max_r)

ax_a.legend(loc='upper right')

# ===================== 图 B：t 与曲线值（对比） =====================
fig_b, ax_b = plt.subplots(figsize=(12, 5))
ax_b.plot(t, x_add_rot, color='tab:blue',  label='x_add(t)',  alpha=ALPHA, linewidth=LINE_W)
ax_b.plot(t, y_min_rot, color='tab:red',   label='y_minus(t)', alpha=ALPHA, linewidth=LINE_W)
ax_b.plot(t, -1.0/t,    color='tab:purple',label='-1/t', alpha=0.8, linewidth=1.0)
ax_b.set_title('Curves with Continuous Rotation and Decay')
ax_b.set_xlabel('t'); ax_b.set_ylabel('Value')
ax_b.grid(True, alpha=0.3)
ax_b.legend()

# ===================== 图 C：3D 圆周阵列（HSV 颜色 + XY 投影） =====================
z_vals = z_fun(t)
fig_c = plt.figure(figsize=(11, 10))
ax_c = fig_c.add_subplot(111, projection='3d')
colors_3d = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))

all_x3d, all_y3d, all_z3d = [], [], []
for i, (xc, yc) in enumerate(curves):
    # 收集边界
    all_x3d.extend(xc); all_y3d.extend(yc); all_z3d.extend(z_vals)
    # 空间曲线
    ax_c.plot(xc, yc, z_vals, color=colors_3d[i], linewidth=0.7, alpha=0.9,
              label=f'Spiral {i * (360 / polar_array):.0f}°')
    # XY 平面投影
    ax_c.plot(xc, yc, np.zeros_like(z_vals), color=colors_3d[i],
              linewidth=0.6, alpha=0.6, linestyle='--')

ax_c.set_xlabel('X'); ax_c.set_ylabel('Y'); ax_c.set_zlabel('Z')
ax_c.set_title(f'3D Spiral Polar Array (spiral_deg={spiral_deg}°)')
# 等比例设置（x/y 同量纲；z 自适应）
x_min, x_max = min(all_x3d), max(all_x3d)
y_min, y_max = min(all_y3d), max(all_y3d)
z_min, z_max = min(all_z3d), max(all_z3d)
x_ctr, y_ctr = (x_min + x_max)/2, (y_min + y_max)/2
max_xy = max(x_max - x_min, y_max - y_min)
ax_c.set_xlim(x_ctr - max_xy/2, x_ctr + max_xy/2)
ax_c.set_ylim(y_ctr - max_xy/2, y_ctr + max_xy/2)
ax_c.set_zlim(z_min, z_max)

ax_c.legend(loc='upper left')

# ===================== 显示 =====================
plt.tight_layout()
plt.show()
