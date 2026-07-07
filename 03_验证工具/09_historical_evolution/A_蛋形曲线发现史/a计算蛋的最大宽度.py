import sympy as sp

# 定义符号
t = sp.symbols('t')

# 定义常量
k = 2/3
a = sp.atan(k)
b = 5/3
print('k斜率:', k)
print('a斜率的弧度:', a)
print('b中轴交点:', b)


# 定义方程 y
y = sp.sqrt(-t**2/(1 + k**2) + 1/(b - (k*t)/sp.sqrt(1 + k**2))**2)

# 计算 y 的导数
y_derivative = sp.diff(y, t)

# 求解导数为零的点
critical_points = sp.solve(y_derivative, t)

# 过滤出区间 [-0.5, 0.5] 内的实数临界点
critical_points_in_interval = []
for pt in critical_points:
    if pt.is_real and pt >= -1/2 and pt <= 1/2:
        critical_points_in_interval.append(pt)

# 在这些临界点以及区间的端点计算 y 的值
y_values = [y.subs(t, pt) for pt in critical_points_in_interval]
y_values += [y.subs(t, -1/2), y.subs(t, 1/2)]

# 找到最大值
y_max = max(y_values)
if y_max in y_values[:-2]:
    t_max = critical_points_in_interval[y_values.index(y_max)]
else:
    t_max = -1/2 if y.subs(t, -1/2) == y_max else 1/2

print('egg width:', y_max * 2)
print('Corresponding t:', t_max)
