import numpy as np
import sys
import matplotlib.pyplot as plt

sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Set the value of 'a' to 1.618
b=25.4
a = b*1.618
phi=(-1+np.sqrt(5))/2
turns=18
high=30
c=-np.log(turns)/np.log(phi)
# Define equations for the second spiral
def x2_segment(t):
    return 2 * a *phi * np.pi * 2 * np.pi / t

def y2_segment(t):
    return np.zeros_like(t)

def z2_segment(t):
    return b*high/c * (-np.log(2 * np.pi) / np.log(phi) + np.log(t) / np.log(phi))

# Define parameters for the spiral
t_values = np.linspace(2 * np.pi, turns * 2 * np.pi, 5000)

# Create a new FreeCAD document for the spiral
doc = App.newDocument("Spiral2")

# Generate points for the spiral
x_values = x2_segment(t_values)
y_values = y2_segment(t_values)
z_values = z2_segment(t_values)

# Create the spline from points
points = [App.Vector(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]
spline = Part.BSplineCurve()
spline.buildFromPoles(points)
wire = Part.Wire(spline.toShape())
Part.show(wire)

# Create the Z-axis as the construction line
z_min = np.min(z_values)
z_max = np.max(z_values)
z_axis = [App.Vector(0, 0, z_min), App.Vector(0, 0, z_max)]
wire_z_axis = Part.makePolygon(z_axis)

# Show the Z-axis as a construction line
Part.show(wire_z_axis)

# Combine all wires together into a single compound
compound = Part.makeCompound([wire, wire_z_axis])

# Export as STP file
stp_filename = f"curve_high{high}_{turns}turns.stp"
compound.exportStep(stp_filename)

print(f"STP file for Spiral 2 with Z-axis has been created and saved as {stp_filename}.")

# Plot the spiral and Z-axis using matplotlib
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the spiral
ax.plot(x_values, y_values, z_values, label='Spiral')
ax.axis('equal')
# Plot the Z-axis as a dashed line
ax.plot([0, 0], [0, 0], [z_min, z_max], 'r--', label='Z-axis')

# Set labels
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# Set the title and show the plot
ax.set_title('3D Spiral with Z-axis')
ax.legend()

plt.show()
