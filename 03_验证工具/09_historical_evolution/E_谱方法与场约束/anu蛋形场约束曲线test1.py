import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

# 定义参数
phi = 0.618  # 黄金比例
a = 0.588  # 蛋形曲面参数
b = 5 / 3  # 蛋形曲面参数
n = 3.326  # 放大倍数
M = 2.553  # t_s的最大值

# 计算v_min和v_max
v_min = np.log(0.5) / np.log(phi)  # ≈ -1.9505
v_max = np.log(M) / np.log(phi)  # ≈ 1.4427

print(f"v_min: {v_min}, v_max: {v_max}")


# 定义蛋形部分的f(z)，考虑放大系数n
def f(z):
    # z是放大后的坐标，需要先除以n得到原始蛋形曲面的z坐标
    z_original = z / n
    denominator = b - z_original * np.sin(a)
    # 避免分母为零
    if abs(denominator) < 1e-10:
        return 0
    f_val = 1 / (denominator) ** 2 - (z_original * np.cos(a)) ** 2
    return max(f_val, 0)  # 确保非负


# 定义融合曲面的半径函数r(v)
def r_v(v):
    f_val = f(v)
    if f_val <= 0:
        return 0
    return n * np.sqrt(f_val)


# 计算r_v的最小值和最大值
v_samples = np.linspace(v_min, v_max, 1000)
r_samples = [r_v(v) for v in v_samples]
r_min = min([r for r in r_samples if r > 0])
r_max = max(r_samples)

print(f"r_min: {r_min}, r_max: {r_max}")


# 定义测地线的被积函数，添加安全检查
def integrand(v, C):
    r_val = r_v(v)
    # 安全检查：确保分母不为零且sqrt的参数非负
    if r_val <= C or np.isclose(r_val, C, atol=1e-6):
        return 0
    denominator = r_val ** 2 * np.sqrt(1 - C ** 2 / r_val ** 2)
    if denominator < 1e-10:
        return 0
    return C / denominator


# 定义积分函数，用于计算从v_min到v_max的积分值
def total_integral(C):
    # 找到r_v(v) >= C的有效区间
    v_low = v_min
    v_high = v_max

    # 使用自适应积分
    integral, _ = quad(integrand, v_low, v_high, args=(C,), epsabs=1e-6, epsrel=1e-6, limit=1000)
    return integral


# 求解C，使得积分值为10π
target = 10 * np.pi


# 使用布伦特方法求解C，更稳定
def equation(C):
    return total_integral(C) - target


# 确保C在有效范围内
C_min = r_min + 1e-6
C_max = r_max - 1e-6

try:
    C_solution = brentq(equation, C_min, C_max, xtol=1e-6, maxiter=100)
    print(f"Solved C: {C_solution}")
except ValueError:
    print("Brentq method failed, using fallback value")
    C_solution = (r_min + r_max) / 2


# 计算u(v)通过数值积分
def u_v(v, C):
    # 找到r_v(v) >= C的有效区间
    v_low = v_min
    # 使用自适应积分
    integral, _ = quad(integrand, v_low, v, args=(C,), epsabs=1e-6, epsrel=1e-6, limit=1000)
    return integral


# 生成v值数组，确保在有效范围内
v_values = np.linspace(v_min, v_max, 1000)
u_values = np.zeros_like(v_values)

# 预先计算u_values，使用更稳健的方法
for i, v in enumerate(v_values):
    u_values[i] = u_v(v, C_solution)

# 计算测地线的坐标
x_geodesic = np.array([r_v(v) * np.cos(u) for v, u in zip(v_values, u_values)])
y_geodesic = np.array([r_v(v) * np.sin(u) for v, u in zip(v_values, u_values)])
z_geodesic = v_values

# 绘制融合曲面
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# 生成曲面数据
u_angle = np.linspace(0, 2 * np.pi, 100)
v_height = np.linspace(v_min+2, v_max, 100)
U, V = np.meshgrid(u_angle, v_height)

# 计算曲面坐标，考虑放大系数n
X = np.zeros_like(U)
Y = np.zeros_like(U)
Z = np.zeros_like(U)

for i in range(U.shape[0]):
    for j in range(U.shape[1]):
        u_val = U[i, j]
        v_val = V[i, j]
        r_val = r_v(v_val)
        X[i, j] = r_val * np.cos(u_val)
        Y[i, j] = r_val * np.sin(u_val)
        Z[i, j] = v_val

# 绘制曲面
surf = ax.plot_surface(X, Y, Z, cmap=cm.viridis, alpha=0.3, linewidth=0, antialiased=True)

# 绘制测地线
ax.plot(x_geodesic, y_geodesic, z_geodesic, color='red', linewidth=3, label='Geodesic Spiral')

# 设置坐标轴标签，考虑放大系数
ax.set_xlabel('X (scaled by n)')
ax.set_ylabel('Y (scaled by n)')
ax.set_zlabel('Z (scaled by n)')
ax.set_title('Fused Egg-Funnel Surface with 5-Turn Geodesic Spiral')
ax.legend()

# 设置坐标轴范围，确保显示完整的曲面和螺旋线
ax.set_xlim(-n * 2, n * 2)
ax.set_ylim(-n * 2, n * 2)
ax.set_zlim(v_min, v_max)

# 添加颜色条
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

plt.tight_layout()
plt.show()

# 输出一些关键参数
print(f"Amplification factor n: {n}")
print(f"Maximum t_s value M: {M}")
print(f"Minimum radius r_min: {r_min}")
print(f"Maximum radius r_max: {r_max}")
print(f"Geodesic constant C: {C_solution}")
print(f"Total angle change: {u_values[-1]} radians, {u_values[-1] / (2 * np.pi)} turns")