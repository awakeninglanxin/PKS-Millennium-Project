import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import fsolve

# 参数设置
phi = (np.sqrt(5) - 1) / 2
ln_phi = np.log(phi)  # 负值
k = 1 / (2 * np.pi * ln_phi)  # 负值
D = np.sqrt(1 + k ** 2)  # 常数


# 修正b_n计算（使用加号）
def calculate_b_n(n):
    return (np.log(n) + 1 / (2 * np.pi * n)) / ln_phi


# 计算z_n（A_n点的z坐标）
def calculate_z_n(n):
    return np.log(n) / ln_phi


# 修正2D曲线方程（使用负指数）
def solve_v(u, n):
    """计算给定u和n时的v值"""
    exponent = -(u / (np.pi * D) + 1 / (np.pi * n))
    term = (1 / n ** 2) * np.exp(exponent) - (u ** 2) / (D ** 2)
    if term >= 0:
        return np.sqrt(term)
    else:
        return np.nan


# 优化u范围求解
def find_u_range(n):
    """找到给定n时u的有效范围"""

    # 定义方程：f(u) = (1/n²)exp(-(u/(πD)+1/(πn))) - u²/D² = 0
    def equation(u):
        exponent = -(u / (np.pi * D) + 1 / (np.pi * n))
        return (1 / n ** 2) * np.exp(exponent) - (u ** 2) / (D ** 2)

    # 使用更稳健的求解方法
    u_min = fsolve(equation, -3)[0]
    u_max = fsolve(equation, 3)[0]
    return min(u_min, u_max), max(u_min, u_max)


# 生成节点数据
def generate_nodes(n_values):
    nodes = []
    for n in n_values:
        b_n = calculate_b_n(n)
        z_n = calculate_z_n(n)
        nodes.append({
            'n': n,
            'b_n': b_n,
            'z_n': z_n,
            'label': f'n={n}'
        })
    return nodes


# 设置参数
num_curves = 29  # 曲线数量
n_values = range(1, num_curves + 1)  # n从1到29

# 生成节点
nodes = generate_nodes(n_values)

# 创建图像和子图
fig = plt.figure(figsize=(18, 8))

# 创建3D子图
ax1 = fig.add_subplot(121, projection='3d')

# 创建颜色映射
colors = plt.cm.viridis(np.linspace(0, 1, num_curves))

# 绘制每条曲线
for i, node in enumerate(nodes):
    n = node['n']
    z_n = node['z_n']
    color = colors[i]

    # 获取u的范围
    u_min, u_max = find_u_range(n)
    u_values = np.linspace(u_min, u_max, 500)

    # 计算v值
    v_positive = np.array([solve_v(u, n) for u in u_values])
    v_negative = -v_positive

    # 创建z值数组
    z_values = np.full_like(u_values, z_n)

    # 绘制曲线
    ax1.plot(u_values, v_positive, z_values, color=color, alpha=0.8)
    ax1.plot(u_values, v_negative, z_values, color=color, alpha=0.8)

    # 标记原点
    ax1.scatter(0, 0, z_n, color=color, s=30)
    ax1.text(0, 0, z_n, f"n={n}", fontsize=8)

# 添加z轴曲线（红色曲线）
t_values = np.linspace(0.5, num_curves, 100)
x_red = 1 / t_values
z_red = np.log(t_values) / ln_phi

# 绘制红色曲线（正负两条）
ax1.plot(x_red, np.zeros_like(z_red), z_red,
         color='red', linewidth=2, alpha=0.7)
ax1.plot(-x_red, np.zeros_like(z_red), z_red,
         color='red', linewidth=2, alpha=0.7)

# 添加标签和网格
ax1.set_xlabel('u')
ax1.set_ylabel('v')
ax1.set_zlabel('z')
ax1.set_title(f'3D Edge Curves for n=1 to {num_curves} with Red Curves')
ax1.grid(True)

# 设置u和v轴等比例
u_min, u_max = ax1.get_xlim()
v_min, v_max = ax1.get_ylim()
max_range = max(u_max - u_min, v_max - v_min) / 2.0
u_center = (u_min + u_max) / 2
v_center = (v_min + v_max) / 2
ax1.set_xlim(u_center - max_range, u_center + max_range)
ax1.set_ylim(v_center - max_range, v_center + max_range)

# 设置视角
ax1.view_init(elev=30, azim=-60)

# 创建2D UV投影子图
ax2 = fig.add_subplot(122)

# 绘制每条曲线在UV平面上的投影
for i, node in enumerate(nodes):
    n = node['n']
    color = colors[i]

    # 获取u的范围
    u_min, u_max = find_u_range(n)
    u_values = np.linspace(u_min, u_max, 500)

    # 计算v值
    v_positive = np.array([solve_v(u, n) for u in u_values])
    v_negative = -v_positive

    # 绘制曲线在UV平面上的投影
    ax2.plot(u_values, v_positive, color=color, alpha=0.8)
    ax2.plot(u_values, v_negative, color=color, alpha=0.8)

    # 标记原点
    ax2.scatter(0, 0, color=color, s=30)
    ax2.text(0, 0, f"n={n}", fontsize=8)

# 添加红色曲线在UV平面上的投影
# 在UV平面中，红色曲线投影为v=0的线段
ax2.plot(x_red, np.zeros_like(x_red),
         color='red', linewidth=2, alpha=0.7)
ax2.plot(-x_red, np.zeros_like(-x_red),
         color='red', linewidth=2, alpha=0.7)

# 设置2D坐标轴标签和标题
ax2.set_xlabel('u')
ax2.set_ylabel('v')
ax2.set_title(f'UV Plane Projection (n=1 to {num_curves})')
ax2.grid(True)
ax2.set_aspect('equal')  # 保持纵横比相等

# 设置相同的UV范围，便于比较
uv_range = max(max_range, max(np.abs(u_values)), max(np.abs(v_positive))) * 1.1
ax2.set_xlim(-uv_range, uv_range)
ax2.set_ylim(-uv_range, uv_range)

# 添加图例
ax2.legend(['Curve Projection', 'Red Curve Projection'], loc='upper right')

# 调整布局
plt.tight_layout()

# 保存并显示图像
plt.savefig(f"3d_edge_curves_n={num_curves}_with_projection.png", dpi=300, transparent=True)
plt.show()