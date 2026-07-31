import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part

# Set the value of 'a' to 1.618
a = 25.4 * 1.618

# Define equations for the spiral segments from the image
def x_segment_1(t):
    return 2 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (180 * np.pi / 180)) * np.cos(t)

def y_segment_1(t):
    return 2 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (180 * np.pi / 180)) * (-np.sin(t))

def x_segment_2(t):
    return (3/2 - np.sqrt(5)/2) * 2 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (150 * np.pi / 180)) * np.cos(t)

def y_segment_2(t):
    return (3/2 - np.sqrt(5)/2) * 2 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (150 * np.pi / 180)) * (-np.sin(t))

def x_segment_3(t):
    return 3.2 * ((np.sqrt(5) - 1) / 2) ** (t / (120 * np.pi / 180)) * np.cos(t)

def y_segment_3(t):
    return 3.2 * ((np.sqrt(5) - 1) / 2) ** (t / (120 * np.pi / 180)) * (-np.sin(t))

def x_segment_4(t):
    return 2.64 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (90 * np.pi / 180)) * np.cos(t)

def y_segment_4(t):
    return 2.64 * np.pi * ((np.sqrt(5) - 1) / 2) ** (t / (90 * np.pi / 180)) * (-np.sin(t))

def z_segment(t):
    return np.zeros_like(t)

# Parameters for each spiral segment
params = [
    (x_segment_1, y_segment_1, np.linspace(0, 2 * np.pi, 5000)),
    (x_segment_2, y_segment_2, np.linspace(0, 2 * np.pi, 5000)),
    (x_segment_3, y_segment_3, np.linspace(2 * np.pi, 4 * np.pi, 5000)),
    (x_segment_4, y_segment_4, np.linspace(4 * np.pi, 6 * np.pi, 5000)),
]

# Create a new FreeCAD document for the spiral
doc = App.newDocument("SpiralSegments")

# Iterate over each segment, create a spline, and export it as a separate STP file
for i, (x_func, y_func, t_values) in enumerate(params):
    # Generate points for the current segment
    x_values = x_func(t_values)
    y_values = y_func(t_values)
    z_values = z_segment(t_values)

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
    stp_filename = f"curvature_consistent_spiral_segment_{i+1}.stp"
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
