import rhinoscriptsyntax as rs
import math

# Parameters from the image
a = 3
k = 0.1
step = 500
t_start = 6 * math.pi
t_end = 10.2 * math.pi

# Define parameter range
t_values = [t_start + i * ((t_end - t_start) / step) for i in range(step + 1)]

# Calculate x(t), y(t), z(t)
x = [math.cos(a * t) * (math.sin(t) - k * t) for t in t_values]
y = [math.sin(a * t) * (math.sin(t) - k * t) for t in t_values]
z = [t for t in t_values]

# Combine into 3D points
points = [[xi, yi, zi] for xi, yi, zi in zip(x, y, z)]

# Create 3D interpolated curve in Rhino
curve = rs.AddInterpCurve(points, 3)

# Zoom to fit the new curve
rs.ZoomExtents
