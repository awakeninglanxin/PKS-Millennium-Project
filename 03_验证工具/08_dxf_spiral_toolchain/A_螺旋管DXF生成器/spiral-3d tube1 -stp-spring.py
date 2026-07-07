import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

a = 254

# 定义 y(t) 和 z(t) 函数
def y(t):
    return 2 * a * np.pi * np.sin(t) / t

def z(t):
    return a * np.log(t) / (np.log(0.618))

# 定义旋转曲线生成的弹簧线
def x_spring(t):
    return y(t) * np.cos(t)  # 将 y(t) 旋转
def y_spring(t):
    return y(t) * np.sin(t)  # 将 y(t) 旋转
def z_spring(t):
    return z(t)  # 保持 z(t) 方向的变化并增加 t 来形成弹簧的高度

# 生成点，使用关键 t 值生成不同节点的弹簧线
t_values = np.concatenate([
    np.linspace(np.pi, 2 * np.pi, 1000),    # 半圈
    np.linspace(2 * np.pi, 4 * np.pi, 1000), # 1圈
    np.linspace(4 * np.pi, 10 * np.pi, 1000),# 1圈
    np.linspace(10 * np.pi, 20 * np.pi, 1000) # 1圈
])
x_values = x_spring(t_values)
y_values = y_spring(t_values)
z_values = z_spring(t_values)

# 使用 matplotlib 可视化
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot(x_values, y_values, z_values, label='3D Helical Spring', color='b')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Helical Spring Around Conical Surface with Multiple Nodes')
ax.legend()
plt.show()

# 创建FreeCAD文档并导出为STP文件
doc = App.newDocument("3DSpiral")
points = [App.Vector(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]
spline = Part.BSplineCurve()
spline.buildFromPoles(points)
wire = Part.Wire(spline.toShape())
Part.show(wire)

stp_filename = "3d_spiral_conical_spring_nodes.stp"
wire.exportStep(stp_filename)

print(f"STP file has been created and saved as {stp_filename}.")
