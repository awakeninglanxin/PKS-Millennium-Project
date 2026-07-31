import numpy as np
import matplotlib.pyplot as plt

# Constants
L = (2 * np.sqrt(41)) / 3  # Total height of the fish shape
A = 1 / 3  # Maximum amplitude
a=-1
b=0.5
# Refined envelope function for a sharper "fish" shape
def envelope(t, L):
    return np.abs(np.cos(np.pi * t / L)**b)

# Non-linear frequency function to create varying pitch
def non_linear_frequency(t, L):
    return 2 * np.pi * (1 + a * t / L)

# Define the sine wave function with the refined envelope and non-linear frequency
def y(t, L, A):
    k = non_linear_frequency(t, L)
    return A * envelope(t, L) * np.sin(k * t)

# Generate t values from -L/2 to L/2 for symmetry
t_values = np.linspace(-L/2, L/2, 1000)

# Calculate y values
y_values = y(t_values, L, A)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(t_values, y_values, label='Refined Fish-Shaped Sine Wave', color='blue')
plt.title('Refined Fish-Shaped Sine Wave')
plt.xlabel('t')
plt.ylabel('y(t)')
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.grid(True)
plt.legend()
plt.gca().set_aspect('equal', adjustable='box')
plt.show()
