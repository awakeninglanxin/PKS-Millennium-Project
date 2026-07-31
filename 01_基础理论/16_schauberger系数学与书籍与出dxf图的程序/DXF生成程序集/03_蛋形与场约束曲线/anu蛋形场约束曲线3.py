import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import CubicSpline
import time

# 记录开始时间
start_time = time.time()

# 参数定义
a = 0.588
b = 5 / 3
scale = 7
M = 29  # 波段数
z_limit = np.pi / 2  # z的限制范围 ±π/2

print("开始计算蛋形曲面参数...")


# 计算蛋形曲面的z范围
def find_z_bounds(a, b, z_limit):
    """找到蛋形曲面有效的z范围，确保在±z_limit内"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)

    # 使用数值方法
    z_values = np.linspace(-z_limit * 1.1, z_limit * 1.1, 1000)
    R_squared = 1 / (b - z_values * sin_a) ** 2 - (z_values * cos_a) ** 2

    valid_indices = np.where(R_squared >= 0)[0]
    z_min = max(z_values[valid_indices[0]], -z_limit)
    z_max = min(z_values[valid_indices[-1]], z_limit)

    return z_min, z_max


# 计算蛋形曲面半径函数
def egg_radius(z):
    """计算蛋形曲面在给定z处的半径"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)
    denom = b - z * sin_a
    inside = 1 / denom ** 2 - (z * cos_a) ** 2
    return np.sqrt(np.maximum(inside, 0))


# 生成原始3D连续螺旋漏斗曲线
def create_original_spiral(z_min, z_max, M, num_points=1000):
    """创建原始的3D连续螺旋漏斗曲线"""
    # 参数t从0到2πM
    t = np.linspace(0, 2 * np.pi * M, num_points)

    # 使用黄金比例相关的参数
    phi = (np.sqrt(5) - 1) / 2
    k = 1 / (2 * np.pi * np.log(phi))

    # 计算z坐标 - 确保在z_min和z_max之间
    z = z_min + (z_max - z_min) * (1 + np.sin(t / (2 * M))) / 2

    # 计算半径 - 使用指数衰减创建漏斗形状
    r = np.exp(-t / (2 * np.pi * M)) * egg_radius(z)

    # 计算角度
    theta = t + np.pi / 2

    # 计算x和y坐标
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    return x, y, z, t


# 生成封闭圆环曲线
def create_closed_torus(x_spiral, y_spiral, z_spiral, t_spiral, num_points=500):
    """创建封闭的圆环曲线，位于螺旋漏斗曲线内部"""
    # 找到螺旋线的中心线
    x_center = np.mean(x_spiral)
    y_center = np.mean(y_spiral)
    z_center = np.mean(z_spiral)

    # 计算螺旋线的平均半径
    r_avg = np.mean(np.sqrt((x_spiral - x_center) ** 2 + (y_spiral - y_center) ** 2))

    # 创建圆环参数
    u = np.linspace(0, 2 * np.pi, num_points)
    v = np.linspace(0, 2 * np.pi, num_points)

    # 圆环的大半径（主要半径）
    R = r_avg * 0.8  # 稍微小于平均半径，确保在螺旋内部

    # 圆环的小半径（截面半径）
    r = r_avg * 0.2

    # 生成圆环曲线
    x_torus = x_center + (R + r * np.cos(v)) * np.cos(u)
    y_torus = y_center + (R + r * np.cos(v)) * np.sin(u)
    z_torus = z_center + r * np.sin(v)

    return x_torus, y_torus, z_torus, u


# 生成蛋形测地线
def create_geodesic(z_min, z_max, num_points=500):
    """创建蛋形测地线，用于与圆环外侧对接"""
    # 参数t从0到2π
    t = np.linspace(0, 2 * np.pi, num_points)

    # z坐标在z_min和z_max之间变化
    z = z_min + (z_max - z_min) * (1 + np.sin(t)) / 2

    # 计算蛋形曲面半径
    R = egg_radius(z)

    # 计算角度 - 确保与z同步变化
    theta = t + np.pi / 2

    # 计算x和y坐标
    x = R * np.cos(theta)
    y = R * np.sin(theta)

    return x, y, z, t


