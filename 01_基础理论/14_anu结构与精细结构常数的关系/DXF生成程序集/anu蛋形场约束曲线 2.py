import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time

# 记录开始时间
start_time = time.time()

# 参数定义
a = 0.588
b = 5 / 3
scale = 3
M = 2.5  # 减少波段数，改为2.5

print("开始计算蛋形曲面参数...")


# 计算蛋形曲面的z范围 - 使用解析方法
def find_z_bounds(a, b):
    """使用解析方法找到蛋形曲面有效的z范围"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)

    # 解析求解 R(z)^2 >= 0 的条件
    # 1/(b - z*sin_a)^2 >= (z*cos_a)^2
    # => (b - z*sin_a)^2 * (z*cos_a)^2 <= 1

    # 使用数值方法但更高效
    z_values = np.linspace(-1.57, 1.57, 1000)
    R_squared = 1 / (b - z_values * sin_a) ** 2 - (z_values * cos_a) ** 2

    valid_indices = np.where(R_squared >= 0)[0]
    z_min = z_values[valid_indices[0]]
    z_max = z_values[valid_indices[-1]]

    return z_min, z_max


# 计算蛋形曲面半径函数
def egg_radius(z):
    """计算蛋形曲面在给定z处的半径"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)
    denom = b - z * sin_a
    inside = 1 / denom ** 2 - (z * cos_a) ** 2
    return np.sqrt(np.maximum(inside, 0))


# 生成蛋形曲面上的点
def generate_egg_surface_points(z_min, z_max, num_points=100):
    """生成蛋形曲面上的点，用于可视化"""
    z_vals = np.linspace(z_min, z_max, num_points)
    theta_vals = np.linspace(0, 2 * np.pi, num_points)

    Z, Theta = np.meshgrid(z_vals, theta_vals)
    R = egg_radius(Z)

    X = R * np.cos(Theta)
    Y = R * np.sin(Theta)

    return X, Y, Z


print("正在生成3D螺旋线...")


# 使用直接参数化方法创建3D螺旋线
def create_3d_spiral_direct(z_min, z_max, M, num_points=500):
    """直接参数化方法创建在蛋形曲面上的3D螺旋线"""
    # 参数t从0到1
    t = np.linspace(0, 1, num_points)

    # z坐标在z_min和z_max之间变化
    z = z_min + (z_max - z_min) * (1 - np.cos(2 * np.pi * t)) / 2

    # 角度变化 - 确保M圈
    theta = 2 * np.pi * M * t

    # 计算蛋形曲面半径
    R = egg_radius(z)

    # 计算x和y坐标
    x = R * np.cos(theta)
    y = R * np.sin(theta)

    return x, y, z, t


# 确保曲线闭合
def ensure_closure(x, y, z):
    """确保曲线闭合（起点和终点重合）"""
    # 将终点设置为起点
    x[-1] = x[0]
    y[-1] = y[0]
    z[-1] = z[0]

    return x, y, z


print("正在计算曲率...")


# 计算曲率
def compute_curvature(x, y, z, t):
    """计算曲线的曲率"""
    dx_dt = np.gradient(x, t)
    dy_dt = np.gradient(y, t)
    dz_dt = np.gradient(z, t)

    d2x_dt2 = np.gradient(dx_dt, t)
    d2y_dt2 = np.gradient(dy_dt, t)
    d2z_dt2 = np.gradient(dz_dt, t)

    # 计算曲率
    cross_norm = np.sqrt(
        (dy_dt * d2z_dt2 - dz_dt * d2y_dt2) ** 2 +
        (dz_dt * d2x_dt2 - dx_dt * d2z_dt2) ** 2 +
        (dx_dt * d2y_dt2 - dy_dt * d2x_dt2) ** 2
    )

    velocity_norm = np.sqrt(dx_dt ** 2 + dy_dt ** 2 + dz_dt ** 2) ** 3

    curvature = np.zeros_like(velocity_norm)
    nonzero = velocity_norm > 1e-10
    curvature[nonzero] = cross_norm[nonzero] / velocity_norm[nonzero]

    return curvature


print("正在生成图形...")


