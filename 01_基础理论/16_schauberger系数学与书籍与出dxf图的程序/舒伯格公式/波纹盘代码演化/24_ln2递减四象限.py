import numpy as np
import matplotlib.pyplot as plt

# 参数设置
k, b, a, m, user_num,amp = 2/3, 5/3, 2 * np.pi, 2/3,5,1
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
    return a * ((2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t)))) - amp*t_min)

def y_add(t, b, k, a, m, t_min):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) +
              np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) *
             (((k**2 - 1)/k) * b + ((k**2 + 1)/k) *
             np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) /
             (2*k*np.sqrt(1 + k**2)))
    return a * ((m*term1 + term2) + amp*t_min)

# 计算曲线 (统一乘上 amp)
amp = amp_continuous(t, user_num)
x_vals = x_fun(t, b, k, a)
y_vals = y_fun(t, b, k, a, m)
x_vals_add = x_minus(t, b, k, a, t_min) * amp
y_vals_minus = y_add(t, b, k, a, m, t_min) * amp
middle_curve = (x_vals_add + y_vals_minus) / 2

# 顺时针旋转90°变换
def rotate_90(x, y):
    return y, -x

# 计算旋转后的曲线
x_vals_2, y_vals_2 = rotate_90(x_vals, y_vals)
x_vals_3, y_vals_3 = rotate_90(x_vals_2, y_vals_2)
x_vals_4, y_vals_4 = rotate_90(x_vals_3, y_vals_3)

x_vals_add_2, y_vals_minus_2 = rotate_90(x_vals_add, y_vals_minus)
x_vals_add_3, y_vals_minus_3 = rotate_90(x_vals_add_2, y_vals_minus_2)
x_vals_add_4, y_vals_minus_4 = rotate_90(x_vals_add_3, y_vals_minus_3)

middle_curve_2 = (x_vals_add_2 + y_vals_minus_2) / 2
middle_curve_3 = (x_vals_add_3 + y_vals_minus_3) / 2
middle_curve_4 = (x_vals_add_4 + y_vals_minus_4) / 2

# 绘制四种不同象限的曲线
plt.figure(figsize=(12, 8))
# 第一象限
plt.plot(t, x_vals, color='blue', linestyle='--', label='x(t) - Quadrant I')
plt.plot(t, y_vals, color='blue', linestyle='--', label='y(t) - Quadrant I')
plt.plot(t, x_vals_add, color='blue', label='x_add(t) - Quadrant I')
plt.plot(t, y_vals_minus, color='blue', label='y_minus(t) - Quadrant I')
plt.plot(t, middle_curve, color='blue', linestyle='--', label='middle_curve - Quadrant I')

# 第二象限
plt.plot(t, x_vals_2, color='green', linestyle='--', label='x(t) - Quadrant II')
plt.plot(t, y_vals_2, color='green', linestyle='--', label='y(t) - Quadrant II')
plt.plot(t, x_vals_add_2, color='green', label='x_add(t) - Quadrant II')
plt.plot(t, y_vals_minus_2, color='green', label='y_minus(t) - Quadrant II')
plt.plot(t, middle_curve_2, color='green', linestyle='--', label='middle_curve - Quadrant II')

# 第三象限
plt.plot(t, x_vals_3, color='red', linestyle='--', label='x(t) - Quadrant III')
plt.plot(t, y_vals_3, color='red', linestyle='--', label='y(t) - Quadrant III')
plt.plot(t, x_vals_add_3, color='red', label='x_add(t) - Quadrant III')
plt.plot(t, y_vals_minus_3, color='red', label='y_minus(t) - Quadrant III')
plt.plot(t, middle_curve_3, color='red', linestyle='--', label='middle_curve - Quadrant III')

# 第四象限
plt.plot(t, x_vals_4, color='yellow', linestyle='--', label='x(t) - Quadrant IV')
plt.plot(t, y_vals_4, color='yellow', linestyle='--', label='y(t) - Quadrant IV')
plt.plot(t, x_vals_add_4, color='yellow', label='x_add(t) - Quadrant IV')
plt.plot(t, y_vals_minus_4, color='yellow', label='y_minus(t) - Quadrant IV')
plt.plot(t, middle_curve_4, color='yellow', linestyle='--', label='middle_curve - Quadrant IV')

plt.xlabel('t'); plt.ylabel('Value')
plt.title('Plot of x(t) and y(t) with continuous log-integral decay in 4 quadrants')
plt.axis('equal'); plt.legend(); plt.grid(True)
plt.show()

# 绘制四种不同螺旋曲线
plt.figure(figsize=(8, 8))
plt.plot(x_vals, y_vals, label='Spiral Curve - Quadrant I')
plt.plot(x_vals_add, y_vals_minus, label='Spiral Curve - Quadrant I')
plt.plot(x_vals_2, y_vals_2, label='Spiral Curve - Quadrant II')
plt.plot(x_vals_add_2, y_vals_minus_2, label='Spiral Curve - Quadrant II')
plt.plot(x_vals_3, y_vals_3, label='Spiral Curve - Quadrant III')
plt.plot(x_vals_add_3, y_vals_minus_3, label='Spiral Curve - Quadrant III')
plt.plot(x_vals_4, y_vals_4, label='Spiral Curve - Quadrant IV')
plt.plot(x_vals_add_4, y_vals_minus_4, label='Spiral Curve - Quadrant IV')
plt.xlabel('x(t)'); plt.ylabel('y(t)')
plt.title('Spiral Curves in 4 Quadrants with Egg-shaped Forms')
plt.axis('equal')
plt.legend()
plt.grid(True)
plt.show()
