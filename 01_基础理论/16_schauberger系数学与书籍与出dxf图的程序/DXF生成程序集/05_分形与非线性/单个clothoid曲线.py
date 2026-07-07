import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# 默认曲率函数
user_input = "s*(s+448/75)"

# 定义曲率函数
try:
    def curvature(s):
        return eval(user_input)
except Exception as e:
    print(f"输入曲率函数有误: {e}")
    raise

def generate_clothoid(k_func, arc_length, num_points):
    """
    生成clothoid曲线
    k_func: 曲率函数
    arc_length: 弧长范围
    num_points: 采样点数量
    """
    s_vals = np.linspace(-arc_length, arc_length, num_points)  # 对称弧长范围
    x_vals = np.zeros(num_points)  # 初始化 x 坐标
    y_vals = np.zeros(num_points)  # 初始化 y 坐标
    theta = 0  # 初始角度
    for i in range(1, num_points):
        ds = s_vals[i] - s_vals[i - 1]  # 弧长增量
        k = k_func(s_vals[i - 1])  # 当前点的曲率
        theta += k * ds  # 累积角度变化
        x_vals[i] = x_vals[i - 1] + np.cos(theta) * ds  # 更新 x 坐标
        y_vals[i] = y_vals[i - 1] + np.sin(theta) * ds  # 更新 y 坐标

    return x_vals, y_vals, s_vals

# 参数
arc_length = 10  # 弧长范围
num_points = 1000  # 点数量
x_vals, y_vals, s_vals = generate_clothoid(curvature, arc_length, num_points)

# 绘制曲线
fig, ax = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.35)
ax.plot(x_vals, y_vals, label=f"Clothoid Curve (k(s) = {user_input})", color="blue")
ax.set_title(f"Clothoid Curve for k(s) = {user_input}")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend()
ax.axis("equal")
ax.grid()

# 添加滑块
ax_slider_s = plt.axes([0.2, 0.2, 0.6, 0.03])
s_slider = Slider(ax_slider_s, 'Coefficient (7)', -32, 32, valinit=7)

ax_slider_arc = plt.axes([0.2, 0.1, 0.6, 0.03])
arc_slider = Slider(ax_slider_arc, 'Arc Position', -arc_length, arc_length, valinit=0)

# 更新函数
def update(val):
    coeff = s_slider.val
    arc_position = arc_slider.val

    # 更新曲率函数
    global user_input
    user_input = f"s*(s+{coeff})"
    x_vals, y_vals, s_vals = generate_clothoid(curvature, arc_length, num_points)

    # 清除并重绘曲线
    ax.clear()
    ax.plot(x_vals, y_vals, label=f"Clothoid Curve (k(s) = {user_input})", color="blue")
    ax.set_title(f"Clothoid Curve for k(s) = {user_input}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    ax.axis("equal")
    ax.grid()

    # 高亮当前弧长位置点
    point_index = np.argmin(np.abs(s_vals - arc_position))
    ax.plot(x_vals[point_index], y_vals[point_index], 'ro', label="Current Point")
    fig.canvas.draw_idle()

s_slider.on_changed(update)
arc_slider.on_changed(update)

plt.show()