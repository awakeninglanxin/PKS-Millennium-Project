import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import ezdxf
from ezdxf.math import Vec3

# 参数设置
k = 3  # 可以根据需要调整
c = 1.0  # 可以根据需要调整
d = 5  # 可以根据需要调整

# 生成t值数组
t_values = np.linspace(-math.pi, math.pi, 1000)

# 初始化x, y, z数组
x_values = []
y_values = []
z_values = []

# 计算每个t对应的x, y, z值
for t in t_values:
    # 计算分母，避免除零错误
    denominator = math.cos(t) + k
    if abs(denominator) < 1e-10:  # 跳过分母接近零的点
        continue

    # 计算x, y, z坐标
    atan_sin_t = math.atan(math.sin(t))
    x = k * (c - atan_sin_t) * math.sin(d * t) / denominator
    y = k * (c - atan_sin_t) * math.cos(d * t) / denominator
    z = -k * math.atan(1 + math.cos(t))

    x_values.append(x)
    y_values.append(y)
    z_values.append(z)

# 绘制3D图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot(x_values, y_values, z_values, 'b-', linewidth=1)

# 设置等轴比例
ax.set_box_aspect([1, 1, 1])  # 设置等轴比例

# 设置坐标轴标签
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Parametric Curve')

# 显示图形
plt.show()

# 创建DXF文档
doc = ezdxf.new('R2010')  # 使用DXF R2010版本
msp = doc.modelspace()  # 获取模型空间

# 创建3D点列表
points_3d = [Vec3(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]

# 创建3阶B样条曲线
# 使用正确的方法创建B样条
if len(points_3d) >= 4:
    # 创建B样条曲线 - 使用正确的API
    spline = msp.add_spline(points_3d)

    # 设置B样条的阶数为3
    spline.dxf.degree = 3

    # 保存DXF文件
    doc.saveas('anu 蛋形曲线3d_bspline.dxf')
    print("3D B样条曲线DXF文件已保存为 'anu 蛋形曲线3d_bspline.dxf'")
else:
    print("错误：需要至少4个点来创建3阶B样条曲线")