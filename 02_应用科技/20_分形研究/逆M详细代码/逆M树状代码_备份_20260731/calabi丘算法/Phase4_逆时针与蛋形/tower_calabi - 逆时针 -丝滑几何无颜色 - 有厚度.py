import numpy as np
import trimesh

# 参数设置
n_vs = [12]
n_values = [int(value * 1) for value in n_vs]
slices_values = [16] * len(n_vs)
scale_factors = list(range(len(n_vs) - 1, -1, -1))
scale_factors = [2 ** (factor / 2) for factor in scale_factors]
alpha_v = 0  # radian
thickness = 0.02  # 定义总厚度值
filename = f'solid_calabi-yau_{len(n_vs)}_layers_{alpha_v}_symmetric_thick.obj'


def calabi_yau(z, k1, k2, alpha, n):
    # 保持不变
    exp_k1 = np.exp(-2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(-2 * np.pi * (1j) * k2 / n)

    epsilon = 1e-10
    cosh_z = np.cosh(z)
    sinh_z = np.sinh(z)

    z1 = exp_k1 * (np.power(cosh_z + epsilon, 2 / n))
    z2 = exp_k2 * (np.power(sinh_z + epsilon, 2 / n))

    real_z1 = np.real(z1)
    real_z2 = np.real(z2)
    imag_comb = np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

    return real_z1, real_z2, imag_comb


def create_solid_mesh(n, slices, position, scale, alpha=alpha_v, thickness=thickness):
    # 创建两个曲面：底部和顶部
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)

    points = []
    faces = []
    vertex_count = 0

    # 创建两个曲面：底部和顶部
    for y_offset in [-thickness / 2, thickness / 2]:
        for k1 in range(n):
            for k2 in range(n):
                vertices = []
                for i in range(slices):
                    for j in range(slices):
                        z = u[i] + 1j * v[j]
                        x, y, z_val = calabi_yau(z, k1, k2, alpha, n)
                        # 添加y轴方向的对称偏移
                        vertices.append([x * scale, y * scale + y_offset, z_val * scale])

                # 创建面
                for i in range(slices - 1):
                    for j in range(slices - 1):
                        idx = i * slices + j
                        # 根据偏移方向决定面的朝向
                        if y_offset < 0:  # 底部曲面
                            faces.append([
                                vertex_count + idx,
                                vertex_count + idx + slices,
                                vertex_count + idx + 1
                            ])
                            faces.append([
                                vertex_count + idx + 1,
                                vertex_count + idx + slices,
                                vertex_count + idx + slices + 1
                            ])
                        else:  # 顶部曲面
                            faces.append([
                                vertex_count + idx,
                                vertex_count + idx + 1,
                                vertex_count + idx + slices
                            ])
                            faces.append([
                                vertex_count + idx + 1,
                                vertex_count + idx + slices + 1,
                                vertex_count + idx + slices
                            ])

                points.extend(vertices)
                vertex_count += len(vertices)

    # 创建连接底部和顶部的侧面
    for k1 in range(n):
        for k2 in range(n):
            # 底部和顶部曲面的顶点索引偏移
            bottom_offset = (k1 * n + k2) * slices * slices
            top_offset = (n * n * slices * slices) + bottom_offset

            # 创建四个边界上的侧面
            # 1. u = -1 边界 (最小u值)
            for j in range(slices - 1):
                bottom_idx1 = bottom_offset + j
                bottom_idx2 = bottom_offset + j + 1
                top_idx1 = top_offset + j
                top_idx2 = top_offset + j + 1

                faces.append([bottom_idx1, top_idx1, bottom_idx2])
                faces.append([bottom_idx2, top_idx1, top_idx2])

            # 2. u = 1 边界 (最大u值)
            for j in range(slices - 1):
                bottom_idx1 = bottom_offset + (slices - 1) * slices + j
                bottom_idx2 = bottom_offset + (slices - 1) * slices + j + 1
                top_idx1 = top_offset + (slices - 1) * slices + j
                top_idx2 = top_offset + (slices - 1) * slices + j + 1

                faces.append([bottom_idx1, bottom_idx2, top_idx1])
                faces.append([bottom_idx2, top_idx2, top_idx1])

            # 3. v = 0 边界 (最小v值)
            for i in range(slices - 1):
                bottom_idx1 = bottom_offset + i * slices
                bottom_idx2 = bottom_offset + (i + 1) * slices
                top_idx1 = top_offset + i * slices
                top_idx2 = top_offset + (i + 1) * slices

                faces.append([bottom_idx1, top_idx1, bottom_idx2])
                faces.append([bottom_idx2, top_idx1, top_idx2])

            # 4. v = π/2 边界 (最大v值)
            for i in range(slices - 1):
                bottom_idx1 = bottom_offset + i * slices + (slices - 1)
                bottom_idx2 = bottom_offset + (i + 1) * slices + (slices - 1)
                top_idx1 = top_offset + i * slices + (slices - 1)
                top_idx2 = top_offset + (i + 1) * slices + (slices - 1)

                faces.append([bottom_idx1, bottom_idx2, top_idx1])
                faces.append([bottom_idx2, top_idx2, top_idx1])

            # 5. 特别处理：中轴区域的侧面连接
            # 对于每个(k1,k2)对，检查是否需要与相邻的对连接
            # 这里我们假设中轴区域需要特殊的侧面连接
            if k1 == 0 or k1 == n - 1 or k2 == 0 or k2 == n - 1:
                # 这是边界情况，可能需要额外的侧面连接
                # 这里我们添加额外的侧面连接以确保中轴区域封闭
                for i in range(slices - 1):
                    # 中轴区域的特殊侧面连接
                    bottom_idx1 = bottom_offset + i * slices + slices // 2
                    bottom_idx2 = bottom_offset + (i + 1) * slices + slices // 2
                    top_idx1 = top_offset + i * slices + slices // 2
                    top_idx2 = top_offset + (i + 1) * slices + slices // 2

                    faces.append([bottom_idx1, top_idx1, bottom_idx2])
                    faces.append([bottom_idx2, top_idx1, top_idx2])

    points = np.array(points)
    faces = np.array(faces)

    mesh = trimesh.Trimesh(vertices=points + position, faces=faces)

    # 确保网格是水密的（封闭的）
    if not mesh.is_watertight:
        print("Warning: Mesh is not watertight. Attempting to fix...")
        # 尝试修复网格
        mesh.fill_holes()

    return mesh


