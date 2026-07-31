import numpy as np
import matplotlib.pyplot as plt


def red_sawtooth_wave(t, period=1.0, num_periods=6):
    """
    模仿红色曲线波形：类似上移的余弦波从1下降到0，然后垂直跳回1

    参数：
    - t: 时间参数（0到1范围）
    - period: 单个周期的长度比例
    - num_periods: 显示的周期数量
    """
    # 扩展时间范围以显示多个周期

    t_extended = t * num_periods * period
    phi_squared = (1 + np.sqrt(5)) / 2
    phi_squared = phi_squared ** 2
    # 计算在每个周期内的相对位置
    phase = t_extended % period
    phase_normalized = phase / period
    y = 1 + (phi_squared - 1) * 0.5 * (1 + np.cos(np.pi * phase_normalized))
    # 使用余弦函数创建平滑下降（从1到0）
    # 相当于 cos(π * phase_normalized) 从1到-1，然后映射到1到0
    return y


# 生成数据（显示2个完整周期）
t = np.linspace(1, 12, 1000)
y = red_sawtooth_wave(t, period=0.5, num_periods=2)

# 创建与描述图片相似的视觉效果
plt.figure(figsize=(12, 6))

# 绘制浅蓝色网格背景（模仿坐标纸）
plt.grid(True, color='lightblue', alpha=0.7, linestyle='-', linewidth=0.5)

# 绘制红色曲线（模仿图片中的波形）
plt.plot(t, y, color='red', linewidth=2.5, label='红色周期波形')

# 设置坐标轴范围
plt.ylim(-0.1, 4)
plt.xlim(1, 5)

# 添加标题和标签
plt.title('红色周期波形：类似上移余弦波的下降段', fontsize=14, pad=20)
plt.xlabel('时间', fontsize=12)
plt.ylabel('振幅', fontsize=12)

# 标记关键特征点
plt.axhline(y=1, color='gray', linestyle=':', alpha=0.5, label='峰值水平')
plt.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='谷值水平')

# 标记周期边界
for i in range(3):
    x_pos = i * 0.5
    if x_pos <= 1:
        plt.axvline(x=x_pos, color='lightgray', linestyle='--', alpha=0.7)

plt.legend(fontsize=10)
plt.tight_layout()
plt.show()