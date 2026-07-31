import numpy as np  # 导入NumPy库，用于数学计算
import matplotlib.pyplot as plt  # 导入Matplotlib库，用于绘图
from scipy.integrate import quad  # 从SciPy库中导入quad函数，用于积分计算

# 定义中心线函数1
def center_line1(t):
    # 计算中心线1的x和y坐标
    return (np.pi / 2) - np.arccos(np.sin(t)), t + (np.pi / 2)

# 定义中心线函数2
def center_line2(t):
    # 计算中心线2的x和y坐标
    return (3 * np.pi / 2) - np.sin(t), t + (3 * np.pi / 2)

# 计算旋转体的体积
def calculate_volume(W_func, t_min, t_max):
    # 定义积分的被积函数
    integrand = lambda t: np.pi * (W_func(t)) ** 2
    # 计算积分以得到体积
    volume, _ = quad(integrand, t_min, t_max)
    return volume

# 计算夹层体积
def calculate_layer_volume(W_up_func, W_down_func, t_min, t_max):
    # 计算上边界体积
    volume_up = calculate_volume(W_up_func, t_min, t_max)
    # 计算下边界体积
    volume_down = calculate_volume(W_down_func, t_min, t_max)
    # 计算夹层体积（上边界体积 - 下边界体积）
    return volume_up - volume_down

# 计算上下通道宽度变化
def width_up(t, d_up_in, d_up_out, t_min, t_max):
    # 通过插值计算上边界的宽度
    return np.interp(t, [t_min, t_max], [d_up_in, d_up_out])

def width_down(t, d_down_in, d_down_out, t_min, t_max):
    # 通过插值计算下边界的宽度
    return np.interp(t, [t_min, t_max], [d_down_in, d_down_out])

# 设置参数
t1_min = 2 * np.pi - (np.pi / 2)  # 蓝线的起始点
t1_max = 6 * 2 * np.pi - (np.pi / 2)  # 蓝线的结束点
t2_min = 2 * np.pi - (np.pi / 2)  # 红线的起始点
t2_max = 6 * 2 * np.pi - (np.pi / 2)  # 红线的结束点
n_segments = 5  # 分段数

d_up_in = 3.1  # 夹层在起始点上流时的宽度
d_up_out = 2.7  # 夹层在结束点下流时的宽度
d_down_in = 8  # 夹层在起始点上流时的宽度
d_down_out = 6  # 夹层在结束点下流时的宽度

# 分段计算上下边界
t1_segments = np.linspace(t1_min, t1_max, n_segments + 1)  # 计算蓝线分段点
t2_segments = np.linspace(t2_min, t2_max, n_segments + 1)  # 计算红线分段点

# 计算每段（夹层体积）
target_layer_volume = calculate_layer_volume(
    lambda t: width_up(t, d_up_in, d_up_out, t1_min, t1_max),  # 上边界宽度函数
    lambda t: width_down(t, d_down_in, d_down_out, t2_min, t2_max),  # 下边界宽度函数
    t1_min, t1_max
) / n_segments  # 目标体积 = 总体积 / 段数

# 存储每段的体积
layer_volumes = []

# 绘制上下边界
fig, ax = plt.subplots()  # 创建绘图对象

# 遍历每个段进行计算和绘制
for i in range(n_segments):
    t1_start = t1_segments[i]  # 当前段的蓝线起始点
    t1_end = t1_segments[i + 1]  # 当前段的蓝线结束点
    t2_start = t2_segments[i]  # 当前段的红线起始点
    t2_end = t2_segments[i + 1]  # 当前段的红线结束点

    # 定义当前段的上边界和下边界宽度函数
    def W_up(t):
        return width_up(t, d_up_in, d_up_out, t1_start, t1_end)

    def W_down(t):
        return width_down(t, d_down_in, d_down_out, t2_start, t2_end)

    # 计算每段的夹层体积
    current_layer_volume = calculate_layer_volume(W_up, W_down, t1_start, t1_end)
    layer_volumes.append(current_layer_volume)

    # 调整上边界和下边界宽度使体积与目标体积一致
    scaling_factor = np.sqrt(target_layer_volume / current_layer_volume)

    # 计算当前段的中心线坐标
    x_c_segment, y_c_segment1 = center_line1(np.linspace(t1_start, t1_end, 100))
    _, y_c_segment2 = center_line2(np.linspace(t2_start, t2_end, 100))

    # 计算当前段的上边界和下边界y坐标
    y_u = y_c_segment1 + scaling_factor * W_up(np.linspace(t1_start, t1_end, 100)) / 2
    y_l = y_c_segment2 - scaling_factor * W_down(np.linspace(t2_start, t2_end, 100)) / 2

    # 绘制当前段的上下边界
    ax.plot(x_c_segment, y_u, color='blue')
    ax.plot(x_c_segment, y_l, color='red')

# 输出每段的体积
for i, vol in enumerate(layer_volumes, 1):
    print(f"第 {i} 段的体积: {vol}")

# 设置图形
ax.set_xlabel('X')  # 设置x轴标签
ax.set_ylabel('Y')  # 设置y轴标签
ax.set_title('2D Cross-Section of the Disk')  # 设置图形标题
ax.grid(True)  # 显示网格线
ax.set_aspect('equal')  # 设置坐标轴比例相等
filename='圆盘夹片上下曲线.png'  # 设置保存文件名
fig.savefig(filename, transparent=True)  # 保存图形
# 展示图形
plt.show()
