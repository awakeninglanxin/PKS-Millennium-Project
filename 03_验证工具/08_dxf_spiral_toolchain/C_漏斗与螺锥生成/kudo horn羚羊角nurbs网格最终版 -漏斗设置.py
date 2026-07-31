import numpy as np
import trimesh
import scipy.interpolate as interpolate
import pandas as pd

class NurbsSurfaceGenerator:
    """NURBS表面生成器类"""

    def __init__(self, params):
        self.params = params
        self.degree = params.nurbs_degree

    def _interpolate_coordinate(self, coord_data, u, v):
        """对单个坐标分量进行样条插值"""
        try:
            interpolator = interpolate.RectBivariateSpline(
                u, v,
                coord_data,
                kx=min(3, len(u) - 1),
                ky=min(3, len(v) - 1)
            )

            u_dense = np.linspace(0, 1, len(u))
            v_dense = np.linspace(0, 1, len(v))
            return interpolator(u_dense, v_dense)
        except Exception as e:
            print(f"插值过程出错: {str(e)}")
            return coord_data

    def generate_nurbs_surface(self, points):
        """生成NURBS表面"""
        if not isinstance(points, np.ndarray) or len(points.shape) != 3 or points.shape[2] != 3:
            print("输入点数据格式错误")
            return points

        rows, cols, _ = points.shape
        u = np.linspace(0, 1, rows)
        v = np.linspace(0, 1, cols)

        try:
            x_surface = self._interpolate_coordinate(points[:, :, 0], u, v)
            y_surface = self._interpolate_coordinate(points[:, :, 1], u, v)
            z_surface = self._interpolate_coordinate(points[:, :, 2], u, v)
            return np.stack([x_surface, y_surface, z_surface], axis=2)
        except Exception as e:
            print(f"NURBS表面生成失败: {str(e)}")
            return points
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
        num_theta = 4  # 减少分段数以提高性能
        theta = np.linspace(0, 2 * np.pi, num_theta)
        z = np.linspace(min_z, max_z, self.params.num_t)

        # 使用numpy广播来简化循环
        theta_grid, z_grid = np.meshgrid(theta, z)

        X = np.cos(theta_grid)
        Y = np.sin(theta_grid)
        Z = z_grid

        vertices, faces = self.create_surface_mesh(X, Y, Z)

        if self.vertices:
            faces += len(self.vertices)

        self.vertices.extend(vertices)
        self.faces.extend(faces)

    def build_mesh(self):
        """构建最终的网格"""
        vertices = np.array(self.vertices)
        faces = np.array(self.faces)
        return trimesh.Trimesh(vertices=vertices, faces=faces)

class SpiralParameters:
    """控制螺旋形状的参数类"""

    def __init__(self, **kwargs):
        # 默认参数
        self.t_max = 7 * np.pi
        self.t_min = 2 * np.pi  # 修改为0，与CSV数据范围匹配
        self.d = 20  # 水平偏移
        self.z_v = 2  # 垂直系数
        self.num_t = 108  # 纵向分辨率
        self.num_theta = 36  # 周向分辨率
        self.num_instances = 3  # 螺旋数量
        self.nurbs_degree = 3  # NURBS阶数
        self.spline_points_file = "spline_points.csv"  # 曲线点数据文件路径
        self.amp = 1  # 放大系数

        # 更新用户自定义参数
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"警告: 未知参数 {key}")

    @property
    def t_length(self):
        return self.t_max - self.t_min

    @property
    def b(self):
        # b=np.log(2) / (self.t_length / 4)
        b = np.log(2) /np.pi
        return b
class CurvePointsLoader:
    """曲线点数据加载器类"""

    @staticmethod
    def load_points(file_path, amp=20):
        """从CSV文件加载曲线点数据并应用放大系数"""
        try:
            df = pd.read_csv(file_path)
            if 't' not in df.columns or 'x' not in df.columns or 'y' not in df.columns:
                raise ValueError("CSV文件必须包含't', 'x', 'y'列")

            # 确保t值在正确的范围内
            t_values = df['t'].values
            if t_values.min() < 0 or t_values.max() > 2*np.pi:
                raise ValueError("t值应该在0到2π之间")

            amplified_x = df['x'].values * amp
            amplified_y = df['y'].values * amp

            # 对数据进行排序，确保t值递增
            sort_idx = np.argsort(t_values)
            t_values = t_values[sort_idx]
            amplified_x = amplified_x[sort_idx]
            amplified_y = amplified_y[sort_idx]

            print(f"螺旋管件已加载并放大 {amp} 倍")
            print(f"t范围: {t_values.min():.2f} 到 {t_values.max():.2f}")
            return t_values, amplified_x, amplified_y
        except Exception as e:
            print(f"加载曲线点数据失败：{str(e)}")
            raise


