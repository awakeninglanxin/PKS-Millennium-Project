import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import ezdxf


class SpiralSweepGenerator:
    def __init__(self, t_min=0, t_max=6 * np.pi, amp=0.3,
                 sign_spiral_dir=1, sign=1, f=1.5, angle=0.588, b=1.6, c=1):
        # 基础参数初始化
        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.t_length = self.t_max - self.t_min
        self.num_t = 240
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 控制参数
        self.r = sign_spiral_dir
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

        self.reference_length = None
        self.t0_point = None

    def load_section_data(self, filepath):
        """加载断面数据，特别处理t=0点"""
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {filepath} not found.")

        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 找到并存储t=0点的原始位置
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])
        self.reference_length = np.linalg.norm(self.t0_point)

        # 重建为34个点的闭合曲线
        if not np.allclose([self.section_x[0], self.section_y[0]],
                           [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

        t = np.zeros(len(self.section_x))
        dx = np.diff(self.section_x)
        dy = np.diff(self.section_y)
        segment_lengths = np.sqrt(dx ** 2 + dy ** 2)
        t[1:] = np.cumsum(segment_lengths)
        t = t / t[-1]

        t_new = np.linspace(0, 1, 34)
        interp_x = interp1d(t, self.section_x)
        interp_y = interp1d(t, self.section_y)

        self.section_x = interp_x(t_new)
        self.section_y = interp_y(t_new)

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
        # 生成中心直线点 - 保持沿着z轴
        z_values = np.linspace(0, self.total_h, self.num_t)
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
            # 副法向量始终沿Z轴
            B_unit[i] = np.array([0, 0, 1])

            # 计算从z轴到螺旋点的水平投影向量作为N向量
            radial = spiral_points[i] - np.array([0, 0, spiral_points[i][2]])
            if np.linalg.norm(radial) > 1e-10:
                N_unit[i] = radial / np.linalg.norm(radial)
            else:
                N_unit[i] = np.array([1, 0, 0])

            # 计算切向量
            T_unit[i] = np.cross(N_unit[i], B_unit[i])
            T_unit[i] = T_unit[i] / np.linalg.norm(T_unit[i])

        return center_line, spiral_points, [T_unit, N_unit, B_unit]

    def sweep_section(self):
        """沿中心直线扫掠断面，同时保持t=0点跟随螺旋曲线"""
        center_line, spiral_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        swept_sections = []
        egghead_points = []
        section_colors = []

        for i in range(self.num_t):
            # 计算当前螺旋点到中心线的距离作为缩放因子
            radial_vector = spiral_points[i] - center_line[i]
            scale_factor = np.linalg.norm(radial_vector) / self.bottom_r

            # 缩放断面
            scaled_x = self.section_x * scale_factor
            scaled_y = self.section_y * scale_factor

            section_points = []
            for j in range(len(scaled_x)):
                B_term = self.sign * scaled_x[j] * B_unit[i]
                N_term = self.sign * scaled_y[j] * N_unit[i]
                vector = B_term + N_term

                # 以中心直线上的点为基准
                global_point = center_line[i] + vector

                # 如果是t=0点，确保它落在螺旋曲线上
                if j == 0:
                    global_point = spiral_points[i]
                    egghead_points.append(global_point.tolist())

                section_points.append(global_point.tolist())

            swept_sections.append(section_points)
            section_colors.append('section_normal' if i % 20 != 0 else 'section_highlight')

        return swept_sections, center_line.tolist(), egghead_points, section_colors

    def get_cone_profile(self, x, y):
        x, y = float(x), float(y)
        r_xy = np.sqrt(x ** 2 + y ** 2)
        z_axis = np.log(0.5) / np.log(self.phi) + \
                 (np.log(self.bottom_r / r_xy) * self.user_high) / (np.log(self.turns_num / 2) - np.log(0.5))
        return float(z_axis), float(r_xy)

    def save_to_dxf(self, filename):
        """保存到DXF文件"""
        colors = {
            'center_line': 1,
            'egg_tip': 5,
            'section_normal': 6,
            'section_highlight': 3,
            'axis': 4
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, egghead_points, section_colors = self.sweep_section()

        # 中心线
        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        # 螺旋边缘线
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        # 截面
        for section, color_type in zip(swept_sections, section_colors):
            spline = msp.add_spline(section)
            spline.dxf.color = colors[color_type]

        # Z轴
        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)


def main():
    """Main function to generate different spiral models"""
    print("Generating spiral models...")

    # Initialize the generator
    generator = SpiralSweepGenerator()

    # Load section data from your specific CSV file
    generator.load_section_data("spline_points口朝右上逆转90度.csv")

    # Model 1: Right-facing spiral
    generator.sign = -1
    generator.r = -1
    generator.save_to_dxf('直管蛋面locas螺旋_1.dxf')
    print("Model 1 generated")

    # Model 2: Left-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.save_to_dxf('直管蛋面locas螺旋_2.dxf')
    print("Model 2 generated")


if __name__ == "__main__":
    main()