import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# 定义动力系统方程
def system(state, t, b, c):
    x, y, z = state
    dxdt = 0.3 * y * z  # 控制螺旋展开速度
    dydt = x - b * y    # 控制圆周运动
    dzdt = c - x * y    # 控制垂直方向的运动，形成锥形
    return [dxdt, dydt, dzdt]

# 参数设置
b = 2  # 控制轨迹的圆环半径
c = 2  # 控制锥形高度
initial_state = [0.1, 0.1, 0.1]  # 初始状态

# 时间范围
t = np.linspace(0, 200, 2000)  # 增加时间点以获得平滑轨迹

# 求解方程
solution = odeint(system, initial_state, t, args=(b, c))

# 创建图形
fig = plt.figure(figsize=(15, 7))

# 子图1：侧视图（锥形效果）
ax1 = fig.add_subplot(121, projection='3d')
ax1.set_title("侧视图", color='white')
for i in range(len(solution) - 1):
    ax1.plot(solution[i:i+2, 0], solution[i:i+2, 1], solution[i:i+2, 2],
             color=plt.cm.plasma(i / len(solution)), linewidth=0.5)
ax1.view_init(elev=30, azim=60)  # 调整角度，突出锥形
ax1.set_axis_off()  # 隐藏坐标轴
ax1.set_facecolor('black')
# 子图2：俯视图（圆环摆线效果）
ax2 = fig.add_subplot(122, projection='3d')
ax2.set_title("俯视图", color='white')
for i in range(len(solution) - 1):
    ax2.plot(solution[i:i+2, 0], solution[i:i+2, 1], solution[i:i+2, 2],
             color=plt.cm.plasma(i / len(solution)), linewidth=0.5)
ax2.view_init(elev=90, azim=0)  # 俯视视角
ax2.set_axis_off()  # 隐藏坐标轴
ax2.set_facecolor('black')
# 设置全局样式
fig.set_facecolor('black')  # 设置背景为黑色

plt.show()