# 创建所有网格
positions = []
current_height = 0
all_meshes = []

for n, slices, scale in zip(n_values, slices_values, scale_factors):
    mesh = create_solid_mesh(n, slices, (0, current_height, 0), scale, alpha_v, thickness)
    bounds = mesh.bounds
    height = (bounds[1][1] - bounds[0][1]) / 1.2
    positions.append((0, current_height, 0))
    current_height += height
    all_meshes.append(mesh)

# 合并所有网格
combined_mesh = trimesh.util.concatenate(all_meshes)

# 缩放和居中
bounds = combined_mesh.bounds
height = bounds[1][1] - bounds[0][1]
box_height = 1.0
scale_factor = box_height / height
combined_mesh.apply_scale(scale_factor)
combined_mesh.apply_translation(-combined_mesh.bounds.mean(axis=0))

# 保存网格
combined_mesh.export(filename)
print(f"Saved: {filename}")

# 检查网格是否是水密的
if combined_mesh.is_watertight:
    print("Mesh is watertight (closed solid).")
else:
    print("Warning: Mesh is not watertight.")

# 输出归一化比例
bounds = combined_mesh.bounds
scale_factors = bounds[1] - bounds[0]
normalized_scale = scale_factors / np.max(scale_factors)
print("Normalization scale of the combined mesh (x, y, z):")
print(f"Normalization scale: {normalized_scale}")