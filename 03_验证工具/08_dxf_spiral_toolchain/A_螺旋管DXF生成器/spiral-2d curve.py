import numpy as np
import ezdxf

# Functions for 2D spiral curve
def x(t):
    return -2 * np.pi * np.cos(t) / t

def y(t):
    return 2 * np.pi * np.sin(t) / t

# Generate points for the spiral curve with updated t_values
t_values = np.linspace(2 * np.pi / 30, 2 * np.pi / 4, 3000)  # Updated range for t
x_values = x(t_values)
y_values = y(t_values)

# Create DXF document
doc = ezdxf.new()
msp = doc.modelspace()

# Plot the spiral curve in DXF as a series of line segments
for i in range(len(x_values) - 1):
    msp.add_line(start=(x_values[i], y_values[i]), end=(x_values[i + 1], y_values[i + 1]))

# Save the DXF document
doc.saveas("spiral_curve_only.dxf")
