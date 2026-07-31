# -*- coding: utf-8 -*-
import math
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

# 参数设置（完全保留原始参数）
a = 1
k = 2 / 3
b = 5 / 3
m = 2 / 3

# 完全保留你的原始方程
def x(t, b, k, a):
    return a * (2 * math.sin(t) / (b + math.sqrt(b ** 2 - 4 * k * math.cos(t))))

def y(t, b, k, a, m):
    term1 = -((math.sqrt(1 + k ** 2) * (-math.sqrt(b ** 2 - 4 * k) + math.sqrt(b ** 2 - 4 * k * math.cos(math.pi)))) / (2 * k))
    term2 = ((1 / (2 * math.sqrt(1 + k ** 2))) * (((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * math.sqrt(b ** 2 - 4 * k * math.cos(t))))) - ((b * (-1 + k ** 2) + math.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * math.sqrt(1 + k ** 2)))
    return a * (m * term1 + term2)

# 生成点（确保首尾闭合）
t_values = [i * 2 * math.pi / 200 for i in range(201)]  # 201点确保首尾重合
points = [rg.Point3d(x(t, b, k, a), y(t, b, k, a, m), 0) for t in t_values]

# 创建闭合曲线（正确方法）
if points:
    # 方法1：直接创建闭合插值曲线
    curve = rs.AddCurve(points, degree=3)
    if curve and rs.IsCurveClosed(curve) == False:
        # 如果未自动闭合，手动添加闭合点
        points.append(points[0])  # 添加起点使闭合
        curve = rs.AddCurve(points, degree=3)
    
    # 方法2：使用NURBS曲线确保严格闭合（备用方案）
    if not rs.IsCurveClosed(curve):
        nurbs_curve = rs.AddNurbsCurve(points, degree=3)
        if nurbs_curve:
            curve = nurbs_curve


print("封闭曲线已创建（使用AddCurve方法）")