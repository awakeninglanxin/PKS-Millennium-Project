import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Constants
# a = (254 / 2) / 2.423  # a 是图形放大倍数
a = 12.4044/1.24  # 放大倍数
# 八度节点参数集合
nodes = [
    {'k': 0.00000001, 'b': 1, 'm': 0.5, 'label': 'egg0'},
    {'k': 2 / 3, 'b': 5 / 3, 'm': 2 / 3, 'label': 'egg1'},
    {'k': 8 / 3, 'b': 10 / 3, 'm': 2 / 3, 'label': 'egg2'},
    {'k': 32 / 3, 'b': 20 / 3, 'm': 2 / 3, 'label': 'egg3'}
]


# Functions
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))


def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)


# 创建FreeCAD文档
doc = App.newDocument("3DSpiral")

# Iterate through each node and generate files
for node in nodes:
    k = node['k']
    b = node['b']
    m = node['m']
    label = node['label']

    # Generate points
    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)

    # Plot the figure
    plt.figure(figsize=(10, 6))
    plt.plot(x_values, y_values, label=f'Parametric Curve for {label}')
    plt.scatter(0, 0, color='red', label='Origin (0,0)')  # Add the origin point
    plt.axhline(0, color='black', linewidth=0.5)  # x-axis
    plt.axvline(0, color='black', linewidth=0.5)  # y-axis
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title(f'Parametric Curve with m={m} ({label})')
    plt.legend()
    plt.axis('equal')
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig(f"{label}_m={m}.png", transparent=True)  # Save the figure
    plt.show()

    # 创建点和样条曲线
    points = [App.Vector(x, y, 0) for x, y in zip(x_values, y_values)]

    # 创建样条曲线
    spline = Part.BSplineCurve()
    spline.buildFromPoles(points)
    wire = Part.Wire(spline.toShape())

    # 闭合曲线
    closed_wire = Part.Wire([wire, Part.makeLine(points[-1], points[0])])  # 添加一条线段闭合曲线

    Part.show(closed_wire)

    # Add x and y axes in FreeCAD
    axis_x = [App.Vector(min(x_values), 0, 0), App.Vector(max(x_values), 0, 0)]
    axis_y = [App.Vector(0, min(y_values), 0), App.Vector(0, max(y_values), 0)]

    wire_axis_x = Part.makePolygon(axis_x)
    wire_axis_y = Part.makePolygon(axis_y)

    Part.show(wire_axis_x)
    Part.show(wire_axis_y)

    # Combine all wires together into a single compound
    compound = Part.makeCompound([closed_wire, wire_axis_x, wire_axis_y])

    # 导出为STP文件
    stp_filename = f"{label}_m={m}.stp"
    compound.exportStep(stp_filename)

    print(f"STP file with polyline for {label} and origin point has been created and saved as {stp_filename}.")
