import numpy as np  # 导入 numpy 库用于数值计算
import trimesh  # 导入 trimesh 库用于3D网格处理
import matplotlib.cm as cm  # 导入 matplotlib 的 colormap 模块用于颜色映射
import matplotlib.colors as mcolors  # 导入 matplotlib 的 colors 模块用于颜色处理

n_vs = [6, 5, 4, 3]  # 定义参数列表 n_vs
n_values = [int(value * 1) for value in n_vs]  # 将 n_vs 中的每个值乘以 1 并存储在 n_values 中
slices_values = [6] * len(n_vs)  # 定义 slices_values 列表，每个元素为 6
scale_factors = list(range(len(n_vs) - 1, -1, -1))  # 定义从 len(n_vs)-1 到 0 的 scale_factors 列表
scale_factors = [2 ** factor/2 for factor in scale_factors]  # 将 scale_factors 中的每个因子计算为 2 的次方
alpha_v = 0  # 定义 alpha_v 参数
filename = f'calabi_yau_cone_{len(n_vs)}_combined.obj'  # 定义输出文件名

def calabi_yau(z, k1, k2, alpha, n):
    exp_k1 = np.exp(2 * np.pi * (1j) * k1 / n)  # 计算 exp_k1
    exp_k2 = np.exp(2 * np.pi * (1j) * k2 / n)  # 计算 exp_k2

    # 计算半径，随着 z 的增加而减小形成锥形
    r = max(0, (1 - (z + 1) / 2))  # 半径随 z 增加而线性减小
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))  # 计算 z1
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))  # 计算 z2
    return r*np.real(z1), r*np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)  # 返回 z1 和 z2 的实部，以及 z1 和 z2 的虚部的组合

def create_reversed_cmap(cmap_name):
    cmap = cm.get_cmap(cmap_name)  # 获取指定名称的 colormap
    reversed_cmap = mcolors.ListedColormap(cmap.colors[::-1])  # 反转 colormap 的颜色
    return reversed_cmap  # 返回反转的 colormap

def create_mesh(n, slices, position, scale, alpha=alpha_v):
    u = np.linspace(-1, 1, slices)  # 生成从 -1 到 1 的线性空间数组 u
    v = np.linspace(0, np.pi / 2, slices)  # 生成从 0 到 pi/2 的线性空间数组 v

    points = []  # 初始化点列表
    colors = []  # 初始化颜色列表
    faces = []  # 初始化面列表

    for k1 in range(n):  # 遍历 k1 从 0 到 n-1
        for k2 in range(n):  # 遍历 k2 从 0 到 n-1
            for i in range(slices - 1):  # 遍历 i 从 0 到 slices-2
                for j in range(slices - 1):  # 遍历 j 从 0 到 slices-2
                    p0 = np.array(calabi_yau(u[i] + 1j * v[j], k1, k2, alpha, n)) * scale  # 计算 p0 点
                    p1 = np.array(calabi_yau(u[i + 1] + 1j * v[j], k1, k2, alpha, n)) * scale  # 计算 p1 点
                    p2 = np.array(calabi_yau(u[i] + 1j * v[j + 1], k1, k2, alpha, n)) * scale  # 计算 p2 点
                    p3 = np.array(calabi_yau(u[i + 1] + 1j * v[j + 1], k1, k2, alpha, n)) * scale  # 计算 p3 点

                    idx0 = len(points)  # 获取当前点的索引
                    idx1 = idx0 + 1  # 获取下一个点的索引
                    idx2 = idx0 + 2  # 获取再下一个点的索引
                    idx3 = idx0 + 3  # 获取最后一个点的索引

                    points.extend([p0, p1, p2, p3])  # 将 p0, p1, p2, p3 加入点列表

                    color_u = cm.get_cmap('viridis')((u[i] + 1) / 2)  # 获取 u[i] 的颜色并归一化到 [0, 1] 范围
                    color_v = cm.get_cmap('hsv_r')(v[j] / (np.pi / 2))  # 获取 v[j] 的颜色并归一化到 [0, 1] 范围
                    combined_color = (np.array(color_u[:3]) + np.array(color_v[:3])) / 2  # 平均两个颜色
                    colors.extend([combined_color, combined_color, combined_color, combined_color])  # 将颜色加入颜色列表

                    faces.append([idx0, idx1, idx2])  # 添加面索引
                    faces.append([idx1, idx3, idx2])  # 添加面索引

    points = np.array(points)  # 将点列表转换为 numpy 数组
    colors = np.array(colors)  # 将颜色列表转换为 numpy 数组
    faces = np.array(faces)  # 将面列表转换为 numpy 数组

    mesh = trimesh.Trimesh(vertices=points + position, faces=faces, vertex_colors=colors)  # 创建带有顶点颜色的网格
    return mesh  # 返回网格

# Create all meshes with different scales and positions
positions = []
current_height = 0
all_meshes = []  # 初始化所有网格的列表

for n, slices, scale in zip(n_values, slices_values, scale_factors):
    mesh = create_mesh(n, slices, (0, current_height, 0), scale)
    bounds = mesh.bounds
    height = (bounds[1][1] - bounds[0][1]) / (2 ** 0.5)  # 计算当前网格的高度
    positions.append((0, current_height, 0))
    current_height += height  # 更新当前高度
    all_meshes.append(mesh)

# Combine all meshes into one
combined_mesh = trimesh.util.concatenate(all_meshes)  # 合并所有网格

# Calculate bounding box and normalization scale
bounds = combined_mesh.bounds  # 获取合并网格的边界
height = bounds[1][1] - bounds[0][1]  # 计算合并网格的总高度

# Define the height of the cubic box
box_height = 1.0  # 例如，立方体盒子的高度设为 1.0

# Calculate scale factor to fit the mesh into the cubic box
scale_factor = box_height / height

# Scale the combined mesh to fit the cubic box
combined_mesh.apply_scale(scale_factor)

# Center the mesh in the cubic box
combined_mesh.apply_translation(-combined_mesh.bounds.mean(axis=0))

# Save the combined mesh
combined_mesh.export(filename)  # 导出合并后的网格
print(f"Saved: {filename}")  # 打印保存文件信息

# Calculate and print the normalization scale for x, y, z
bounds = combined_mesh.bounds  # 获取合并网格的边界
scale_factors = bounds[1] - bounds[0]  # 计算 xyz 的缩放因子
normalized_scale = scale_factors / np.max(scale_factors)  # 计算归一化比例

print("Normalization scale of the combined mesh (x, y, z):")  # 打印归一化比例提示
print(f"Normalization scale: {normalized_scale}")  # 打印归一化比例
