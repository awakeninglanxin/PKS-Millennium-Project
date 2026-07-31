import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
import imageio.v2 as imageio  # 使用 imageio.v2 以避免 DeprecationWarning
import os

# Function to parse a single row of user input data from the CSV
def parse_row(row):
    if len(row) < 7:
        raise ValueError("Row does not contain 7 elements.")
    turns_num = float(row[0])
    a_values = [float(val.replace('*', '')) for val in row[1:4]]
    n_values = [float(val) for val in row[4:7]]
    return turns_num, a_values, n_values

# Function to generate a plot based on the given parameters and save it as a PNG file
def generate_plot(turns_num, a_values, n_values, filename):
    bottom_radius = 2 * np.pi
    phi = (np.sqrt(5) - 1) / 2  # 黄金比例倒数

    def spiral(t, a, n):
        x = bottom_radius * (phi**(t / (a * np.pi / 180))) * np.cos(t) * (phi**n)
        y = bottom_radius * (phi**(t / (a * np.pi / 180))) * -np.sin(t) * (phi**n)
        return x, y

    def transform_spiral(x, y):
        h = bottom_radius / abs(x)
        h = h * ((turns_num * 2 * np.pi - 2 * np.pi) + 2 * np.pi)
        h1 = abs(np.log(turns_num) / np.log((-1 + np.sqrt(5))/2))
        x_new = (abs((-np.log(2 * np.pi) / np.log(phi)) + (np.log(h) / np.log(phi))) - h1) * 30 / h1
        r = np.sign(x) * np.sqrt(x**2 + y**2)
        return x_new, r

    sampling_t1_2 = [0, np.pi]
    sampling_t3 = [0, np.pi, 2 * np.pi]
    points_x = []
    points_y = []
    labels = []

    for t in sampling_t1_2:
        x1_s, y1_s = spiral(t, a_values[0], n_values[0])
        x1_new, r1 = transform_spiral(x1_s, y1_s)
        points_x.append(x1_new)
        points_y.append(r1)
        labels.append(f"[{x1_new:.2f}, {r1:.2f}]")

    for t in sampling_t1_2:
        x2_s, y2_s = spiral(t, a_values[1], n_values[1])
        x2_new, r2 = transform_spiral(x2_s, y2_s)
        points_x.append(x2_new)
        points_y.append(r2)
        labels.append(f"[{x2_new:.2f}, {r2:.2f}]")

    for t in sampling_t3:
        x3_s, y3_s = spiral(t, a_values[2], n_values[2])
        x3_new, r3 = transform_spiral(x3_s, y3_s)
        points_x.append(x3_new)
        points_y.append(r3)
        labels.append(f"[{x3_new:.2f}, {r3:.2f}]")

    # Ensure that the x values are strictly increasing for interpolation
    sorted_indices = np.argsort(points_x)
    points_x = np.array(points_x)[sorted_indices]
    points_y = np.array(points_y)[sorted_indices]

    # Remove duplicates to ensure strictly increasing sequence
    unique_indices = np.diff(points_x) > 0
    points_x = points_x[np.insert(unique_indices, 0, True)]
    points_y = points_y[np.insert(unique_indices, 0, True)]

    # Perform interpolation and plot the result
    try:
        pchip = PchipInterpolator(points_x, points_y)
        x_smooth = np.linspace(min(points_x), max(points_x), 500)
        y_smooth = pchip(x_smooth)
    except ValueError as e:
        print(f"Skipping plot generation for {filename} due to error: {e}")
        return False  # Indicate that this plot generation failed

    fig, ax = plt.subplots()
    ax.plot(x_smooth, y_smooth, color='blue', linestyle='-')
    ax.scatter(points_x, points_y, color='red')
    ax.axhline(y=0, color='gray', linestyle='--')

    for i, label in enumerate(labels):
        ax.annotate(label, (points_x[i], points_y[i]), textcoords="offset points", xytext=(5,-5), ha='center')

    ax.text(0.05, 0.95, f'a1={a_values[0]}, a2={a_values[1]}, a3={a_values[2]}', transform=ax.transAxes, fontsize=10, verticalalignment='top')
    ax.text(0.05, 0.90, f'n1={n_values[0]}, n2={n_values[1]}, n3={n_values[2]}', transform=ax.transAxes, fontsize=10, verticalalignment='top')
    ax.text(0.05, 0.85, f'turns = {turns_num}', transform=ax.transAxes, fontsize=10, verticalalignment='top')

    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_title('Spiral Projection Points with Smooth Curve')
    ax.axis('equal')

    # fig.savefig(filename, transparent=True)
    fig.savefig(filename, transparent=False)
    plt.close(fig)
    return True  # Indicate that the plot was successfully generated

# Load the data from the CSV file
data = pd.read_csv('7-data.csv', header=None)

# Directory to save images
image_dir = "images"
os.makedirs(image_dir, exist_ok=True)

# List to store the file paths of generated images
image_files = []

# Generate a plot for each row in the CSV
for i, row in data.iterrows():
    try:
        turns_num, a_values, n_values = parse_row(row)
        filename = os.path.join(image_dir, f"spiral_{i}.png")
        if generate_plot(turns_num, a_values, n_values, filename):
            image_files.append(filename)
    except Exception as e:
        print(f"Skipping row {i} due to error: {e}")

# Create a GIF from the generated images
gif_filename = "spiral_animation.gif"
with imageio.get_writer(gif_filename, mode='I', duration=0.3) as writer:
    for filename in image_files:
        image = imageio.imread(filename)
        writer.append_data(image)

print(f"GIF 动态图已保存为 {gif_filename}")
