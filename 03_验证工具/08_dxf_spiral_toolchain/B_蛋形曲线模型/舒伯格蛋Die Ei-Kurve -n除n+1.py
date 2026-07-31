import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simpson

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (10, 10)  # 设置默认图形大小
plt.rcParams['figure.autolayout'] = True  # 启用自动布局

# 黄金比例相关的角度
phi = (np.sqrt(5) + 1) / 2
twist_angle = 0


def calculate_area(points):
    """使用鞋带公式计算多边形面积"""
    x, y = zip(*points)
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def calculate_perimeter(points):
    """计算多边形周长"""
    perimeter = 0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        perimeter += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return perimeter


def generate_egg_curve(b, k, n, amp_scheme, num_points=1000):
    """生成蛋形曲线"""
    phi_values = np.linspace(0, 2 * np.pi, num_points)

    # 根据选择的方案计算振幅
    if amp_scheme == "inverse":
        amp = 1 / n
    elif amp_scheme == "direct":
        amp = n
    elif amp_scheme == "unit":
        amp = 1
    else:  # "max_n"
        amp = 1

    alpha = math.atan(k)
    sin_alpha = math.sin(alpha)
    cos_alpha = math.cos(alpha)

    sin_phi = np.sin(phi_values)
    cos_phi = np.cos(phi_values)

    # 计算分母内部项
    denominator_inside = np.sqrt(sin_phi ** 2 + cos_phi ** 2 * cos_alpha ** 2)

    # 计算平方根内部项
    inside_sqrt = b ** 2 - (4 * cos_phi * sin_alpha) / denominator_inside

    # 过滤有效点
    valid_mask = inside_sqrt >= 0
    phi_valid = phi_values[valid_mask]
    sin_phi_valid = sin_phi[valid_mask]
    cos_phi_valid = cos_phi[valid_mask]
    inside_sqrt_valid = inside_sqrt[valid_mask]

    if len(phi_valid) == 0:
        return [], [], [], []

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
        return [], [], [], []

    # 计算半径
    sqrt_val = np.sqrt(inside_sqrt_valid)
    r1 = amp * (b + sqrt_val) / denominator
    r2 = amp * (b - sqrt_val) / denominator

    # 计算坐标
    x1, y1 = r1 * sin_phi_valid, r1 * cos_phi_valid
    x2, y2 = r2 * sin_phi_valid, r2 * cos_phi_valid

    branch1 = list(zip(x1, y1))
    branch2 = list(zip(x2, y2))

    return branch1, branch2, phi_valid, r2, amp


def rotate_points(points, theta):
    """旋转点集"""
    return [
        (x * math.cos(theta) - y * math.sin(theta),
         x * math.sin(theta) + y * math.cos(theta))
        for x, y in points
    ]


