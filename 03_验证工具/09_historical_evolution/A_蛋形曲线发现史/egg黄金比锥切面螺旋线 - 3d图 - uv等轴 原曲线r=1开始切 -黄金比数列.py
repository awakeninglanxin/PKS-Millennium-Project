import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (兼容部分环境)
from scipy.interpolate import CubicSpline
import ezdxf

# ======================
# 参数 & 常量设置
# ======================
phi = (np.sqrt(5) - 1) / 2  # 小黄金比例
ln_phi = np.log(phi)        # 负值
# 独立设置：红色曲线（漏斗母线/曲面）最大 t_s
RED_T_MAX = 29

# ======================
# Lotus 数列 Z(n) = Z(n-1) + Z(n-2), Z(0)=2, Z(1)=1
# 返回从 n=1 开始的序列: [1, 3, 4, 7, 11, 18, 29, 47] （默认 7 次迭代）
# ======================
def generate_lotus_sequence(num_terms=7):
    Z = [2, 1]  # Z(0)=2, Z(1)=1
    for i in range(2, num_terms + 1):
        Z.append(Z[i - 1] + Z[i - 2])
    return Z[1:]  # 去掉 Z(0)=2，从 n=1 开始


# 生成 Lotus 数列（仅用于蓝色曲线）
lotus_sequence = generate_lotus_sequence()
max_n = max(lotus_sequence)  # 蓝色曲线自己的跨度（与红曲线无关）

# 红色曲线（漏斗）的最小 z 值（由 t_s 的上界 RED_T_MAX 决定）
min_z_red = np.log(RED_T_MAX) / ln_phi

# （可选）最大允许半径（由公式 r = exp(min_z_red * ln_phi) 推出，此处等于 RED_T_MAX）
r_max = np.exp(min_z_red * ln_phi)

# ======================
# 连续 T 以及 t_s（蓝色曲线使用）
# ======================
total_points = 1000
T = np.linspace(0, 2 * np.pi * max_n, total_points)

n_indices = np.floor(T / (2 * np.pi)).astype(int) + 1
tau = T % (2 * np.pi)
t_s = n_indices + tau / (2 * np.pi)

# z = log(t_s)/ln_phi（仅用于参考）
z = np.log(t_s) / ln_phi

# ======================
# 蓝色曲线半径：样条插值（在 Lotus 点处半径 = phi^(n-1)）
# ======================
lotus_t_s = np.array(lotus_sequence)
lotus_radii = phi ** (lotus_t_s - 1)

# 三次样条（默认支持外推）；如需限制，可对 t_s 做 clip
radius_spline = CubicSpline(lotus_t_s, lotus_radii)
# t_s_clamped = np.clip(t_s, lotus_t_s.min(), lotus_t_s.max())
# r_blue = radius_spline(t_s_clamped)
r_blue = radius_spline(t_s)

# 角度
theta = T + np.pi

# 蓝色曲线（XY 平面）
x_blue = r_blue * np.cos(theta)
y_blue = r_blue * np.sin(theta)

# ======================
# 红色曲线（漏斗母线）& 漏斗曲面：使用独立的 RED_T_MAX
# ======================
n_points = 100  # 总点数

# 使用对数映射调整采样密度（t_min处密集，t_max处稀疏）
log_min = np.log(1)  # t_red_min = 1
log_max = np.log(RED_T_MAX)
log_space = np.linspace(log_min, log_max, n_points)
t_red = np.exp(log_space)

z_red = np.log(t_red) / ln_phi
x_red = 1 / t_red  # 母线在 XZ 平面上的 x

theta_funnel = np.linspace(0, 2 * np.pi, 100)
theta_grid, t_grid = np.meshgrid(theta_funnel, t_red)
x_funnel = (1 / t_grid) * np.cos(theta_grid)
y_funnel = (1 / t_grid) * np.sin(theta_grid)
z_funnel = np.log(t_grid) / ln_phi
# ======================
# 蓝色曲线垂直投影到漏斗表面（得到绿色曲线）
# ======================
# 修正：平方运算符 **2
r_green = np.sqrt(x_blue**2 + y_blue**2)
z_green = np.log(1 / r_green) / ln_phi

# 只保留 z >= min_z_red 的点（在漏斗范围内）
mask = z_green >= min_z_red
x_blue = x_blue[mask]
y_blue = y_blue[mask]
z_green = z_green[mask]
theta = theta[mask]
r_blue = r_blue[mask]
t_s = t_s[mask]

# ======================
# 作图
# ======================
fig = plt.figure(figsize=(18, 8))

# ---- 3D 子图 ----
ax1 = fig.add_subplot(121, projection='3d')

# 蓝色平面曲线（Z=0）
ax1.plot(x_blue, y_blue, np.zeros_like(x_blue), color='blue', linewidth=2, alpha=0.8, label='Blue Curve (2D)')

# 红色母线（正负 x 对称）
ax1.plot(x_red, np.zeros_like(x_red), z_red, color='red', linewidth=2, alpha=0.7, label='Red Curve')
ax1.plot(-x_red, np.zeros_like(x_red), z_red, color='red', linewidth=2, alpha=0.7)

