import numpy as np
import trimesh
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import os
from datetime import datetime

def lotus_fibonacci(n):
    sequence = [2, 1, 3]
    for i in range(3, n):
        next_value = sequence[-1] + sequence[-2]
        sequence.append(int(next_value))
    return sequence

def krystal_2(n):
    sequence = [1]
    for i in range(1, n):
        next_value = sequence[-1] * 2
        sequence.append(next_value)
    return sequence

# 生成前12项
n_vs = [15]
print(n_vs)
n_values = [int(value * 1) for value in n_vs]
slices_values = [4] * len(n_vs)
scale_factors = [np.log(factor) for factor in n_vs]
alpha_v_list = [i * np.pi for i in np.arange(0, 2, 1/6)]

# 修复文件名生成 - 使用简单合法的文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# 创建一个简化的描述，避免特殊字符和过长路径
filename = f'calabi_yau_merge_{timestamp}.obj'
# 或者指定一个安全的输出目录
output_dir = r'C:\Users\81432\PycharmProjects\pythonProject\program\calabi3d'  # 确保这个目录存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
filename = os.path.join(output_dir, f'calabi_yau_merge_{timestamp}.obj')

print(f"输出文件: {filename}")


def calabi_yau(z, k1, k2, alpha, n):
    exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return (np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)) ,np.real(z1), np.real(z2)

def create_reversed_cmap(cmap_name):
    cmap = plt.get_cmap(cmap_name)
    reversed_cmap = mcolors.ListedColormap(cmap.colors[::-1])
    return reversed_cmap

def create_mesh(n, slices, position, scale, alpha):
    u = np.linspace(-np.pi, np.pi, slices)
    v = np.linspace(0, np.pi / 2, slices)

    points = []
    colors = []
    faces = []

    for k1 in range(n):
        for k2 in range(n):
            for i in range(slices - 1):
                for j in range(slices - 1):
                    p0 = np.array(calabi_yau(u[i] + 1j * v[j], k1, k2, alpha, n)) * scale
                    p1 = np.array(calabi_yau(u[i + 1] + 1j * v[j], k1, k2, alpha, n)) * scale
                    p2 = np.array(calabi_yau(u[i] + 1j * v[j + 1], k1, k2, alpha, n)) * scale
                    p3 = np.array(calabi_yau(u[i + 1] + 1j * v[j + 1], k1, k2, alpha, n)) * scale

                    idx0 = len(points)
                    idx1 = idx0 + 1
                    idx2 = idx0 + 2
                    idx3 = idx0 + 3

                    points.extend([p0, p1, p2, p3])

                    z1_normalized = (np.real(p0[0]), np.real(p1[0]), np.real(p2[0]), np.real(p3[0]))
                    z2_normalized = (np.real(p0[1]), np.real(p1[1]), np.real(p2[1]), np.real(p3[1]))

                    color_z1 = plt.get_cmap('spring')(np.interp(np.mean(z1_normalized), [-1, 1], [0, 1]))
                    color_z2 = plt.get_cmap('spring')(np.interp(np.mean(z2_normalized), [-1, 1], [0, 1]))
                    combined_color = (np.array(color_z1[:3]) + np.array(color_z2[:3])) / 2
                    combined_color_with_alpha = np.append(combined_color, 0.1)

                    colors.extend([combined_color_with_alpha] * 4)

                    faces.append([idx0, idx1, idx2])
                    faces.append([idx1, idx3, idx2])

    points = np.array(points)
    colors = np.array(colors)
    faces = np.array(faces)

    mesh = trimesh.Trimesh(vertices=points + position, faces=faces, vertex_colors=colors)
    return mesh

# 确保输出目录存在
output_dir = os.path.dirname(filename)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Create all meshes with different scales and alpha values
positions = [(0, 0, 0)] * len(n_vs) * len(alpha_v_list)
all_meshes = []
for alpha_v in alpha_v_list:
    meshes = [create_mesh(n, slices, pos, scale, alpha_v) for n, slices, pos, scale in zip(n_values, slices_values, positions, scale_factors)]
    all_meshes.extend(meshes)

# Combine all meshes into one
combined_mesh = trimesh.util.concatenate(all_meshes)

# 保存文件
try:
    combined_mesh.export(filename)
    print(f"文件保存成功: {filename}")
except Exception as e:
    print(f"保存文件时出错: {e}")
    # 如果仍然出错，尝试使用更简单的文件名和路径
    simple_filename = os.path.join(os.getcwd(), f'output_{timestamp}.obj')
    combined_mesh.export(simple_filename)
    print(f"使用备用文件名保存: {simple_filename}")

# Calculate and print the normalization scale
bounds = combined_mesh.bounds
scale_factors = bounds[1] - bounds[0]
normalized_scale = scale_factors / np.max(scale_factors)

print("合并网格的归一化比例 (x, y, z):")
print(f"归一化比例: {normalized_scale}")