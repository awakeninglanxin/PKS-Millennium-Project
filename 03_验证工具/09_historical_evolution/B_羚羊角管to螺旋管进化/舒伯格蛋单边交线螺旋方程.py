import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import ezdxf
from ezdxf.math import Vec3

# 参数设置
b = 1.6
k = 2/3
d = 5

# 计算 t 的范围
t = np.linspace(-np.pi/2, 2*np.pi/3, 1000)

# 计算中间变量
alpha = np.arctan(k)
sin_alpha = np.sin(alpha)
cos_alpha = np.cos(alpha)

# 计算分母项，避免除零错误
denominator = b - t * sin_alpha
# 只处理分母不为零的点
valid_indices = np.abs(denominator) > 1e-10
t_valid = t[valid_indices]
denominator_valid = denominator[valid_indices]

# 计算平方根内的表达式
term1 = 1 / (denominator_valid**2)
term2 = (t_valid * cos_alpha)**2
inside_sqrt = term1 - term2

# 只处理非负的平方根
valid_sqrt = inside_sqrt >= 0
t_final = t_valid[valid_sqrt]
inside_sqrt_final = inside_sqrt[valid_sqrt]

# 计算半径
radius = np.sqrt(inside_sqrt_final)

# 计算 3D 坐标
x = radius * np.cos(d * t_final)
y = radius * np.sin(d * t_final)
z = -t_final

# 创建 3D 图形
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')

# 绘制 3D 曲线
ax.plot(x, y, z, color='blue', linewidth=1.5)

# 设置标签和标题
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Egg-shaped Spiral Curve (d=36)')

# 设置等轴比例
max_range = np.array([x.max()-x.min(), y.max()-y.min(), z.max()-z.min()]).max() / 2.0
mid_x = (x.max()+x.min()) * 0.5
mid_y = (y.max()+y.min()) * 0.5
mid_z = (z.max()+z.min()) * 0.5
ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
ax.set_zlim(mid_z - max_range, mid_z + max_range)

# 设置等轴比例
ax.set_box_aspect([1, 1, 1])

plt.show()

# 创建新的 DXF 文档
doc = ezdxf.new()
msp = doc.modelspace()

# 将 3D 点转换为适合 B 样条曲线的格式
points = [Vec3(float(x[i]), float(y[i]), float(z[i])) for i in range(len(x))]

# 创建内插式样条曲线 - 使用拟合点
spline = msp.add_spline(fit_points=points, degree=3, dxfattribs={'color': 1})

# 保存 DXF 文件
filename = "3d蛋形螺旋曲线.dxf"
doc.saveas(filename)
print(f"3D蛋形螺旋曲线已保存为 {filename}")