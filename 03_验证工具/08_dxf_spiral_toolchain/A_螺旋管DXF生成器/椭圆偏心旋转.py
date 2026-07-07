import numpy as np
import matplotlib.pyplot as plt

# Parameters
k =0.5  # Adjust as needed
b_max =3# Adjust as needed
A0 = 9  # Adjust as needed
T =100 * 2 * np.pi  # Adjust as needed

p_p = 5  # Total number of ellipses
i_p = np.arange(0, p_p)  # Ellipse index
# Range for x
x = np.linspace(1, b_max, 6000)

# Plot
plt.figure(figsize=(10, 10))

for idx in i_p:
    # Calculate coordinates for ellipses
    angle = (idx / p_p) * 2 * np.pi
    X = []
    Y = []
    for xi in x:
        # Calculate the center distance
        center_distance = np.sqrt(
            (xi * np.cos(angle - ((1 - xi / b_max) * A0) + T / xi)) ** 2 +
            (xi / k * np.sin(angle - ((1 - xi / b_max) * A0) + T / xi)) ** 2
        )
        semi_major_axis = xi ** 2 / k
        semi_minor_axis = xi / k
        # Normalize coordinates
        norm_factor = np.sqrt(semi_major_axis ** 2 + semi_minor_axis ** 2)
        X.append((center_distance / norm_factor) * np.cos(angle + T / xi))
        Y.append((center_distance / norm_factor) * np.sin(angle + T / xi))

    # Plot the ellipse
    plt.plot(X, Y, label=f'Ellipse {idx}')

plt.xlabel('X')
plt.ylabel('Y')
plt.title('Concentric Ellipses with Varying Alignment')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()
