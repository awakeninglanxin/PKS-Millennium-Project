import numpy as np
import matplotlib.pyplot as plt

# 更新参数并考虑新的方程
b = 5 / 3  # 更新的 b 值
k = 2 / 3  # 更新的 k 值
theta = np.pi / 6  # 角度 theta

t = np.linspace(0, 2 * np.pi, 400)  # 参数 t

# 定义 x(t) 和 y(t) 考虑到新的方程
r = 1 / np.sqrt(k * (1 + np.tan(theta)**2))  # r(t) 的表达式
x = r * np.cos(t)  # x(t)
y = r * np.sin(t)  # y(t)

# 绘制图形
plt.figure(figsize=(6,6))
plt.plot(x, y, label='Parametric Curve x(t), y(t) with updated equation')
plt.xlabel('x(t)')
plt.ylabel('y(t)')
plt.title('Parametric Plot of x(t) and y(t) with updated b, k, and equation')
plt.legend()
plt.grid(True)

# 显示图像
plt.show()
