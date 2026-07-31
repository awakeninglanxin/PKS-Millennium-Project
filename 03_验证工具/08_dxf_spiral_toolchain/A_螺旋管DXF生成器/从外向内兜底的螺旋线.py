import rhinoscriptsyntax as rs
import math

# Step and parameters
step = 360  # Number of steps
d = 3  # Scaling factor
t = [math.pi / 6 + i * (math.pi / 6 / step) for i in range(step)]  # Define the t range

# Filter out invalid t values where sqrt_term is negative
valid_indices = [i for i in range(len(t)) if math.pi / 6 <= t[i] <= 2*math.pi]  # Extend range
t_valid = [t[i] for i in valid_indices]

# Calculate x, y, z values
x = []
y = []
z = []
for ti in t_valid:
    try:
        sqrt_term = math.sqrt(1 / (2.414 - ti * math.sin(-1.618))**2 - (ti * math.cos(-1.618))**2)
        # Use ti directly in the sine and cosine functions as per the formula
        x_value = 1.95 * math.sin(d*ti) * sqrt_term * (1 + math.cos(ti))
        y_value = 1.95 * math.cos(d*ti) * sqrt_term * (1 + math.cos(ti))
        z_value = -1.347 - 1.5 * math.sin(ti)
        
        x.append(x_value)
        y.append(y_value)
        z.append(z_value)
    except ValueError:
        # Handle cases where sqrt_term calculation results in a complex value
        continue

# Convert data points to Rhino points
points = [[xi, yi, zi] for xi, yi, zi in zip(x, y, z)]

# Create 3D curve in Rhino
curve = rs.AddInterpCurve(points, 3)  # Degree 3 curve

# Adjust the view to fit the curve
rs.ZoomExtents()
