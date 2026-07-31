import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# 参数设置
b = np.log(2) / np.pi  # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率

d = 2.5 # 控制水平偏移的参数

t_max = 14* np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 7* np.pi
t_length = t_max - t_min
z = 15
num_t = 500  # 时间 t 的分辨率
num_theta = 100  # 椭圆的角度分辨率
num_instances = 5  # 生成的螺旋阵列数量

# leaf shape parameterization
def x(t, b, k, a):
    return -a *2*np.pi * np.cos(t)/t
def y(t, b, k, a, m):
    return -a *2*np.pi * np.sin(t)/t

# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
phi = np.linspace(-np.pi/2, np.pi/2, num_t)  # 初蛋尖朝向到末蛋尖朝向
theta = np.linspace(np.pi, 3 * np.pi, num_theta)
a = np.linspace(1, 1/81, num_t)
# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (1+np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (1+np.cos(t))
z_spiral = np.exp(b * t) *z# 修正 z 轴分量为线性关系

# 计算切线向量 T(t)、法向量 N(t) 和副法向量 B(t)
T_unit = np.zeros((num_t, 3))  # 初始化切线向量矩阵
N_unit = np.zeros((num_t, 3))  # 初始化法向量矩阵
B_unit = np.zeros((num_t, 3))  # 初始化副法向量矩阵

for i in range(num_t):
    # 计算 \hat{T}(t) 切线向量
    T_unit[i, 0] = d * (b * (np.sin(t[i]) + np.cos(t[i]))) / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))
    T_unit[i, 1] = d * (b * (np.cos(t[i]) - np.sin(t[i]))) / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))
    T_unit[i, 2] = -b * z / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))

    # 计算 \hat{N}(t) 法向量
    N_unit[i, 0] = (b * np.cos(t[i]) - np.sin(t[i])) / np.sqrt(1 + b ** 2)
    N_unit[i, 1] = (-b * np.sin(t[i]) - np.cos(t[i])) / np.sqrt(1 + b ** 2)
    N_unit[i, 2] = 0  # 法向量 z 分量为 0

    # 计算 \hat{B}(t) 副法向量
    B_unit[i, 0] = b * z * (b * np.sin(t[i]) + np.cos(t[i])) / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))
    B_unit[i, 1] = b * z * (b * np.cos(t[i]) - np.sin(t[i])) / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))
    B_unit[i, 2] = d * (b ** 2 + 1) / np.sqrt((b ** 2 + 1) * (d ** 2) + (b ** 2) * (z ** 2))


# 生成mesh圆盘的函数
def generate_thick_disc_mesh(radius, z_value, thickness, num_points=100):
    """
    生成有厚度的圆盘，带有上表面和下表面，并且连接侧面。
    参数:
    radius -- 圆盘的半径
    z_value -- 圆盘中心的 z 坐标
    thickness -- 圆盘的厚度
    num_points -- 圆周上的点的数量，用于控制圆的细腻程度
    返回:
    vertices -- 圆盘的顶点数组
    faces -- 圆盘的面数组
    """
    # 生成圆周上的角度
    theta = np.linspace(0, 2 * np.pi, num_points)

    # 生成上表面的顶点 (z = z_value)
    x_upper = radius * np.cos(theta)
    y_upper = radius * np.sin(theta)
    z_upper = np.full_like(x_upper, z_value)

    # 生成下表面的顶点 (z = z_value - thickness)
    z_lower = np.full_like(x_upper, z_value - thickness)

    # 上表面和下表面的顶点
    vertices_upper = np.column_stack((x_upper, y_upper, z_upper))
    vertices_lower = np.column_stack((x_upper, y_upper, z_lower))

    # 将顶点连接在一起，上表面、下表面和侧面
    vertices = np.vstack((vertices_upper, vertices_lower))

    # 生成面数组
    faces = []

    # 上表面的三角形面片
    for i in range(num_points - 1):
        faces.append([0, i + 1, (i + 2) % num_points])
    faces.append([0, num_points - 1, 1])  # 连接最后一个面

    # 下表面的三角形面片
    for i in range(num_points - 1):
        faces.append([num_points, num_points + i + 1, num_points + (i + 2) % num_points])
    faces.append([num_points, 2 * num_points - 1, num_points + 1])  # 连接最后一个面

    # 生成侧面的三角形面片
    for i in range(num_points - 1):
        upper1 = i
        upper2 = (i + 1) % num_points
        lower1 = num_points + i
        lower2 = num_points + (i + 1) % num_points
        faces.append([upper1, upper2, lower2])
        faces.append([upper1, lower2, lower1])

    return vertices, np.array(faces)

