import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

a = 254/2

# Functions for 3D curve
def x(t):
    # return -2 * a * np.pi * np.cos(t) / t
 return np.zeros_like(t)

def y(t):
    return 2 * a * np.pi / t

def z(t):
    return a * np.log(t) / (np.log(0.618))

# Generate points
t_values = np.linspace(np.pi, 64*np.pi, 5000)
x_values = x(t_values)
y_values = y(t_values)
z_values = z(t_values)

# Generate central axis points
z_axis = np.linspace(min(z_values), max(z_values), 300)
x_axis = np.zeros_like(z_axis)
y_axis = np.zeros_like(z_axis)

# Plot the 3D figure
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot(x_values, y_values, z_values, label='3D Parametric Curve')
ax.plot(x_axis, y_axis, z_axis, 'r--', label='Central Axis')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('3D Parametric Curve with Central Axis')
ax.legend()
ax.set_box_aspect([1,1,1])  # Ensure equal scaling of axes

plt.show()

# Create FreeCAD document
doc = App.newDocument("3DSpiral")

# Add 3D curve to FreeCAD
points_curve = [App.Vector(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]
spline_curve = Part.BSplineCurve()
spline_curve.buildFromPoles(points_curve)
wire_curve = Part.Wire(spline_curve.toShape())
Part.show(wire_curve)

# Add central axis to FreeCAD
points_axis = [App.Vector(x, y, z) for x, y, z in zip(x_axis, y_axis, z_axis)]
spline_axis = Part.BSplineCurve()
spline_axis.buildFromPoles(points_axis)
wire_axis = Part.Wire(spline_axis.toShape())
Part.show(wire_axis)

# Export as STP files
file_name_curve = "3d_spiral_curve.stp"
file_name_axis = "central_axis.stp"
wire_curve.exportStep(file_name_curve)
wire_axis.exportStep(file_name_axis)

print(f"STP files '{file_name_curve}' and '{file_name_axis}' with 3D spiral and central axis have been created and saved.")
