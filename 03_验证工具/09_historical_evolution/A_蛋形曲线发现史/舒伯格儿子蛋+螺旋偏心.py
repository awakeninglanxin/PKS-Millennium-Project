import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from matplotlib.widgets import Slider, TextBox

# 设置字体为 SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 参数设置
b = 5 / 3  # 固定参数
f = np.arctan(2 / 3)  # 固定角度
phi = (np.sqrt(5) - 1) / 2  # 黄金比例

# 初始化动态参数
spin_n = 108
phase = 720
period_max = 2 * np.pi
line_thickness = 0.5
clarity = 3000

# 创建子图和滑动条
fig, ax = plt.subplots(figsize=(6, 6))
plt.subplots_adjust(left=0.1, bottom=0.45)


# 计算曲线的函数
def calculate_curve(spin_n, phase, period_max, line_thickness, clarity):
    t_positive = np.linspace(-np.pi / 2, np.pi / 2, 300)
    t_negative = np.linspace(np.pi / 2, -np.pi / 2, 300)
    period_pos = np.linspace(0, period_max / 2, int(clarity))
    period_neg = np.linspace(period_max / 2, period_max, int(clarity))

    # 计算正半部分
    x_pos = []
    y_pos = []
    for t, t1 in zip(t_positive, period_pos):
        value = 1 / (b + t * np.sin(f)) ** 2 - (t * np.cos(f)) ** 2
        if value >= 0:
            cos_form = phi ** (t1 / (phase * np.pi / 180)) * -np.cos(t1 * spin_n)
            sin_form = phi ** (t1 / (phase * np.pi / 180)) * np.sin(t1 * spin_n)
            x_pos.append(t * cos_form)
            y_pos.append(np.sqrt(value) * sin_form)

    # 计算负半部分
    x_neg = []
    y_neg = []
    for t, t1 in zip(t_negative, period_neg):
        value = 1 / (b + t * np.sin(f)) ** 2 - (t * np.cos(f)) ** 2
        if value >= 0:
            cos_form = phi ** (t1 / (phase * np.pi / 180)) * -np.cos(t1 * spin_n)
            sin_form = phi ** (t1 / (phase * np.pi / 180)) * np.sin(t1 * spin_n)
            x_neg.append(t * cos_form)
            y_neg.append(-np.sqrt(value) * sin_form)

    # 绘制图形
    ax.clear()

    # 颜色渐变
    colors_pos = plt.cm.hsv(np.linspace(0, 1, len(x_pos)))
    colors_neg = plt.cm.hsv(np.linspace(0, 1, len(x_neg)))

    # 绘制正半部分
    for i in range(1, len(x_pos)):
        ax.plot(x_pos[i - 1:i + 1], y_pos[i - 1:i + 1], color=colors_pos[i], lw=line_thickness)

    # 绘制负半部分
    for i in range(1, len(x_neg)):
        ax.plot(x_neg[i - 1:i + 1], y_neg[i - 1:i + 1], color=colors_neg[i], lw=line_thickness)

    # 插值平滑过渡
    num_interp_points = 50
    x_last = [x_pos[-1], x_neg[-1]]
    y_last = [y_pos[-1], y_neg[-1]]
    interp_x = np.linspace(x_pos[-1], x_neg[-1], num=num_interp_points)
    interp_func = interp1d(x_last, y_last, kind='linear')
    interp_y = interp_func(interp_x)
    ax.plot(interp_x, interp_y, color=colors_pos[-1], lw=line_thickness)

    # 设置轴比例
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('蛋形摆线曲线')
    ax.axis('equal')
    ax.legend(['正半部分', '负半部分'])
    plt.draw()


# 初始化绘图
calculate_curve(spin_n, phase, period_max, line_thickness, clarity)

# 创建滑动条
ax_spin_n = plt.axes([0.1, 0.3, 0.65, 0.03])
ax_phase = plt.axes([0.1, 0.25, 0.65, 0.03])
ax_period_max = plt.axes([0.1, 0.2, 0.65, 0.03])
ax_line_thickness = plt.axes([0.1, 0.15, 0.65, 0.03])
ax_clarity = plt.axes([0.1, 0.1, 0.65, 0.03])

slider_spin_n = Slider(ax_spin_n, 'Spin N', 1, 6000, valinit=spin_n, valstep=1)
slider_phase = Slider(ax_phase, 'Phase', 30, 360 * 2, valinit=phase, valstep=1)
slider_period_max = Slider(ax_period_max, 'Period Max', np.pi, 9 * np.pi, valinit=period_max)
slider_line_thickness = Slider(ax_line_thickness, 'Line Thickness', 0.1, 1.0, valinit=line_thickness)
slider_clarity = Slider(ax_clarity, 'Clarity', 100, 10000, valinit=clarity, valstep=1)

# 创建文本框
axbox_spin_n = plt.axes([0.78, 0.3, 0.1, 0.03])
text_box_spin_n = TextBox(axbox_spin_n, '', initial=str(spin_n))

axbox_phase = plt.axes([0.78, 0.25, 0.1, 0.03])
text_box_phase = TextBox(axbox_phase, '', initial=str(phase))

axbox_period_max = plt.axes([0.78, 0.2, 0.1, 0.03])
text_box_period_max = TextBox(axbox_period_max, '', initial=str(period_max))

axbox_line_thickness = plt.axes([0.78, 0.15, 0.1, 0.03])
text_box_line_thickness = TextBox(axbox_line_thickness, '', initial=str(line_thickness))

axbox_clarity = plt.axes([0.78, 0.1, 0.1, 0.03])
text_box_clarity = TextBox(axbox_clarity, '', initial=str(clarity))


# 滑动条更新函数
def update(val):
    spin_n = slider_spin_n.val
    phase = slider_phase.val
    period_max = slider_period_max.val
    line_thickness = slider_line_thickness.val
    clarity = slider_clarity.val

    # 更新文本框的值
    text_box_spin_n.set_val(str(spin_n))
    text_box_phase.set_val(str(phase))
    text_box_period_max.set_val(str(period_max))
    text_box_line_thickness.set_val(str(line_thickness))
    text_box_clarity.set_val(str(clarity))

    calculate_curve(spin_n, phase, period_max, line_thickness, clarity)


# 文本框更新函数
def update_from_text_box():
    try:
        spin_n = float(text_box_spin_n.text)
        phase = float(text_box_phase.text)
        period_max = float(text_box_period_max.text)
        line_thickness = float(text_box_line_thickness.text)
        clarity = float(text_box_clarity.text)

        # 设置滑动条的值
        slider_spin_n.set_val(spin_n)
        slider_phase.set_val(phase)
        slider_period_max.set_val(period_max)
        slider_line_thickness.set_val(line_thickness)
        slider_clarity.set_val(clarity)
    except ValueError:
        pass  # 忽略无效输入


# 将滑动条与更新函数绑定
slider_spin_n.on_changed(update)
slider_phase.on_changed(update)
slider_period_max.on_changed(update)
slider_line_thickness.on_changed(update)
slider_clarity.on_changed(update)

# 将文本框与更新函数绑定
text_box_spin_n.on_submit(lambda text: update_from_text_box())
text_box_phase.on_submit(lambda text: update_from_text_box())
text_box_period_max.on_submit(lambda text: update_from_text_box())
text_box_line_thickness.on_submit(lambda text: update_from_text_box())
text_box_clarity.on_submit(lambda text: update_from_text_box())

# 显示图形
plt.show()
