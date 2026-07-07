import numpy as np
import matplotlib.pyplot as plt

# 参数设置
z0 = 5 / 3
alpha = np.arctan(2/3)

# 定义方程
def equation_to_solve(y, x):
    return 1/(z0 + y*np.sin(alpha))**2 - (x**2 + (y*np.cos(alpha))**2)

# 创建网格，y的范围限制在[-π/2, π/2]
x = np.linspace(-3, 3, 500)
y = np.linspace(-np.pi/2, np.pi/2, 500)
X, Y = np.meshgrid(x, y)
Z = equation_to_solve(Y, X)

# 绘制等高线图（隐式函数）
plt.figure(figsize=(8, 6))
# 使用contour绘制级别为0的等高线
contour = plt.contour(X, Y, Z, levels=[0], colors='red', linewidths=2)
plt.xlabel('x')
plt.ylabel('y')
plt.title('Egg-shaped curve (Implicit function) with y in [-π/2, π/2]')
plt.axis("equal")
plt.grid(True)

# 添加坐标轴
plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.3)

# 显示y的范围标记
plt.axhline(y=np.pi/2, color='gray', linestyle=':', alpha=0.5)
plt.axhline(y=-np.pi/2, color='gray', linestyle=':', alpha=0.5)
plt.text(2.5, np.pi/2+0.05, 'y=π/2', fontsize=10)
plt.text(2.5, -np.pi/2-0.15, 'y=-π/2', fontsize=10)

plt.show()