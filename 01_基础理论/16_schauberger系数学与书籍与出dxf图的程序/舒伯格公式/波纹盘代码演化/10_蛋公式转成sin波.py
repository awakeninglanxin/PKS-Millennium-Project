import numpy as np
import matplotlib.pyplot as plt

# 设置参数
k = 2/3
b = 5/3
c = 1
t = np.linspace(0, 2 * np.pi, 400)  # 定义 t 的范围

# 定义 y(t) 和 x(t) 的表达式
y = (2 * np.sin(t)) / (b + np.sqrt(b**2 - 4 * k * np.cos(t)))

sqrt_b2_minus_4k = np.sqrt(b**2 - 4 * k)
sqrt_b2_plus_4k = np.sqrt(b**2 + 4 * k)

term1 = -(2/3) * (-c * (1 + k**2) * (sqrt_b2_minus_4k - sqrt_b2_plus_4k) -
                  (b * (-1 + k**2) + sqrt_b2_plus_4k * (1 + k**2)) * np.sin(c * np.pi)) / (2 * c * k * np.sqrt(1 + k**2))

term2 = - (b * (-1 + k**2) + sqrt_b2_minus_4k * (1 + k**2)) / (2 * k * np.sqrt(1 + k**2))

term3 = ((k**2 - 1) * b / k + (k**2 + 1) * np.sqrt(b**2 - 4 * k * np.cos(t)) / k) / (2 * np.sqrt(1 + k**2))

x = term1 + term2 + term3

# 绘制 x(t) 和 y(t)
plt.figure(figsize=(10, 6))
plt.plot(t, x, label='x(t)', color='blue')
plt.plot(t, y, label='y(t)', color='green')
plt.title('Plot of x(t) and y(t)')
plt.xlabel('t')
plt.ylabel('x(t) and y(t)')
plt.legend()
plt.grid(True)
plt.show()

# 绘制参数方程曲线 x(t) vs y(t)
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='Parametric Curve (x(t), y(t))', color='purple')
plt.title('Parametric Plot of x(t) and y(t)')
plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()
