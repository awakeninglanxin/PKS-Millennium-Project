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

# Arc area integral
def arc_area(a):
    integrand = lambda t: x(t, a) * y(t, a)
    result, error = quad(integrand,0, 2*np.pi)
    return result

# Calculate arc area for a given value of a
a_value = 1  # Replace with your desired value of a
area = arc_area(a_value)
print(f"Arc area for a = {a_value}: {area}")
print(f"换成圆半径：= {a_value}: {np.sqrt(area/np.pi)}")