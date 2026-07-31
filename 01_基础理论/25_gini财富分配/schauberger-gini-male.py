import numpy as np
import plotly.graph_objects as go

a = 1
# Adjustable odd number n (must be an odd number)
n =4 #分n段阶级
male_num=10000
# Functions for 3D curve
def x(t):
    return -2 * a * np.pi * np.cos(t) / t
def y(t):
    return 2 * a * np.pi * np.sin(t) / t
def z(t):
    return a * np.log(t) / (np.log(0.618))

# Generate points
t_values = np.linspace(4 * np.pi, 2**(n+2) * np.pi, male_num+1)  # Avoid t=0 to prevent division by zero
x_values = x(t_values)
y_values = y(t_values)
z_values = z(t_values)
# Generate intervals using 2^n
intervals = [2**i * np.pi for i in range(2, 3+n)]
points_in_intervals = []
for i in range(len(intervals) - 1):
    count = np.sum((t_values >= intervals[i]) & (t_values < intervals[i + 1]))
    points_in_intervals.append(count)
print("Points in each interval:", points_in_intervals)
# Given total wealth and calculate wealth distribution
total_wealth = 60000
b = total_wealth / len(points_in_intervals)
sequence = []
for count in points_in_intervals:
    c = b / count
    sequence.extend([c] * count)

# Calculate Gini coefficient
sequence.sort()                        # Sort from poorest to richest
sample_count = len(sequence)            # Total number of samples
cw = []
for i in range(sample_count):           # Calculate cumulative wealth
    cw.append(sum(sequence[:i + 1]))  # cw[i] represents the total wealth of the poorest i+1 people

total_wealth = cw[-1]                   # Total wealth in society
for i in range(len(cw)):               # Calculate cumulative wealth ratio
    cw[i] = cw[i] / total_wealth        # cw[i] represents the wealth ratio of the poorest i+1 people
cw = [0] + cw                          # Add 0: 0% of people own 0% of wealth
cp = [0] + [i / sample_count for i in range(1, sample_count + 1)]
B = 0                                  # Calculate area B using the trapezoidal rule
for i in range(1, sample_count + 1):
    B = B + (cw[i] + cw[i - 1]) * (cp[i] - cp[i - 1]) / 2
A = 0.5 - B                            # A+B = 0.5

# Plot the Lorenz curve and Gini coefficient using Plotly
cp = [0] + [i / sample_count for i in range(1, sample_count + 1)]
cw = [0] + cw[1:]  # Use the updated cw with 0 added

# Create a plot object
fig = go.Figure()

# Add the Lorenz curve
fig.add_trace(go.Scatter(x=cp, y=cw, mode='lines', name='Lorenz Curve', line=dict(color='blue', dash='dash')))

# Add the line of equality
fig.add_trace(go.Scatter(x=cp, y=cp, mode='lines', name='Line of Equality', line=dict(color='red')))

# Adding a specific point on the Lorenz curve
middle_index = len(cp) // 2  # Get the middle index
fig.add_trace(go.Scatter(x=[cp[middle_index]], y=[cw[middle_index]], mode='markers', marker=dict(color='black', size=10), name='Middle Point'))

# Labeling the middle point
fig.add_annotation(x=cp[middle_index], y=cw[middle_index], text=f"{cp[middle_index]*100:.1f}%, {cw[middle_index]*100:.1f}%", showarrow=True, arrowhead=1)

# Fill area A
fig.add_trace(go.Scatter(x=cp + cp[::-1], y=cw + [i for i in cp[::-1]], fill='toself', fillcolor='red', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='Area A'))

# Fill area B
fig.add_trace(go.Scatter(x=cp, y=cw, fill='tonexty', fillcolor='green', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='Area B'))

# Calculate the Gini coefficient
gini_coefficient = A / (A + B)
# Poorest person's wealth
poorest_salary = sequence[0]
# Richest person's wealth
richest_salary = sequence[-1]
# Define the title, including all required information
title_text = (
    f"male Gini Coefficient: {gini_coefficient:.3f}<br>"
    f"Wealth of Poorest Person: {poorest_salary}<br>"
    f"Wealth of Richest Person: {richest_salary}<br>"
    f"Sample Size: {sample_count}"
)

# Update layout settings
fig.update_layout(
    title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=14)),
    xaxis_title='Population Percentage',
    yaxis_title='Wealth Percentage',
    xaxis=dict(tickformat=',.0%', range=[0, 1]),
    yaxis=dict(tickformat=',.0%', range=[0, 1]),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

# Show the plot
fig.show()