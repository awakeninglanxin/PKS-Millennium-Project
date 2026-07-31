import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import ezdxf


class SpiralSweepGenerator:

    def __init__(self, t_min=0, t_max=6 * np.pi,
                 sign_spiral_dir=1, sign=1, twist=1, initial_rotation=0):
        # 基础参数初始化
        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.t_length = self.t_max - self.t_min
        self.num_t = 240
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 控制参数
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign

        # 锥体参数
        self.phi = (np.sqrt(5) - 1) / 2
        self.bottom_r = 10.0
        self.turns_num = 32

        # 计算锥体高度
        self.h2 = np.log(0.5) / np.log(self.phi)
        self.h1 = np.log(self.turns_num / 2) / np.log(self.phi)
        self.total_h = self.h1 - self.h2
        self.user_high = abs(self.total_h) * self.bottom_r

        self.set_default_psi()
        self.reference_length = None
        self.t0_point = None
        self.initial_rotation = initial_rotation
        self.ref_point = np.array([1.0, 0.0])  # 默认参考点

    def load_section_data(self, filepath):
        """加载并处理断面数据"""
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {filepath} not found.")

        # 直接加载数据
        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 计算初始长度参考
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])

        # 找到最大半径点
        radii = np.sqrt(self.section_x ** 2 + self.section_y ** 2)
        self.max_radius_idx = np.argmax(radii)
        self.max_radius = radii[self.max_radius_idx]
        print(f"Maximum radius in section: {self.max_radius}")

        # 确保曲线闭合
        if not np.allclose([self.section_x[0], self.section_y[0]],
                           [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

        # 重建为34个点
        t = np.zeros(len(self.section_x))
        dx = np.diff(self.section_x)
        dy = np.diff(self.section_y)
        segment_lengths = np.sqrt(dx ** 2 + dy ** 2)
        t[1:] = np.cumsum(segment_lengths)
        t = t / t[-1]

        t_new = np.linspace(0, 1, 34)

        # 创建插值函数
        interp_x = interp1d(t, self.section_x)
        interp_y = interp1d(t, self.section_y)

        # 重建断面
        self.section_x = interp_x(t_new)
        self.section_y = interp_y(t_new)

    def generate_spiral_curves(self):
        """生成中心直线和螺旋曲线"""
        # 生成中心直线点
        z_values = np.linspace(0, self.total_h, self.num_t)
        center_line = np.array([[0, 0, z] for z in z_values])

        # 生成螺旋曲线点
        spiral_points = self.calculate_spiral_coords()

        # 计算初始点的旋转角度
        initial_point = spiral_points[0][:2]
        ref_angle = np.arctan2(self.ref_point[1], self.ref_point[0])
        current_angle = np.arctan2(initial_point[1], initial_point[0])
        rotation_angle = ref_angle - current_angle + self.initial_rotation

        # 创建绕z轴的旋转矩阵
        rotation_matrix = np.array([
            [np.cos(rotation_angle), -np.sin(rotation_angle), 0],
            [np.sin(rotation_angle), np.cos(rotation_angle), 0],
            [0, 0, 1]
        ])

        # 对所有螺旋点进行旋转
        rotated_spiral_points = np.array([rotation_matrix @ point for point in spiral_points])

        # 确保点数一致
        if len(rotated_spiral_points) != self.num_t:
            t_old = np.linspace(0, 1, len(rotated_spiral_points))
            t_new = np.linspace(0, 1, self.num_t)
            spiral_points_interp = np.zeros((self.num_t, 3))
            for i in range(3):
                spiral_points_interp[:, i] = np.interp(t_new, t_old, rotated_spiral_points[:, i])
            rotated_spiral_points = spiral_points_interp

        # 计算框架向量
        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        for i in range(self.num_t):
            # 计算整个断面的基准位置
            section_center_offset = rotated_spiral_points[i] - center_line[i]
            section_center_offset[2] = 0  # 确保水平偏移

            # 计算标准化的方向向量
            if np.linalg.norm(section_center_offset) > 1e-10:
                N_unit[i] = section_center_offset / np.linalg.norm(section_center_offset)
            else:
                N_unit[i] = np.array([1, 0, 0])

            # T向量保持垂直向上
            T_unit[i] = np.array([0, 0, 1])

            # B向量通过叉积确保整个断面的水平旋转
            B_unit[i] = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B_unit[i] / np.linalg.norm(B_unit[i])

        return center_line, rotated_spiral_points, [T_unit, N_unit, B_unit]

    def calculate_spiral_coords(self):
        """计算锥面螺旋曲线坐标"""
        t = np.linspace(0, 8 * np.pi, self.num_t)
        a = 360

        # 计算基础螺旋曲线，使用最大半径作为基准
        r = self.bottom_r * np.power(2, -t / (a * np.pi / 180))
        x = r * np.cos(t)
        y = r * np.sin(t)

        # 计算投影到锥面上的点
        points = []
        for i in range(len(x)):
            if abs(x[i]) < 1e-10:
                continue
            z_cone, r_cone = self.get_cone_profile(x[i], y[i])
            points.append([x[i], y[i], z_cone])
        return np.array(points)

    def sweep_section(self):
        """沿中心直线扫掠断面"""
        center_line, spiral_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        swept_sections = []
        spiral_points_list = []  # 存储螺旋线点
        section_colors = []

        for i in range(self.num_t):
            # 计算当前点到中心的水平距离作为缩放因子
            radial_vector = spiral_points[i] - center_line[i]
            radial_vector[2] = 0
            scale_factor = np.linalg.norm(radial_vector) / self.bottom_r

            # 缩放断面
            scaled_x = self.section_x * scale_factor
            scaled_y = self.section_y * scale_factor

            section_points = []
            for j in range(len(scaled_x)):
                B_term = self.sign * scaled_x[j] * B_unit[i]
                N_term = self.sign * scaled_y[j] * N_unit[i]
                vector = N_term + B_term

                base_point = np.array([0, 0, spiral_points[i][2]])
                global_point = base_point + vector
                section_points.append(global_point.tolist())

            # 存储螺旋线点
            spiral_points_list.append(spiral_points[i].tolist())
            swept_sections.append(section_points)
            section_colors.append('section_normal' if i % 20 != 0 else 'section_highlight')

        return swept_sections, spiral_points_list, section_colors

    def set_default_psi(self):
        """设置默认的psi值"""
        self.psi = np.linspace(0, 0, self.num_t)

    def get_cone_profile(self, x, y):
        """计算锥面轮廓"""
        x, y = float(x), float(y)
        r_xy = np.sqrt(x ** 2 + y ** 2)
        z_axis = np.log(0.5) / np.log(self.phi) + \
                 (np.log(self.bottom_r / r_xy) * self.user_high) / (np.log(self.turns_num / 2) - np.log(0.5))
        return float(z_axis), float(r_xy)

    def save_to_dxf(self, filename):
        """保存到DXF文件"""
        colors = {
            'spiral': 5,  # 螺旋线使用红色
            'section_normal': 6,
            'section_highlight': 3,
            'axis': 4
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, spiral_points, section_colors = self.sweep_section()

        # 绘制螺旋线
        spline = msp.add_spline(spiral_points)
        spline.dxf.color = colors['spiral']

        # 绘制截面
        for section, color_type in zip(swept_sections, section_colors):
            spline = msp.add_spline(section)
            spline.dxf.color = colors[color_type]

        # 绘制Z轴
        z_coords = [p[2] for p in spiral_points]
        if z_coords:
            line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
            line.dxf.color = colors['axis']

        doc.saveas(filename)

    # 以下方法保持不变...
    def set_default_psi(self):
        self.psi = np.linspace(0,0, self.num_t)



    def rotation_matrix_around_vector(self, v, psi):
        v = v / np.linalg.norm(v)
        vx, vy, vz = v
        K = np.array([
            [0, -vz, vy],
            [vz, 0, -vx],
            [-vy, vx, 0]
        ])
        I = np.eye(3)
        R = I + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)
        return R


def main():
    """Main function to generate different spiral models"""
    print("Generating different spiral models...")


    # Initialize the generator
    generator = SpiralSweepGenerator()

    # Load section data from your specific CSV file
    generator.load_section_data("spline_points口朝右上逆转90度.csv")

    # Model 1: Right-facing spiral
    generator.sign = -1
    generator.r = -1
    generator.twist = -1
    generator.set_default_psi()
    generator.save_to_dxf('直管蛋面sun螺旋_1.dxf')
    print("Model 1 generated with high precision calculations")

    # Model 2: Left-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.twist = -1
    generator.set_default_psi()
    generator.save_to_dxf('直管蛋面sun螺旋_2.dxf')
    print("Model 2 generated")


if __name__ == "__main__":
    main()