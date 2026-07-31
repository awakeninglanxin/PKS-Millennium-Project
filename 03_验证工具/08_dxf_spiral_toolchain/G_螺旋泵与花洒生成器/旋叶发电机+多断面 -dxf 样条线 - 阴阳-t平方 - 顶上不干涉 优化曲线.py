import numpy as np
import ezdxf
import pandas as pd

def x(t, a):
    """Calculate x coordinate for section curve"""
    # return a * np.pi * np.sin(t) / t
    return a * np.pi * np.cos(t) *np.sqrt(2)**(-t)

def y(t, a):
    """Calculate y coordinate for section curve"""
    # return a * np.pi * np.cos(t) / t
    return a * np.pi *- np.sin(t) *np.sqrt(2)**(-t)

class SpiralSweepGenerator:
    """Spiral sweep generator class for creating 3D spiral curves"""

    def __init__(self, t_min=-np.pi / 2, t_max=2 * np.pi / 3, d=5, z_v=1, amp=0.15,
                 sign_spiral_dir=1, sign=1, twist=1, k=2 / 3, b=1.6, c=1):
        # 修改了参数默认值：t_min, t_max, d, z_v
        # 移除了f和angle参数，增加了k参数
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = b
        self.k = k  # 新增参数k，替代原来的angle
        self.alpha = np.arctan(k)  # 计算alpha
        self.c = c
        self.d = d  # d现在直接作为参数，不再是计算值
        self.z_v = z_v  # z_v默认值改为1
        self.amp = amp
        self.num_t = 105
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp, self.amp / 12, self.num_t)
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.set_default_psi()

        # Generate the initial section curve
        t_section = np.linspace(0, 1.5 * np.pi, 16)
        self.section_x, self.section_y = self.change_section(t_section, self.amp)

    def calculate_spiral_coords(self):
        """Calculate spiral coordinates using the egg-shaped spiral formula from doc2"""
        t = self.t_spiral

        # 计算中间变量
        sin_alpha = np.sin(self.alpha)
        cos_alpha = np.cos(self.alpha)

        # 计算分母项，避免除零错误
        denominator = self.b - t * sin_alpha

        # 只处理分母不为零的点
        valid_indices = np.abs(denominator) > 1e-10

        # 计算平方根内的表达式
        term1 = 1 / (denominator[valid_indices] ** 2)
        term2 = (t[valid_indices] * cos_alpha) ** 2
        inside_sqrt = term1 - term2

        # 只处理非负的平方根
        valid_sqrt = inside_sqrt >= 0

        # 获取最终有效的t值
        t_final = t[valid_indices][valid_sqrt]

        # 计算半径
        radius = np.sqrt(inside_sqrt[valid_sqrt])

        # 计算坐标
        x_spiral = radius * np.cos(self.d * t_final)
        y_spiral = radius * np.sin(self.d * t_final)
        z_spiral = -t_final * self.z_v

        # 确保所有数组长度一致
        min_length = min(len(x_spiral), len(y_spiral), len(z_spiral))
        x_spiral = x_spiral[:min_length]
        y_spiral = y_spiral[:min_length]
        z_spiral = z_spiral[:min_length]

        # 更新t_spiral以匹配有效点
        self.t_spiral = t_final[:min_length]
        self.num_t = min_length

        return x_spiral, y_spiral, z_spiral

    def generate_spiral_curves(self):
        """Generate spiral curves with their frame vectors"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        # 确保有足够的点来计算导数
        if len(x_spiral) < 3:
            raise ValueError("Not enough valid points to generate spiral curves")

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
    def set_default_psi(self):
        """Set default psi values"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """Set custom psi values"""
        self.psi = np.linspace(self.twist * start, self.twist * end, self.num_t)

    def change_section(self, t_values, a):
        """Generate section curve using given x(t) and y(t) equations"""
        x_vals = x(t_values, a)
        y_vals = y(t_values, a)
        return x_vals, y_vals


    def rotation_matrix_around_vector(self, v, psi):
        """Calculate rotation matrix around vector v by angle psi"""
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
        """Offset section curve in the same plane"""
        points = np.column_stack((section_x, section_y))
        num_points = len(points)
        offset_points = np.zeros_like(points)

        for i in range(num_points):
            prev_point = points[(i - 1) % num_points]
            curr_point = points[i]
            next_point = points[(i + 1) % num_points]

            v1 = curr_point - prev_point
            v2 = next_point - curr_point

            v1_norm = v1 / np.linalg.norm(v1)
            v2_norm = v2 / np.linalg.norm(v2)

            normal = np.array([0, 0, 1])

            n1 = np.cross(normal, v1_norm)[:2]
            n2 = np.cross(v2_norm, normal)[:2]

            offset_dir = (n1 + n2)
            if np.all(offset_dir == 0):
                offset_dir = n1
            offset_dir = offset_dir / np.linalg.norm(offset_dir)

            offset_points[i] = curr_point + offset_dir * offset_distance

        return offset_points[:, 0], offset_points[:, 1]

    def sweep_section(self):
        """Generate swept sections along the spiral curve"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        # t_values = np.linspace(np.pi, 3 * np.pi, 36)
        t_values = np.linspace(0, 1.5 * np.pi, 36)
        for i in range(self.num_t):
            new_section_x, new_section_y = self.change_section(t_values, self.a[i])
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

            if i == 0 or (i + 1) % 7 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

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

        # Add center line
        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        # Add egg tip line
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        # Add section curves
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        # Add vertical axis
        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")

def main():
    """Main function to generate different spiral models"""
    print("生成不同方向的螺旋模型...")

    # Create generator instance
    generator = SpiralSweepGenerator()

    # Model 1: Right-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.set_default_psi()
    generator.save_to_dxf('旋叶发电spiral_model_1.dxf')
    print("Model 1 generated")

    # Model 2: Left-facing spiral
    generator.sign = -1
    generator.r = -1
    generator.set_default_psi()
    generator.save_to_dxf('旋叶发电spiral_model_2.dxf')
    print("Model 2 generated")

    # Model 3: Custom twisted spiral
    generator.sign = 1
    generator.r = -1
    generator.set_custom_psi(-np.pi / 2, generator.t_length / 2 - np.pi / 2)
    generator.save_to_dxf('旋叶发电spiral_model_3.dxf')
    print("Model 3 generated")

if __name__ == "__main__":
    main()