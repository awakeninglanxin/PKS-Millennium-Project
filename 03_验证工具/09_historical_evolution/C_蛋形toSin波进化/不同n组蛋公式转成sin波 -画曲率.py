import numpy as np
import matplotlib.pyplot as plt

user_num = 7

# List of 'a' values for each node
a_values = [391.0276949433876, 875.5601603212338, 1597.334575944935, 2721.0330593947865, 4621.600304941234, 7970.621111052443, 13978.387403950166]
a_values.reverse()

# List of values to subtract from x_vals
x_subtract_values = [420, 280, 210, 168, 140, 120, 105]
x_subtract_values = [x * 12 for x in x_subtract_values]

# Function to generate nodes based on the corrected pattern with k and b numerators
def generate_nodes(num_nodes=user_num):
    nodes = []
    for i in range(0, num_nodes):
        k_numerator = 2 * (2 ** i)  # k's numerator starts at 2 and increases by a factor of 4
        b_numerator = 5 * (2 ** i)  # b's numerator starts at 5 and increases by a factor of 2
        node = {
            'k': k_numerator / 3,
            'b': b_numerator / 3,
            'm': 2 / 3,
            'a': a_values[i],  # Assign a different 'a' value for each node
            'x_subtract': x_subtract_values[i],  # Assign corresponding x subtract value for each node
            'label': f'egg{i}',
            't_range': (2 * (i) * np.pi, 2 * (i + 1) * np.pi)
        }
        nodes.append(node)
    return nodes

# Functions to calculate x(t) and y(t)
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))

def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)

# Function to calculate curvature
def curvature(t, b, k, a, m):
    # First derivatives
    dx_dt = a * (2 * (np.cos(t) * (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))) - 2 * k * np.sin(t)**2 / np.sqrt(b ** 2 - 4 * k * np.cos(t)))) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))**2
    dy_dt = m * (-2 * np.sqrt(1 + k ** 2) * np.sin(t) / np.sqrt(b ** 2 - 4 * k * np.cos(t)))

    # Second derivatives
    d2x_dt2 = -a * (2 * np.sin(t) * (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))**2 + \
              a * (4 * k * np.cos(t) * np.sin(t)) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t)))**3
    d2y_dt2 = m * (-2 * np.sqrt(1 + k ** 2) * np.cos(t) / np.sqrt(b ** 2 - 4 * k * np.cos(t)))

    # Curvature formula
    curvature_values = np.abs(dx_dt * d2y_dt2 - dy_dt * d2x_dt2) / (dx_dt**2 + dy_dt**2)**(3/2)
    return curvature_values

# Generate nodes
nodes = generate_nodes(num_nodes=user_num)

# Plotting x(t) and y(t) with curvature lines
plt.figure(figsize=(10, 6))

previous_y_end = 0  # Initialize the previous end y-value for shifting

# Loop through each node
for node in nodes:
    t = np.linspace(node['t_range'][0], node['t_range'][1], 400)
    x_vals = x(t, node['b'], node['k'], node['a'])
    y_vals = y(t, node['b'], node['k'], node['a'], node['m'])

    # Calculate curvature
    curv_vals = curvature(t, node['b'], node['k'], node['a'], node['m'])

    # Shift y_vals to ensure continuity
    y_vals_shifted = y_vals + previous_y_end - y_vals[0]
    previous_y_end = y_vals_shifted[-1]  # Update the previous y-end value

    # Plot x(t), y(t), and curvature lines
    plt.plot(t, x_vals, label=f'x(t) - {node["label"]}', color='blue')
    plt.plot(t, y_vals_shifted, label=f'y(t) - {node["label"]}', color='green')
    plt.plot(t, 100*(curv_vals + previous_y_end), label=f'Curvature - {node["label"]}', color='red', linestyle='--')

plt.title('Plot of x(t), y(t), and Curvature for Different Nodes (Aligned)')
plt.xlabel('t')
plt.ylabel('x(t), y(t), and Curvature')
plt.legend()
plt.grid(True)
plt.show()
