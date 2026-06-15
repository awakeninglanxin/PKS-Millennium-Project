import numpy as np
import matplotlib.pyplot as plt

# 设置字体为 SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
# 设置正常显示负号
plt.rcParams['axes.unicode_minus'] = False

# Parameters
x = np.linspace(-np.pi / 2, np.pi / 2, 1680*4)  # xi 范围
b = 5 / 3  # 固定参数
f = np.arctan(2 / 3)  # 固定角度

# 初始化 X 和 Y 列表
X = []
Y = []

odd = 0

for xi in x:
    if (-1) ** odd == 1:
        # 计算中心距离
        Y_distance = np.sqrt(1 / (b - xi * np.sin(f)) ** 2 - (xi * np.cos(f)) ** 2)
        X_distance = xi
        X.append(X_distance)
        Y.append(Y_distance)
    else:
        Y_distance = -np.sqrt(1 / (b - xi * np.sin(f)) ** 2 - (xi * np.cos(f)) ** 2)
        X_distance = xi
        X.append(X_distance)
        Y.append(Y_distance)
    odd += 1
# print(plt.colormaps())
# 设置颜色映射，根据 xi 的变化生成渐变色
colors = plt.cm.cool(np.linspace(0, 1, len(x)))

# 绘制线条并应用渐变色
plt.figure(figsize=(10, 6))
for i in range(len(X) - 1):
    plt.plot(Y[i:i + 2], x[i:i + 2], color=colors[i], lw=0.01)  # 将点连成线

plt.xlabel('Y')
plt.ylabel('x')
plt.title('舒伯格儿子方案：蛋 - 渐变色连线')
plt.grid(False)
plt.axis('equal')
plt.show()
