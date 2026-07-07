# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math
import System
from System import Array

def create_nested_squares_with_spiral(n):
    """
    在Rhino中创建嵌套正方形和螺旋线
    """
    # 删除所有现有对象（可选）
    # rs.DeleteAllObjects()
    
    # 初始正方形参数
    center = (0.0, 0.0, 0.0)
    size = 1.0
    angle = 0.0
    
    # 创建图层
    blue_layer = "BLUE"
    if not rs.IsLayer(blue_layer):
        rs.AddLayer(blue_layer, (0, 0, 255))  # 蓝色图层
    
    gray_layer = "GRAY"
    if not rs.IsLayer(gray_layer):
        rs.AddLayer(gray_layer, (128, 128, 128))  # 灰色图层
    
    reference_layer = "REFERENCE"
    if not rs.IsLayer(reference_layer):
        rs.AddLayer(reference_layer, (0, 255, 0))  # 参考线图层
    
    spiral_layer = "SPIRAL"
    if not rs.IsLayer(spiral_layer):
        rs.AddLayer(spiral_layer, (255, 0, 0))  # 螺旋线图层(红色)
    
    # 添加x=4和x=-4的参考线
    max_extent = 2 * (math.sqrt(2) ** (n - 1))
    
    # x=4的参考线
    line1 = rs.AddLine((-4, -max_extent, 0), (-4, max_extent, 0))
    rs.ObjectLayer(line1, reference_layer)
    rs.LayerLinetype(reference_layer, "Dashed")
    
    # x=-4的参考线
    line2 = rs.AddLine((4, -max_extent, 0), (4, max_extent, 0))
    rs.ObjectLayer(line2, reference_layer)
    rs.LayerLinetype(reference_layer, "Dashed")
    
    # 收集螺旋线点
    spiral_points = []
    
    for i in range(n):
        # 计算正方形的四个顶点
        half_size = size / 2
        points = [
            (center[0] - half_size, center[1] - half_size, 0),  # 左下
            (center[0] + half_size, center[1] - half_size, 0),  # 右下
            (center[0] + half_size, center[1] + half_size, 0),  # 右上
            (center[0] - half_size, center[1] + half_size, 0),  # 左上
        ]
        
        # 旋转点
        rotated_points = []
        for point in points:
            # 平移至原点
            x, y = point[0] - center[0], point[1] - center[1]
            
            # 旋转
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            x_rot = x * cos_angle - y * sin_angle
            y_rot = x * sin_angle + y * cos_angle
            
            # 平移回原位置
            rotated_point = (x_rot + center[0], y_rot + center[1], 0)
            rotated_points.append(rotated_point)
        
        # 添加左上角顶点到螺旋线点集
        spiral_points.append(rotated_points[3])  # 左上角顶点
        
        # 绘制正方形的四条边
        for j in range(4):
            start_point = rotated_points[j]
            end_point = rotated_points[(j + 1) % 4]
            
            # 检查线段是否在|x|<=4范围内
            all_points_in_range = True
            for point in [start_point, end_point]:
                if abs(point[0]) > 4:
                    all_points_in_range = False
                    break
            
            # 在Rhino中创建线段
            line = rs.AddLine(start_point, end_point)
            
            # 设置线段图层
            if all_points_in_range:
                rs.ObjectLayer(line, blue_layer)
            else:
                rs.ObjectLayer(line, gray_layer)
        
        # 更新下一个正方形的参数
        angle += math.pi / 4  # 顺时针旋转45度
        size *= math.sqrt(2)  # 放大sqrt(2)倍
    
    # 创建螺旋线(使用内插点曲线)
    if len(spiral_points) > 1:
        # 将点列表转换为Rhino需要的点数组
        points_array = Array[System.Object](spiral_points)
        
        # 创建内插点曲线
        spiral_curve = rs.AddInterpCurve(points_array)
        rs.ObjectLayer(spiral_curve, spiral_layer)
    
    # 添加图例文本
    text_height = 0.5
    text_point = (0, -max_extent + 3, 0)
    
    text1 = rs.AddText("蓝色: |x| ≤ 4", text_point, text_height, justification=2)
    rs.ObjectLayer(text1, blue_layer)
    
    text_point = (0, -max_extent + 2, 0)
    text2 = rs.AddText("灰色: |x| > 4", text_point, text_height, justification=2)
    rs.ObjectLayer(text2, gray_layer)
    
    text_point = (0, -max_extent + 1, 0)
    text3 = rs.AddText("参考线: x=±4", text_point, text_height, justification=2)
    rs.ObjectLayer(text3, reference_layer)
    
    text_point = (0, -max_extent + 0, 0)
    text4 = rs.AddText("红色: 螺旋线", text_point, text_height, justification=2)
    rs.ObjectLayer(text4, spiral_layer)
    
    # 缩放视图以显示所有对象
    rs.ZoomExtents()
    
    print("嵌套正方形与螺旋线创建完成")
    print("包含 " + str(n) + " 个嵌套正方形和螺旋线")

# 用户可调整参数
n = 6  # 正方形数量，用户可以修改这个值

# 在Rhino中创建图形
create_nested_squares_with_spiral(n)