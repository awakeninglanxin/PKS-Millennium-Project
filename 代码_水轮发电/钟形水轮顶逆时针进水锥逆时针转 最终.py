import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# 参数设置
angle=0.588
b = 1.618 # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率

t_max = 2*np.pi/3   # 时间 t 的最大值，决定螺旋长度
t_min =0

z_v = 2
f=3
t_length = t_max-t_min
num_t = 300  # 时间 t 的分辨率
num_theta = 12  # 榴圈的角度分辨率
num_instances = 3  # 生成的螺旋阵列数量

# leaf shape parameterization
def x(t, a):
    return -a *np.pi * np.sin(t)/t
def y(t, a):
    return a* np.pi * np.cos(t)/t

# 生成时间 t 和榴圈角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
phi = np.linspace(0, 0, num_t)  # 初蛋尖朝向到末蛋尖朝向
theta = np.linspace(1*np.pi, 2.5 * np.pi, num_theta)
a = np.linspace(0.3, 0.1, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.sin(3*f*t)*(np.sqrt(1/(b-t*np.sin(angle))**2-(t*np.cos(angle))**2))
y_spiral = np.cos(3*f*t)*(np.sqrt(1/(b-t*np.sin(angle))**2-(t*np.cos(angle))**2))
z_spiral =-t* z_v

# 计算切线向量 T(t)、法向量 N(t) 和副法向量 B(t)
T_unit = np.zeros((num_t, 3))  # 初始化切线向量矩阵
N_unit = np.zeros((num_t, 3))  # 初始化法向量矩阵
B_unit = np.zeros((num_t, 3))  # 初始化副法向量矩阵

for i in range(num_t):
    # 计算 \hat{T}(t) 切线向量
    dx_dt = 3 * f * np.cos(3 * f * t[i]) * (np.sqrt(1/(b-t[i]*np.sin(angle))**2-(t[i]*np.cos(angle))**2))
    dy_dt = -3 * f * np.sin(3 * f * t[i]) * (np.sqrt(1/(b-t[i]*np.sin(angle))**2-(t[i]*np.cos(angle))**2))
    dz_dt = -z_v
    T = np.array([dx_dt, dy_dt, dz_dt])
    T_unit[i] = T / np.linalg.norm(T)

    # 计算 \hat{N}(t) 法向量
    d2x_dt2 = -9 * f**2 * np.sin(3 * f * t[i]) * (np.sqrt(1/(b-t[i]*np.sin(angle))**2-(t[i]*np.cos(angle))**2))
    d2y_dt2 = -9 * f**2 * np.cos(3 * f * t[i]) * (np.sqrt(1/(b-t[i]*np.sin(angle))**2-(t[i]*np.cos(angle))**2))
    d2z_dt2 = 0
    N = np.array([d2x_dt2, d2y_dt2, d2z_dt2])
    N_unit[i] = N / np.linalg.norm(N)

    # 计算 \hat{B}(t) 副法向量
    B = np.cross(T_unit[i], N_unit[i])
    B_unit[i] = B / np.linalg.norm(B)

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

psi = np.linspace(0, 3*t_length/2, num_t)

# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = (1 / (t[i] + 1))
        # 按照公式生成榴圈在局部坐标系中的分量
        B_term = (x(theta[j], a[i]) * np.cos(phi[i]) - y(theta[j], a[i]) * np.sin(phi[i])) * B_unit[i]
        N_term = (x(theta[j], a[i]) * np.sin(phi[i]) + y(theta[j], a[i]) * np.cos(phi[i])) * N_unit[i]
        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 榴圈点，并应用旋转矩阵
        vector = np.dot(R_theta, (N_term + B_term))
        ellipse_point = vector*scale_factor
        # 计算最终曲面 C(t, θ)
        X_surface[i, j] = x_spiral[i] + ellipse_point[0]
        Y_surface[i, j] = y_spiral[i] + ellipse_point[1]
        Z_surface[i, j] = z_spiral[i] + ellipse_point[2]

# 生成螺旋的圆周阵列
angle_step = 2 * np.pi / num_instances  # 每个螺旋之间的角度差
vertices_combined = []
faces_combined = []

for n in range(num_instances):
    # 旋转螺旋顶点
    rotation = rotation_matrix_around_vector(np.array([0, 0, 1]), n * angle_step)
    rotated_vertices_spiral = np.column_stack((X_surface.flatten(), Y_surface.flatten(), Z_surface.flatten())).dot(rotation.T)

    # 将旋转后的螺旋顶点添加到总顶点列表
    vertices_combined.append(rotated_vertices_spiral)

    # 处理 faces 偏移
    offset = len(X_surface.flatten()) * n
    faces_spiral = []
    for i in range(num_t - 1):
        for j in range(num_theta - 1):
            idx1 = i * num_theta + j
            idx2 = i * num_theta + (j + 1)
            idx3 = (i + 1) * num_theta + j
            idx4 = (i + 1) * num_theta + (j + 1)
            faces_spiral.append([idx1 + offset, idx2 + offset, idx4 + offset])
            faces_spiral.append([idx1 + offset, idx4 + offset, idx3 + offset])
    faces_combined.append(faces_spiral)

# 合并所有螺旋顶点和面
vertices_combined = np.vstack(vertices_combined)
faces_combined = np.vstack(faces_combined)

# 使用 trimesh 创建网格并导出为 obj 文件
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.export('generator_with_axis_array_fixed.obj')
