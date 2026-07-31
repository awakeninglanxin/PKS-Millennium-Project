import numpy as np
import matplotlib.pyplot as plt

# Parameters for the spiral
k = 2 / 3
b = 5 / 3
a = 2* np.pi
m = 2 / 3
d=1
# c=np.pi/2
c = 3*np.pi / 4
user_num = 8
# f=1  #天眼
f=2  #蛋

# Define the range for t
# t_min =2* np.pi/(user_num+1)
t_min=2* np.pi
t_max = 2* np.pi+(2*user_num)* np.pi

t = np.linspace(t_min, t_max, 1000*user_num)

def x(t, b, k, a, d, c, f):
    return -a * ((np.cos(d * t - c) * 2 * np.sin(f * t)) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(f * t))))/t
def x_add(t, b, k, a, d, c, f):
    return -a * (((np.cos(d * t - c) * 2 * np.sin(f * t)) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(f * t))))/t+1/t)

# Function to calculate y(t)
def y(t, b, k, a, m, d, c, f):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(f * np.pi)))) / (2 * k))
    term2 = (1 / (2 * np.sqrt(1 + k ** 2))) * ((k ** 2 - 1) / k * b + (k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(f * t)))
    term3 = -((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2)))
    return -a * ((np.sin(d * t + c)) * m * (term1 + term2 + term3))

# Calculate x and y values
x_vals = x(t, b, k, a, d, c, f)
y_vals = y(t, b, k, a, m, d, c, f)

def y_minus(t, b, k, a, m, d, c, f):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(f * np.pi)))) / (
                2 * k))
    term2 = (1 / (2 * np.sqrt(1 + k ** 2))) * (
                (k ** 2 - 1) / k * b + (k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(f * t)))
    term3 = -((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2)))
    return -a * ((np.sin(d * t + c)) * m * (term1 + term2 + term3)/t-1/t)

# Calculate x and y values
x_vals_add = x_add(t, b, k, a, d, c, f)
y_vals_minus = y_minus(t, b, k, a, m, d, c, f)
middle_curve = (x_vals_add + y_vals_minus) / 2
# Plot x(t) and y(t)
plt.figure(figsize=(10, 6))
# plt.plot(t, x_vals, color='gray', label='x(t)',linestyle='--')
plt.plot(t, x_vals_add, color='blue', label='x_add(t)')
plt.plot(t, y_vals_minus, color='green', label='y_minus(t)')
plt.plot(t, middle_curve, color='purple', linestyle='--')
plt.xlabel('t')
plt.ylabel('Value')
plt.title('Plot of x(t) and y(t)')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(x_vals, y_vals, label='Spiral Curve')
plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.title('Spiral Curve')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.show()