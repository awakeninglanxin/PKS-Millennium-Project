import rhinoscriptsyntax as rs
import math

def parametric_curve(a, b, d, t_start, t_end, step_size):
    points = []
    t = t_start
    while t <= t_end:
        # Calculate the value inside the square root
        term = 1 / (b - t * math.sin(a) / 2)**2 - (t * math.cos(a) / 2)**2
        
        # Only calculate the square root if the term is non-negative
        if term < 0:
            t += step_size  # Skip this iteration
            continue
        
        sqrt_term = math.sqrt(term)
        
        # Modify the equations according to the formulas from the image
        x = -(3 + 2 * math.cos(t)) * math.sin(3 * d * t) * sqrt_term
        y = -(3 + 2 * math.cos(t)) * math.cos(3 * d * t) * sqrt_term
        z = c * math.sin(t)
        
        points.append([x, y, z])
        t += step_size  # Increment t by step_size
        
    return points

# Parameters
a = -0.6  # Adjust the angle a as needed
b = 5 / 3  # Adjust the b parameter
d = 3
c = 3.6
t_start = -math.pi
t_end = math.pi
number_of_steps = 1680  # Set the number of steps

# Calculate step size based on the number of steps
step_size = (t_end - t_start) / number_of_steps

# Create the parametric curve
points = parametric_curve(a, b, d, t_start, t_end, step_size)
rs.AddCurve(points)
