import numpy as np
import ezdxf
import pandas as pd
import math


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, bottom=300, high=300, n_turns=1.5, sign_spiral_dir=1,
                 sign=1, twist=1, amp=0.75, alpha_deg=11):
        """
        初始化螺旋扫掠生成器
        :param bottom: 底部直径 = 300
        :param high: 高度 = 300
        :param n_turns: 螺旋圈数
        :param amp: 截面曲线形状大小的初始缩放因子，随时间线性减小到amp/3
        :param alpha_deg: 目标侧面夹角，若提供则根据此计算顶部直径
        """
        self.bottom = bottom
        self.high = high
        self.n_turns = n_turns
        self.num_t = 660
        self.t_param = np.linspace(0, 1, self.num_t)  # 参数t从0到1
        self.r = sign_spiral_dir
        self._twist = twist
        self._sign = sign
        self.alpha_deg = alpha_deg  # 目标侧面夹角
        self.a = np.linspace(amp, amp / 4, self.num_t)
        # 如果提供了目标侧面夹角alpha_deg，则根据该值反推top直径
        self.top = self.calculate_top_diameter_from_alpha(self.alpha_deg)
        # 计算指数螺旋参数
        self.calculate_spiral_parameters()
        # 计算梯形锥角度
        self.load_section_data(spline_data_path)
        self.update_parameters()

    def calculate_top_diameter_from_alpha(self, alpha_deg):
        """根据目标侧面夹角alpha_deg计算顶部直径"""
        top_radius = (self.bottom / 2) - (math.tan(math.radians(alpha_deg)) * self.high)
        return 2 * top_radius

    def update_parameters(self):
        """更新所有依赖于twist、sign和amp的参数"""
        self.update_psi()

    def update_psi(self):
        """更新psi值（使用非线性指数增长扭转）"""
        t_length = 2 * np.pi * self.n_turns

        # 创建归一化的时间参数 t ∈ [0, 1]
        t_normalized = np.linspace(0, 1, self.num_t)

        # 计算指数增长函数
        exponential_growth = np.exp(t_normalized) - 1

        # 归一化到0到1的范围
        exponential_normalized = exponential_growth / (np.exp(1) - 1)

        # 应用总的扭转角度（保持原有的偏移量逻辑）
        shift0to1 = 0.25
        base_angle = -shift0to1 * self._twist * t_length
        total_range = self._twist * t_length

        self.psi = base_angle + exponential_normalized * total_range

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
            if i == 0 or (i + 1) % 11 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

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

    def calculate_spiral_parameters(self):
        """计算指数螺旋的参数"""
        R_top = self.top / 2
        R_bottom = self.bottom / 2

        # 计算b因子: R_bottom = R_top * exp(b)
        if R_top > 0:
            self.b = math.log(R_bottom / R_top)
        else:
            self.b = 0

        print(f"指数螺旋参数:")
        print(f"  顶部半径: {R_top}")
        print(f"  底部半径: {R_bottom}")
        print(f"  指数因子 b: {self.b:.4f}")

    def calculate_spiral_coords(self):
        """计算非线性螺旋线的坐标 - 基于指数螺旋原理"""
        R_top = self.top / 2

        # 使用指数螺旋计算半径: R = R_top * exp(b * t)
        R = R_top * np.exp(self.b * self.t_param)

        # 计算角度
        theta = 2 * np.pi * self.n_turns * self.t_param

        # 计算坐标
        x = R * np.sin(theta) * self.r
        y = R * np.cos(theta)

        # 计算高度 - 使用指数关系保持一致性
        if abs(self.b) > 1e-6:
            z = self.high * (np.exp(self.b * self.t_param) - 1) / (np.exp(self.b) - 1)
        else:
            z = self.t_param * self.high  # 线性退化

        # 保存半径用于断面缩放
        self.R = R

        return x, y, z

    def analyze_spiral_properties(self):
        """分析螺旋线的特性，包括实际的几何参数"""
        x, y, z = self.calculate_spiral_coords()

        # 计算相邻点之间的距离
        dx = np.diff(x)
        dy = np.diff(y)
        dz = np.diff(z)
        distances = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

        # 计算半径变化率
        dR = np.diff(self.R)

        # 计算实际的几何参数
        actual_height = z[-1] - z[0]
        actual_radius_diff = self.R[-1] - self.R[0]

        if actual_height > 0:
            actual_side_angle_rad = math.atan(actual_radius_diff / actual_height)
            actual_side_angle_deg = math.degrees(actual_side_angle_rad)
            actual_apex_angle_deg = 2 * actual_side_angle_deg

            print(f"\n=== 实际几何参数分析 ===")
            print(f"  实际底部直径: {2 * self.R[-1]:.2f}")
            print(f"  实际顶部直径: {2 * self.R[0]:.2f}")
            print(f"  实际高度: {actual_height:.2f}")
            print(f"  实际侧面夹角: {actual_side_angle_deg:.2f}°")
            print(f"  实际锥顶角: {actual_apex_angle_deg:.2f}°")

        print(f"\n=== 螺旋线特性分析 ===")
        print(f"  总长度: {np.sum(distances):.2f}")
        print(f"  平均间距: {np.mean(distances):.4f}")
        print(f"  最大间距: {np.max(distances):.4f}")
        print(f"  最小间距: {np.min(distances):.4f}")
        print(f"  半径变化范围: {self.R[0]:.2f} -> {self.R[-1]:.2f}")
        print(f"  最大半径变化率: {np.max(np.abs(dR)):.4f}")

        return {
            'bottom_diameter': 2 * self.R[-1],
            'top_diameter': 2 * self.R[0],
            'height': actual_height,
            'side_angle_deg': actual_side_angle_deg,
            'apex_angle_deg': actual_apex_angle_deg,
            'b_factor': self.b,
            'total_length': np.sum(distances)
        }

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
        self.section_x = -self.section_x / egg_tip_y  # 此处加了负号在前代表以Y轴镜像翻了一下
        self.section_y = self.section_y / egg_tip_y

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

    def find_closest_points_to_z_axis(self, swept_sections, egghead_points, turn_interval=0.5, n_end_sections=2):
        """
        找到每指定圈数间隔范围内距离z轴最近的蛋尖点，以及首尾断面的最近点
        :param swept_sections: 扫掠断面列表
        :param egghead_points: 蛋尖点列表
        :param turn_interval: 圈数间隔（例如0.5表示每半圈）
        :param n_end_sections: 首尾要处理的断面数量
        :return: 包含所有点组的列表，以及对应的z轴投影点列表
        """
        # 1. 按圈数间隔分组
        groups = []
        projection_points = []

        # 计算每个蛋尖点到z轴的距离
        distances = [np.sqrt(p[0] ** 2 + p[1] ** 2) for p in egghead_points]

        # 计算每个间隔对应的点数
        points_per_interval = int(self.num_t * (turn_interval / self.n_turns))

        # 计算间隔数量
        num_intervals = int(self.n_turns / turn_interval)

        for i in range(num_intervals):
            start_idx = i * points_per_interval
            end_idx = min((i + 1) * points_per_interval, self.num_t)

            # 找到该间隔内距离z轴最近的点
            interval_distances = distances[start_idx:end_idx]
            min_idx_in_interval = np.argmin(interval_distances) + start_idx

            # 收集该点及其前后各5个点
            start_collect = max(0, min_idx_in_interval - 5)
            end_collect = min(self.num_t, min_idx_in_interval + 6)  # +6 因为切片是左闭右开

            # 如果起点不足5个点，从结尾补充
            if min_idx_in_interval - start_collect < 5:
                needed = 5 - (min_idx_in_interval - start_collect)
                end_collect = min(self.num_t, end_collect + needed)

            # 如果终点不足5个点，从开头补充
            if end_collect - min_idx_in_interval - 1 < 5:
                needed = 5 - (end_collect - min_idx_in_interval - 1)
                start_collect = max(0, start_collect - needed)

            # 收集点
            collected_points = egghead_points[start_collect:end_collect]
            groups.append(collected_points)

            # 为这些点创建对应的z轴投影点
            proj_group = [[0, 0, p[2]] for p in collected_points]
            projection_points.append(proj_group)

        # 2. 处理首尾断面的最近点
        # 处理前n_end_sections个断面
        for i in range(min(n_end_sections, len(swept_sections))):
            section = swept_sections[i]
            # 找到该断面上距离z轴最近的点
            min_point = min(section, key=lambda p: np.sqrt(p[0] ** 2 + p[1] ** 2))
            groups.append([min_point])
            projection_points.append([[0, 0, min_point[2]]])

        # 处理后n_end_sections个断面
        for i in range(max(0, len(swept_sections) - n_end_sections), len(swept_sections)):
            section = swept_sections[i]
            # 找到该断面上距离z轴最近的点
            min_point = min(section, key=lambda p: np.sqrt(p[0] ** 2 + p[1] ** 2))
            groups.append([min_point])
            projection_points.append([[0, 0, min_point[2]]])

        return groups, projection_points

    def save_to_dxf(self, filename, turn_interval=0.5, n_end_sections=2):
        """保存到DXF文件
        :param filename: 输出文件名
        :param turn_interval: 圈数间隔（例如0.5表示每半圈）
        :param n_end_sections: 首尾要处理的断面数量
        """
        # 定义颜色方案
        colors = {
            'center_line': 1,  # 红色
            'egg_tip': 5,  # 蓝色
            'sections': 3,  # 绿色
            'axis': 7,  # 黄色
            'projection_lines': 6,  # 品红色
            'end_section_lines': 6   # 品红色
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

        # 添加每指定圈数间隔的最近点及其投影连线
        groups, projection_points = self.find_closest_points_to_z_axis(
            swept_sections, egghead_points, turn_interval, n_end_sections
        )

        for group, proj_group in zip(groups, projection_points):
            # 添加投影点连线
            for point, proj_point in zip(group, proj_group):
                # 根据组的大小确定颜色：大组使用品红色，小组（首尾断面）使用青色
                color = colors['end_section_lines'] if len(group) == 1 else colors['projection_lines']
                line = msp.add_line(point, proj_point)
                line.dxf.color = color

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


# 使用示例
if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    new_bottom, new_h, new_amp = 75, 95, 9
    target_side_angle_deg = 11.75  # 用户要求的侧面夹角

    # 使用目标侧面夹角计算top直径并创建模型
    generator_right = SpiralSweepGenerator(
        'spline_points口朝右上.csv',
        bottom=new_bottom,
        high=new_h,
        amp=new_amp,
        alpha_deg=target_side_angle_deg  # 直接传递侧面夹角参数
    )

    # 设置其他参数并生成dxf文件
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = -0.5
    generator_right.save_to_dxf('非线性扭转 指数螺旋_固定参数.dxf',
                                turn_interval=0.5)  # 使用0.5圈间隔，首尾各2个断面

    generator_right.sign = 1  # 管旋转180
    generator_right.r = 1
    generator_right.save_to_dxf('非线性扭转 指数螺旋_反向旋转.dxf',
                                turn_interval=0.5)  # 使用0.25圈间隔，首尾各3个断面