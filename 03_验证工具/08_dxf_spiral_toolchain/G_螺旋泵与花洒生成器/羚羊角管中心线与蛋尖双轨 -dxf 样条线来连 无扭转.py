import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev
import trimesh
import ezdxf

# Parameters
b = np.log(2) / np.pi  # Spiral expansion control
c = 1  # Linear movement rate along z-axis
t_max = 5 * np.pi  # Maximum value for t, determining the spiral length
t_min = 0
d = 5  # Horizontal offset control parameter
z_v = 40
num_t = 500  # Resolution of t
amp = 0.18

# Generate time t
t = np.linspace(t_min, t_max, num_t)

# Parameter a varies from 1 to 1/3
a = np.linspace(1, 1/3, num_t)

# Calculate the spiral curve
x_spiral = amp * np.exp(b * t) * d * (np.sin(t))
y_spiral = amp * np.exp(b * t) * d * (np.cos(t))
z_spiral = amp * (np.exp(b * t) * z_v - np.exp(b * t_min) * z_v)

# Extract the two edge lines of the spiral ribbon
edge_offset = 0.2  # Offset from the center to create edges
x_edge1 = x_spiral
y_edge1 = y_spiral + edge_offset * a
x_edge2 = x_spiral
y_edge2 = y_spiral

# Create smooth splines for the two edges
tck_edge1, u_edge1 = splprep([x_edge1, y_edge1, z_spiral], s=0)
tck_edge2, u_edge2 = splprep([x_edge2, y_edge2, z_spiral], s=0)

u_fine = np.linspace(0, 1, num_t * 2)  # Increase the number of points for smoothness
edge1_spline = splev(u_fine, tck_edge1)
edge2_spline = splev(u_fine, tck_edge2)

# Create a DXF file and add the splines
dxf_doc = ezdxf.new()
modelspace = dxf_doc.modelspace()

# Add edge 1 spline
for i in range(len(edge1_spline[0]) - 1):
    modelspace.add_line(
        (edge1_spline[0][i], edge1_spline[1][i], edge1_spline[2][i]),
        (edge1_spline[0][i + 1], edge1_spline[1][i + 1], edge1_spline[2][i + 1])
    )

# Add edge 2 spline
for i in range(len(edge2_spline[0]) - 1):
    modelspace.add_line(
        (edge2_spline[0][i], edge2_spline[1][i], edge2_spline[2][i]),
        (edge2_spline[0][i + 1], edge2_spline[1][i + 1], edge2_spline[2][i + 1])
    )

# Add the central axis as a straight line through the origin
modelspace.add_line(
    (0, 0, z_spiral[0]),
    (0, 0, z_spiral[-1])
)

# Save the DXF file
dxf_doc.saveas("spiral_strip_splines.dxf")

print("DXF file 'spiral_strip_splines.dxf' has been created with two edge splines and a central axis line.")
