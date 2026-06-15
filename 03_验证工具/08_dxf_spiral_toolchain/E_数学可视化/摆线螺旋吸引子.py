import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# 定义系统的方程
def system(state, t, b, c):
    x, y, z = state
    dxdt = 0.382*y*z  # This is typically the equation for Sprott B attractor
    dydt = x - b * y
    dzdt = c - x * y
    return [dxdt, dydt, dzdt]

# 设置参数
b = 1.6  # 控制轨迹的圆环半径
c = 1.2  # 控制锥形高度

# 初始条件
initial_state = [0.1, 0.2, 0.4]

# 时间范围 (increase points for smoother trajectory)
t = np.linspace(0, 200, 2000)

# 求解微分方程
solution = odeint(system, initial_state, t, args=(b, c))

# 绘制三维图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 使用spring配色方案创建渐变色
colors = plt.cm.hsv(np.linspace(0, 1, len(solution)-1))

# 绘制轨迹线条
for i in range(len(solution)-1):
    ax.plot(solution[i:i+2, 0],
            solution[i:i+2, 1],
            solution[i:i+2, 2],
            color=colors[i],
            linewidth=0.5)

# 设置视角
ax.view_init(elev=20, azim=45)

# 移除坐标轴和网格
ax.set_axis_off()

# 设置黑色背景
ax.set_facecolor('black')
fig.set_facecolor('black')

plt.show()