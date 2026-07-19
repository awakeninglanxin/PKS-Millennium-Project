import numpy as np
import trimesh

# 参数设置
n_vs = [15]
n_values = [int(value * 1) for value in n_vs]
slices_values = [4] * len(n_vs)  # 大幅增加采样点数量以提高平滑度
scale_factors = list(range(len(n_vs) - 1, -1, -1))
scale_factors = [2 ** (factor / 2) for factor in scale_factors]
# alpha_v = np.pi/4 #radian
alpha_v =3.59 #radian
filename = f'smooth_calabi-yau_{len(n_vs)}_layers_{alpha_v}.obj'


def calabi_yau(z, k1, k2, alpha, n):
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


def create_mesh(n, slices, position, scale, alpha=alpha_v):
    # 创建密集采样网格
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)

    points = []
    faces = []

    vertex_count = 0

    for k1 in range(n):
        for k2 in range(n):
            # 为当前(k1,k2)对创建顶点
            vertices = []
            for i in range(slices):
                for j in range(slices):
                    z = u[i] + 1j * v[j]
                    x, y, z_val = calabi_yau(z, k1, k2, alpha, n)
                    vertices.append([x * scale, y * scale, z_val * scale])

            # 创建面
            for i in range(slices - 1):
                for j in range(slices - 1):
                    idx = i * slices + j
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

    points = np.array(points)
    faces = np.array(faces)

    mesh = trimesh.Trimesh(vertices=points + position, faces=faces)
    return mesh


# 创建所有网格
positions = []
current_height = 0
all_meshes = []

for n, slices, scale in zip(n_values, slices_values, scale_factors):
    mesh = create_mesh(n, slices, (0, current_height, 0), scale)
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

# 输出归一化比例
bounds = combined_mesh.bounds
scale_factors = bounds[1] - bounds[0]
normalized_scale = scale_factors / np.max(scale_factors)
print("Normalization scale of the combined mesh (x, y, z):")
print(f"Normalization scale: {normalized_scale}")