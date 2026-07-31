# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino.Geometry as rg
import math

# 清除现有对象
rs.EnableRedraw(False)
rs.DeleteObjects(rs.AllObjects())

# 参数设置
k, b, a, m, user_num, amp1, amp2 = 2/3, 5/3, 2 * math.pi, 2/3, 5, 1, 1
t_min = 2 * math.pi / (user_num + 1)
t_max = 2 * math.pi + (2 * user_num) * math.pi
num_points = 2000

# 生成t值序列
t_values = []
for i in range(num_points):
    t = t_min + (t_max - t_min) * i / (num_points - 1)
    t_values.append(t)

# 连续对数积分衰减因子
def amp_continuous(t, user_num):
    return 1.0 / ((1.0 + t/(2*math.pi)) * math.log(user_num + 1))

# 原函数定义（不含衰减）
def x_fun(t, b, k, a):
    denominator = b + math.sqrt(max(0, b**2 - 4 * k * math.cos(t)))
    if abs(denominator) < 1e-10:
        return 0
    return a * (2 * math.sin(t) / denominator)

def y_fun(t, b, k, a, m):
    # 确保平方根内的值为非负
    b2_minus_4k = max(0, b**2 - 4*k)
    b2_minus_4k_cost = max(0, b**2 - 4*k*math.cos(t))
    
    sqrt_b2_minus_4k = math.sqrt(b2_minus_4k)
    sqrt_b2_minus_4k_cost = math.sqrt(b2_minus_4k_cost)
    sqrt_1_plus_k2 = math.sqrt(1 + k**2)
    
    term1 = -((sqrt_1_plus_k2 * (-sqrt_b2_minus_4k + sqrt_b2_minus_4k_cost))) / (2*k)
    
    term2_numerator1 = ((k**2 - 1)/k) * b + ((k**2 + 1)/k) * sqrt_b2_minus_4k_cost
    term2_part1 = (1 / (2*sqrt_1_plus_k2)) * term2_numerator1
    
    term2_numerator2 = b * (-1 + k**2) + sqrt_b2_minus_4k * (1 + k**2)
    term2_part2 = term2_numerator2 / (2*k*sqrt_1_plus_k2)
    
    term2 = term2_part1 - term2_part2
    
    return a * (m*term1 + term2)

def x_minus(t, b, k, a, t_min, amp_val):
    base_x = x_fun(t, b, k, a)
    return base_x - a * amp_val * t_min

def y_add(t, b, k, a, m, t_min, amp_val):
    base_y = y_fun(t, b, k, a, m)
    return base_y + a * amp_val * t_min

# 计算基础曲线值 (使用amp1)
x_vals = []
y_vals = []
x_vals_add_amp1 = []
y_vals_minus_amp1 = []
middle_curve_amp1 = []

for t in t_values:
    amp_val = amp_continuous(t, user_num)
    
    x_val = x_fun(t, b, k, a)
    y_val = y_fun(t, b, k, a, m)
    x_add_val = x_minus(t, b, k, a, t_min, amp1) * amp_val
    y_minus_val = y_add(t, b, k, a, m, t_min, amp1) * amp_val
    middle_val = (x_add_val + y_minus_val) / 2
    
    x_vals.append(x_val)
    y_vals.append(y_val)
    x_vals_add_amp1.append(x_add_val)
    y_vals_minus_amp1.append(y_minus_val)
    middle_curve_amp1.append(middle_val)

# 计算基础曲线值 (使用amp2)
x_vals_add_amp2 = []
y_vals_minus_amp2 = []
middle_curve_amp2 = []

for t in t_values:
    amp_val = amp_continuous(t, user_num)
    
    x_add_val = x_minus(t, b, k, a, t_min, amp2) * amp_val
    y_minus_val = y_add(t, b, k, a, m, t_min, amp2) * amp_val
    middle_val = (x_add_val + y_minus_val) / 2
    
    x_vals_add_amp2.append(x_add_val)
    y_vals_minus_amp2.append(y_minus_val)
    middle_curve_amp2.append(middle_val)

# 顺时针旋转90°变换
def rotate_90(x, y):
    return y, -x

# 计算旋转后的曲线
def rotate_curve(x_list, y_list):
    x_rotated = []
    y_rotated = []
    for x, y in zip(x_list, y_list):
        x_rot, y_rot = rotate_90(x, y)
        x_rotated.append(x_rot)
        y_rotated.append(y_rot)
    return x_rotated, y_rotated

