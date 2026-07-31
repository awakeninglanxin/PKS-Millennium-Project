import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
import os

user_high = 24  # 用户设定的标准高度，用于标准化投影的z轴高度
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
    top_radius = bottom_radius * (phi ** (2 * np.pi / (a_values[-1] * np.pi / 180))) * np.cos(2 * np.pi) * (
            phi ** n_values[-1])
    print(f'底圆半径{round(bottom_radius,2)}/顶圆半径{round(top_radius,2)}=', round((bottom_radius/top_radius),2))

    def spiral(t, a, n):
        x = bottom_radius * (phi ** (t / (a * np.pi / 180))) * np.cos(t) * (phi ** n)
        y = bottom_radius * (phi ** (t / (a * np.pi / 180))) * -np.sin(t) * (phi ** n)
        return x, y

    def transform_spiral(x, y):
        h2 = np.log(1 / 2) / np.log((np.sqrt(5) - 1) / 2)
        h1 = np.log(turns_num / 2) / np.log((np.sqrt(5) - 1) / 2)
        total_h=h1-h2
        z_axis = (np.log(bottom_radius / abs(2*x)) / np.log(phi)) * user_high / total_h  # 根据新的投影方程
        # Calculate z_axis based on the radial distance
        r = np.sign(x) * np.sqrt(x ** 2 + y ** 2)
        return z_axis, r  # 返回标准化后的x坐标和z轴高度

    # Generate spiral lines in the xy plane
    t_values = np.linspace(0, 2 * np.pi, 500)
    x1, y1 = spiral(t_values, a_values[0], n_values[0])
    x2, y2 = spiral(t_values, a_values[1], n_values[1])
    x3, y3 = spiral(t_values, a_values[2], n_values[2])

    # Create the figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))  # Adjust figsize to accommodate both plots

    # Plot the xy plane (top-down view) on the left axis
    ax1.plot(x1, y1)
    ax1.plot(x2, y2)
    ax1.plot(x3, y3)

    # Additional parameter curves
    x_add1 = bottom_radius * np.sin(t_values)
    y_add1 = bottom_radius * np.cos(t_values)

    x_add2 = top_radius * np.sin(t_values)
    y_add2 = top_radius * np.cos(t_values)

    ax1.plot(x_add1, y_add1, linestyle='--')
    ax1.plot(x_add2, y_add2, linestyle='--')

    ax1.set_xlabel('X-axis')
    ax1.set_ylabel('Y-axis')
    ax1.set_title('XY Plane Projection')
    ax1.axis('equal')

    # Generate the transformed spiral projection (side view) and plot on the right axis
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

    ax2.plot(x_smooth, y_smooth, color='blue', linestyle='-')
    ax2.scatter(points_x, points_y, color='red')
    ax2.axhline(y=0, color='gray', linestyle='--')

    for i, label in enumerate(labels):
        ax2.annotate(label, (points_x[i], points_y[i]), textcoords="offset points", xytext=(5, -5), ha='center')

    ax2.text(0.05, 0.95, f'a1={a_values[0]}, a2={a_values[1]}, a3={a_values[2]}', transform=ax2.transAxes, fontsize=10,
             verticalalignment='top')
    ax2.text(0.05, 0.90, f'n1={n_values[0]}, n2={n_values[1]}, n3={n_values[2]}', transform=ax2.transAxes, fontsize=10,
             verticalalignment='top')
    ax2.text(0.05, 0.85, f'turns = {turns_num},high={user_high}', transform=ax2.transAxes, fontsize=10, verticalalignment='top')

    ax2.set_xlabel('Z-axis')
    ax2.set_ylabel('X-axis')
    ax2.set_title('3 Spiral Projection Curve')
    ax2.axis('equal')

    fig.savefig(filename, transparent=True)  # Save with non-transparent background
    plt.close(fig)
    return True  # Indicate that the plot was successfully generated

# Load the data from the CSV file
data = pd.read_csv('7-data.csv', header=None)

# Directory to save images
image_dir = "3段images_pi"
os.makedirs(image_dir, exist_ok=True)

# List to store the file paths of generated images
image_files = []

# Generate a plot for each row in the CSV
for i, row in data.iterrows():
    try:
        turns_num, a_values, n_values = parse_row(row)
        # Use descriptive filenames based on row data
        filename = os.path.join(image_dir, f"{turns_num}圈_相位{a_values[0]: .0f}，{a_values[1]: .0f}，{a_values[2]: .0f}n次方：{n_values[0]: .1f}，{n_values[1]: .1f}，{n_values[2]: .1f}.png")
        if generate_plot(turns_num, a_values, n_values, filename):
            image_files.append(filename)
    except Exception as e:
        print(f"Skipping row {i} due to error: {e}")