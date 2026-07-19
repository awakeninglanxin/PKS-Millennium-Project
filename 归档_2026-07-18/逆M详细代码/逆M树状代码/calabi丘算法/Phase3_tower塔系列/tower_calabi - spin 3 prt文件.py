import numpy as np  # 导入 numpy 库用于数值计算
import trimesh  # 导入 trimesh 库用于3D网格处理
import matplotlib.cm as cm  # 导入 matplotlib 的 colormap 模块用于颜色映射
import matplotlib.colors as mcolors  # 导入 matplotlib 的 colors 模块用于颜色处理

# Parameters
n_vs = [42, 30, 20, 12, 6]
# n_vs = [6,4,3]
n_values = [int(value * 1) for value in n_vs]
slices_values = [8] * len(n_vs)
scale_factors = list(range(len(n_vs) - 1, -1, -1))
scale_factors = [2 ** (factor / 2) for factor in scale_factors]
alpha_v = np.pi
filename_obj = f'calabi-Yau不动3d图_{len(n_vs)}图合一{alpha_v}_2^n.obj'
filename_prt = filename_obj.replace('.obj', '.prt')  # 修改为 PRT 格式
thickness = 0.01  # 面的厚度

def calabi_yau(z, k1, k2, alpha, n):
    exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n)
    exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_reversed_cmap(cmap_name):
    cmap = cm.get_cmap(cmap_name)
    reversed_cmap = mcolors.ListedColormap(cmap.colors[::-1])
    return reversed_cmap

def create_mesh(n, slices, position, scale, alpha=alpha_v):
    u = np.linspace(-1, 1, slices)
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

                    color_u = cm.get_cmap('viridis')((u[i] + 1) / 2)
                    color_v = cm.get_cmap('hsv_r')(v[j] / (np.pi / 2))
                    combined_color = (np.array(color_u[:3]) + np.array(color_v[:3])) / 2
                    colors.extend([combined_color] * 4)

                    # 计算厚度面的位置
                    p0_bottom = p0 - np.array([0, thickness / 2, 0])
                    p1_bottom = p1 - np.array([0, thickness / 2, 0])
                    p2_bottom = p2 - np.array([0, thickness / 2, 0])
                    p3_bottom = p3 - np.array([0, thickness / 2, 0])

                    points.extend([p0_bottom, p1_bottom, p2_bottom, p3_bottom])
                    idx4 = len(points) - 4
                    idx5 = idx4 + 1
                    idx6 = idx4 + 2
                    idx7 = idx4 + 3

                    # 创建厚度面的面
                    faces.append([idx0, idx1, idx2])
                    faces.append([idx1, idx3, idx2])
                    faces.append([idx4, idx6, idx5])  # 下表面
                    faces.append([idx5, idx6, idx7])  # 下表面
                    faces.append([idx0, idx2, idx4])  # 连接上下表面
                    faces.append([idx2, idx6, idx4])
                    faces.append([idx1, idx5, idx3])  # 连接上下表面
                    faces.append([idx3, idx5, idx7])

    points = np.array(points)
    colors = np.array(colors)
    faces = np.array(faces)

    mesh = trimesh.Trimesh(vertices=points + position, faces=faces, vertex_colors=colors)
    return mesh

def create_disk(radius, thickness, position=(0, 0, 0)):
    disk = trimesh.creation.cylinder(radius=radius, height=thickness, sections=64)
    rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    disk.apply_translation(position)
    disk.apply_transform(rotation_matrix)
    disk.visual.vertex_colors = [0, 0, 255, 255]  # Blue color for the disk
    return disk

def create_cylinder_with_area(target_area, height, position=(0, 0, 0)):
    radius = np.sqrt(target_area / np.pi)
    cylinder = trimesh.creation.cylinder(radius=radius, height=height, sections=32)
    rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    cylinder.apply_translation(position)
    cylinder.apply_transform(rotation_matrix)
    cylinder.visual.vertex_colors = [255, 0, 0, 255]  # Red color for the cylinder
    return cylinder

# Create all meshes with different scales and positions
positions = []
current_height = 0
all_meshes = []

for n, slices, scale in zip(n_values, slices_values, scale_factors):
    mesh = create_mesh(n, slices, (0, current_height, 0), scale)
    bounds = mesh.bounds
    height = (bounds[1][1] - bounds[0][1]) / 1.2
    print("height:", height)
    positions.append((0, current_height, 0))

    # Insert disk in the middle of the current mesh
    disk_position = (0, 0, -current_height)
    disk = create_disk(radius=1 * scale, thickness=0.02, position=disk_position)

    # Update current height for the next mesh
    current_height += height
    all_meshes.append(mesh)
    all_meshes.append(disk)  # Add disk to the mesh list

# Combine all meshes into one
combined_mesh = trimesh.util.concatenate(all_meshes)

# Calculate bounding box and normalization scale
bounds = combined_mesh.bounds
height = bounds[1][1] - bounds[0][1]

hull = combined_mesh.convex_hull
hull_area = hull.area
hull_high = hull.bounds[1][2]
# Define the target area for the cylinder's base
target_area = hull_area / 1100
print('target_area:', target_area)
# Calculate scale factor to fit the mesh into the cubic box
cylinder_height = height
print('轴高:', height)
cylinder_position = (0, 0, 0)
# Create the cylinder with the target area
cylinder_mesh = create_cylinder_with_area(target_area, -cylinder_height * 1.55, cylinder_position)

# Center the mesh in the cubic box
combined_with_cylinder_and_disk = trimesh.util.concatenate([combined_mesh, cylinder_mesh])
# Save the combined mesh
combined_with_cylinder_and_disk.export(filename_obj)
print(f"Saved: {filename_obj}")

# 保存为 STL 格式
filename_stl = filename_obj.replace('.obj', '.stl')
combined_with_cylinder_and_disk.export(filename_stl)
print(f"Saved: {filename_stl}")