# 旋转基础曲线 (使用amp1)
x_vals_2, y_vals_2 = rotate_curve(x_vals, y_vals)
x_vals_3, y_vals_3 = rotate_curve(x_vals_2, y_vals_2)
x_vals_4, y_vals_4 = rotate_curve(x_vals_3, y_vals_3)

x_vals_add_amp1_2, y_vals_minus_amp1_2 = rotate_curve(x_vals_add_amp1, y_vals_minus_amp1)
x_vals_add_amp1_3, y_vals_minus_amp1_3 = rotate_curve(x_vals_add_amp1_2, y_vals_minus_amp1_2)
x_vals_add_amp1_4, y_vals_minus_amp1_4 = rotate_curve(x_vals_add_amp1_3, y_vals_minus_amp1_3)

middle_curve_amp1_2 = [(x + y) / 2 for x, y in zip(x_vals_add_amp1_2, y_vals_minus_amp1_2)]
middle_curve_amp1_3 = [(x + y) / 2 for x, y in zip(x_vals_add_amp1_3, y_vals_minus_amp1_3)]
middle_curve_amp1_4 = [(x + y) / 2 for x, y in zip(x_vals_add_amp1_4, y_vals_minus_amp1_4)]

# 旋转基础曲线 (使用amp2)
x_vals_add_amp2_2, y_vals_minus_amp2_2 = rotate_curve(x_vals_add_amp2, y_vals_minus_amp2)
x_vals_add_amp2_3, y_vals_minus_amp2_3 = rotate_curve(x_vals_add_amp2_2, y_vals_minus_amp2_2)
x_vals_add_amp2_4, y_vals_minus_amp2_4 = rotate_curve(x_vals_add_amp2_3, y_vals_minus_amp2_3)

middle_curve_amp2_2 = [(x + y) / 2 for x, y in zip(x_vals_add_amp2_2, y_vals_minus_amp2_2)]
middle_curve_amp2_3 = [(x + y) / 2 for x, y in zip(x_vals_add_amp2_3, y_vals_minus_amp2_3)]
middle_curve_amp2_4 = [(x + y) / 2 for x, y in zip(x_vals_add_amp2_4, y_vals_minus_amp2_4)]

# 创建曲线函数
def create_curve(x_values, y_values, z_offset=0):
    points = []
    for x, y in zip(x_values, y_values):
        points.append(rg.Point3d(x, y, z_offset))
    
    if len(points) >= 2:
        return rg.Curve.CreateControlPointCurve(points, 3)
    return None

# 创建并添加曲线到Rhino
def add_curves_to_rhino(x_add, y_minus, middle, z_offset, color_name):
    curves = []
    
    # x_add曲线
    curve1 = create_curve(t_values, x_add, z_offset)
    if curve1:
        sc.doc.Objects.AddCurve(curve1)
        curves.append(curve1)
    
    # y_minus曲线
    curve2 = create_curve(t_values, y_minus, z_offset)
    if curve2:
        sc.doc.Objects.AddCurve(curve2)
        curves.append(curve2)
    
    # middle曲线
    curve3 = create_curve(t_values, middle, z_offset)
    if curve3:
        sc.doc.Objects.AddCurve(curve3)
        curves.append(curve3)
    
    print("创建了{color_name}组曲线，Z偏移: {z_offset}")
    return curves

# 添加四组曲线，每组向下平移12单位
all_curves = []

# 第一组 (蓝色, z=0, 使用amp1)
all_curves.extend(add_curves_to_rhino(x_vals_add_amp1, y_vals_minus_amp1, middle_curve_amp1, 0, "蓝色"))

# 第二组 (绿色, z=-12, 使用amp2)
all_curves.extend(add_curves_to_rhino(x_vals_add_amp2_2, y_vals_minus_amp2_2, middle_curve_amp2_2, -12, "绿色"))

# 第三组 (红色, z=-24, 使用amp1)
all_curves.extend(add_curves_to_rhino(x_vals_add_amp1_3, y_vals_minus_amp1_3, middle_curve_amp1_3, -24, "红色"))

# 第四组 (黄色, z=-36, 使用amp2)
all_curves.extend(add_curves_to_rhino(x_vals_add_amp2_4, y_vals_minus_amp2_4, middle_curve_amp2_4, -36, "黄色"))

# 刷新视图
rs.EnableRedraw(True)
rs.ZoomExtents()

print("曲线创建完成！总共创建了 {len(all_curves)} 条曲线")
print("四组曲线已分别向下平移：")
print("第1组(蓝色, 使用amp1): Z = 0")
print("第2组(绿色, 使用amp2): Z = -12")
print("第3组(红色, 使用amp1): Z = -24") 
print("第4组(黄色, 使用amp2): Z = -36")