import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# 曲率函数1: k(s) = s
def curvature_x(s):
    return s

# 曲率函数2: k(s) = s^2 + s - 2
def curvature_s2(s):
    return s**2 + s - 2

# 添加新的曲率函数
def curvature_s3(s):
    return s**2 + 4*s + 3

def curvature_s4(s):
    return s**2 - 1.5*s - 1

def curvature_s5(s):
    return s**2 + 0.75*s - 0.25


def generate_curve(k_func, arc_length, num_points):
    """
    生成曲线，并确保对称性
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

    # 平移修正：确保几何中心在 (0, 0)
    x_vals -= np.mean(x_vals)
    y_vals -= np.mean(y_vals)

    return x_vals, y_vals, s_vals

# 计算密切圆的圆心和半径
def osculating_circle(x_vals, y_vals, s_vals, theta_vals, k_func, arc_position):
    """
    计算密切圆的圆心和半径
    x_vals, y_vals: 曲线的 x 和 y 坐标
    s_vals: 弧长值
    theta_vals: 累积角度值
    k_func: 曲率函数
    arc_position: 当前弧长位置
    """
    index = np.argmin(np.abs(s_vals - arc_position))  # 找到最近的弧长位置索引
    k = k_func(s_vals[index])  # 当前曲率
    R = 1 / abs(k) if k != 0 else np.inf  # 半径
    theta = theta_vals[index]  # 当前点的切线方向（累积角度）

    # 判断是否需要翻转：对于k(s) = s (直线)，需要翻转；其他曲线则不翻转
    if k_func == curvature_x:  # k(s) = s，直线
        if arc_position < 0:
            x_c = x_vals[index] + R * np.sin(theta)
            y_c = y_vals[index] - R * np.cos(theta)
        else:
            x_c = x_vals[index] - R * np.sin(theta)
            y_c = y_vals[index] + R * np.cos(theta)
    else:
        # 其他曲线不需要翻转
        x_c = x_vals[index] - R * np.sin(theta)
        y_c = y_vals[index] + R * np.cos(theta)

    return x_c, y_c, R, x_vals[index], y_vals[index]


# 参数
arc_length = 10  # 弧长范围
num_points = 1000  # 点数量

# ================= 第一张图 (k(s) = s) =================
x_vals1, y_vals1, s_vals1 = generate_curve(curvature_x, arc_length, num_points)
theta_vals1 = np.cumsum(curvature_x(s_vals1) * (2 * arc_length / num_points))

fig1, ax1 = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)
ax1.plot(x_vals1, y_vals1, label="Curve (k(s) = s)", color="blue")
k_vals1 = curvature_x(s_vals1)
ax1.plot(s_vals1, k_vals1, label="Curvature Function (k = s)", color="red", linestyle="-")

# 初始化密切圆
arc_position1 = 0
x_c1, y_c1, R1, x_p1, y_p1 = osculating_circle(x_vals1, y_vals1, s_vals1, theta_vals1, curvature_x, arc_position1)
circle_artist1 = plt.Circle((x_c1, y_c1), R1, color="purple", fill=False, linestyle="--", label="Osculating Circle")
ax1.add_artist(circle_artist1)
point_on_curve1, = ax1.plot([x_p1], [y_p1], 'ro', label="Point on Curve")

ax1.set_title("Curve and Curvature Function (k(s) = s)")
ax1.set_xlabel("x")
ax1.set_ylabel("y")
ax1.legend()
ax1.axis("equal")
ax1.grid()

# 添加滑块
ax_slider1 = plt.axes([0.2, 0.1, 0.6, 0.03])
slider1 = Slider(ax_slider1, 'Arc Position', -arc_length, arc_length, valinit=arc_position1)

# 更新函数
def update1(val):
    arc_position1 = slider1.val
    x_c1, y_c1, R1, x_p1, y_p1 = osculating_circle(x_vals1, y_vals1, s_vals1, theta_vals1, curvature_x, arc_position1)
    circle_artist1.center = (x_c1, y_c1)
    circle_artist1.set_radius(R1)
    point_on_curve1.set_data([x_p1], [y_p1])
    fig1.canvas.draw_idle()

slider1.on_changed(update1)

# ================= 第二张图 (k(s) = s^2 + s - 2) =================
x_vals2, y_vals2, s_vals2 = generate_curve(curvature_s2, arc_length, num_points)
theta_vals2 = np.cumsum(curvature_s2(s_vals2) * (2 * arc_length / num_points))

fig2, ax2 = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)
ax2.plot(x_vals2, y_vals2, label="Curve (k(s) = s^2 + s - 2)", color="blue")
k_vals2 = curvature_s2(s_vals2)
ax2.plot(s_vals2, k_vals2, label="Curvature Function (k = s^2 + s - 2)", color="red", linestyle="-")

# 初始化密切圆
arc_position2 = 0
x_c2, y_c2, R2, x_p2, y_p2 = osculating_circle(x_vals2, y_vals2, s_vals2, theta_vals2, curvature_s2, arc_position2)
circle_artist2 = plt.Circle((x_c2, y_c2), R2, color="purple", fill=False, linestyle="--", label="Osculating Circle")
ax2.add_artist(circle_artist2)
point_on_curve2, = ax2.plot([x_p2], [y_p2], 'ro', label="Point on Curve")

ax2.set_title("Curve and Curvature Function (k(s) = s^2 + s - 2)")
ax2.set_xlabel("x")
ax2.set_ylabel("y")
ax2.legend()
ax2.axis("equal")
ax2.grid()

# 添加滑块
ax_slider2 = plt.axes([0.2, 0.1, 0.6, 0.03])
slider2 = Slider(ax_slider2, 'Arc Position', -arc_length, arc_length, valinit=arc_position2)

# 更新函数
def update2(val):
    arc_position2 = slider2.val
    x_c2, y_c2, R2, x_p2, y_p2 = osculating_circle(x_vals2, y_vals2, s_vals2, theta_vals2, curvature_s2, arc_position2)
    circle_artist2.center = (x_c2, y_c2)
    circle_artist2.set_radius(R2)
    point_on_curve2.set_data([x_p2], [y_p2])
    fig2.canvas.draw_idle()

slider2.on_changed(update2)


# ================= 第三张图 (k(s) = s^2 + 4*s + 3) =================
x_vals3, y_vals3, s_vals3 = generate_curve(curvature_s3, arc_length, num_points)
theta_vals3 = np.cumsum(curvature_s3(s_vals3) * (2 * arc_length / num_points))

fig3, ax3 = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)
ax3.plot(x_vals3, y_vals3, label="Curve (k(s) = s^2 + 4*s + 3)", color="blue")
k_vals3 = curvature_s3(s_vals3)
ax3.plot(s_vals3, k_vals3, label="Curvature Function (k = s^2 + 4*s + 3)", color="red", linestyle="-")

# 初始化密切圆
arc_position3 = 0
x_c3, y_c3, R3, x_p3, y_p3 = osculating_circle(x_vals3, y_vals3, s_vals3, theta_vals3, curvature_s3, arc_position3)
circle_artist3 = plt.Circle((x_c3, y_c3), R3, color="purple", fill=False, linestyle="--", label="Osculating Circle")
ax3.add_artist(circle_artist3)
point_on_curve3, = ax3.plot([x_p3], [y_p3], 'ro', label="Point on Curve")

ax3.set_title("Curve and Curvature Function (k(s) = s^2 + 4*s + 3)")
ax3.set_xlabel("x")
ax3.set_ylabel("y")
ax3.legend()
ax3.axis("equal")
ax3.grid()

# 添加滑块
ax_slider3 = plt.axes([0.2, 0.1, 0.6, 0.03])
slider3 = Slider(ax_slider3, 'Arc Position', -arc_length, arc_length, valinit=arc_position3)

# 更新函数
def update3(val):
    arc_position3 = slider3.val
    x_c3, y_c3, R3, x_p3, y_p3 = osculating_circle(x_vals3, y_vals3, s_vals3, theta_vals3, curvature_s3, arc_position3)
    circle_artist3.center = (x_c3, y_c3)
    circle_artist3.set_radius(R3)
    point_on_curve3.set_data([x_p3], [y_p3])
    fig3.canvas.draw_idle()

slider3.on_changed(update3)

# ================= 第四张图 (k(s) = s^2 - 1.5*s - 1) =================
x_vals4, y_vals4, s_vals4 = generate_curve(curvature_s4, arc_length, num_points)
theta_vals4 = np.cumsum(curvature_s4(s_vals4) * (2 * arc_length / num_points))

fig4, ax4 = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)
ax4.plot(x_vals4, y_vals4, label="Curve (k(s) = s^2 - 1.5*s - 1)", color="blue")
k_vals4 = curvature_s4(s_vals4)
ax4.plot(s_vals4, k_vals4, label="Curvature Function (k = s^2 - 1.5*s - 1)", color="red", linestyle="-")

# 初始化密切圆
arc_position4 = 0
x_c4, y_c4, R4, x_p4, y_p4 = osculating_circle(x_vals4, y_vals4, s_vals4, theta_vals4, curvature_s4, arc_position4)
circle_artist4 = plt.Circle((x_c4, y_c4), R4, color="purple", fill=False, linestyle="--", label="Osculating Circle")
ax4.add_artist(circle_artist4)
point_on_curve4, = ax4.plot([x_p4], [y_p4], 'ro', label="Point on Curve")

ax4.set_title("Curve and Curvature Function (k(s) = s^2 - 1.5*s - 1)")
ax4.set_xlabel("x")
ax4.set_ylabel("y")
ax4.legend()
ax4.axis("equal")
ax4.grid()

# 添加滑块
ax_slider4 = plt.axes([0.2, 0.1, 0.6, 0.03])
slider4 = Slider(ax_slider4, 'Arc Position', -arc_length, arc_length, valinit=arc_position4)

# 更新函数
def update4(val):
    arc_position4 = slider4.val
    x_c4, y_c4, R4, x_p4, y_p4 = osculating_circle(x_vals4, y_vals4, s_vals4, theta_vals4, curvature_s4, arc_position4)
    circle_artist4.center = (x_c4, y_c4)
    circle_artist4.set_radius(R4)
    point_on_curve4.set_data([x_p4], [y_p4])
    fig4.canvas.draw_idle()

slider4.on_changed(update4)

# ================= 第五张图 (k(s) = s^2 + 0.75*s - 0.25) =================
x_vals5, y_vals5, s_vals5 = generate_curve(curvature_s5, arc_length, num_points)
theta_vals5 = np.cumsum(curvature_s5(s_vals5) * (2 * arc_length / num_points))

fig5, ax5 = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)
ax5.plot(x_vals5, y_vals5, label="Curve (k(s) = s^2 + 0.75*s - 0.25)", color="blue")
k_vals5 = curvature_s5(s_vals5)
ax5.plot(s_vals5, k_vals5, label="Curvature Function (k = s^2 + 0.75*s - 0.25)", color="red", linestyle="-")

# 初始化密切圆
arc_position5 = 0
x_c5, y_c5, R5, x_p5, y_p5 = osculating_circle(x_vals5, y_vals5, s_vals5, theta_vals5, curvature_s5, arc_position5)
circle_artist5 = plt.Circle((x_c5, y_c5), R5, color="purple", fill=False, linestyle="--", label="Osculating Circle")
ax5.add_artist(circle_artist5)
point_on_curve5, = ax5.plot([x_p5], [y_p5], 'ro', label="Point on Curve")

ax5.set_title("Curve and Curvature Function (k(s) = s^2 + 0.75*s - 0.25)")
ax5.set_xlabel("x")
ax5.set_ylabel("y")
ax5.legend()
ax5.axis("equal")
ax5.grid()

# 添加滑块
ax_slider5 = plt.axes([0.2, 0.1, 0.6, 0.03])
slider5 = Slider(ax_slider5, 'Arc Position', -arc_length, arc_length, valinit=arc_position5)

# 更新函数
def update5(val):
    arc_position5 = slider5.val
    x_c5, y_c5, R5, x_p5, y_p5 = osculating_circle(x_vals5, y_vals5, s_vals5, theta_vals5, curvature_s5, arc_position5)
    circle_artist5.center = (x_c5, y_c5)
    circle_artist5.set_radius(R5)
    point_on_curve5.set_data([x_p5], [y_p5])
    fig5.canvas.draw_idle()

slider5.on_changed(update5)

plt.show()