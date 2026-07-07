import numpy as np
import ezdxf
import pandas as pd
import math


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, bottom=10, top=5, high=10, n_turns=3, sign_spiral_dir=1,
                 sign=1, twist=1, amp=1.0):
        """
        初始化螺旋扫掠生成器
        :param bottom: 底部直径
        :param top: 顶部直径
        :param high: 高度
        :param n_turns: 螺旋圈数
        :param amp: 截面曲线形状大小的初始缩放因子，随时间线性减小到amp/3
        """
        self.bottom = bottom
        self.top = top
        self.high = high
        self.n_turns = n_turns
        self.num_t = 660
        self.t_param = np.linspace(0, 1, self.num_t)  # 参数t从0到1
        self.r = sign_spiral_dir
        self._twist = twist
        self._sign = sign
        self._amp = amp  # 初始振幅值
        self.a = np.linspace(self.amp, self.amp / 3, self.num_t)
        # 计算梯形锥角度
        self.calculate_cone_angle()

        self.load_section_data(spline_data_path)
        self.update_parameters()

    def calculate_top_from_angle(self, angle_deg):
        """
        根据给定的侧面与垂直方向夹角计算顶部直径
        :param angle_deg: 侧面与垂直方向夹角（度）
        :return: 计算出的顶部直径
        """
        if self.high <= 0:
            print("警告: 高度必须大于0才能计算角度")
            return self.top

        angle_rad = math.radians(angle_deg)
        bottom_radius = self.bottom / 2
        top_radius = bottom_radius - self.high * math.tan(angle_rad)
        top_diameter = 2 * top_radius

        print(f"根据侧面夹角 {angle_deg}° 计算:")
        print(f"  底部半径: {bottom_radius}")
        print(f"  计算出的顶部半径: {top_radius:.2f}")
        print(f"  计算出的顶部直径: {top_diameter:.2f}")

        return top_diameter

    def calculate_cone_angle(self):
        """计算梯形锥的角度"""
        # 计算侧面与垂直方向的夹角
        if self.high > 0:
            radius_diff = (self.bottom - self.top) / 2
            self.side_angle_rad = math.atan(radius_diff / self.high)
            self.side_angle_deg = math.degrees(self.side_angle_rad)

            # 计算锥顶角（两个侧面之间的夹角）
            self.apex_angle_deg = 2 * self.side_angle_deg

            print(f"梯形锥参数:")
            print(f"  底部直径: {self.bottom}")
            print(f"  顶部直径: {self.top}")
            print(f"  高度: {self.high}")
            print(f"  侧面与垂直方向夹角: {self.side_angle_deg:.2f}°")
            print(f"  锥顶角: {self.apex_angle_deg:.2f}°")
        else:
            print("警告: 高度必须大于0才能计算角度")

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

    @property
    def amp(self):
        return self._amp

    @amp.setter
    def amp(self, value):
        self._amp = value
        self.update_parameters()

    def update_parameters(self):
        """更新所有依赖于twist、sign和amp的参数"""
        self.update_psi()

    def update_psi(self):
        """更新psi值"""
        self.psi = np.linspace(self._twist * 2 * np.pi * self.n_turns, 0, self.num_t)

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

        # 归一化断面数据，使蛋尖点的y坐标为1
        t0_idx = np.argmin(np.abs(self.section_t - 0))
        egg_tip_y = self.section_y[t0_idx]
        self.section_x = self.section_x / egg_tip_y
        self.section_y = self.section_y / egg_tip_y

        # 保存原始截面数据（不应用振幅缩放）
        self.original_section_x = self.section_x.copy()
        self.original_section_y = self.section_y.copy()

    def calculate_spiral_coords(self):
        """计算螺旋线的坐标 - 修改为线性增长以实现梯形"""
        # 计算半径随高度的变化
        R_top = self.top / 2  # 顶部半径
        R_bottom = self.bottom / 2  # 底部半径

        # 半径从顶部到底部线性变化
        R = R_top + (R_bottom - R_top) * self.t_param

        # 计算角度
        theta = 2 * np.pi * self.n_turns * self.t_param

        x = R * np.sin(theta) * self.r
        y = R * np.cos(theta)
        z = self.t_param * self.high

        # 保存半径用于断面缩放
        self.R = R

        return x, y, z

    def generate_spiral_curves(self):
        """生成两条螺旋轨道线，确保断面正确对齐"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        # 计算切线向量
        dx = np.gradient(x_spiral, self.t_param)
        dy = np.gradient(y_spiral, self.t_param)
        dz = np.gradient(z_spiral, self.t_param)

        ddx = np.gradient(dx, self.t_param)
        ddy = np.gradient(dy, self.t_param)
        ddz = np.gradient(dz, self.t_param)

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
            return self.original_section_x[j]

        def y(j):
            return self.original_section_y[j]

        for i in range(self.num_t):
            section_points = []
            for j in range(len(self.original_section_x)):
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

    # 首先计算11°夹角对应的顶部直径
    generator = SpiralSweepGenerator('spline_points口朝右上.csv', bottom=300, top=150, high=200, amp=12)
    target_top = generator.calculate_top_from_angle(11)

    print(f"\n使用计算出的顶部直径 {target_top:.1f} 创建模型...")

    generator_right = SpiralSweepGenerator('spline_points口朝右上.csv', bottom=300, top=target_top, high=300, amp=12)
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = -0.5
    generator_right.save_to_dxf('参数可调最简优先 对扭转—口朝内(头朝下).dxf')

    generator_right.sign = 1  # 管旋转180
    generator_right.r = 1
    generator_right.save_to_dxf('参数可调螺旋锥 对扭转—口朝内(头朝下).dxf')