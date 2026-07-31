import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

# 定义底部圆半径和黄金比例常数
bottom_radius = 2 * np.pi
phi = (np.sqrt(5) - 1) / 2  # 黄金比例倒数

# 用户定义的高度
user_high = 30

# 解析提供的数据
turns_num = 1364
a_values = [360, 180, 120, 90, 72]
n_values = [0, 1, 3, 6, 10]

# 生成螺旋参数方程
def spiral(t, a, n):
    x = bottom_radius * (phi ** (t / (a * np.pi / 180))) * np.cos(t) * (phi ** n)
    y = bottom_radius * (phi ** (t / (a * np.pi / 180))) * -np.sin(t) * (phi ** n)
    return x, y

# 计算螺旋变换函数
def transform_spiral(x, y):
    h1 = abs(np.log(turns_num) / np.log((-1 + np.sqrt(5)) / 2))
    z_axis = (np.log(bottom_radius / 2 * abs(x)) / np.log(phi)) * user_high / h1
    r = np.sign(x) * np.sqrt(x ** 2 + y ** 2)
    if np.sign(x) > 0:
        print(round(bottom_radius / r, 0))
    return z_axis, r

# 计算顶部圆的半径
top_radius = bottom_radius * (phi ** (2 * np.pi / (a_values[-1] * np.pi / 180))) * (phi ** n_values[-1])
print(f'底圆半径 {round(bottom_radius, 2)} / 顶圆半径 {round(top_radius, 2)} =', round((bottom_radius / top_radius), 2))

# 生成时间序列
t_values = np.linspace(0, 2 * np.pi, 500)

# 生成五段螺旋
x1, y1 = spiral(t_values, a_values[0], n_values[0])
x2, y2 = spiral(t_values, a_values[1], n_values[1])
x3, y3 = spiral(t_values, a_values[2], n_values[2])
x4, y4 = spiral(t_values, a_values[3], n_values[3])
x5, y5 = spiral(t_values, a_values[4], n_values[4])

# 创建图形
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 绘制 XY 平面投影
ax1.plot(x1, y1)
ax1.plot(x2, y2)
ax1.plot(x3, y3)
ax1.plot(x4, y4)
ax1.plot(x5, y5)

# 添加底部和顶部圆
x_add1 = bottom_radius * np.sin(t_values)
y_add1 = bottom_radius * np.cos(t_values)
x_add2 = top_radius * np.sin(t_values)
y_add2 = top_radius * np.cos(t_values)

ax1.plot(x_add1, y_add1, linestyle='--', label='Bottom Radius')
ax1.plot(x_add2, y_add2, linestyle='--', label='Top Radius')

ax1.set_xlabel('X-axis')
ax1.set_ylabel('Y-axis')
ax1.set_title('XY Plane Projection')
ax1.legend()
ax1.axis('equal')

# 采样点和变换
sampling_t1_2_3 = [0, np.pi]
sampling_t4_5 = [0, np.pi, 2 * np.pi]
points_x = []
points_y = []
labels = []

for t in sampling_t1_2_3:
    x1_s, y1_s = spiral(t, a_values[0], n_values[0])
    z1_axis, r1 = transform_spiral(x1_s, y1_s)
    points_x.append(z1_axis)
    points_y.append(r1)
    labels.append(f"[{z1_axis:.2f}, {r1:.2f}]")

for t in sampling_t1_2_3:
    x2_s, y2_s = spiral(t, a_values[1], n_values[1])
    z2_axis, r2 = transform_spiral(x2_s, y2_s)
    points_x.append(z2_axis)
    points_y.append(r2)
    labels.append(f"[{z2_axis:.2f}, {r2:.2f}]")

for t in sampling_t1_2_3:
    x3_s, y3_s = spiral(t, a_values[2], n_values[2])
    z3_axis, r3 = transform_spiral(x3_s, y3_s)
    points_x.append(z3_axis)
    points_y.append(r3)
    labels.append(f"[{z3_axis:.2f}, {r3:.2f}]")

for t in sampling_t1_2_3:
    x4_s, y4_s = spiral(t, a_values[3], n_values[3])
    z4_axis, r4 = transform_spiral(x4_s, y4_s)
    points_x.append(z4_axis)
    points_y.append(r4)
    labels.append(f"[{z4_axis:.2f}, {r4:.2f}]")

for t in sampling_t4_5:
    x5_s, y5_s = spiral(t, a_values[4], n_values[4])
    z5_axis, r5 = transform_spiral(x5_s, y5_s)
    points_x.append(z5_axis)
    points_y.append(r5)
    labels.append(f"[{z5_axis:.2f}, {r5:.2f}]")

# 确保采样点数量足够进行插值
sorted_indices = np.argsort(points_x)
points_x = np.array(points_x)[sorted_indices]
points_y = np.array(points_y)[sorted_indices]

unique_indices = np.diff(points_x) > 0
points_x = points_x[np.insert(unique_indices, 0, True)]
points_y = points_y[np.insert(unique_indices, 0, True)]

pchip = PchipInterpolator(points_x, points_y)
x_smooth = np.linspace(min(points_x), max(points_x), 500)
y_smooth = pchip(x_smooth)

# 绘制 Z 轴投影曲线
ax2.plot(x_smooth, y_smooth, color='blue', linestyle='-')
ax2.scatter(points_x, points_y, color='red')
ax2.axhline(y=0, color='gray', linestyle='--')

# 添加标签
for i, label in enumerate(labels):
    if i < len(points_x) and i < len(points_y):
        ax2.annotate(label, (points_x[i], points_y[i]), textcoords="offset points", xytext=(5, -5), ha='center')

ax2.text(0.05, 0.95, f'a1={a_values[0]}, a2={a_values[1]}, a3={a_values[2]}, a4={a_values[3]}, a5={a_values[4]}',
         transform=ax2.transAxes, fontsize=10,
         verticalalignment='top')
ax2.text(0.05, 0.90, f'n1={n_values[0]}, n2={n_values[1]}, n3={n_values[2]}, n4={n_values[3]}, n5={n_values[4]}',
         transform=ax2.transAxes, fontsize=10,
         verticalalignment='top')
ax2.text(0.05, 0.85, f'turns = {turns_num}, high={user_high}', transform=ax2.transAxes, fontsize=10, verticalalignment='top')

ax2.set_xlabel('Z-axis')
ax2.set_ylabel('X-axis')
ax2.set_title('5 Spiral Projection Curve')
ax2.axis('equal')

# 保存图像
plt.savefig('5spiral_projection.png', transparent=True)
plt.close(fig)

print("5段螺旋图像已生成并保存为 '5spiral_projection.png'")