def plot_egg_curves(n_max=5, amp_scheme="inverse", branch_to_show="both", amp_choice="1"):
    """绘制不同参数组的蛋形曲线旋转叠加效果"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # 设置颜色映射 - 蛋外曲线使用彩虹色，蛋曲线使用HSV色
    colors_rainbow = plt.cm.rainbow(np.linspace(0, 1, n_max))
    colors_hsv = plt.cm.hsv(np.linspace(0, 1, n_max))

    # 打印表头
    print(f"振幅方案: {amp_scheme}")
    print(
        "n\tk\t\tb\t\t实际面积\t实际等效半径\t实际周长\t实际周长等效半径\t原始面积\t原始等效半径\t原始周长\t原始周长等效半径")
    print("-" * 120)

    for n in range(1, n_max + 1):
        # 计算参数
        k = n / (n + 1)
        b = (2 * n + 1) / (n + 1)

        # 生成蛋形曲线
        branch1, branch2, phi_valid, r2, amp = generate_egg_curve(b, k, n, amp_scheme)

        # 计算蛋曲线的面积、周长和等效半径
        if branch2:
            # 计算实际曲线（包含amp）的面积和周长
            actual_area = calculate_area(branch2)
            actual_area_equivalent_radius = math.sqrt(actual_area / math.pi)

            actual_perimeter = calculate_perimeter(branch2)
            actual_perimeter_equivalent_radius = actual_perimeter / (2 * math.pi)

            # 计算原始曲线（不包含amp）的面积和周长
            original_points = [(x / amp, y / amp) for x, y in branch2]
            original_area = calculate_area(original_points)
            original_area_equivalent_radius = math.sqrt(original_area / math.pi)

            original_perimeter = calculate_perimeter(original_points)
            original_perimeter_equivalent_radius = original_perimeter / (2 * math.pi)

            # 打印参数
            print(
                f"{n}\t{k:.6f}\t{b:.6f}\t{actual_area:.6f}\t{actual_area_equivalent_radius:.6f}\t{actual_perimeter:.6f}\t{actual_perimeter_equivalent_radius:.6f}\t{original_area:.6f}\t{original_area_equivalent_radius:.6f}\t{original_perimeter:.6f}\t{original_perimeter_equivalent_radius:.6f}")
        else:
            print(f"{n}\t{k:.6f}\t{b:.6f}\tN/A\t\tN/A\t\tN/A\t\tN/A\t\tN/A\t\tN/A\t\tN/A\t\tN/A")

        # 根据用户选择的显示分支
        if amp_choice == "4" and n != n_max:
            continue  # 如果选择了只显示最大n值的曲线，跳过其他曲线

        # 计算旋转角度
        rotation_angle = (n - 1) * twist_angle / (n_max - 1) if n_max > 1 else 0
        rotation_rad = -math.radians(rotation_angle)

        if branch_to_show in ["both", "蛋外曲线"]:
            if branch1:
                rotated1 = rotate_points(branch1, rotation_rad)
                x1, y1 = zip(*rotated1)
                ax.plot(x1, y1, color=colors_rainbow[n - 1], alpha=0.7, lw=0.5, label=f'n={n} (+)')

        if branch_to_show in ["both", "蛋曲线"]:
            if branch2:
                rotated2 = rotate_points(branch2, rotation_rad)
                x2, y2 = zip(*rotated2)
                ax.plot(x2, y2, color=colors_hsv[n - 1], alpha=0.7, lw=0.3, label=f'n={n} (-)')

    # 设置图形属性
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax.axvline(0, color='k', linestyle='--', alpha=0.3)
    ax.set_aspect('equal')
    ax.grid(True)

    # 标题包含twist_angle和振幅方案信息
    ax.set_title(f'蛋形曲线旋转叠加效果 (扭转角度：{twist_angle:.2f}°, 振幅方案: {amp_scheme})')

    # 添加颜色条 - 使用彩虹色映射
    sm = plt.cm.ScalarMappable(cmap=plt.cm.rainbow, norm=plt.Normalize(vmin=1, vmax=n_max))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('n值')

    plt.tight_layout()

    # 尝试最大化窗口
    try:
        fig_manager = plt.get_current_fig_manager()
        fig_manager.window.state('zoomed')  # 适用于Windows后端
    except:
        try:
            fig_manager.window.showMaximized()  # 适用于Qt后端
        except:
            pass

    plt.show()


def main():
    """主函数"""
    n_max = int(input("请输入最大n值 (默认72): ") or 72)

    # 让用户选择振幅方案
    amp_choice = input(
        "请选择振幅方案 (1: amp = 1/n, 2: amp = n, 3: amp = 1, 4: amp = 1, 仅显示最大n值的曲线, 默认1): ") or "1"
    if amp_choice == "1":
        amp_scheme = "inverse"
    elif amp_choice == "2":
        amp_scheme = "direct"
    elif amp_choice == "3":
        amp_scheme = "unit"
    else:
        amp_scheme = "max_n"

    # 让用户选择显示的曲线分支
    branch_choice = input(
        "请选择要显示的分支 (1: 只显示蛋外曲线, 2: 只显示蛋曲线, 3: 显示蛋外曲线和蛋曲线, 默认3): ") or "3"
    if branch_choice == "1":
        branch_to_show = "蛋外曲线"
    elif branch_choice == "2":
        branch_to_show = "蛋曲线"
    else:
        branch_to_show = "both"

    plot_egg_curves(n_max, amp_scheme, branch_to_show, amp_choice)


if __name__ == "__main__":
    main()
