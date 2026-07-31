import numpy as np
import ezdxf
import pandas as pd


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, t_min=2 * np.pi, t_max=7 * np.pi, d=15, z_v=2, amp=2.5):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = np.log(2) / (self.t_length / 2)
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 105
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 加载2D断面数据
        self.load_section_data(spline_data_path)

    def load_section_data(self, filepath):
        """加载2D断面数据并调整方向"""
        df = pd.read_csv(filepath)
        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 找到t=0对应的点的索引
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])

        # 计算t=0点到原点的向量
        t0_vector = self.t0_point

        # 计算当前t=0向量与y轴的夹角（因为我们希望它与法向量平行，后续会对齐到N方向）
        angle = np.arctan2(t0_vector[0], t0_vector[1])

        # 构建旋转矩阵，将t=0向量旋转到y轴方向
        cos_theta = np.cos(-angle)
        sin_theta = np.sin(-angle)
        rot_matrix = np.array([[cos_theta, -sin_theta],
                               [sin_theta, cos_theta]])

        # 旋转所有点
        points = np.column_stack((self.section_x, self.section_y))
        rotated_points = np.dot(points, rot_matrix.T)

        self.section_x = rotated_points[:, 0]
        self.section_y = rotated_points[:, 1]

        # 确保断面是闭合的
        if not np.allclose([self.section_x[0], self.section_y[0]],
                           [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

    def calculate_spiral_coords(self):
        """计算螺旋线的坐标"""
        x = np.exp(self.b * self.t_spiral) * self.d * np.sin(self.t_spiral)
        y = np.exp(self.b * self.t_spiral) * self.d * np.cos(self.t_spiral)
        z = self.t_spiral ** 2 * self.z_v - self.t_min ** 2 * self.z_v
        return x, y, z

    def generate_spiral_curves(self):
        """生成两条螺旋轨道线，确保断面正确对齐"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        # 计算切线向量
        dx = np.gradient(x_spiral, self.t_spiral)
        dy = np.gradient(y_spiral, self.t_spiral)
        dz = np.gradient(z_spiral, self.t_spiral)

        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        for i in range(self.num_t):
            # 切线向量
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)

            # 构造初始法向量（在xz平面内）
            init_N = np.array([-dz[i], 0, dx[i]])
            if np.linalg.norm(init_N) < 1e-6:
                init_N = np.array([1, 0, 0])
            init_N = init_N / np.linalg.norm(init_N)

            # 计算副法向量
            B = np.cross(T_unit[i], init_N)
            B_unit[i] = B / np.linalg.norm(B)

            # 重新计算法向量以确保正交性
            N = np.cross(B_unit[i], T_unit[i])
            N_unit[i] = N / np.linalg.norm(N)

        # 生成两条螺旋线
        center_points = []
        egghead_points = []

        psi = np.linspace(0, -self.t_length / 2, self.num_t)

        for i in range(self.num_t):
            # Center point
            center_points.append([x_spiral[i], y_spiral[i], z_spiral[i]])

            # 使用t0_point作为N方向的位移向量
            offset_vector = self.t0_point[1] * N_unit[i]  # 使用y分量因为已经旋转到y轴
            if psi[i] != 0:
                v = T_unit[i]
                vx, vy, vz = v
                K = np.array([[0, -vz, vy],
                              [vz, 0, -vx],
                              [-vy, vx, 0]])
                I = np.eye(3)
                R = I + np.sin(psi[i]) * K + (1 - np.cos(psi[i])) * np.dot(K, K)
                offset_vector = np.dot(R, offset_vector)

            egghead_points.append([
                x_spiral[i] + offset_vector[0],
                y_spiral[i] + offset_vector[1],
                z_spiral[i] + offset_vector[2]
            ])

        return np.array(center_points), np.array(egghead_points), [T_unit, N_unit, B_unit]

    def sweep_section(self):
        """使用正确对齐的断面进行扫掠"""
        center_points, egghead_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        swept_sections = []
        for i in range(self.num_t):
            section_points = []
            for j in range(len(self.section_x)):
                # 在法向量-副法向量平面内构建点
                vector = self.section_x[j] * B_unit[i] + self.section_y[j] * N_unit[i]

                global_point = [
                    center_points[i][0] + vector[0],
                    center_points[i][1] + vector[1],
                    center_points[i][2] + vector[2]
                ]
                section_points.append(global_point)

            if not np.allclose(section_points[0], section_points[-1]):
                section_points.append(section_points[0])

            swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points.tolist()

    def save_to_dxf(self, filename):
        """保存到DXF文件"""
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, egghead_points = self.sweep_section()

        # 添加两条主要曲线
        msp.add_spline(center_points)  # 中心线
        msp.add_spline(egghead_points)  # egghead线

        # 添加所有扫掠断面
        for section in swept_sections:
            msp.add_spline(section)

        # 添加中心轴
        z_coords = [p[2] for p in center_points]
        msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


# 使用示例
if __name__ == "__main__":
    generator = SpiralSweepGenerator('spline_points.csv')
    generator.save_to_dxf('swept_spiral.dxf')