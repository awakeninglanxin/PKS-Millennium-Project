import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def create_sphere_torus_mobius():
    # 创建图形和3D轴
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 1. 创建外球体
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    U, V = np.meshgrid(u, v)

    sphere_radius = 2.0
    X_sphere = sphere_radius * np.sin(V) * np.cos(U)
    Y_sphere = sphere_radius * np.sin(V) * np.sin(U)
    Z_sphere = sphere_radius * np.cos(V)

    # 绘制半透明球体
    ax.plot_surface(X_sphere, Y_sphere, Z_sphere, color='cyan', alpha=0.1, linewidth=0.5)

    # 2. 创建双环面结构
    torus_u = np.linspace(0, 2 * np.pi, 60)
    torus_v = np.linspace(0, 2 * np.pi, 60)
    U_torus, V_torus = np.meshgrid(torus_u, torus_v)

    # 第一个环面（水平）
    R1, r1 = 1.2, 0.3
    X_torus1 = (R1 + r1 * np.cos(V_torus)) * np.cos(U_torus)
    Y_torus1 = (R1 + r1 * np.cos(V_torus)) * np.sin(U_torus)
    Z_torus1 = r1 * np.sin(V_torus)

    # 第二个环面（垂直）
    R2, r2 = 1.2, 0.3
    X_torus2 = (R2 + r2 * np.cos(V_torus)) * np.cos(U_torus)
    Y_torus2 = r2 * np.sin(V_torus)
    Z_torus2 = (R2 + r2 * np.cos(V_torus)) * np.sin(U_torus)

    # 绘制双环面
    ax.plot_wireframe(X_torus1, Y_torus1, Z_torus1, color='red', alpha=0.7, linewidth=1)
    ax.plot_wireframe(X_torus2, Y_torus2, Z_torus2, color='blue', alpha=0.7, linewidth=1)

    # 3. 创建中心漏斗（旋转双曲面）
    hyper_u = np.linspace(0, 2 * np.pi, 50)
    hyper_v = np.linspace(-1, 1, 50)
    U_hyper, V_hyper = np.meshgrid(hyper_u, hyper_v)

    a, c = 0.5, 0.8
    X_hyper = a * np.cosh(V_hyper) * np.cos(U_hyper)
    Y_hyper = a * np.cosh(V_hyper) * np.sin(U_hyper)
    Z_hyper = c * np.sinh(V_hyper)

    # 绘制漏斗
    ax.plot_wireframe(X_hyper, Y_hyper, Z_hyper, color='green', alpha=0.8, linewidth=1.5)

    # 4. 创建莫比乌斯带测地线
    mobius_u = np.linspace(0, 2 * np.pi, 100)
    mobius_v = np.linspace(-0.3, 0.3, 20)
    U_mobius, V_mobius = np.meshgrid(mobius_u, mobius_v)

    X_mobius = (1 + V_mobius * np.cos(U_mobius / 2)) * np.cos(U_mobius)
    Y_mobius = (1 + V_mobius * np.cos(U_mobius / 2)) * np.sin(U_mobius)
    Z_mobius = V_mobius * np.sin(U_mobius / 2)

    # 绘制莫比乌斯带
    ax.plot_surface(X_mobius, Y_mobius, Z_mobius, color='purple', alpha=0.6, linewidth=0.5)

    # 设置图形属性
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('球内双环莫比乌斯漏斗结构')
    ax.set_box_aspect([1, 1, 1])

    # 设置视角
    ax.view_init(elev=20, azim=45)

    plt.tight_layout()
    plt.show()


# 运行函数创建图形
if __name__ == "__main__":
    create_sphere_torus_mobius()
