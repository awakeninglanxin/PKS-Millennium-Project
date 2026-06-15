# -*- coding: utf-8 -*-
"""
功能清单：
1) 2D：合并螺旋（相位差 180°）
2) 2D：t-x(t)
3) 2D：t-y(t)
4) 3D：合并螺旋（共享 z(t)）
5) 2D 圆周阵列（HSV 不同颜色；沿角度复制并旋转）
6) 3D 圆周阵列（HSV 不同颜色；绕 z 轴旋转）

只显示图像，不保存文件：每个轴 ax.legend()，最后 plt.tight_layout(); plt.show()

与原脚本一致点：
- 先得到已衰减的曲线，再做“圆周阵列”旋转。
- 圆周阵列：for rotation in range(polar_array): angle = rotation * spiral_deg
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib.colors import hsv_to_rgb

# ===================== 基本参数 =====================
T = 2 * np.pi      # 基本周期
user_num = 6       # 使用的周期数
num_samples = 81 * user_num
dis_shift=0#蛋截面曲线平移离原点的距离,正值为蛋向下平移，负值为蛋向上平移
dis_tocenter=0#蛋螺旋曲线俯视图看45°偏离公转中心的距离一般取(pi/4)的整数倍
# 圆周阵列参数（方向数量 & 起始偏移角）
polar_array = 12                 # 方向数量（等分 360°）
initial_rotation_deg = 0.0       # 初始整体偏移角
spiral_deg = 360.0 / polar_array # 每个方向之间的角度

# 线条样式
LINE_W = 1.3
ALPHA  = 0.95

# ===================== 时间与采样 =====================
t_min = T
t_max = T + T * user_num
t = np.linspace(t_min, t_max, num_samples)

# ===================== 公共函数 =====================
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
    return a * ((m*term1 + term2)) + shift_radian

def apply_rotation_and_decay(x_data, y_data, amp_factor, rotation_angles_rad):
    """逐点（可变角）旋转 + 衰减；本脚本 rotation_angles_rad=0，等价仅做幅度衰减。"""
    x_rotated = np.zeros_like(x_data)
    y_rotated = np.zeros_like(y_data)
    for i in range(len(x_data)):
        ca = np.cos(rotation_angles_rad[i]); sa = np.sin(rotation_angles_rad[i])
        x_rotated[i] = x_data[i] * ca - y_data[i] * sa
        y_rotated[i] = x_data[i] * sa + y_data[i] * ca
    return x_rotated * amp_factor, y_rotated * amp_factor

def rotate_xy(x, y, angle_rad):
    """整体刚体旋转（圆周阵列用）"""
    ca, sa = np.cos(angle_rad), np.sin(angle_rad)
    xr = x * ca - y * sa
    yr = x * sa + y * ca
    return xr, yr

def hsv_palette(n, s=0.95, v=0.95):
    """等分色相 HSV 调色板"""
    hues = np.linspace(0.0, 1.0, n, endpoint=False)
    return [hsv_to_rgb([h, s, v]) for h in hues]

rotation_angles_rad = np.zeros_like(t)  # 原脚本为 0，如需每点自转可改写

# ===================== 螺旋 A（“阴”） =====================
a0, m0 = 2*np.pi, 2/3+dis_shift
shift0 = dis_tocenter
def amp0(t):
    n = t / T
    num = 2 * (2 * n**2 + 2 * n + 1)
    den = n * (n + 1)
    # return 1  # 螺旋微微漏斗(基本是直管)
    # return 1/np.sqrt(num / den) #螺旋直水滴管
    return 1 / (t * np.sqrt(num / den)) #螺旋双曲水滴漏斗管

def k0(t):
    return (t/T) / (t/T + 1)
def b0(t):
    return 2 * np.sqrt((t/T) / ((t/T) + 1)) + 1e-15
x0 = x_minus(t, b0(t), k0(t), a0, shift0)
y0 = y_add(t, b0(t), k0(t), a0, m0, shift0)
x0f, y0f = apply_rotation_and_decay(x0, y0, amp0(t), rotation_angles_rad)

# ===================== 螺旋 B（“阳”）+ 强制 180° 相位差 =====================
a1, m1 = 2*np.pi, 2/3+dis_shift
shift1 = dis_tocenter
def amp1(t):
    n = t / T
    # return 1  # 螺旋直锥
    # return 1/np.sqrt(2*(n+1/n)) #螺旋直水滴管
    return 1/(t*np.sqrt(2*(n+1/n))) #螺旋双曲水滴漏斗管

def k1(t):
    return 1 / (t / T)
def b1(t):
    return 2 / np.sqrt(t / T) + 1e-15
x1 = x_minus(t, b1(t), k1(t), a1, shift1)
y1 = y_add(t, b1(t), k1(t), a1, m1, shift1)
x1f, y1f = apply_rotation_and_decay(x1, y1, amp1(t), rotation_angles_rad)

# x1p, y1p = -x1f, -y1f# 两种螺旋相位差为 180°
x1p, y1p = x1f, y1f #两种螺旋相位差为 0°

# ===================== 1) 2D 合并 =====================
fig_xy, ax = plt.subplots(figsize=(9, 9))
ax.plot(x0f, y0f, label="Spiral A (Yin)", linewidth=LINE_W, alpha=ALPHA)
ax.plot(x1p, y1p, label="Spiral B (Yang) 180°", linewidth=LINE_W, alpha=ALPHA)
ax.axhline(0, linestyle="--", alpha=0.35); ax.axvline(0, linestyle="--", alpha=0.35)
ax.set_aspect('equal', adjustable='box')
ax.set_title("Two Spirals Combined (Phase = 180°)")
ax.set_xlabel("x(t)"); ax.set_ylabel("y(t)")
ax.grid(True, alpha=0.3)
ax.legend()

# ===================== 2) t-x(t) =====================
fig_tx, ax_tx = plt.subplots(figsize=(12, 4.5))
ax_tx.plot(t, x0f, label="x_A(t)", linewidth=LINE_W, alpha=ALPHA)
ax_tx.plot(t, x1p, label="x_B(t) (180°)", linewidth=LINE_W, alpha=ALPHA)
ax_tx.set_title("t vs x(t)"); ax_tx.set_xlabel("t"); ax_tx.set_ylabel("x(t)")
ax_tx.grid(True, alpha=0.3)
ax_tx.legend()

# ===================== 3) t-y(t) =====================
fig_ty, ax_ty = plt.subplots(figsize=(12, 4.5))
ax_ty.plot(t, y0f, label="y_A(t)", linewidth=LINE_W, alpha=ALPHA)
ax_ty.plot(t, y1p, label="y_B(t) (180°)", linewidth=LINE_W, alpha=ALPHA)
ax_ty.set_title("t vs y(t)"); ax_ty.set_xlabel("t"); ax_ty.set_ylabel("y(t)")
ax_ty.grid(True, alpha=0.3)
ax_ty.legend()

# ===================== 4) 3D 合并（共享 z(t)） =====================
z = (t - t.min()) / (t.max() - t.min())
fig_3d = plt.figure(figsize=(9, 9))
ax3d = fig_3d.add_subplot(111, projection='3d')
ax3d.plot(x0f, y0f, z, label="Spiral A (Yin)", linewidth=LINE_W, alpha=ALPHA)
ax3d.plot(x1p, y1p, z, label="Spiral B (Yang) 180°", linewidth=LINE_W, alpha=ALPHA)
ax3d.set_title("3D Spirals (shared z(t))")
ax3d.set_xlabel("x(t)"); ax3d.set_ylabel("y(t)"); ax3d.set_zlabel("z(t) ~ normalized t")
ax3d.legend()

# ===================== 5) 2D 圆周阵列（HSV 颜色） =====================
fig_arr2d, ax2 = plt.subplots(figsize=(10, 10))
ax2.set_title(f"2D Polar Array (N={polar_array}, HSV colors)")
ax2.set_xlabel("x"); ax2.set_ylabel("y")
ax2.grid(True, alpha=0.25)
ax2.set_aspect('equal', adjustable='box')

palette2d = hsv_palette(polar_array)
for i in range(polar_array):
    angle_deg = initial_rotation_deg + i * spiral_deg
    angle = np.deg2rad(angle_deg)
    # 旋转已衰减的基准曲线
    xA, yA = rotate_xy(x0f, y0f, angle)
    xB, yB = rotate_xy(x1p, y1p, angle)
    color = palette2d[i]
    # 同色区分：A 实线，B 虚线
    labA = "A (Yin)" if i == 0 else None
    labB = "B (Yang, 180°)" if i == 0 else None
    ax2.plot(xA, yA, color=color, linewidth=LINE_W, alpha=ALPHA, label=labA)
    ax2.plot(xB, yB, color=color, linewidth=LINE_W, alpha=ALPHA*0.9, linestyle="--", label=labB)

ax2.legend()

# ===================== 6) 3D 圆周阵列（HSV 颜色） =====================
fig_arr3d = plt.figure(figsize=(11, 9))
ax3 = fig_arr3d.add_subplot(111, projection='3d')
ax3.set_title(f"3D Polar Array (N={polar_array}, HSV colors)")
ax3.set_xlabel("x"); ax3.set_ylabel("y"); ax3.set_zlabel("z")
ax3.set_box_aspect((1, 1, 1))  # 立方比例

palette3d = hsv_palette(polar_array)
for i in range(polar_array):
    angle_deg = initial_rotation_deg + i * spiral_deg
    angle = np.deg2rad(angle_deg)
    xA, yA = rotate_xy(x0f, y0f, angle)
    xB, yB = rotate_xy(x1p, y1p, angle)
    color = palette3d[i]
    labA = "A (Yin)" if i == 0 else None
    labB = "B (Yang, 180°)" if i == 0 else None
    ax3.plot(xA, yA, z, color=color, linewidth=LINE_W, alpha=ALPHA, label=labA)
    ax3.plot(xB, yB, z, color=color, linewidth=LINE_W, alpha=ALPHA*0.9, linestyle="--", label=labB)

ax3.legend()

# ===================== 显示 =====================
plt.tight_layout()
plt.show()
