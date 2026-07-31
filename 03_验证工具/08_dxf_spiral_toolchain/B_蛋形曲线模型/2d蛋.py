import rhinoscriptsyntax as rs
import math

step=1000
# Define parameter range
t = [-math.pi / 2 + i * (2 * math.pi / step) for i in range(step)]
degree_rad = 0.588 # 100 * math.pi / (3 * 180)

# Define the equation
d = 0  # Assume d=216
phi = 5/3 #(1 + math.sqrt(5)) / 2
sqrt_term = [1 / (phi - ti * math.sin(degree_rad))**2 - (ti * math.cos(degree_rad))**2 for ti in t]

# Skip the points where the value is negative and outside the valid t range
valid_indices = [i for i in range(len(sqrt_term)) if sqrt_term[i] >= 0 and -math.pi / 2 <= t[i] <= math.pi / 2]
t_valid = [t[i] for i in valid_indices]
sqrt_term_valid = [sqrt_term[i] for i in valid_indices]

# Calculate x, y, z
x = [math.sin(d * ti) * math.sqrt(st) for ti, st in zip(t_valid, sqrt_term_valid)]
y = [math.cos(d * ti) * math.sqrt(st) for ti, st in zip(t_valid, sqrt_term_valid)]
z = [-ti for ti in t_valid]

# Convert data points to Rhino points
points = [[xi, yi, zi] for xi, yi, zi in zip(x, y, z)]

# Create 3D curve in Rhino
curve = rs.AddInterpCurve(points,3)

# Adjust the view to fit the curve
rs.ZoomExtents()

