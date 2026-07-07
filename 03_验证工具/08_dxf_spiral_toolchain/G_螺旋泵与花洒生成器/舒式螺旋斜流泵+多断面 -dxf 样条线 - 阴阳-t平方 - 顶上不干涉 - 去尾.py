import numpy as np
import ezdxf
from mpmath import mp

def x(t, a):
    """Calculate x coordinate for section curve"""
    return a * np.pi * np.sin(t) / t


def y(t, a):
    """Calculate y coordinate for section curve"""
    return a * np.pi * np.cos(t) / t


class SpiralSweepGenerator:
    """Spiral sweep generator class for creating 3D spiral curves with high precision"""


    def set_default_psi(self):
        """Set default psi values"""
        self.psi = np.linspace(0, self.twist * self.t_max / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """Set custom psi values"""
        self.psi = np.linspace(self.twist * start, self.twist * end, self.num_t)

    def generate_base_spirals(self, a_list=[180, 180, 180], n_list=[0, 2, 4]):
        """Generate smoother base spiral curves"""
        points_per_spiral = self.num_t // len(a_list)
        all_points = []

        for i in range(len(a_list)):
            t = np.linspace(0, 2 * np.pi, points_per_spiral * 2)
            a = a_list[i]
            n = n_list[i]

            # 计算半径
            r = self.bottom_r * np.power(self.phi, t / (a * np.pi / 180)) * np.power(self.phi, n)

            if i > 0:
                blend_factor = 0.2
                blend_start = int(len(r) * (1 - blend_factor))
                r[blend_start:] = np.linspace(r[blend_start], r[-1], len(r) - blend_start)

            x = r * np.cos(t)
            y = r * np.sin(t)

            if i > 0:
                points = np.column_stack((x[1:], y[1:]))
            else:
                points = np.column_stack((x, y))
            all_points.extend(points)

        points_array = np.array(all_points)
        t_old = np.linspace(0, 1, len(points_array))
        t_new = np.linspace(0, 1, self.num_t)
        x_interp = np.interp(t_new, t_old, points_array[:, 0])
        y_interp = np.interp(t_new, t_old, points_array[:, 1])

        return np.column_stack((x_interp, y_interp))


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

    def change_section(self, t_values, a):
        """Generate section curve using given x(t) and y(t) equations"""
        x_vals = x(t_values, a)
        y_vals = y(t_values, a)
        return x_vals, y_vals

    def __init__(self, t_min=0, t_max=6 * np.pi, d=4.31, z_v=2, amp=5,
                 sign_spiral_dir=1, sign=1, twist=-1, f=1.5, angle=0.588, b=1.6, c=1):
        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.t_length = self.t_max - self.t_min
        self.b = float(b)
        self.f = float(f)
        self.angle = float(angle)
        self.c = float(c)
        self.d = float(d)
        self.z_v = float(z_v)
        self.amp = float(amp)
        self.num_t = 90

        # 生成t_spiral
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 生成振幅序列
        self.a = np.linspace(self.amp, self.amp / 18, self.num_t)

        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.set_default_psi()

        # 使用numpy计算黄金分割比
        self.phi = (np.sqrt(5) - 1) / 2
        self.bottom_r = 10.0
        self.user_high = 6 * self.bottom_r
        self.turns_num = 18.0

        # 计算对数值
        self.h2 = np.log(0.5) / np.log(self.phi)
        self.h1 = np.log(self.turns_num / 2) / np.log(self.phi)
        self.total_h = self.h1 - self.h2

        # 生成t_values
        self.t_values = np.linspace(np.pi, 3 * np.pi, 12)

    def get_cone_profile(self, x, y):
        """Calculate cone profile using numpy"""
        x, y = float(x), float(y)
        r_xy = np.sqrt(x ** 2 + y ** 2)
        theta = np.arctan2(y, x)

        # 简化后的z_axis计算
        z_axis = np.log(0.5) / np.log(self.phi) + \
                 (np.log(self.bottom_r / r_xy) * self.user_high) / (np.log(self.turns_num / 2) - np.log(0.5))

        return float(z_axis), float(r_xy)

    def rotation_matrix_around_vector(self, v, psi):
        """Calculate rotation matrix around vector v by angle psi using numpy"""
        v = np.array(v, dtype=np.float64)
        psi = float(psi)

        # 归一化向量
        v = v / np.linalg.norm(v)
        vx, vy, vz = v

        # 构建旋转矩阵
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

        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")

    def rebuild_curve(self, points, tolerance=0.06, max_points=180):
        """Rebuild curve with given tolerance and max points number"""
        num_points = len(points)
        new_points = [points[0]]  # 保留起点

        for i in range(1, num_points - 1):
            prev_point = new_points[-1]
            current_point = points[i]
            next_point = points[i + 1]

            v1 = current_point - prev_point
            v2 = next_point - prev_point

            # 计算点到线的距离
            d = np.linalg.norm(np.cross(v1, v2)) / np.linalg.norm(v2)

            if d > tolerance and len(new_points) < max_points:
                new_points.append(current_point)

        new_points.append(points[-1])  # 保留终点
        return np.array(new_points)

    def sweep_section(self):
        """Generate swept sections along the spiral curve"""
        center_points, frame_vectors = self.generate_spiral_curves()

        # 重建中心线
        rebuilt_center_points = self.rebuild_curve(center_points)

        # 根据重建后的点重新计算框架向量
        # ... [这里需要重新计算frame_vectors，使用与generate_spiral_curves相同的逻辑]

        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        # 使用重建后的点继续原来的处理
        for i in range(len(rebuilt_center_points)):
            new_section_x, new_section_y = self.change_section(self.t_values, self.a[i])
            section_points = []

            for j in range(len(new_section_x)):
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])
                B_term = self.sign * new_section_x[j] * B_unit[i]
                N_term = self.sign * new_section_y[j] * N_unit[i]
                vector = np.dot(R_theta, (N_term + B_term))
                global_point = rebuilt_center_points[i] + vector

                if j == 0:
                    egghead_points.append(global_point.tolist())

                section_points.append(global_point.tolist())

            swept_sections.append(section_points)

        return swept_sections, rebuilt_center_points.tolist(), egghead_points


def main():
    """Main function to generate different spiral models"""
    print("Generating different spiral models...")

    generator = SpiralSweepGenerator()

    # Model 1: Right-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.twist = 1
    generator.save_to_dxf('spiral_1.dxf')
    print("Model 1 generated with high precision calculations")


if __name__ == "__main__":
    main()