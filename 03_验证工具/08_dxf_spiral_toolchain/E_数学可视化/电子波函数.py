import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 参数设置
A = 1            # 振幅
k_x, k_y, k_z = 2*np.pi, 2*np.pi, 2*np.pi  # 波数
omega = 2*np.pi  # 角频率
phi_0 = 0        # 初始相位
t = 0.5          # 时间

# 创建空间网格
x = np.linspace(-10, 10, 200)
y = np.linspace(-10, 10, 200)
z = np.linspace(-10, 10, 200)
X, Y, Z = np.meshgrid(x, y, z)

# 计算波的电场
E = A * np.exp(1j * (k_x * X + k_y * Y + k_z * Z - phi_0)) * np.exp(-1j * omega * t)

# 获取波的实部作为可视化目标
E_real = np.real(E)

# 绘制3D波动
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X[:,:,0], Y[:,:,0], E_real[:,:,0], cmap='viridis', edgecolor='none')

# 添加标题和标签
ax.set_title('3D Wave Field (Real Part)')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Amplitude')

# 显示颜色条
fig.colorbar(surf)

plt.show()
