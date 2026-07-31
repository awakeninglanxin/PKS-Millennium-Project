import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# 参数设置
b = np.log(2) / np.pi  # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率
d = 2.5  # 控制水平偏移的参数
t_max = 10 * np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 7 * np.pi
t_length = t_max - t_min
z = 15
num_t = 200  # 时间 t 的分辨率
num_theta = 12 # 椭圆的角度分辨率
num_instances = 1  # 生成的螺旋阵列数量


# 修改后的 leaf shape parameterization
def x1(t, a):
    """
    根据 t 的奇偶性返回 0 或 2 * a
    """
    # 使用布尔数组判断 t 的索引是偶数还是奇数
    # 这里假设 t 是一个数组索引
    # 如果 t 是一个标量，可以根据具体条件修改
    # 这里使用 t % (2 * np.pi) < np.pi 作为示例条件
    return 0.01*np.sin(t)+2*a

def y1(t, a):
    """
    始终返回 0，因为 np.sin(np.pi) = 0
    """
    return 0.01*np.cos(t)
# 修改后的 leaf shape parameterization
def x2(t, a):
    """
    根据 t 的奇偶性返回 0 或 2 * a
    """
    # 使用布尔数组判断 t 的索引是偶数还是奇数
    # 这里假设 t 是一个数组索引
    # 如果 t 是一个标量，可以根据具体条件修改
    # 这里使用 t % (2 * np.pi) < np.pi 作为示例条件
    return 0.01*np.sin(t)

def y2(t, a):
    """
    始终返回 0，因为 np.sin(np.pi) = 0
    """
    return 0.01*np.cos(t)


# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
phi = 0
theta = np.linspace(0, 2 * np.pi, num_theta)
a = np.linspace(1, 1 / 30, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (np.cos(t))
z_spiral = np.exp(b * t) * z - np.exp(b * t_min) * z  # 修正 z 轴分量为线性关系

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


def rotation_matrix_z(theta):
    """
    返回绕 Z 轴旋转 angle theta（弧度）的旋转矩阵。
    """
    return np.array([[np.cos(theta), -np.sin(theta), 0],
                     [np.sin(theta), np.cos(theta), 0],
                     [0, 0, 1]])


def rotation_matrix_y(theta):
    """
    返回绕 Y 轴旋转 angle theta（弧度）的旋转矩阵。
    """
    return np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])


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


# 修改 psi 的生成方式以匹配新的 t_length
psi = np.linspace(0, -t_length / 2, num_t)  # 避免 t = 0 的问题

# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface1 = np.zeros((num_t, num_theta))
Y_surface1 = np.zeros((num_t, num_theta))
Z_surface1 = np.zeros((num_t, num_theta))
X_surface2 = np.zeros((num_t, num_theta))
Y_surface2 = np.zeros((num_t, num_theta))
Z_surface2 = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = np.exp(b * t[i]) - (1 / (t[i] + 1))
        # 根据公式生成椭圆在局部坐标系中的分量
        N_term1 = (x1(theta[j], a[i]) * np.cos(phi) - y1(theta[j], a[i]) * np.sin(phi)) * N_unit[i]
        B_term1 = (x1(theta[j], a[i]) * np.sin(phi) + y1(theta[j], a[i]) * np.cos(phi)) * B_unit[i]

        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta1 = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 椭圆点，并应用尺度变化因子和旋转矩阵
        vector1 = np.dot(R_theta1, (N_term1 + B_term1))
        ellipse_point1 = scale_factor * vector1
        # 根据公式生成椭圆在局部坐标系中的分量
        N_term2 = (x2(theta[j], a[i]) * np.cos(phi) - y2(theta[j], a[i]) * np.sin(phi)) * N_unit[i]
        B_term2 = (x2(theta[j], a[i]) * np.sin(phi) + y2(theta[j], a[i]) * np.cos(phi)) * B_unit[i]

        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta2 = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 椭圆点，并应用尺度变化因子和旋转矩阵
        vector2 = np.dot(R_theta2, (N_term2 + B_term2))
        ellipse_point2 = scale_factor * vector2
        # 计算最终曲面 C(t, θ)
        X_surface1[i, j] = x_spiral[i] + ellipse_point1[0]
        Y_surface1[i, j] = y_spiral[i] + ellipse_point1[1]
        Z_surface1[i, j] = z_spiral[i] + ellipse_point1[2]
        X_surface2[i, j] = x_spiral[i] + ellipse_point2[0]
        Y_surface2[i, j] = y_spiral[i] + ellipse_point2[1]
        Z_surface2[i, j] = z_spiral[i] + ellipse_point2[2]

# Combine vertices for both surfaces
vertices_spiral1 = np.column_stack((X_surface1.flatten(), Y_surface1.flatten(), Z_surface1.flatten()))
vertices_spiral2 = np.column_stack((X_surface2.flatten(), Y_surface2.flatten(), Z_surface2.flatten()))

# Correctly stack both surface vertices
vertices_combined = np.vstack([vertices_spiral1, vertices_spiral2])

# Generate faces as before
# (faces_spiral1, faces_spiral2 generation unchanged)

# Now merge with cylinder vertices and faces


# Combine faces for both surfaces
faces_spiral1 = []
faces_spiral2 = []

for i in range(num_t - 1):
    for j in range(num_theta - 1):
        # Surface 1 faces
        idx1 = i * num_theta + j
        idx2 = i * num_theta + (j + 1)
        idx3 = (i + 1) * num_theta + j
        idx4 = (i + 1) * num_theta + (j + 1)
        faces_spiral1.append([idx1, idx2, idx4])
        faces_spiral1.append([idx1, idx4, idx3])

        # Surface 2 faces
        idx1 = i * num_theta + j + len(vertices_spiral1)  # Offset by the number of vertices in surface 1
        idx2 = i * num_theta + (j + 1) + len(vertices_spiral1)
        idx3 = (i + 1) * num_theta + j + len(vertices_spiral1)
        idx4 = (i + 1) * num_theta + (j + 1) + len(vertices_spiral1)
        faces_spiral2.append([idx1, idx2, idx4])
        faces_spiral2.append([idx1, idx4, idx3])

faces_spiral1 = np.array(faces_spiral1)
faces_spiral2 = np.array(faces_spiral2)

# Append faces for both spirals and cylinder
faces_combined = np.vstack([faces_spiral1, faces_spiral2])

radius = 100
theta_cylinder = np.linspace(0, 2 * np.pi, num_theta)
# 生成圆柱的 X, Y, Z 坐标
X_cylinder = np.tile(radius * np.cos(theta_cylinder), (num_t, 1))
Y_cylinder = np.tile(radius * np.sin(theta_cylinder), (num_t, 1))
z_cylinder = np.linspace(min(Z_surface1.flatten()), max(Z_surface1.flatten()) * 1.5, num_t)  # 圆柱高度与螺旋高度相同
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

vertices_combined = np.vstack([vertices_combined, vertices_cylinder])
faces_combined = np.vstack([faces_combined, faces_cylinder])
# 使用 trimesh 创建网格并导出为 obj 文件
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.export('kudo_horn_with_red_axis_array.obj')

