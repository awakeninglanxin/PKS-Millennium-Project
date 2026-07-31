import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

n = 12
slices = 12
alpha_steps = 3  # 将圆周分为6段
filename = f'正侧视图_颜色_{n}极_{slices}片a{alpha_steps}_圆台.obj'

def calabi_yau(z, k1, k2, alpha):
    exp_k1 = np.exp(2 * np.pi * 1j * k1 / n)
    exp_k2 = np.exp(2 * np.pi * 1j * k2 / n)

    # 半径随着 z 值变化，形成圆台形状
    r = max(0, (1 - (z + 1) / 2))  # 半径随 z 增加而线性减小
    z1 = exp_k1 * (np.cosh(z) ** (2 / n)) * r
    z2 = exp_k2 * (np.sinh(z) ** (2 / n)) * r
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_mesh(alpha):
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)

    points = np.array([calabi_yau(u + 1j * v, k1, k2, alpha)
                       for k1 in range(n) for k2 in range(n)
                       for u, v in zip(np.ravel(U), np.ravel(V))]).reshape(-1, 3)

    # 创建顶点索引
    faces = []
    for i in range(slices - 1):
        for j in range(slices - 1):
            idx1 = i * slices + j
            idx2 = idx1 + 1
            idx3 = idx1 + slices
            idx4 = idx3 + 1
            faces.append([idx1, idx2, idx3])
            faces.append([idx2, idx4, idx3])

    faces = np.array(faces)

    # 保存为 OBJ 文件
    save_obj(filename, points, faces)
    print(f"Saved: {filename}")

def save_obj(filename, vertices, faces):
    unique_vertices, indices = np.unique(vertices, return_inverse=True, axis=0)
    with open(filename, 'w') as file:
        for vertex in unique_vertices:
            file.write(f'v {vertex[0]} {vertex[1]} {vertex[2]}\n')
        for i in range(len(faces)):
            file.write(f'f {indices[faces[i][0]] + 1} {indices[faces[i][1]] + 1} {indices[faces[i][2]] + 1}\n')

create_mesh(0)  # 示例：生成 alpha = 0 的模型

# 验证生成模型的外观
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 加载 OBJ 文件
mesh = trimesh.load(filename)

# 提取顶点和面
vertices = mesh.vertices
faces = mesh.faces

face_vertices = vertices[faces]  # 创建多边形集合
collection = Poly3DCollection(face_vertices, alpha=0.1, linewidths=1, edgecolors='r')
ax.add_collection3d(collection)

# 自动缩放以匹配所有数据
scale = vertices.flatten()
ax.auto_scale_xyz(scale, scale, scale)
plt.show()
