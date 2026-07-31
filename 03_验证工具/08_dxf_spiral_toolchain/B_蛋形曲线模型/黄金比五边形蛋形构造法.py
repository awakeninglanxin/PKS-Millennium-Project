import matplotlib.pyplot as plt
import numpy as np

# Constants from the diagram
phi = (1 + np.sqrt(5)) / 2  # Golden ratio (approximately 1.618)
inv_phi = 1 / phi  # Inverse golden ratio (approximately 0.618)

# Create a figure
fig, ax = plt.subplots()

# Plot the main circle with radius 2.618 (golden ratio scaled)
circle = plt.Circle((0, 0), 2.618, color='gray', fill=False, linestyle='--', linewidth=1)
ax.add_artist(circle)

# Coordinates for the pentagon's vertices (in polar form)
theta = np.linspace(0, 2 * np.pi, 6)  # Angle array for the pentagon (close the loop)
r = 1  # Radius for the pentagon (unit circle)

# Pentagon vertices based on the golden ratio and angle separation
x = r * np.cos(theta)
y = r * np.sin(theta)

# Plot the pentagon
ax.plot(x, y, 'k-', lw=2)

# Plot the inner smaller circle with radius 1
inner_circle = plt.Circle((0, 0), 1, color='red', fill=False, linestyle='-', linewidth=1)
ax.add_artist(inner_circle)

# Plot a circle with radius 0.618
smaller_circle = plt.Circle((0, 0), inv_phi, color='blue', fill=False, linestyle='-', linewidth=1)
ax.add_artist(smaller_circle)

# Set the aspect of the plot to be equal, so the circle is not distorted
ax.set_aspect('equal')

# Limit the axes to fit the whole figure
ax.set_xlim([-3, 3])
ax.set_ylim([-3, 3])

# Set grid and labels
ax.grid(True)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('Geometric Diagram: Golden Ratio and Pentagon')

plt.show()
