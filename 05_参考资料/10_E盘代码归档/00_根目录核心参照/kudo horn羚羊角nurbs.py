import numpy as np
import trimesh
import scipy.interpolate as interpolate


class SpiralParameters:
    """控制螺旋形状的参数类"""

    def __init__(self, **kwargs):
        # 默认参数
        self.t_max = 6 * np.pi
        self.t_min = np.pi
        self.d = 20  # 水平偏移
        self.z_v = 2  # 垂直系数
        self.num_t = 180  # 纵向分辨率
        self.num_theta = 36  # 周向分辨率
        self.num_instances = 3  # 螺旋数量
        self.nurbs_degree = 3  # NURBS阶数

        # 更新用户自定义参数
        self.__dict__.update(kwargs)

    @property
    def t_length(self):
        return self.t_max - self.t_min

    @property
    def b(self):
        return np.log(2) / (self.t_length / 2)


class GeometryCalculator:
    """几何计算工具类"""

    @staticmethod
    def rotation_matrix_z(theta):
        """绕Z轴旋转矩阵"""
        return np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ])

    @staticmethod
    def rotation_matrix_around_vector(v, psi):
        """绕任意向量旋转矩阵"""
        v = v / np.linalg.norm(v)
        vx, vy, vz = v
        K = np.array([
            [0, -vz, vy],
            [vz, 0, -vx],
            [-vy, vx, 0]
        ])
        I = np.eye(3)
        return I + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)


class NurbsSurfaceGenerator:
    """NURBS表面生成器类"""

    def __init__(self, params):
        self.params = params

    def generate_nurbs_surface(self, points):
        """生成NURBS表面"""
        rows, cols, _ = points.shape

        # 创建参数化网格
        u = np.linspace(0, 1, rows)
        v = np.linspace(0, 1, cols)

        # 分别对 x, y, z 坐标进行样条插值
        x_surface = self._interpolate_coordinate(points[:, :, 0], u, v)
        y_surface = self._interpolate_coordinate(points[:, :, 1], u, v)
        z_surface = self._interpolate_coordinate(points[:, :, 2], u, v)

        return np.stack([x_surface, y_surface, z_surface], axis=2)

    def _interpolate_coordinate(self, coord_data, u, v):
        """对单个坐标分量进行样条插值"""
        try:
            # 使用RectBivariateSpline进行插值，这比bisplrep更稳定
            interp = interpolate.RectBivariateSpline(
                u, v, coord_data,
                kx=min(self.params.nurbs_degree, 3),
                ky=min(self.params.nurbs_degree, 3),
                s=0  # 无平滑，精确插值
            )

            # 在同样的网格上求值
            uu, vv = np.meshgrid(u, v, indexing='ij')
            return interp(u, v, grid=True)

        except Exception as e:
            print(f"插值警告：{str(e)}")
            # 如果插值失败，返回原始数据
            return coord_data

def generate_spiral_tower(output_file="spiral_tower.obj", **params):
    """主函数：生成螺旋塔

    Args:
        output_file: 输出文件路径
        **params: 可选的参数覆盖默认值，比如：
                 num_instances=8  # 螺旋数量
                 nurbs_degree=3   # NURBS阶数
    """
    try:
        # 使用用户提供的参数初始化
        spiral_params = SpiralParameters(**params)

        # 生成螺旋数据
        generator = SpiralGenerator(spiral_params)
        generator.generate_base_parameters()
        generator.calculate_spiral_curve()
        generator.calculate_vectors()
        generator.calculate_surface()

        # 构建网格模型
        builder = MeshBuilder(spiral_params)

        # 添加螺旋实例
        for n in range(spiral_params.num_instances):
            angle = n * 2 * np.pi / spiral_params.num_instances
            try:
                # 使用NURBS平滑处理后的表面
                smooth_surface = generator.generate_smooth_surface()
                builder.add_spiral_instance(
                    smooth_surface[:, :, 0],
                    smooth_surface[:, :, 1],
                    smooth_surface[:, :, 2],
                    angle
                )
            except Exception as e:
                print(f"警告：平滑处理失败，使用原始表面。错误：{str(e)}")
                builder.add_spiral_instance(
                    generator.X_surface,
                    generator.Y_surface,
                    generator.Z_surface,
                    angle
                )

        # 添加中心圆柱体
        builder.add_center_cylinder(
            min_z=np.min(generator.Z_surface),
            max_z=np.max(generator.Z_surface)
        )

        # 创建并保存网格
        mesh = builder.build_mesh()
        mesh.export(output_file)
        print(f"模型文件已保存到: {output_file}")

    except Exception as e:
        print(f"生成螺旋塔时发生错误：{str(e)}")
        raise

