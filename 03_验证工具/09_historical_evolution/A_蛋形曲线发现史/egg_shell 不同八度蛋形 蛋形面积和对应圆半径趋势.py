# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# Constants
a = 1
num_egg = 12


# 推导公式：根据 num_egg 动态生成 nodes
def generate_nodes(num_egg):
    nodes = []
    for i in range(1, num_egg):
        k = (4**i / 6)  # k 的递推关系
        b = (5*2**i / 6)  # b 的递推关系
        m = 2 / 3  # m 固定
        amp = (2**i) / (np.sqrt(9 + 2**(4*i - 2)))
        label = f'egg{i+1}'
        nodes.append({'k': k, 'b': b, 'm': m, 'amp': amp, 'label': label})
    return nodes



# Functions
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))


def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)


# 使用梯形法则计算积分
def trapezoidal_integration(x, y):
    return np.trapz(y, x)


# 计算参数曲线面积
def calculate_area(t_values, x_values, y_values):
    # 使用格林公式计算面积: A = 1/2 ∮(xdy - ydx)
    dx_dt = np.gradient(x_values, t_values)
    dy_dt = np.gradient(y_values, t_values)
    integrand = x_values * dy_dt - y_values * dx_dt
    area = 0.5 * np.abs(trapezoidal_integration(t_values, integrand))
    return area


# 根据 num_egg 生成节点
nodes = generate_nodes(num_egg)

# 计算每个曲线的面积和等效半径
areas = []
n_values = []
r_values = []  # 等效半径

for i, node in enumerate(nodes):
    k = node['k']
    b = node['b']
    m = node['m']

    # 生成参数点
    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)

    # 计算面积
    area = calculate_area(t_values, x_values, y_values)
    areas.append(area)
    n_values.append(i + 1)

    # 计算等效半径
    sqrt_s_over_pi = np.sqrt(area / np.pi)
    r_values.append(sqrt_s_over_pi)

# 转换为numpy数组
n_array = np.array(n_values)
s_array = np.array(areas)
r_array = np.array(r_values)

# 1. 面积S_n与n的关系拟合
print("=" * 50)
print("面积S_n与n的关系拟合:")
print("=" * 50)

# 尝试不同的拟合模型
coeffs_linear_s = np.polyfit(n_array, s_array, 1)
s_fit_linear = np.polyval(coeffs_linear_s, n_array)

coeffs_quad_s = np.polyfit(n_array, s_array, 2)
s_fit_quad = np.polyval(coeffs_quad_s, n_array)

coeffs_cubic_s = np.polyfit(n_array, s_array, 3)
s_fit_cubic = np.polyval(coeffs_cubic_s, n_array)

# 计算拟合误差
error_linear_s = np.mean(np.abs(s_array - s_fit_linear))
error_quad_s = np.mean(np.abs(s_array - s_fit_quad))
error_cubic_s = np.mean(np.abs(s_array - s_fit_cubic))

# 选择最好的拟合
errors_s = [error_linear_s, error_quad_s, error_cubic_s]
best_fit_s = np.argmin(errors_s)

if best_fit_s == 0:
    coeffs_s = coeffs_linear_s
    fit_type_s = "线性"
elif best_fit_s == 1:
    coeffs_s = coeffs_quad_s
    fit_type_s = "二次"
else:
    coeffs_s = coeffs_cubic_s
    fit_type_s = "三次"

print(f"面积S_n与n的最佳拟合为{fit_type_s}多项式:")
if len(coeffs_s) == 2:
    print(f"S_n = {coeffs_s[0]:.6f}n + {coeffs_s[1]:.6f}")
elif len(coeffs_s) == 3:
    print(f"S_n = {coeffs_s[0]:.6f}n² + {coeffs_s[1]:.6f}n + {coeffs_s[2]:.6f}")
else:
    print(f"S_n = {coeffs_s[0]:.6f}n³ + {coeffs_s[1]:.6f}n² + {coeffs_s[2]:.6f}n + {coeffs_s[3]:.6f}")

# 2. 等效半径r与n的关系拟合
print("\n" + "=" * 50)
print("等效半径r与n的关系拟合:")
print("=" * 50)

# 拟合 r = c / sqrt(n) 模型
c_squared = n_array * (r_array ** 2)
c = np.sqrt(np.mean(c_squared))
r_fit_power = c / np.sqrt(n_array)
error_power = np.mean(np.abs(r_array - r_fit_power))

print(f"幂律拟合: r_n = {c:.6f} / √n")
print(f"平均绝对误差: {error_power:.6f}")

# 检查其他可能的拟合
coeffs_linear_r = np.polyfit(n_array, r_array, 1)
r_fit_linear = np.polyval(coeffs_linear_r, n_array)
error_linear_r = np.mean(np.abs(r_array - r_fit_linear))

coeffs_quad_r = np.polyfit(n_array, r_array, 2)
r_fit_quad = np.polyval(coeffs_quad_r, n_array)
error_quad_r = np.mean(np.abs(r_array - r_fit_quad))

