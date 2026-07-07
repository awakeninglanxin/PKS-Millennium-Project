import numpy as np
import matplotlib.pyplot as plt

# 设置字体为 SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
# 设置正常显示负号
plt.rcParams['axes.unicode_minus'] = False
# Parameters
k =2
# k = 1 # Adjust as needed
u_n=5
A0 = 0.5 # Adjust as needed
T =6 # Adjust as needed
x = np.linspace(-np.pi/2, np.pi/2, 6000)
b=5/3
f=np.arctan(2/3)
# Plot
plt.figure(figsize=(10, 10))
# theta = t * a + d / t
X = []
Y = []
odd=0
for xi in x:
    theta = xi * A0 + T / xi
    semi_major_axis = xi
    semi_minor_axis = xi / k
    if (-1)**odd==1:
        # Calculate the center distance
        Y_distance=np.sqrt(1 / (b - xi*np.sin(f)) ** 2 - (xi*np.cos(f)) ** 2)
        X_distance= xi
        # Normalize coordinates
        X.append((X_distance) * np.cos(T/xi))
        Y.append((Y_distance) * np.sin(T/xi))
    if (-1) ** odd == -1:
        # Calculate the center distance
        Y_distance=-np.sqrt(1 / (b - xi*np.sin(f)) ** 2 - (xi*np.cos(f)) ** 2)
        X_distance= xi
        # Normalize coordinates

        X.append((X_distance) * np.cos(T/xi))
        Y.append((Y_distance) * np.sin(T/xi))
    odd+=1
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
plt.plot(x, Y, color='blue')

plt.xlabel('x')
plt.ylabel('Y')
plt.title('x(绿色) vs y(蓝色)')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()