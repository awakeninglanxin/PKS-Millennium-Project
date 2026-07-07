import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Define constants
bottom_radius = 2 * np.pi
phi = (np.sqrt(5) - 1) / 2  # Golden ratio reciprocal

# Prompt the user for input or use default values
user_input = input("Enter the parameters (default: 76 360 180 180 90 0 1 3 5): ")
if not user_input.strip():
    user_input = "76 360 180 180 90 0 1 3 5"

# Process the input
row_list = list(map(int, user_input.replace('*', '').split()))
turns = row_list[0]
a_values = row_list[1:5]
n_values = row_list[5:]

# Define the spiral function
def spiral(t, a, n):
    x = bottom_radius * (phi ** (t / (a * np.pi / 180))) * np.cos(t) * (phi ** n)
    y = bottom_radius * (phi ** (t / (a * np.pi / 180))) * -np.sin(t) * (phi ** n)
    return x, y

# Define the common t_values
t_values = np.linspace(0, 2 * np.pi, 500)

# Parameters for each spiral segment
params = [
    (a_values[0], n_values[0]),
    (a_values[1], n_values[1]),
    (a_values[2], n_values[2]),
    (a_values[3], n_values[3]),
]

# Create a new FreeCAD document for the spiral
doc = App.newDocument("SpiralSegments")

# Iterate over each segment, create a spline, and export it as a separate STP file
for i, (a, n) in enumerate(params):
    # Generate points for the current segment
    x_values, y_values = spiral(t_values, a, n)
    z_values = np.zeros_like(t_values)

    # Plot the current segment
    plt.plot(x_values, y_values, label=f'Segment {i+1}')

    # Convert the list of points into FreeCAD vectors
    points = [App.Vector(x, y, z) for x, y, z in zip(x_values, y_values, z_values)]

    # Create the continuous BSplineCurve from the points for smooth connection with consistent curvature
    spline = Part.BSplineCurve()
    spline.buildFromPoles(points)
    wire = Part.Wire(spline.toShape())
    Part.show(wire)

    # Export each segment as an STP file
    stp_filename = f"spiral_{turns}_segment_{i+1}.stp"
    wire.exportStep(stp_filename)

    print(f"STP file for Segment {i+1} of the curvature consistent spiral has been created and saved as {stp_filename}.")

# Show the origin point on the plot
plt.scatter(0, 0, color='red', label='Origin (0,0)')
plt.axhline(0, color='black', linewidth=0.5)  # x-axis
plt.axvline(0, color='black', linewidth=0.5)  # y-axis
plt.xlabel('x')
plt.ylabel('y')
plt.title('Parametric Curve of the Spiral Segments')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')

# Display the plot
plt.show()