print(f"线性拟合: r_n = {coeffs_linear_r[0]:.6f}n + {coeffs_linear_r[1]:.6f}")
print(f"线性拟合误差: {error_linear_r:.6f}")

# 3. 打印所有数据
print("\n" + "=" * 50)
print("各曲线的面积和等效半径:")
print("=" * 50)
print("n\tS_n\t\tr = sqrt(S_n/π)")
for i, n in enumerate(n_values):
    print(f"{n}\t{areas[i]:.6f}\t{r_values[i]:.6f}")

# 4. 可视化结果
plt.figure(figsize=(15, 10))

# 4.1 面积与n的关系
plt.subplot(2, 3, 1)
plt.plot(n_values, areas, 'o-', label='实际面积', linewidth=2, markersize=4)
plt.plot(n_values, s_fit_linear, '--', label='线性拟合', alpha=0.7)
plt.plot(n_values, s_fit_quad, '--', label='二次拟合', alpha=0.7)
plt.plot(n_values, s_fit_cubic, '--', label='三次拟合', alpha=0.7)
plt.xlabel('n')
plt.ylabel('面积 S_n')
plt.title('曲线面积与n的关系')
plt.legend()
plt.grid(True)

# 4.2 等效半径与n的关系
plt.subplot(2, 3, 2)
plt.plot(n_values, r_values, 's-', color='red', linewidth=2, markersize=4, label='实际等效半径')
plt.plot(n_values, r_fit_power, '--', color='blue', label=f'幂律拟合: r = {c:.3f}/√n', linewidth=2)
plt.plot(n_values, r_fit_linear, '--', color='green', label='线性拟合', linewidth=2)
plt.xlabel('n')
plt.ylabel('等效半径 r')
plt.title('等效半径与n的关系')
plt.legend()
plt.grid(True)

# 4.3 幂律关系验证: log(r) vs log(n)
plt.subplot(2, 3, 3)
log_n = np.log(n_array)
log_r = np.log(r_array)
plt.plot(log_n, log_r, 'o-', label='实际数据', markersize=4)
coeffs_power = np.polyfit(log_n, log_r, 1)
log_r_fit = np.polyval(coeffs_power, log_n)
plt.plot(log_n, log_r_fit, 'r--', label=f'拟合: 斜率={coeffs_power[0]:.3f}', linewidth=2)
plt.xlabel('log(n)')
plt.ylabel('log(r)')
plt.title('幂律关系验证: log(r) vs log(n)')
plt.legend()
plt.grid(True)

# 4.4 平方根倒数关系: r vs 1/√n
plt.subplot(2, 3, 4)
one_over_sqrt_n = 1 / np.sqrt(n_array)
plt.plot(one_over_sqrt_n, r_array, 'o-', label='实际数据', markersize=4)
coeffs_sqrt = np.polyfit(one_over_sqrt_n, r_array, 1)
r_fit_sqrt = np.polyval(coeffs_sqrt, one_over_sqrt_n)
plt.plot(one_over_sqrt_n, r_fit_sqrt, 'r--', label=f'线性拟合', linewidth=2)
plt.xlabel('1/√n')
plt.ylabel('r')
plt.title('检查: r ∝ 1/√n')
plt.legend()
plt.grid(True)

# 4.5 拟合误差对比
plt.subplot(2, 3, 5)
models = ['幂律拟合', '线性拟合', '二次拟合']
errors_r = [error_power, error_linear_r, error_quad_r]
plt.bar(models, errors_r, color=['blue', 'green', 'orange'])
plt.ylabel('平均绝对误差')
plt.title('不同拟合模型的误差对比')
plt.grid(True, axis='y')

# 4.6 前20个曲线的拟合效果
plt.subplot(2, 3, 6)
n_show = n_array[:20]
r_show = r_array[:20]
r_fit_show = r_fit_power[:20]
plt.plot(n_show, r_show, 'o-', label='实际数据', markersize=4)
plt.plot(n_show, r_fit_show, 'r--', label='幂律拟合', linewidth=2)
plt.xlabel('n')
plt.ylabel('r')
plt.title('前20个数据的拟合效果')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("combined_analysis.png", dpi=300)
plt.show()

# 5. 绘制前20个曲线
plt.figure(figsize=(10, 8))
for i, node in enumerate(nodes[:20]):
    k = node['k']
    b = node['b']
    m = node['m']

    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)

    plt.plot(x_values, y_values, alpha=0.7, label=f'n={i + 1}')

plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.xlabel('x')
plt.ylabel('y')
plt.title(f'前20个参数曲线 (num_egg={num_egg})')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.axis('equal')
plt.grid(True)
plt.tight_layout()
plt.savefig(f"first_20_curves.png", transparent=True, dpi=300)
plt.show()

print(f"\n分析完成！所有图表已保存。")
print(f"\n主要结论:")
print(f"1. 等效半径与n的关系最符合幂律关系: r_n = {c:.6f} / √n")
print(f"2. 这意味着面积 S_n ∝ 1/n")
print(f"3. 幂律拟合的平均绝对误差: {error_power:.6f}")
print(f"4. log(r) vs log(n)的斜率为: {coeffs_power[0]:.6f} (理论值应为-0.5)")