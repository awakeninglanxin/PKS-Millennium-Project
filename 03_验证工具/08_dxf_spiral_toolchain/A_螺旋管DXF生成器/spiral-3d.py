import numpy as np
import matplotlib.pyplot as plt
import ezdxf


# Functions for 3D curve
def x(t):
    return -2 * np.pi * np.cos(t) / t

def y(t):
    return 2 * np.pi * np.sin(t) / t

def z(t):
    return np.log(t)

# Generate points
t_values = np.linspace(np.pi/12, 7*np.pi, 3000)  # Avoid t=0 to prevent division by zero
x_values = x(t_values)
y_values = y(t_values)
z_values = z(t_values)

# Generate central axis points
z_axis = np.linspace(-10, 10, 300)
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
ax.axis('equal')

plt.show()
# plt.savefig("3d_spiral.png", transparent=True)  # Add this line to save the figure
# Create DXF file
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

# Add 3D polyline to DXF
points_curve = list(zip(x_values, y_values, z_values))
msp.add_polyline3d(points_curve, dxfattribs={'closed': False})

# Add central axis to DXF
points_axis = list(zip(x_axis, y_axis, z_axis))
msp.add_polyline3d(points_axis, dxfattribs={'closed': False, 'linetype': 'DASHED'})

file_name = "3d_spiral_with_axis.dxf"
# Save DXF file in the current directory
doc.saveas(file_name)

print(f"DXF file with 3D spiral and central axis has been created and saved.")