def rotation_matrix_z(theta):
    """
    Returns the rotation matrix for a rotation around the Z-axis by angle theta (in radians).
    """
    return np.array([[np.cos(theta), -np.sin(theta), 0],
                     [np.sin(theta), np.cos(theta), 0],
                     [0, 0, 1]])

def rotation_matrix_around_vector(v, psi):
    """
    根据任意单位向量 v 和旋转角度 psi 生成旋转矩阵.
    参数:
    v -- 单位向量 (3维向量)
    psi -- 旋转角度（以弧度为单位）
    返回值:
    3x3 的旋转矩阵
    """
    # 确保 v 是单位向量
    v = v / np.linalg.norm(v)
    # 提取向量的分量
    vx, vy, vz = v
    # 计算 K 矩阵 (叉乘矩阵)
    K = np.array([
        [0, -vz, vy],
        [vz, 0, -vx],
        [-vy, vx, 0]
    ])
    # 生成旋转矩阵 R (Rodrigues 公式)
    I = np.eye(3)
    R = I + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)
    return R

psi =np.linspace(-t_length /4,t_length /4 , num_t)  # 避免 t = 0 的问题
# theta_z=np.linspace(-np.pi/2, 0, num_t)  # 避免 t = 0 的问题
# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        # 计算变化因子 (exp(b * t) - 1 / (t + 1))
        scale_factor = np.exp(b * t[i]) - (1 / (t[i] + 1))
        # 根据公式生成椭圆在局部坐标系中的分量
        N_term = (x(theta[j], 5 / 3, 2 / 3, a[i]) * np.cos(phi[i]) - y(theta[j], 5 / 3, 2 / 3, a[i], 2 / 3) * np.sin(phi[i])) * N_unit[i]
        B_term = (x(theta[j], 5 / 3, 2 / 3, a[i]) * np.sin(phi[i]) + y(theta[j], 5 / 3, 2 / 3, a[i], 2 / 3) * np.cos(phi[i])) * B_unit[i]

        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 椭圆点，并应用尺度变化因子和旋转矩阵
        vector=np.dot(R_theta, (N_term + B_term))
        ellipse_point = scale_factor * vector
        # 计算最终曲面 C(t, θ)
        X_surface[i, j] = x_spiral[i] + ellipse_point[0]
        Y_surface[i, j] = y_spiral[i] + ellipse_point[1]
        Z_surface[i, j] = z_spiral[i] + ellipse_point[2]

vertices_spiral = np.column_stack((X_surface.flatten(), Y_surface.flatten(), Z_surface.flatten()))
# 修改中轴圆柱体参数
# 生成螺旋壳体的面
faces_spiral = []
for i in range(num_t - 1):
    for j in range(num_theta - 1):
        idx1 = i * num_theta + j
        idx2 = i * num_theta + (j + 1)
        idx3 = (i + 1) * num_theta + j
        idx4 = (i + 1) * num_theta + (j + 1)
        faces_spiral.append([idx1, idx2, idx4])
        faces_spiral.append([idx1, idx4, idx3])
faces_spiral = np.array(faces_spiral)

radius = 1000
z_cylinder = np.linspace(min(Z_surface.flatten()), max(Z_surface.flatten()), num_t)  # 圆柱高度与螺旋高度相同
theta_cylinder = np.linspace(0, 2 * np.pi, num_theta)

# 生成圆柱的 X, Y, Z 坐标
X_cylinder = np.tile(radius * np.cos(theta_cylinder), (num_t, 1))
Y_cylinder = np.tile(radius * np.sin(theta_cylinder), (num_t, 1))
Z_cylinder = np.tile(z_cylinder[:, np.newaxis], (1, num_theta))



# 生成螺旋的圆周阵列
angle_step = 2 * np.pi / num_instances  # 每个螺旋之间的角度差
vertices_combined = []
faces_combined = []

for n in range(num_instances):
    # 旋转螺旋顶点
    rotation = rotation_matrix_z(n * angle_step)
    rotated_vertices_spiral = vertices_spiral.dot(rotation.T)

    # 将旋转后的螺旋顶点添加到总顶点列表
    vertices_combined.append(rotated_vertices_spiral)

    # 处理 faces 偏移
    faces_spiral_offset = faces_spiral + len(vertices_spiral) * n
    faces_combined.append(faces_spiral_offset)

# 合并所有螺旋顶点和面
vertices_combined = np.vstack(vertices_combined)
faces_combined = np.vstack(faces_combined)
# 假设 vertices_combined 是 N x 3 的矩阵

