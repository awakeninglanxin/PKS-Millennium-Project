import numpy as np
import ezdxf
import pandas as pd


def x(t, a):
    return a * np.pi * np.sin(t) / t


def y(t, a):
    return a * np.pi * np.cos(t) / t


class SpiralSweepGenerator:
    """螺旋扫探生成器类"""

    def __init__(self, t_min=3 * np.pi, t_max=8 * np.pi, d=4.31, z_v=0.3487125*1.08, amp=10,
                 sign_spiral_dir=1, sign=1, twist=1):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = np.log(2) / (self.t_length / 2)
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 147 * 2
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp, self.amp / 2.5, self.num_t)
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.set_default_psi()

        # Generate the initial section curve
        t_section = np.linspace(np.pi, 3 * np.pi, 100)  # Added: Generate points for the section curve
        self.section_x, self.section_y = self.change_section(t_section, self.amp)

    def set_default_psi(self):
        """设置默认的psi值"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """设置自定义的psi值"""
        self.psi = np.linspace(self.twist * start, self.twist * end, self.num_t)

    def change_section(self, t_values, a):
        """
        使用给定的x(t)和y(t)方程，根据参数a生成截面曲线。
        """
        x_vals = x(t_values, a)
        y_vals = y(t_values, a)
        return x_vals, y_vals

    def calculate_spiral_coords(self):
        x = np.exp(self.b * self.t_spiral) * self.d * np.sin(self.t_spiral) * self.r
        y = np.exp(self.b * self.t_spiral) * self.d * np.cos(self.t_spiral)
        z = (self.t_spiral ** 2 * self.z_v - self.t_min ** 2 * self.z_v)
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
        在同一平面内偏移断面曲线

        参数:
        offset_distance: float, 偏移距离
        section_x, section_y: 断面坐标数组

        返回:
        offset_x, offset_y: 偏移后的断面坐标数组
        """
        points = np.column_stack((section_x, section_y))
        num_points = len(points)
        offset_points = np.zeros_like(points)

        for i in range(num_points):
            # 获取当前点和相邻点
            prev_point = points[(i - 1) % num_points]
            curr_point = points[i]
            next_point = points[(i + 1) % num_points]

            # 计算相邻边的向量
            v1 = curr_point - prev_point
            v2 = next_point - curr_point

            # 单位化向量
            v1_norm = v1 / np.linalg.norm(v1)
            v2_norm = v2 / np.linalg.norm(v2)

            # 计算单位法向量（垂直于平面）
            normal = np.array([0, 0, 1])

            # 计算当前点的偏移方向（两边的平均）
            n1 = np.cross(normal, v1_norm)[:2]  # 只取x,y分量
            n2 = np.cross(v2_norm, normal)[:2]  # 只取x,y分量

            # 归一化偏移方向
            offset_dir = (n1 + n2)
            if np.all(offset_dir == 0):  # 处理特殊情况（180度角）
                offset_dir = n1
            offset_dir = offset_dir / np.linalg.norm(offset_dir)

            # 计算偏移点
            offset_points[i] = curr_point + offset_dir * offset_distance

        return offset_points[:, 0], offset_points[:, 1]

    def sweep_section(self):
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        # 生成 t 从 π 到 3π 的值
        t_values = np.linspace(np.pi, 3 * np.pi, 36)

        for i in range(self.num_t):
            new_section_x, new_section_y = self.change_section(t_values, self.a[i])
            section_points = []

            for j in range(len(new_section_x)):
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])

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

            if i == 0 or (i + 1) % 7 == 0:
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

        for section in swept_sections:
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

    # 创建生成器实例
    generator = SpiralSweepGenerator()

    # 第一个模型
    generator.sign = 1
    generator.r = -1
    generator.twist = -1
    generator.save_to_dxf('spiral_model_1.dxf')

    # 第二个模型
    generator.sign = -1
    generator.r = -1
    generator.set_default_psi()
    generator.save_to_dxf('spiral_model_2.dxf')

    # 第三个模型
    generator.sign = 1
    generator.r = -1
    generator.set_custom_psi(-np.pi / 2, generator.t_length / 2 - np.pi / 2)
    generator.save_to_dxf('spiral_model_3.dxf')


if __name__ == "__main__":
    main()