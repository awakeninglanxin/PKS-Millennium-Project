import numpy as np
import ezdxf
from scipy.interpolate import interp1d
# DXF 文件创建
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

# 修改后的 leaf shape parameterization
def x1(t, a):
    return 2 * a

def y1(t, a):
    return 0

def x2(t, a):
    return 0

def y2(t, a):
    return 0

# 参数设置
b = np.log(2) / np.pi  # 控制螺旋的扩展
c = 1  # z 轴方向的线性移动速率
d = 2.5  # 控制水平偏移的参数
t_max = 12 * np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 7 * np.pi
t_length = t_max - t_min
z = 15
num_t = 200  # 时间 t 的分辨率
num_theta = 12  # 椭圆的角度分辨率

# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)
theta = np.linspace(0, 2 * np.pi, num_theta)
a = np.linspace(1, 1 / 30, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (-np.cos(t))
z_spiral = np.exp(b * t) * z - np.exp(b * t_min) * z

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

# 生成 psi 值
psi = np.linspace(0, -t_length / 2, num_t)  # 避免 t = 0 的问题

# 旋转矩阵函数
def rotation_matrix_around_vector(v, psi):
    """
    根据任意单位向量 v 和旋转角度 psi 生成旋转矩阵.
    参数:
    v -- 单位向量 (3维向量)
    psi -- 旋转角度（以弧度为单位）
    返回值:
    3x3 的旋转矩阵
    """
    v = v / np.linalg.norm(v)  # 确保 v 是单位向量
    vx, vy, vz = v
    K = np.array([
        [0, -vz, vy],
        [vz, 0, -vx],
        [-vy, vx, 0]
    ])
    I = np.eye(3)
    R = I + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)
    return R


# 初始化空列表来存储线段数据点
ellipse1_points = []
ellipse2_points = []
# 生成线段而不是曲面
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = np.exp(b * t[i]) - ( np.pi/ (t[i] + np.pi))
        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 计算 ellipse2 的每个点的坐标
        N_term1 = (x1(theta[j], a[i]) * N_unit[i])
        B_term1 = (y1(theta[j], a[i]) * B_unit[i])
        vector1 = np.dot(R_theta, (N_term1 + B_term1))
        ellipse1_x1 = x_spiral[i] + scale_factor * vector1[0]
        ellipse1_y1 = y_spiral[i] + scale_factor * vector1[1]
        ellipse1_z1 = z_spiral[i] + scale_factor * vector1[2]
        ellipse1_points.append([ellipse1_x1, ellipse1_y1, ellipse1_z1])

        ellipse2_x1 = x_spiral[i] + scale_factor * x2(theta[j], a[i])
        ellipse2_y1 = y_spiral[i] + scale_factor * y2(theta[j], a[i])
        ellipse2_z1 = z_spiral[i]
        ellipse2_points.append([ellipse2_x1, ellipse2_y1, ellipse2_z1])
        # 将 ellipse2 的线段添加到 DXF 文件
# 将数据点转换为 NumPy 数组，方便插值
ellipse1_points = np.array(ellipse1_points)
ellipse2_points = np.array(ellipse2_points)
# 插值函数
def smooth_curve(points, num_points=500):
    t_original = np.linspace(0, 1, len(points))
    t_smooth = np.linspace(0, 1, num_points)

    # 分别对 x, y, z 进行插值
    x_interp = interp1d(t_original, points[:, 0], kind='cubic')(t_smooth)
    y_interp = interp1d(t_original, points[:, 1], kind='cubic')(t_smooth)
    z_interp = interp1d(t_original, points[:, 2], kind='cubic')(t_smooth)

    return np.vstack((x_interp, y_interp, z_interp)).T

# 对 ellipse1 和 ellipse2 的数据点进行平滑插值
smooth_ellipse1 = smooth_curve(ellipse1_points)
smooth_ellipse2 = smooth_curve(ellipse2_points)

# 将平滑后的 ellipse1 和 ellipse2 点连接成线
for i in range(len(smooth_ellipse1) - 1):
    msp.add_line(smooth_ellipse1[i], smooth_ellipse1[i + 1])

for i in range(len(smooth_ellipse2) - 1):
    msp.add_line(smooth_ellipse2[i], smooth_ellipse2[i + 1])

# 添加中轴线（直线），忽略半径
msp.add_line((0, 0, z_spiral[0]), (0, 0, z_spiral[-1]))

# 保存 DXF 文件
doc.saveas("spiral_with_centerline_ellipse_psi_fixed.dxf")
