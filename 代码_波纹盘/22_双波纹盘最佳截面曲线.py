# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

# ============================
# 参数设置
# ============================
k = 2.0 / 3.0
b = 5.0 / 3.0
a = 2.0 * math.pi
m = 2.0 / 3.0
user_num = 5

# t 范围和采样点数
t_min = 2.0 * math.pi / (user_num + 1)
t_max = 2.0 * math.pi + (2.0 * user_num) * math.pi
num_samples = 1000
t_values = [t_min + i * (t_max - t_min) / (num_samples - 1) for i in range(num_samples)]

# ============================
# 连续对数积分衰减因子
# ============================
def amp_continuous(t, user_num):
    return 1.0 / ((1.0 + t/(2.0*math.pi)) * math.log(user_num+1))

# ============================
# 曲线函数
# ============================
def x_minus(t, b, k, a, t_min):
    return a * ((2.0*math.sin(t) / (b + math.sqrt(b**2 - 4.0*k*math.cos(t)))) - t_min)

def y_add(t, b, k, a, m, t_min):
    term1 = -((math.sqrt(1 + k**2) * (-math.sqrt(b**2 - 4.0*k) +
             math.sqrt(b**2 - 4.0*k*math.cos(math.pi)))) / (2.0*k))
    term2 = ((1.0 / (2.0*math.sqrt(1 + k**2))) *
            (((k**2 - 1.0)/k)*b + ((k**2 + 1.0)/k) *
             math.sqrt(b**2 - 4.0*k*math.cos(t)))) - \
            ((b*(-1.0 + k**2) + math.sqrt(b**2 - 4.0*k)*(1.0 + k**2)) /
             (2.0*k*math.sqrt(1 + k**2)))
    return a * ((m*term1 + term2) + t_min)

# ============================
# 生成曲线点 (t-x_add, t-y_minus)
# ============================
blue_points = []   # 蓝色曲线 (t, x_add)
green_points = []  # 绿色曲线 (t, y_minus)

for t in t_values:
    amp = amp_continuous(t, user_num)
    x_add_val = x_minus(t, b, k, a, t_min) * amp
    y_minus_val = y_add(t, b, k, a, m, t_min) * amp

    # 曲线点 (t, value, 0)
    blue_points.append((t, x_add_val, 0.0))     # 蓝色：t vs x_add
    green_points.append((t, y_minus_val, 0.0))  # 绿色：t vs y_minus

# ============================
# 在 Rhino 里生成曲线
# ============================
if blue_points: rs.AddInterpCurve(blue_points)
if green_points: rs.AddInterpCurve(green_points)
