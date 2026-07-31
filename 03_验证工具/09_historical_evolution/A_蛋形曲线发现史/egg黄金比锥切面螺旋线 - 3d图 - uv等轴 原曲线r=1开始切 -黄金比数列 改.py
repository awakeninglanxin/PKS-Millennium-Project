import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (兼容部分环境)
from scipy.interpolate import CubicSpline
import ezdxf

# ======================
# 参数 & 常量设置
# ======================
phi = (np.sqrt(5) - 1) / 2  # 小黄金比例
phi_big = (np.sqrt(5) + 1) / 2  # 大黄金比例
ln_phi = np.log(phi)        # 负值

# 独立设置：红色曲线（漏斗母线/曲面）最小和最大 t_s
RED_T_MIN = 1
RED_T_MAX = 7
# n_circuits = RED_T_MAX
n_circuits = 2.5 # 螺旋线的圈数
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False
# 选择beta计算方案 (1-4)
BETA_SCHEME = 4  # 1: 指数方案, 2: 线性方案, 3: 对数方案, 4: 常数方案

# ======================
# 红色曲线（漏斗母线）& 漏斗曲面
# ======================
n_points_red = 100  # 红色曲线点数

# 使用对数映射调整采样密度（t_min处密集，t_max处稀疏）
log_min = np.log(RED_T_MIN)
log_max = np.log(RED_T_MAX)
log_space = np.linspace(log_min, log_max, n_points_red)
t_red = np.exp(log_space)

z_red = np.log(t_red) / ln_phi
x_red = 1 / t_red  # 母线在 XZ 平面上的 x

theta_funnel = np.linspace(0, 2 * np.pi, 100)
theta_grid, t_grid = np.meshgrid(theta_funnel, t_red)
x_funnel = (1 / t_grid) * np.cos(theta_grid)
y_funnel = (1 / t_grid) * np.sin(theta_grid)
z_funnel = np.log(t_grid) / ln_phi

# ======================
# 蓝色曲线生成（基于红色漏斗的半径范围）
# ======================
total_points = 3000

# 基于红色漏斗的半径范围确定蓝色曲线的半径范围
r_min_blue = 1 / RED_T_MAX  # 蓝色曲线最小半径 = 红色漏斗底部最小半径
r_max_blue = 1 / RED_T_MIN  # 蓝色曲线最大半径 = 红色漏斗顶部最大半径

# 使用对数间隔生成蓝色曲线半径（确保小半径处有更高密度）
log_r_min = np.log(r_min_blue)
log_r_max = np.log(r_max_blue)
log_r_space = np.linspace(log_r_min, log_r_max, total_points)
r_blue = np.exp(log_r_space)

# 生成角度参数 T（从 0 到 2π * n_circuits）
T = np.linspace(0, 2 * np.pi * n_circuits, total_points)

# 计算非线性变化的 beta 参数
t_normalized = T / (2 * np.pi * n_circuits)  # 归一化到[0,1]
k = 9

# 根据选择的方案计算beta
if BETA_SCHEME == 1:
    # 指数方案
    beta = 1 + 2 * (np.exp(k * t_normalized) - 1) / (np.exp(k) - 1)
    scheme_name = "指数方案"
elif BETA_SCHEME == 2:
    # 线性方案
    beta = 1 + 2 * t_normalized
    scheme_name = "线性方案"
elif BETA_SCHEME == 3:
    # 对数方案
    beta = 1 + 2 * np.log(1 + t_normalized * (np.exp(k) - 1)) / k
    scheme_name = "对数方案"
else:
    # 常数方案
    beta = np.full_like(t_normalized, 1)  # 创建与t_normalized形状相同的数组，所有元素为1
    scheme_name = "常数方案"

# 计算角度 theta
theta = T / beta

# 蓝色曲线（XY 平面）
x_blue = r_blue * np.cos(theta)
y_blue = r_blue * np.sin(theta)

# ======================
# 绿色曲线（蓝色曲线在漏斗曲面上的投影）
# ======================
r_green = np.sqrt(x_blue**2 + y_blue**2)
z_green = np.log(1 / r_green) / ln_phi

# ======================
# 作图
# ======================
fig = plt.figure(figsize=(18, 12))

# ---- 3D 主图 ----
ax1 = fig.add_subplot(221, projection='3d')

# 蓝色平面曲线（Z=0）
ax1.plot(x_blue, y_blue, np.zeros_like(x_blue), color='blue', linewidth=2, alpha=0.8)

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
ax1.set_title(f'3D View: Blue Curve Projected onto Funnel Surface ({scheme_name})')
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
ax2.set_xlabel('X')
ax2.set_ylabel('Z')
ax2.set_title('ZX Plane Projection (Side View)')
ax2.grid(True)

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
# DXF 导出函数
# ======================
def export_curves_to_dxf(x_blue, y_blue, z_green, x_red, z_red, filename="太阴数列0.618^n螺旋r=1.dxf"):
    # 创建 DXF 文档
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

    # 蓝色曲线（XY平面上的原始曲线，Z=0）
    blue_points = [(x, y, 0) for x, y in zip(x_blue, y_blue)]
    msp.add_polyline3d(blue_points, dxfattribs={'color': 5, 'layer': 'BLUE_CURVE'})  # 蓝色，DXF颜色索引5

    # 绿色曲线（3D 多段线，投影后的曲线）
    green_points = [(x, y, z) for x, y, z in zip(x_blue, y_blue, z_green)]
    msp.add_polyline3d(green_points, dxfattribs={'color': 3, 'layer': 'GREEN_CURVE'})  # 绿色，DXF颜色索引3

    # 红色曲线（XZ 平面上的两条对称母线）
    red_points = [(x, 0, z) for x, z in zip(x_red, z_red)]
    msp.add_polyline3d(red_points, dxfattribs={'color': 1, 'layer': 'RED_CURVE'})  # 红色，DXF颜色索引1
    red_points_neg = [(-x, 0, z) for x, z in zip(x_red, z_red)]
    msp.add_polyline3d(red_points_neg, dxfattribs={'color': 1, 'layer': 'RED_CURVE'})

    # 保存 DXF
    doc.saveas(filename)
    print(f"蓝色、绿色和红色曲线已导出为 {filename}")
# 执行导出与保存图片
export_filename = f"太阴数列0.618^n螺旋r=1_{scheme_name}.dxf"
export_curves_to_dxf(x_blue, y_blue, z_green, x_red, z_red, export_filename)
plt.savefig(f"blue_curve_projected_onto_funnel_{scheme_name}.png", dpi=300, transparent=True)
plt.show()

# 绘制beta随时间变化图
plt.figure(figsize=(10, 6))
plt.plot(T, beta, 'purple', linewidth=2)
plt.xlabel('Continuous Time T')
plt.ylabel('beta')
plt.title(f'Beta Parameter Variation ({scheme_name})')
plt.grid(True)
plt.savefig(f"beta_variation_{scheme_name}.png", dpi=300, transparent=True)
plt.show()