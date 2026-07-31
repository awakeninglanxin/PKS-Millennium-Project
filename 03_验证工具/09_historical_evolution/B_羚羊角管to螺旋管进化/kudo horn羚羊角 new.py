import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# 参数设置
b = np.log(2) / np.pi  # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率
a = 1  # 蛋大小
d = 2  # 控制水平偏移的参数
phi = 0  # 椭圆旋转角度 Φ
t_max = 12 * np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 2 * np.pi
t_length=t_max-t_min
z = 10
num_t = 500  # 时间 t 的分辨率
num_theta = 100  # 椭圆的角度分辨率

# # Egg shape parameterization
# def x(t, b, k, a):
#     return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))/t
#
# def y(t, b, k, a, m):
#     term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
#     term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
#             ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
#                 ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
#     return -a * (m * term1 + term2)/t

# leaf shape parameterization
def x(t, b, k, a):
    return -a *np.pi*np.cos(t)/t

def y(t, b, k, a, m):
    return -a*np.pi*np.sin(t)/t
# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
# theta = np.linspace(-1.5* np.pi, 0 * np.pi, num_theta)  #egg
theta = np.linspace(np.pi, 3 * np.pi, num_theta) #2
phi_gr=(np.sqrt(5)-1/2)
# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * np.sin(t)  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * np.cos(t)
z_spiral = z*t**2 # 修正 z 轴分量为线性关系

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

psi = -t_length/2 # 旋转角度90度

# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        # 计算变化因子 (exp(b * t) - 1 / (t + 1))
        scale_factor = np.exp(b * t[i]) - (1 / (t[i] + 1))
        # 根据标记 (7) 的公式生成椭圆在局部坐标系中的分量
        N_term = (x(theta[j], 5 / 3, 2 / 3, 1) * np.cos(phi) - y(theta[j], 5 / 3, 2 / 3, 1, 2 / 3) * np.sin(phi)) * N_unit[i]
        B_term = (x(theta[j], 5 / 3, 2 / 3, 1) * np.sin(phi) + y(theta[j], 5 / 3, 2 / 3, 1, 2 / 3) * np.cos(phi)) * B_unit[i]

        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi)

        # 椭圆点，并应用尺度变化因子和旋转矩阵
        ellipse_point = scale_factor * np.dot(R_theta, (N_term + B_term))

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
radius = 50
z_cylinder = np.linspace(min(Z_surface.flatten()), max(Z_surface.flatten()), num_t)  # 圆柱高度与螺旋高度相同
theta_cylinder = np.linspace(0, 2 * np.pi, num_theta)

# 生成圆柱的 X, Y, Z 坐标
X_cylinder = np.tile(radius * np.cos(theta_cylinder), (num_t, 1))
Y_cylinder = np.tile(radius * np.sin(theta_cylinder), (num_t, 1))
Z_cylinder = np.tile(z_cylinder[:, np.newaxis], (1, num_theta))

# 生成 3D 图像
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制螺旋壳曲面
ax.plot_surface(X_surface, Y_surface, Z_surface, cmap='cool', edgecolor='none')

# 绘制中轴圆柱 (红色)
ax.plot_surface(X_cylinder, Y_cylinder, Z_cylinder, color='red', edgecolor='none')

# 设置标签
ax.set_title('3D Spiral Shell Model with Red Central Axis')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()

# --------- 导出到 obj 文件 -----------

# 创建螺旋面顶点数组
vertices = np.column_stack((X_surface.flatten(), Y_surface.flatten(), Z_surface.flatten()))

# 创建圆柱顶点数组
vertices_cylinder = np.column_stack((X_cylinder.flatten(), Y_cylinder.flatten(), Z_cylinder.flatten()))

# 合并原来的螺旋面顶点与圆柱顶点
vertices_combined = np.vstack([vertices, vertices_cylinder])

# 创建圆柱顶点数组
vertices_cylinder = np.column_stack((X_cylinder.flatten(), Y_cylinder.flatten(), Z_cylinder.flatten()))

# 创建圆柱的 faces
faces_cylinder = []
offset = len(vertices_spiral)  # 圆柱体顶点的偏移
for i in range(num_t - 1):
    for j in range(num_theta - 1):
        idx1 = offset + i * num_theta + j
        idx2 = offset + i * num_theta + (j + 1)
        idx3 = offset + (i + 1) * num_theta + j
        idx4 = offset + (i + 1) * num_theta + (j + 1)
        faces_cylinder.append([idx1, idx2, idx4])
        faces_cylinder.append([idx1, idx4, idx3])
faces_cylinder = np.array(faces_cylinder)

# 合并螺旋面顶点和圆柱顶点
vertices_combined = np.vstack([vertices_spiral, vertices_cylinder])

# 合并 faces
faces_combined = np.vstack([faces_spiral, faces_cylinder])

# 使用 trimesh 创建网格并导出为 obj 文件
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.export('kudo_horn_with_red_axis.obj')