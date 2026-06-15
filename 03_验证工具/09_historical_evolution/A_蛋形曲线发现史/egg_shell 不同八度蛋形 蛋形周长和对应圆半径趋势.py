# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# Constants
a = 1
num_egg = 15


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


# 计算曲线长度（微分法）
def calculate_length(t_values, x_values, y_values):
    # 计算导数
    dx_dt = np.gradient(x_values, t_values)
    dy_dt = np.gradient(y_values, t_values)

    # 计算弧长微分 ds = sqrt((dx/dt)^2 + (dy/dt)^2) * dt
    ds_dt = np.sqrt(dx_dt ** 2 + dy_dt ** 2)

    # 积分得到总长度
    length = np.trapz(ds_dt, t_values)
    return length


# 根据 num_egg 生成节点
nodes = generate_nodes(num_egg)

# 计算每个曲线的长度和等效半径
lengths = []
n_values = []
r_length_values = []  # 基于长度的等效半径

for i, node in enumerate(nodes):
    k = node['k']
    b = node['b']
    m = node['m']

    # 生成参数点
    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)

    # 计算曲线长度
    length = calculate_length(t_values, x_values, y_values)
    lengths.append(length)
    n_values.append(i + 1)

    # 计算基于长度的等效半径 (L/2π)
    r_length = length / (2 * np.pi)
    r_length_values.append(r_length)

# 转换为numpy数组
n_array = np.array(n_values)
L_array = np.array(lengths)
r_array = np.array(r_length_values)


# 定义各种拟合函数
def power_law(n, c):
    return c / np.sqrt(n)


def inverse_law(n, c):
    return c / n


def exponential_decay(n, a, b):
    return a * np.exp(-b * n)


def power_law_general(n, a, b):
    return a * n ** b


def rational_function(n, a, b):
    return a / (1 + b * n)


def logarithmic_decay(n, a, b):
    return a - b * np.log(n)


# 尝试各种拟合模型
fits = []
errors = []

# 1. 幂律拟合: r = c/√n
try:
    popt, _ = curve_fit(lambda n, c: c / np.sqrt(n), n_array, r_array)
    r_fit_power = power_law(n_array, popt[0])
    error_power = np.mean(np.abs(r_array - r_fit_power))
    fits.append(('幂律 r = c/√n', r_fit_power, f'c = {popt[0]:.6f}'))
    errors.append(error_power)
except:
    pass

# 2. 反比拟合: r = c/n
try:
    popt, _ = curve_fit(lambda n, c: c / n, n_array, r_array)
    r_fit_inverse = inverse_law(n_array, popt[0])
    error_inverse = np.mean(np.abs(r_array - r_fit_inverse))
    fits.append(('反比 r = c/n', r_fit_inverse, f'c = {popt[0]:.6f}'))
    errors.append(error_inverse)
except:
    pass

# 3. 指数衰减拟合: r = a*exp(-b*n)
try:
    popt, _ = curve_fit(exponential_decay, n_array, r_array, p0=[1, 0.1])
    r_fit_exp = exponential_decay(n_array, *popt)
    error_exp = np.mean(np.abs(r_array - r_fit_exp))
    fits.append(('指数 r = a*exp(-b*n)', r_fit_exp, f'a = {popt[0]:.6f}, b = {popt[1]:.6f}'))
    errors.append(error_exp)
except:
    pass

# 4. 广义幂律拟合: r = a*n^b
try:
    popt, _ = curve_fit(power_law_general, n_array, r_array, p0=[1, -0.5])
    r_fit_gen_power = power_law_general(n_array, *popt)
    error_gen_power = np.mean(np.abs(r_array - r_fit_gen_power))
    fits.append(('广义幂律 r = a*n^b', r_fit_gen_power, f'a = {popt[0]:.6f}, b = {popt[1]:.6f}'))
    errors.append(error_gen_power)
except:
    pass

# 5. 有理函数拟合: r = a/(1 + b*n)
try:
    popt, _ = curve_fit(rational_function, n_array, r_array, p0=[1, 0.1])
    r_fit_rational = rational_function(n_array, *popt)
    error_rational = np.mean(np.abs(r_array - r_fit_rational))
    fits.append(('有理函数 r = a/(1+b*n)', r_fit_rational, f'a = {popt[0]:.6f}, b = {popt[1]:.6f}'))
    errors.append(error_rational)
except:
    pass

# 6. 对数衰减拟合: r = a - b*log(n)
try:
    popt, _ = curve_fit(logarithmic_decay, n_array, r_array, p0=[1, 0.1])
    r_fit_log = logarithmic_decay(n_array, *popt)
    error_log = np.mean(np.abs(r_array - r_fit_log))
    fits.append(('对数 r = a - b*log(n)', r_fit_log, f'a = {popt[0]:.6f}, b = {popt[1]:.6f}'))
    errors.append(error_log)
except:
    pass

