import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Set the value of 'a' to 1.618
a = 25.4 * 1.618

# Define equations for the spiral segments
def x_segment(t, factor, angle):
    return a * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (angle * np.pi / 180)) * np.cos(t) * factor

def y_segment(t, factor, angle):
    return a * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (angle * np.pi / 180)) * np.sin(t) * factor

def z_segment(t):
    return np.zeros_like(t)

# Parameters for each spiral segment
params = [
    (2 * ((np.sqrt(5) + 1) / 2), np.linspace(2 * np.pi, 4 * np.pi, 5000), 180),
    (2 * ((np.sqrt(5) + 1) / 2) ** 3, np.linspace(4 * np.pi, 6 * np.pi, 5000), 120),
    (2 * ((np.sqrt(5) + 1) / 2) ** 6, np.linspace(6 * np.pi, 8 * np.pi, 5000), 90)
]

# Create a new FreeCAD document to hold the entire spiral
doc = App.newDocument("CompleteSpiral")

# Initialize a list to hold all points for the continuous spiral
all_points = []

# Initialize matplotlib plot
plt.figure(figsize=(10, 6))

# Iterate over each segment and gather points
for i, (factor, t_values, angle) in enumerate(params):
    # Generate points for the current spiral segment
    x_values = x_segment(t_values, factor, angle)
    y_values = y_segment(t_values, factor, angle)
    z_values = z_segment(t_values)

    # Append the generated points to the list of all points
    all_points.extend(zip(x_values, y_values, z_values))

    # Plot the current segment
    plt.plot(x_values, y_values, label=f'Segment {i+1}')

# Show the origin point
plt.scatter(0, 0, color='red', label='Origin (0,0)')
plt.axhline(0, color='black', linewidth=0.5)  # x-axis
plt.axvline(0, color='black', linewidth=0.5)  # y-axis
plt.xlabel('x')
plt.ylabel('y')
plt.title('Parametric Curve of the Spiral')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')

# Display the plot
plt.show()

# Convert the list of points into FreeCAD vectors
points = [App.Vector(x, y, z) for x, y, z in all_points]

# Create the continuous BSplineCurve from the points for smooth connection with consistent curvature
spline = Part.BSplineCurve()
spline.approximate(points)  # Using approximate ensures the curve passes through all points smoothly
wire = Part.Wire(spline.toShape())
Part.show(wire)

# Add x and y axes in FreeCAD
axis_x = [App.Vector(min([p.x for p in points]), 0, 0), App.Vector(max([p.x for p in points]), 0, 0)]
axis_y = [App.Vector(0, min([p.y for p in points]), 0), App.Vector(0, max([p.y for p in points]), 0)]

wire_axis_x = Part.makePolygon(axis_x)
wire_axis_y = Part.makePolygon(axis_y)

Part.show(wire_axis_x)
Part.show(wire_axis_y)

# Combine all wires together into a single compound
compound = Part.makeCompound([wire, wire_axis_x, wire_axis_y])

# Export as STP file
stp_filename = "curvature_consistent_spiral.stp"
compound.exportStep(stp_filename)

print(f"STP file for the curvature consistent spiral has been created and saved as {stp_filename}.")
