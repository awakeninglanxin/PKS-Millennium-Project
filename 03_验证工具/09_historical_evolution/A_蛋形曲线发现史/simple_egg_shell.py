import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# 定义参数
alpha = 33.69  # 角度
b = 5/3  # 常量b
alpha_r = np.radians(alpha)  # 将角度转换为弧度

# 定义 t 的范围
t = np.linspace(-np.pi/2, np.pi/2, 4000)

# 计算 x 的值，并进行检查
x_positive = np.sqrt(np.maximum(0, 1 / (b - t * np.sin(alpha_r))**2 - (t * np.cos(alpha_r))**2))
x_negative = -np.sqrt(np.maximum(0, 1 / (b - t * np.sin(alpha_r))**2 - (t * np.cos(alpha_r))**2))
y = -t

# 绘制图形
plt.figure(figsize=(10, 10))
plt.plot(x_positive, y, label=r'$x = +\sqrt{\frac{1}{(b - y \sin \alpha)^2} - (y \cos \alpha)^2}$')
plt.plot(x_negative, y, label=r'$x = -\sqrt{\frac{1}{(b - y \sin \alpha)^2} - (y \cos \alpha)^2}$')
plt.xlabel(r'$\bar{y}$')
plt.ylabel(r'$\bar{x}$')
plt.title(r'Graph of $\bar{y}$ vs $\bar{x}$')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.show()

# 保存为DWG格式
dwg = ezdxf.new('R2010')
modelspace = dwg.modelspace()

# 添加正负两部分数据
for x, y_val in zip(x_positive, y):
    if not np.isnan(y_val):  # 忽略无效值
        modelspace.add_point((x, y_val))

for x, y_val in zip(x_negative, y):
    if not np.isnan(y_val):  # 忽略无效值
        modelspace.add_point((x, y_val))

# 保存DWG文件
dwg.saveas("simple_egg_shell_plot.dwg")
