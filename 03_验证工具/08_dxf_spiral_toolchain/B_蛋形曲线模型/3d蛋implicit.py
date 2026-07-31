# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import math

def solve_z_min():
    """数值求解 2^z = z^2 的最小 z（负解）"""
    z = -1.0  # 更合适的初始值
    for _ in range(100):
        f = 2**z - z**2
        df = math.log(2) * 2**z - 2*z
        z_new = z - f / df
        if abs(z_new - z) < 1e-6:
            return z_new
        z = z_new
    return z

def generate_egg_nonlinear_sampling():
    # 计算 z 的有效范围
    z_min = solve_z_min()
    print('z_min:', z_min)
    z_max = 2.0
    print("z range: [{0:.3f}, {1}]".format(z_min, z_max))

    # 非线性采样参数
    delta_z0 = 0.1  # 更小的初始步长
    k1 = 3.0          # 更大的衰减系数
    k2 = 1.5
    # 生成 z 值（非线性采样）
    z_values = []
    
    # 负半轴采样（从0向z_min方向采样）
    z = 0
    while z >= z_min:
        z_values.append(z)
        delta_z = delta_z0 * math.exp(-k1 * abs(z))
        z -= delta_z  # 注意这里是减
    
    # 正半轴采样（从0到z_max）
    z = 0
    while z <= z_max:
        if z not in z_values:  # 避免重复添加z=0
            z_values.append(z)
        delta_z = delta_z0 * math.exp(-k2 * abs(z))
        z += delta_z

    # 确保z_min和z_max被精确包含
    if z_min not in z_values:
        z_values.append(z_min)
    if z_max not in z_values:
        z_values.append(z_max)
    
    # 排序z值
    z_values.sort()

    # 生成截面圆
    circles = []
    for z in z_values:
        r_squared = 2**z - z**2
        if r_squared <= 0:
            # 处理零或负半径的情况
            radius = 0.01  # 很小的半径而不是零
        else:
            radius = math.sqrt(r_squared)
        
        # 添加圆
        try:
            circle = rs.AddCircle((0, 0, z), radius)
            if circle:
                circles.append(circle)
        except:
            print("无法在z={z}处创建圆，半径={radius}")

    # 用Loft生成封闭实体
    if len(circles) >= 2:
        loft = rs.AddLoftSrf(circles, loft_type=1)  # loft_type=1表示"封闭"
        if loft:
            print("蛋形实体生成成功！")
            return loft
    else:
        print("错误：未生成足够的截面圆！可用圆数量:", len(circles))
    return None

# 执行
if __name__ == "__main__":
    rs.EnableRedraw(False)
    generate_egg_nonlinear_sampling()
    rs.EnableRedraw(True)