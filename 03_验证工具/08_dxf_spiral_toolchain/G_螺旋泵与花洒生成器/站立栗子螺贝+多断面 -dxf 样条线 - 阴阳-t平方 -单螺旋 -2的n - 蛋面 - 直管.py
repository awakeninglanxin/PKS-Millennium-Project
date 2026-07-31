import numpy as np
import pandas as pd
import ezdxf


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, t_min=0, t_max=6 * np.pi, amp=0.3,
                 sign_spiral_dir=1, sign=1, twist=1, f=1.5, angle=0.588, b=1.6, c=1):
        # 基础参数初始化
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = self.t_max - self.t_min
        self.num_t = 49
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 控制参数
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign

        # 锥体参数
        self.phi = (np.sqrt(5) - 1) / 2
        self.bottom_r = 10.0
        self.turns_num = 144

        # 计算锥体高度
        self.h2 = np.log(0.5) / np.log(self.phi)
        self.h1 = np.log(self.turns_num / 2) / np.log(self.phi)
        self.total_h = self.h1 - self.h2
        self.user_high = abs(self.total_h) * self.bottom_r

        self.reference_length = None
        self.t0_point = None

        self.load_section_data(spline_data_path)
        self.set_default_psi()

    @property
    def twist(self):
        return self._twist

    @twist.setter
    def twist(self, value):
        self._twist = value
        self.update_parameters()

    @property
    def sign(self):
        return self._sign

    @sign.setter
    def sign(self, value):
        self._sign = value
        self.update_parameters()

    def update_parameters(self):
        """更新所有依赖于twist和sign的参数"""
        self.update_psi()

    def update_psi(self):
        """更新psi值"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)

    def load_section_data(self, filepath):
        """加载2D断面数据并调整方向"""
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件 {filepath} 未找到。")
        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 找到t=0对应的点的索引
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])

        # 计算t=0点到原点的向量
        t0_vector = self.t0_point
        vector_length = np.linalg.norm(t0_vector)
        print(f"蛋心到蛋尖的初始长度: {vector_length}")

        # 计算当前t=0向量与y轴的夹角
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
        if not np.allclose([self.section_x[0], self.section_y[0]], [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

    def set_default_psi(self):
        self.psi = np.linspace(0, 0, self.num_t)

    def get_cone_profile(self, x, y):
        x, y = float(x), float(y)
        r_xy = np.sqrt(x ** 2 + y ** 2)
        z_axis = np.log(0.5) / np.log(self.phi) + \
                 (np.log(self.bottom_r / r_xy) * self.user_high) / (np.log(self.turns_num / 2) - np.log(0.5))
        return float(z_axis), float(r_xy)

    def calculate_spiral_coords(self):
        """计算锥面螺旋曲线坐标"""
        t = np.linspace(0, 8 * np.pi, self.num_t)
        a = 360

        # 计算基础螺旋曲线
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

    def generate_spiral_curves(self):
        """生成中心直线和螺旋曲线"""
        # 生成中心直线点

        z_values = np.linspace(0, self.user_high, self.num_t)
        center_line = np.array([[0, 0, z] for z in z_values])

        # 生成螺旋曲线点
        spiral_points = self.calculate_spiral_coords()

        # 确保点数一致
        if len(spiral_points) != self.num_t:
            t_old = np.linspace(0, 1, len(spiral_points))
            t_new = np.linspace(0, 1, self.num_t)
            spiral_points_interp = np.zeros((self.num_t, 3))
            for i in range(3):
                spiral_points_interp[:, i] = np.interp(t_new, t_old, spiral_points[:, i])
            spiral_points = spiral_points_interp

        # 计算框架向量
        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        for i in range(self.num_t):
            # 切向量始终沿Z轴
            T_unit[i] = np.array([0, 0, 1])

            # 计算从中心点到螺旋点的向量
            radial = spiral_points[i] - center_line[i]
            if np.linalg.norm(radial) > 1e-10:
                N_unit[i] = radial / np.linalg.norm(radial)
            else:
                N_unit[i] = np.array([1, 0, 0])

            # 计算副法向量
            B_unit[i] = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B_unit[i] / np.linalg.norm(B_unit[i])

        return center_line, spiral_points, [T_unit, N_unit, B_unit]

    def rotation_matrix_around_vector(self, v, psi):
        """根据任意单位向量 v 和旋转角度 psi 生成旋转矩阵"""
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

    def sweep_section(self):
        """使用正确对齐的断面进行扫掠"""
        center_points, spiral_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []
        def x(j):
            return self.section_x[j]

        def y(j):
            return self.section_y[j]

        for i in range(self.num_t):
            section_points = []
            for j in range(len(self.section_x)):
                # 在法向量-副法向量平面内构建点
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])
                # 计算 ellipse2 的每个点的坐标
                B_term1 = self.sign * x(j) * B_unit[i]
                N_term1 = self.sign * y(j) * N_unit[i]
                vector = np.dot(R_theta, (N_term1 + B_term1))

                global_point = [
                    center_points[i][0] + vector[0],
                    center_points[i][1] + vector[1],
                    center_points[i][2] + vector[2]
                ]
                if j == 0:
                    # 计算并存储蛋尖点的实际3D坐标
                    egghead_point = [
                        center_points[i][0] + vector[0],
                        center_points[i][1] + vector[1],
                        center_points[i][2] + vector[2]
                    ]
                    egghead_points.append(egghead_point)
                section_points.append(global_point)

            if not np.allclose(section_points[0], section_points[-1]):
                section_points.append(section_points[0])
            swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

    def save_to_dxf(self, filename):
        """保存到DXF文件"""
        # 定义颜色方案
        colors = {
            'center_line': 1,  # 红色
            'egg_tip': 5,  # 蓝色
            'sections': 3,  # 绿色
            'axis': 7  # 黄色
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, egghead_points = self.sweep_section()

        # 添加中心线
        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        # 添加蛋尖线
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        # 添加所有扫掠断面
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


# 使用示例
if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")

    generator_right = SpiralSweepGenerator('spline_points口朝右上逆转90度.csv')
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = -1  # 使用属性setter而不是直接访问_twist
    generator_right.save_to_dxf('最简优先 对扭转—口朝内(头朝下).dxf')

    generator_right.sign = 1   # 管旋转180
    generator_right.r = 1
    generator_right.save_to_dxf('螺旋锥 对扭转—口朝内(头朝下).dxf')
