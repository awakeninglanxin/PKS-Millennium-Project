import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpmath import zeta
import mpmath


def generate_riemann_spiral(t_start=0, t_end=10, points=100):
    """生成基于黎曼zeta函数的螺旋轨迹"""
    mpmath.mp.dps = 15
    t = np.linspace(t_start, t_end, points)

    # 计算关键线上的zeta值
    zeta_values = [zeta(complex(0.5, y)) for y in t]

    # 提取实部和虚部
    x = np.array([float(mpmath.re(z)) for z in zeta_values])
    y = np.array([float(mpmath.im(z)) for z in zeta_values])

    return x, y, t


def create_blade_profile(x, y, t, blade_length=50):
    """基于黎曼螺旋创建叶片轮廓"""
    # 归一化坐标
    x = x / np.max(np.abs(x))
    y = y / np.max(np.abs(y))

    # 计算局部扭转角
    twist_angle = np.arctan2(y, x)

    # 计算径向位置（基于参数t的归一化值）
    r = t / np.max(t) * blade_length

    return x, y, r, twist_angle


def naca4digit(m, p, t, num_points=50):
    """生成NACA 4位数翼型"""
    x = np.linspace(0, 1, num_points)

    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x -
                  0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1015 * x ** 4)

    if m == 0:
        return x, yt, x, -yt

    yc = np.where(x < p,
                  m * x * (2 * p - x) / (p ** 2),
                  m * (1 - x) * (1 + x - 2 * p) / ((1 - p) ** 2))

    dyc_dx = np.where(x < p,
                      2 * m * (p - x) / (p ** 2),
                      2 * m * (p - x) / ((1 - p) ** 2))
    theta = np.arctan(dyc_dx)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    return xu, yu, xl, yl


def plot_riemann_blade(num_sections=30):
    """绘制基于黎曼函数的3D叶片"""
    # 生成黎曼螺旋
    x_spiral, y_spiral, t = generate_riemann_spiral(points=num_sections)
    x_profile, y_profile, r, twist = create_blade_profile(x_spiral, y_spiral, t)

    # 创建3D图
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 为每个径向位置创建翼型截面
    for i in range(num_sections):
        # 基于径向位置调整翼型参数
        relative_r = r[i] / np.max(r)
        m = 0.02 * (1 - relative_r)  # 弯度随半径减小
        p = 0.4
        t = 0.12 * (1 - 0.5 * relative_r)  # 厚度随半径减小

        # 获取翼型坐标
        xu, yu, xl, yl = naca4digit(m, p, t)

        # 缩放翼型（弦长随半径减小）
        scale = (1 - 0.7 * relative_r) * 5  # 调整弦长

        # 应用黎曼螺旋的扭转
        cos_twist = np.cos(twist[i])
        sin_twist = np.sin(twist[i])

        # 计算扭转后的坐标
        x_upper = xu * cos_twist - yu * sin_twist
        y_upper = xu * sin_twist + yu * cos_twist
        x_lower = xl * cos_twist - yl * sin_twist
        y_lower = xl * sin_twist + yl * cos_twist

        # 绘制当前截面
        x_section = np.concatenate([x_upper, x_lower]) * scale
        y_section = np.concatenate([y_upper, y_lower]) * scale
        z_section = np.ones_like(x_section) * r[i]

        ax.plot(x_section, y_section, z_section, 'b-', alpha=0.5)

        # 绘制前缘和后缘线
        if i == 0:
            x_le = []
            y_le = []
            z_le = []
            x_te = []
            y_te = []
            z_te = []

        x_le.append(x_section[0])
        y_le.append(y_section[0])
        z_le.append(z_section[0])
        x_te.append(x_section[len(x_upper)])
        y_te.append(y_section[len(x_upper)])
        z_te.append(z_section[len(x_upper)])

    # 绘制前缘和后缘线
    ax.plot(x_le, y_le, z_le, 'r-', linewidth=2, label='Leading Edge')
    ax.plot(x_te, y_te, z_te, 'g-', linewidth=2, label='Trailing Edge')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Blade Length (m)')
    ax.set_title('Wind Turbine Blade Based on Riemann Zeta Function')
    ax.legend()

    plt.show()

    # 绘制扭转角分布
    plt.figure(figsize=(10, 5))
    plt.plot(r, np.degrees(twist), 'b-')
    plt.xlabel('Radial Position (m)')
    plt.ylabel('Twist Angle (degrees)')
    plt.title('Blade Twist Distribution from Riemann Spiral')
    plt.grid(True)
    plt.show()


# 生成叶片设计
plot_riemann_blade()