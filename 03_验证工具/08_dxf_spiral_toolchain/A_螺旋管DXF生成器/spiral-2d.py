import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# Functions for 2D curve
def x(t):
    return -2 * np.pi * np.cos(t) / t

def y(t):
    return 2 * np.pi * np.sin(t) / t

# Generate points
t_values = np.linspace(2*np.pi/30, 8*np.pi, 3000)  # Avoid t=0 to prevent division by zero
x_values = x(t_values)
y_values = y(t_values)

# Plot the 2D figure
plt.figure(figsize=(12, 8))
plt.plot(x_values, y_values, label='2D Parametric Curve')
plt.scatter(0, 0, color='red', label='Origin (0,0)')  # Add the origin point

# Add the construction line y=2π, x from -30 to 3
plt.plot([-30, 3], [2*np.pi, 2*np.pi], 'g--', label='Construction line y=2π')  # Add the construction line

plt.xlabel('X')
plt.ylabel('Y')
plt.title('2D Parametric Curve')
plt.axis('equal')
plt.legend()

# Save the plot as PNG with transparent background
plt.savefig("2d_spiral_with_origin_and_line.png", transparent=True)  # Add this line to save the figure

plt.show()

# Create DXF file
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

# Add 2D polyline to DXF
points = list(zip(x_values, y_values))
msp.add_polyline2d(points, dxfattribs={'closed': False})

# Add origin point to DXF
msp.add_point((0, 0), dxfattribs={'color': 1})  # Color 1 is red in DXF

# Add construction line to DXF
msp.add_line((-30, 2*np.pi), (3, 2*np.pi), dxfattribs={'color': 3})  # Color 3 is green in DXF

file_name = "2d_spiral_with_origin_and_line.dxf"
# Save DXF file in the current directory
doc.saveas(file_name)

print(f"DXF file with 2D spiral, origin point, and construction line has been created and saved.")