class SpiralGenerator:
    """螺旋生成器类"""

    def __init__(self, params):
        self.params = params
        self.calc = GeometryCalculator()
        self.nurbs = NurbsSurfaceGenerator(params)

    def generate_base_parameters(self):
        """生成基础参数"""
        self.t = np.linspace(self.params.t_min, self.params.t_max, self.params.num_t)
        self.phi = np.zeros(self.params.num_t)
        self.theta = np.linspace(np.pi, 3 * np.pi, self.params.num_theta)
        self.a = np.linspace(12, 12 / 4, self.params.num_t)
        self.psi = np.linspace(0, -self.params.t_length / 2, self.params.num_t)

    def calculate_spiral_curve(self):
        """计算螺旋曲线"""
        self.x_spiral = np.exp(self.params.b * self.t) * self.params.d * np.sin(self.t)
        self.y_spiral = np.exp(self.params.b * self.t) * self.params.d * np.cos(self.t)
        self.z_spiral = self.t ** 2 * self.params.z_v

    def calculate_vectors(self):
        """计算向量场"""
        self.T_unit = np.zeros((self.params.num_t, 3))
        self.N_unit = np.zeros((self.params.num_t, 3))
        self.B_unit = np.zeros((self.params.num_t, 3))

        for i in range(self.params.num_t):
            # 切向量
            dx_dt = np.exp(self.params.b * self.t[i]) * self.params.d * (
                    self.params.b * np.sin(self.t[i]) + np.cos(self.t[i]))
            dy_dt = np.exp(self.params.b * self.t[i]) * self.params.d * (
                    self.params.b * np.cos(self.t[i]) - np.sin(self.t[i]))
            dz_dt = self.params.z_v * 2 * self.t[i]

            T = np.array([dx_dt, dy_dt, dz_dt])
            self.T_unit[i] = T / np.linalg.norm(T)

            # 法向量
            d2x_dt2 = np.exp(self.params.b * self.t[i]) * self.params.d * (
                    (self.params.b ** 2) * np.sin(self.t[i]) +
                    2 * self.params.b * np.cos(self.t[i]) - np.sin(self.t[i]))
            d2y_dt2 = np.exp(self.params.b * self.t[i]) * self.params.d * (
                    (self.params.b ** 2) * np.cos(self.t[i]) -
                    2 * self.params.b * np.sin(self.t[i]) - np.cos(self.t[i]))
            d2z_dt2 = self.params.z_v * 2

            N = np.array([d2x_dt2, d2y_dt2, d2z_dt2])
            self.N_unit[i] = N / np.linalg.norm(N)

            # 副法向量
            B = np.cross(self.T_unit[i], self.N_unit[i])
            self.B_unit[i] = B / np.linalg.norm(B)

    def calculate_surface(self):
        """计算曲面点云"""
        self.X_surface = np.zeros((self.params.num_t, self.params.num_theta))
        self.Y_surface = np.zeros((self.params.num_t, self.params.num_theta))
        self.Z_surface = np.zeros((self.params.num_t, self.params.num_theta))

        for i in range(self.params.num_t):
            for j in range(self.params.num_theta):
                B_term = (self.x(self.theta[j], self.a[i]) * np.cos(self.phi[i]) -
                          self.y(self.theta[j], self.a[i]) * np.sin(self.phi[i])) * self.B_unit[i]
                N_term = (self.x(self.theta[j], self.a[i]) * np.sin(self.phi[i]) +
                          self.y(self.theta[j], self.a[i]) * np.cos(self.phi[i])) * self.N_unit[i]

                R_theta = self.calc.rotation_matrix_around_vector(self.T_unit[i], self.psi[i])
                vector = np.dot(R_theta, (N_term + B_term))

                self.X_surface[i, j] = self.x_spiral[i] + vector[0]
                self.Y_surface[i, j] = self.y_spiral[i] + vector[1]
                self.Z_surface[i, j] = self.z_spiral[i] + vector[2]

    def generate_smooth_surface(self):
        """使用NURBS生成平滑表面"""
        points = np.stack([self.X_surface, self.Y_surface, self.Z_surface], axis=2)
        return self.nurbs.generate_nurbs_surface(points)

    @staticmethod
    def x(t, a):
        return a * 2 * np.pi * np.sin(t) / t

    @staticmethod
    def y(t, a):
        return a * 2 * np.pi * np.cos(t) / t


