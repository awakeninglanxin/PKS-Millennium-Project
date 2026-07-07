import rhinoscriptsyntax as rs
import math

# Define the curvature function
def curvature(s):
    return s * (s + 448 / 75)

# Generate clothoid curve
def generate_clothoid(k_func, arc_length, num_points):
    """
    Generate clothoid curve points
    k_func: Curvature function
    arc_length: Range of arc length
    num_points: Number of sampling points
    """
    
    s_vals = [i * (2 * arc_length / num_points) -arc_length for i in range(num_points)]
    points = []
    theta = 0  # Initial angle
    x, y = 0, 0  # Initial position

    for i in range(1, len(s_vals)):
        ds = s_vals[i] - s_vals[i - 1]  # Arc length increment
        k = k_func(s_vals[i - 1])  # Curvature at current point
        theta += k * ds  # Update angle
        x += math.cos(theta) * ds  # Update x-coordinate
        y += math.sin(theta) * ds  # Update y-coordinate
        points.append((x, y, 0))  # Add point as (x, y, z)

    return points

# Parameters
arc_length = 5  # Arc length range
num_points = 500  # Number of sampling points

# Generate the clothoid points
clothoid_points = generate_clothoid(curvature, arc_length, num_points)

# Add the curve to Rhino
if clothoid_points:
    rs.AddCurve(clothoid_points)
