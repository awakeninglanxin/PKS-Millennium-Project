import numpy as np
import ezdxf
import pandas as pd


class SpiralSweepGenerator:
    """螺旋扫探生成器类"""

    def __init__(self, spline_data_path, t_min=0, t_max=8 * np.pi, d=3, z_v=5, amp=0.3,
                 sign_spiral_dir=1, sign=1, twist=1):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = np.log(2) / (2*np.pi)
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 240
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp, self.amp, self.num_t)
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.load_section_data(spline_data_path)
        self.set_default_psi()

    def set_default_psi(self):
        """设置默认的psi值"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """设置自定义的psi值"""
        self.psi = np.linspace(self.twist *start, self.twist *end, self.num_t)
    def load_section_data(self, filepath):
        """
        加载2D断面数据，调整方向，重建为34个点，然后进行偏移
        """
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件 {filepath} 未找到。")

        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 找到t=0对应的点的索引并计算初始长度
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])
        t0_vector = self.t0_point
        vector_length = np.linalg.norm(t0_vector)
        print(f"蛋心到蛋尖的初始长度: {vector_length}")

        # 旋转调整
        angle = np.arctan2(t0_vector[0], t0_vector[1])
        cos_theta = np.cos(-angle)
        sin_theta = np.sin(-angle)
        rot_matrix = np.array([[cos_theta, -sin_theta],
                               [sin_theta, cos_theta]])
        points = np.column_stack((self.section_x, self.section_y))
        rotated_points = np.dot(points, rot_matrix.T)

        self.section_x = rotated_points[:, 0]
        self.section_y = rotated_points[:, 1]

        # 确保闭合
        if not np.allclose([self.section_x[0], self.section_y[0]],
                           [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

        # 重建曲线为34个点
        t = np.zeros(len(self.section_x))
        dx = np.diff(self.section_x)
        dy = np.diff(self.section_y)
        segment_lengths = np.sqrt(dx ** 2 + dy ** 2)
        t[1:] = np.cumsum(segment_lengths)
        t = t / t[-1]

        t_new = np.linspace(0, 1, 34)

        from scipy.interpolate import interp1d
        interp_x = interp1d(t, self.section_x)
        interp_y = interp1d(t, self.section_y)

        # 重建原始曲线
        self.section_x = interp_x(t_new)
        self.section_y = interp_y(t_new)

    def change_section(self, section_x, section_y, a):
        """
        缩放断面坐标
        """
        return section_x * a, section_y * a

    def calculate_spiral_coords(self):
        x = self.d * np.sin(self.t_spiral) * self.r
        y = self.d * np.cos(self.t_spiral)
        z = self.t_spiral * self.z_v
        return x, y, z

    def generate_spiral_curves(self):
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        dx = np.gradient(x_spiral, self.t_spiral)
        dy = np.gradient(y_spiral, self.t_spiral)
        dz = np.gradient(z_spiral, self.t_spiral)

        ddx = np.gradient(dx, self.t_spiral)
        ddy = np.gradient(dy, self.t_spiral)
        ddz = np.gradient(dz, self.t_spiral)

        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        for i in range(self.num_t):
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)

            N = np.array([ddx[i], ddy[i], ddz[i]])
            N_unit[i] = N / np.linalg.norm(N)

            B = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B / np.linalg.norm(B)

        center_points = []
        for i in range(self.num_t):
            center_points.append([x_spiral[i], y_spiral[i], z_spiral[i]])

        return np.array(center_points), [T_unit, N_unit, B_unit]

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

    def offset_section(self, offset_distance, section_x, section_y):
        """
        通过从原点到曲线上的点的向量进行偏移

        参数:
        offset_distance: float, 偏移距离 (1.5mm)
        section_x, section_y: 断面坐标
        """
        # 获取当前断面的原点 (0,0)
        center_point = np.array([0, 0])

        # 计算从原点到每个点的向量
        vectors = np.column_stack((section_x, section_y))

        # 计算每个向量的长度
        vector_lengths = np.sqrt(np.sum(vectors ** 2, axis=1))

        # 计算单位向量
        unit_vectors = vectors / vector_lengths[:, np.newaxis]

        # 计算新的偏移长度（原长度 + offset_distance）
        new_lengths = vector_lengths + offset_distance

        # 计算偏移后的点的坐标
        offset_points = unit_vectors * new_lengths[:, np.newaxis]

        return offset_points[:, 0], offset_points[:, 1]

    def sweep_section(self):
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        for i in range(self.num_t):
            # 先进行缩放
            new_section_x, new_section_y = self.change_section(self.section_x, self.section_y, self.a[i])
            # 对缩放后的断面进行偏移

            section_points = []

            for j in range(len(new_section_x)):
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])

                # 处理原始断面
                B_term = self.sign * new_section_x[j] * B_unit[i]
                N_term = self.sign * new_section_y[j] * N_unit[i]
                vector = np.dot(R_theta, (N_term + B_term))
                global_point = [
                    center_points[i][0] + vector[0],
                    center_points[i][1] + vector[1],
                    center_points[i][2] + vector[2]
                ]

                if j == 0:
                    egghead_point = global_point.copy()
                    egghead_points.append(egghead_point)

                section_points.append(global_point)

            if i == 0 or (i + 1) % 20 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

    def save_to_dxf(self, filename):
        colors = {
            'center_line': 1,
            'egg_tip': 5,
            'sections': 3,
            'axis': 4
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, egghead_points = self.sweep_section()

        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        for i, section in enumerate(swept_sections):
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


def main():
    """主函数"""
    print("以下对应阴阳：")
    print("生成口朝右下的模型 d 为正...")

    generator_right = SpiralSweepGenerator('spline_points口朝右上.csv')

    # 第一个模型
    generator_right.sign = 1
    generator_right.r = -1
    generator_right.twist = -1
    generator_right.twist = 1
    # generator_right.set_custom_psi(-np.pi / 2, generator_right.t_length / 2 - np.pi / 2)
    generator_right.save_to_dxf('t平方最简优先 弹簧 对扭转—口朝内(头朝下).dxf')

    # 第二个模型
    generator_right.sign = 1
    generator_right.r = 1
    generator_right.set_default_psi()  # 使用默认的psi值
    generator_right.save_to_dxf('t平方 弹簧 对扭转—口朝内(头朝外).dxf')

    # 新增的第三个模型，使用修改后的psi值
    generator_right.sign = -1
    generator_right.r = 1
    generator_right.set_default_psi()
    # generator_right.set_custom_psi(-np.pi / 2, generator_right.t_length / 2 - np.pi / 2)  # 设置新的psi值
    generator_right.save_to_dxf('t平方 弹簧 对扭转—口朝内(头朝内).dxf')


if __name__ == "__main__":
    main()