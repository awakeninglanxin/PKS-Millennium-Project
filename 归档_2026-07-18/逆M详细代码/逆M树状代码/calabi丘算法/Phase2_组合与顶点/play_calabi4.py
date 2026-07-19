import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from stl import mesh
n = 8

slices = 49
angle=0
filename = f'play 3d图_颜色_{n}极_{slices}片 角度{angle}.obj'
# def calabi_yau(z, k1, k2, alpha):
#     exp_k1 = np.exp(2*np.pi * (1j) * k1 / n)*(np.cos(z)/z)
#     exp_k2 = np.exp(2*np.pi * (1j) * k2 / n)*(np.sin(z)/z)
#     z1 = exp_k1 * (np.cosh(z) ** (2 / n))
#     z2 = exp_k2 * (np.sinh(z) ** (2 / n))
#     return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)
def calabi_yau(z, k1, k2, alpha):
    exp_k1 = np.exp(2*np.pi * (1j) * k1 / n)*(2**z)
    exp_k2 = np.exp(2*np.pi * (1j) * k2 / n)*(2**z)
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
    # 打印重新排列后的点的数量
    print(len(points))
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


create_mesh(angle)  # 示例：生成 alpha = 0 的模型
