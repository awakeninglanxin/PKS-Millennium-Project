import rhinoscriptsyntax as rs
import math

def parametric_curve(k, d, t_start, t_end, step_size):
    points = []
    t = t_start
    while t <= t_end:
        x = k * (-1 + math.sin(t)) * math.sin(d * t) * math.pi / (t)
        y = k * (-1 + math.sin(t)) * math.cos(d * t) * math.pi / (t)
        z = k *1.5* math.cos(t)
        
        points.append([x, y, z])
        t += step_size  # Increment t by step_size
        
    return points

# Parameters
k = 1
d = 3
t_start = math.pi / 2
t_end = 2.5 * math.pi
step_size = 0.01  # Smaller step_size for denser points

# Create the parametric curve
points = parametric_curve(k, d, t_start, t_end, step_size)
rs.AddCurve(points)
