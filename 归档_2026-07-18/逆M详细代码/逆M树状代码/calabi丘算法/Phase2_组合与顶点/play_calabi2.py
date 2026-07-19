import numpy as np
import trimesh
import matplotlib.cm as cm
import matplotlib.colors as mcolors

n = 12
slices = 12
angle = 0
filename = f'play_3d图_颜色_{n}极_{slices}片_角度{angle}—双色渐变4.obj'

def calabi_yau(z, k1, k2, alpha):
    exp_k1 = np.exp(2 * np.pi * (-1j) * k1 / n)
    exp_k2 = np.exp(2 * np.pi * (-1j) * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = -exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_reversed_cmap(cmap_name):
    cmap = cm.get_cmap(cmap_name)
    reversed_cmap = mcolors.ListedColormap(cmap.colors[::-1])
    return reversed_cmap

def create_mesh(alpha):
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)
    U, V = np.meshgrid(u, v)

    points = []
    colors = []
    faces = []

    for k1 in range(n):
        for k2 in range(n):
            for i in range(slices - 1):
                for j in range(slices - 1):
                    p0 = calabi_yau(u[i] + 1j * v[j], k1, k2, alpha)
                    p1 = calabi_yau(u[i + 1] + 1j * v[j], k1, k2, alpha)
                    p2 = calabi_yau(u[i] + 1j * v[j + 1], k1, k2, alpha)
                    p3 = calabi_yau(u[i + 1] + 1j * v[j + 1], k1, k2, alpha)

                    idx0 = len(points)
                    idx1 = idx0 + 1
                    idx2 = idx0 + 2
                    idx3 = idx0 + 3

                    points.extend([p0, p1, p2, p3])

                    color_u = cm.get_cmap('viridis')((u[i] + 1) / 2)  # Normalize u to [0, 1] range
                    color_v = cm.get_cmap('hsv_r')(v[j] / (np.pi / 2))  # Normalize v to [0, 1] range
                    combined_color = (np.array(color_u[:3]) + np.array(color_v[:3])) / 2  # Average the two colors
                    colors.extend([combined_color, combined_color, combined_color, combined_color])

                    faces.append([idx0, idx1, idx2])
                    faces.append([idx1, idx3, idx2])

    points = np.array(points)
    colors = np.array(colors)
    faces = np.array(faces)

    # Save the mesh with vertex colors
    mesh = trimesh.Trimesh(vertices=points, faces=faces, vertex_colors=colors)
    mesh.export(filename)
    print(f"Saved: {filename}")

create_mesh(angle)  # 示例：生成 alpha = 0 的模型
