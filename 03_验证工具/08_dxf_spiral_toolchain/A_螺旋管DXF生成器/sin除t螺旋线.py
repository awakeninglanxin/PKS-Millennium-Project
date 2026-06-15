import rhinoscriptsyntax as rs
import math

def create_parametric_curve():
    # Set range for parameter t
    t_min = math.pi / 9
    t_max = 9 * math.pi
    steps = 108  # Increased number of points for smoother curve
    
    # Create arrays to store points
    points = []
    
    # Calculate step size
    t_step = (t_max - t_min) / (steps - 1)
    
    # Generate points using parametric equations
    for i in range(steps):
        t = t_min + i * t_step
        
        # Calculate x and y coordinates
        x = math.sin(t) / t
        y = -math.cos(t) / t
        z = 0  # Setting z=0 for 2D curve, can be modified if 3D is needed
        
        # Create point and add to array
        point = rs.CreatePoint(x, y, z)
        points.append(point)
    
    # Create interpolated curve through points
    curve = rs.AddInterpCurve(points)
    
    if curve:
        # Change curve color (using red in this example)
        rs.ObjectColor(curve, (255, 0, 0))
        print("Parametric curve created successfully!")
    else:
        print("Failed to create curve.")
    
    return curve

# Run main function
if __name__ == "__main__":
    create_parametric_curve()