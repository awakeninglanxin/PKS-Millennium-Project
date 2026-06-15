import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import os

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False
phi = (np.sqrt(5) + 1) / 2
phi_squared = phi ** 2
twist_angle = 360 / phi_squared  # 137.5°
t_step = 1 / 9


def calculate_from_z1_z2(z1, z2):
    """基于 z1 和 z2 计算 z0, tan_alpha"""
    if math.isclose(z1 + z2, 0, abs_tol=1e-10):
        raise ValueError("分母 z1 + z2 为零")
    z0 = (z1 ** 2 + z2 ** 2) / (z1 + z2)
    tan_alpha = (-z1 * z2 * (z2 - z1)) / (z1 + z2)
    return z0, tan_alpha


def calculate_z1_z2_from_z0_tan_alpha(z0, tan_alpha):
    """
    从 z0 和 tan_alpha 计算 z1 和 z2
    使用文档中的点斜式公式
    """
    # 解二次方程: z1^2 - z0*z1 - tanα = 0
    discriminant1 = z0 ** 2 + 4 * tan_alpha
    if discriminant1 < 0:
        raise ValueError("无实数解")
    z1 = (z0 - math.sqrt(discriminant1)) / 2

    # 解二次方程: z2^2 - z0*z2 + tanα = 0
    discriminant2 = z0 ** 2 - 4 * tan_alpha
    if discriminant2 < 0:
        raise ValueError("无实数解")
    z2 = (z0 + math.sqrt(discriminant2)) / 2

    return z1, z2


def calculate_volume_optimized(z1, z2, z0, tan_alpha):
    """优化后的蛋形曲线体积计算"""
    alpha = math.atan(tan_alpha)
    cos_alpha = math.cos(alpha)

    # 避免除以零
    if abs(cos_alpha) < 1e-10:
        return 0

    # 计算分子部分
    numerator = z1 + z2

    # 计算分母部分
    denominator = (z1 * z0 - tan_alpha) * (z2 * z0 + tan_alpha)

    # 避免除以零
    if abs(denominator) < 1e-10:
        return 0

    # 计算括号内的表达式
    bracket = numerator / denominator - (1 / (3 * z1 ** 3) + 1 / (3 * z2 ** 3))

    # 计算最终体积
    return abs((math.pi / cos_alpha) * bracket)


def generate_egg_curves_vectorized(z0, tan_alpha, t=0, num_points=1000):
    """使用向量化操作生成蛋形曲线"""
    phi_values = np.linspace(0, 2 * np.pi, num_points)
    amp = 1.0 / (t + 1.0)

    alpha = math.atan(tan_alpha)
    sin_alpha = math.sin(alpha)
    cos_alpha = math.cos(alpha)

    sin_phi = np.sin(phi_values)
    cos_phi = np.cos(phi_values)

    # 计算分母内部项
    denominator_inside = np.sqrt(sin_phi ** 2 + cos_phi ** 2 * cos_alpha ** 2)

    # 计算平方根内部项
    inside_sqrt = z0 ** 2 - (4 * cos_phi * sin_alpha) / denominator_inside

    # 过滤有效点
    valid_mask = inside_sqrt >= 0
    phi_valid = phi_values[valid_mask]
    sin_phi_valid = sin_phi[valid_mask]
    cos_phi_valid = cos_phi[valid_mask]
    denominator_inside_valid = denominator_inside[valid_mask]
    inside_sqrt_valid = inside_sqrt[valid_mask]

    if len(phi_valid) == 0:
        return [], [], [], [], []

    # 计算分母
    denominator = 2 * cos_phi_valid * sin_alpha

    # 避免除以零
    valid_denom_mask = np.abs(denominator) > 1e-10
    phi_valid = phi_valid[valid_denom_mask]
    sin_phi_valid = sin_phi_valid[valid_denom_mask]
    cos_phi_valid = cos_phi_valid[valid_denom_mask]
    denominator_inside_valid = denominator_inside_valid[valid_denom_mask]
    inside_sqrt_valid = inside_sqrt_valid[valid_denom_mask]
    denominator = denominator[valid_denom_mask]

    if len(phi_valid) == 0:
        return [], [], [], [], []

    # 计算半径
    sqrt_val = np.sqrt(inside_sqrt_valid)
    r1 = amp * (z0 + sqrt_val) / denominator
    r2 = amp * (z0 - sqrt_val) / denominator

    # 计算坐标
    x1, y1 = r1 * sin_phi_valid, r1 * cos_phi_valid
    x2, y2 = r2 * sin_phi_valid, r2 * cos_phi_valid

    branch1 = list(zip(x1, y1))
    branch2 = list(zip(x2, y2))

    return branch1, branch2, r1.tolist(), r2.tolist(), phi_valid.tolist()


