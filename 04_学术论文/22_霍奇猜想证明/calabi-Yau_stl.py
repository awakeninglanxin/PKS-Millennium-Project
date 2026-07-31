import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh

# 初始化参数
n = 3
slices = 81
alpha_steps =6  # 将圆周分为4段

def calabi_yau(z, k1, k2, alpha):
    exp_k1 = np.exp(2 * np.pi * 1j * k1 / n)
    exp_k2 = np.exp(2 * np.pi * 1j * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_mesh(alpha):
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)
    points = np.array([calabi_yau(u + 1j * v, k1, k2, alpha)
                       for k1 in range(n) for k2 in range(n)
                       for u, v in zip(np.ravel(U), np.ravel(V))]).reshape(-1, 3)
    data = np.zeros(len(points) - 1, dtype=mesh.Mesh.dtype)
    for i in range(len(points) - 1):
        data['vectors'][i] = np.array([points[i], points[i + 1], [0, 0, 0]])  # 生成三角面片
    m = mesh.Mesh(data)
    filename = f'正侧视图_颜色hsv_{n}极_{slices}片.stl'
    m.save(filename)
    print(f"Saved: {filename}")

# # 生成STL文件
# for i in range(alpha_steps):
#     create_mesh(np.pi * i / alpha_steps)
create_mesh(0)

# 验证生成模型的外观
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 加载并绘制STL文件
filename = f'正侧视图_颜色hsv_{n}极_{slices}片.stl'
your_mesh = mesh.Mesh.from_file(filename)
poly3d = [[your_mesh.v0[i], your_mesh.v1[i], your_mesh.v2[i]] for i in range(len(your_mesh.v0))]
collection = Poly3DCollection(poly3d, alpha=0.1, linewidths=1, edgecolors='r')
ax.add_collection3d(collection)

# 设置图形的缩放比例
scale = your_mesh.points.flatten()
ax.auto_scale_xyz(scale, scale, scale)

plt.show()
