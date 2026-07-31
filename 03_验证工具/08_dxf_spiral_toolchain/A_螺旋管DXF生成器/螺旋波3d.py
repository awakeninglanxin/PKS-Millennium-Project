# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

# 参数设定
step = 200
t_values = [i * 0.05 - 5 for i in range(step)]  # t 从 -5 到 5
gamma = 0.2  # 控制高斯宽度
omega = 3 * math.pi  # 振荡频率
t0 = 0  # 中心时间

# 构建三维复函数轨迹
points = []
for t in t_values:
    magnitude = math.exp(-gamma * (t - t0)**2)
    real_part = magnitude * math.cos(omega * t)
    imag_part = magnitude * math.sin(omega * t)
    points.append([real_part, imag_part, t])

# 创建曲线
curve = rs.AddInterpCurve(points, 3)
rs.ZoomExtents()
