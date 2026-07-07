import numpy as np
import matplotlib.pyplot as plt

# 参数设置
k, b, a, m, user_num = 2/3, 5/3, 2 * np.pi, 2/3, 5
t_min = 2 * np.pi / (user_num + 1)
t_max = 2 * np.pi + (2 * user_num) * np.pi
t = np.linspace(t_min, t_max, 2000)

# 连续对数积分衰减因子
def amp_continuous(t, user_num):
    return 1.0 / ((1.0 + t/(2*np.pi)) * np.log(user_num+1))

# 原函数定义（不含衰减）
def x_fun(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t))))

def y_fun(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) +
              np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) *
             (((k**2 - 1)/k) * b + ((k**2 + 1)/k) *
             np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) /
             (2*k*np.sqrt(1 + k**2)))
    return a * (m*term1 + term2)

def x_minus(t, b, k, a, t_min):
    return a * ((2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t)))) - t_min)

def y_add(t, b, k, a, m, t_min):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) +
              np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) *
             (((k**2 - 1)/k) * b + ((k**2 + 1)/k) *
             np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) /
             (2*k*np.sqrt(1 + k**2)))
    return a * ((m*term1 + term2) + t_min)

# 计算曲线 (统一乘上 amp)
amp = amp_continuous(t, user_num)
x_vals = x_fun(t, b, k, a)
y_vals = y_fun(t, b, k, a, m)
x_vals_add = x_minus(t, b, k, a, t_min) * amp
y_vals_minus = y_add(t, b, k, a, m, t_min) * amp
middle_curve = (x_vals_add + y_vals_minus) / 2

# 绘制原始曲线
plt.figure(figsize=(10, 6))
plt.plot(t, x_vals, color='gray', label='x(t)', linestyle='--')
plt.plot(t, y_vals, color='red', label='y(t)', linestyle='--')
plt.plot(t, x_vals_add, color='blue', label='x_add(t)')
plt.plot(t, y_vals_minus, color='green', label='y_minus(t)')
plt.plot(t, middle_curve, color='purple', linestyle='--')
plt.xlabel('t'); plt.ylabel('Value')
plt.title('Plot of x(t) and y(t) with continuous log-integral decay')
plt.axis('equal'); plt.legend(); plt.grid(True)
plt.show()

# 绘制螺旋曲线，确保x、y轴等距显示
plt.figure(figsize=(10, 6))
plt.plot(x_vals, y_vals, label='Spiral Curve')
plt.plot(x_vals_add, y_vals_minus, label='Spiral Curve 2')
plt.xlabel('x(t)'); plt.ylabel('y(t)')
plt.title('Spiral Curve with continuous log-integral decay')
plt.axis('equal')  # 等距轴显示
plt.legend()
plt.grid(True)
plt.show()
