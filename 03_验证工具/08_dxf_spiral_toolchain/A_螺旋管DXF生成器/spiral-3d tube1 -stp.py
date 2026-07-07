import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial import Polynomial
from mpl_toolkits.mplot3d import Axes3D
import sys
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Parameters
a = 254 / 2

# Functions for x, y, z
def x(t):
    return -2 * a * np.pi * np.cos(t) / t

def y(t):
    return 2 * a * np.pi * np.sin(t) / t

def z(t):
    return a * np.log(t) / (np.log(0.618))

# Generate t values and corresponding x, y, z values
t_values = np.linspace(np.pi, 20 * np.pi, 1680)
x_values = x(t_values)
y_values = y(t_values)
z_values = z(t_values)

# Fit a 4th degree polynomial for each axis
p_x = Polynomial.fit(t_values, x_values, 3)
p_y = Polynomial.fit(t_values, y_values, 3)
p_z = Polynomial.fit(t_values, z_values, 3)

# Generate smooth curve using the polynomial fits
smooth_t = np.linspace(np.pi, 20 * np.pi, 1680)
smooth_x = p_x(smooth_t)
smooth_y = p_y(smooth_t)
smooth_z = p_z(smooth_t)

# Plotting the 3D spiral and polynomial fit
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x_values, y_values, z_values, color='blue', s=1, label='Data Points')
ax.plot(smooth_x, smooth_y, smooth_z, color='red', label='4th Degree Polynomial Fit')
ax.axis('equal')
# Set equal aspect ratio
ax.set_box_aspect([1,1,1])
plt.legend()
plt.show()

# Exporting to FreeCAD STP file

# Creating a FreeCAD document
doc = App.newDocument("3DSpiral")

# Creating points and B-Spline curve
points = [App.Vector(x, y, z) for x, y, z in zip(smooth_x, smooth_y, smooth_z)]
spline = Part.BSplineCurve()
spline.buildFromPoles(points)
wire = Part.Wire(spline.toShape())
Part.show(wire)

# Exporting as STP file
stp_filename = "3d_spiral_with_axis-tube1.stp"
wire.exportStep(stp_filename)

print(f"STP file has been created and saved as {stp_filename}.")
