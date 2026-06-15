import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib
# 指定默认字体
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'
# 参数定义
a = 5.0       # 弹簧开始时的半径
turns = 5    # 弹簧的圈数
points_per_turn = 100  # 每圈的点数

# 生成自定义数列（类似斐波那契）
def generate_custom_sequence(length):
    sequence = [2, 1]  # 初始值
    for _ in range(2, length):
        next_value = sequence[-1] + sequence[-2]  # 类似斐波那契，但可以根据需要修改
        sequence.append(next_value)
    return sequence

# 生成自定义数列，使用对数增长的高度
def generate_log_sequence(length):
    sequence = []
    for i in range(1, length + 1):
        height = 2 * np.pi * np.log(i)
        sequence.append(height)
    return sequence

# 生成弹簧的数据
def generate_spring_data(turns, points_per_turn, heights):
    t = np.linspace(0, turns * 2 * np.pi, int(turns * points_per_turn))
    x = t
    r = a / (x + 1)  # 半径随着x线性变化

    # 转换为笛卡尔坐标系
    x = r * np.cos(t)
    y = r * np.sin(t)

    # 非线性增加高度
    z = np.zeros_like(t)
    for i in range(1, len(t)):
        turn_index = int(i / points_per_turn)  # 当前是第几圈
        z[i] = np.sum(heights[:turn_index]) if turn_index > 0 else 0
        z[i] += (heights[turn_index] * (i % points_per_turn) / points_per_turn)

    # 计算每个点的螺距和线宽，线宽随点渐变
    d = 20 / ((np.arange(len(t)) / points_per_turn + 1) ** 2)

    return x, y, z, d

# 生成斐波那契数列高度和对数高度
fib_heights = generate_custom_sequence(turns)
log_heights = generate_log_sequence(turns)

# 生成斐波那契数列弹簧的数据
fib_x, fib_y, fib_z, fib_d = generate_spring_data(turns, points_per_turn, fib_heights)

# 生成对数增长高度弹簧的数据
log_x, log_y, log_z, log_d = generate_spring_data(turns, points_per_turn, log_heights)

# 绘制3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 设置 xy 轴范围为 ±5
ax.set_xlim([-5, 5])
ax.set_ylim([-5, 5])

# 绘制斐波那契数列弹簧的圆柱，并标记
for i in range(turns * points_per_turn - 1):
    ax.plot([fib_x[i], fib_x[i+1]], [fib_y[i], fib_y[i+1]], [fib_z[i], fib_z[i+1]], color=cm.hsv(i / (turns * points_per_turn)), linewidth=fib_d[i], label='太阴数列fib' if i == 0 else None)

# 绘制对数增长高度弹簧的圆柱，并标记
for i in range(turns * points_per_turn - 1):
    ax.plot([log_x[i], log_x[i+1]], [log_y[i], log_y[i+1]], [log_z[i] + 30, log_z[i+1] + 30], color=cm.turbo(i / (turns * points_per_turn)), linewidth=log_d[i], label='太阳数列log' if i == 0 else None)

ax.set_box_aspect([1, 1, 1])  # 确保x, y, z轴等长

# 设置标签和图表属性
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_zlabel('Z Axis')
ax.set_title('3D Variable Schauberger Vortex')
ax.legend()

plt.show()
