import numpy as np
import matplotlib.pyplot as plt
import ezdxf  # 导入ezdxf库

# 参数设置
a = 1
k = 2 / 3
b = 5 / 3
m = 2 / 3

# Functions
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))

def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)

# 生成点
t_values = np.linspace(0, 2 * np.pi, 2000)
x_values = x(t_values, b, k, a)
y_values = y(t_values, b, k, a, m)

# 设置颜色渐变，根据 t_values 生成颜色
colors = plt.cm.hsv(np.linspace(0, 1, len(t_values)))

# 绘制曲线
plt.figure(figsize=(10, 6))

# 使用颜色渐变画线
for j in range(len(t_values) - 1):
    plt.plot(x_values[j:j + 2], y_values[j:j + 2], color=colors[j], lw=0.5)

plt.scatter(0, 0, color='red', label='Origin (0,0)')  # 添加原点
plt.axhline(0, color='black', linewidth=0.5)  # x轴
plt.axvline(0, color='black', linewidth=0.5)  # y轴
plt.xlabel('x')
plt.ylabel('y')
plt.title('Parametric Curve with HSV Gradient')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')

# 保存图像
plt.savefig("parametric_curve_hsv.png", transparent=True)
plt.show()
