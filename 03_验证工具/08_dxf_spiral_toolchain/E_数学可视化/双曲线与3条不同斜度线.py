# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def create_lines():
    # Hyperbola y = 1/x, parameterized using log function
    t_start = math.log(1/9)  # t = ln(x), x = 1/9
    t_end = math.log(9)      # t = ln(x), x = 9
    steps = 20  # Number of segments
    points_hyperbola = []
    
    # Generate points on the hyperbola using parameterization
    for i in range(steps + 1):
        t = t_start + (t_end - t_start) * i / steps
        x = math.exp(t)  # x = e^t
        y = math.exp(-t) # y = e^{-t} = 1/x
        points_hyperbola.append(rg.Point3d(x, y, 0))
    
    # Create the hyperbola
    if points_hyperbola:
        rs.AddCurve(points_hyperbola)
        print("Hyperbola created successfully!")
    else:
        print("Failed to create the hyperbola.")

    # Define the parameters for the three lines
    lines = [
        {"k": 2 / 3, "b": 5 / 3},   # Line 1
        {"k": 8 / 3, "b": 10 / 3},  # Line 2
        {"k": 32 / 3, "b": 20 / 3}  # Line 3
    ]

    # Create each line
    for line in lines:
        k = line["k"]
        b = line["b"]

        # Find the intersection point of the line with y = 0
        x_start = -b / k  # x = -b / k when y = 0
        start_point = rg.Point3d(x_start, 0, 0)  # Start at intersection with y = 0

        # Find the intersection point of the line with x = 1
        y_end = k * 1 + b  # y = k * 1 + b when x = 1
        end_point = rg.Point3d(1, y_end, 0)  # End at intersection with x = 1

        # Create the line
        if start_point and end_point:
            rs.AddLine(start_point, end_point)
            print("Line with k = {k}, b = {b} created successfully from y = 0 to x = 1!")
        else:
            print("Failed to create the line with k = {k}, b = {b}.")

    # Create a circle in the zx plane (y = 0), centered at the origin, with radius 9
    circle_plane = rs.PlaneFromNormal([0, 0, 0], [0, 1, 0])  # Plane with normal in y direction
    circle = rs.AddCircle(circle_plane, 9)
    if circle:
        print("Circle created successfully in the zx plane!")
    else:
        print("Failed to create the circle.")

# Run the function
create_lines()