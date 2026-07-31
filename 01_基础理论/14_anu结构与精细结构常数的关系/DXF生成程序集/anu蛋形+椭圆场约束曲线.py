import numpy as np
import matplotlib.pyplot as plt
import math
from mpl_toolkits.mplot3d import Axes3D
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
# 原始蛋形曲线参数 (对应 z₀ 和 α)
b = 5/3  # z₀
a = 0.588  # α (弧度)

# 计算蛋形曲线参数
# 根据之前的推导，椭圆半焦距 c = (b * √2 / 2) * tan(2a)
c = (b * math.sqrt(2) / 2) * math.tan(2 * a)

# 计算蛋形曲线短轴半径 (当 z=0 时的最小半径)
# 从蛋形方程: x² + z² = 1/(b - y·sinα)² - (y·cosα)²
# 当 y=0 时，x² + z² = 1/b²，所以短轴半径 r = 1/b
r = 1 / b

print(f"蛋形曲线参数: b = {b}, a = {a} rad")
print(f"推导出的圆环参数: R = {c:.4f}, r = {r:.4f}")

# 生成圆环曲面点
theta = np.linspace(0, 2*np.pi, 100)
phi = np.linspace(0, 2*np.pi, 100)
theta, phi = np.meshgrid(theta, phi)

# 圆环参数方程
x = (c + r * np.cos(theta)) * np.cos(phi)
y = (c + r * np.cos(theta)) * np.sin(phi)
z = r * np.sin(theta)

# 计算蛋形方程的值用于颜色映射
# 蛋形方程: G(x,y,z) = x² + y² - 1/(b - z·sinα)² + (z·cosα)²
G_val = x**2 + y**2 - 1/(b - z * np.sin(a))**2 + (z * np.cos(a))**2

# 归一化G值用于颜色映射
G_norm = (G_val - np.min(G_val)) / (np.max(G_val) - np.min(G_val))

# 创建图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制曲面，使用蛋形方程的G值作为颜色
surf = ax.plot_surface(x, y, z, facecolors=plt.cm.viridis(G_norm),
                      alpha=0.8, linewidth=0, antialiased=True)

# 添加颜色条
mappable = plt.cm.ScalarMappable(cmap=plt.cm.viridis)
mappable.set_array(G_val)
fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=5, label='蛋形方程 G(x,y,z) 值')

# 设置坐标轴标签
ax.set_xlabel('X轴')
ax.set_ylabel('Y轴')
ax.set_zlabel('Z轴')
ax.set_title(f'基于蛋形参数的圆环结构\nb = {b:.3f}, a = {a:.3f} rad, R = {c:.3f}, r = {r:.3f}')

# 设置视角
ax.view_init(elev=30, azim=45)

plt.tight_layout()
plt.show()