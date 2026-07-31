import numpy as np
import matplotlib.pyplot as plt
from mpmath import zeta
import mpmath


def compute_blade_profile(wind_speed, blade_length=50, points=100):
    """
    计算风力涡轮机叶片的最优轮廓
    wind_speed: 风速 (m/s)
    blade_length: 叶片长度 (m)
    points: 计算点数
    """
    mpmath.mp.dps = 15

    # 基于风速调整参数
    t_scale = wind_speed / 10  # 标准化风速

    # 生成参数空间
    t = np.linspace(0, 5 * t_scale, points)

    # 计算黎曼zeta函数值作为基准曲线
    zeta_values = [zeta(complex(0.5, y)) for y in t]

    # 提取实部和虚部，并缩放到实际尺寸
    real_parts = np.array([float(mpmath.re(z)) for z in zeta_values])
    imag_parts = np.array([float(mpmath.im(z)) for z in zeta_values])

    # 缩放到实际叶片尺寸
    x = real_parts * blade_length / np.max(np.abs(real_parts))
    y = imag_parts * blade_length / np.max(np.abs(imag_parts))

    # 计算扭转角（基于当地风速和位置）
    twist_angle = np.arctan2(y, x) * 180 / np.pi * 0.3

    return x, y, twist_angle


def plot_blade_design(wind_speeds=[5, 10, 15]):
    """为不同风速绘制叶片设计"""
    plt.figure(figsize=(15, 10))

    # 绘制叶片轮廓
    plt.subplot(211)
    for wind_speed in wind_speeds:
        x, y, _ = compute_blade_profile(wind_speed)
        plt.plot(x, y, label=f'Wind Speed {wind_speed} m/s')

    plt.title('Wind Turbine Blade Profiles for Different Wind Speeds')
    plt.xlabel('Blade Length (m)')
    plt.ylabel('Blade Width (m)')
    plt.grid(True)
    plt.legend()

    # 绘制扭转角分布
    plt.subplot(212)
    for wind_speed in wind_speeds:
        x, _, twist = compute_blade_profile(wind_speed)
        plt.plot(x, twist, label=f'Wind Speed {wind_speed} m/s')

    plt.title('Blade Twist Angle Distribution')
    plt.xlabel('Blade Length (m)')
    plt.ylabel('Twist Angle (degrees)')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

    # 打印设计参数
    for wind_speed in wind_speeds:
        _, _, twist = compute_blade_profile(wind_speed)
        print(f"\nWind Speed {wind_speed} m/s:")
        print(f"Maximum twist angle: {np.max(twist):.1f}°")
        print(f"Average twist angle: {np.mean(twist):.1f}°")


# 运行设计分析
plot_blade_design()