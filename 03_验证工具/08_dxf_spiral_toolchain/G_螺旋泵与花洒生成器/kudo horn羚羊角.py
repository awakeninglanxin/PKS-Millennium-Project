import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh

# Egg shape parameterization
def x(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b ** 2 - 4 * k * np.cos(t))))

def y(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k ** 2) * (-np.sqrt(b ** 2 - 4 * k) + np.sqrt(b ** 2 - 4 * k * np.cos(np.pi)))) / (2 * k))
    term2 = ((1 / (2 * np.sqrt(1 + k ** 2))) * (
            ((k ** 2 - 1) / k * b) + ((k ** 2 + 1) / k * np.sqrt(b ** 2 - 4 * k * np.cos(t))))) - (
                ((b * (-1 + k ** 2) + np.sqrt(b ** 2 - 4 * k) * (1 + k ** 2)) / (2 * k * np.sqrt(1 + k ** 2))))
    return a * (m * term1 + term2)

# 八度节点参数集合
nodes = [
    {'k': 2 / 3, 'b': 5 / 3, 'm': 2 / 3, 'a': 9,'label': 'egg1'},
    {'k': 8 / 3, 'b': 10 / 3, 'm': 2 / 3, 'a': 1,'label': 'egg2'},
]

# 参数设置
b = np.log(2)/np.pi  # 控制螺旋的扩展
a_start = 9  # 起始比例
a_end = 1  # 终止比例
t_max = 8 * np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 2 * np.pi
t_length = t_max - t_min
num_t = 1000  # 时间 t 的分辨率
num_theta = 100  # θ 的分辨率

psi_start = 0  # 起始自旋角度
psi_end = -2.5 * np.pi  # 终止自旋角度（可以根据需求设置）

# 生成参数 t 和 θ
t = np.linspace(2 * np.pi, t_max, num_t)
theta = np.linspace(0, t_length / 2, num_theta)

# 创建网格
T, Theta = np.meshgrid(t, theta)

# 定义螺旋线的参数化方程
X_spiral = np.exp(b * T) * np.cos(T)
Y_spiral = -np.exp(b * T) * np.sin(T)
Z_spiral = T**2  # z 方向的线性增长

# 将螺旋转置，使其与 X_rotated 一致
X_spiral = X_spiral.T
Y_spiral = Y_spiral.T
Z_spiral = Z_spiral.T

# 自旋角度的线性变化
psi = np.linspace(psi_start, psi_end, num_t)  # 从起点到终点的自旋角度

# 旋转后的蛋形在每个时间步长的变化
X_rotated = np.zeros((num_t, num_theta))
Y_rotated = np.zeros((num_t, num_theta))
Z_rotated = np.zeros((num_t, num_theta))  # 修正 Z_rotated 的维度

# 生成蛋形曲面代替椭圆
for i in range(num_t):
    # 当前时间点的旋转矩阵（自旋角度）
    rotation_matrix = np.array([
        [np.cos(psi[i]), -np.sin(psi[i]), 0],
        [np.sin(psi[i]), np.cos(psi[i]), 0],
        [0, 0, 1]
    ])

    # 选择当前步长的 egg1 和 egg2
    node = nodes[i % len(nodes)]
    k = node['k']
    b_param = node['b']
    m = node['m']
    a_param = 1  # 可以根据需求调整蛋的缩放比例

    # 生成蛋形结构
    for j in range(num_theta):
        t_val = t[j]
        original_point = np.array([x(t_val, b_param, k, a_param), y(t_val, b_param, k, a_param, m), 0])
        rotated_point = np.dot(rotation_matrix, original_point)

        X_rotated[i, j] = rotated_point[0]
        Y_rotated[i, j] = rotated_point[1]
        Z_rotated[i, j] = Z_spiral[i, 0]  # 修正，确保 Z_rotated 的赋值为标量

# 最终的 3D 坐标计算
X_final = X_spiral + X_rotated
Y_final = Y_spiral + Y_rotated
Z_final = Z_rotated

# 生成 3D 图像
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 使用 plot_surface 来绘制曲面
ax.plot_surface(X_final, Y_final, Z_final, cmap='cool', edgecolor='none')

# 设置标签
ax.set_title('Kudo Horn-like 3D Model with Egg Shape Transition')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()

# --------- 导出到 obj 文件 -----------

# 创建顶点数组
vertices = np.column_stack((X_final.flatten(), Y_final.flatten(), Z_final.flatten()))

# 创建面数据 (三角网格)
faces = []

for i in range(num_t - 1):
    for j in range(num_theta - 1):
        # 每个方块由两个三角形组成
        idx1 = i * num_theta + j
        idx2 = i * num_theta + (j + 1)
        idx3 = (i + 1) * num_theta + j
        idx4 = (i + 1) * num_theta + (j + 1)

        faces.append([idx1, idx2, idx4])
        faces.append([idx1, idx4, idx3])

faces = np.array(faces)

# 使用 trimesh 创建网格
mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

# 导出为 obj 文件
mesh.export('kudo_horn_with_eggs.obj')
