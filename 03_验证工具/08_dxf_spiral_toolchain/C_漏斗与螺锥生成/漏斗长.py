# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

def create_curves_and_line():
    # Set range for y values
    min_abs_y = 1.0/18.0
    max_abs_y = 2.0
    steps = 100  # points per side
    
    # Create logarithmically spaced points
    y_positive = []
    log_min = math.log10(min_abs_y)
    log_max = math.log10(max_abs_y)
    log_step = (log_max - log_min) / (steps - 1)
    
    # Generate logarithmically spaced y values
    for i in range(steps):
        log_y = log_min + i * log_step
        y_pos = math.pow(10, log_y)
        y_positive.append(y_pos)
    
    # Create points arrays
    points_curve1 = []  # for z = -1/y (negative y)
    points_curve2 = []  # for z = 1/y (positive y)
    
    # Generate points for both curves
    for y_pos in y_positive:
        # Points for first curve (negative y)
        y_neg = -y_pos
        x = 0
        z1 = -1.0 / y_neg
        point1 = rs.CreatePoint(x, y_neg, z1)
        points_curve1.append(point1)
        
        # Points for second curve (positive y)
        z2 = 1.0 / y_pos
        point2 = rs.CreatePoint(x, y_pos, z2)
        points_curve2.append(point2)
    
    # Create hyperbolic curves
    curve1 = rs.AddInterpCurve(list(reversed(points_curve1)))
    curve2 = rs.AddInterpCurve(points_curve2)
    
    # Create line segment through specified points
    point_start = rs.CreatePoint(0, -1, 1)    # First point (y=-1, z=1)
    point_end = rs.CreatePoint(0, 0.5, 2)     # Second point (y=0.5, z=2)
    line = rs.AddLine(point_start, point_end)
    
    if curve1 and curve2 and line:
        # Change colors to distinguish curves and line
        rs.ObjectColor(curve1, (255, 0, 0))    # Red for first curve
        rs.ObjectColor(curve2, (0, 0, 255))    # Blue for second curve
        rs.ObjectColor(line, (0, 255, 0))      # Green for line
        print("Curves and line created successfully!")
    else:
        print("Failed to create one or more objects.")

# Run main function
if __name__ == "__main__":
    create_curves_and_line()