# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

def draw_parametric_curve_adaptive(a, b, c, d):
    t_start = -math.pi
    t_end = math.pi
    avg_num_points = ((a + b)/2)*3  # 平均点数基于 (a+b)/2
    min_step = 1e-5        # 最小步长（避免极端密集）
    max_step = (t_end - t_start) / ((a + b)/32)  # 最大步长（避免极端稀疏）

    # 先计算总"速度积分"，用于归一化
    def compute_speed(t):
        # 求导：dx/dt = a*cos(a*t) - b*cos(b*t)
        #       dy/dt = -c*sin(c*t) + d*sin(d*t)
        dx_dt = a * math.cos(a * t) - b * math.cos(b * t)
        dy_dt = -c * math.sin(c * t) + d * math.sin(d * t)
        speed = math.sqrt(dx_dt**2 + dy_dt**2)
        return speed + 1e-6  # 避免除零错误

    # 自适应采样
    points = []
    t = t_start
    while t <= t_end:
        # 计算当前点
        x = math.sin(a * t) - math.sin(b * t)
        y = math.cos(c * t) - math.cos(d * t)
        points.append((x, y, 0))

        # 计算当前速度，并动态调整步长
        speed = compute_speed(t)
        step = (t_end - t_start) / avg_num_points / speed  # 速度越大，步长越小
        step = max(min_step, min(step, max_step))  # 限制步长范围

        t += step

    # 创建曲线
    curve = rs.AddCurve(points)
    print("曲线控制点数量:", len(points))
    return curve

# 调用函数绘制自适应曲线（示例参数：296, 298, 291, 303）
curve = draw_parametric_curve_adaptive(296, 298, 291, 303)