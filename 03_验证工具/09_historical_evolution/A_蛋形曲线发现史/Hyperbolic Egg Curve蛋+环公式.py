import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import ezdxf
from mpl_toolkits.mplot3d import Axes3D

# DXF 文件创建
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

num_p =500

def hyperbolic_egg_curve(alpha_deg, z0, num_points=num_p):
    alpha_val = alpha_deg * np.pi / 180  # Example value for alpha (in radians)
    phi = np.linspace(0, 2 * np.pi, num_points)
    # Calculate r using the given formula
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    term_under_sqrt = z0 ** 2 - (4 * cos_phi * np.sin(alpha_val)) / (sin_phi ** 2 + cos_phi ** 2 * np.cos(alpha_val) ** 2)
    term_under_sqrt = np.where(term_under_sqrt >= 0, term_under_sqrt, 0)  # Ensure no negative values under sqrt
    with np.errstate(divide='ignore', invalid='ignore'):
        r_minus = np.where(cos_phi != 0, (1 / (2 * cos_phi * np.sin(alpha_val))) * (z0 - np.sqrt(term_under_sqrt)), 0)
    # Calculate x and y for the solution
    return r_minus * sin_phi, r_minus * cos_phi

# Initial Parameters
alpha_deg = 30
alpha_val = alpha_deg * np.pi / 180  # Example value for alpha (in radians)
z0 = 5 / 3  # Example value for z0
a1, b1 = hyperbolic_egg_curve(alpha_deg, z0, num_points=num_p)
torus = []
t = np.linspace(0, 2 * np.pi, num_p)

# 修改后的 parametric_curve_3d 函数
def parametric_curve_3d(a, b, alpha_deg, z0, c, d):
    global ax_3d
    ax_3d.clear()  # 清除之前的绘图

    # 重新计算alpha值
    alpha_val = alpha_deg * np.pi / 180
    a1, b1 = hyperbolic_egg_curve(alpha_deg, z0, num_points=num_p)

    x_vals = []
    y_vals = []
    z_vals = []

    for i in range(num_p):
        # Parametric equations from the image
        x = (b * b1[i] + a * a1[i] * np.cos(t[i])) * np.cos(c * t[i])
        y = (b * b1[i] + a * a1[i] * np.cos(t[i])) * np.sin(c * t[i])
        z = d * np.sin(t[i])
        torus.append([x, y, z])
        x_vals.append(x)
        y_vals.append(y)
        z_vals.append(z)

    # Plotting the 3D curve
    ax_3d.plot3D(x_vals, y_vals, z_vals, label='3D Parametric Curve', color='b')
    ax_3d.set_xlabel('x(t)')
    ax_3d.set_ylabel('y(t)')
    ax_3d.set_zlabel('z(t)')
    ax_3d.set_title('3D Parametric Curve')
    ax_3d.legend()
    ax_3d.axis('equal')
    fig.canvas.draw_idle()

# Plotting setup
fig = plt.figure(figsize=(14, 7))
ax_2d = fig.add_subplot(1, 2, 1)
ax_3d = fig.add_subplot(1, 2, 2, projection='3d')
plt.subplots_adjust(left=0.1, bottom=0.3, wspace=0.4)

# Plotting the 2D Hyperbolic Egg Curve
ax_2d.set_xlabel('x')
ax_2d.set_ylabel('y')
ax_2d.set_title('Hyperbolic Egg Curve')
ax_2d.axhline(0, color='black', lw=0.5)
ax_2d.axvline(0, color='black', lw=0.5)
ax_2d.grid(True)
ax_2d.axis('equal')

def plot_hyperbolic_egg_curve(alpha_deg, z0):
    x_minus, y_minus = hyperbolic_egg_curve(alpha_deg, z0, num_points=num_p)
    ax_2d.clear()
    ax_2d.plot(x_minus, y_minus, label='Hyperbolic Egg Curve (-)', color='r')
    ax_2d.set_xlabel('x')
    ax_2d.set_ylabel('y')
    ax_2d.set_title('Hyperbolic Egg Curve')
    ax_2d.axhline(0, color='black', lw=0.5)
    ax_2d.axvline(0, color='black', lw=0.5)
    ax_2d.grid(True)
    ax_2d.legend()
    ax_2d.axis('equal')
    fig.canvas.draw_idle()
    return x_minus, y_minus

a = 1
b = 1
c = 5  # Example value for c

d = 3
plot_hyperbolic_egg_curve(alpha_deg, z0)
parametric_curve_3d(a, b, alpha_val, z0, c, d)

# Slider setup
ax_alpha_deg = plt.axes([0.1, 0.25, 0.65, 0.03])
ax_z0 = plt.axes([0.1, 0.2, 0.65, 0.03])
ax_c = plt.axes([0.1, 0.15, 0.65, 0.03])
ax_a = plt.axes([0.1, 0.1, 0.65, 0.03])
ax_b = plt.axes([0.1, 0.05, 0.65, 0.03])

slider_a = Slider(ax_a, 'a', 1, 5.0, valinit=a, valstep=0.25)
slider_b = Slider(ax_b, 'b', 1, 5.0, valinit=b, valstep=0.25)
slider_alpha_deg = Slider(ax_alpha_deg, 'alpha_deg', 0, 90, valinit=alpha_deg)
slider_z0 = Slider(ax_z0, 'z0', 0.000001, 4, valinit=z0)
slider_c = Slider(ax_c, 'c', 1, 30, valinit=c, valstep=1)

def update(val):
    # 获取滑动条的值
    alpha_deg = slider_alpha_deg.val  # 保持为角度制
    a = slider_a.val
    b = slider_b.val
    z0_val = slider_z0.val
    c_val = slider_c.val

    # 更新2D图
    plot_hyperbolic_egg_curve(alpha_deg, z0_val)
    # 更新3D图
    parametric_curve_3d(a, b, alpha_deg, z0_val, c_val, d)

slider_alpha_deg.on_changed(update)
slider_z0.on_changed(update)
slider_c.on_changed(update)
slider_a.on_changed(update)
slider_b.on_changed(update)

plt.show()