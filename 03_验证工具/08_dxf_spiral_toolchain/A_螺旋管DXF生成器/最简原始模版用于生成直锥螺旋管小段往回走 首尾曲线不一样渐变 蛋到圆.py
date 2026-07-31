import numpy as np
import ezdxf
import pandas as pd
from scipy.interpolate import splprep, splev


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, taichi_data_path,
                 t_min=2 * np.pi, t_max=5 * np.pi, d=4,
                 amp=0.01, sign_spiral_dir=1, sign=1, twist=1,points=108):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = -np.log(2) / (self.t_length / 4)
        self.d = d
        self.amp = amp
        self.num_t = 49  # 总断面数（含首尾）
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp /5, self.amp, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self._sign = sign
        self.points=points #控制散点数量
        # 加载两个断面数据
        self.load_egg_section(spline_data_path)
        self.load_taichi_section(taichi_data_path)
        self.update_parameters()

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
        self.update_psi()

    def update_psi(self):
        self.psi = np.linspace(0, self._twist * self.t_length / 2, self.num_t)

    def load_egg_section(self, filepath):
        """加载蛋形数据（已对齐Y轴）"""
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"蛋形数据文件 {filepath} 未找到")

        # 重采样至self.points点
        x_raw = df['x'].values
        y_raw = df['y'].values
        tck, u = splprep([x_raw, y_raw], s=0, per=1)
        u_new = np.linspace(0, 1, self.points)
        self.egg_x, self.egg_y = splev(u_new, tck)

        # 确认基准点方向（无需旋转）
        t0_idx = np.argmin(np.abs(df['t'].values - 0))
        self.t0_point = np.array([df['x'][t0_idx], df['y'][t0_idx]])
    def load_taichi_section(self, filepath):
        """加载太极图数据（已对齐Y轴）"""
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"太极数据文件 {filepath} 未找到")

        # 重采样至self.points点
        x_raw = df['x'].values
        y_raw = df['y'].values
        tck, u = splprep([x_raw, y_raw], s=0, per=1)
        u_new = np.linspace(0, 1, self.points+1)
        self.taichi_x, self.taichi_y = splev(u_new, tck)

        # 确认基准点方向（无需旋转）
        t0_idx = np.argmin(np.abs(df['t'].values - 0))
        self.t0_point = np.array([df['x'][t0_idx], df['y'][t0_idx]])


    def calculate_spiral_coords(self):
        x = np.exp(self.b * self.t_spiral) * self.d * np.sin(self.t_spiral) * self.r
        y = np.exp(self.b * self.t_spiral) * self.d * np.cos(self.t_spiral)
        z = np.exp(self.b * self.t_spiral) * (self.t_spiral-4)
        return x, y, z

    def generate_spiral_curves(self):
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()
        dx = np.gradient(x_spiral)
        dy = np.gradient(y_spiral)
        dz = np.gradient(z_spiral)

        T_unit = np.column_stack((dx, dy, dz))
        T_norm = np.linalg.norm(T_unit, axis=1)
        T_unit = T_unit / T_norm[:, np.newaxis]

        # 简化的法向量计算
        N_unit = np.zeros_like(T_unit)
        N_unit[:, 0] = -T_unit[:, 1]
        N_unit[:, 1] = T_unit[:, 0]
        N_unit[:, 2] = 0

        B_unit = np.cross(T_unit, N_unit)
        return np.column_stack((x_spiral, y_spiral, z_spiral)), [T_unit, N_unit, B_unit]

    def rotation_matrix_around_vector(self, v, psi):
        v = v / np.linalg.norm(v)
        vx, vy, vz = v
        K = np.array([[0, -vz, vy], [vz, 0, -vx], [-vy, vx, 0]])
        I = np.eye(3)
        return I + np.sin(psi) * K + (1 - np.cos(psi)) * (K @ K)

    def sweep_section(self):
        """断面插值扫掠"""
        center_points, frames = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frames
        swept_sections = []
        tip_points = []

        for i in range(self.num_t):
            section = []
            t = i / (self.num_t - 1)  # 插值权重

            # 蛋形与扇形混合
            x_blend = (1 - t) * self.egg_x + t * self.taichi_x[:-1]  # 去除闭合点
            y_blend = (1 - t) * self.egg_y + t * self.taichi_y[:-1]

            for j in range(self.points):
                # 坐标系变换
                R = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])
                vec = np.dot(R, self.sign * (x_blend[j] * B_unit[i] + y_blend[j] * N_unit[i]))
                x_3d = center_points[i, 0] + self.a[i] * vec[0]
                y_3d = center_points[i, 1] + self.a[i] * vec[1]
                z_3d = center_points[i, 2] + self.a[i] * vec[2]
                section.append([x_3d, y_3d, z_3d])
                if j == 0:
                    tip_points.append([x_3d, y_3d, z_3d])

            # 闭合处理
            section.append(section[0])
            swept_sections.append(section)   #此处是断面sections

        return swept_sections, center_points.tolist(), tip_points #此处center_points.tolist()是导轨1（也就是curve1）的控制点， tip_points是导轨2（也就是curve2）的控制点

    def save_to_dxf(self, filename):
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()
        sections, center, tips = self.sweep_section()

        # 添加中心线
        msp.add_spline(center, dxfattribs={'color': 1})

        # 添加断面
        for section in sections:
            msp.add_spline(section, dxfattribs={'color': 3})

        # 添加尖端轨迹
        msp.add_spline(tips, dxfattribs={'color': 5})

        doc.saveas(filename)
        print(f"文件已保存至 {filename}")


# 使用示例
if __name__ == "__main__":
    generator = SpiralSweepGenerator(
        spline_data_path='spline_points口朝右上.csv',
        taichi_data_path='圆.csv'
    )
    generator.sign = -1
    generator.twist = -1
    generator.save_to_dxf('蛋形到圆形过渡+.dxf')