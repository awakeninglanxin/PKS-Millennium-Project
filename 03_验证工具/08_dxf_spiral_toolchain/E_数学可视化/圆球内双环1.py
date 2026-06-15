import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
# 设置参数
k = 0.5  # Schauberger锥常数
lambda_val = 1  # w场衰减系数
alpha = 0.5  # 投影压缩率
phi = np.pi/4  # 等角螺线的恒定螺角 (45度)
beta = 0.618  # 回流角速度系数
R_c = 5  # 临界回流半径

# 创建网格
theta = np.linspace(0, 4*np.pi, 500)
z_vals = np.linspace(-4, 4, 500)
z_vals = z_vals[z_vals != 0]  # 避免除零错误

# 计算Schauberger超双曲锥
r_cone = k / np.abs(z_vals)
Theta, Z = np.meshgrid(theta, z_vals)
R_cone = k / np.abs(Z)

# 计算w场
w = np.exp(-lambda_val * (R_cone**2 + Z**2))

# 四维投影到三维空间
X_cone = R_cone * np.cos(Theta) * w**alpha
Y_cone = R_cone * np.sin(Theta) * w**alpha
Z_cone = Z * w**alpha

# 生成等角螺线
r0 = 0.1  # 初始半径
r_spiral = r0 * np.exp(theta * 1/np.tan(phi))  # 等角螺线方程
z_spiral = k / r_spiral

# 计算螺线上的w场
w_spiral = np.exp(-lambda_val * (r_spiral**2 + z_spiral**2))

# 应用回流条件
for i in range(len(theta)):
    if r_spiral[i] > R_c:
        # 角速度反转 (回流效应)
        theta[i:] = theta[i] - beta * (theta[i:] - theta[i])
        # 更新回流后的螺线
        r_spiral[i:] = R_c * np.exp(-(theta[i:] - theta[i]) * np.tan(phi))

# 投影螺线到三维空间
X_spiral = r_spiral * np.cos(theta) * w_spiral**alpha
Y_spiral = r_spiral * np.sin(theta) * w_spiral**alpha
Z_spiral = z_spiral * w_spiral**alpha

# 创建图形
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# 绘制Schauberger锥面
surf = ax.plot_surface(X_cone, Y_cone, Z_cone, alpha=0.3,
                      cmap='viridis', linewidth=0, antialiased=True)

# 绘制等角螺线
ax.plot(X_spiral, Y_spiral, Z_spiral, 'r-', linewidth=2, label='等角螺线')

# 标记关键区域
ax.scatter(0, 0, 0, c='black', s=100, marker='*', label='银心')
ax.scatter(X_spiral[-1], Y_spiral[-1], Z_spiral[-1],
          c='blue', s=50, marker='o', label='银晕环')

# 设置图形属性
ax.set_xlabel('X (kpc)')
ax.set_ylabel('Y (kpc)')
ax.set_zlabel('Z (kpc)')
ax.set_title('Schauberger超双曲锥四维投影银河模型', fontsize=14)
ax.legend()

# 添加光照效果
ls = LightSource(azdeg=315, altdeg=45)
rgb = ls.shade(Z_cone, plt.cm.viridis)

plt.tight_layout()
plt.show()

# 额外绘制二维投影视图
plt.figure(figsize=(12, 5))

# XY平面投影
plt.subplot(121)
plt.plot(X_spiral, Y_spiral, 'r-', linewidth=2)
plt.xlabel('X (kpc)')
plt.ylabel('Y (kpc)')
plt.title('银盘平面投影')
plt.grid(True)
plt.axis('equal')

# XZ平面投影
plt.subplot(122)
plt.plot(X_spiral, Z_spiral, 'r-', linewidth=2)
plt.xlabel('X (kpc)')
plt.ylabel('Z (kpc)')
plt.title('银晕侧面投影')
plt.grid(True)

plt.tight_layout()
plt.show()