# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

def compute_points(a1, b1, a2, b2, scale=50, steps=1000):
    points = []
    for i in range(steps + 1):
        t = -math.pi + (2 * math.pi * i / steps)
        x = math.sin(a1 * t) - math.sin(b1 * t)
        y = math.cos(b1 * t) - math.cos(a1 * t)
        points.append([x * scale, y * scale, 0])
    return points

def draw_two_parametric_curves():
    # 曲线1参数：12 和 7
    pts1 = compute_points(12, 7, 12, 7)
    rs.AddLayer("Curve_12_7", color=(0, 0, 255))  # 蓝色
    crv1 = rs.AddCurve(pts1, degree=3)
    rs.ObjectLayer(crv1, "Curve_12_7")

    # 曲线2参数：13 和 1
    pts2 = compute_points(13, 1, 1, 13)
    rs.AddLayer("Curve_15_3", color=(255, 0, 0))  # 红色
    crv2 = rs.AddCurve(pts2, degree=3)
    rs.ObjectLayer(crv2, "Curve_15_3")

draw_two_parametric_curves()

