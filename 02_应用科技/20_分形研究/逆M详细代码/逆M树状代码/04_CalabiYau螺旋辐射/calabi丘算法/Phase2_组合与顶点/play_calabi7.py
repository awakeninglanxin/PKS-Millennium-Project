import numpy as np
import trimesh
import matplotlib.cm as cm
import matplotlib.colors as mcolors
n = 5
slices = 12
filename = f'play_3d图_颜色_{n}极_{slices}片_3图_双色渐变.obj'
# 示例调用
theta = np.pi / 4  # 角度（弧度）
angles = [0]
def calabi_yau_ring(r, theta, k1, k2, alpha):
    exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n)
    z1 = exp_k1 * (r * np.cos(theta))
    z2 = exp_k2 * (r * np.sin(theta))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_reversed_cmap(cmap_name):
    cmap = cm.get_cmap(cmap_name)
    reversed_cmap = mcolors.ListedColormap(cmap.colors[::-1])
    return reversed_cmap

def create_single_mesh(alpha, offset):
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
                    p0 = calabi_yau_ring(u[i] + 1j * v[j], theta, k1, k2, alpha)
                    p1 = calabi_yau_ring(u[i + 1] + 1j * v[j], theta, k1, k2, alpha)
                    p2 = calabi_yau_ring(u[i] + 1j * v[j + 1], theta, k1, k2, alpha)
                    p3 = calabi_yau_ring(u[i + 1] + 1j * v[j + 1], theta, k1, k2, alpha)

                    # Apply the offset to each point
                    p0 = np.array(p0) + offset
                    p1 = np.array(p1) + offset
                    p2 = np.array(p2) + offset
                    p3 = np.array(p3) + offset

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

    return points, faces, colors

def create_mesh():
    all_points = []
    all_faces = []
    all_colors = []
    offset_step = 5  # Offset step to separate the 8 models
    face_offset = 0  # Initial face offset

    for i, angle in enumerate(angles):
        offset = np.array([i % 4 * offset_step, i // 4 * offset_step, 0])  # Calculate the offset for each model
        points, faces, colors = create_single_mesh(angle, offset)
        all_points.append(points)
        all_faces.append(faces + face_offset)
        all_colors.append(colors)
        face_offset += points.shape[0]

    all_points = np.concatenate(all_points)
    all_faces = np.concatenate(all_faces)
    all_colors = np.concatenate(all_colors)

    # Save the mesh with vertex colors
    mesh = trimesh.Trimesh(vertices=all_points, faces=all_faces, vertex_colors=all_colors)
    mesh.export(filename)
    print(f"Saved: {filename}")

create_mesh()
