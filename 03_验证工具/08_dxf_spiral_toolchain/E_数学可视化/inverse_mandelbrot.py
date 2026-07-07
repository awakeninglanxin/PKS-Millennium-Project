# -*- coding: utf-8 -*-
from scriptcontext import doc
import rhinoscriptsyntax as rs
from Rhino.Geometry import Point3d, NurbsCurve
import math
import System

def mandelbrot_iteration(c, max_iter=501):
    z = 0j
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z*z + c
    return max_iter

def create_inverse_mandelbrot_boundary():
    # Parameters
    num_points = 1000  # Number of points
    max_iter = 500
    
    points = []
    
    # Generate points with non-uniform angle distribution
    for i in range(num_points):
        # Use non-linear mapping for point concentration
        t = i / (num_points - 1.0)
        # Concentrate points near bottom tip
        angle = 2 * math.pi * (1 - (1 - t) ** 2)
        
        # Variable radius calculation
        if math.pi/2 <= angle <= 3*math.pi/2:
            # Bottom half - pointed shape
            base_radius = 2.0 * (1 + 0.5 * math.cos(angle))
            # More tapering near bottom
            if abs(angle - math.pi) < math.pi/4:
                base_radius *= 0.5 + 0.5 * abs(angle - math.pi)/(math.pi/4)
        else:
            # Top half - rounded shape
            base_radius = 2.0
        
        x = base_radius * math.cos(angle)
        y = base_radius * math.sin(angle)
        
        # Adjust tip sharpness
        if abs(angle - math.pi) < math.pi/6:
            y *= 60  # Vertical stretch near tip
            
        points.append(Point3d(x, y, 0))
    
    # Close the curve
    points.append(points[0])
    
    # Create curve
    point_array = System.Array[Point3d](points)
    degree = 3
    curve = NurbsCurve.CreateInterpolatedCurve(point_array, degree)
    
    # Add to document
    if doc:
        guid = doc.Objects.AddCurve(curve)
        if guid:
            obj = doc.Objects.Find(guid)
            obj.Attributes.ObjectColor = System.Drawing.Color.Purple
            obj.CommitChanges()
        doc.Views.Redraw()

if __name__ == "__main__":
    create_inverse_mandelbrot_boundary()