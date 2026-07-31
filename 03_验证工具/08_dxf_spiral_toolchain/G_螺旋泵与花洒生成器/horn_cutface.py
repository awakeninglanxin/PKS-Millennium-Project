import numpy as np
import matplotlib.pyplot as plt

# Constants
a = 100
b = 161
z = 1/3

# Theta values
theta = np.linspace(0, 2 * np.pi, 400)

# Calculate radius using the provided equation
r = np.pi * ((1/a) - (1/b)) / ((z - (1/a)) * (z - (1/b) * np.sin(theta) * np.exp(np.log(np.e) * theta)) +
                               (((1/b)**3 - (1/a)**3) * (np.cos(theta))**2 * np.exp(np.log(2) * theta)))

# Convert polar to cartesian coordinates
x = r * np.cos(theta)
y = r * np.sin(theta)

# Plotting the shape
plt.figure(figsize=(8, 8))
plt.plot(x, y, label='Hawbeak Peach Cross-section at z=1/3')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
plt.title('Cross-section of a Special "Hawbeak Peach" Shape')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.show()
