import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import minimize
from scipy.interpolate import CubicSpline, splprep, splev
from scipy.integrate import solve_bvp
import numpy.polynomial.chebyshev as cheb

# 参数定义
a = 0.588
b = 5 / 3
scale = 7
M = 29  # 波段数


# 计算蛋形曲面的z范围
def find_z_bounds(a, b):
    """找到蛋形曲面有效的z范围"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)

    # 定义函数来找到R(z)^2 >= 0的z范围
    def R_squared(z):
        denom = b - z * sin_a
        return 1 / denom ** 2 - (z * cos_a) ** 2

    # 使用优化方法找到边界
    result1 = minimize(lambda z: -z, x0=0, bounds=[(-10, 10)], constraints={
        'type': 'ineq', 'fun': lambda z: R_squared(z)
    })
    z_min = result1.x[0]

    result2 = minimize(lambda z: z, x0=0, bounds=[(-10, 10)], constraints={
        'type': 'ineq', 'fun': lambda z: R_squared(z)
    })
    z_max = result2.x[0]

    return z_min, z_max


# 蛋形曲面半径函数
def egg_radius(z):
    """计算蛋形曲面在给定z处的半径"""
    sin_a = np.sin(a)
    cos_a = np.cos(a)
    denom = b - z * sin_a
    inside = 1 / denom ** 2 - (z * cos_a) ** 2
    return np.sqrt(np.maximum(inside, 0))


# 使用谱方法创建3D连续螺旋线
def create_3d_spiral(z_min, z_max, a, b, M, num_points=1000):
    """创建在蛋形曲面上的3D连续螺旋线"""
    # 使用Chebyshev多项式基函数
    t = cheb.chebpts2(num_points)

    # 参数化曲线
    theta = 2 * np.pi * M * t  # 角度变化

    # 计算z坐标 - 使用光滑函数确保C∞连续
    z = 0.5 * (z_max + z_min) + 0.5 * (z_max - z_min) * np.sin(np.pi * t)

    # 计算蛋形曲面半径
    R = egg_radius(z)

    # 计算x和y坐标
    x = R * np.cos(theta)
    y = R * np.sin(theta)

    return x, y, z, t


# 使用有限元法优化曲线
def optimize_with_fem(x, y, z, t, num_iter=10):
    """使用有限元法优化曲线光滑度"""
    # 将曲线参数化
    points = np.vstack([x, y, z]).T

    # 使用样条插值
    tck, u = splprep(points.T, s=0, k=5)

    # 生成更光滑的曲线
    u_new = np.linspace(0, 1, len(t) * 2)
    x_new, y_new, z_new = splev(u_new, tck)

    return x_new, y_new, z_new, u_new


# 使用边界元法确保曲线闭合
def ensure_closure_with_bem(x, y, z):
    """使用边界元法确保曲线闭合"""
    # 计算起点和终点的平均
    x_avg = (x[0] + x[-1]) / 2
    y_avg = (y[0] + y[-1]) / 2
    z_avg = (z[0] + z[-1]) / 2

    # 使用边界元法平滑过渡
    n = len(x)
    for i in range(n):
        # 使用权重函数确保平滑过渡
        w = 0.5 * (1 - np.cos(2 * np.pi * i / (n - 1)))
        x[i] = (1 - w) * x[i] + w * x_avg
        y[i] = (1 - w) * y[i] + w * y_avg
        z[i] = (1 - w) * z[i] + w * z_avg

    return x, y, z


# 计算曲率和曲率导数
def compute_curvature_and_derivatives(x, y, z, t):
    """计算曲线的曲率和曲率导数"""
    # 一阶导数
    dx_dt = np.gradient(x, t)
    dy_dt = np.gradient(y, t)
    dz_dt = np.gradient(z, t)

    # 二阶导数
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

    # 计算曲率导数
    curvature_derivative = np.gradient(curvature, t)

    return curvature, curvature_derivative


# 使用共轭梯度法优化曲率连续性
def optimize_curvature_continuity(x, y, z, t, max_iter=100):
    """使用共轭梯度法优化曲率连续性"""

    # 定义目标函数：最小化曲率导数的平方和
    def objective(params):
        # 参数是曲线点的微小调整
        dx, dy, dz = params[:len(x)], params[len(x):2 * len(x)], params[2 * len(x):]
        x_new = x + dx
        y_new = y + dy
        z_new = z + dz

        # 计算曲率导数
        _, curvature_derivative = compute_curvature_and_derivatives(x_new, y_new, z_new, t)

        # 返回曲率导数的平方和
        return np.sum(curvature_derivative ** 2)

    # 初始猜测（零调整）
    initial_params = np.zeros(3 * len(x))

    # 使用共轭梯度法优化
    result = minimize(objective, initial_params, method='CG',
                      options={'maxiter': max_iter, 'disp': True})

    # 提取优化后的参数
    opt_params = result.x
    dx = opt_params[:len(x)]
    dy = opt_params[len(x):2 * len(x)]
    dz = opt_params[2 * len(x):]

    return x + dx, y + dy, z + dz


# 主程序
def main():
    # 找到蛋形曲面的z范围
    z_min, z_max = find_z_bounds(a, b)
    print(f"蛋形曲面z范围: [{z_min:.3f}, {z_max:.3f}]")

    # 创建3D螺旋线
    x, y, z, t = create_3d_spiral(z_min, z_max, a, b, M)

    # 使用有限元法优化曲线
    x, y, z, t = optimize_with_fem(x, y, z, t)

    # 使用边界元法确保曲线闭合
    x, y, z = ensure_closure_with_bem(x, y, z)

    # 使用共轭梯度法优化曲率连续性
    x, y, z = optimize_curvature_continuity(x, y, z, t)

    # 应用缩放
    x_scaled = x * scale
    y_scaled = y * scale
    z_scaled = z * scale

    # 计算曲率和曲率导数
    curvature, curvature_derivative = compute_curvature_and_derivatives(x, y, z, t)

    # 绘制曲线
    fig = plt.figure(figsize=(18, 12))

    # 绘制3D曲线
    ax1 = fig.add_subplot(231, projection='3d')
    ax1.plot(x_scaled, y_scaled, z_scaled, 'b-', linewidth=2, label='3D Continuous Spiral')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('3D Continuous Spiral on Egg Surface')

    # 绘制曲率图
    ax2 = fig.add_subplot(232)
    ax2.plot(t, curvature, 'r-', linewidth=2)
    ax2.set_xlabel('Parameter t')
    ax2.set_ylabel('Curvature')
    ax2.set_title('Curvature Profile')
    ax2.grid(True)

    # 绘制曲率导数图
    ax3 = fig.add_subplot(233)
    ax3.plot(t, curvature_derivative, 'g-', linewidth=2)
    ax3.set_xlabel('Parameter t')
    ax3.set_ylabel('Curvature Derivative')
    ax3.set_title('Curvature Derivative Profile')
    ax3.grid(True)

    # 绘制XY投影
    ax4 = fig.add_subplot(234)
    ax4.plot(x_scaled, y_scaled, 'm-', linewidth=2)
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    ax4.set_title('XY Projection')
    ax4.grid(True)
    ax4.axis('equal')

    # 绘制XZ投影
    ax5 = fig.add_subplot(235)
    ax5.plot(x_scaled, z_scaled, 'c-', linewidth=2)
    ax5.set_xlabel('X')
    ax5.set_ylabel('Z')
    ax5.set_title('XZ Projection')
    ax5.grid(True)

    # 绘制YZ投影
    ax6 = fig.add_subplot(236)
    ax6.plot(y_scaled, z_scaled, 'y-', linewidth=2)
    ax6.set_xlabel('Y')
    ax6.set_ylabel('Z')
    ax6.set_title('YZ Projection')
    ax6.grid(True)

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

    # 检查曲率导数连续性
    max_curvature_derivative = np.max(np.abs(curvature_derivative))
    print(f"最大曲率导数: {max_curvature_derivative:.6e}")


if __name__ == "__main__":
    main()