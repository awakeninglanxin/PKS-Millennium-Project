import numpy as np
from scipy.integrate import quad
import matplotlib.pyplot as plt

# Define the function for the curve
def curve_function(t):
    y = 1/ t
    return y

# Define the intervals using a loop to simplify the expression
n_intervals = 47
intervals = [(2**(k), 2**(k+1)) for k in range(0, n_intervals)]
# Generate x values for the curve
x = np.linspace(1, 2 ** (n_intervals), 1000)
y = curve_function(x)

# Create the figure and two subplots (one for each scale)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot the curve on both subplots

# Fill intervals with colors on both subplots
colors = plt.cm.viridis(np.linspace(0, 1, n_intervals))  # Create a colormap

for i, (start, end) in enumerate(intervals):
    x_fill = np.linspace(start, end, 100)
    y_fill = curve_function(x_fill)

    # Fill the interval on the upper plot (log scale)
    ax1.fill_between(x_fill, y_fill, color=colors[i], alpha=0.5, label=f'Interval {i + 1}' if i == 0 else "")

    # Fill the interval on the lower plot (linear scale)
    ax2.fill_between(x_fill, y_fill, color=colors[i], alpha=0.5, label=f'Interval {i + 1}' if i == 0 else "")

# Set labels and title for the upper plot
ax1.set_yscale('log')
ax1.set_xscale('log', base=2)
ax1.set_title('Curve with Intervals Colored (Log Scale on Top, Linear Scale on Bottom)')
ax1.set_ylabel('y (Log Scale)')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

# Set labels for the lower plot
ax2.set_yscale('linear')
ax2.set_xlabel('t')
ax2.set_ylabel('y (Linear Scale)')
ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

# Show legend in the upper plot
ax1.legend()
ax1.plot(x, y, color='black')

# Adjust layout to prevent overlap
plt.tight_layout()
plt.show()

# intervals = [((k), (k+1)) for k in range(1, n_intervals+1)]
# Calculate the area for each segment
volumes = []
for start, end in intervals:
    volume, _ = quad(curve_function, start, end)
    volumes.append(volume)

# Calculate the percentage change between each segment area
percentage_changes = [(volumes[i] - volumes[i - 1]) / volumes[i - 1] * 100 for i in range(1, len(volumes))]

# # Calculate the areas by dividing volumes by (i + 2) with i in reverse order and n in ascending order
# areas = [volumes[n] / (len(volumes) - n + 1) for n in range(len(volumes))]
# Calculate the areas by dividing volumes by (k+1)
areas = [volumes[i] / (i + 2) for i in range(len(volumes))]
# Calculate the percentage change between each segment area
area_percentage_changes = [(areas[i] - areas[i - 1]) / areas[i - 1] * 100 for i in range(1, len(areas))]

# Print volumes and percentage changes
print("Volumes:", volumes)
print("Percentage Changes:", percentage_changes)
print("Areas:", areas)
total_areas=sum(areas)
print("Areas:", total_areas)
area_percentage = [round((areas[i]/total_areas * 100),3) for i in range(0, len(areas))]
print("Areas%:", area_percentage)
print("Area Percentage Changes:", area_percentage_changes)

# Create a figure with two subplots side by side
fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(14, 7))

# Plot volume and percentage change
ax1.set_xlabel('Segment')
ax1.set_ylabel('Volume', color='tab:blue')
bars = ax1.bar(range(1, len(volumes) + 1), volumes, color='tab:blue', label='Volume')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Change (%)', color='tab:red')
line, = ax2.plot(range(2, len(volumes) + 1), percentage_changes, marker='o', color='tab:red', label='Percentage Change')
ax2.tick_params(axis='y', labelcolor='tab:red')

# Annotate data points for volume
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax1.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom')

# Annotate data points for percentage change
for i, (x, y) in enumerate(zip(range(2, len(volumes) + 1), percentage_changes)):
    ax2.annotate(f'{y:.2f}%',
                 xy=(x, y),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom')

ax1.set_title("Volume and Percentage Change")

# Plot area and area percentage change
ax3.set_xlabel('Segment')
ax3.set_ylabel('Area', color='tab:blue')
area_bars = ax3.bar(range(1, len(areas) + 1), areas, color='tab:blue', label='Area')
ax3.tick_params(axis='y', labelcolor='tab:blue')

ax4 = ax3.twinx()
ax4.set_ylabel('Area Percentage Change (%)', color='tab:red')
area_line, = ax4.plot(range(2, len(areas) + 1), area_percentage_changes, marker='o', color='tab:red', label='Area Percentage Change')
ax4.tick_params(axis='y', labelcolor='tab:red')

# Annotate data points for area
for i, bar in enumerate(area_bars):
    height = bar.get_height()
    ax3.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom')

# Annotate data points for area percentage change
for i, (x, y) in enumerate(zip(range(2, len(areas) + 1), area_percentage_changes)):
    ax4.annotate(f'{y:.2f}%',
                 xy=(x, y),
                 xytext=(0, 3),
                 textcoords="offset points",
                 ha='center', va='bottom')

ax3.set_title("Area and Percentage Change")

# Adjust layout and show plot
fig.tight_layout()
plt.show()
