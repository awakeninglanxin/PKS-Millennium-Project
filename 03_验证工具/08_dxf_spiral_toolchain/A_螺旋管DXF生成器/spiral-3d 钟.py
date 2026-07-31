import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys

sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD, Part


# Define the parametric equations with updated a and b values
def parametric_surface(u, v, a, b):
    expression = (b - v * np.sin(a)) ** 2 - (v * np.cos(a)) ** 2
    valid_mask = expression > 0  # Check for valid expression values
    x = np.where(valid_mask, np.sqrt(1 / expression) * np.cos(u), np.nan)
    y = np.where(valid_mask, -v * np.sin(u), np.nan)
    z = u  # 'u' is always valid in this context
    return x, y, z


# Parameters
a = 0.588  # in radians
b = 1.6
u_range = np.linspace(0, 2 * np.pi, 30)
v_range = np.linspace(-np.pi, np.pi, 15)

# Meshgrid for u and v
u, v = np.meshgrid(u_range, v_range)

# Calculate the surface points
x, y, z = parametric_surface(u, v, a, b)

# Plotting the surface
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z, cmap='viridis')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()


# Convert the points to FreeCAD format and export as STP file
def parametric_surface_freecad(u, v, a, b):
    expression = (b - v * np.sin(a)) ** 2 - (v * np.cos(a)) ** 2
    if expression <= 0:
        return None  # Ignore points where the expression is invalid
    x = np.sqrt(1 / expression) * np.cos(u)
    y = -v * np.sin(u)
    z = u
    return FreeCAD.Vector(x, y, z)


# Generate the surface points for FreeCAD
points = []
for ui in u_range:
    row = []
    for vi in v_range:
        point = parametric_surface_freecad(ui, vi, a, b)
        if point is not None:
            row.append(point)
    if row:  # Only add rows with valid points
        points.append(row)

# Ensure there are valid points before attempting to create a surface
if points:
    u_degree = 3  # Degree of the spline in U direction
    v_degree = 3  # Degree of the spline in V direction

    # Number of poles in U and V directions
    num_poles_u = len(points)
    num_poles_v = len(points[0])

    # Multiplicities should be degree + 1 at the ends, and 1 in between
    umults = [u_degree + 1] + [1] * (num_poles_u - u_degree - 1) + [u_degree + 1]
    vmults = [v_degree + 1] + [1] * (num_poles_v - v_degree - 1) + [v_degree + 1]

    # Knot vectors should be a simple sequence from 0 to num_poles - degree
    uknots = list(range(num_poles_u - u_degree))
    vknots = list(range(num_poles_v - v_degree))

    # Create a BSpline surface from the points in FreeCAD
    surface = Part.BSplineSurface()
    try:
        surface.buildFromPolesMultsKnots(points, umults, vmults, uknots, vknots, False, False, u_degree, v_degree)
    except Exception as e:
        print(f"Error building BSplineSurface: {e}")
    else:
        # Create a face from the surface
        face = surface.toShape()

        # Save the face as an STP file
        stp_filename = 'parametric_surface.stp'
        Part.export([face], stp_filename)
        print(f"STP file saved as {stp_filename}")
else:
    print("No valid points were generated for the surface.")
