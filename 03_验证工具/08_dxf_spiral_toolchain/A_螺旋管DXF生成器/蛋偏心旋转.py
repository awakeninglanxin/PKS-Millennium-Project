from calcplot3d import CalcPlot

# Define t and theta ranges
t = linspace(0, 2*pi, 1000)
theta = linspace(0, 2*pi, 100)

# Define parameters
b = 5/3
k = 2/3
c = 1
pi = 3.141592653589793

# Parametric equations
x = 2 * sin(t) / (b + sqrt(b**2 - 4 * k * cos(t)))
y = -(2/3) * ((-c * (1 + k**2) * (sqrt(b**2 - 4 * k) - sqrt(b**2 + 4 * k)) - (b * (-1 + k**2) + sqrt(b**2 + 4 * k) * (1 + k**2)) * sin(c * pi)) / (2 * c * k * sqrt(1 + k**2))) - ((b * (-1 + k**2) + sqrt(b**2 - 4 * k) * (1 + k**2)) / (2 * k * sqrt(1 + k**2))) + ((k^2 - 1) * b / k + (k^2 + 1) * sqrt(b^2 - 4 * k * cos(t)) / k) / (2 * sqrt(1 + k^2))

# Parametric surface equations for rotation around z-axis
X = lambda t, theta: x * cos(theta)
Y = lambda t, theta: x * sin(theta)
Z = lambda t, theta: y

# Plot the surface
plot = CalcPlot()
plot.surface_parametric(X, Y, Z, [t, theta])
plot.show()
