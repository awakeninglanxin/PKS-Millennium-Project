import numpy as np
import matplotlib.pyplot as plt

# Parameters for the spiral
k = 2 / 3
b = 5 / 3
a = 2* np.pi
m = 2 / 3

user_num = 5

t = np.linspace( np.pi/user_num, np.pi, 3000*user_num)

# Functions to calculate x(t) and y(t)
def x(t, b, k, a):
    return -a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))

def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return -a * (m * term1 + term2)

x_vals_magic = ((x(303*t, b, k, a)- x(285*t, b, k, a)))/t
y_vals_magic = ((y(301*t, b, k, a, m)-y(287*t, b, k, a, m)))/t

# Normalize t for color mapping
norm = plt.Normalize(t.min(), t.max())
colors = plt.cm.hsv(norm(t))

# Plot the first spiral curve with HSV coloring
plt.figure(figsize=(10, 6))
for i in range(len(t) - 1):
    plt.plot(x_vals_magic[i:i+2], y_vals_magic[i:i+2], color=colors[i], lw=0.1)

plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.title('Spiral Curve with HSV Color Gradient')
plt.legend(['Spiral Curve'])
plt.axis('equal')
plt.grid(True)
plt.show()
t = np.linspace( np.pi/user_num, 2*np.pi*(user_num+1), 1000*user_num)
# Plot the second spiral curve with HSV coloring
plt.figure(figsize=(10, 6))
for i in range(len(t) - 1):
    plt.plot(t[i:i+2], x_vals_magic[i:i+2], color=colors[i], lw=0.8)
    plt.plot(t[i:i+2], y_vals_magic[i:i+2], color=colors[i], lw=0.8)

plt.xlabel('t')
plt.ylabel('Value')
plt.title('Plot of x(t) and y(t) with HSV Color Gradient')
plt.legend(['x_magic(t)', 'y_magic(t)'])
plt.grid(True)
plt.show()
