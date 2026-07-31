import numpy as np
import pandas as pd  # Add this import
from scipy.interpolate import interp1d
import ezdxf
from mpmath import mp


class SpiralSweepGenerator:
    """Spiral sweep generator class for creating 3D spiral curves with high precision"""
    def __init__(self, t_min=0, t_max=6 * np.pi, amp=0.3,
                 sign_spiral_dir=1, sign=1, twist=1, f=1.5, angle=0.588, b=1.6, c=1):
        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.t_length = self.t_max - self.t_min
        self.b = float(b)
        self.f = float(f)
        self.angle = float(angle)
        self.c = float(c)
        self.amp = float(amp)
        self.num_t = 240

        # Generate t_spiral
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # Generate amplitude sequence
        self.a = np.linspace(self.amp, self.amp / 32, self.num_t)

        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.set_default_psi()

        # Calculate golden ratio using numpy
        self.phi = (np.sqrt(5) - 1) / 2
        self.bottom_r = 10.0

        self.turns_num = 32
        self.a = np.linspace(self.amp, self.amp /self.turns_num, self.num_t)
        # Calculate logarithmic values
        self.h2 = np.log(0.5) / np.log(self.phi)
        self.h1 = np.log(self.turns_num / 2) / np.log(self.phi)
        self.total_h = self.h1 - self.h2
        print('缩放锥的前自然高度：',abs(self.total_h))
        self.user_high = abs(self.total_h) * self.bottom_r
        # self.user_high = 60

        # Generate t_values
        self.t_values = np.linspace(0, 2 * np.pi, 12)

    def load_section_data(self, filepath):
        """
        Load 2D section data, rebuild to 34 points, and ensure closure
        """
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
        vector_length = np.linalg.norm(self.t0_point)
        print(f"Initial length from section start to end: {vector_length}")

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

    def change_section(self, t_vals, section_x, section_y, a):
        """
        缩放断面坐标

        Parameters:
            t_vals: 参数值
            section_x: x坐标
            section_y: y坐标
            a: 缩放因子

        Returns:
            缩放后的x和y坐标
        """
        return section_x * a, section_y * a

    def set_default_psi(self):
        """Set default psi values"""
        self.psi = np.linspace(0, self.twist * self.t_max / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """Set custom psi values"""
        self.psi = np.linspace(self.twist * start, self.twist * end, self.num_t)

    def generate_base_spirals(self):
        """Generate base spiral curve"""
        t = np.linspace(0, 8 * np.pi, self.num_t)
        a = 360

        # Calculate radius
        r = self.bottom_r * np.power(2, -t / (a * np.pi / 180))

        x = r * np.cos(t)
        y = r * np.sin(t)

        points_array = np.column_stack((x, y))
        return points_array

    def calculate_spiral_coords(self):
        """Project spiral onto cone surface with high precision"""
        spiral_points = self.generate_base_spirals()
        projected_points = []

        for point in spiral_points:
            x, y = point[0], point[1]
            if abs(x) < 1e-10:
                continue

            z_cone, r_cone = self.get_cone_profile(x, y)
            projected_points.append([x, y, z_cone])

        if not projected_points:
            return np.zeros((1, 3))

        return np.array(projected_points)

    def generate_spiral_curves(self):
        """Generate spiral curves with their frame vectors"""
        # Get projected points
        points = self.calculate_spiral_coords()

        # Ensure we have exactly num_t points
        if len(points) != self.num_t:
            t_old = np.linspace(0, 1, len(points))
            t_new = np.linspace(0, 1, self.num_t)
            points_interp = np.zeros((self.num_t, 3))
            for i in range(3):
                points_interp[:, i] = np.interp(t_new, t_old, points[:, i])
            points = points_interp

        # Separate coordinates
        x_spiral = points[:, 0]
        y_spiral = points[:, 1]
        z_spiral = points[:, 2]

        # Calculate derivatives
        dx = np.gradient(x_spiral, self.t_spiral)
        dy = np.gradient(y_spiral, self.t_spiral)
        dz = np.gradient(z_spiral, self.t_spiral)

        ddx = np.gradient(dx, self.t_spiral)
        ddy = np.gradient(dy, self.t_spiral)
        ddz = np.gradient(dz, self.t_spiral)

        # Initialize unit vectors
        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        # Calculate Frenet frame
        for i in range(self.num_t):
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)

            N = np.array([ddx[i], ddy[i], ddz[i]])
            N_unit[i] = N / np.linalg.norm(N)

            B = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B / np.linalg.norm(B)

        center_points = np.column_stack((x_spiral, y_spiral, z_spiral))
        return center_points, [T_unit, N_unit, B_unit]




    def get_cone_profile(self, x, y):
        """Calculate cone profile using numpy"""
        x, y = float(x), float(y)
        r_xy = np.sqrt(x ** 2 + y ** 2)
        theta = np.arctan2(y, x)

        # Simplified z_axis calculation
        z_axis = np.log(0.5) / np.log(self.phi) + \
                 (np.log(self.bottom_r / r_xy) * self.user_high) / (np.log(self.turns_num / 2) - np.log(0.5))

        return float(z_axis), float(r_xy)

    def rotation_matrix_around_vector(self, v, psi):
        """Calculate rotation matrix around vector v by angle psi using numpy"""
        v = np.array(v, dtype=np.float64)
        psi = float(psi)

        # Normalize vector
        v = v / np.linalg.norm(v)
        vx, vy, vz = v

        # Construct rotation matrix
        K = np.array([
            [0, -vz, vy],
            [vz, 0, -vx],
            [-vy, vx, 0]
        ])

        I = np.eye(3)
        R = I + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)

        return R

    def save_to_dxf(self, filename):
        """Save the generated curves to a DXF file"""
        colors = {
            'center_line': 1,  # White
            'egg_tip': 5,  # Blue
            'section_normal': 6,
            'section_highlight': 3,  # Green
            'axis': 4  # Cyan
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, egghead_points, section_colors = self.sweep_section()

        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        for section, color_type in zip(swept_sections, section_colors):
            spline = msp.add_spline(section)
            spline.dxf.color = colors[color_type]

        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")

    def sweep_section(self):
        """Generate swept sections along the spiral curve"""
        center_points, frame_vectors = self.generate_spiral_curves()

        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []
        section_colors = []

        for i in range(len(center_points)):
            # 使用存储的section数据
            new_section_x, new_section_y = self.change_section(
                self.t_values,
                self.section_x,  # 使用加载的断面数据
                self.section_y,  # 使用加载的断面数据
                self.a[i]  # 缩放因子
            )
            section_points = []

            for j in range(len(new_section_x)):
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])
                B_term = self.sign * new_section_x[j] * B_unit[i]
                N_term = self.sign * new_section_y[j] * N_unit[i]
                vector = np.dot(R_theta, (N_term + B_term))
                global_point = center_points[i] + vector

                if j == 0:
                    egghead_points.append(global_point.tolist())

                section_points.append(global_point.tolist())

            swept_sections.append(section_points)

            # Determine color for this section
            if i == 0 or (i + 1) % 20 == 0:
                section_colors.append('section_highlight')  # Green
            else:
                section_colors.append('section_normal')  # Red

        return swept_sections, center_points.tolist(), egghead_points, section_colors



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
    generator.save_to_dxf('蛋面sun螺旋_1.dxf')
    print("Model 1 generated with high precision calculations")

    # Model 2: Left-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.twist = -1
    generator.set_default_psi()
    generator.save_to_dxf('蛋面sun螺旋_2.dxf')
    print("Model 2 generated")

    # Model 3: Custom twisted spiral
    generator.sign = 1
    generator.r = -1
    generator.twist = -1
    generator.set_custom_psi(-np.pi / 2, generator.t_length / 2 - np.pi / 2)
    generator.save_to_dxf('蛋面sun螺旋_3.dxf')
    print("Model 3 generated")

if __name__ == "__main__":
    main()