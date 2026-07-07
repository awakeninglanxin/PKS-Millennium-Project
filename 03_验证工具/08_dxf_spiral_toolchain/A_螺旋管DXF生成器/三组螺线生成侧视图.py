import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator


# Function to parse user input and validate the number of inputs
def parse_user_input(user_input):
    if user_input.strip() == "":
        # Default values if the user presses enter
        return 29, [360, 180, 90], [0, 1, 3]

    values = user_input.split()
    if len(values) != 7:
        raise ValueError("输入的参数数量不足，请确保输入7个参数：turns_num, a1, a2, a3, n1, n2, n3。")

    turns_num = float(values[0].replace('*', ''))
    a_values = [float(val.replace('*', '')) for val in values[1:4]]
    n_values = [float(val) for val in values[4:7]]

    return turns_num, a_values, n_values


# Get user input
user_input = input("请输入turns_num, a1, a2, a3, n1, n2, n3（用*或空格隔开，直接按回车键使用默认值）：")

# Parse the input
turns_num, a_values, n_values = parse_user_input(user_input)

# Parameters
bottom_radius = 2 * np.pi

# Constants
phi = (np.sqrt(5) - 1) / 2  # 黄金比例倒数


# Spiral equations for x1, y1; x2, y2; x3, y3
def spiral(t, a, n):
    x = bottom_radius * (phi ** (t / (a * np.pi / 180))) * np.cos(t) * (phi ** n)
    y = bottom_radius * (phi ** (t / (a * np.pi / 180))) * -np.sin(t) * (phi ** n)
    return x, y


# Calculate the new x (horizontal data points) and r (vertical data points)
def transform_spiral(x, y):
    h = bottom_radius / abs(x)
    h = h * ((turns_num * 2 * np.pi - 2 * np.pi) + 2 * np.pi)
    h1 = abs(np.log(turns_num) / np.log((-1 + np.sqrt(5)) / 2))  # Corrected expression
    x_new = (abs((-np.log(2 * np.pi) / np.log(phi)) + (np.log(h) / np.log(phi))) - h1) * 30 / h1
    r = np.sign(x) * np.sqrt(x ** 2 + y ** 2)  # 保持r的符号
    return x_new, r


# Sampling data points
sampling_t1_2 = [0, np.pi]  # For the first two spirals
sampling_t3 = [0, np.pi, 2 * np.pi]  # For the last spiral

# Collect points for all spirals
points_x = []
points_y = []
labels = []

# First spiral
for t in sampling_t1_2:
    x1_s, y1_s = spiral(t, a_values[0], n_values[0])
    x1_new, r1 = transform_spiral(x1_s, y1_s)
    points_x.append(x1_new)
    points_y.append(r1)
    labels.append(f"[{x1_new:.2f}, {r1:.2f}]")

# Second spiral
for t in sampling_t1_2:
    x2_s, y2_s = spiral(t, a_values[1], n_values[1])
    x2_new, r2 = transform_spiral(x2_s, y2_s)
    points_x.append(x2_new)
    points_y.append(r2)
    labels.append(f"[{x2_new:.2f}, {r2:.2f}]")

# Third spiral
for t in sampling_t3:
    x3_s, y3_s = spiral(t, a_values[2], n_values[2])
    x3_new, r3 = transform_spiral(x3_s, y3_s)
    points_x.append(x3_new)
    points_y.append(r3)
    labels.append(f"[{x3_new:.2f}, {r3:.2f}]")

# Interpolating to create smooth curves with PchipInterpolator
pchip = PchipInterpolator(points_x, points_y)

# Generate smooth data points
x_smooth = np.linspace(min(points_x), max(points_x), 500)
y_smooth = pchip(x_smooth)

# Plotting the points and connecting them with smooth lines
fig, ax = plt.subplots()

ax.plot(x_smooth, y_smooth, color='blue', linestyle='-')  # Smooth curve
ax.scatter(points_x, points_y, color='red')  # Original points

# Draw the r=0 axis as a dashed line
ax.axhline(y=0, color='gray', linestyle='--')

# Annotate each point with its coordinates
for i, label in enumerate(labels):
    ax.annotate(label, (points_x[i], points_y[i]), textcoords="offset points", xytext=(5, -5), ha='center')

# Annotate parameters a1, a2, a3, n1, n2, n3 on the plot
ax.text(0.05, 0.95, f'a1={a_values[0]}, a2={a_values[1]}, a3={a_values[2]}', transform=ax.transAxes, fontsize=10,
        verticalalignment='top')
ax.text(0.05, 0.90, f'n1={n_values[0]}, n2={n_values[1]}, n3={n_values[2]}', transform=ax.transAxes, fontsize=10,
        verticalalignment='top')
ax.text(0.05, 0.85, f'turns = {turns_num}', transform=ax.transAxes, fontsize=10, verticalalignment='top')

ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.set_title('Spiral Projection Points with Smooth Curve')
ax.axis('equal')

# Show and save the plot
plt.show()

# Save the figure as a PNG with transparent background
fig.savefig("spiral_projection_smooth.png", transparent=True)

