import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# 参数设置
b = np.log(2) /(300*np.pi/180)  # 控制螺旋的扩展

t_max = 5* np.pi  # 时间 t 的最大值，决定螺旋长度
t_min =0
t_length = t_max - t_min
d = -5 # 控制水平偏移的参数
z_v = 40
num_t = 200  # 时间 t 的分辨率
num_theta = 12  # 椭圆的角度分辨率
num_instances = 3# 生成的螺旋阵列数量
amp=2
# leaf shape parameterization
def x(t, a):
    return  amp*a *2*3*np.pi * np.sin(t)/t
def y(t, a):
    return  amp*-a *2*3*np.pi * np.cos(t)/t

# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
phi = np.linspace(0, 0, num_t)  # 初蛋尖朝向到末蛋尖朝向
theta = np.linspace(np.pi, 3 * np.pi, num_theta)
a = np.linspace(3, 1, num_t)
# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = amp*np.exp(b * t) * d * (np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = amp*np.exp(b * t) * d * (np.cos(t))
z_spiral = amp*(np.exp(b * t) * z_v - np.exp(b * t_min) * z_v)# 修正 z 轴分量为线性关系

# 计算切线向量 T(t)、法向量 N(t) 和副法向量 B(t)
T_unit = np.zeros((num_t, 3))  # 初始化切线向量矩阵
N_unit = np.zeros((num_t, 3))  # 初始化法向量矩阵
B_unit = np.zeros((num_t, 3))  # 初始化副法向量矩阵

for i in range(num_t):
    # 计算 \hat{T}(t) 切线向量
    dx_dt = np.exp(b * t[i]) * d * (b * np.sin(t[i]) + np.cos(t[i]))
    dy_dt = np.exp(b * t[i]) * d * (b * np.cos(t[i]) - np.sin(t[i]))
    dz_dt = b * np.exp(b * t[i]) * z_v
    T = np.array([dx_dt, dy_dt, dz_dt])
    T_unit[i] = T / np.linalg.norm(T)

    # 计算 \hat{N}(t) 法向量
    d2x_dt2 = np.exp(b * t[i]) * d * ((b ** 2) * np.sin(t[i]) + 2 * b * np.cos(t[i]) - np.sin(t[i]))
    d2y_dt2 = np.exp(b * t[i]) * d * ((b ** 2) * np.cos(t[i]) - 2 * b * np.sin(t[i]) - np.cos(t[i]))
    d2z_dt2 = (b ** 2) * np.exp(b * t[i]) * z_v
    N = np.array([d2x_dt2, d2y_dt2, d2z_dt2])
    N_unit[i] = N / np.linalg.norm(N)

    # 计算 \hat{B}(t) 副法向量
    B = np.cross(T_unit[i], N_unit[i])
    B_unit[i] = B / np.linalg.norm(B)
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

psi = np.linspace(0, -t_length / 2, num_t)  # 负扭转
# psi = np.linspace(0, t_length / 2, num_t)  #正扭转
# psi = np.linspace(0, 0, num_t)  #不扭转
# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        # scale_factor = (1 / (t[i]+1))
        scale_factor=1
        # 根据公式生成椭圆在局部坐标系中的分量
        B_term = (x(theta[j], a[i]) * np.cos(phi[i]) - y(theta[j], a[i]) * np.sin(phi[i])) * B_unit[i]
        N_term = (x(theta[j], a[i]) * np.sin(phi[i]) + y(theta[j],  a[i])* np.cos(phi[i])) * N_unit[i]
        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 椭圆点，并应用尺度变化因子和旋转矩阵
        vector=np.dot(R_theta, (N_term + B_term))
        ellipse_point = scale_factor * vector
        # 计算最终曲面 C(t, θ)
        X_surface[i, j] = x_spiral[i] + ellipse_point[0]
        Y_surface[i, j] = y_spiral[i] + ellipse_point[1]
        Z_surface[i, j] = z_spiral[i] + ellipse_point[2]
print('a[0]:',2*a[0]*np.exp(b * t_min) - (np.pi / (t_min + np.pi)))
print('a[-1]:',2*a[-1]*np.exp(b * t_max) - (np.pi / (t_max + np.pi)))
print('a[0]/a[-1]:',(2*a[0]*np.exp(b * t_min) - (np.pi / (t_min + np.pi)))/(2*a[-1]*np.exp(b * t_max) - (np.pi / (t_max + np.pi))))

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

radius = 1*amp
theta_cylinder = np.linspace(0, 2 * np.pi, num_theta)
# 生成圆柱的 X, Y, Z 坐标
X_cylinder = np.tile(radius * np.cos(theta_cylinder), (num_t, 1))
Y_cylinder = np.tile(radius * np.sin(theta_cylinder), (num_t, 1))
z_cylinder = np.linspace(min(Z_surface.flatten()), max(Z_surface.flatten())*1.5, num_t)  # 圆柱高度与螺旋高度相同
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
mesh.export('羚羊角底逆时针内进水锥顺转.obj')
