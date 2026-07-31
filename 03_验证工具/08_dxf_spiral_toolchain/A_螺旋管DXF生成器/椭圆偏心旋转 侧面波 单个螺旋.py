import numpy as np
import matplotlib.pyplot as plt

# 设置字体为 SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
# 设置正常显示负号
plt.rcParams['axes.unicode_minus'] = False
# Parameters
k =1/np.sqrt(2)  # Adjust as needed
# k = 1 # Adjust as needed
u_n=5
A0 = 3 # Adjust as needed
T =90 # Adjust as needed
x = np.linspace(1/u_n, u_n, 6000)

# Plot
plt.figure(figsize=(10, 10))
# theta = t * a + d / t
X = []
Y = []
for xi in x:
    # theta = T / xi
    # theta = xi * A0
    theta = xi * A0 + T / xi
    # Calculate the center distance
    center_distance = np.sqrt((xi * np.cos(theta)** 2+(xi / k * np.sin(theta)** 2)))
    semi_major_axis = xi
    semi_minor_axis = xi / k
    # Normalize coordinates
    norm_factor = np.sqrt(semi_major_axis ** 2 + semi_minor_axis ** 2)
    X.append((center_distance / norm_factor) * np.cos(T/xi))
    Y.append((center_distance / norm_factor) * np.sin(T/xi))

# Plot the ellipse
plt.plot(X, Y, label=f'Ellipse 0')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Concentric Ellipses with Varying Alignment')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(x, X, color='green')
plt.plot(x, Y, color='blue')

plt.xlabel('x')
plt.ylabel('Y')
plt.title('x(绿色) vs y(蓝色)')
plt.legend()
plt.grid(True)
plt.show()