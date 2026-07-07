import rhinoscriptsyntax as rs
import math

phi=(math.sqrt(5)-1)/2

def create_parametric_curve2():
    # Set range for parameter t
    t_min = math.pi  # Starting from pi
    t_max = 29*2 * math.pi  # Ending at 3*pi
    steps = 100  # Using 6000 steps as per the given settings
    
    # Create arrays to store points - FIXED: Initialize as empty lists
    points1 = []
    points2 = []
    
    # Calculate step size
    t_step = (t_max - t_min) / (steps - 1)
    
    # Generate points using parametric equations
    for i in range(steps):
        t = t_min + i * t_step
        
        # Calculate x, y, and z coordinates based on the given parametric equations
        x1 = (-2 * math.pi) / t
        x2 = (2 * math.pi) / t
        y = 0  # y is always 0
        z = math.log(t) / math.log(phi)  # For the z equation
        
        # Create point and add to array
        point1 = rs.CreatePoint(x1, y, z)
        point2 = rs.CreatePoint(x2, y, z)
        points1.append(point1)
        points2.append(point2)
    
    # Create interpolated curve through points
    curve1 = rs.AddInterpCurve(points1, 3)
    curve2 = rs.AddInterpCurve(points2, 3)
    
    if curve1 and curve2:  # FIXED: Check both curves
        # Change curve color to red
        rs.ObjectColor(curve1, (255, 0, 0))
        rs.ObjectColor(curve2, (255, 0, 0))
        print("Parametric curves created successfully!")
    else:
        print("Failed to create curves.")
    
    return curve1, curve2 

def create_parametric_curve():
    # Set range for parameter t
    t_min = math.pi  # Starting from pi
    t_max = 29 * 2 * math.pi  # Ending at 3*pi
    steps = 1000  # Using 6000 steps as per the given settings
    
    # Create arrays to store points
    points1 = []
    points2 = []
    
    # Calculate step size
    t_step = (t_max - t_min) / (steps - 1)
    
    # Generate points using parametric equations
    for i in range(steps):
        t = t_min + i * t_step
        
        # Calculate x, y, and z coordinates based on the given parametric equations
        x = (-2 * math.pi * math.cos(t)) / t
        y = (2 * math.pi * math.sin(t)) / t
        z = math.log(t) / math.log(phi)  # For the z equation
        
        # Create point and add to array
        point1 = rs.CreatePoint(x, y, z)
        point2 = rs.CreatePoint(x, 0, z)
        points1.append(point1)
        points2.append(point2)
    
    # Create interpolated curve through points
    curve1 = rs.AddInterpCurve(points1, 3)
    curve2 = rs.AddInterpCurve(points2, 3)
    if curve1 or curve2:
        # Change curve color to blue
        rs.ObjectColor(curve1, (0, 0, 255))
        rs.ObjectColor(curve2, (0, 125, 0))
        print("Parametric curve created successfully!")
    else:
        print("Failed to create curve.")
    
    return curve1, curve2 

# Run main function
if __name__ == "__main__":
    create_parametric_curve()  # This will create a blue curve
    create_parametric_curve2()  # This will create red curves