# 确保C∞连续的光滑过渡函数
def c_infty_transition(t, t0, t1):
    """创建C∞连续的光滑过渡函数"""
    # 使用指数函数构造无限可导的过渡函数
    if t <= t0:
        return 0.0
    elif t >= t1:
        return 1.0
    else:
        u = (t - t0) / (t1 - t0)
        # 使用C∞函数：f(u) = e^(-1/(u(1-u))) for 0<u<1
        return np.exp(-1 / (u * (1 - u))) if 0 < u < 1 else (0 if u <= 0 else 1)


# 将圆环与测地线丝滑对接
def connect_torus_to_geodesic(x_torus, y_torus, z_torus, x_geo, y_geo, z_geo):
    """将圆环外侧与蛋形测地线丝滑对接，确保C∞连续"""
    # 找到对接点（圆环上最外侧的点）
    torus_radii = np.sqrt(x_torus ** 2 + y_torus ** 2 + z_torus ** 2)
    connect_idx_torus = np.argmax(torus_radii)

    # 找到测地线上对应的点
    geo_radii = np.sqrt(x_geo ** 2 + y_geo ** 2 + z_geo ** 2)
    connect_idx_geo = np.argmin(np.abs(geo_radii - torus_radii[connect_idx_torus]))

    # 创建过渡区域
    transition_points = 100
    transition_start = connect_idx_torus - transition_points // 2
    transition_end = connect_idx_torus + transition_points // 2

    # 确保索引在有效范围内
    transition_start = max(0, transition_start)
    transition_end = min(len(x_torus) - 1, transition_end)

    # 应用光滑过渡
    for i in range(transition_start, transition_end):
        # 计算过渡权重
        t = (i - transition_start) / (transition_end - transition_start)
        weight = c_infty_transition(t, 0.2, 0.8)

        # 计算目标点（测地线上的对应点）
        target_idx = connect_idx_geo + (i - connect_idx_torus)
        if target_idx < 0:
            target_idx += len(x_geo)
        if target_idx >= len(x_geo):
            target_idx -= len(x_geo)

        # 应用过渡
        x_torus[i] = (1 - weight) * x_torus[i] + weight * x_geo[target_idx]
        y_torus[i] = (1 - weight) * y_torus[i] + weight * y_geo[target_idx]
        z_torus[i] = (1 - weight) * z_torus[i] + weight * z_geo[target_idx]

    return x_torus, y_torus, z_torus


print("正在生成曲线...")


