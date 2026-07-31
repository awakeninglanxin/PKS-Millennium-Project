import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad


# 定义R_up和R_down作为新函数
def R_up(t, A_up=1.0, C_up=0.5):
    return 1 - A_up * (1 - np.arccos(np.sin(t))) + C_up


def R_down(t, A_down=0.8, C_down=-0.5, phi=np.pi / 2):
    return A_down * np.sin(t + phi) + C_down


# 计算旋转体的体积
def calculate_volume(R_func, t_min, t_max):
    integrand = lambda t: np.pi * (R_func(t)) ** 2
    volume, _ = quad(integrand, t_min, t_max)
    return volume


# 计算夹层体积
def calculate_layer_volume(R_up_func, R_down_func, t_min, t_max):
    volume_up = calculate_volume(R_up_func, t_min, t_max)
    volume_down = calculate_volume(R_down_func, t_min, t_max)
    return volume_up - volume_down


# 定义体积函数
def volume_function(R_up, R_down):
    return np.pi * (R_up ** 2 - R_down ** 2)


# 设置参数
t_min = 1.5 * np.pi  # 时间的起始点
t_max = 11.5 * np.pi  # 时间的结束点
n_segments = 5  # 分成5段

A_up = 1.0
C_up = 0.5
A_down = 0.8
C_down = -0.5
phi = np.pi / 2

# 定义时间序列
t_values = np.linspace(t_min, t_max, 500)

# 计算R_up和R_down的值
R_up_values = R_up(t_values, A_up, C_up)
R_down_values = R_down(t_values, A_down, C_down, phi)

# 计算体积函数在每个时间点的值
V_values = volume_function(R_up_values, R_down_values)

# 计算体积导数（使用梯度）
V_prime_values = np.gradient(V_values, t_values)

# 分段计算
t_segments = np.linspace(t_min, t_max, n_segments + 1)

# 绘制上下边界曲线和体积导数为零的点
fig, ax = plt.subplots()

for i in range(n_segments):
    t_segment_start = t_segments[i]
    t_segment_end = t_segments[i + 1]

    t_segment = np.linspace(t_segment_start, t_segment_end, 100)
    R_up_segment = R_up(t_segment, A_up, C_up)
    R_down_segment = R_down(t_segment, A_down, C_down, phi)

    V_prime_segment = V_prime_values[(t_values >= t_segment_start) & (t_values <= t_segment_end)]

    ax.plot(t_segment, R_up_segment, 'b-', label='R_up' if i == 0 else "")
    ax.plot(t_segment, R_down_segment, 'r-', label='R_down' if i == 0 else "")

    # 标注导数为零的点
    zero_derivative_points = np.where(np.abs(V_prime_segment) < 1e-3)[0]
    ax.scatter(t_segment[zero_derivative_points], R_up_segment[zero_derivative_points], color='green', s=50,
               label='V\'(t)=0' if i == 0 else "")

    # 打印导数为零的点
    if len(zero_derivative_points) > 0:
        print(f"在第 {i + 1} 段中导数为零的点 t 值：")
        print(t_segment[zero_derivative_points])
    else:
        print(f"在第 {i + 1} 段中没有找到导数为零的点。")

# 设置图形
ax.set_xlabel('t')
ax.set_ylabel('Radius')
ax.set_title('R_up and R_down with V\'(t)=0')
ax.legend()
ax.grid(True)
ax.set_aspect('equal')

# 保存和展示图形
filename = '圆盘夹片上下曲线.png'
fig.savefig(filename, transparent=True)
plt.show()