# 提取 x 和 y 坐标
x_coords = vertices_combined[:, 0]
y_coords = vertices_combined[:, 1]
# 计算 x^2 + y^2
xy_square_sum = x_coords**2 + y_coords**2
# 找到最小值的索引
min_index = np.argmin(xy_square_sum)
max_index = np.argmax(xy_square_sum)
# 最小值的平方根
min_value = np.sqrt(xy_square_sum[min_index])
max_value = np.sqrt(xy_square_sum[max_index])

# 打印最小值的平方根
print("The smallest radius is:", min_value)

min_z = vertices_combined[min_index, 2]
print("The smallest min_z locate at:", min_z)
max_z = vertices_combined[max_index, 2]
print("The smallest max_z locate at:", max_z)
# 生成从 min_z 到 max_z 之间的 5 个平均分布的 z 值
z_values = np.linspace(min_z, max_z, 5)
# 为每个 z 平面找到最大的 sqrt(x^2 + y^2)
discs = []
for z in z_values:
    # 找到接近当前 z 值的所有点
    close_points_mask = np.isclose(vertices_combined[:, 2], z, atol=10)
    close_points = vertices_combined[close_points_mask]

    # 如果该 z 平面上有点，计算最大半径
    if len(close_points) > 0:
        x_coords_close = close_points[:, 0]
        y_coords_close = close_points[:, 1]
        # 计算 x^2 + y^2
        xy_square_sum_close = x_coords_close ** 2 + y_coords_close ** 2
        # 找到最大半径
        max_radius = np.sqrt(np.max(xy_square_sum_close))
        discs.append((z, max_radius))
thickness = 500  # 定义厚度
vertices_combined_disc = []
faces_combined_disc = []
vertex_offset = 0  # 用于处理顶点的偏移

for disc in discs:
    z_value, radius = disc
    # 为每个圆盘生成有厚度的顶点和面
    print('z_value, Disc radius:',z_value, radius)
    vertices, faces = generate_thick_disc_mesh(radius, z_value, thickness)

    # 将生成的顶点和面添加到总数组
    vertices_combined_disc.append(vertices)
    faces_combined_disc.append(faces + vertex_offset)  # 面需要根据顶点的总偏移进行调整
    vertex_offset += vertices.shape[0]  # 更新顶点偏移量

# 合并所有顶点和面
vertices_combined_disc = np.vstack(vertices_combined_disc)
faces_combined_disc = np.vstack(faces_combined_disc)

radius = min_value*2
z_cylinder = np.linspace(min(Z_surface.flatten()), max(Z_surface.flatten())*1.5, num_t)  # 圆柱高度与螺旋高度相同
theta_cylinder = np.linspace(0, 2 * np.pi, num_theta)

# 生成圆柱的 X, Y, Z 坐标
X_cylinder = np.tile(radius * np.cos(theta_cylinder), (num_t, 1))
Y_cylinder = np.tile(radius * np.sin(theta_cylinder), (num_t, 1))
Z_cylinder = np.tile(z_cylinder[:, np.newaxis], (1, num_theta))
# 合并螺旋和圆柱体
vertices_cylinder = np.column_stack((X_cylinder.flatten(), Y_cylinder.flatten(), Z_cylinder.flatten()))
faces_cylinder = []
offset = len(vertices_combined)  # 圆柱体顶点的偏移
for i in range(num_t - 1):
    for j in range(num_theta - 1):
        idx1 = offset + i * num_theta + j
        idx2 = offset + i * num_theta + (j + 1)
        idx3 = offset + (i + 1) * num_theta + j
        idx4 = offset + (i + 1) * num_theta + (j + 1)
        faces_cylinder.append([idx1, idx2, idx4])
        faces_cylinder.append([idx1, idx4, idx3])
faces_cylinder = np.array(faces_cylinder)

vertices_combined = np.vstack([vertices_combined, vertices_cylinder,vertices_combined_disc])
# faces_combined = np.vstack([faces_combined, faces_cylinder,faces_combined_disc])
faces_combined = np.vstack([faces_combined,faces_combined_disc])
# 使用 trimesh 创建网格并导出为 obj 文件
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.export('kudo_horn_with_red_axis_array.obj')

# 生成 3D 图像
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制螺旋壳曲面和圆柱
ax.plot_trisurf(vertices_combined[:, 0], vertices_combined[:, 1], vertices_combined[:, 2], triangles=faces_combined, cmap='cool', edgecolor='none')

# 设置标签
ax.set_title('3D Spiral Array with Red Central Axis')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
#
# plt.show()
