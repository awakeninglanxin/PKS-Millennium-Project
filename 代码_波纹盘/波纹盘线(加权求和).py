import numpy as np
import matplotlib.pyplot as plt
import sympy

# 使用 sympy 库获取前500个素数
# primes = list(sympy.primerange(1, 5000))[:500]
# primes =[2, 3, 5, 13, 89, 233, 1597, 28657, 514229]
primes =[1, 1, 2, 5, 13, 89, 233, 1597, 28657, 514229, 433494437, 2971215073, 99194853094755497]

# 定义计算的 x 范围
x = np.linspace(0.01, 32, 500)  # 避免 x=0 时除以0，设置为 0.01
x_filtered = x[(x >= 1) & (x <= 30)]  # 只选择 1 到 24 范围

# 定义素数序列
prime_numbers = np.array(primes)  # 转换为 NumPy 数组

# 预计算 sin(n * x) / x 并将其存储
sin_terms = np.array([np.sin(n * x_filtered) / (x_filtered) for n in prime_numbers])

# 使用广播对素数加权，并直接计算结果
y_prime_modified_filtered = np.sum(prime_numbers[:, np.newaxis] * sin_terms, axis=0)

# 绘制结果
plt.figure(figsize=(10, 6))
plt.plot(x_filtered, y_prime_modified_filtered, label="y(x) with primes (modified, x from 1 to 24)", color="purple")
plt.title("Plot of y(x) using prime numbers (modified term, x from 1 to 24)")
plt.xlabel("x")
plt.ylabel("y(x)")
# plt.axis('equal')
plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
plt.axvline(0, color='black', linewidth=0.5, linestyle='--')
plt.grid(True)
plt.legend()
plt.show()
