import numpy as np
import ezdxf
import pandas as pd


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, t_min=0 * np.pi, t_max=3 * np.pi, d=4, z_v=1, amp=0.1, sign_spiral_dir=1,
                 sign=1, twist=1):
        """
        初始化螺旋扫掠生成器 np.sqrt(2)
        """
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = 0.1
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 660
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp, self.amp / 3, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self._sign = sign
        self.load_section_data(spline_data_path)
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
        """更新所有依赖于twist和sign的参数"""
        self.update_psi()
        # 这里可以添加其他需要随sign变化而更新的参数

    def update_psi(self):
        """更新psi值 - 改为非线性指数增长"""
        # 归一化的t值，从0到1
        t_normalized = (self.t_spiral - self.t_min) / self.t_length

        # 指数增长函数: ratio = e^t - 1, t ≥ 0
        # 这里t_normalized从0到1，所以e^t_normalized - 1从0到(e-1)
        exponential_growth = np.exp(t_normalized) - 1

        # 归一化到0到1的范围
        exponential_normalized = exponential_growth / (np.exp(1) - 1)

        # 应用总的扭转角度
        self.psi = exponential_normalized * self._twist * self.t_length

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

    def calculate_spiral_coords(self):
        """计算螺旋线的坐标"""
        x = (1+2/(np.pi)) **(self.t_spiral) * np.sin(self.t_spiral) * self.r
        y = (1+2/(np.pi)) **(self.t_spiral) * np.cos(self.t_spiral)
        z = (1+2/(np.pi)) **(self.t_spiral) *self.z_v
        return x, y, z

    def generate_spiral_curves(self):
        """生成两条螺旋轨道线，确保断面正确对齐"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        # 计算切线向量
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
            # 切线向量
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)

            # 构造初始法向量（在xz平面内）
            N = np.array([ddx[i], ddy[i], ddz[i]])
            N_unit[i] = N / np.linalg.norm(N)

            # 计算副法向量
            B = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B / np.linalg.norm(B)

        # 生成螺旋线
        center_points = []

        for i in range(self.num_t):
            # Center point
            center_points.append([x_spiral[i], y_spiral[i], z_spiral[i]])

        return np.array(center_points), [T_unit, N_unit, B_unit]

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
        center_points, frame_vectors = self.generate_spiral_curves()
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
                    center_points[i][0] + self.a[i] * vector[0],
                    center_points[i][1] + self.a[i] * vector[1],
                    center_points[i][2] + self.a[i] * vector[2]
                ]
                if j == 0:
                    # 计算并存储蛋尖点的实际3D坐标
                    egghead_point = [
                        center_points[i][0] + self.a[i] * vector[0],
                        center_points[i][1] + self.a[i] * vector[1],
                        center_points[i][2] + self.a[i] * vector[2]
                    ]
                    egghead_points.append(egghead_point)
                section_points.append(global_point)

            if not np.allclose(section_points[0], section_points[-1]):
                section_points.append(section_points[0])
            # if i == 0 or (i + 1) % 2 == 0 or (i + 1) % 3 == 0 or (i + 1) % 5 == 0 or (i + 1) % 11 == 0:
            if i == 0 or (i + 1) % 11 == 0:
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

        # 添加中心轴
        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


# 使用示例
if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    generator_right = SpiralSweepGenerator('spline_points口朝右上.csv')
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = -0.5
    generator_right.save_to_dxf('最简优先 对扭转—口朝内(头朝下) krystal 2.dxf')
    generator_right.sign = 1  # 管旋转180
    generator_right.r = 1

    generator_right.save_to_dxf('螺旋锥 对扭转—口朝内(头朝下) krystal 2.dxf')