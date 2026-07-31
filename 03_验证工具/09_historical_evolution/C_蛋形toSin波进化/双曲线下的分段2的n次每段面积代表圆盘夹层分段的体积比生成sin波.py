import numpy as np
import matplotlib.pyplot as plt

# Parameters

interval_width = 2 * np.pi  # Width of each segment (container)
areas = [0.3465735902799726, 0.2310490601866484, 0.1732867951399863, 0.13862943611198902, 0.1155245300933242, 0.09902102579427788, 0.08664339756999315, 0.07701635339554946, 0.06931471805599451, 0.06301338005090411, 0.0577622650466621, 0.05331901388922655, 0.04951051289713894, 0.04620981203732968, 0.04332169878499657]
n_points = 1000  # Number of points per segment
n_intervals = len(areas)
tilt_angle = 0.2  # Tilt angle in radians (you can adjust this value)

# Create a figure
fig, ax = plt.subplots(figsize=(14, 7))

# Function to generate wave shape for each container
def wave_shape(x, amplitude, wavelength=interval_width):
    return amplitude * np.sin(2 * np.pi * x / wavelength)

# Function to generate scatter points within a container with tilt effect
def generate_scatter_points(area, num_points, width, tilt_angle):
    x = np.linspace(0, width, num_points)
    y = wave_shape(x, area)
    # Apply tilt to x values
    x_tilted = x - np.tan(tilt_angle) * y
    return x_tilted, y

# Plot each container segment
for i, area in enumerate(areas):
    start_x = i * interval_width
    end_x = (i + 1) * interval_width
    num_points = int(n_points * (area / max(areas)))  # Scale the number of points by the area
    x, y = generate_scatter_points(area, num_points, interval_width, tilt_angle)

    # Scatter points, adding a small random jitter for visual appeal
    ax.scatter(x + start_x, y + np.random.uniform(-0.02, 0.02, len(y)), s=5,
               label=f'Segment {i + 1} (Area: {area:.2f})')

# Add labels and title
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Scatter Plot Representing Areas in Tilted Wave-shaped Containers')
ax.legend()
ax.grid(True)

# Show plot
plt.show()
