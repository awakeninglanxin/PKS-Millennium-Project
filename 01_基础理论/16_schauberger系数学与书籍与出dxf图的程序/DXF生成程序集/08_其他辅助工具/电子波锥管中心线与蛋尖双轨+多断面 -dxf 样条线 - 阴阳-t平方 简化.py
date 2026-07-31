import numpy as np
import ezdxf
import pandas as pd
from scipy.interpolate import interp1d


class SpiralSweepGenerator:
    """螺旋扫探生成器类，用于生成3D螺旋曲面模型"""

    def __init__(self, spline_data_path, t_min=-np.pi/2, t_max= np.pi/2, d=21, z_v=80, amp=1,
                 sign_spiral_dir=1, sign=1, twist=1, b=(np.sqrt(5) + 1) / 2, k=2):
        """
        初始化螺旋扫探生成器

        Args:
            spline_data_path (str): 断面数据文件路径
            t_min (float): 参数方程最小值
            t_max (float): 参数方程最大值
            d (float): 曲线缩放参数
            z_v (float): Z轴方向缩放
            amp (float): 振幅
            sign_spiral_dir (int): 螺旋方向符号
            sign (int): 整体符号
            twist (int): 扭转方向
            c (float): Z方向缩放系数
            b (float): 黄金分割比
            k (float): 螺旋缩放速度
        """
        self.validate_inputs(t_min, t_max, d, amp)

        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 121
        n = self.num_t // 2  # 单侧点数（不包括峰值点）
        self.a = np.concatenate([
            np.linspace(self.amp / 5, self.amp, n + 1)[:-1],  # 上升段，不包括峰值
            [self.amp],  # 峰值点
            np.linspace(self.amp, self.amp / 5, n + 1)[1:]  # 下降段，不包括峰值
        ])

        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.f = 24
        self.b = b
        self.k = k

        self.load_section_data(spline_data_path)
        self.set_default_psi()

    @staticmethod
    def validate_inputs(t_min, t_max, d, amp):
        """验证输入参数"""
        if t_max <= t_min:
            raise ValueError("t_max必须大于t_min")
        if d <= 0:
            raise ValueError("d必须为正数")
        if amp <= 0:
            raise ValueError("amp必须为正数")
    def set_default_psi(self):
        """设置默认的psi值"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)
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

    def change_section(self, section_x, section_y, a):
        """
        缩放断面坐标
        """
        return section_x * a, section_y * a

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

            if i == 0 or (i + 1) % 11 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points
    def calculate_curve_radius(self, t, d, f):
        """
        计算参数方程在给定t处的半径（标量版本）

        Args:
            t (float): 参数值
            d (float): 缩放参数
            f (float): 频率参数

        Returns:
            float: 曲线在该点的半径
        """
        t, d, f = map(float, (t, d, f))
        cos_t = np.cos(t)
        x_t = d * (cos_t ** 2) * np.sin(f * t)
        y_t = d * (cos_t ** 2) * np.cos(f * t)
        return np.sqrt(x_t ** 2 + y_t ** 2)

    def calculate_curve_radius_array(self, t, d, f):
        """计算参数方程在给定t处的半径（数组版本）"""
        cos_t = np.cos(t)
        x_t = d * np.power(cos_t, 2) * np.sin(f * t)
        y_t = d * np.power(cos_t, 2) * np.cos(f * t)
        return np.sqrt(x_t ** 2 + y_t ** 2)

    def find_end_t(self, d, f, threshold=0.1, epsilon=1e-6):
        """
        二分法找到使r(t) < threshold*d的t值

        Args:
            d (float): 缩放参数
            f (float): 频率参数
            threshold (float): 阈值比例
            epsilon (float): 精度控制

        Returns:
            float: 满足条件的t值
        """
        t_left, t_right = 0, np.pi / 2

        while (t_right - t_left) > epsilon:
            t_mid = (t_left + t_right) / 2
            r = self.calculate_curve_radius(t_mid, d, f)

            if r < (d * threshold):
                t_right = t_mid
            else:
                t_left = t_mid

        return t_left

    def calculate_spiral_coords(self):
        """
        计算参数方程定义的曲线坐标

        Returns:
            tuple: (x坐标数组, y坐标数组, z坐标数组)
        """
        t_end = self.find_end_t(self.d, self.f)
        print('t_end：',t_end)
        t = np.linspace(-t_end, t_end, self.num_t)

        cos_t = np.cos(t)
        cos_t_squared = cos_t ** 2
        f_t = self.f * t

        x = self.d * cos_t_squared * np.sin(f_t)
        y = self.d * cos_t_squared * np.cos(f_t)
        z = self.z_v * np.tan(t)

        return x, y, z

    def load_section_data(self, filepath):
        """
        加载并处理2D断面数据

        Args:
            filepath (str): 数据文件路径
        """
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到文件: {filepath}")
        except Exception as e:
            raise Exception(f"读取文件时出错: {str(e)}")

        self.section_t = df['t'].values
        self.section_x = df['x'].values
        self.section_y = df['y'].values

        # 处理断面方向
        self._process_section_direction()

        # 重建为34个点的曲线
        self._rebuild_section_curve()

    def _process_section_direction(self):
        """处理断面方向"""
        t0_idx = np.argmin(np.abs(self.section_t))
        self.t0_point = np.array([self.section_x[t0_idx], self.section_y[t0_idx]])
        vector_length = np.linalg.norm(self.t0_point)
        print(f"蛋心到蛋尖的初始长度: {vector_length}")

        # 旋转调整
        angle = np.arctan2(self.t0_point[0], self.t0_point[1])
        rot_matrix = np.array([
            [np.cos(-angle), -np.sin(-angle)],
            [np.sin(-angle), np.cos(-angle)]
        ])

        points = np.column_stack((self.section_x, self.section_y))
        rotated_points = np.dot(points, rot_matrix.T)

        self.section_x, self.section_y = rotated_points.T

    def _rebuild_section_curve(self):
        """重建断面曲线为34个点"""
        # 确保曲线闭合
        if not np.allclose([self.section_x[0], self.section_y[0]],
                           [self.section_x[-1], self.section_y[-1]]):
            self.section_x = np.append(self.section_x, self.section_x[0])
            self.section_y = np.append(self.section_y, self.section_y[0])

        # 计算参数化曲线
        dx = np.diff(self.section_x)
        dy = np.diff(self.section_y)
        segment_lengths = np.sqrt(dx ** 2 + dy ** 2)
        t = np.zeros(len(self.section_x))
        t[1:] = np.cumsum(segment_lengths)
        t = t / t[-1]

        # 重建为34个点
        t_new = np.linspace(0, 1, 34)
        self.section_x = interp1d(t, self.section_x)(t_new)
        self.section_y = interp1d(t, self.section_y)(t_new)

    def save_to_dxf(self, filename):
        """
        保存模型到DXF文件

        Args:
            filename (str): 输出文件名
        """
        colors = {
            'center_line': 1,
            'egg_tip': 5,
            'sections': 3,
            'axis': 4
        }

        try:
            doc = ezdxf.new(dxfversion='R2010')
            msp = doc.modelspace()

            swept_sections, center_points, egghead_points = self.sweep_section()

            # 添加中心线
            msp.add_spline(center_points).dxf.color = colors['center_line']

            # 添加蛋尖曲线
            msp.add_spline(egghead_points).dxf.color = colors['egg_tip']

            # 添加横截面
            for section in swept_sections:
                msp.add_spline(section).dxf.color = colors['sections']

            # 添加z轴
            z_coords = [p[2] for p in center_points]
            msp.add_line(
                (0, 0, min(z_coords)),
                (0, 0, max(z_coords))
            ).dxf.color = colors['axis']

            doc.saveas(filename)
            print(f"成功保存曲线到文件: {filename}")

        except Exception as e:
            print(f"保存DXF文件时出错: {str(e)}")
            raise


def main():
    """主函数 - 生成不同配置的模型"""
    try:
        print("生成口朝右下的模型，d为正...")

        # 创建生成器实例
        generator = SpiralSweepGenerator('spline_points口朝右上.csv')

        # 生成三个不同配置的模型
        configurations = [
            {
                'sign': 1,
                'r': -1,
                'twist': 1,
                'filename': 't平方最简优先 电子驻波形 对扭转—口朝内(头朝下).dxf'
            },
            {
                'sign': 1,
                'r': 1,
                'twist': 1,
                'filename': 't平方 电子驻波形 对扭转—口朝内(头朝外).dxf'
            },
            {
                'sign': -1,
                'r': 1,
                'twist': 1,
                'filename': 't平方 电子驻波形 对扭转—口朝内(头朝内).dxf'
            }
        ]

        for config in configurations:
            generator.sign = config['sign']
            generator.r = config['r']
            generator.twist = config['twist']
            generator.set_default_psi()
            generator.save_to_dxf(config['filename'])

    except Exception as e:
        print(f"生成模型时出错: {str(e)}")
        raise


if __name__ == "__main__":
    main()