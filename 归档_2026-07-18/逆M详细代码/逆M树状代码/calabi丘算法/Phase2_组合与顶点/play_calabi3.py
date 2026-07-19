import numpy as np
import trimesh
import matplotlib.cm as cm

n = 1
slices = 9
angle = 0
filename = f'play_3d图_颜色_{n}极_{slices}片_角度{angle}—单色渐变.obj'

def calabi_yau(z, k1, k2, alpha):
    exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_mesh(alpha):
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)

    points = []
    colors = []
    cmap = cm.get_cmap('viridis')  # 使用一种颜色映射

    for k1 in range(n):
        for k2 in range(n):
            for u, v in zip(np.ravel(U), np.ravel(V)):
                point = calabi_yau(u + 1j * v, k1, k2, alpha)
                points.append(point)
                color = cmap((u + 1) / 2)[:3]  # Normalize u to [0, 1] range and get RGB color
                colors.append(color)

    points = np.array(points).reshape(-1, 3)
    colors = np.array(colors)

    # Save the mesh with vertex colors
    mesh = trimesh.Trimesh(vertices=points, vertex_colors=colors)
    mesh.export(filename)
    print(f"Saved: {filename}")

create_mesh(angle)  # 示例：生成 alpha = 0 的模型
