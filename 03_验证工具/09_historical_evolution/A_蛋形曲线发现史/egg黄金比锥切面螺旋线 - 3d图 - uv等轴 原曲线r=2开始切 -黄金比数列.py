import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (兼容部分环境)
from scipy.interpolate import CubicSpline
import ezdxf
from scipy.optimize import root_scalar  # 确保导入root_scalar
# ======================
# 参数 & 常量设置
# ======================
phi = (np.sqrt(5) - 1) / 2  # 小黄金比例
ln_phi = np.log(phi)        # 负值
# 独立设置：红色曲线（漏斗母线/曲面）最小和最大 t_s
RED_T_MIN = 0.5  # 修改为0.5
num_terms=6

# ======================
# Lotus 数列 Z(n) = Z(n-1) + Z(n-2), Z(0)=2, Z(1)=1
# 返回从 n=1 开始的序列: [1, 3, 4, 7, 11, 18, 29, 47] （默认 7 次迭代）
# ======================
def generate_lotus_sequence(num_terms):
    Z = [2, 1]  # Z(0)=2, Z(1)=1
    for i in range(2, num_terms + 1):
        Z.append(Z[i - 1] + Z[i - 2])
    return Z[1:]  # 去掉 Z(0)=2，从 n=1 开始


# 生成 Lotus 数列（仅用于蓝色曲线）
lotus_sequence = generate_lotus_sequence(num_terms)
RED_T_MAX = lotus_sequence[-1]
max_n = max(lotus_sequence)  # 蓝色曲线自己的跨度（与红曲线无关）

# 红色曲线（漏斗）的最小和最大 z 值
min_z_red = np.log(RED_T_MIN) / ln_phi  # 修改为使用RED_T_MIN
max_z_red = np.log(RED_T_MAX) / ln_phi
print("红色曲线底部： ", max_z_red)
# （可选）最大允许半径（由公式 r = exp(min_z_red * ln_phi) 推出，此处等于 RED_T_MIN 的倒数）
r_max = 1 / RED_T_MIN

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
lotus_radii = 2*phi ** (lotus_t_s - 1)

# 三次样条（默认支持外推）；如需限制，可对 t_s 做 clip
radius_spline = CubicSpline(lotus_t_s, lotus_radii)
r_blue = radius_spline(t_s)

# 角度
beta=3   #调整绿色曲线的曲率
theta = T/beta
# 蓝色曲线（XY 平面）
x_blue = r_blue * np.cos(theta)
y_blue = r_blue * np.sin(theta)
# 绿色曲线
r_green = np.sqrt(x_blue**2 + y_blue**2)
z_green = np.log(1 / r_green) / ln_phi
# ======================
# 红色曲线（漏斗母线）& 漏斗曲面：使用独立的 RED_T_MIN 和 RED_T_MAX
# ======================
n_points = 100  # 总点数

# 使用对数映射调整采样密度（t_min处密集，t_max处稀疏）
log_min = np.log(RED_T_MIN)
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
# 作图
# ======================
fig = plt.figure(figsize=(18, 12))

# ---- 3D 主图 ----
ax1 = fig.add_subplot(221, projection='3d')

# 蓝色平面曲线（Z=0）
ax1.plot(x_blue, y_blue, 2, color='blue', linewidth=2, alpha=0.8)

# 红色母线（正负 x 对称）
ax1.plot(x_red, np.zeros_like(x_red), z_red, color='red', linewidth=2, alpha=0.7)
ax1.plot(-x_red, np.zeros_like(x_red), z_red, color='red', linewidth=2, alpha=0.7)

# 漏斗表面（线框）
ax1.plot_wireframe(x_funnel, y_funnel, z_funnel, color='red', alpha=0.1, rstride=10, cstride=10)

# 绿色曲线（投影）
ax1.plot(x_blue, y_blue, z_green, color='green', linewidth=2, alpha=0.8)

ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title('3D View: Blue Curve Projected onto Funnel Surface')
ax1.grid(True)

# 等轴比例
all_x = np.concatenate([x_blue, x_red, x_blue])
all_y = np.concatenate([y_blue, np.zeros_like(x_red), y_blue])
all_z = np.concatenate([np.zeros_like(x_blue), z_red, z_green])

x_min, x_max = np.min(all_x), np.max(all_x)
y_min, y_max = np.min(all_y), np.max(all_y)
z_min, z_max = np.min(all_z), np.max(all_z)

max_range = max(x_max - x_min, y_max - y_min, z_max - z_min) / 2.0
mid_x = (x_min + x_max) / 2
mid_y = (y_min + y_max) / 2
mid_z = (z_min + z_max) / 2
#
ax1.set_xlim(mid_x - max_range, mid_x + max_range)
ax1.set_ylim(mid_y - max_range, mid_y + max_range)
ax1.set_zlim(mid_z - max_range, mid_z + max_range)

ax1.view_init(elev=30, azim=-60)

# ---- ZX 平面投影（侧视图） ----
ax2 = fig.add_subplot(222)
ax2.plot(x_blue, z_green, color='green', linewidth=2, alpha=0.8)
# 添加红色母线
ax2.plot(x_red, z_red, color='red', linewidth=2, alpha=0.7)
ax2.plot(-x_red, z_red, color='red', linewidth=2, alpha=0.7)
# 设置ZX平面等轴比例
ax2.set_aspect('equal')

# ---- ZY 平面投影（另一个侧视图） ----
ax3 = fig.add_subplot(223)
ax3.plot(y_blue, z_green, color='green', linewidth=2, alpha=0.8)
ax3.set_xlabel('Y')
ax3.set_ylabel('Z')
ax3.set_title('ZY Plane Projection (Another Side View)')
ax3.grid(True)

# 设置ZY平面等轴比例
ax3.set_aspect('equal')

# ---- XY 平面投影 ----
ax4 = fig.add_subplot(224)
ax4.plot(x_blue, y_blue, color='blue', linewidth=2, alpha=0.8)

# 绿色曲线的 XY 投影与蓝色重合
ax4.plot(x_blue, y_blue, color='green', linewidth=2, alpha=0.8)

ax4.set_xlabel('X')
ax4.set_ylabel('Y')
ax4.set_title('XY Plane Projection (Top View)')
ax4.grid(True)

# 设置XY平面等轴比例
ax4.set_aspect('equal')

# 调整所有平面图的范围以保持等轴比例
# 计算所有平面图的最大范围
all_xz_x = np.concatenate([x_blue, x_red, -x_red])
all_xz_z = np.concatenate([z_green, z_red])
xz_range = max(np.abs(all_xz_x).max(), np.abs(all_xz_z).max()) * 1.1
ax2.set_xlim(-xz_range, xz_range)
ax2.set_ylim(-xz_range, xz_range)

all_yz_y = np.concatenate([y_blue])
all_yz_z = np.concatenate([z_green])
yz_range = max(np.abs(all_yz_y).max(), np.abs(all_yz_z).max()) * 1.1
ax3.set_xlim(-yz_range, yz_range)
ax3.set_ylim(-yz_range, yz_range)

xy_range = max(np.abs(all_x).max(), np.abs(all_y).max()) * 1.1
ax4.set_xlim(-xy_range, xy_range)
ax4.set_ylim(-xy_range, xy_range)

plt.tight_layout()

# ======================
# DXF
# ======================
def export_curves_to_dxf(x_green, y_green, z_green, x_red, z_red, filename="太阴数列0.618^n螺旋r=2.dxf"):
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