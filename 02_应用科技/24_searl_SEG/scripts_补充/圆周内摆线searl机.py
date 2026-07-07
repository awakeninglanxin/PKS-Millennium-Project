import rhinoscriptsyntax as rs
import math

def involute_curve(r, R, t_start, t_end, step_size):
    points = []
    t = t_start
    while t <= t_end:
        x = (R - r) * math.cos(t) + r * math.cos(((R - r) / r) * t)
        y = (R - r) * math.sin(t) - r * math.sin(((R - r) / r) * t)
        z = 0  
        points.append([x, y, z])
        t += step_size
        
    return points

# Parameters for the inner involute
r = 1   # Small circle radius
R = 12  # Large circle radius
t_start =-math.pi
t_end = math.pi
step_size = 0.01  # Finer step size for smoother curve

# Generate and draw the involute curve
points = involute_curve(r, R, t_start, t_end, step_size)
rs.AddInterpCurve(points,3)