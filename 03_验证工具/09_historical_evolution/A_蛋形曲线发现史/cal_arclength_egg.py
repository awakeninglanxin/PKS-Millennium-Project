from scipy.integrate import quad
import numpy as np

# Parameters
k = 2/3
b = 5/3
m = 2/3

# Function definitions
def x(t, a):
    return 2 * np.sin(a * t) / (b + np.sqrt(b**2 - 4 * k * np.cos(a * t)))

def y(t, a):
    term1 = -m * ((-np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4 * k) + np.sqrt(b**2 - 4 * k * np.cos(a * np.pi)))) / (2 * k))
    term2 = (1 / (2 * np.sqrt(1 + k**2))) * (((k**2 - 1) / k) * b + ((k**2 + 1) / k) * np.sqrt(b**2 - 4 * k * np.cos(a * t)))
    term3 = -(b * (k**2 - 1) + np.sqrt(b**2 - 4 * k) * (k**2 + 1)) / (2 * k * np.sqrt(1 + k**2))
    return term1 + term2 + term3

# Derivatives
def dx_dt(t, a):
    return (2 * a * np.cos(a * t) * (b + np.sqrt(b**2 - 4 * k * np.cos(a * t))) - 2 * np.sin(a * t) * (1 + 2 * k * np.sin(a * t))) / (b + np.sqrt(b**2 - 4 * k * np.cos(a * t)))**2

def dy_dt(t, a):
    term1 = -m * ((-np.sqrt(1 + k**2) * np.sqrt(b**2 - 4 * k) * a * np.sin(a * t)) / (2 * np.sqrt(b**2 - 4 * k * np.cos(a * t))))
    term2 = (1 / (2 * np.sqrt(1 + k**2))) * (((k**2 - 1) / k) * (-k * np.sin(a * t)) + ((k**2 + 1) / k) * (-2 * k * np.sin(a * t) * np.sqrt(b**2 - 4 * k * np.cos(a * t))))
    term3 = (b * (k**2 - 1) + np.sqrt(b**2 - 4 * k) * (k**2 + 1) * a * np.sin(a * t)) / (2 * k * np.sqrt(1 + k**2) * np.sqrt(b**2 - 4 * k * np.cos(a * t)))
    return term1 + term2 + term3

# Arc length integral
def arc_length(a):
    integrand = lambda t: np.sqrt(dx_dt(t, a)**2 + dy_dt(t, a)**2)
    result, error = quad(integrand, -np.pi, np.pi)
    return result

# Calculate arc length for a given value of a
a_value = 1  # Replace with your desired value of a
length = arc_length(a_value)
print(f"Arc length for a = {a_value}: {length}")
print(f"换成圆半径：= {a_value}: {length/(2*np.pi)}")