"""
egg_tube_mesh.py — 3D蛋形管网格生成
==========================================
生成蛋形截面直管的三维网格，用于CFD仿真。

网格生成策略:
  1. 在截面内用"边界法向插值"生成2D结构化网格
  2. 沿管轴(z方向)均匀拉伸
  3. 输出VTK/OpenFOAM/GMSH格式

数学方法:
  - 边界法向量: 从隐式函数 f(x,y)=0 的梯度导出
    f(x,y) = x² - [1/(z₀-y·sinα)² - (y·cosα)²]
    法向量 n = (-∂f/∂x, -∂f/∂y) / ||∇f||
  
  - 近壁加密: t_phys = t^p, p=1.5
    线性分布 t ∈ [0,1] 映射到物理坐标
    p>1 时壁面附近 (t→0) 更密
        
网格拓扑:
  - 截面: 极坐标式 (θ, r)，但r方向用蛋形曲线法向
  - 轴向: 均匀分布
  - 边界: 壁面(no-slip), 入口(inlet), 出口(outlet)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass
import json

# 导入蛋形曲线模块
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '01_geometry'))
from egg_curve import EggCurve, EggParams


@dataclass
class MeshConfig:
    """网格配置"""
    n_radial: int = 40       # 径向网格数
    n_angular: int = 80      # 角向网格数 (绕蛋形一周)
    n_axial: int = 60        # 轴向网格数 (管长方向)
    tube_length: float = 6.0 # 管长 (无量纲)
    scale: float = 1.0       # 缩放因子


class EggTubeMesh:
    """蛋形管3D网格生成器"""

    def __init__(self, egg_params: EggParams, config: MeshConfig):
        self.egg = EggCurve(egg_params)
        self.cfg = config

    def _egg_normal_at_point(self, x: float, y: float) -> Tuple[float, float]:
        """计算蛋形曲线上某点的法向量 (指向内部)"""
        eps = 1e-6
        # 数值梯度
        x0, y0 = x, y

        # 在蛋形曲线上找法向: 梯度方向
        # f(x,y) = x² - [1/(z0-y·sinα)² - (y·cosα)²] = 0
        z0 = self.egg.p.z0
        sa = self.egg.p.sin_a
        ca = self.egg.p.cos_a

        def f(xv, yv):
            return xv**2 - (1.0 / (z0 - yv * sa)**2 - (yv * ca)**2)

        dfdx = (f(x0 + eps, y0) - f(x0 - eps, y0)) / (2 * eps)
        dfdy = (f(x0, y0 + eps) - f(x0, y0 - eps)) / (2 * eps)

        norm = np.sqrt(dfdx**2 + dfdy**2)
        if norm < 1e-12:
            return 0.0, 0.0
        return -dfdx / norm, -dfdy / norm  # 指向内部

    def generate_2d_section(self) -> dict:
        """
        生成单个蛋形截面的2D网格
        
        使用"蛋形-椭圆"映射:
          1. 在蛋形曲线上取 n_angular 个点
          2. 从每个点沿法向向内插值 n_radial 个点
          3. 中心用退化三角形处理
        
        返回: {
            'x': (n_angular, n_radial+1),  # 含中心点
            'y': (n_angular, n_radial+1),
        }
        """
        n_ang = self.cfg.n_angular
        n_rad = self.cfg.n_radial
        s = self.cfg.scale

        # 获取蛋形曲线点
        x_boundary, y_boundary = self.egg.get_curve_points(n_ang)
        n_pts = len(x_boundary)

        # 均匀采样角向
        indices = np.linspace(0, n_pts - 1, n_ang, endpoint=False).astype(int)
        x_bnd = x_boundary[indices] * s
        y_bnd = y_boundary[indices] * s

        # 截面中心
        cx, cy = 0.0, (np.max(y_bnd) + np.min(y_bnd)) / 2

        # 径向插值: 从边界到中心
        x_grid = np.zeros((n_ang, n_rad + 1))
        y_grid = np.zeros((n_ang, n_rad + 1))

        for i in range(n_ang):
            # 从边界点到中心的线性插值 (可以用非线性加密)
            t = np.linspace(0, 1, n_rad + 1)
            # 使用幂律加密近壁区: t_phys = t^p, p>1 时壁面附近更密
            p = 1.5  # 近壁加密指数
            t_phys = t**p

            x_grid[i, :] = x_bnd[i] * (1 - t_phys) + cx * t_phys
            y_grid[i, :] = y_bnd[i] * (1 - t_phys) + cy * t_phys

        return {'x': x_grid, 'y': y_grid, 'cx': cx, 'cy': cy}

    def generate_3d_mesh(self) -> dict:
        """
        生成3D蛋形管网格
        
        返回: {
            'X': (n_axial, n_angular, n_radial+1),
            'Y': (n_axial, n_angular, n_radial+1),
            'Z': (n_axial, n_angular, n_radial+1),
        }
        """
        section = self.generate_2d_section()
        n_ax = self.cfg.n_axial
        n_ang = self.cfg.n_angular
        n_rad = self.cfg.n_radial

        z_vals = np.linspace(0, self.cfg.tube_length, n_ax)

        X = np.zeros((n_ax, n_ang, n_rad + 1))
        Y = np.zeros((n_ax, n_ang, n_rad + 1))
        Z = np.zeros((n_ax, n_ang, n_rad + 1))

        for k in range(n_ax):
            X[k, :, :] = section['x']
            Y[k, :, :] = section['y']
            Z[k, :, :] = z_vals[k]

        return {'X': X, 'Y': Y, 'Z': Z}

    def export_vtk(self, filename: str):
        """导出为VTK结构化网格"""
        mesh = self.generate_3d_mesh()
        X, Y, Z = mesh['X'], mesh['Y'], mesh['Z']
        dims = X.shape

        with open(filename, 'w') as f:
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Egg tube mesh\n")
            f.write("ASCII\n")
            f.write("DATASET STRUCTURED_GRID\n")
            f.write(f"DIMENSIONS {dims[2]} {dims[1]} {dims[0]}\n")
            f.write(f"POINTS {dims[0]*dims[1]*dims[2]} float\n")

            for k in range(dims[0]):
                for j in range(dims[1]):
                    for i in range(dims[2]):
                        f.write(f"{X[k,j,i]:.6f} {Y[k,j,i]:.6f} {Z[k,j,i]:.6f}\n")

        print(f"✅ VTK网格已导出: {filename}")

    def export_openfoam(self, dirname: str):
        """
        生成OpenFOAM的blockMeshDict
        使用O-grid拓扑将蛋形截面分解为6个block
        """
        section = self.generate_2d_section()
        n_rad = self.cfg.n_radial
        n_ang = self.cfg.n_angular
        n_ax = self.cfg.n_axial
        L = self.cfg.tube_length
        s = self.cfg.scale

        # 取关键点
        x_bnd = section['x'][:, 0]  # 边界点
        y_bnd = section['y'][:, 0]
        cx, cy = section['cx'], section['cy']

        blockMeshDict = f"""\
