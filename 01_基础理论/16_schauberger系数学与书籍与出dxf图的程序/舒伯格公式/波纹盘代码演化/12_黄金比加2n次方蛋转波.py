import numpy as np
import matplotlib.pyplot as plt

user_num = 10

# Function to generate Fibonacci numbers starting from 5 and 8
def generate_fibonacci_sequence(length=5):
    fib = [5, 8]
    while len(fib) < length:
        fib.append(fib[-1] + fib[-2])
    return fib

# Function to generate nodes based on the corrected pattern with k and b numerators
def generate_nodes(num_nodes=user_num):
    nodes = []
    fibonacci_sequence = generate_fibonacci_sequence(length=num_nodes)

    for i in range(0, num_nodes):
        k_numerator = 2 * (2 ** i)  # k's numerator starts at 2 and increases by a factor of 4
        b_numerator = fibonacci_sequence[i]  # Using Fibonacci sequence for b_numerator
        node = {
            'k': k_numerator / 3,
            'b': b_numerator / 3,
            'm': 2 / 3,
            'label': f'egg{i}',
            't_range': (2 * (i+1) * np.pi, 2 * (i+2) * np.pi)
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

# Generate nodes
nodes = generate_nodes(num_nodes=user_num)

# Plotting x(t) and y(t) over time t
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
    plt.plot(t, x_vals, color='blue')
    plt.plot(t, y_vals_shifted, color='green')

plt.title('Plot of x(t) and y(t) for Different Nodes (Aligned)')
plt.xlabel('t')
plt.ylabel('x(t) and y(t)')
plt.grid(True)

plt.show()

# Plotting the parametric curve x(t) vs y(t)
plt.figure(figsize=(10, 6))

for node in nodes:
    t = np.linspace(node['t_range'][0], node['t_range'][1], 400)
    x_vals = x(t, node['b'], node['k'], 1)
    y_vals = y(t, node['b'], node['k'], 1, node['m'])

    plt.plot(x_vals, y_vals, label=f'Parametric Curve (x(t), y(t)) - {node["label"]}', color='purple')

plt.title('Parametric Plot of x(t) and y(t)')
plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()
