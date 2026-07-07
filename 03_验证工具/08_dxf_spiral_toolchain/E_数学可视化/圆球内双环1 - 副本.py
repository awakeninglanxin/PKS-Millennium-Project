import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import Axes3D
from scipy.special import expit

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 设置参数
k =0.25# Schauberger锥常数
lambda_val = 1  # w场衰减系数
alpha = 0.5  # 投影压缩率
phi = np.pi / 4  # 等角螺线的恒定螺角 (45度)
beta = 0.618  # 回流角速度系数
R_c = 5  # 临界回流半径

# 创建网格
theta = np.linspace(0, 8 * np.pi, 1000)  # 增加角度范围以实现完整循环
z_vals = np.linspace(-4, 4, 500)
z_vals = z_vals[z_vals != 0]  # 避免除零错误


# 重新设计Schauberger锥 - 底部向外扩展
# 修改锥面生成逻辑，使底部向外张开
def modified_cone_radius(z, k, expansion_factor=0.8):
    """修改的锥面半径计算，底部向外扩展"""
    base_radius = k/(np.exp(abs(z) * np.log((np.sqrt(5) - 1) / 2)))
    # 在底部区域添加向外扩展
    expansion_zone = np.abs(z) < 1.2
    expansion = np.zeros_like(z)
    expansion[expansion_zone] = expansion_factor * (1.2 - np.abs(z[expansion_zone])) ** 2
    return base_radius + expansion


# 计算修改后的Schauberger锥
r_cone = modified_cone_radius(z_vals, k)
Theta, Z = np.meshgrid(theta, z_vals)
R_cone = modified_cone_radius(Z, k)

# 计算w场
w = np.exp(-lambda_val * (R_cone ** 2 + Z ** 2))
d=6
# 四维投影到三维空间
X_cone = R_cone * np.cos(d*Theta) * w ** alpha
Y_cone = R_cone * np.sin(d*Theta) * w ** alpha
Z_cone = Z * w ** alpha

# 生成等角螺线 - 修改底部行为使其向外扩展
r0 = 0.1  # 初始半径
r_spiral = r0 * np.exp(d * theta * 1 / np.tan(phi))  # 等角螺线方程，添加 d 参数

# 修改底部行为 - 在接近原点时向外扩展
# 确定底部区域（接近原点）
bottom_region = theta > 6.5 * np.pi
if np.any(bottom_region):
    # 计算扩展因子 - 在底部区域半径增加
    expand_factor = 0.5 * (theta[bottom_region] - 6.5 * np.pi) / (2 * np.pi)
    r_spiral[bottom_region] = r_spiral[bottom_region] * (1 + expand_factor)

z_spiral = k / r_spiral

# 计算螺线上的w场
w_spiral = np.exp(-lambda_val * (r_spiral ** 2 + z_spiral ** 2))

# 应用回流条件 - 使用平滑过渡
transition_width = 0.5
transition_center = R_c
transition_weight = expit((r_spiral - transition_center) / transition_width)

# 初始化修改后的角度
theta_modified = d * theta.copy()  # 使用 d 参数

for i in range(len(theta)):
    if r_spiral[i] > transition_center:
        weight = transition_weight[i]
        theta_modified[i:] = theta_modified[i:] - beta * weight * (theta_modified[i:] - theta_modified[i])

        # 平滑更新半径，确保向外扩展
        r_spiral[i:] = (1 - weight) * r_spiral[i:] + weight * (
                transition_center * np.exp(-(theta_modified[i:] - theta_modified[i]) * np.tan(phi)) +
                0.3 * (theta_modified[i:] - theta_modified[i])  # 添加向外扩展项
        )

# 重新计算z坐标
z_spiral = k / r_spiral
w_spiral = np.exp(-lambda_val * (r_spiral ** 2 + z_spiral ** 2))

# 投影螺线到三维空间
X_spiral = r_spiral * np.cos(theta_modified) * w_spiral ** alpha
Y_spiral = r_spiral * np.sin(theta_modified) * w_spiral ** alpha
Z_spiral = z_spiral * w_spiral ** alpha

# 创建图形
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# 绘制Schauberger锥面
surf = ax.plot_surface(X_cone, Y_cone, Z_cone, alpha=0.05,
                       cmap='viridis', linewidth=0, antialiased=True)

# 绘制等角螺线
ax.plot(X_spiral, Y_spiral, Z_spiral, 'r-', linewidth=2, label='等角螺线')

# 标记关键区域
ax.scatter(0, 0, 0, c='black', s=100, marker='*', label='银心')
ax.scatter(X_spiral[-1], Y_spiral[-1], Z_spiral[-1],
           c='blue', s=50, marker='o', label='银晕环')

# 设置图形属性
ax.set_xlabel('X (kpc)')
ax.set_ylabel('Y (kpc)')
ax.set_zlabel('Z (kpc)')
ax.set_title('Schauberger超双曲锥四维投影银河模型（底部向外扩展）', fontsize=14)
ax.legend()

# 添加光照效果
ls = LightSource(azdeg=315, altdeg=45)
rgb = ls.shade(Z_cone, plt.cm.viridis)

plt.tight_layout()
plt.show()

# 额外绘制二维投影视图
plt.figure(figsize=(12, 5))

# XY平面投影
plt.subplot(121)
plt.plot(X_spiral, Y_spiral, 'r-', linewidth=2)
plt.xlabel('X (kpc)')
plt.ylabel('Y (kpc)')
plt.title('银盘平面投影')
plt.grid(True)
plt.axis('equal')

# XZ平面投影
plt.subplot(122)
plt.plot(X_spiral, Z_spiral, 'r-', linewidth=2)
plt.xlabel('X (kpc)')
plt.ylabel('Z (kpc)')
plt.title('银晕侧面投影')
plt.grid(True)

plt.tight_layout()
plt.show()