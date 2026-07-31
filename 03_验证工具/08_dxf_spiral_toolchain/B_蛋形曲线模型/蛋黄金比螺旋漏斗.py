import rhinoscriptsyntax as rs
import math

# Parameters
b = (1 + math.sqrt(5)) / 2 
degree = 100 / 3

a = degree * math.pi / 180 
d = 216 
t_min = -math.pi / 3
t_max = 2 * math.pi / 3
steps = 660

# Generate points
points = []
for i in range(steps + 1):
    t = 2 * math.pi * i / steps
    denominator = 1 / (b - t * math.sin(a))**2 - (t * math.cos(a))**2
    if denominator >= 0:  
        x = math.sin(d * t) * math.sqrt(denominator)
        y = math.cos(d * t) * math.sqrt(denominator)
        z = t
        points.append(rs.CreatePoint(x, y, z))

# Add the points to the document
rs.AddPoints(points)
