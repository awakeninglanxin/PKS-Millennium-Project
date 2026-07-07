import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 创建图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 生成双球体结构的参数
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 50)

# 上球体参数
upper_center_z = 2.5
upper_radius = 1.5

# 下球体参数
lower_center_z = -2.5
lower_radius = 1.5

# 颈部连接参数
neck_radius = 0.3
neck_height = 1.0

# 生成上球体
x_upper = upper_radius * np.outer(np.cos(u), np.sin(v))
y_upper = upper_radius * np.outer(np.sin(u), np.sin(v))
z_upper = upper_radius * np.outer(np.ones(np.size(u)), np.cos(v)) + upper_center_z

# 生成下球体
x_lower = lower_radius * np.outer(np.cos(u), np.sin(v))
y_lower = lower_radius * np.outer(np.sin(u), np.sin(v))
z_lower = lower_radius * np.outer(np.ones(np.size(u)), np.cos(v)) + lower_center_z

# 生成颈部连接
neck_u = np.linspace(0, 2 * np.pi, 50)
neck_v = np.linspace(-neck_height/2, neck_height/2, 20)
neck_u, neck_v = np.meshgrid(neck_u, neck_v)

x_neck_upper = neck_radius * np.cos(neck_u)
y_neck_upper = neck_radius * np.sin(neck_u)
z_neck_upper = neck_v + neck_height/2 + upper_center_z - upper_radius

x_neck_lower = neck_radius * np.cos(neck_u)
y_neck_lower = neck_radius * np.sin(neck_u)
z_neck_lower = neck_v - neck_height/2 + lower_center_z + lower_radius

# 绘制上球体（红色线条）
ax.plot_wireframe(x_upper, y_upper, z_upper, color='red', alpha=0.6, linewidth=0.5)

# 绘制下球体（红色线条）
ax.plot_wireframe(x_lower, y_lower, z_lower, color='red', alpha=0.6, linewidth=0.5)

# 绘制颈部连接
ax.plot_wireframe(x_neck_upper, y_neck_upper, z_neck_upper, color='red', alpha=0.8, linewidth=0.8)
ax.plot_wireframe(x_neck_lower, y_neck_lower, z_neck_lower, color='red', alpha=0.8, linewidth=0.8)

# 设置图形属性
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('对称双球体结构')
ax.set_box_aspect([1, 1, 2])  # 保持比例

# 设置视角
ax.view_init(elev=20, azim=45)

# 隐藏坐标轴
ax.set_axis_off()

plt.tight_layout()
plt.show()