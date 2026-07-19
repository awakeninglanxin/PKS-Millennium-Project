import numpy as np
import matplotlib.pyplot as plt

# Define inverse Mandelbrot formula
def mandelbrot_iteration(C, max_iter=1000):
    z = 0
    for i in range(max_iter):
        try:
            z = z**2 + 1/C
        except ZeroDivisionError:
            return 0  # Immediately escapes if C is zero
        # Check for escape
        if abs(z) > 1000:
            return i
    return max_iter

# Find points with high iteration counts (potential boundary points)
def find_red_points(x_range, y_range, step_size=0.05, max_iter=1000, threshold=950):
    red_points = []
    for x in np.arange(x_range[0], x_range[1], step_size):
        for y in np.arange(y_range[0], y_range[1], step_size):
            # Skip the origin (0,0) and points very close to it
            if abs(x) < 1e-10 and abs(y) < 1e-10:
                continue
            C = complex(x, y)
            iterations = mandelbrot_iteration(C, max_iter)
            if iterations > threshold:
                red_points.append(C)
    return red_points

# Define different search regions with appropriate step sizes
regions = [
    ((-1.4, 0), (0, 1.626), 0.05),   # Region 1: fine step
    ((0, 3.5), (0, 1.626), 0.1),     # Region 2: coarse step
    ((3.5, 4.25), (0, 1.626), 0.05)  # Region 3: fine step
]

# Find points in all regions
red_points = []
for x_range, y_range, step_size in regions:
    red_points += find_red_points(x_range, y_range, step_size)

# Visualize the points
plt.figure(figsize=(10, 8))
for point in red_points:
    plt.plot(point.real, point.imag, 'ro', markersize=1)
plt.title("Points with high iteration counts in the inverse Mandelbrot set")
plt.axis('equal')
plt.xlabel("Real part of C")
plt.ylabel("Imaginary part of C")
plt.grid(True)
plt.show()