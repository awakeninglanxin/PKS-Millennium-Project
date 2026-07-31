import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.cm as cm
import os
import sys

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False

# 黄金比例参数
phi = (np.sqrt(5) + 1) / 2
total_rotation = 0  # 总旋转角度为2520° (7圈)


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


def create_egg_curves_gif_with_pause(n_max=72, gif_filename="fibonacci_egg_curves_7turns_with_pause.gif",
                                     dxf_filename="fibonacci_egg_curves.dxf", dpi=100, fps=10,
                                     amp_func=None):
    """
    创建蛋形曲线的GIF动画，每一帧对应一个图层，从n_max开始递减，最后停顿20帧，并导出DXF文件
    """
    # 修复文件名中的非法字符
    gif_filename = gif_filename.replace("<", "").replace(">", "")
    dxf_filename = dxf_filename.replace("<", "").replace(">", "")

    # 默认振幅函数：sqrt(n)
    if amp_func is None:
        amp_func = lambda n: math.sqrt(n)

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal', 'box')
    ax.grid(True, alpha=0.3, linestyle='--')

    # 获取振幅函数名称用于标题
    amp_func_name = amp_func.__name__ if hasattr(amp_func, '__name__') else str(amp_func)
    if 'lambda' in amp_func_name:
        amp_func_name = 'lambda表达式'

    ax.set_title(
        f'斐波那契蛋形曲线 (n={n_max}→1) - Rainbow渐变色\n总旋转角度: {total_rotation}° ({int(total_rotation / 360)}圈)\n振幅方案: amp = {amp_func_name}',
        fontsize=16, pad=20)
    ax.set_xlabel('X轴', fontsize=12)
    ax.set_ylabel('Y轴', fontsize=12)

    # 预计算所有曲线的参数（从n_max到1递减）
    curve_params = []
    for n in range(n_max, 0, -1):
        k = fibonacci(n + 1) / fibonacci(n + 2)
        b = fibonacci(n + 3) / fibonacci(n + 2)
        z0, tan_alpha = b, k
        amp = amp_func(n)
        rotation_factor = (n_max - n) / (n_max - 1) if n_max > 1 else 0
        curve_params.append({
            'n': n,
            'z0': z0,
            'tan_alpha': tan_alpha,
            'amp': amp,
            'rotation_factor': rotation_factor
        })

    # 预计算所有曲线并找到最大边界
    frames_data = []
    all_x_min = []
    all_x_max = []
    all_y_min = []
    all_y_max = []

    for i, param in enumerate(curve_params):
        x, y = generate_egg_curve_vectorized(
            param['z0'], param['tan_alpha'], param['amp']
        )
        if len(x) > 0 and len(y) > 0:
            # 计算旋转后的坐标
            theta_rad = -param['rotation_factor'] * total_rotation * math.pi / 180.0
            x_rotated, y_rotated = rotate_points(x, y, theta_rad)

            # 记录边界
            all_x_min.append(np.min(x_rotated))
            all_x_max.append(np.max(x_rotated))
            all_y_min.append(np.min(y_rotated))
            all_y_max.append(np.max(y_rotated))

        frames_data.append((x, y, param))

    # 将最后一帧复制20次，创建停顿效果
    pause_frames_count = 20
    for _ in range(pause_frames_count):
        frames_data.append(frames_data[-1])

    total_frames = len(frames_data)

    # 计算自适应坐标轴范围（基于所有旋转后的曲线）
    if all_x_min:  # 确保有有效数据
        x_min = min(all_x_min)
        x_max = max(all_x_max)
        y_min = min(all_y_min)
        y_max = max(all_y_max)

        # 添加20%边距
        x_margin = (x_max - x_min) * 0.2
        y_margin = (y_max - y_min) * 0.2
        x_min -= x_margin
        x_max += x_margin
        y_min -= y_margin
        y_max += y_margin

        # 确保坐标轴范围合理
        if x_max - x_min < 1e-6:
            x_min, x_max = -10, 10
        if y_max - y_min < 1e-6:
            y_min, y_max = -10, 10
    else:
        x_min, x_max, y_min, y_max = -20, 20, -20, 20

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # 设置合理的刻度
    x_range = x_max - x_min
    y_range = y_max - y_min
    max_range = max(x_range, y_range)
    tick_step = 2 if max_range <= 30 else 5 if max_range <= 60 else 10 if max_range <= 120 else 20
    x_ticks = np.arange(math.floor(x_min / tick_step) * tick_step,
                        math.ceil(x_max / tick_step) * tick_step + tick_step, tick_step)
    y_ticks = np.arange(math.floor(y_min / tick_step) * tick_step,
                        math.ceil(y_max / tick_step) * tick_step + tick_step, tick_step)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)

    # 存储所有已绘制的曲线
    drawn_lines = []

    def init():
        for line in drawn_lines:
            line.remove()
        drawn_lines.clear()
        ax.set_title(
            f'斐波那契蛋形曲线 (n={n_max}→1) - Rainbow渐变色\n总旋转角度: {total_rotation}° ({int(total_rotation / 360)}圈)\n振幅方案: amp = {amp_func_name}',
            fontsize=16, pad=20)
        return []

    def update(frame_idx):
        x, y, param = frames_data[frame_idx]

        if len(x) > 0 and len(y) > 0:
            theta_deg = param['rotation_factor'] * total_rotation
            theta_rad = -theta_deg * math.pi / 180.0
            x_rotated, y_rotated = rotate_points(x, y, theta_rad)

            n_ratio = (n_max - param['n']) / (n_max - 1) if n_max > 1 else 0
            current_color = plt.colormaps['rainbow'](n_ratio)

            line, = ax.plot(x_rotated, y_rotated, '-', linewidth=1.8, alpha=1.0,
                            color=current_color, label=f'n={param["n"]}')
            drawn_lines.append(line)

            is_pause_frame = frame_idx >= n_max
            title_text = f'斐波那契蛋形曲线 (n={n_max}→1) - Rainbow渐变色\n总旋转角度: {total_rotation}° ({int(total_rotation / 360)}圈)\n振幅方案: amp = {amp_func_name}'
            if is_pause_frame:
                title_text += f"\n(停顿帧: {frame_idx - n_max + 1}/{pause_frames_count})"
            ax.set_title(title_text, fontsize=16, pad=20)

            info_text = f"最终曲线: n={param['n']}, 旋转角度: {theta_deg:.1f}°\n振幅: {param['amp']:.3f}\n已绘制曲线: {n_max}/{n_max} (停顿中...)" if is_pause_frame else f"当前曲线: n={param['n']}, 旋转角度: {theta_deg:.1f}°\n振幅: {param['amp']:.3f}\n已绘制曲线: {frame_idx + 1}/{n_max}"

            for txt in ax.texts:
                txt.remove()

            ax.text(0.02, 0.98, info_text,
                    transform=ax.transAxes, fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

        return drawn_lines

    # 添加颜色条
    try:
        sm = cm.ScalarMappable(cmap=plt.colormaps['rainbow'], norm=plt.Normalize(1, n_max))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label('n值')
    except Exception as e:
        print(f"颜色条创建失败: {e}")

    # 创建动画
    anim = FuncAnimation(fig, update, frames=total_frames,
                         init_func=init, interval=200, blit=True, repeat=False)

    # 保存GIF
    writer = PillowWriter(fps=fps)
    try:
        anim.save(gif_filename, writer=writer, dpi=dpi, savefig_kwargs={'metadata': {'loop': 0}})
    except Exception as e:
        anim.save(gif_filename, writer=writer, dpi=dpi)

    # 导出DXF文件
    dxf_success = export_curves_to_dxf(curve_params, frames_data[:n_max], total_rotation, n_max, dxf_filename)

    plt.tight_layout()
    plt.close(fig)

    return anim, curve_params, gif_filename, dxf_success, dxf_filename


# 辅助函数定义
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


def generate_egg_curve_vectorized(z0, tan_alpha, amp=1.0, num_points=1000):
    """生成蛋形曲线"""
    phi_values = np.linspace(0, 2 * np.pi, num_points)

    alpha = math.atan(tan_alpha)
    sin_alpha = math.sin(alpha)
    cos_alpha = math.cos(alpha)

    sin_phi = np.sin(phi_values)
    cos_phi = np.cos(phi_values)

    denominator_inside = np.sqrt(sin_phi ** 2 + cos_phi ** 2 * cos_alpha ** 2)
    inside_sqrt = z0 ** 2 - (4 * cos_phi * sin_alpha) / denominator_inside

    valid_mask = inside_sqrt >= 0
    phi_valid = phi_values[valid_mask]
    sin_phi_valid = sin_phi[valid_mask]
    cos_phi_valid = cos_phi[valid_mask]
    inside_sqrt_valid = inside_sqrt[valid_mask]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    denominator = 2 * cos_phi_valid * sin_alpha
    valid_denom_mask = np.abs(denominator) > 1e-10
    phi_valid = phi_valid[valid_denom_mask]
    sin_phi_valid = sin_phi_valid[valid_denom_mask]
    cos_phi_valid = cos_phi_valid[valid_denom_mask]
    inside_sqrt_valid = inside_sqrt_valid[valid_denom_mask]
    denominator = denominator[valid_denom_mask]

    if len(phi_valid) == 0:
        return np.array([]), np.array([])

    sqrt_val = np.sqrt(inside_sqrt_valid)
    r = amp * (z0 - sqrt_val) / denominator
    x, y = r * sin_phi_valid, r * cos_phi_valid

    return x, y


def rotate_points(x_coords, y_coords, theta):
    """旋转点集"""
    x_rotated = x_coords * math.cos(theta) - y_coords * math.sin(theta)
    y_rotated = x_coords * math.sin(theta) + y_coords * math.cos(theta)
    return x_rotated, y_rotated


def export_curves_to_dxf(curve_params, frames_data, total_rot, n_max, dxf_filename):
    """将最终图形中的所有蛋形曲线导出为DXF文件"""
    try:
        import ezdxf
    except ImportError:
        print("错误: 需要安装ezdxf库才能导出DXF文件")
        print("请使用以下命令安装: pip install ezdxf")
        return False

    try:
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        for i, param in enumerate(curve_params):
            x, y, _ = frames_data[i]

            if len(x) > 0 and len(y) > 0:
                theta_deg = param['rotation_factor'] * total_rot
                theta_rad = -theta_deg * math.pi / 180.0
                x_rotated, y_rotated = rotate_points(x, y, theta_rad)
                points = [(float(x_rotated[j]), float(y_rotated[j]), 0.0)
                          for j in range(len(x_rotated))]
                msp.add_lwpolyline(points)

        doc.saveas(dxf_filename)
        return True

    except Exception as e:
        print(f"导出DXF文件时出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("斐波那契蛋形曲线GIF生成器 (7圈螺旋) - 可自定义振幅函数")
    print("=" * 60)

    # 固定参数设置
    n_max = 36

    # 定义振幅函数
    amp_functions = {
        "sqrt": lambda n: math.sqrt(n),  # 平方根函数
        "inv": lambda n: 1.0 / n,  # 倒数函数
        "linear": lambda n: n,  # 线性函数
        "log": lambda n: math.log(n + 1),  # 对数函数
        "quadratic": lambda n: n * n,  # 二次函数
        "constant": lambda n: 1.0,  # 常数函数
        "golden_ratio": lambda n: phi ** n,  # 黄金比例指数函数
        "fibonacci_ratio": lambda n: fibonacci(n) / fibonacci(n + 1),  # 斐波那契比例
    }

    # 选择振幅函数
    selected_amp_func = amp_functions["sqrt"]  # 默认使用平方根函数

    print(f"固定参数设置:")
    print(f"n_max = {n_max}")
    print(f"总旋转角度 = {total_rotation}° ({int(total_rotation / 360)}圈)")
    print(f"振幅函数: {selected_amp_func.__name__ if hasattr(selected_amp_func, '__name__') else selected_amp_func}")
    print(f"停顿帧数: 20帧")

    # 生成文件名
    amp_func_name = selected_amp_func.__name__ if hasattr(selected_amp_func, '__name__') else "custom"
    gif_filename = f"fibonacci_egg_curves_n{n_max}_7turns_amp_{amp_func_name}.gif"
    dxf_filename = f"fibonacci_egg_curves_n{n_max}_amp_{amp_func_name}.dxf"

    print(f"\n生成GIF动画中...")
    print(f"输出文件: {gif_filename}")
    print(f"帧率: 10 fps")
    print(f"动画帧数: {n_max}个曲线帧 + 20个停顿帧 = {n_max + 20}帧")
    print(f"DXF导出文件: {dxf_filename}")

    anim, curve_params, output_file, dxf_success, dxf_output_file = create_egg_curves_gif_with_pause(
        n_max=n_max,
        gif_filename=gif_filename,
        dxf_filename=dxf_filename,
        fps=10,
        amp_func=selected_amp_func
    )

    print(f"\nGIF动画已保存到: {output_file}")
    print(f"文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")

    if dxf_success:
        print(f"\nDXF文件已保存到: {dxf_output_file}")
        print(f"文件大小: {os.path.getsize(dxf_output_file) / 1024:.2f} KB")
    else:
        print("\nDXF文件导出失败，请检查错误信息。")

    print("\n关键信息:")
    print(f"1. 图形框大小已自动调整为适应所有旋转后的蛋形曲线")
    print(f"2. 曲线数量: {n_max}")
    print(f"3. 总旋转角度: {total_rotation}° ({int(total_rotation / 360)}圈)")
    print(f"4. 振幅函数: {amp_func_name}")


if __name__ == "__main__":
    main()
