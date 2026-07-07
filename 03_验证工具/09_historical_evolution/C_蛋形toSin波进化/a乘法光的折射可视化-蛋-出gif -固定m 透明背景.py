import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import imageio
import os

# 设置 GIF 的帧率
fps_n = 3

# 固定图像的大小
fixed_fig_size = (4, 7)  # 设定一个固定的图像大小

# 创建一个文件夹用于存储 PNG 图像
output_dir = 'png_frames'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Define the function to generate the cardioid set and plot it
def generate_colored_cardioid_set(m, t):
    k = 2 / 3
    b = 5 / 3
    line_thickness = 0.1
    a = 5
    colormap_hsv = cm.hsv  # 使用新的 colormap 调用方法
    points = []

    for nos in range(m):
        angle = nos * 2 * np.pi / m
        cos_angle = np.cos(angle)
        x = a * (2 * np.sin(angle)) / (b + np.sqrt(b ** 2 - 4 * k * cos_angle))

        sqrt_b2_minus_4k = np.sqrt(b ** 2 - 4 * k)
        sqrt_b2_plus_4k = np.sqrt(b ** 2 + 4 * k)

        term1 = -(2 / 3) * (-(1 + k ** 2) * (sqrt_b2_minus_4k - sqrt_b2_plus_4k) -
                            (b * (-1 + k ** 2) + sqrt_b2_plus_4k * (1 + k ** 2)) * np.sin(np.pi)) / (
                        2 * k * np.sqrt(1 + k ** 2))
        term2 = - (b * (-1 + k ** 2) + sqrt_b2_minus_4k * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))
        term3 = ((k ** 2 - 1) * b / k + (k ** 2 + 1) * np.sqrt(b ** 2 - 4 * k * cos_angle) / k) / (
                2 * np.sqrt(1 + k ** 2))

        y = a * (term1 + term2 + term3)
        points.append((x, y))

    fig, ax = plt.subplots(figsize=fixed_fig_size)  # 使用固定的图像大小
    ax.set_aspect('equal')

    for i in range(m):
        start_point = points[i]
        end_point = points[(t * i) % m]
        x_values = [start_point[0], end_point[0]]
        y_values = [start_point[1], end_point[1]]

        color = colormap_hsv(i / m)
        ax.plot(x_values, y_values, color=color, lw=line_thickness)
    ax.set_facecolor((0, 0, 0, 0))  # 将背景颜色设置为透明
    ax.set_title(f"m={m}, t={t}", loc='center', color='black')  # 设置标题颜色为白色
    plt.axis('on')
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    return fig, ax

# Define the list of m values
m_values = [1640]

# Define t_values based on Oblong numbers sequence
# t_values = [2, 6, 12, 20, 30, 42, 56, 72, 90, 110, 132, 156, 182, 210, 240, 272, 306, 342, 380, 420, 462, 506, 552, 600, 650, 702, 756, 812, 870, 930, 992, 1056, 1122, 1190, 1260, 1332, 1406, 1482, 1560, 1640]
t_values = [992]
# Generate frames and save as PNG files
for t_idx, t in enumerate(t_values):
    for m in m_values:
        fig, ax = generate_colored_cardioid_set(m, t)
        png_filename = os.path.join(output_dir, f'frame_{t_idx:03d}.png')
        fig.savefig(png_filename, format='png', transparent=1)  # 保存为透明背景的 PNG
        # plt.axis('equal')

        plt.close(fig)

# Load all PNG files and convert them to a GIF
png_files = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.png')])
frames = [imageio.imread(png) for png in png_files]
imageio.mimsave('colored_cardioid_set—透明重叠.gif', frames, fps=fps_n)

# # 可选：删除生成的 PNG 文件以节省空间
# for png in png_files:
#     os.remove(png)
