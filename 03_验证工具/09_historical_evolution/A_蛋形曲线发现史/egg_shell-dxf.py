import numpy as np
import matplotlib.pyplot as plt
import ezdxf  # 导入ezdxf库

# Constants
# a = 12.4044/1.24  # 放大倍数
# 八度节点参数集合
a=1
nodes = [
    {'k': 0.00000001, 'b': 1, 'm': 0.5, 'label': 'egg0'},
    {'k': 2 / 3, 'b': 5 / 3, 'm': 2 / 3, 'label': 'egg1'},
    {'k': 8 / 3, 'b': 10 / 3, 'm': 2 / 3, 'label': 'egg2'},
    {'k': 32 / 3, 'b': 20 / 3, 'm': 2 / 3, 'label': 'egg3'}
]

# Functions
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))

def y(t, b, k,  a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)

# Iterate through each node and generate files
for i, node in enumerate(nodes):
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

    # Create a DXF document
    dxf_doc = ezdxf.new()
    msp = dxf_doc.modelspace()

    # Plot the spiral curve in DXF as a series of line segments
    for j in range(len(x_values) - 1):
        msp.add_line(start=(x_values[j], y_values[j]), end=(x_values[j + 1], y_values[j + 1]))

    # Save the DXF document
    dxf_filename = f"{label}_m={m}.dxf"
    dxf_doc.saveas(dxf_filename)
    print(f"DXF file for {label} has been created and saved as {dxf_filename}.")
