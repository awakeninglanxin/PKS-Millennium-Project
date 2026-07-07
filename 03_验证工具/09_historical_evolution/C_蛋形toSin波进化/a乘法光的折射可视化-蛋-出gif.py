import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import imageio

fps_n = 6
pause = 2 * fps_n

# 固定图像的大小
fixed_fig_size = (7, 9)  # 设定一个固定的图像大小

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

        y = a * (term1 + term2 + term3) + 1
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

    ax.set_title(f"m={m}, t={t}", loc='center')
    plt.axis('off')
    plt.gca().set_aspect('equal', adjustable='box')
    return fig, ax

# Define the list of m values
# m_values = [24, 36, 48, 60, 120, 180, 240, 360, 720, 840, 1260, 1680]
m_values = [24, 36, 48, 60, 120, 180, 240, 360, 720, 840, 1260, 1680]
t_values = [2, 3, 5, 7, 9, 12]

# Initialize lists for frames
frames = []

# Generate frames for each combination of m and t
for t in t_values:
    for m in m_values:
        fig, ax = generate_colored_cardioid_set(m, t)
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype='uint8').reshape(
            fig.canvas.get_width_height()[::-1] + (4,))
        frames.append(frame)

        # If it's the last m in the current group, repeat the frame to create a pause effect
        if m == m_values[-1]:
            for _ in range(pause):  # Repeat the last frame pause times to achieve a 2-second pause at 12 fps
                frames.append(frame)

        plt.close(fig)

# Save the frames as a GIF
imageio.mimsave('colored_cardioid_set.gif', frames, fps=fps_n)