def rotate_points(points, theta):
    """旋转点集"""
    return [
        (x * math.cos(theta) - y * math.sin(theta),
         x * math.sin(theta) + y * math.cos(theta))
        for x, y in points
    ]


def animate_egg_curves_optimized(z0, tan_alpha, z1, z2, total_rotation=twist_angle):
    """优化后的蛋形曲线动画"""
    fig = plt.figure(figsize=(9, 16))
    plt.rcParams['animation.embed_limit'] = 100
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1])

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    # 设置子图属性
    for ax in [ax1, ax3]:
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax.axvline(0, color='k', linestyle='--', alpha=0.3)
        ax.set_aspect('equal')
        ax.grid(True)

    ax2.set_xlim(0, 2 * np.pi)
    ax2.set_ylim(-np.pi, np.pi)
    ax2.set_aspect('equal')
    ax2.grid(True)

    ax1.set_title('原始蛋形曲线')
    ax2.set_title('r值运算结果')
    ax3.set_title(f'旋转曲线 (总角度: {total_rotation}°)')
    fig.suptitle(f'舒伯格蛋形曲线动画\nz0 = {z0:.4f}, tanα = {tan_alpha:.4f}', fontsize=16, y=0.95)

    # 初始化图形元素
    line1, = ax1.plot([], [], 'b-', lw=1, label='正号分支 (+)')
    line2, = ax1.plot([], [], 'r-', lw=1, label='负号分支 (-)')
    line_multiply, = ax2.plot([], [], 'purple', lw=1, label='两±r相乘')
    line_add, = ax2.plot([], [], 'green', lw=1, label='两±r相加')
    line3_branch1, = ax3.plot([], [], 'b-', alpha=0.7, lw=1, label='正号分支 (+)')
    line3_branch2, = ax3.plot([], [], 'r-', alpha=0.7, lw=1, label='负号分支 (-)')

    for ax in [ax1, ax2, ax3]:
        ax.legend()

    time_text = fig.text(0.5, 0.01, '', ha='center', fontsize=12)
    volume_text = ax1.text(0.02, 0.98, '', transform=ax1.transAxes,
                           va='top', bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    traj_points1, traj_points2 = [], []
    t_values = np.arange(0, 12, t_step)

    # 预计算所有帧
    frames = []
    for t in t_values:
        branch1, branch2, r1_vals, r2_vals, phi_valid = generate_egg_curves_vectorized(z0, tan_alpha, t)
        r_multiply = [r1 * r2 for r1, r2 in zip(r1_vals, r2_vals)] if r1_vals else []
        r_add = [r1 + r2 for r1, r2 in zip(r1_vals, r2_vals)] if r1_vals else []
        frames.append((branch1, branch2, phi_valid, r_multiply, r_add, t))

    def update(frame):
        branch1, branch2, phi_valid, r_multiply, r_add, t = frame

        # 更新左上子图
        if branch1:
            branch1_arr = np.array(branch1)
            line1.set_data(branch1_arr[:, 0], branch1_arr[:, 1])
        else:
            line1.set_data([], [])

        if branch2:
            branch2_arr = np.array(branch2)
            line2.set_data(branch2_arr[:, 0], branch2_arr[:, 1])
        else:
            line2.set_data([], [])

        # 更新右上子图
        if phi_valid and r_multiply and r_add:
            line_multiply.set_data(phi_valid, r_multiply)
            line_add.set_data(phi_valid, r_add)
        else:
            line_multiply.set_data([], [])
            line_add.set_data([], [])

        # 更新下方子图
        if branch1 and branch2:
            theta_deg = (t / 12.0) * total_rotation
            theta_rad = -theta_deg * math.pi / 180.0
            rotated1 = rotate_points(branch1, theta_rad)
            rotated2 = rotate_points(branch2, theta_rad)
            traj_points1.extend(rotated1)
            traj_points2.extend(rotated2)

            if traj_points1:
                traj1_arr = np.array(traj_points1)
                line3_branch1.set_data(traj1_arr[:, 0], traj1_arr[:, 1])
            if traj_points2:
                traj2_arr = np.array(traj_points2)
                line3_branch2.set_data(traj2_arr[:, 0], traj2_arr[:, 1])
        else:
            line3_branch1.set_data([], [])
            line3_branch2.set_data([], [])

        # 更新文本
        # amp = 1.0 / (t + 1.0)
        amp =-1
        z1_scaled, z2_scaled = z1 * amp, z2 * amp
        volume = calculate_volume_optimized(z1_scaled, z2_scaled, z0, tan_alpha)
        time_text.set_text(f't = {t:.2f}, 旋转角度: {theta_deg:.1f}°')
        volume_text.set_text(f'体积 V ≈ {volume:.6f}')

        return line1, line2, line_multiply, line_add, line3_branch1, line3_branch2, time_text, volume_text

    anim = FuncAnimation(fig, update, frames=frames, interval=12, blit=True)
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.close(fig)
    return anim


def main():
    """主函数"""
    print("参数输入方式:")
    print("1. 使用 z1 和 z2 计算参数")
    print("2. 直接设置 z0 和 tan_alpha")
    choice = input("请选择 (1/2): ")

    if choice == "1":
        z1 = float(input("z1 (默认1.0): ") or 1.0)
        z2 = float(input("z2 (默认2.0): ") or 2.0)
        z0, tan_alpha = calculate_from_z1_z2(z1, z2)
    elif choice == "2":
        z0 = float(input("z0 (默认1.6667): ") or 5 / 3)
        tan_alpha = float(input("tan_alpha (默认-0.6667): ") or -2 / 3)
        try:
            z1, z2 = calculate_z1_z2_from_z0_tan_alpha(z0, tan_alpha)
        except Exception as e:
            print(f"计算错误: {e}")
            print("尝试使用默认值 z1=1.0, z2=2.0")
            z1, z2 = 1.0, 2.0
    else:
        z1, z2 = 1.0, 2.0
        z0, tan_alpha = calculate_from_z1_z2(z1, z2)

    print(f"参数: z0={z0:.4f}, tan_alpha={tan_alpha:.4f}, z1={z1:.4f}, z2={z2:.4f}")
    total_rotation = float(input(f"总旋转角度(度, 默认{twist_angle:.1f}): ") or twist_angle)

    print("生成动画中...")
    anim = animate_egg_curves_optimized(z0, tan_alpha, z1, z2, total_rotation)

    save_dir = input("保存目录(回车使用当前目录): ") or os.getcwd()
    save_path = os.path.join(save_dir, "egg_curve.mp4")

    try:
        anim.save(save_path, writer='ffmpeg', fps=2 / t_step, dpi=100)
        print(f"动画已保存至: {save_path}")
    except Exception as e:
        print(f"MP4保存失败: {e}")
        save_path = os.path.join(save_dir, "egg_curve.gif")
        anim.save(save_path, writer='pillow', fps=2 / t_step, dpi=100)
        print(f"GIF已保存至: {save_path}")

    try:
        from IPython.display import HTML
        return HTML(anim.to_jshtml())
    except:
        print("请在Jupyter环境中查看动画")


if __name__ == "__main__":
    main()