import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib import cm

# Parameters definition
a = 5.0       # Initial radius of the spring
turns = 7    # Number of turns of the spring
points_per_turn = 200  # Points per turn
k = -0.5       # Twist factor

# Generate the spring data
t = np.linspace(0, turns * 2 * np.pi, int(turns * points_per_turn))
r = a / (t + 1)  # Radius changes linearly with t
x = r * np.cos(t + k * t)
y = r * np.sin(t + k * t)
z = np.linspace(0, 10, int(turns * points_per_turn))  # Linearly increasing z

# Define the cross-section shape (using "Hawbeak Peach" cross-section data)
theta = np.linspace(0, 2 * np.pi, 100)
r_section = np.pi * ((1/100) - (1/162)) / ((0.3 - (1/100)) * (0.3 - (1/162) * np.sin(theta) * np.exp(np.log(np.e) * theta)) + (((1/162)**3 - (1/100)**3) * (np.cos(theta))**2 * np.exp(np.log(np.e) * theta)) / 3)
x_section_base = r_section * np.cos(theta)
y_section_base = r_section * np.sin(theta)

# Function to align and project cross-sections
def align_and_project_cross_section(x_sec, y_sec, p0, tangent, scale):
    tangent /= np.linalg.norm(tangent)
    if abs(tangent[0]) < abs(tangent[2]):
        normal = np.cross(tangent, np.array([0, 0, 1]))
    else:
        normal = np.cross(tangent, np.array([1, 0, 0]))
    normal /= np.linalg.norm(normal)
    binormal = np.cross(tangent, normal)
    rotation_matrix = np.array([normal, binormal, tangent]).T
    scaled_x_sec = x_sec * scale  # Scale the section size based on z position
    scaled_y_sec = y_sec * scale  # Scale the section size based on z position
    rotated_points = np.dot(rotation_matrix, np.vstack([scaled_x_sec, scaled_y_sec, np.zeros_like(scaled_x_sec)]))
    projected_points = rotated_points + p0[:, np.newaxis]
    return projected_points

# Plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
for i in range(len(x) - 1):
    tangent = np.array([x[i+1] - x[i], y[i+1] - y[i], z[i+1] - z[i]])
    # print(i/points_per_turn)
    scale_factor = 1/(i/points_per_turn +1)   # Increase size with z
    print(scale_factor)
    p0 = np.array([x[i], y[i], z[i]])
    projected_points = align_and_project_cross_section(x_section_base, y_section_base, p0, tangent, scale_factor)
    ax.add_collection3d(Poly3DCollection([list(zip(projected_points[0], projected_points[1], projected_points[2]))], color=cm.viridis(i / len(x)), alpha=0.6))

ax.set_xlim([-5, 5])
ax.set_ylim([-5, 5])
ax.set_zlim([0, max(z)])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Spring with Scaled "Hawbeak Peach" Cross-Sections')
plt.show()
