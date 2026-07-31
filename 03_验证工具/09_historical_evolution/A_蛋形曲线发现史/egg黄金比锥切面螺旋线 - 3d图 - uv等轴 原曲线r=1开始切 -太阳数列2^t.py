import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import ezdxf
# 黄金比例常数
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值
ln2 = np.log(2)

# 参数设置
num_bands = 32  # 波段数量（同时决定红色母线的 t_red 上限）
total_points = 32 * num_bands  # 总点数
alpha = 0.01  # 控制 k 变化速率的常数（当前未使用到，可保留）
t_red_min = 1  # 红色曲线的最小t值
t_red_max = num_bands  # 红色曲线的最大t值
# 计算红色曲线的 z 最大值（t_red = num_bands 时）
z_max_red = np.log(num_bands) / ln_phi

# 计算蓝色曲线达到 z_max_red 时的 t_max
# 由 z = (t_val / (2π)) * (ln2 / ln_phi) = z_max_red
# => t_val = z_max_red * (2π * ln_phi) / ln2
t_max = z_max_red * (2 * np.pi * ln_phi) / ln2
t_min = 0
# 创建连续参数 t_total (0 到 t_max)
t_total = np.linspace(0, t_max, total_points)

# 存储螺旋线点
spiral_x, spiral_y, spiral_z = [], [], []

# 生成连续螺旋线（r=2^(-t/(2π))，z 随 t 线性增长）
for t_val in t_total:
    # 半径（连续指数衰减）
    r = 2 ** (-t_val / (2 * np.pi))
    # 高度（匹配红色曲面）
    z = (t_val / (2 * np.pi)) * (ln2 / ln_phi)
    # 坐标（围绕 z 轴的螺旋）
    x = r * np.cos(t_val)
    y = r * np.sin(t_val)

    spiral_x.append(x)
    spiral_y.append(y)
    spiral_z.append(z)

spiral_x = np.array(spiral_x)
spiral_y = np.array(spiral_y)
spiral_z = np.array(spiral_z)

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建 3D 子图
ax1 = fig.add_subplot(121, projection='3d')

# 添加红色曲线（漏斗母线，正负 x 对称）
# 计算对数空间参数
log_min = np.log(t_red_min)
log_max = np.log(t_red_max)
# 在对数空间均匀采样（确保t_min处密集）
log_space = np.linspace(log_min, log_max, 60)
# 将采样点从对数空间转换回线性空间
t_red = np.exp(log_space)

# 为红色漏斗曲线生成 3D 坐标（向量化计算）
x_funnel = 1 / t_red
y_funnel = np.zeros_like(t_red)
z_funnel = np.log(t_red) / ln_phi

ax1.plot(x_funnel, y_funnel, z_funnel,
         color='red', linewidth=2, alpha=0.7, label='Red Curve')
ax1.plot(-x_funnel,y_funnel, z_funnel,
         color='red', linewidth=2, alpha=0.7)

# 绘制蓝色螺旋线
ax1.plot(spiral_x, spiral_y, spiral_z, color='blue', linewidth=1.0, alpha=0.8, label='Blue Spiral')

# ========= ZX 平面（y=0）虚线标记：r = 2^{-n}, n = 0,1,2,... =========
# 与螺旋自然“圈数”对齐：t = 2π n 时，r = 2^{-n}，z = n * (ln2/ln_phi)
n_max = int(np.floor(t_max / (2 * np.pi)))  # 最大整圈数
for n in range(n_max + 1):
    r_n = 2 ** (-n)                       # 半径
    z_n = n * (ln2 / ln_phi)              # 高度
    x_n, y_n = r_n, 0.0                   # ZX 平面（y=0），x 取正向（t=2πn 时 cos=1）

    # 在 ZX 平面画虚线（从 z=0 到 z=z_n）
    ax1.plot([x_n, x_n], [0, 0], [0, z_n],
             linestyle='--', linewidth=1.0, color='gray', alpha=0.6)

    # 顶端加一个小圆点标注（同时也是螺旋上 t=2πn 的点）
    ax1.scatter([x_n], [0], [z_n], s=25, color='black', alpha=0.8)

    # 文本标注（避免遮挡，稍微抬高一些）
    ax1.text(x_n, 0, z_n * 1.02, f"2^(-{n}) = 1/{2 **n}",
             fontsize=8, ha='center', va='bottom')

# 设置 3D 坐标轴标签和标题
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
ax1.set_title(f'3D Logarithmic Spiral with ZX-plane Markers (z_max={z_max_red:.3f})')
ax1.grid(True)
ax1.legend()

# 设置等轴比例
max_range = max(
    np.max(spiral_x) - np.min(spiral_x),
    np.max(spiral_y) - np.min(spiral_y),
    np.max(spiral_z) - np.min(spiral_z),
) / 2.0

mid_x = (np.max(spiral_x) + np.min(spiral_x)) / 2
mid_y = (np.max(spiral_y) + np.min(spiral_y)) / 2
mid_z = (np.max(spiral_z) + np.min(spiral_z)) / 2

ax1.set_xlim(mid_x - max_range, mid_x + max_range)
ax1.set_ylim(mid_y - max_range, mid_y + max_range)
ax1.set_zlim(mid_z - max_range, mid_z + max_range)

# 设置 3D 视角
ax1.view_init(elev=30, azim=-60)

# 创建 2D XY 投影子图
ax2 = fig.add_subplot(122)

# 螺旋线的 XY 投影
ax2.plot(spiral_x, spiral_y, color='blue', linewidth=1.0, alpha=0.8, label='Spiral Projection')

# 红色曲线的 XY 投影（XZ 母线在 XY 平面投影为两条 x 轴上的曲线）
ax2.plot(x_funnel, y_funnel,
         color='red', linewidth=2, alpha=0.7, label='Red Curve Projection')
ax2.plot(-x_funnel, y_funnel,
         color='red', linewidth=2, alpha=0.7)

# 在 2D 投影上标出 r=2^{-n} 的 x 位置（可选）
for n in range(n_max + 1):
    r_n = 2 ** (-n)
    ax2.axvline(r_n, linestyle='--', linewidth=0.8, color='gray', alpha=0.4)
    ax2.text(
        r_n, 0.75,
        f"2^(-{n}) = 1/{2 **n}",   # 格式化成字符串，保留小数位更直观
        fontsize=7, rotation=90,
        ha='right', va='bottom', color='gray'
    )

# 设置 2D 坐标轴标签和标题
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_title('XY Plane Projection')
ax2.grid(True)
ax2.set_aspect('equal')
ax2.legend()

# 设置 XY 范围
xy_range = 1.1 * max(np.max(np.abs(spiral_x)), np.max(np.abs(spiral_y)))
ax2.set_xlim(-xy_range, xy_range)
ax2.set_ylim(-xy_range, xy_range)

# 创建DXF文档
doc = ezdxf.new('R2010')
msp = doc.modelspace()


# 添加红色漏斗曲线到 DXF 文件
msp.add_polyline3d(np.column_stack([x_funnel, y_funnel, z_funnel]), dxfattribs={'color': 1})  # 红色

# 添加蓝色螺旋线到DXF（3D曲线）
msp.add_polyline3d(np.column_stack([spiral_x, spiral_y, spiral_z]), dxfattribs={'color': 5})  # 蓝色


# 保存DXF文件
doc.saveas("太阳数列2^n螺旋r=1.dxf")
print('已经导出dxf')

# 调整布局与保存
plt.tight_layout()
plt.savefig("3d_log_spiral_on_funnel_surface.png", dpi=300, transparent=True)
plt.show()
