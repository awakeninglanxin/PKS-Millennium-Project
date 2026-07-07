import rhinoscriptsyntax as rs
import math

def evolute_curve(r, R, t_start, t_end, step_size):
    points = []
    t = t_start
    while t <= t_end:
        x = (R + r) * math.cos(t) - r * math.cos(((R + r) / r) * t)
        y = (R + r) * math.sin(t) - r * math.sin(((R + r) / r) * t)
        z = 0  
        points.append([x, y, z])
        t += step_size
    
    # Ensure the curve is closed by adding the first point at the end
    points.append(points[0])
    return points

# Parameters for the outer evolute
r = 1   
R = 4

t_start = -math.pi
t_end = math.pi
step_size = 0.01

# Generate the curve points
points = evolute_curve(r, R, t_start, t_end, step_size)

# Create the curve in Rhino
curve = rs.AddInterpCurve(points, 3)

# Check if the curve is closed, and close it if necessary
if not rs.IsCurveClosed(curve):
    rs.CloseCurve(curve)

# Define the height of the surface
height = 1  # in mm

# Create copies of the curve and move them along the Z-axis
curve_copy1 = rs.CopyObject(curve, [0, 0, height])
if not curve_copy1:
    print("Failed to copy the curve (positive Z direction).")
    exit()

curve_copy2 = rs.CopyObject(curve, [0, 0, -height])
if not curve_copy2:
    print("Failed to copy the curve (negative Z direction).")
    exit()

# Create a lofted surface between the copied curves
surface = rs.AddLoftSrf([curve_copy2, curve_copy1])
if not surface:
    print("Failed to create the lofted surface.")
    exit()

# Optionally, delete the original curves if you only want the surface
rs.DeleteObject(curve)
rs.DeleteObject(curve_copy1)

print("Surface created successfully!")
