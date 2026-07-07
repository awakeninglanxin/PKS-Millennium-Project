import numpy as np
import sys
import matplotlib.pyplot as plt
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Parameters
a = 254 / 4
original_t_range = 19 * np.pi  # Original t range corresponding to 9.5 turns
new_t_range = 7*np.pi  # New t range corresponding to 3.5 turns

# Functions
def x(t):
    return -2 * a * np.pi * np.cos(t) / t

def y(t):
    return 2 * a * np.pi * np.sin(t) / t

def z(t):
    scale_factor = original_t_range / new_t_range
    return a * np.log(t) / (np.log(0.618)) * scale_factor

# Generate new t values for 3.5 turns
t_values = np.linspace(np.pi, 9 * np.pi, 10000)

# Calculate x, y, z values
x_values = x(t_values)
y_values = y(t_values)
z_values = z(t_values)

# Plotting the 3D spiral
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(x_values, y_values, z_values)
ax.axis('equal')
# Setting equal aspect ratio
ax.set_box_aspect([1,1,1])

plt.show()

# Creating a FreeCAD document
doc = App.newDocument("3DSpiral")

# Creating points and B-Spline curve
points = [App.Vector(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]
spline = Part.BSplineCurve()
spline.buildFromPoles(points)
wire = Part.Wire(spline.toShape())
Part.show(wire)

# Exporting as STP file
stp_filename = "3d_spiral_with_axis-tube1.stp"
wire.exportStep(stp_filename)

print(f"STP file has been created and saved as {stp_filename}.")
