import numpy as np
import matplotlib.pyplot as plt

# Constants
a = 1
num_egg = 8  # 你可以根据需要设置 num_egg（例如：3 或 6）

# 推导公式：根据 num_egg 动态生成 nodes
def generate_nodes(num_egg):
    nodes = []
    for i in range(1, num_egg):
        k = (4**i / 6)  # k 的递推关系
        b = (5*2**i / 6)  # b 的递推关系
        m = 2 / 3  # m 固定
        amp = (2**i) / (np.sqrt(9 + 2**(4*i - 2))) #这个对应Ln的倒数
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

# 根据 num_egg 生成节点
nodes = generate_nodes(num_egg)

# 第一张图：原始曲线
plt.figure(figsize=(10, 6))
for node in nodes:
    k, b, m, amp, label = node['k'], node['b'], node['m'], node['amp'], node['label']
    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a)
    y_values = y(t_values, b, k, a, m)
    plt.plot(x_values, y_values)

plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.xlabel('x')
plt.ylabel('y')
plt.title(f'Original Curves for num_egg={num_egg}')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')
plt.savefig(f"original_curves_num_egg={num_egg}.png", transparent=True)
plt.show()

# 第二张图：幅度缩放后的曲线
plt.figure(figsize=(10, 6))
for node in nodes:
    k, b, m, amp, label = node['k'], node['b'], node['m'], node['amp'], node['label']
    t_values = np.linspace(0, 2 * np.pi, 2000)
    x_values = x(t_values, b, k, a) * amp
    y_values = y(t_values, b, k, a, m) * amp
    plt.plot(x_values, y_values)

plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.xlabel('x')
plt.ylabel('y')
plt.title(f'Amplitude Scaled Curves for num_egg={num_egg}')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')
plt.savefig(f"scaled_curves_num_egg={num_egg}.png", transparent=True)
plt.show()
