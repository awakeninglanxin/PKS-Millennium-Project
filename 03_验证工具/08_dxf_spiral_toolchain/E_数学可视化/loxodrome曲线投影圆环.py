import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Function to create loxodrome on a sphere
def loxodrome(phi0, theta_max, n_points=1000):
    theta = np.linspace(0, theta_max, n_points)
    f =40
    phi = np.arctan(np.tan(phi0) / np.cos(theta))
    x = np.sin(phi) * np.cos(f*theta)
    y = np.sin(phi) * np.sin(f*theta)
    z = np.cos(phi)
    return x, y, z

# Function for stereographic projection
def stereographic_projection(x, y, z, R=1):
    denom = R - z
    x_proj = x * R / denom
    y_proj = y * R / denom
    return x_proj, y_proj

# Create a loxodrome
phi0 = np.radians(45)  # Initial angle (constant heading)
theta_max = np.pi  # Max latitude range (from pole to pole)
x, y, z = loxodrome(phi0, theta_max)

# Apply stereographic projection to the loxodrome
x_proj, y_proj = stereographic_projection(x, y, z)

# Create the torus surface
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, 2 * np.pi, 100)
u, v = np.meshgrid(u, v)
R = 1
r = 1
x_torus = (R + r * np.cos(v)) * np.cos(u)
y_torus = (R + r * np.cos(v)) * np.sin(u)
z_torus = r * np.sin(v)

# Plot the torus with the projected loxodrome
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')  # Create 3D plot

# Plot the torus surface
ax.plot_surface(x_torus, y_torus, z_torus, color='lightgrey', alpha=0.5)

# Plot the stereographically projected loxodrome
ax.plot(x_proj, y_proj, zs=0, color='red', lw=2)

ax.set_title('Stereographic Projection of a Loxodrome onto a Torus')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()