import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.cm as cm
import os

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False

# 黄金比例参数
phi = (np.sqrt(5) + 1) / 2
total_rotation = 360*7  # 总旋转角度为360°


def fibonacci(n):
    """生成斐波那契数列的第n项"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 1, 1
        for _ in range(2, n):
            a, b = b, a + b
        return b


def calculate_k_b(n):
    """基于斐波那契数列计算k和b参数"""
    fib_n = fibonacci(n + 1)  # F_{n+1}
    fib_n1 = fibonacci(n + 2)  # F_{n+2}
    fib_n2 = fibonacci(n + 3)  # F_{n+3}

    k = fib_n / fib_n1
    b = fib_n2 / fib_n1

    return k, b


def calculate_from_z1_z2(z1, z2):
    """基于 z1 和 z2 计算 z0, tan_alpha"""
    if math.isclose(z1 + z2, 0, abs_tol=1e-10):
        raise ValueError("分母 z1 + z2 为零")
    z0 = (z1 ** 2 + z2 ** 2) / (z1 + z2)
    tan_alpha = (-z1 * z2 * (z2 - z1)) / (z1 + z2)
    return z0, tan_alpha


def calculate_z1_z2_from_z0_tan_alpha(z0, tan_alpha):
    """从 z0 和 tan_alpha 计算 z1 和 z2"""
    discriminant1 = z0 ** 2 + 4 * tan_alpha
    if discriminant1 < 0:
        raise ValueError("无实数解")
    z1 = (z0 - math.sqrt(discriminant1)) / 2

    discriminant2 = z0 ** 2 - 4 * tan_alpha
    if discriminant2 < 0:
        raise ValueError("无实数解")
    z2 = (z0 + math.sqrt(discriminant2)) / 2

    return z1, z2


def generate_egg_curve_vectorized(z0, tan_alpha, amp=1.0, num_points=1000):
    """生成蛋形曲线"""
    phi_values = np.linspace(0, 2 * np.pi, num_points)

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
    inside_sqrt_valid = inside_sqrt[valid_mask]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    # 计算分母
    denominator = 2 * cos_phi_valid * sin_alpha

    # 避免除以零
    valid_denom_mask = np.abs(denominator) > 1e-10
    phi_valid = phi_valid[valid_denom_mask]
    sin_phi_valid = sin_phi_valid[valid_denom_mask]
    cos_phi_valid = cos_phi_valid[valid_denom_mask]
    inside_sqrt_valid = inside_sqrt_valid[valid_denom_mask]
    denominator = denominator[valid_denom_mask]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    # 计算半径（只取负号分支，即蛋形曲线内部）
    sqrt_val = np.sqrt(inside_sqrt_valid)
    r = amp * (z0 - sqrt_val) / denominator

    # 计算坐标
    x, y = r * sin_phi_valid, r * cos_phi_valid

    return x, y


def rotate_points(x_coords, y_coords, theta):
    """旋转点集"""
    x_rotated = x_coords * math.cos(theta) - y_coords * math.sin(theta)
    y_rotated = x_coords * math.sin(theta) + y_coords * math.cos(theta)
    return x_rotated, y_rotated


def calculate_auto_scale(all_curves_x, all_curves_y, margin_ratio=0.1):
    """计算自适应坐标轴范围"""
    if not all_curves_x or not all_curves_y:
        return -1.5, 1.5, -1.5, 1.5

    # 将所有曲线的点连接起来
    all_x = np.concatenate(all_curves_x) if len(all_curves_x) > 0 else np.array([])
    all_y = np.concatenate(all_curves_y) if len(all_curves_y) > 0 else np.array([])

    if len(all_x) == 0 or len(all_y) == 0:
        return -1.5, 1.5, -1.5, 1.5

    x_min, x_max = np.min(all_x), np.max(all_x)
    y_min, y_max = np.min(all_y), np.max(all_y)

    # 计算中心点
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2

    # 计算范围
    x_range = x_max - x_min
    y_range = y_max - y_min

    # 使用最大范围确保等比例
    max_range = max(x_range, y_range)

    if max_range == 0:
        max_range = 1

    # 添加边距
    margin = max_range * margin_ratio

    # 计算新的范围
    new_range = max_range + 2 * margin

    # 计算新的边界
    x_min_new = x_center - new_range / 2
    x_max_new = x_center + new_range / 2
    y_min_new = y_center - new_range / 2
    y_max_new = y_center + new_range / 2

    return x_min_new, x_max_new, y_min_new, y_max_new


def clamp_value(value, min_val=0.0, max_val=1.0):
    """确保值在指定范围内，避免浮点数精度问题"""
    return max(min_val, min(value, max_val))


def create_egg_curves_gif(n_max=72, gif_filename="fibonacci_egg_curves.gif", dpi=100, fps=10):
    """创建蛋形曲线的GIF动画，每一帧对应一个图层"""
    fig, ax = plt.subplots(figsize=(12, 10))

    # 设置自适应显示
    ax.set_aspect('equal', 'box')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_title(
        f'斐波那契蛋形曲线 (n=1-{n_max}) - Rainbow渐变色\n总旋转角度: {total_rotation}°\n振幅方案: amp = sqrt(n)',
        fontsize=16, pad=20)
    ax.set_xlabel('X轴', fontsize=12)
    ax.set_ylabel('Y轴', fontsize=12)

    # 预计算所有曲线的参数
    print(f"预计算 {n_max} 个蛋形曲线的参数...")
    curve_params = []
    for n in range(1, n_max + 1):
        k, b = calculate_k_b(n)
        z0, tan_alpha = b, k
        amp = math.sqrt(n)  # sqrt(n) 振幅方案
        curve_params.append({
            'n': n,
            'z0': z0,
            'tan_alpha': tan_alpha,
            'amp': amp,
            'rotation_factor': (n - 1) / (n_max - 1) if n_max > 1 else 0
        })

    # 预计算所有曲线
    print("预计算所有曲线...")
    frames_data = []
    for i, param in enumerate(curve_params):
        x, y = generate_egg_curve_vectorized(
            param['z0'], param['tan_alpha'], param['amp']
        )
        frames_data.append((x, y, param))

    # 计算整体坐标轴范围
    all_x = []
    all_y = []
    for frame in frames_data:
        x, y, _ = frame
        if len(x) > 0 and len(y) > 0:
            all_x.append(x)
            all_y.append(y)

    if all_x and all_y:
        x_min, x_max, y_min, y_max = calculate_auto_scale(all_x, all_y, margin_ratio=0.2)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
    else:
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)

    # 创建Rainbow渐变色映射
    rainbow_cmap = cm.get_cmap('rainbow')

    # 存储所有已绘制的曲线
    drawn_lines = []

    def init():
        """初始化函数，清空所有已绘制的曲线"""
        for line in drawn_lines:
            line.remove()
        drawn_lines.clear()
        ax.set_title(
            f'斐波那契蛋形曲线 (n=1-{n_max}) - Rainbow渐变色\n总旋转角度: {total_rotation}°\n振幅方案: amp = sqrt(n)',
            fontsize=16, pad=20)
        return []

    def update(frame_idx):
        """更新函数，绘制新的一帧"""
        x, y, param = frames_data[frame_idx]

        if len(x) > 0 and len(y) > 0:
            # 计算旋转角度
            theta_deg = param['rotation_factor'] * total_rotation
            theta_rad = -theta_deg * math.pi / 180.0

            # 旋转点
            x_rotated, y_rotated = rotate_points(x, y, theta_rad)

            # 计算颜色
            n_ratio = (param['n'] - 1) / (n_max - 1) if n_max > 1 else 0
            current_color = rainbow_cmap(n_ratio)

            # 绘制当前曲线（作为新的图层）
            line, = ax.plot(x_rotated, y_rotated, '-', linewidth=1.8, alpha=1.0,
                            color=current_color, label=f'n={param["n"]}')
            drawn_lines.append(line)

            # 更新标题显示当前进度
            ax.set_title(
                f'斐波那契蛋形曲线 (n=1-{param["n"]}/{n_max}) - Rainbow渐变色\n总旋转角度: {total_rotation}°\n振幅方案: amp = sqrt(n)',
                fontsize=16, pad=20)

            # 添加信息文本
            info_text = f"当前曲线: n={param['n']}, 旋转角度: {theta_deg:.1f}°\n振幅: {param['amp']:.3f}\n已绘制曲线: {frame_idx + 1}/{n_max}"

            # 移除旧的文本（如果有的话）
            for txt in ax.texts:
                txt.remove()

            ax.text(0.02, 0.98, info_text,
                    transform=ax.transAxes, fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

        return drawn_lines

    # 添加颜色条
    sm = cm.ScalarMappable(cmap=rainbow_cmap, norm=plt.Normalize(1, n_max))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
    cbar.set_label('n值')

    # 创建动画
    print("创建动画...")
    anim = FuncAnimation(fig, update, frames=len(frames_data),
                         init_func=init, interval=200, blit=True, repeat=False)

    # 保存GIF
    print(f"保存GIF到: {gif_filename}")
    writer = PillowWriter(fps=fps)
    anim.save(gif_filename, writer=writer, dpi=dpi)
    print(f"GIF保存完成! 文件大小: {os.path.getsize(gif_filename) / 1024:.2f} KB")

    plt.tight_layout()
    plt.close(fig)  # 关闭图形以释放内存

    return anim, curve_params, gif_filename


def main():
    """主函数"""
    print("=" * 60)
    print("斐波那契蛋形曲线GIF生成器")
    print("=" * 60)

    # 获取用户输入的n值
    try:
        n_input = input("请输入n值 (默认72, 按Enter使用默认值): ").strip()
        n_max = int(n_input) if n_input else 72
    except ValueError:
        print("输入无效，使用默认值72")
        n_max = 72

    if n_max < 1:
        print("n值必须大于0，使用默认值72")
        n_max = 72

    # 获取GIF文件名
    gif_filename = input("请输入GIF文件名 (默认: fibonacci_egg_curves.gif): ").strip()
    if not gif_filename:
        gif_filename = "fibonacci_egg_curves.gif"
    elif not gif_filename.endswith('.gif'):
        gif_filename += '.gif'

    # 获取帧率
    try:
        fps_input = input("请输入GIF帧率 (默认10, 按Enter使用默认值): ").strip()
        fps = int(fps_input) if fps_input else 10
    except ValueError:
        print("输入无效，使用默认值10")
        fps = 10

    print(f"\n将生成 {n_max} 个斐波那契蛋形曲线的GIF动画")
    print(f"参数生成规则: k = F_{{n+1}}/F_{{n+2}}, b = F_{{n+3}}/F_{{n+2}}")
    print(f"振幅方案: amp = sqrt(n)")
    print(f"旋转方案: 均匀分布在0°到{total_rotation}°之间")
    print(f"GIF帧率: {fps} fps")
    print(f"输出文件: {gif_filename}")

    # 显示前几个参数示例
    print("\n前5个曲线的参数示例:")
    for n in range(1, min(6, n_max + 1)):
        k, b = calculate_k_b(n)
        amp = math.sqrt(n)
        print(f"n={n}: k={k:.6f}, b={b:.6f}, amp={amp:.6f}")

    if n_max > 5:
        print(f"... 共{n_max}个曲线")

    print("\n生成GIF动画中...")
    anim, curve_params, output_file = create_egg_curves_gif(n_max, gif_filename, fps=fps)

    # 显示所有曲线参数
    print("\n所有曲线参数汇总:")
    print("n\tk\t\tb\t\t振幅(amp)")
    print("-" * 50)
    for param in curve_params:
        n = param['n']
        k = param['tan_alpha']
        b = param['z0']
        amp = param['amp']
        print(f"{n}\t{k:.6f}\t{b:.6f}\t{amp:.6f}")

    print(f"\nGIF动画已保存到: {output_file}")
    print(f"文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
    print("\n程序结束")


if __name__ == "__main__":
    main()
