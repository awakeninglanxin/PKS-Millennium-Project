import matplotlib.colors as mcolors
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# 设置参数
# 参数设置
m = 1680  # 你可以修改m的值
t = 2  # 你可以修改t的值
# 定义 y(t) 和 x(t) 的表达式
def generate_colored_cardioid_set(m, t):
    k = 2 / 3
    b = 5 / 3
    fig_size = 5
    line_thickness = 0.1
    a=5
    colormap_hsv = cm.get_cmap('hsv', m)
    points = []

    for nos in range(m):
        angle = nos * 2 * np.pi / m
        cos_angle = np.cos(angle)
        x = a*(2 * np.sin(angle)) / (b + np.sqrt(b ** 2 - 4 * k * cos_angle))

        sqrt_b2_minus_4k = np.sqrt(b ** 2 - 4 * k)
        sqrt_b2_plus_4k = np.sqrt(b ** 2 + 4 * k)

        term1 = -(2 / 3) * (-(1 + k ** 2) * (sqrt_b2_minus_4k - sqrt_b2_plus_4k) -
                            (b * (-1 + k ** 2) + sqrt_b2_plus_4k * (1 + k ** 2)) * np.sin(np.pi)) / (
                        2 * k * np.sqrt(1 + k ** 2))
        term2 = - (b * (-1 + k ** 2) + sqrt_b2_minus_4k * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))
        term3 = ((k ** 2 - 1) * b / k + (k ** 2 + 1) * np.sqrt(b ** 2 - 4 * k * cos_angle) / k) / (
                    2 * np.sqrt(1 + k ** 2))

        y = a*(term1 + term2 + term3)+1
        points.append((x, y))

    # 绘图
    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    # 绘制连接线
    for i in range(m):
        start_point = points[i]
        end_point = points[(t * i) % m]
        x_values = [start_point[0], end_point[0]]
        y_values = [start_point[1], end_point[1]]

        color = colormap_hsv(i / m)
        ax.plot(x_values, y_values, color=color, lw=line_thickness)

    ax.set_xlim(-fig_size, fig_size)
    ax.set_ylim(-fig_size, fig_size)
    plt.axis('off')  # 设置坐标轴比例
    plt.show()




generate_colored_cardioid_set(m, t)