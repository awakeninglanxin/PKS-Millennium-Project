import numpy as np
import matplotlib.pyplot as plt

# Nodes with parameters and corresponding t ranges
nodes = [
    {'k': 0.00000001, 'b': 1, 'm': 0.5, 'label': 'egg0', 't_range': (0, 2 * np.pi)},
    {'k': 2 / 3, 'b': 5 / 3, 'm': 2 / 3, 'label': 'egg1', 't_range': (2 * np.pi, 4 * np.pi)},
    {'k': 8 / 3, 'b': 10 / 3, 'm': 2 / 3, 'label': 'egg2', 't_range': (4 * np.pi, 6 * np.pi)},
    {'k': 32 / 3, 'b': 20 / 3, 'm': 2 / 3, 'label': 'egg3', 't_range': (6 * np.pi, 8 * np.pi)}
]


# Functions to calculate x(t) and y(t)
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))


def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)


# Plotting
plt.figure(figsize=(10, 6))

previous_y_end = 0  # Initialize the previous end y-value for shifting
a = 1  # Assuming 'a' is a constant for scaling, modify if needed

# Loop through each node
for node in nodes:
    t = np.linspace(node['t_range'][0], node['t_range'][1], 400)
    x_vals = x(t, node['b'], node['k'], a)
    y_vals = y(t, node['b'], node['k'], a, node['m'])

    # Shift y_vals to ensure continuity
    y_vals_shifted = y_vals + previous_y_end - y_vals[0]
    previous_y_end = y_vals_shifted[-1]  # Update the previous y-end value

    # Plot x(t) and y(t)
    plt.plot(t, x_vals, label=f"x(t) - {node['label']}", color='blue')
    plt.plot(t, y_vals_shifted, label=f"y(t) - {node['label']}", color='green')

plt.title('Plot of x(t) and y(t) for Different Nodes (Aligned)')
plt.xlabel('t')
plt.ylabel('x(t) and y(t)')
plt.legend()
plt.grid(True)
plt.show()
# 绘制参数方程曲线 x(t) vs y(t)
