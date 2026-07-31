import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建图形和3D坐标轴
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')


# 绘制内PKS螺旋曲线 (M=0.5到M=2)
def plot_pks_curve(ax):
    M_start = 0.5
    M_end = 2.5
    T_values = np.linspace(2 * np.pi * M_start, 2 * np.pi * M_end, 2000)

    x_vals = []
    y_vals = []
    z_vals = []

    for T in T_values:
        # 计算分母部分
        k = math.floor(T / (2 * np.pi))
        remainder = T % (2 * np.pi)
        denominator = k + 1 + remainder / (2 * np.pi)

        # 计算坐标
        x = (1 / math.sqrt(denominator)) * math.cos(T + np.pi)
        y = (math.log(denominator)) / math.log((math.sqrt(5) - 1) / 2)
        z = (1 / math.sqrt(denominator)) * math.sin(T + np.pi)

        x_vals.append(x)
        y_vals.append(y)
        z_vals.append(z)

    ax.plot(x_vals, y_vals, z_vals, 'b-', linewidth=2, alpha=0.8, label=f'内PKS螺旋曲线 (M={M_start}到M={M_end})')

    # 标记起点和终点
    ax.scatter(x_vals[0], y_vals[0], z_vals[0], color='green', s=100, label=f'起点 (M={M_start})')
    ax.scatter(x_vals[-1], y_vals[-1], z_vals[-1], color='red', s=100, label=f'终点 (M={M_end})')


# 绘制过渡曲线
def plot_transition_curve(ax):
    # 定义权重函数
    def w(lambd):
        if lambd == 0 or lambd == 1:
            return 0
        return math.exp(-1 / (lambd * (1 - lambd)))

    # 外蛋壳端点坐标 (根据文档设定)
    x_out = 0.68
    y_out = 1
    z_out = 0

    lambd_values = np.linspace(0, 1, 1000)

    x_vals = []
    y_vals = []
    z_vals = []

    for lambd in lambd_values:
        # 计算T(λ)
        T_lambda = np.pi + 5 * np.pi * lambd

        # 计算分母部分
        k = math.floor(T_lambda / (2 * np.pi))
        remainder = T_lambda % (2 * np.pi)
        denominator = k + 1 + remainder / (2 * np.pi)

        # 计算权重
        weight = w(lambd)

        # 计算坐标
        x = weight * x_out + (1 - weight) * (math.cos(T_lambda + np.pi) / denominator)
        y = weight * y_out + (1 - weight) * (math.log(denominator) / math.log((math.sqrt(5) - 1) / 2))
        z = (1 - weight) * (math.sin(T_lambda + np.pi) / denominator)

        x_vals.append(x)
        y_vals.append(y)
        z_vals.append(z)

    ax.plot(x_vals, y_vals, z_vals, 'r-', linewidth=2, alpha=0.8, label='无限可导的过渡曲线')

    # 标记起点和终点
    ax.scatter(x_vals[0], y_vals[0], z_vals[0], color='orange', s=100, label='外蛋壳端点')
    ax.scatter(x_vals[-1], y_vals[-1], z_vals[-1], color='purple', s=100, label='连接点 (M=2)')


# 绘制两条曲线在同一图中
plot_pks_curve(ax)
plot_transition_curve(ax)

# 设置图形属性
ax.set_xlabel('X轴')
ax.set_ylabel('Y轴')
ax.set_zlabel('Z轴')
ax.set_title('内PKS螺旋曲线与无限可导过渡曲线')
ax.legend()

plt.tight_layout()
plt.show()