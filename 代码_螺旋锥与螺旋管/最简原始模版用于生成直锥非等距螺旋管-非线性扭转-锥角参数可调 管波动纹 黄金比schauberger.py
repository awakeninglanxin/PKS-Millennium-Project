import numpy as np
import ezdxf
import math
from scipy.optimize import minimize
from scipy.interpolate import splprep, splev

phi=(np.sqrt(5)+1)/2
class SpiralSweepGenerator:
    def __init__(self, start_dxf_path, end_dxf_path, bottom=300, high=300, n_turns=2, sign_spiral_dir=1,
                 sign=1, twist=1, amp=1, alpha_deg=11,collect_n=50, amp_nonlinear=False, dxf_points=16,twist_type='linear'):
        """
        初始化螺旋扫掠生成器 - 只支持DXF文件
        增加dxf_points参数控制DXF曲线重建点数
        """
        self.amp_nonlinear = amp_nonlinear
        self.bottom = bottom
        self.high = high
        self.n_turns = n_turns
        self.num_t = 2205
        self.t_param = np.linspace(0, 1, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self.twist_type = twist_type  # 保存扭转类型
        self._sign = sign
        self.dxf_points = dxf_points  # DXF曲线重建点数
        self.alpha_deg = alpha_deg
        self.amp_initial = amp  # 保存初始amp值，用于加载阶段的断面缩放
        self.a = np.linspace(1, 1/3, self.num_t)
        self.collect_n = collect_n
        # 计算顶部直径
        self.top = self.calculate_top_diameter_from_alpha(self.alpha_deg)

        # 计算指数螺旋参数
        self.calculate_spiral_parameters()

        # 直接从DXF文件加载断面数据
        self.load_section_from_dxf(start_dxf_path, section_type='start')
        self.load_section_from_dxf(end_dxf_path, section_type='end')

        self.update_parameters()
        self._precompute_exp_wave()

    @property
    def twist(self):
        return self._twist

    @twist.setter
    def twist(self, value):
        self._twist = value
        self.update_parameters()  # 自动更新参数
    def load_section_from_dxf(self, dxf_path, section_type):
        """
        从DXF文件加载断面数据，使用dxf_points参数重建曲线
        修改：强制将断面缩放到等效半径为amp
        """
        try:
            # 读取DXF文件
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # 查找第一条SPLINE
            spline_found = False
            for entity in msp:
                if entity.dxftype() == 'SPLINE':
                    spline_found = True
                    spline_tool = entity.construction_tool()

                    # 使用指定点数重建曲线，并将生成器转换为列表
                    points_generator = spline_tool.approximate(self.dxf_points)
                    points = list(points_generator)

                    # 确保有足够的点
                    if len(points) < 3:
                        raise RuntimeError(f"重建的曲线点数不足 ({len(points)}点)，需要至少3个点")

                    # 提取x,y坐标
                    x_vals = [p[0] for p in points]
                    y_vals = [p[1] for p in points]

                    # 寻找正x半轴交点 (y≈0, x>0)
                    base_point_index = None
                    min_angle = float('inf')
                    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                        # 计算点与x轴的夹角（绝对值）
                        if x != 0:
                            angle = abs(math.atan(y / x))
                            # 选择最接近x轴的点（夹角最小的点）
                            if angle < min_angle and x > 0:
                                min_angle = angle
                                base_point_index = i

                    # 如果没有找到合适的点，使用最接近(0,0)的点
                    if base_point_index is None:
                        min_dist = float('inf')
                        for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                            dist = math.sqrt(x ** 2 + y ** 2)
                            if dist < min_dist:
                                min_dist = dist
                                base_point_index = i

                    # 获取基准点的坐标
                    base_x = x_vals[base_point_index]
                    base_y = y_vals[base_point_index]

                    # 计算基准点到x轴的偏移量
                    y_offset = base_y

                    # 避免除零错误（如果需要）
                    if abs(base_x) < 1e-6:
                        base_x = 1e-6 if base_x >= 0 else -1e-6

                    # 归一化处理：将基准点移到(1,0)
                    x_temp = []
                    y_temp = []
                    for x, y in zip(x_vals, y_vals):
                        # 先平移y坐标，使基准点的y坐标为0
                        y_adjusted = y - y_offset

                        # 然后缩放，使基准点的x坐标为1
                        x_temp.append(x / base_x)
                        y_temp.append(y_adjusted / base_x)

                    # 转换为NumPy数组
                    x_norm = np.array(x_temp)
                    y_norm = np.array(y_temp)

                    # 计算等效圆半径（面积相等）
                    def calculate_equivalent_circle_radius(x, y):
                        # 计算断面多边形面积
                        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
                        # 计算等效圆半径
                        equivalent_circle_radius = np.sqrt(area / np.pi) if area > 0 else 0
                        return equivalent_circle_radius

                    # 计算当前等效半径
                    current_radius = calculate_equivalent_circle_radius(x_norm, y_norm)

                    # 强制缩放到等效半径为amp
                    if current_radius > 0:
                        # 计算缩放因子：目标amp / 当前等效半径
                        scale_factor = self.amp_initial / current_radius
                        x_norm *= scale_factor
                        y_norm *= scale_factor
                    else:
                        scale_factor = 1.0
                        print(f"警告: {dxf_path} 等效半径为零或负值，不进行缩放")

                    # 重新计算缩放后的等效半径
                    final_radius = calculate_equivalent_circle_radius(x_norm, y_norm)

                    # 如果最终半径接近amp，则设置为amp（避免浮点精度问题）
                    if abs(final_radius - self.amp_initial) < 1e-6:
                        final_radius = self.amp_initial

                    if section_type == 'start':
                        self.start_x, self.start_y = x_norm, y_norm
                        section_name = "起始断面"
                    else:
                        self.end_x, self.end_y = x_norm, y_norm
                        section_name = "结束断面"

                    # 打印基准点信息
                    print(f"成功加载 {dxf_path}: 重建为 {self.dxf_points} 点, 基准点索引 {base_point_index}")
                    print(f"基准点原始坐标: ({x_vals[base_point_index]:.6f}, {y_vals[base_point_index]:.6f})")
                    print(f"归一化后基准点坐标: ({x_norm[base_point_index]:.6f}, {y_norm[base_point_index]:.6f})")
                    print(f"缩放因子: {scale_factor:.6f}")
                    print(f"目标等效半径: {self.amp_initial:.6f}")
                    print(f"{section_name}实际等效半径: {final_radius:.6f}")

                    return

            if not spline_found:
                raise RuntimeError(f"未在DXF文件中找到样条曲线: {dxf_path}")

        except Exception as e:
            # 使用更安全的错误信息生成方式
            error_msg = f"加载DXF文件失败: {dxf_path} - {type(e).__name__}: {str(e)}"
            raise RuntimeError(error_msg)
    def calculate_equivalent_radius(x, y):
        # 计算所有点到原点的距离
        distances = np.sqrt(x ** 2 + y ** 2)

        # 计算平均半径
        avg_radius = np.mean(distances)

        # 计算最大半径
        max_radius = np.max(distances)

        # 计算最小半径
        min_radius = np.min(distances)

        # 计算等效圆半径（面积相等）
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        equivalent_circle_radius = np.sqrt(area / np.pi) if area > 0 else 0

        return {
            "avg_radius": avg_radius,
            "max_radius": max_radius,
            "min_radius": min_radius,
            "equivalent_circle_radius": equivalent_circle_radius
        }

    def sweep_section(self):
        """使用断面插值扫掠方法生成扫掠曲面，增加中间点轨道"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        # 确保断面数据是NumPy数组
        if not isinstance(self.end_x, np.ndarray):
            self.end_x = np.array(self.end_x)
            self.end_y = np.array(self.end_y)
        if not isinstance(self.start_x, np.ndarray):
            self.start_x = np.array(self.start_x)
            self.start_y = np.array(self.start_y)

        # 确保两个断面点数相同
        min_points = min(len(self.end_x), len(self.start_x))
        end_x = -self.end_x[:min_points]   # 此处加了负号在前代表以Y轴镜像翻了一下
        end_y = self.end_y[:min_points]
        start_x = -self.start_x[:min_points] # 此处加了负号在前代表以Y轴镜像翻了一下
        start_y = self.start_y[:min_points]

        for i in range(self.num_t):
            section_points = []
            t = i / (self.num_t - 1)  # 插值权重，从0到1

            # 交换了混合顺序：start_x -> end_x
            x_blend = ((1 - t) * start_x + t * end_x)
            y_blend = ((1 - t) * start_y + t * end_y)

            for j in range(len(x_blend)):
                # 在法向量-副法向量平面内构建点
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i]) * self.exp_wave(i)
                # 计算每个点的坐标
                B_term1 = self.sign * x_blend[j] * B_unit[i]
                N_term1 = self.sign * y_blend[j] * N_unit[i]
                vector = np.dot(R_theta, (N_term1 + B_term1))
                global_point = [
                    center_points[i][0] + self.a[i] * vector[0],
                    center_points[i][1] + self.a[i] * vector[1],
                    center_points[i][2] + self.a[i] * vector[2]
                ]

                # 记录蛋咬一口尖点 (j=0)
                if j == 0:
                    egghead_points.append(global_point)
                section_points.append(global_point)

            # 闭合处理 - 添加第一个点作为最后一个点
            if not np.allclose(section_points[0], section_points[-1]):
                section_points.append(section_points[0])

            # 仅保存部分断面以节省内存
            if i == 0 or (i + 1) % 21 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points
    def _precompute_exp_wave(self):
        """预计算exp_wave的值"""
        # 定义目标波段数量
        target_bands = 47

        # 定义优化函数
        def objective(k):
            # 数值积分计算总波段数
            t_samples = np.linspace(0, self.n_turns * 2 * np.pi, 100000)
            freq = np.power(phi, k * t_samples)/ (2 * np.pi)
            # 使用 trapezoid 替代 trapz
            phase = np.trapezoid(freq, t_samples)
            return abs(phase - target_bands +0.1)  # +0.1是为了消除末尾振幅的扩展

        # 优化求解k值
        res = minimize(objective, x0=0.1, bounds=[(0.001, 1)])
        k = res.x[0]

        # 计算时间序列（映射到0-1范围）
        t_normalized = self.t_param * (self.n_turns * 2 * np.pi) / (self.n_turns * 2 * np.pi)

        # 计算频率和相位
        freq = np.power(phi, k * t_normalized* (self.n_turns * 2 * np.pi)) / (2 * np.pi)
        phase = np.cumsum(freq) * (t_normalized[1] - t_normalized[0]) * (self.n_turns * 2 * np.pi)

        # 生成锯齿波 (从1降到0)
        y = 2 - phase % 1

        # 计算振幅
        if self.amp_nonlinear:
            amplitude = np.power(phi, t_normalized * self.n_turns)
        else:
            amplitude = np.ones_like(t_normalized)  # 线性情况
        self.exp_wave_values = amplitude * y

        # 验证结果
        actual_bands = phase[-1] - phase[0]
        print(f"计算得到的k值为: {k:.10f}")
        print(f"目标波段数量: {target_bands:.6f} (21-0.001)")
        print(f"实际累计波段数量: {actual_bands:.10f}")
        print(f"误差: {abs(actual_bands - target_bands):.2e}")

    def exp_wave(self, t_index):
        """
        获取预计算的波形值
        :param t_index: 时间索引
        :return: 波形值
        """
        return self.exp_wave_values[t_index]

    def calculate_top_diameter_from_alpha(self, alpha_deg):
        """根据目标侧面夹角alpha_deg计算顶部直径"""
        top_radius = (self.bottom / 2) - (math.tan(math.radians(alpha_deg)) * self.high)
        return 2 * top_radius

    def update_parameters(self):
        """更新所有依赖于twist、sign和amp的参数"""
        self.update_psi()

    def update_psi(self):
        """更新psi值，根据选择的扭转类型"""
        t_length = 2 * np.pi * self.n_turns
        shift0to1 = 0
        exponential_coef=3
        if self.twist_type == 'linear':
            # 线性扭转

            self.psi = np.linspace(-shift0to1 * self._twist * t_length,
                                   (1 - shift0to1) * self._twist * t_length,
                                   self.num_t)
        elif self.twist_type == 'exponential':
            # 非线性指数增长扭转
            # 创建归一化的时间参数 t ∈ [0, 1]
            t_normalized = np.linspace(0, 1, self.num_t)
            # 计算指数增长函数
            # exponential_growth = np.exp(exponential_coef*t_normalized) - 1
            # 使用以2为底的指数函数
            exponential_growth = np.power(2, exponential_coef * t_normalized) - 1
            # 归一化到0到1的范围
            # exponential_normalized = exponential_growth / (np.exp(exponential_coef) - 1)
            exponential_normalized = exponential_growth / (np.power(2, exponential_coef) - 1)
            # 应用总的扭转角度（保持原有的偏移量逻辑）
            base_angle = -shift0to1 * self._twist * t_length
            total_range = self._twist * t_length
            self.psi = base_angle + exponential_normalized * total_range
        else:
            raise ValueError(f"未知的扭转类型: {self.twist_type}。请选择 'linear' 或 'exponential'")

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
        找到每指定圈数间隔范围内距离z轴最近的蛋咬一口尖点，以及首尾断面的最近点
        增加内插值曲线功能（颜色2）
        :param swept_sections: 扫掠断面列表
        :param egghead_points: 蛋咬一口尖点列表
        :param turn_interval: 圈数间隔（例如0.5表示每半圈）
        :param n_end_sections: 首尾要处理的断面数量
        :return: 包含所有点组的列表，对应的z轴投影点列表，以及内插值曲线列表
        """
        # 1. 按圈数间隔分组
        groups = []
        projection_points = []
        interpolated_curves = []  # 存储内插值曲线点

        # 计算每个蛋咬一口尖点到z轴的距离
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

            # 收集该点及其前后各collect_n个点
            start_collect = max(0, min_idx_in_interval - self.collect_n)
            end_collect = min(self.num_t, min_idx_in_interval + self.collect_n+1)  # +6 因为切片是左闭右开

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

            # 生成内插值曲线（样条曲线）
            if len(collected_points) >= 3:  # 至少需要3个点才能生成样条曲线
                # 提取坐标
                x = [p[0] for p in collected_points]
                y = [p[1] for p in collected_points]
                z = [p[2] for p in collected_points]

                # 使用样条插值
                tck, u = splprep([x, y, z], s=0)
                u_new = np.linspace(0, 1, 100)  # 生成100个点用于平滑曲线
                x_new, y_new, z_new = splev(u_new, tck)

                # 创建曲线点列表
                curve_points = list(zip(x_new, y_new, z_new))
                interpolated_curves.append(curve_points)
            else:
                interpolated_curves.append([])  # 点数不足，添加空列表

        # 2. 处理首尾断面的最近点
        # 处理前n_end_sections个断面
        for i in range(min(n_end_sections, len(swept_sections))):
            section = swept_sections[i]
            # 找到该断面上距离z轴最近的点
            min_point = min(section, key=lambda p: np.sqrt(p[0] ** 2 + p[1] ** 2))
            groups.append([min_point])
            projection_points.append([[0, 0, min_point[2]]])
            interpolated_curves.append([])  # 单点无法生成曲线

        # 处理后n_end_sections个断面
        for i in range(max(0, len(swept_sections) - n_end_sections), len(swept_sections)):
            section = swept_sections[i]
            # 找到该断面上距离z轴最近的点
            min_point = min(section, key=lambda p: np.sqrt(p[0] ** 2 + p[1] ** 2))
            groups.append([min_point])
            projection_points.append([[0, 0, min_point[2]]])
            interpolated_curves.append([])  # 单点无法生成曲线

        return groups, projection_points, interpolated_curves

    def save_to_dxf(self, filename, turn_interval=0.5, n_end_sections=2):
        """保存到DXF文件，增加中间点轨道和偏移截面"""
        # 定义颜色方案
        colors = {
            'center_line': 1,  # 红色
            'egg_tip': 5,  # 蓝色
            'sections': 3,  # 绿色
            'axis': 7,  # 黑色
            'projection_lines': 6,  # 品红色
            'end_section_lines': 6,  # 品红色
            'interpolated_curves': 2  # 黄色
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, egghead_points = self.sweep_section()  # 获取偏移截面

        # 添加中心线
        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        # 添加蛋咬一口尖线
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']


        # 添加所有扫掠断面
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        # 添加中心轴
        z_coords = [p[2] for p in center_points]
        z_axis_length = max(z_coords) - min(z_coords)
        line = msp.add_line((0, 0, -z_axis_length / 3), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        # 添加每指定圈数间隔的最近点及其投影连线
        groups, projection_points, interpolated_curves = self.find_closest_points_to_z_axis(
            swept_sections, egghead_points, turn_interval, n_end_sections
        )

        for group, proj_group in zip(groups, projection_points):
            # 添加投影点连线
            for point, proj_point in zip(group, proj_group):
                # 根据组的大小确定颜色：大组使用品红色，小组（首尾断面）使用青色
                color = colors['end_section_lines'] if len(group) == 1 else colors['projection_lines']
                line = msp.add_line(point, proj_point)
                line.dxf.color = color

        # 添加内插值曲线（颜色2）
        for curve in interpolated_curves:
            if curve:  # 只添加非空曲线
                spline = msp.add_spline(curve)
                spline.dxf.color = colors['interpolated_curves']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")

if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    print("当psi越来越大，则是顺时针旋转；若是越来越小 → 则是逆时针旋转")
    new_bottom, new_h, new_amp = 108, 144, 3
    target_side_angle_deg =13.282525   # 用户要求的侧面夹角 11.75是基于地磁偏角

    # 使用目标侧面夹角计算top直径并创建模型
    generator_right = SpiralSweepGenerator(
        'start 舒伯格蛋咬一口曲线.dxf', 'end 舒伯格蛋咬一口曲线.dxf',
        bottom=new_bottom,
        high=new_h,
        amp=new_amp,
        alpha_deg=target_side_angle_deg,
        dxf_points=32,  # 指定DXF曲线重建点数
        twist_type = 'exponential'  # linear线性扭转，exponential非线性扭转
    )

    # 设置其他参数并生成dxf文件
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = -0.5
    generator_right.save_to_dxf('波纹螺旋锥管 指数螺旋_phi.dxf',
                                turn_interval=0.5)  # 使用0.5圈间隔，首尾各2个断面
