import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from stl import mesh
n = 12
slices = 30
alpha_steps = 3  # 将圆周分为6段
filename = f'play 3d图_颜色_{n}极_{slices}片a{alpha_steps}.obj'


# def calabi_yau(z, k1, k2, alpha):
#     # 使用非线性变换强调中心空心效果
#     scale_factor = np.exp(-np.abs(z))  # 为了使中心空心，增加一个衰减因子
#     exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n) * (np.cos(z) / (z + 1e-10))
#     exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n) * (np.sin(z) / (z + 1e-10))
#     z1 = exp_k1 * (np.cosh(z) ** (2 / n))
#     z2 = exp_k2 * (np.sinh(z) ** (2 / n))
#
#     # 应用衰减因子以调整中心和外围的密度
#     x = scale_factor * np.real(z1)
#     y = scale_factor * np.real(z2)
#     z = scale_factor * (np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2))
#
#     return x, y, z
# def calabi_yau(z, k1, k2, alpha):
#     # 调整z的幅度
#     magnitude = np.abs(z)
#     adjusted_magnitude = np.log1p(magnitude)  # 对数函数增长
#     adjusted_z = adjusted_magnitude * np.exp(1j * np.angle(z))
#
#     exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n) * (np.cos(adjusted_z) / (adjusted_z + 1e-10))
#     exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n) * (np.sin(adjusted_z) / (adjusted_z + 1e-10))
#     z1 = exp_k1 * (np.cosh(adjusted_z) ** (2 / n))
#     z2 = exp_k2 * (np.sinh(adjusted_z) ** (2 / n))
#
#     x = np.real(z1)
#     y = np.real(z2)
#     z = np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)
#
#     return x, y, z
# def calabi_yau(z, k1, k2, alpha):
#     # 使用径向调整函数
#     radial_adjustment = np.abs(z) ** 2 / (1 + np.abs(z) ** 2)  # Sigmoid-like adjustment
#
#     exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n) * (np.cos(z) / (z + 1e-10))
#     exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n) * (np.sin(z) / (z + 1e-10))
#     z1 = radial_adjustment * exp_k1 * (np.cosh(z) ** (2 / n))
#     z2 = radial_adjustment * exp_k2 * (np.sinh(z) ** (2 / n))
#
#     x = np.real(z1)
#     y = np.real(z2)
#     z = np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)
#     return x, y, z

def calabi_yau(z, k1, k2, alpha):
    # Define exponentials with additional terms to modify hollowness
    exp_k1 = np.log(2 * np.pi * (1j) * k1 / n) * (1 + np.sin(z) / (  z))
    exp_k2 = np.log(2 * np.pi * (1j) * k2 / n) * (1 + np.cos(z) / (  z))

    # Modify hyperbolic trigonometric functions to increase hollowness
    z1 = exp_k1 * (np.cosh(z) / z ** (2 / n)) * 3  # Adjust the coefficient for desired hollowness
    z2 = exp_k2 * (np.sinh(z) / z ** (2 / n)) * 3  # Adjust the coefficient for desired hollowness

    # Return modified coordinates
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

#
# def calabi_yau(z, k1, k2, alpha,scale=10.0):
#     # 反转幅度效果，通过scale参数调整中空半径
#     magnitude = np.abs(z)
#     adjusted_magnitude = 1 / (1 + scale * magnitude)  # Increase the scale to enlarge the hollow center
#     adjusted_z = adjusted_magnitude * np.log(1j * np.angle(z))
#
#     exp_k1 = np.exp(2*np.pi * (1j) * k1 / n)*(1+np.sin(adjusted_z)/(adjusted_z))
#     exp_k2 = np.exp(2*np.pi * (1j) * k2 / n)*(1+np.cos(adjusted_z)/(adjusted_z))
#     z1 = exp_k1 * (np.cosh(adjusted_z)/adjusted_z ** (2 / n))
#     z2 = exp_k2 * (np.sinh(adjusted_z)/adjusted_z ** (2 / n))
#
#     x = np.real(z1)
#     y = np.real(z2)
#     z = np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)
#     return x, y, z

# 使用这个新的 calabi_yau 函数，调整scale参数来观察中空半径的变化
def create_mesh(alpha):
    # 使用非线性变换来改变顶点分布
    u = np.tan(np.linspace(-np.pi/4, np.pi/4, slices))  # 使用正切函数调整分布
    v = np.linspace(0, np.pi / 2, slices) ** 2  # v 的平方映射以增加边缘密度
    U, V = np.meshgrid(u, v)
    points = np.array([calabi_yau(u + 1j * v, k1, k2, alpha)
                       for k1 in range(n) for k2 in range(n)
                       for u, v in zip(np.ravel(U), np.ravel(V))]).reshape(-1, 3)
    data = np.zeros(len(points) - 1, dtype=mesh.Mesh.dtype)
    for i in range(len(points) - 1):
        data['vectors'][i] = np.array([points[i], points[i + 1], [0, 0, 0]])
    m = mesh.Mesh(data)
    save_obj(filename, m)
    print(f"Saved: {filename}")

def save_obj(filename, your_mesh):
    vertices = np.vstack((your_mesh.v0, your_mesh.v1, your_mesh.v2))
    unique_vertices, indices = np.unique(vertices, return_inverse=True, axis=0)
    with open(filename, 'w') as file:
        for vertex in unique_vertices:
            file.write(f'v {vertex[0]} {vertex[1]} {vertex[2]}\n')
        for i in range(0, len(indices), 3):
            file.write(f'f {indices[i]+1} {indices[i+1]+1} {indices[i+2]+1}\n')


create_mesh(0)  # 示例：生成 alpha = 0 的模型

#
# # 验证生成模型的外观
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# filename = f'正侧视图_颜色hsv_{n}极_{slices}片a{alpha_steps}.obj'
# # 加载 OBJ 文件
# mesh = trimesh.load(filename)
# # 提取顶点和面
#
# vertices = mesh.vertices
# faces = mesh.faces
#
# face_vertices = vertices[faces]# 创建多边形集合
# collection = Poly3DCollection(face_vertices, alpha=0.1, linewidths=1, edgecolors='r')
# ax.add_collection3d(collection)
# # 自动缩放以匹配所有数据
# scale = vertices.flatten()
# ax.auto_scale_xyz(scale, scale, scale)
# plt.show()