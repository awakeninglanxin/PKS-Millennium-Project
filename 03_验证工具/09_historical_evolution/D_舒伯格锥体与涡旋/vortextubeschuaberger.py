import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

# 参数定义
a = 5.0       # 弹簧开始时的半径
height = 16   # 弹簧的高度
turns = 8    # 弹簧的圈数
points_per_turn = 100  # 每圈的点数

# 生成弹簧的数据
t = np.linspace(0, turns * 2 * np.pi, int(turns * points_per_turn))
x = t
r = a / (x + 1)  # 半径随着x线性变化

# 转换为笛卡尔坐标系
x = r * np.cos(t)
y = r * np.sin(t)

# 计算每个点的圈数并应用相应的螺距
d = []
for i in range(len(t)):
    n = int(i/points_per_turn) + 1  # 第n圈
    d.append(50/(n*(n + 1)))# 螺距与 height 和 turns 相关

# 非线性增加高度
z = height * t / (turns * 2 * np.pi)

# 绘制3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 设置 xy 轴范围为 ±2
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])

# 生成弹簧的圆柱
for i in range(turns * points_per_turn - 1):
    ax.plot([x[i], x[i+1]], [y[i], y[i+1]], [z[i], z[i+1]], color=cm.hsv(i / (turns * points_per_turn)), linewidth=d[i])

ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长
ax.legend()

# 设置标签和图表属性
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_zlabel('Z Axis')
ax.set_title('3D Variable Schauberger vortex')

plt.show()
