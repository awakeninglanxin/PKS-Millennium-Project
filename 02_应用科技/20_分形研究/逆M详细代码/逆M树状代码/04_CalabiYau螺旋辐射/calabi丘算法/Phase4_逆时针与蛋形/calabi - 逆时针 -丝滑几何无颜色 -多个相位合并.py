import numpy as np
import trimesh
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 参数设置
n_vs = [15]
n_values = [int(value * 1) for value in n_vs]
slices_values = [8] * len(n_vs)  # 保持文档2的高采样密度
scale_factors = list(range(len(n_vs) - 1, -1, -1))
scale_factors = [2 ** (factor / 2) for factor in scale_factors]

# 使用文档1的多alpha_v功能
alpha_v_list = [i * np.pi for i in np.arange(0, 1, 1 / 4)]  # 生成4个不同的alpha值
alpha_v_list = [np.pi/4,3*np.pi/4]  # 生成4个不同的alpha值

# 使用文档1的文件名生成方式
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = r'C:\Users\81432\PycharmProjects\pythonProject\program\calabi3d'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
filename = os.path.join(output_dir, f'smooth_calabi_yau_multialpha_{timestamp}.obj')

print(f"输出文件: {filename}")


def calabi_yau(z, k1, k2, alpha, n):
    exp_k1 = np.exp(-2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(-2 * np.pi * (1j) * k2 / n)

    epsilon = 1e-10  # 保持文档2的数值稳定性处理
    cosh_z = np.cosh(z)
    sinh_z = np.sinh(z)

    z1 = exp_k1 * (np.power(cosh_z + epsilon, 2 / n))
    z2 = exp_k2 * (np.power(sinh_z + epsilon, 2 / n))

    real_z1 = np.real(z1)
    real_z2 = np.real(z2)
    imag_comb = np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

    return real_z1, real_z2, imag_comb


def create_mesh(n, slices, position, scale, alpha):
    u = np.linspace(-np.pi / 2,np.pi / 2, slices)  # 修正u范围
    v = np.linspace(0, np.pi/ 2, slices)

    total_points = n * n * slices * slices
    points = np.zeros((total_points, 3))
    colors = np.zeros((total_points, 4))

    # 一次性计算所有顶点
    idx = 0
    for k1 in range(n):
        for k2 in range(n):
            for i in range(slices):
                for j in range(slices):
                    z = u[i] + 1j * v[j]
                    x, y, z_val = calabi_yau(z, k1, k2, alpha, n)
                    points[idx] = [x * scale, y * scale, z_val * scale]

                    # 颜色计算
                    color_val = (x + 1) / 2  # 归一化到[0,1]
                    colors[idx] = [*plt.cm.viridis(color_val)[:3], 0.1]
                    idx += 1

    # 创建统一的网格连接
    faces = []
    for k1 in range(n):
        for k2 in range(n):
            block_start = (k1 * n + k2) * slices * slices
            for i in range(slices - 1):
                for j in range(slices - 1):
                    idx = block_start + i * slices + j
                    faces.append([idx, idx + 1, idx + slices])
                    faces.append([idx + 1, idx + slices + 1, idx + slices])

    return trimesh.Trimesh(vertices=points + position, faces=faces, vertex_colors=colors)


# 创建所有网格 - 使用文档1的多alpha_v叠加方式
positions = [(0, 0, 0)] * len(n_vs) * len(alpha_v_list)  # 所有网格在同一位置叠加
all_meshes = []

for alpha_v in alpha_v_list:
    for n, slices, scale in zip(n_values, slices_values, scale_factors):
        mesh = create_mesh(n, slices, (0, 0, 0), scale, alpha_v)  # 所有网格在相同位置
        all_meshes.append(mesh)

# 合并所有网格
combined_mesh = trimesh.util.concatenate(all_meshes)

# 应用文档2的缩放和居中处理
bounds = combined_mesh.bounds
height = bounds[1][1] - bounds[0][1]
box_height = 1.0
scale_factor = box_height / height
combined_mesh.apply_scale(scale_factor)
combined_mesh.apply_translation(-combined_mesh.bounds.mean(axis=0))

# 保存网格（使用文档1的错误处理）
try:
    combined_mesh.export(filename)
    print(f"文件保存成功: {filename}")
except Exception as e:
    print(f"保存文件时出错: {e}")
    simple_filename = os.path.join(os.getcwd(), f'output_{timestamp}.obj')
    combined_mesh.export(simple_filename)
    print(f"使用备用文件名保存: {simple_filename}")

# 输出归一化比例
bounds = combined_mesh.bounds
scale_factors = bounds[1] - bounds[0]
normalized_scale = scale_factors / np.max(scale_factors)
print("合并网格的归一化比例 (x, y, z):")
print(f"归一化比例: {normalized_scale}")
print(f"使用了 {len(alpha_v_list)} 个不同的alpha值进行叠加")