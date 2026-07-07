import numpy as np
import matplotlib.pyplot as plt

# Parameters for the spiral
k = 2 / 3
b = 5 / 3
a = 2* np.pi
m = 2 / 3

user_num = 7
# Define the range for t
# t_min =2* np.pi/(user_num+1)
t_min =2* np.pi
t_max = 2* np.pi+(2*user_num)* np.pi

t = np.linspace(t_min, t_max, 100*user_num)


# Functions to calculate x(t) and y(t)
def x(t, b, k, a):
    return -a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))/t
def x_add(t, b, k, a):
    return -a * ((2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))/t+1/t)
def x_shift(t, b, k, a):
    return -a * ((2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))/t+1/t)

def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return -a * (m * term1 + term2)/t
def y_minus(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return -a * ((m * term1 + term2)/t-1/t)
def y_shift(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return -a * ((m * term1 + term2)/t-1/t)

# Calculate x and y values
x_vals = x(t, b, k, a)
x_vals_add = x_add(t, b, k, a)
y_vals = y(t, b, k, a, m)
y_vals_minus = y_minus(t, b, k, a, m)
middle_curve = (x_vals_add + y_vals_minus) / 2
# Plot x(t) and y(t)
plt.figure(figsize=(10, 6))
plt.plot(t, x_vals, color='gray', label='x(t)',linestyle='--')
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