# 漏斗表面（线框）
ax1.plot_wireframe(x_funnel, y_funnel, z_funnel, color='red', alpha=0.1, rstride=10, cstride=10)

# 绿色曲线（投影）
ax1.plot(x_blue, y_blue, z_green, color='green', linewidth=2, alpha=0.8, label='Green Curve (Projection)')


ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title('Blue Curve Projected onto Funnel Surface (Green Curve)')
ax1.grid(True)
ax1.legend()

# 等轴比例
all_x = np.concatenate([x_blue, x_red, x_blue])
all_y = np.concatenate([y_blue, np.zeros_like(x_red), y_blue])
all_z = np.concatenate([np.zeros_like(x_blue), z_red, z_green])

x_min, x_max = np.min(all_x), np.max(all_x)
y_min, y_max = np.min(all_y), np.max(all_y)
z_min, z_max = np.min(all_z), np.max(all_z)
print("z_min",z_min)
max_range = max(x_max - x_min, y_max - y_min, z_max - z_min) / 2.0
mid_x = (x_min + x_max) / 2
mid_y = (y_min + y_max) / 2
mid_z = (z_min + z_max) / 2

# 标记 Lotus 数列对应的点
for n in range(1,abs(int(z_min))+2):
    t_s_point = n
    z_point = np.log(t_s_point) / ln_phi
    r_point = phi ** (t_s_point - 1)
    T_point = 2 * np.pi * (n - 1)
    theta_point = T_point + np.pi
    x_point = r_point * np.cos(theta_point)
    y_point = r_point * np.sin(theta_point)

    z_green_point = np.log(1 / r_point) / ln_phi

    if z_green_point >= min_z_red:
        ax1.scatter(x_point, y_point, 0, color='blue', s=50, alpha=0.8)
        ax1.scatter(x_point, y_point, z_green_point, color='green', s=50, alpha=0.8)
        ax1.plot([x_point, x_point], [y_point, y_point], [0, z_green_point],
                 color='gray', linestyle='--', alpha=0.5)
ax1.set_xlim(mid_x - max_range, mid_x + max_range)
ax1.set_ylim(mid_y - max_range, mid_y + max_range)
ax1.set_zlim(mid_z - max_range, mid_z + max_range)

ax1.view_init(elev=30, azim=-60)

# ---- 2D XY 投影 ----
ax2 = fig.add_subplot(122)
ax2.plot(x_blue, y_blue, color='blue', linewidth=2, alpha=0.8, label='Blue Curve')

# 绿色曲线的 XY 投影与蓝色重合
ax2.plot(x_blue, y_blue, color='green', linewidth=2, alpha=0.8, label='Green Curve (XY Projection)')

# 标记 Lotus 数列点（XY 投影）
for n in range(1,abs(int(z_min))+2):
    t_s_point = n
    r_point = phi ** (t_s_point - 1)
    T_point = 2 * np.pi * (n - 1)
    theta_point = T_point + np.pi
    x_point = r_point * np.cos(theta_point)
    y_point = r_point * np.sin(theta_point)

    z_green_point = np.log(1 / r_point) / ln_phi

    if z_green_point >= min_z_red:
        ax2.scatter(x_point, y_point, color='blue', s=50, alpha=0.8)
        ax2.text(x_point, y_point, f'n={lotus_sequence[n-1]}', fontsize=8,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title('XY Plane Projection')
ax2.grid(True)
ax2.set_aspect('equal')
ax2.legend()

xy_range = max(np.abs(all_x).max(), np.abs(all_y).max()) * 1.1
ax2.set_xlim(-xy_range, xy_range)
ax2.set_ylim(-xy_range, xy_range)

plt.tight_layout()


# ======================
# DXF 导出
# ======================
def export_curves_to_dxf(x_green, y_green, z_green, x_red, z_red, filename="太阴数列0.618^n螺旋r=1.dxf"):
    # 创建 DXF 文档
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

    # 绿色曲线（3D 多段线）
    green_points = [(x, y, z) for x, y, z in zip(x_green, y_green, z_green)]
    msp.add_polyline3d(green_points, dxfattribs={'color': 3, 'layer': 'GREEN_CURVE'})

    # 红色曲线（XZ 平面上的两条对称母线）
    red_points = [(x, 0, z) for x, z in zip(x_red, z_red)]
    msp.add_polyline3d(red_points, dxfattribs={'color': 1, 'layer': 'RED_CURVE'})
    red_points_neg = [(-x, 0, z) for x, z in zip(x_red, z_red)]
    msp.add_polyline3d(red_points_neg, dxfattribs={'color': 1, 'layer': 'RED_CURVE'})

    # 保存 DXF
    doc.saveas(filename)
    print(f"绿色和红色曲线已导出为 {filename}")


# 执行导出与保存图片
export_curves_to_dxf(x_blue, y_blue, z_green, x_red, z_red)
plt.savefig("blue_curve_projected_onto_funnel.png", dpi=300, transparent=True)
plt.show()
