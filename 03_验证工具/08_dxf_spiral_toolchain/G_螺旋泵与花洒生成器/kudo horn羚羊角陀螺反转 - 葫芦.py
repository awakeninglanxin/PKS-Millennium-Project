import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh
import matplotlib.cm as cm
from scipy.interpolate import splprep, splev

# 参数设置
b = np.log(2) / np.pi  # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率

t_max = 15 * np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 7 * np.pi
t_length = t_max - t_min
d = 5  # 控制水平偏移的参数
z_v = 9
num_t = 60  # 时间 t 的分辨率
num_theta = 18  # 椭圆的角度分辨率
num_instances = 8  # 生成的螺旋阵列数量

# leaf shape parameterization
def x(t, a):
    return -a * 2 * np.pi * np.sin(t) / t

def y(t, a):
    return a * 2 * np.pi * np.cos(t) / t

# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)  # 避免 t = 0 的问题
phi = np.linspace(0, 0, num_t)  # 初蛋尖朝向到末蛋尖朝向
theta = np.linspace(np.pi, 3 * np.pi, num_theta)
a = np.linspace(1, 1, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (-np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (-np.cos(t))
z_spiral = (np.exp(b * t) * z_v - np.exp(b * t_min) * z_v) * (np.cos(t / 5))  # 修正 z 轴分量为线性关系
# z_spiral = (np.exp(b * t) * z_v - np.exp(b * t_min))*t**2

# 计算切线向量 T(t)、法向量 N(t) 和副法向量 B(t)
T_unit = np.zeros((num_t, 3))  # 初始化切线向量矩阵
N_unit = np.zeros((num_t, 3))  # 初始化法向量矩阵
B_unit = np.zeros((num_t, 3))  # 初始化副法向量矩阵
b_val = 1 / 3
d_val = 1
for i in range(num_t):
    # 计算 \hat{T}(t) 切线向量
    T_unit[i, 0] = d_val * (b_val * (np.sin(t[i]) + np.cos(t[i]))) / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))
    T_unit[i, 1] = d_val * (b_val * (np.cos(t[i]) - np.sin(t[i]))) / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))
    T_unit[i, 2] = -b_val * z_v / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))

    # 计算 \hat{N}(t) 法向量
    N_unit[i, 0] = (b_val * np.cos(t[i]) - np.sin(t[i])) / np.sqrt(1 + b_val ** 2)
    N_unit[i, 1] = (-b_val * np.sin(t[i]) - np.cos(t[i])) / np.sqrt(1 + b_val ** 2)
    N_unit[i, 2] = 0  # 法向量 z 分量为 0

    # 计算 \hat{B}(t) 副法向量
    B_unit[i, 0] = b_val * z_v * (b_val * np.sin(t[i]) + np.cos(t[i])) / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))
    B_unit[i, 1] = b_val * z_v * (b_val * np.cos(t[i]) - np.sin(t[i])) / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))
    B_unit[i, 2] = d_val * (b_val ** 2 + 1) / np.sqrt((b_val ** 2 + 1) * (d_val ** 2) + (b_val ** 2) * (z_v ** 2))

# 初始化螺旋壳体的 X, Y, Z 坐标
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# 生成曲面 C(t, θ)
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = np.exp(b * t[i]) - (np.pi / (t[i] + np.pi))
        # 根据公式生成椭圆在局部坐标系中的分量
        B_term = (x(theta[j], a[i]) * np.cos(phi[i]) - y(theta[j], a[i]) * np.sin(phi[i])) * B_unit[i]
        N_term = (x(theta[j], a[i]) * np.sin(phi[i]) + y(theta[j], a[i]) * np.cos(phi[i])) * N_unit[i]
        # 椭圆点
        ellipse_point = scale_factor * (N_term + B_term)
        # 计算最终曲面 C(t, θ)
        X_surface[i, j] = x_spiral[i] + ellipse_point[0]
        Y_surface[i, j] = y_spiral[i] + ellipse_point[1]
        Z_surface[i, j] = z_spiral[i] + ellipse_point[2]

vertices_spiral = np.column_stack((X_surface.flatten(), Y_surface.flatten(), Z_surface.flatten()))

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
    rotation = np.array([[np.cos(n * angle_step), -np.sin(n * angle_step), 0],
                         [np.sin(n * angle_step), np.cos(n * angle_step), 0],
                         [0, 0, 1]])
    rotated_vertices_spiral = vertices_spiral.dot(rotation.T)

    # 将旋转后的螺旋顶点添加到总顶点列表
    vertices_combined.append(rotated_vertices_spiral)

    # 处理 faces 偏移
    faces_spiral_offset = faces_spiral + len(vertices_spiral) * n
    faces_combined.append(faces_spiral_offset)

# 合并所有螺旋顶点和面
vertices_combined = np.vstack(vertices_combined)
faces_combined = np.vstack(faces_combined)

# 样条线生成函数
def generate_spline(vertices, num_points=1000):
    tck, u = splprep([vertices[:, 0], vertices[:, 1], vertices[:, 2]], s=0)
    u_new = np.linspace(u.min(), u.max(), num_points)
    x_new, y_new, z_new = splev(u_new, tck, der=0)
    return np.column_stack((x_new, y_new, z_new))

# 生成螺旋的样条线
spline_vertices = generate_spline(vertices_combined)

# HSV颜色映射
num_faces = faces_combined.shape[0]
hsv_colors = cm.hsv(np.linspace(0, 1, num_faces))

# 使用 trimesh 创建网格并为每个面分配颜色和透明度
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.visual.face_colors = (hsv_colors[:, :3] * 255).astype(np.uint8)

# 导出带颜色的 OBJ 文件
mesh.export('kudo_horn_with_spline_and_hsv.obj')

# 绘制样条线
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(spline_vertices[:, 0], spline_vertices[:, 1], spline_vertices[:, 2], color='blue', lw=2)
plt.show()