# 主程序
def main():
    # 找到蛋形曲面的z范围
    z_min, z_max = find_z_bounds(a, b)
    print(f"蛋形曲面z范围: [{z_min:.3f}, {z_max:.3f}]")

    # 创建3D螺旋线
    x, y, z, t = create_3d_spiral_direct(z_min, z_max, M)

    # 确保曲线闭合
    x, y, z = ensure_closure(x, y, z)

    # 应用缩放
    x_scaled = x * scale
    y_scaled = y * scale
    z_scaled = z * scale

    # 计算曲率
    curvature = compute_curvature(x, y, z, t)

    # 生成蛋形曲面点
    X_egg, Y_egg, Z_egg = generate_egg_surface_points(z_min, z_max, 50)
    X_egg_scaled = X_egg * scale
    Y_egg_scaled = Y_egg * scale
    Z_egg_scaled = Z_egg * scale

    # 绘制曲线
    fig = plt.figure(figsize=(15, 10))

    # 绘制3D曲线和蛋形曲面
    ax1 = fig.add_subplot(231, projection='3d')
    ax1.plot(x_scaled, y_scaled, z_scaled, 'b-', linewidth=2, label='3D Spiral')
    ax1.plot_surface(X_egg_scaled, Y_egg_scaled, Z_egg_scaled,
                     alpha=0.2, color='gray', label='Egg Surface')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('3D Spiral on Egg Surface (M=2.5)')
    ax1.legend()

    # 绘制曲率图
    ax2 = fig.add_subplot(232)
    ax2.plot(t, curvature, 'r-', linewidth=1)
    ax2.set_xlabel('Parameter t')
    ax2.set_ylabel('Curvature')
    ax2.set_title('Curvature Profile')
    ax2.grid(True)

    # 绘制XY投影
    ax3 = fig.add_subplot(233)
    ax3.plot(x_scaled, y_scaled, 'g-', linewidth=2)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_title('XY Projection')
    ax3.grid(True)
    ax3.axis('equal')

    # 绘制XZ投影
    ax4 = fig.add_subplot(234)
    ax4.plot(x_scaled, z_scaled, 'm-', linewidth=2)
    ax4.set_xlabel('X')
    ax4.set_ylabel('Z')
    ax4.set_title('XZ Projection')
    ax4.grid(True)

    # 绘制YZ投影
    ax5 = fig.add_subplot(235)
    ax5.plot(y_scaled, z_scaled, 'c-', linewidth=2)
    ax5.set_xlabel('Y')
    ax5.set_ylabel('Z')
    ax5.set_title('YZ Projection')
    ax5.grid(True)

    # 显示计算信息
    ax6 = fig.add_subplot(236)
    ax6.axis('off')
    info_text = f"""
    Calculation Info:
    - a = {a}
    - b = {b:.3f}
    - Scale = {scale}
    - M = {M}
    - z_min = {z_min:.3f}
    - z_max = {z_max:.3f}
    - Points = {len(t)}
    - Calculation time = {time.time() - start_time:.2f}s
    """
    ax6.text(0.1, 0.5, info_text, fontsize=10, verticalalignment='center')

    plt.tight_layout()
    plt.show()

    # 检查闭合性
    start_point = np.array([x[0], y[0], z[0]])
    end_point = np.array([x[-1], y[-1], z[-1]])
    closure_error = np.linalg.norm(start_point - end_point)
    print(f"闭合误差: {closure_error:.6e}")

    # 检查曲率连续性
    max_curvature_change = np.max(np.abs(np.diff(curvature)))
    print(f"最大曲率变化: {max_curvature_change:.6e}")

    # 验证曲线是否在蛋形曲面上
    print("验证曲线是否在蛋形曲面上...")
    for i in range(0, len(x), len(x) // 10):  # 抽样检查10个点
        r_actual = np.sqrt(x[i] ** 2 + y[i] ** 2)
        r_expected = egg_radius(z[i])
        error = abs(r_actual - r_expected)
        print(f"点 {i}: 实际半径={r_actual:.6f}, 期望半径={r_expected:.6f}, 误差={error:.6f}")


if __name__ == "__main__":
    main()
    print(f"总计算时间: {time.time() - start_time:.2f}秒")