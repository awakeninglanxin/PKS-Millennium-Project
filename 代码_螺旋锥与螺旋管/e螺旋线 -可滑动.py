import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Function to generate Exponential spiral points
def exponential_spiral(a, b, num_points, theta_max):
    theta = np.linspace(0, theta_max, num_points)
    r = a * np.exp(b * theta)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y

# Parameters
a_init = 1  # Initial scaling factor
b_init = 0.1  # Initial exponential growth factor
num_points = 1000  # Number of points in the spiral

# Initialize Tkinter root window
root = tk.Tk()
root.title("Transparent Matplotlib Window")

# Set the window to be transparent
root.attributes('-alpha', 0.6)  # Set window transparency on Windows
root.configure(bg='black')  # Set background color (black is commonly used)

# Create a figure and axis with transparent background
fig, ax = plt.subplots(figsize=(6, 6))
fig.patch.set_alpha(0.0)  # Set figure background to transparent
ax.patch.set_alpha(0.0)  # Set axis background to transparent

# Initial plot
theta_max_init_deg = 360  # Initial theta_max in degrees

def update_plot(a, b, theta_max_deg):
    theta_max_rad = np.deg2rad(theta_max_deg)  # Convert degrees to radians
    ax.clear()

    # Generate and plot the spiral
    x, y = exponential_spiral(a, b, num_points, theta_max_rad)
    ax.plot(x, y, color='red', alpha=1.0)

    ax.axhline(0, color='black', linewidth=0.5, alpha=1.0)  # Ensure axis lines are fully opaque
    ax.axvline(0, color='black', linewidth=0.5, alpha=1.0)  # Ensure axis lines are fully opaque
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True)
    fig.canvas.draw_idle()

# Initialize plot
update_plot(a_init, b_init, theta_max_init_deg)

# Embed the plot in Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create sliders for a, b, and theta_max
slider_frame = tk.Frame(root, bg='black')
slider_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Slider and entry for Scaling factor 'a'
a_slider = tk.Scale(slider_frame, from_=0.1, to=5, resolution=0.1, orient=tk.HORIZONTAL, label="Scaling factor a")
a_slider.set(a_init)
a_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Slider and entry for Exponential growth factor 'b'
b_slider = tk.Scale(slider_frame, from_=-1, to=1, resolution=0.01, orient=tk.HORIZONTAL, label="Exponential growth b")
b_slider.set(b_init)
b_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Slider and entry for Theta Max
theta_max_slider = tk.Scale(slider_frame, from_=0, to=720, resolution=1, orient=tk.HORIZONTAL, label="Theta Max (deg)")
theta_max_slider.set(theta_max_init_deg)
theta_max_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Helper function to update plot when sliders are moved
def update_sliders():
    update_plot(a_slider.get(), b_slider.get(), theta_max_slider.get())

a_slider.bind("<Motion>", lambda event: update_sliders())
b_slider.bind("<Motion>", lambda event: update_sliders())
theta_max_slider.bind("<Motion>", lambda event: update_sliders())

# Run the Tkinter event loop
root.mainloop()
