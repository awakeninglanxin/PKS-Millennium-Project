import rhinoscriptsyntax as rs
import math

# Define the parameters
step = 108
k = 30
d = 1
b = 1.92
c = -3
a = 1.62
# Define the parameter range for t
t = [-math.pi + i * (2 * math.pi / step) for i in range(step)]

# Define the equation for x, y, z
x = [math.sin(d * ti) * (math.sqrt(1 / (b - ti * math.sin(a) / 2)**2 - (ti * math.cos(a) / d)**2) * -k * (1 + math.cos(ti)) + c) for ti in t]
y = [math.cos(d * ti) * (math.sqrt(1 / (b - ti * math.sin(a) / 2)**2 - (ti * math.cos(a) / 2)**2) * -k * (1 + math.cos(ti)) + c) for ti in t]
z = [k * math.sin(ti) for ti in t]

# Convert data points to Rhino points
points = [[xi, yi, zi] for xi, yi, zi in zip(x, y, z)]

# Create 3D curve in Rhino
curve = rs.AddInterpCurve(points, 3)

# Adjust the view to fit the curve
rs.ZoomExtents()
