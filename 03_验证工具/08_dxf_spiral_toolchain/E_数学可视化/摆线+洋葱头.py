import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# 定义参数范围
t = np.linspace(-np.pi, np.pi, 1000)

# 计算参数方程
# 注意：由于指数运算，当sin(t)=1时会产生除零错误，需要处理
with np.errstate(divide='ignore', invalid='ignore'):
    # 计算公共部分
    base = 1 - np.sin(t)
    # 处理底数为0的情况（当sin(t)=1时）
    base[base <= 0] = np.nan  # 将非正值设为NaN以避免复数结果

    factor = base ** (-1 / 27)
    x = factor * np.cos(t)
    y = factor * np.sin(t)

# 创建图形
plt.figure(figsize=(8, 8))
plt.plot(x, y, 'b-', linewidth=1.5)
plt.title(
    'Parametric Curve: $x(t) = (1-\\sin(t))^{-1/27} \\cdot \\cos(t)$, $y(t) = (1-\\sin(t))^{-1/27} \\cdot \\sin(t)$')
plt.xlabel('x')
plt.ylabel('y')
plt.axis('equal')
plt.grid(True)
plt.show()

# 创建DXF文件 - 使用新版本的ezdxf API
doc = ezdxf.new('R2010')  # 创建新文档，指定DXF版本
msp = doc.modelspace()  # 获取模型空间

# 将曲线添加到DXF文件中
# 我们需要将点转换为DXF可用的格式
points = []
for x_i, y_i in zip(x, y):
    if not np.isnan(x_i) and not np.isnan(y_i):
        points.append((x_i, y_i))

# 创建多段线
msp.add_lwpolyline(points)

# 保存DXF文件
doc.saveas('摆线+洋葱头曲线.dxf')
print("DXF文件已保存为 '摆线+洋葱头曲线.dxf'")