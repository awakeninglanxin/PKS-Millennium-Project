import numpy as np
import ezdxf
import pandas as pd
from scipy.interpolate import splprep, splev


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, fan_dxf_path,
                 t_min=2 * np.pi, t_max=5 * np.pi, d=4, z_v=1,
                 amp=0.005, sign_spiral_dir=1, sign=1, twist=1,points=50):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = -np.log(2) / (self.t_length / 4)
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 49  # 总断面数（含首尾）
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp / 3, self.amp, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self._sign = sign
        self.points=points #控制散点数量
        # 加载两个断面数据
        self.load_egg_section(spline_data_path)
        self.load_fan_section(fan_dxf_path)
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

    def load_fan_section(self, dxf_path):
        """从散点数据重建扇形断面"""
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 收集所有点实体的坐标
        fan_points = []
        for entity in msp:
            if entity.dxftype() == 'POINT':
                x, y, _ = entity.dxf.location  # 忽略Z坐标
                fan_points.append((x, y))
            elif entity.dxftype() == 'LINE':
                # 如果散点实际是线段端点
                fan_points.extend([entity.dxf.start[:2], entity.dxf.end[:2]])

        # 转换为数组并去重
        fan_points = np.unique(np.array(fan_points), axis=0)

        # 验证点数
        if len(fan_points) < 4:
            raise ValueError("扇形数据至少需要4个特征点")

        # 几何中心计算
        center = np.mean(fan_points, axis=0)

        # 极角排序（以Y轴正方向为起点）
        rel_points = fan_points - center
        theta = np.arctan2(rel_points[:, 1], rel_points[:, 0])
        theta = (theta + 2 * np.pi) % (2 * np.pi)  # 转换到0-2π范围
        sorted_idx = np.argsort(theta)
        fan_sorted = fan_points[sorted_idx]

        # 闭合处理（添加首点）
        fan_sorted = np.vstack([fan_sorted, fan_sorted[0]])

        # 获取t参数数据（创建一个与点数量对应的t值）
        t_values = np.linspace(0, 1, len(fan_sorted))  # 生成与断面点数量相同的时间参数

        # 样条重采样
        tck, u = splprep(fan_sorted.T, u=None, s=0, per=0)
        u_new = np.linspace(0, 1, self.points+1)
        self.fan_x, self.fan_y = splev(u_new, tck)

        # 强制闭合
        self.fan_x[-1] = self.fan_x[0]
        self.fan_y[-1] = self.fan_y[0]

        # 返回t和扇形断面坐标
        self.fan_t = t_values  # 存储t参数

    def calculate_spiral_coords(self):
        x = np.exp(self.b * self.t_spiral) * self.d * np.sin(self.t_spiral) * self.r
        y = np.exp(self.b * self.t_spiral) * self.d * np.cos(self.t_spiral)
        z = np.exp(self.b * self.t_spiral) * (self.t_spiral - 5)
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
            x_blend = (1 - t) * self.egg_x + t * self.fan_x[:-1]  # 去除闭合点
            y_blend = (1 - t) * self.egg_y + t * self.fan_y[:-1]

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
            swept_sections.append(section)

        return swept_sections, center_points.tolist(), tip_points

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
        fan_dxf_path='扇形.dxf'
    )
    generator.sign = 1
    generator.twist = -1
    generator.save_to_dxf('蛋形到扇形过渡.dxf')