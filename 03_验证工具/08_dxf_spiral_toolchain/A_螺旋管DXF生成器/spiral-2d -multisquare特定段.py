import numpy as np
import matplotlib.pyplot as plt
user_num=24
# user_num2=(np.sqrt(5)+1)/2
user_num2=1
# Functions for 2D spiral curve
def x(t):
    return -2 * np.pi * np.cos(t) / t

def y(t):
    return 2 * np.pi * np.sin(t) / t

# Generate points for the spiral curve
t_values = np.linspace(2*np.pi/user_num, 2*np.pi/user_num2, 3000)  # Avoid t=0 to prevent division by zero
x_values = x(t_values)
y_values = y(t_values)

# Function to generate regular polygon vertices
def generate_polygon_vertices(sides, radius):
    angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    vertices = np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))

    # Rotate so that one vertex is on the negative x-axis
    rotation_angle = np.pi
    # print('rotation_angle：',rotation_angle)
    rotation_matrix = np.array([[np.cos(rotation_angle), -np.sin(rotation_angle)],
                                [np.sin(rotation_angle), np.cos(rotation_angle)]])
    vertices = vertices.dot(rotation_matrix)
    return vertices

# Generate the plot
plt.figure(figsize=(20, 20))

# Plot the spiral curve as background with red color
plt.plot(x_values, y_values, color='red', label='2D Parametric Curve')
plt.plot(-x_values, -y_values, color='red', label='2D Parametric Curve')

# Function to plot regular polygons
def plot_polygon(sides, radius, ax, line_width=1.5):
    vertices = generate_polygon_vertices(sides, radius)
    # Draw the polygon with specified line width
    polygon = plt.Polygon(vertices, fill=None, edgecolor='blue', linewidth=line_width)
    ax.add_patch(polygon)
    circle0 = plt.Circle((0, 0), 1, linestyle='--', fill=False, edgecolor='gray', linewidth=line_width)
    ax.add_patch(circle0)
    # Draw the circumcircle with specified line width
    circle = plt.Circle((0, 0), radius, linestyle='--', fill=False, edgecolor='gray', linewidth=line_width)
    ax.add_patch(circle)
    circle2 = plt.Circle((0, 0), 2 * np.pi, linestyle='--', fill=False, edgecolor='red', linewidth=1.5)
    ax.add_patch(circle2)

# Plot polygons from 3 sides to user_num sides with custom line width
plot_polygon(2, 2, plt.gca(), line_width=1.2)
for sides in range(3, user_num+1):
    plot_polygon(sides, sides, plt.gca(), line_width=1.2)  # Set the desired line width here

# Add the construction line y=2π, x from -user_num to 3 with custom line width
plt.plot([-user_num, 0], [2*np.pi, 2*np.pi], 'g--', linewidth=1.0, label='Construction line y=2π')  # Set line width
plt.plot([-0, user_num], [-2*np.pi, -2*np.pi], 'g--', linewidth=1.0, label='Construction line y=-2π')  # Set line width

# Additional plot settings
plt.xlabel('X')
plt.ylabel('Y')
plt.title('2D Parametric Curve with Regular Polygons Scaled by π')
plt.axis('equal')
plt.legend()

# Save the plot as PNG with transparent background
plt.savefig("2d_spiral_with_polygons_scaled_by_pi.png", transparent=True)
plt.show()