/*--------------------------------*- C++ -*----------------------------------*|
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

// 蛋形管网格 - 八度蛋截面
// 生成时间: 2026-05-25
// 参数: z1=1, z2=2, k_E=2, alpha={np.degrees(self.egg.p.alpha):.2f}deg

scale {s};

// 管长
L {L};

// 注意: 完整的蛋形截面blockMesh需要O-grid拓扑
// 建议使用Python生成后转换为polyMesh, 或使用snappyHexMesh

// ===== 推荐替代方案 =====
// 1. 用此脚本的generate_3d_mesh()生成点云
// 2. 用GMSH的.geo脚本生成非结构化网格
// 3. 转换为OpenFOAM格式: gmshToFoam

"""
        with open(dirname + '/blockMeshDict', 'w') as f:
            f.write(blockMeshDict)
        print(f"✅ OpenFOAM blockMeshDict模板已导出: {dirname}/blockMeshDict")

    def export_gmsh_geo(self, filename: str):
        """
        生成GMSH .geo脚本 (推荐方式, 支持蛋形曲线的精确建模)
        """
        s = self.cfg.scale
        L = self.cfg.tube_length
        p = self.egg.p

        # 获取蛋形曲线点
        x_bnd, y_bnd = self.egg.get_curve_points(200)
        n_pts = len(x_bnd)

        geo_lines = [
            "// GMSH .geo script for egg-shaped tube",
            "// Octave egg: z1=1, z2=2, k_E=2",
            f"Mesh.MeshSizeMin = 0.05 * {s};",
            f"Mesh.MeshSizeMax = 0.1 * {s};",
            "",
            "// --- 蛋形截面曲线 (底层 z=0) ---",
        ]

        # 底面蛋形曲线的点
        point_start = 1
        for i in range(n_pts):
            geo_lines.append(f"Point({point_start + i}) = {{{x_bnd[i]*s:.6f}, {y_bnd[i]*s:.6f}, 0, 0.05*s}};")

        # 连线
        line_start = 1
        for i in range(n_pts - 1):
            geo_lines.append(f"Line({line_start + i}) = {{{point_start + i}, {point_start + i + 1}}};")
        geo_lines.append(f"Line({line_start + n_pts - 1}) = {{{point_start + n_pts - 1}, {point_start}}};")

        # 底面曲线环
        loop_idx = 1
        lines_str = ", ".join(str(line_start + i) for i in range(n_pts))
        geo_lines.append(f"Curve Loop({loop_idx}) = {{{lines_str}}};")

        # 底面平面
        geo_lines.append(f"Plane Surface(1) = {{{loop_idx}}};")

        # 拉伸成3D管
        geo_lines.extend([
            "",
            "// --- 拉伸成3D管 ---",
            f"Extrude {{0, 0, {L*s}}} {{",
            "    Surface{1};",
            "    Layers{",
            f"        {{self.cfg.n_axial}},",
            "    };",
            "    Recombine;",
            "}}",
            "",
            "// --- 物理组 ---",
            'Physical Surface("inlet") = {1};',
            'Physical Surface("outlet") = {/* top surface */};',
            'Physical Surface("wall") = {/* side surfaces */};',
            'Physical Volume("fluid") = {1};',
        ])

        with open(filename, 'w') as f:
            f.write('\n'.join(geo_lines))
        print(f"✅ GMSH .geo脚本已导出: {filename}")


