import numpy as np
import ezdxf
from scipy.interpolate import interp1d

# DXF 文件创建
doc = ezdxf.new(dxfversion='R2010')
msp = doc.modelspace()

# 修改后的 leaf shape parameterization
def x1(t, a):
    return 2*a*np.pi*np.sin(t)

def y1(t, a):
    return 2*a*np.pi*np.cos(t)

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
z = 15
num_t = 200  # 时间 t 的分辨率
num_theta = 200  # 椭圆的角度分辨率

# 生成时间 t 和椭圆角度 theta
t = np.linspace(t_min, t_max, num_t)
theta = np.linspace(0, 2 * np.pi, num_theta)
a = np.linspace(1, 1 / 60, num_t)

# 计算螺旋曲线 γ(t) 包含参数 d 进行水平偏移
x_spiral = np.exp(b * t) * d * (np.sin(t))  # 使用 exp(bt) 增加膨胀效果
y_spiral = np.exp(b * t) * d * (np.cos(t))
z_spiral = np.exp(b * t) * z - np.exp(b * t_min) * z

# 初始化空列表来存储线段数据点
ellipse1_points = []
ellipse2_points = []

# 生成线段而不是曲面
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = np.exp(b * t[i]) - (1 / (t[i] + 1))

        # 计算 ellipse1 的每个点的坐标
        ellipse1_x1 = x_spiral[i] + scale_factor * x1(theta[i//2], a[i])
        ellipse1_y1 = y_spiral[i] + scale_factor * y1(theta[i//2], a[i])
        ellipse1_z1 = z_spiral[i]
        ellipse1_points.append([ellipse1_x1, ellipse1_y1, ellipse1_z1])

        # 计算 ellipse2 的每个点的坐标
        ellipse2_x1 = x_spiral[i] + scale_factor * x2(theta[i//2], a[i])
        ellipse2_y1 = y_spiral[i] + scale_factor * y2(theta[i//2], a[i])
        ellipse2_z1 = z_spiral[i]
        ellipse2_points.append([ellipse2_x1, ellipse2_y1, ellipse2_z1])

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
doc.saveas("spiral_with_centerline_ellipse_smooth.dxf")