class MeshBuilder:
    """网格模型构建器类"""

    def __init__(self, params):
        self.params = params
        self.calc = GeometryCalculator()
        self.vertices = []
        self.faces = []

    def create_surface_mesh(self, X, Y, Z):
        """从点云创建三角网格"""
        rows, cols = X.shape
        vertices = np.stack([X, Y, Z], axis=-1)
        vertices = vertices.reshape(-1, 3)

        # 创建面片索引
        faces = []
        for i in range(rows - 1):
            for j in range(cols - 1):
                v0 = i * cols + j
                v1 = v0 + 1
                v2 = (i + 1) * cols + j
                v3 = v2 + 1

                faces.append([v0, v1, v2])
                faces.append([v1, v3, v2])

        return vertices, np.array(faces)

    def add_spiral_instance(self, X, Y, Z, angle):
        """添加一个螺旋实例"""
        rotation = self.calc.rotation_matrix_z(angle)
        X_rot = np.zeros_like(X)
        Y_rot = np.zeros_like(Y)
        Z_rot = np.zeros_like(Z)

        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                point = np.array([X[i, j], Y[i, j], Z[i, j]])
                rotated = np.dot(rotation, point)
                X_rot[i, j], Y_rot[i, j], Z_rot[i, j] = rotated

        vertices, faces = self.create_surface_mesh(X_rot, Y_rot, Z_rot)

        if len(self.vertices) > 0:
            faces += len(self.vertices)

        self.vertices.extend(vertices)
        self.faces.extend(faces)

    def add_center_cylinder(self, min_z, max_z):
        """添加中心圆柱体"""
        radius = 1
        num_theta = 16
        theta = np.linspace(0, 2 * np.pi, num_theta)
        z = np.linspace(min_z, max_z * 1.5, self.params.num_t)

        X = np.zeros((self.params.num_t, num_theta))
        Y = np.zeros((self.params.num_t, num_theta))
        Z = np.zeros((self.params.num_t, num_theta))

        for i in range(self.params.num_t):
            for j in range(num_theta):
                X[i, j] = radius * np.cos(theta[j])
                Y[i, j] = radius * np.sin(theta[j])
                Z[i, j] = z[i]

        vertices, faces = self.create_surface_mesh(X, Y, Z)

        if len(self.vertices) > 0:
            faces += len(self.vertices)

        self.vertices.extend(vertices)
        self.faces.extend(faces)

    def build_mesh(self):
        """构建最终的网格"""
        vertices = np.array(self.vertices)
        faces = np.array(self.faces)
        return trimesh.Trimesh(vertices=vertices, faces=faces)





if __name__ == "__main__":
    # 示例：使用自定义参数生成螺旋塔
    generate_spiral_tower(
        "螺旋塔.obj",
        num_instances=3,  # 设置8个螺旋
        nurbs_degree=5,  # 设置NURBS阶数
    )