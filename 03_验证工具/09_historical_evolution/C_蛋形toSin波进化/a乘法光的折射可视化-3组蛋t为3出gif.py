import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import imageio

fixed_fig_size = (7, 9)  # 设定一个固定的图像大小
# Function to generate the cardioid set and plot it
def generate_colored_cardioid_set(m, t, k, b, a, ax, colormap_hsv):
    line_thickness = 0.1
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

        y = a * ((term1 + term2 + term3) + 4/ 5)
        points.append((x, y))

    for i in range(m):
        start_point = points[i]
        end_point = points[(t * i) % m]
        x_values = [start_point[0], end_point[0]]
        y_values = [start_point[1], end_point[1]]

        color = colormap_hsv(i / m)
        ax.plot(x_values, y_values, color=color, lw=line_thickness)

    ax.set_title(f"m={m}, t={t:.2f}, k={k:.2f}, b={b:.2f}, a={a:.2f}", loc='center')
    ax.axis('off')

    ax.set_aspect('equal', adjustable='box')


# Define the parameters
k_values = [2 / 3, 8 / 3, 32 / 3]
b_values = [5 / 3, 10 / 3, 20 / 3]
a_values = [5, 5, 5]
# m_values = [12, 24, 36, 48, 60, 120, 180, 240, 360, 720, 840, 1260, 1680]
m_values = [180]
t_values = [3]

# Initialize lists for frames
frames = []

# Generate frames for each combination of k, b, a, m, and t
for t in t_values:
    for m in m_values:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        colormap_hsv = cm.get_cmap('hsv', m)

        generate_colored_cardioid_set(m, t, k_values[0], b_values[0], a_values[0], ax1, colormap_hsv)
        generate_colored_cardioid_set(m, t, k_values[1], b_values[1], a_values[1], ax2, colormap_hsv)
        generate_colored_cardioid_set(m, t, k_values[2], b_values[2], a_values[2], ax3, colormap_hsv)

        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype='uint8').reshape(
            fig.canvas.get_width_height()[::-1] + (4,))
        frames.append(frame)
        plt.close(fig)
    plt.subplots(figsize=fixed_fig_size)
# Save the frames as a GIF
imageio.mimsave('colored_cardioid_set3组.gif', frames, fps=10)
