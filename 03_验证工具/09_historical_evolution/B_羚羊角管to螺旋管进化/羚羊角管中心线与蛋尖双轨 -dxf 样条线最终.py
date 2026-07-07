import numpy as np
import ezdxf
# DXF 文件创建
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

# 修改后的 leaf shape parameterization
def x(t, a):
    return  0

def y(t, a):
    return 2*a*t

# 参数设置
t_max = 7* np.pi  # 时间 t 的最大值，决定螺旋长度
t_min = 2*np.pi
t_length = t_max - t_min
b = np.log(2) /(t_length/2)
print('b:',b)
# b = np.log(2) /(t_length/2)
d = 15 # 控制水平偏移的参数
z_v = 2
num_t = 105  # 时间 t 的分辨率
num_instances = 3  # 生成的螺旋阵列数量
amp=2.5
# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)
num_theta =[0,1]
a = np.linspace(6*amp, 2*amp, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (np.cos(t))
z_spiral = t**2* z_v-t_min**2* z_v# 修正 z 轴分量为线性关系

# 计算切线向量 T(t)、法向量 N(t) 和副法向量 B(t)
T_unit = np.zeros((num_t, 3))  # 初始化切线向量矩阵
N_unit = np.zeros((num_t, 3))  # 初始化法向量矩阵
B_unit = np.zeros((num_t, 3))  # 初始化副法向量矩阵
for i in range(num_t):
    # 计算 \hat{T}(t) 切线向量
    dx_dt = np.exp(b * t[i]) * d * (b * np.sin(t[i]) + np.cos(t[i]))
    dy_dt = np.exp(b * t[i]) * d * (b * np.cos(t[i]) - np.sin(t[i]))
    dz_dt = z_v * 2 * t[i]
    T = np.array([dx_dt, dy_dt, dz_dt])
    T_unit[i] = T / np.linalg.norm(T)

    # 计算 \hat{N}(t) 法向量
    d2x_dt2 = np.exp(b * t[i]) * d * ((b ** 2) * np.sin(t[i]) + 2 * b * np.cos(t[i]) - np.sin(t[i]))
    d2y_dt2 = np.exp(b * t[i]) * d * ((b ** 2) * np.cos(t[i]) - 2 * b * np.sin(t[i]) - np.cos(t[i]))
    d2z_dt2 = z_v * 2
    N = np.array([d2x_dt2, d2y_dt2, d2z_dt2])
    N_unit[i] = N / np.linalg.norm(N)

    # 计算 \hat{B}(t) 副法向量
    B = np.cross(T_unit[i], N_unit[i])
    B_unit[i] = B / np.linalg.norm(B)

# 生成 psi 值
psi = np.linspace(0, -t_length / 2, num_t)  # 负扩展
# psi = np.linspace(0, t_length / 2, num_t)  #正扩展
# psi = np.linspace(0, 0, num_t)  #不扩展
phi = np.linspace(0, 0, num_t)  # 初蛋尖朝向到末蛋尖朝向
# 旋转矩阵函数
def rotation_matrix_around_vector(v, psi):
    """根据任意单位向量 v 和旋转角度 psi 生成旋转矩阵.
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
center_points = []
egghead_points = []
# 生成线段而不是曲面
for i in range(num_t):
    for j in num_theta:
        # scale_factor = np.exp(b * t[i]) - (np.pi/ (t[i] + np.pi))
        scale_factor =1
        # 生成旋转矩阵 R_Theta(psi(t))
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        # 计算 ellipse2 的每个点的坐标
        B_term1 = (x(j, a[i]) * np.cos(phi[i]) - y(j, a[i]) * np.sin(phi[i])) * B_unit[i]
        N_term1 = (x(j, a[i]) * np.sin(phi[i]) + y(j, a[i]) * np.cos(phi[i])) * N_unit[i]

        vector1 = np.dot(R_theta, (N_term1 + B_term1))
        ellipse_x = x_spiral[i] + scale_factor * vector1[0]
        ellipse_y = y_spiral[i] + scale_factor * vector1[1]
        ellipse_z = z_spiral[i] + scale_factor * vector1[2]
        if j==0:
            center_points.append([ellipse_x, ellipse_y, ellipse_z])
        if j==1:
            egghead_points.append([ellipse_x, ellipse_y, ellipse_z])
    # if num_t-i > 3:
        # 将 ellipse2 的线段添加到 DXF 文件
# 将数据点转换为 NumPy 数组，方便插值
center_points = np.array(center_points)
egghead_points = np.array(egghead_points)

# 将 ellipse1 的点用样条曲线连接
msp.add_spline(center_points.tolist())

# 将 ellipse2 的点用样条曲线连接
msp.add_spline(egghead_points.tolist())

# 添加中轴线（直线），忽略半径
msp.add_line((0, 0, z_spiral[0]), (0, 0, z_spiral[-1]))
filename = f'负spiral_b={b:.3f},底={d},z轴={z_v},尾蛋距={2*amp:.3f},周期{t_length/(2*np.pi):.3f}.dxf'
# 保存 DXF 文件
doc.saveas(filename)