import numpy as np
from scipy.integrate import quad

# Function to generate nodes with 'a' value set to 1
def generate_nodes(num_nodes=6):
    nodes = []
    for i in range(0, num_nodes):
        k_numerator = 2 * (2 ** i)  # k's numerator starts at 2 and increases by a factor of 4
        b_numerator = 5 * (2 ** i)  # b's numerator starts at 5 and increases by a factor of 2
        node = {
            'k': k_numerator / 3,
            'b': b_numerator / 3,
            'm': 2 / 3,
            'a': 1,  # Set 'a' value to 1 for initial area calculation
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

# Derivative of y(t) with respect to t
def dy_dt(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)

# Function to calculate area under the parametric curve for each node
def calculate_area(node):
    t1, t2 = node['t_range']
    b, k, a, m = node['b'], node['k'], node['a'], node['m']

    def integrand(t):
        return x(t, b, k, a) * dy_dt(t, b, k, a, m)

    # Perform the integration over the given t_range
    area_positive, _ = quad(integrand, (t2 - t1)/4, (t2 - t1)/2)
    area_negative, _ = quad(integrand, t1, (t2 - t1)/4)
    # Calculate the total area by summing the absolute values
    total_area = (abs(area_positive) + abs(area_negative)) * 2
    return total_area

# Generate nodes
nodes = generate_nodes(num_nodes=7)

# Calculate areas for each node with a = 1
areas = [calculate_area(node) for node in nodes]

# Desired target list
# target_list = [n for n in range(2, 8)]
target_list = [420, 280, 210, 168, 140, 120, 105]

# Calculate corresponding a_value for each area to match the target list
a_values = [target / area for target, area in zip(target_list, areas)]
print('a_values:',a_values)
# Print the areas and corresponding a_values
for i, (area, a_value) in enumerate(zip(areas, a_values)):
    print(f"Area for node {i} with a=1 (t_range: {nodes[i]['t_range']}): {area:.9f}")
    print(f"Corresponding a_value to match target {target_list[i]}: {a_value:.9f}")

# Apply the calculated a_values to get the final adjusted areas
adjusted_areas = [area * a_value for area, a_value in zip(areas, a_values)]

# Print the adjusted areas
for i, adjusted_area in enumerate(adjusted_areas):
    print(f"Adjusted Area for node {i} to match target {target_list[i]}: {adjusted_area:.9f}")
