import numpy as np
import matplotlib.pyplot as plt


# 定义中心线
def center_line1(t):
    return (np.pi / 2) - np.arccos(np.sin(t)), t + (np.pi / 2)
def center_line2(t):
    return (3*np.pi / 2) - (np.sin(t)), t + (3*np.pi / 2)

# 上下通道宽度变化
def width_up(t, d_up_in, d_up_out, t1_min, t1_max, n_segments=5):
    segment_length = (t1_max - t1_min) / (n_segments - 1)
    segment_index = (t - t1_min) // segment_length
    d_up = d_up_in + ((d_up_out - d_up_in) / (n_segments - 1)) * segment_index
    return d_up


def width_down(t, d_down_in, d_down_out, t1_min, t1_max, n_segments=5):
    segment_length = (t1_max - t1_min) / (n_segments - 1)
    segment_index = (t - t1_min) // segment_length
    d_down = d_down_in + ((d_down_out - d_down_in) / (n_segments - 1)) * segment_index
    return d_down


# 设置参数
t1_min = 2 * np.pi - (np.pi / 2)
t1_max = 6 * 2 * np.pi - (np.pi / 2)
t2_min = 2 * np.pi - (3*np.pi / 2)
t2_max = 6 * 2 * np.pi - (3*np.pi / 2)
n_segments = 5

d_up_in = 3.2
d_up_out = 2.7
d_down_in = 9
d_down_out = 6

# 生成 t 值
t_values = np.linspace(t1_min, t1_max, 500)

# 计算中心线
x_c, y_c = center_line1(t_values)

# 绘制上下边界
fig, ax = plt.subplots()

# 上边界（锯齿形状）
for i in range(n_segments):
    t_segment = np.linspace(t1_min + i * (t1_max - t1_min) / n_segments,
                            t1_min + (i + 1) * (t1_max - t1_min) / n_segments, 100)

    x_c_segment, y_c_segment = center_line1(t_segment)

    d_up = width_up(t_segment, d_up_in, d_up_out, t1_min, t1_max, n_segments)

    y_u = y_c_segment + d_up / 2

    ax.plot(x_c_segment, y_u, color='blue')

# 下边界（正弦波形状）
for i in range(n_segments):
    t_segment = np.linspace(t2_min+2*np.pi + i * (t2_max - t2_min) / n_segments,
                            t2_min+2*np.pi + (i + 1) * (t2_max - t2_min) / n_segments, 100)

    x_c_segment, y_c_segment = center_line2(t_segment)

    d_down = width_down(t_segment, d_down_in, d_down_out, t2_min+2*np.pi, t2_max+2*np.pi, n_segments)

    y_l = y_c_segment - d_down / 2

    ax.plot(x_c_segment-2.5, y_l, color='red')

# 设置图形
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('2D Cross-Section of the Disk')
ax.grid(True)
ax.set_aspect('equal')

# 展示图形
plt.show()