# 找到最佳拟合
if errors:
    best_idx = np.argmin(errors)
    best_fit_name, best_fit_values, best_params = fits[best_idx]
    best_error = errors[best_idx]

    print("=" * 60)
    print("基于曲线长度的等效半径拟合分析")
    print("=" * 60)
    print(f"最佳拟合: {best_fit_name}")
    print(f"参数: {best_params}")
    print(f"平均绝对误差: {best_error:.8f}")

    # 打印所有拟合结果
    print("\n所有拟合模型比较:")
    for i, ((name, _, params), error) in enumerate(zip(fits, errors)):
        print(f"{i + 1}. {name}")
        print(f"   参数: {params}")
        print(f"   误差: {error:.8f}")
        print()
else:
    print("所有拟合尝试都失败了！")
    best_fit_values = None

# 打印数据
print("=" * 60)
print("各曲线的长度和基于长度的等效半径:")
print("=" * 60)
print("n\t长度 L_n\t等效半径 r_n = L_n/(2π)")
for i, n in enumerate(n_values):
    print(f"{n}\t{lengths[i]:.6f}\t{r_length_values[i]:.6f}")

# 可视化结果
plt.figure(figsize=(15, 10))

# 1. 等效半径与n的关系
plt.subplot(2, 3, 1)
plt.plot(n_values, r_length_values, 'o-', color='blue', linewidth=2, markersize=4, label='实际数据')

if best_fit_values is not None:
    plt.plot(n_values, best_fit_values, 'r--', linewidth=2, label=f'最佳拟合: {best_fit_name}')

plt.xlabel('n')
plt.ylabel('等效半径 r_n')
plt.title('基于长度的等效半径与n的关系')
plt.legend()
plt.grid(True)

# 2. 曲线长度与n的关系
plt.subplot(2, 3, 2)
plt.plot(n_values, lengths, 's-', color='green', linewidth=2, markersize=4)
plt.xlabel('n')
plt.ylabel('曲线长度 L_n')
plt.title('曲线长度与n的关系')
plt.grid(True)

# 3. 不同拟合模型的误差比较
plt.subplot(2, 3, 3)
if fits:
    model_names = [fit[0] for fit in fits]
    plt.bar(range(len(model_names)), errors, color=plt.cm.Set3(range(len(model_names))))
    plt.xticks(range(len(model_names)), [name.split(' ')[0] for name in model_names], rotation=45)
    plt.ylabel('平均绝对误差')
    plt.title('不同拟合模型的误差比较')
    plt.grid(True, axis='y')

# 4. 对数坐标下的关系
plt.subplot(2, 3, 4)
plt.loglog(n_values, r_length_values, 'o-', color='purple', linewidth=2, markersize=4, label='实际数据')
if best_fit_values is not None:
    plt.loglog(n_values, best_fit_values, 'r--', linewidth=2, label='最佳拟合')
plt.xlabel('log(n)')
plt.ylabel('log(r_n)')
plt.title('对数坐标下的关系')
plt.legend()
plt.grid(True)

# 5. 残差分析
plt.subplot(2, 3, 5)
if best_fit_values is not None:
    residuals = r_array - best_fit_values
    plt.plot(n_values, residuals, 'o-', color='orange', linewidth=1, markersize=3)
    plt.axhline(0, color='red', linestyle='--', linewidth=1)
    plt.xlabel('n')
    plt.ylabel('残差')
    plt.title('最佳拟合的残差分析')
    plt.grid(True)

# 6. 前20个数据的拟合效果
plt.subplot(2, 3, 6)
n_show = n_array[:20]
r_show = r_array[:20]
plt.plot(n_show, r_show, 'o-', color='blue', linewidth=2, markersize=4, label='实际数据')

if best_fit_values is not None:
    r_fit_show = best_fit_values[:20]
    plt.plot(n_show, r_fit_show, 'r--', linewidth=2, label='最佳拟合')

plt.xlabel('n')
plt.ylabel('r_n')
plt.title('前20个数据的拟合效果')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("length_based_radius_analysis.png", dpi=300, bbox_inches='tight')
plt.show()

# 绘制前10个曲线
plt.figure(figsize=(12, 8))
colors = plt.cm.viridis(np.linspace(0, 1, 10))

for i, (node, color) in enumerate(zip(nodes[:10], colors)):
    k = node['k']
    b = node['b']
    m = node['m']

    t_values = np.linspace(0, 2 * np.pi, 1000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)

    plt.plot(x_values, y_values, color=color, alpha=0.8, linewidth=2, label=f'n={i + 1}')

plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.xlabel('x')
plt.ylabel('y')
plt.title('前10个参数曲线的形状')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("first_10_curves.png", transparent=True, dpi=300)
plt.show()

print(f"\n分析完成！")
if best_fit_values is not None:
    print(f"\n结论: 基于曲线长度的等效半径最佳拟合方程为: {best_fit_name}")
    print(f"拟合参数: {best_params}")
    print(f"拟合误差: {best_error:.8f}")