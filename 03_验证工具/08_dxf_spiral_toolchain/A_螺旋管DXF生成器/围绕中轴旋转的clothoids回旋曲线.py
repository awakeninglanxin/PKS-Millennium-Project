import rhinoscriptsyntax as rs
import math

# Define the curvature function
def curvature(s):
    return s * (s + 448 / 75)

# Generate clothoid curve
def generate_clothoid(k_func, arc_length, num_points):
    s_vals = [i * (2 * arc_length / num_points) - arc_length for i in range(num_points)]
    points = []
    theta = 0
    x, y = 0, 0

    for i in range(1, len(s_vals)):
        ds = s_vals[i] - s_vals[i - 1]
        k = k_func(s_vals[i - 1])
        theta += k * ds
        x += math.cos(theta) * ds
        y += math.sin(theta) * ds
        points.append((x, y, 0))

    return points, s_vals

# Parameters
arc_length = 5  # Arc length range
num_points = 1500  # Number of sampling points

# Generate the clothoid points
clothoid_points, s_values = generate_clothoid(curvature, arc_length, num_points)

# Find the points corresponding to s = 0 and s = -448/75 with tolerance of 0.1
point_s_0 = None
point_s_neg_448_75_tolerance = None

target_s = -448 / 75  # s = -448/75
tolerance = 0.1  # Tolerance range

# Loop to find the points within the tolerance
for i, s in enumerate(s_values):
    if abs(s - 0) <= 1e-6:  # Find the point where s = 0
        point_s_0 = clothoid_points[i]
    if abs(s - target_s) <= tolerance:  # Find the point where s = -448/75 within tolerance
        point_s_neg_448_75_tolerance = clothoid_points[i]

# Add points to Rhino
if point_s_0:
    rs.AddPoint(point_s_0)
if point_s_neg_448_75_tolerance:
    rs.AddPoint(point_s_neg_448_75_tolerance)