class SpiralGenerator:
    """螺旋生成器类"""

    def __init__(self, params):
        self.params = params
        self.calc = GeometryCalculator()
        self.nurbs = NurbsSurfaceGenerator(params)
        self.curve_loader = CurvePointsLoader()

        # 加载并处理曲线数据
        self.t_values, self.x_values, self.y_values = self.curve_loader.load_points(
            params.spline_points_file,
            amp=params.amp
        )

        # 创建周期性插值，处理2π循环
        self.x_interp = self._create_periodic_interpolation(self.t_values, self.x_values)
        self.y_interp = self._create_periodic_interpolation(self.t_values, self.y_values)

    def _create_periodic_interpolation(self, t, values):
        """创建周期性插值函数"""
        # 在数据两端添加周期性边界条件
        t_extended = np.concatenate([t - 2*np.pi, t, t + 2*np.pi])
        values_extended = np.concatenate([values, values, values])
        return interpolate.interp1d(t_extended, values_extended, kind='cubic')

    def generate_base_parameters(self):
        """生成基础参数"""
        self.t = np.linspace(self.params.t_min, self.params.t_max, self.params.num_t)
        self.phi = np.zeros(self.params.num_t)
        # 修改theta范围以匹配CSV数据
        self.theta = np.linspace(0, 2*np.pi, self.params.num_theta)
        self.a = np.linspace(1, 1/3, self.params.num_t)
        # self.psi = np.linspace(0, -self.params.t_length/2, self.params.num_t)  #管每圈扭转180度
        self.psi = np.linspace(0, 0, self.params.num_t) #管不扭转

    def calculate_spiral_curve(self):
        """计算螺旋曲线"""
        self.x_spiral = np.exp(self.params.b * self.t) * self.params.d * np.sin(self.t)
        self.y_spiral = np.exp(self.params.b * self.t) * self.params.d * np.cos(self.t)
        self.z_spiral = self.t ** 2 * self.params.z_v-self.params.t_min ** 2 * self.params.z_v

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
        self.Y_surface = np.zeros_like(self.X_surface)
        self.Z_surface = np.zeros_like(self.X_surface)

        theta_grid, _ = np.meshgrid(self.theta, range(self.params.num_t))

        for i in range(self.params.num_t):
            theta_vals = theta_grid[i] % (2 * np.pi)
            x_vals = self.x_interp(theta_vals) * self.a[i]
            y_vals = self.y_interp(theta_vals) * self.a[i]

            for j in range(self.params.num_theta):
                B_term = (x_vals[j] * np.cos(self.phi[i]) -
                          y_vals[j] * np.sin(self.phi[i])) * self.B_unit[i]
                N_term = (x_vals[j] * np.sin(self.phi[i]) +
                          y_vals[j] * np.cos(self.phi[i])) * self.N_unit[i]

                R_theta = self.calc.rotation_matrix_around_vector(self.T_unit[i], self.psi[i])
                vector = np.dot(R_theta, (N_term + B_term))

                self.X_surface[i, j] = self.x_spiral[i] + vector[0]
                self.Y_surface[i, j] = self.y_spiral[i] + vector[1]
                self.Z_surface[i, j] = self.z_spiral[i] + vector[2]
    def generate_smooth_surface(self):
        """使用NURBS生成平滑表面"""
        points = np.stack([self.X_surface, self.Y_surface, self.Z_surface], axis=2)
        return self.nurbs.generate_nurbs_surface(points)
# NurbsSurfaceGenerator, MeshBuilder 等类的代码保持不变
def generate_spiral_tower(output_file="spiral_tower.obj", **params):
    """主函数：生成螺旋塔"""
    try:
        spiral_params = SpiralParameters(**params)
        generator = SpiralGenerator(spiral_params)
        generator.generate_base_parameters()
        generator.calculate_spiral_curve()
        generator.calculate_vectors()
        generator.calculate_surface()

        builder = MeshBuilder(spiral_params)

        for n in range(spiral_params.num_instances):
            angle = n * 2 * np.pi / spiral_params.num_instances
            try:
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

if __name__ == "__main__":
    # 示例：使用自定义参数生成螺旋塔
    generate_spiral_tower(
        "负扭转螺旋塔.obj",  #管每圈扭转180度改正反在247行
        num_t=108,  # 纵向分辨率
        d = 20,  # 水平偏移
        z_v = 2*6,
        num_instances=3,  # 设置3个螺旋
        nurbs_degree=5,  # 设置NURBS阶数
        spline_points_file="spline_points.csv",  # 指定曲线数据文件
        amp=2.4*5,  # 设置放大系数
        t_max = 7 * np.pi,
        t_min = 2*np.pi
    )