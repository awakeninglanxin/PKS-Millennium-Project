import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# 设置参数
k = 2 / 3
b = 5 / 3

# 定义 y(t) 和 x(t) 的表达式
def generate_colored_cardioid_set(m, t):
    # 获取HSV的颜色映射
    colormap_hsv = cm.get_cmap('hsv', m)

    # 计算点的坐标
    points = []
    for nos in range(m):
        angle = nos * 2 * np.pi / m
        cos_angle = np.cos(angle)
        y = (2 * np.sin(angle)) / (b + np.sqrt(b ** 2 - 4 * k * cos_angle))

        sqrt_b2_minus_4k = np.sqrt(b ** 2 - 4 * k)
        sqrt_b2_plus_4k = np.sqrt(b ** 2 + 4 * k)

        term1 = -(2 / 3) * (-(1 + k ** 2) * (sqrt_b2_minus_4k - sqrt_b2_plus_4k) -
                            (b * (-1 + k ** 2) + sqrt_b2_plus_4k * (1 + k ** 2)) * np.sin(np.pi)) / (
                        2 * k * np.sqrt(1 + k ** 2))
        term2 = - (b * (-1 + k ** 2) + sqrt_b2_minus_4k * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))
        term3 = ((k ** 2 - 1) * b / k + (k ** 2 + 1) * np.sqrt(b ** 2 - 4 * k * cos_angle) / k) / (
                    2 * np.sqrt(1 + k ** 2))

        x = term1 + term2 + term3
        points.append((x, y))

    # 绘图
    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    # 绘制正序和反序的混合连接线
    for i in range(m):
        start_point = points[i]
        end_point = points[(t * i) % m]
        x_values = [start_point[0], end_point[0]]
        y_values = [start_point[1], end_point[1]]

        # 获取正序颜色和反序颜色
        color_forward = colormap_hsv(i / m)
        color_reverse = colormap_hsv((m - i - 1) / m)

        # 混合颜色 (这里简单地取平均值，模拟颜色叠加)
        mixed_color = [(color_forward[j] + color_reverse[j]) / 2 for j in range(3)]

        ax.plot(x_values, y_values, color=mixed_color, lw=1)

    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    plt.axis('equal')  # 设置坐标轴比例
    plt.show()

# 参数设置
m = 1680  # 你可以修改m的值
t = 7
# 你可以修改t的值

generate_colored_cardioid_set(m, t)