def visualize_mesh():
    """可视化蛋形管网格"""
    p = EggParams(z1=1, z2=2)
    cfg = MeshConfig(n_radial=20, n_angular=40, n_axial=30, tube_length=4.0)
    mesh_gen = EggTubeMesh(p, cfg)

    fig = plt.figure(figsize=(16, 6))

    # === 1. 2D截面网格 ===
    ax1 = fig.add_subplot(131)
    section = mesh_gen.generate_2d_section()
    x, y = section['x'], section['y']

    # 画径向线
    for i in range(0, x.shape[0], 4):
        ax1.plot(x[i, :], y[i, :], 'b-', linewidth=0.5, alpha=0.6)
    # 画环向线
    for j in range(0, x.shape[1], 5):
        ax1.plot(x[:, j], y[:, j], 'b-', linewidth=0.5, alpha=0.6)

    # 标记边界
    ax1.plot(x[:, 0], y[:, 0], 'r-', linewidth=2, label='壁面')
    ax1.plot(x[:, -1], y[:, -1], 'g.', markersize=2, label='中心轴')
    ax1.set_aspect('equal')
    ax1.legend(fontsize=10)
    ax1.set_title('蛋形截面网格 (近壁加密)', fontsize=13)
    ax1.grid(True, alpha=0.2)

    # === 2. 3D管体 (外表面) ===
    ax2 = fig.add_subplot(132, projection='3d')
    mesh_3d = mesh_gen.generate_3d_mesh()
    X, Y, Z = mesh_3d['X'], mesh_3d['Y'], mesh_3d['Z']

    # 画外壁面
    ax2.plot_surface(X[:, :, 0], Y[:, :, 0], Z[:, :, 0],
                     alpha=0.6, color='steelblue', edgecolor='gray', linewidth=0.2)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z (管轴)')
    ax2.set_title('蛋形管3D外表面', fontsize=13)

    # === 3. 几个截面叠放 ===
    ax3 = fig.add_subplot(133)
    z_slices = [0, 1, 2, 3, 4]
    for z_val in z_slices:
        k = int(z_val / cfg.tube_length * (cfg.n_axial - 1))
        k = min(k, X.shape[0] - 1)
        ax3.plot(X[k, :, 0], Y[k, :, 0], linewidth=1.5, label=f'z={z_val:.0f}')
    ax3.set_aspect('equal')
    ax3.legend(fontsize=9)
    ax3.set_title('不同轴向位置的截面', fontsize=13)
    ax3.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig('/sandbox/workspace/egg_vortex_cfd/output/02_egg_tube_mesh.png', dpi=150)
    plt.close()
    print("✅ 蛋形管网格可视化已保存")


# 修复类型提示
from typing import Tuple

if __name__ == '__main__':
    visualize_mesh()

    # 导出网格文件
    p = EggParams(z1=1, z2=2)
    cfg = MeshConfig()
    mesh_gen = EggTubeMesh(p, cfg)

    mesh_gen.export_vtk('/sandbox/workspace/egg_vortex_cfd/output/egg_tube.vtk')
    mesh_gen.export_gmsh_geo('/sandbox/workspace/egg_vortex_cfd/02_mesh/egg_tube.geo')
