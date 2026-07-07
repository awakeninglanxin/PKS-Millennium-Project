import numpy as np
import matplotlib.pyplot as plt
import warnings

# 忽略特定的溢出警告
warnings.filterwarnings("ignore", category=RuntimeWarning)

# 定义 phi(t) 函数，处理端点异常
def smooth_phi(t):
    # 处理左端点附近 (t 接近 0)
    if t < 1e-10:  # 使用更小的阈值
        return 0.0
    # 处理右端点附近 (t 接近 1)
    elif t > 1 - 1e-10:  # 使用更小的阈值
        return 1.0
    # 中间正常计算
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # 临时忽略警告
            exponent = (1/t) - (1/(1-t))
            # 处理极大值的情况
            if exponent > 700:  # exp(700) 已经超过浮点数表示范围
                return 0.0
            elif exponent < -700:
                return 1.0
            else:
                return 1 / (1 + np.exp(exponent))

# 定义 r(t) 的组成部分
def segment1(t):
    base = 1 / (1 - np.sqrt(2)/2)**2
    x = np.sqrt(np.maximum(base - (t**2)/2, 0))  # 确保根号内非负
    y = t
    z = 0
    return np.array([x, y, z])

def segment2(t):
    x = (2/3) * np.cos(2 * np.pi * t)
    y = (2/3) * np.sin(2 * np.pi * t)
    z_constant = np.log(2**(1/3)) / np.log((np.sqrt(5)-1)/2)
    z = z_constant
    return np.array([x, y, z])

# 主函数 r(t)
def r(t):
    phi_val = smooth_phi(t)
    part1 = (1 - phi_val) * segment1(t)
    part2 = phi_val * segment2(t)
    return part1 + part2

# 生成时间点 - 避免在端点处取值
t_values = np.linspace(1e-8, 1-1e-8, 10000)

# 计算每个点的坐标
points = []
for t in t_values:
    points.append(r(t))
points = np.array(points)
x = points[:, 0]
y = points[:, 1]
z = points[:, 2]

# 创建 3D 图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制曲线
ax.plot(x, y, z, linewidth=1.5, color='blue')

# 标记特殊点
ax.scatter([r(0)[0]], [r(0)[1]], [r(0)[2]], color='red', s=100, label='t=0')
ax.scatter([r(1)[0]], [r(1)[1]], [r(1)[2]], color='green', s=100, label='t=1')

# 设置标签和标题
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.axis("equal")
ax.set_title('3D Parametric Curve r(t)')
ax.legend()

# 为了显示效果更好，可以调整视角
ax.view_init(elev=20, azim=-35)

plt.show()

# 打印端点值
print(f"r(0) = ({r(0)[0]:.4f}, {r(0)[1]:.4f}, {r(0)[2]:.4f})")
print(f"r(1) = ({r(1)[0]:.4f}, {r(1)[1]:.4f}, {r(1)[2]:.4f})")