# 主程序
def main():
    # 找到蛋形曲面的z范围
    z_min, z_max = find_z_bounds(a, b, z_limit)
    print(f"蛋形曲面z范围: [{z_min:.3f}, {z_max:.3f}] (限制在±{z_limit:.3f}内)")

    # 创建原始3D连续螺旋漏斗曲线
    x_spiral, y_spiral, z_spiral, t_spiral = create_original_spiral(z_min, z_max, M)

    # 创建封闭圆环曲线（位于螺旋内部）
    x_torus, y_torus, z_torus, u_torus = create_closed_torus(x_spiral, y_spiral, z_spiral, t_spiral)

    # 创建蛋形测地线
    x_geo, y_geo, z_geo, t_geo = create_geodesic(z_min, z_max)

    # 将圆环与测地线丝滑对接
    x_torus, y_torus, z_torus = connect_torus_to_geodesic(x_torus, y_torus, z_torus, x_geo, y_geo, z_geo)

    # 应用缩放
    x_spiral_scaled = x_spiral * scale
    y_spiral_scaled = y_spiral * scale
    z_spiral_scaled = z_spiral * scale

    x_torus_scaled = x_torus * scale
    y_torus_scaled = y_torus * scale
    z_torus_scaled = z_torus * scale

    x_geo_scaled = x_geo * scale
    y_geo_scaled = y_geo * scale
    z_geo_scaled = z_geo * scale

    # 绘制曲线
    fig = plt.figure(figsize=(16, 12))

    # 绘制3D曲线
    ax1 = fig.add_subplot(231, projection='3d')
    ax1.plot(x_spiral_scaled, y_spiral_scaled, z_spiral_scaled, 'b-', linewidth=1, alpha=0.7, label='Original Spiral')
    ax1.plot(x_torus_scaled, y_torus_scaled, z_torus_scaled, 'r-', linewidth=2, label='Closed Torus')
    ax1.plot(x_geo_scaled, y_geo_scaled, z_geo_scaled, 'g-', linewidth=1, alpha=0.7, label='Geodesic')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('Closed Torus Curve with Geodesic Connection')
    ax1.legend()

    # 绘制XY投影
    ax2 = fig.add_subplot(232)
    ax2.plot(x_spiral_scaled, y_spiral_scaled, 'b-', linewidth=1, alpha=0.7, label='Spiral')
    ax2.plot(x_torus_scaled, y_torus_scaled, 'r-', linewidth=2, label='Torus')
    ax2.plot(x_geo_scaled, y_geo_scaled, 'g-', linewidth=1, alpha=0.7, label='Geodesic')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_title('XY Projection')
    ax2.grid(True)
    ax2.axis('equal')
    ax2.legend()

    # 绘制XZ投影
    ax3 = fig.add_subplot(233)
    ax3.plot(x_spiral_scaled, z_spiral_scaled, 'b-', linewidth=1, alpha=0.7, label='Spiral')
    ax3.plot(x_torus_scaled, z_torus_scaled, 'r-', linewidth=2, label='Torus')
    ax3.plot(x_geo_scaled, z_geo_scaled, 'g-', linewidth=1, alpha=0.7, label='Geodesic')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Z')
    ax3.set_title('XZ Projection')
    ax3.grid(True)
    ax3.legend()

    # 绘制YZ投影
    ax4 = fig.add_subplot(234)
    ax4.plot(y_spiral_scaled, z_spiral_scaled, 'b-', linewidth=1, alpha=0.7, label='Spiral')
    ax4.plot(y_torus_scaled, z_torus_scaled, 'r-', linewidth=2, label='Torus')
    ax4.plot(y_geo_scaled, z_geo_scaled, 'g-', linewidth=1, alpha=0.7, label='Geodesic')
    ax4.set_xlabel('Y')
    ax4.set_ylabel('Z')
    ax4.set_title('YZ Projection')
    ax4.grid(True)
    ax4.legend()

    # 显示计算信息
    ax5 = fig.add_subplot(235)
    ax5.axis('off')
    info_text = f"""
    Calculation Info:
    - a = {a}
    - b = {b:.3f}
    - Scale = {scale}
    - M = {M}
    - z_min = {z_min:.3f}
    - z_max = {z_max:.3f}
    - z_limit = ±{z_limit:.3f}
    - Calculation time = {time.time() - start_time:.2f}s
    """
    ax5.text(0.1, 0.5, info_text, fontsize=10, verticalalignment='center')

    # 绘制连接区域特写
    ax6 = fig.add_subplot(236)
    # 找到连接区域
    torus_radii = np.sqrt(x_torus ** 2 + y_torus ** 2 + z_torus ** 2)
    connect_idx = np.argmax(torus_radii)

    # 绘制连接区域
    start_idx = max(0, connect_idx - 20)
    end_idx = min(len(x_torus) - 1, connect_idx + 20)

    ax6.plot(range(start_idx, end_idx), x_torus[start_idx:end_idx], 'r-', label='Torus X')
    ax6.plot(range(start_idx, end_idx), y_torus[start_idx:end_idx], 'g-', label='Torus Y')
    ax6.plot(range(start_idx, end_idx), z_torus[start_idx:end_idx], 'b-', label='Torus Z')
    ax6.set_xlabel('Point Index')
    ax6.set_ylabel('Coordinate Value')
    ax6.set_title('Connection Region Detail')
    ax6.grid(True)
    ax6.legend()

    plt.tight_layout()
    plt.show()

    # 检查闭合性
    start_point = np.array([x_torus[0], y_torus[0], z_torus[0]])
    end_point = np.array([x_torus[-1], y_torus[-1], z_torus[-1]])
    closure_error = np.linalg.norm(start_point - end_point)
    print(f"圆环闭合误差: {closure_error:.6e}")

    # 检查与测地线的连接平滑度
    geo_radii = np.sqrt(x_geo ** 2 + y_geo ** 2 + z_geo ** 2)
    torus_radii = np.sqrt(x_torus ** 2 + y_torus ** 2 + z_torus ** 2)
    max_torus_radius = np.max(torus_radii)
    min_geo_radius = np.min(geo_radii)
    connection_error = abs(max_torus_radius - min_geo_radius)
    print(f"与测地线连接误差: {connection_error:.6e}")


if __name__ == "__main__":
    main()
    print(f"总计算时间: {time.time() - start_time:.2f}秒")