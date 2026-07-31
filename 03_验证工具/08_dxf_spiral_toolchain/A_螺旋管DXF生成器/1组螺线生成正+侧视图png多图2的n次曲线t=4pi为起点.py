import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
import os
import pandas as pd


# Function to parse a single row of user input data from the CSV
def parse_row(row):
    if len(row) < 9:
        raise ValueError("Row does not contain 9 elements.")
    turns_num = float(row[0])
    a_values = [float(val.replace('*', '')) for val in row[1:5]]
    n_values = [float(val) for val in row[5:9]]
    return turns_num, a_values, n_values


# Function to generate a plot based on the given parameters and save it as a PNG file
def generate_plot(turns_num, filename):
    bottom_radius = 2 * np.pi
    phi = (np.sqrt(5) - 1) / 2  # 黄金比例倒数

    def spiral(t):
        x = bottom_radius * 2 ** (-t / (360 * np.pi / 180)) * np.cos(t)
        y = bottom_radius * 2 ** (-t / (360 * np.pi / 180)) * -np.sin(t)
        return x, y

    def transform_spiral(x, y):
        user_high = 30  # 用户设定的标准高度，用于标准化投影的z轴高度

        try:
            time = bottom_radius / abs(x) * (turns_num * np.pi)
            h1 = abs(np.log(turns_num) / np.log(phi))

            # 调整x_new的计算，确保其在4π到29*2π之间
            x_new = (bottom_radius*abs(-np.log(4 * np.pi) / np.log(phi) + np.log(time) / np.log(phi)/2) - h1) * user_high / h1

            r = np.sign(x) * np.sqrt(x ** 2 + y ** 2)
        except Exception as e:
            print(f"Error in transform_spiral function: {e}")
            return None, None
        return x_new, r

    t_values = np.linspace(0, 8 * np.pi, 1000)

    try:
        x, y = spiral(t_values)
    except Exception as e:
        print(f"Error generating spiral: {e}")
        return False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 绘制左图（XY 平面投影）
    ax1.plot(x, y, label='Spiral')
    ax1.set_xlabel('X-axis')
    ax1.set_ylabel('Y-axis')
    ax1.set_title('XY Plane Projection')
    ax1.legend()
    ax1.axis('equal')

    # 绘制右图（投影后的曲线）
    sampling_t = [0, np.pi, 2 * np.pi]
    points_x = []
    points_y = []
    labels = []

    for t in sampling_t:
        x_s, y_s = spiral(t)
        x_new, r = transform_spiral(x_s, y_s)
        if x_new is not None and r is not None:
            points_x.append(x_new)
            points_y.append(r)
            labels.append(f"[{x_new:.2f}, {r:.2f}]")

    if len(points_x) < 2:
        print(f"Not enough points for interpolation in {filename}")
        return False

    sorted_indices = np.argsort(points_x)
    points_x = np.array(points_x)[sorted_indices]
    points_y = np.array(points_y)[sorted_indices]

    unique_indices = np.diff(points_x) > 0
    points_x = points_x[np.insert(unique_indices, 0, True)]
    points_y = points_y[np.insert(unique_indices, 0, True)]

    try:
        pchip = PchipInterpolator(points_x, points_y)
        x_smooth = np.linspace(min(points_x), max(points_x), 500)
        y_smooth = pchip(x_smooth)
    except ValueError as e:
        print(f"Skipping plot generation for {filename} due to interpolation error: {e}")
        return False

    ax2.plot(x_smooth, y_smooth, color='blue', linestyle='-')
    ax2.scatter(points_x, points_y, color='red')
    ax2.axhline(y=0, color='gray', linestyle='--')

    # Only add labels to the right plot (ax2)
    for i, label in enumerate(labels):
        if i < len(points_x) and i < len(points_y):
            ax2.annotate(label, (points_x[i], points_y[i]), textcoords="offset points", xytext=(5, -5), ha='center')

    ax2.text(0.05, 0.95, f'Spiral projection', transform=ax2.transAxes, fontsize=10, verticalalignment='top')
    ax2.set_xlabel('Z-axis')
    ax2.set_ylabel('X-axis')
    ax2.set_title('Spiral Projection Curve')
    ax2.axis('equal')

    fig.savefig(filename, transparent=True)
    plt.close(fig)
    return True


# Load the data from the Excel file
data = pd.read_excel('9-data.xlsx', header=None)

# Directory to save images
image_dir = "images_pi"
os.makedirs(image_dir, exist_ok=True)

# Generate a plot for each row in the CSV
for i, row in data.iterrows():
    try:
        turns_num, _, _ = parse_row(row)
        # Use descriptive filenames based on row data
        filename = os.path.join(image_dir, f"{turns_num}_spiral.png")
        if generate_plot(turns_num, filename):
            print(f"Saved plot to {filename}")
    except Exception as e:
        print(f"Skipping row {i} due to error: {e}")
