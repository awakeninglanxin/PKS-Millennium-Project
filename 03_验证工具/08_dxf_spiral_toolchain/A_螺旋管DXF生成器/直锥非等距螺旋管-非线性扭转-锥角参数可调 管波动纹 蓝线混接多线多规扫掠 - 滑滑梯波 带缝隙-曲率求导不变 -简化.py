import numpy as np
import ezdxf
import math
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev
from numba import jit, njit
from multiprocessing import Pool, cpu_count
import time

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 黄金比例常数
phi = (np.sqrt(5) + 1) / 2
phi_small = (np.sqrt(5) - 1) / 2
phi_squared = phi ** 2
phi_cubic = phi ** 3
sections_mod_n = 21
twist_angle = 0.5



# JIT编译优化函数
@njit(fastmath=True)
def rotation_matrix_around_vector_jit(v, psi):
    """JIT优化的旋转矩阵计算"""
    v_norm = np.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    vx, vy, vz = v[0] / v_norm, v[1] / v_norm, v[2] / v_norm

    K = np.array([[0, -vz, vy],
                  [vz, 0, -vx],
                  [-vy, vx, 0]])

    sin_psi = np.sin(psi)
    cos_psi = np.cos(psi)

    R = np.eye(3) + sin_psi * K + (1 - cos_psi) * (K @ K)
    return R


@njit(fastmath=True)
def evaluate_bezier_jit(control_points, t):
    """JIT优化的贝塞尔曲线计算"""
    n = len(control_points) - 1
    point = np.zeros(3)

    for i in range(n + 1):
        # 计算伯恩斯坦基函数
        bernstein = math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
        point += bernstein * control_points[i]

    return point


@njit(fastmath=True)
def bezier_curve_points_jit(control_points, num_points=20):
    """JIT优化的贝塞尔曲线点生成（不使用math.factorial）"""
    n = len(control_points) - 1
    points = []

    # 预计算组合数（二项式系数）
    binom_coeffs = np.zeros(n + 1)
    for k in range(n + 1):
        # 计算 C(n, k) = n! / (k! * (n-k)
        binom = 1
        for i in range(1, min(k, n - k) + 1):
            binom = binom * (n - i + 1) // i
        binom_coeffs[k] = binom

    for t_idx in range(num_points):
        t = t_idx / (num_points - 1) if num_points > 1 else 0
        point = np.zeros(3)

        for i in range(n + 1):
            # 计算伯恩斯坦基函数
            bernstein = binom_coeffs[i] * (t ** i) * ((1 - t) ** (n - i))
            point += bernstein * control_points[i]

        points.append(point)

    return points

class SpiralSweepGenerator:
    def __init__(self, start_dxf_path, end_dxf_path, bottom=300, high=300, n_turns=2.5, sign_spiral_dir=1,
                 sign=1, twist=1, amp=1, alpha_deg=11, global_a=1, collect_n=50, amp_nonlinear=False, dxf_points=19,
                 twist_type='linear',bands=15, use_parallel=True):
        """
        初始化螺旋扫掠生成器 - 支持并行处理

        参数:
        start_dxf_path: 起始断面DXF文件路径
        end_dxf_path: 结束断面DXF文件路径
        bottom: 底部直径
        high: 高度
        n_turns: 螺旋圈数
        sign_spiral_dir: 螺旋方向 (1或-1)
        sign: 断面旋转符号
        twist: 扭转角度
        amp: 振幅
        alpha_deg: 侧面夹角(度)
        global_a: 全局缩放因子
        collect_n: 收集断面间隔
        amp_nonlinear: 是否使用非线性振幅
        dxf_points: DXF曲线重建点数
        twist_type: 扭转类型 ('linear'或'exponential')
        use_parallel: 是否使用并行处理
        """
        self.amp_nonlinear = amp_nonlinear
        self.bottom = bottom * global_a
        self.high = high * global_a
        self.n_turns = n_turns
        self.num_t = 945*2
        self.t_param = np.linspace(0, 1, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self.twist_type = twist_type
        self._sign = sign
        self.dxf_points = dxf_points
        self.alpha_deg = alpha_deg
        self.amp_initial = amp
        self.a = np.linspace(1, 1 / 3, self.num_t)
        self.collect_n = collect_n
        self.global_a = global_a
        self.jump_points = []
        self.bands=bands
        self.use_parallel = use_parallel  # 是否使用并行处理

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
        self.update_parameters()

    def load_section_from_dxf(self, dxf_path, section_type):
        """从DXF文件加载断面数据并进行归一化和缩放"""
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # 查找第一条SPLINE
            for entity in msp:
                if entity.dxftype() == 'SPLINE':
                    spline_tool = entity.construction_tool()
                    # 修正拼写错误：approximate 而不是 appproximate
                    points = list(spline_tool.approximate(self.dxf_points))

                    if len(points) < 3:
                        raise RuntimeError(f"重建的曲线点数不足 ({len(points)}点)，需要至少3个点")

                    # 提取坐标并寻找基准点
                    x_vals = [p[0] for p in points]
                    y_vals = [p[1] for p in points]

                    base_point_index = None
                    min_angle = float('inf')
                    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                        if x != 0:
                            angle = abs(math.atan(y / x))
                            if angle < min_angle and x > 0:
                                min_angle = angle
                                base_point_index = i

                    if base_point_index is None:
                        min_dist = float('inf')
                        for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                            dist = math.sqrt(x ** 2 + y ** 2)
                            if dist < min_dist:
                                min_dist = dist
                                base_point_index = i

                    # 归一化处理
                    base_x, base_y = x_vals[base_point_index], y_vals[base_point_index]
                    y_offset = base_y
                    if abs(base_x) < 1e-6:
                        base_x = 1e-6 if base_x >= 0 else -1e-6

                    x_temp, y_temp = [], []
                    for x, y in zip(x_vals, y_vals):
                        y_adjusted = y - y_offset
                        x_temp.append(x / base_x)
                        y_temp.append(y_adjusted / base_x)

                    # 计算等效圆半径并缩放
                    area = 0.5 * np.abs(np.dot(x_temp, np.roll(y_temp, 1)) - np.dot(y_temp, np.roll(x_temp, 1)))
                    equivalent_radius = np.sqrt(area / np.pi) if area > 0 else 0

                    if equivalent_radius > 0:
                        scale_factor = self.amp_initial / equivalent_radius
                        x_norm = np.array(x_temp) * scale_factor
                        y_norm = np.array(y_temp) * scale_factor
                    else:
                        scale_factor = 1.0
                        x_norm, y_norm = np.array(x_temp), np.array(y_temp)
                        print(f"警告: {dxf_path} 等效半径为零或负值，不进行缩放")

                    # 保存结果
                    if section_type == 'start':
                        self.start_x, self.start_y = x_norm, y_norm
                    else:
                        self.end_x, self.end_y = x_norm, y_norm

                    print(f"成功加载 {dxf_path}: 重建为 {self.dxf_points} 点, 基准点索引 {base_point_index}")
                    print(f"缩放因子: {scale_factor:.6f}, 等效半径: {equivalent_radius * scale_factor:.6f}")
                    return

            raise RuntimeError(f"未在DXF文件中找到样条曲线: {dxf_path}")

        except Exception as e:
            raise RuntimeError(f"加载DXF文件失败: {dxf_path} - {type(e).__name__}: {str(e)}")
    def calculate_top_diameter_from_alpha(self, alpha_deg):
        """根据目标侧面夹角计算顶部直径"""
        top_radius = (self.bottom / 2) - (math.tan(math.radians(alpha_deg)) * self.high)
        return 2 * top_radius

    def update_parameters(self):
        """更新所有依赖于twist、sign和amp的参数"""
        self.update_psi()

    def update_psi(self):
        """更新psi值，根据选择的扭转类型"""
        t_length = 2 * np.pi * self.n_turns
        shift0to1 = -0.5

        if self.twist_type == 'linear':
            self.psi = np.linspace(-shift0to1 * self._twist * t_length,
                                   (1 - shift0to1) * self._twist * t_length,
                                   self.num_t)
        elif self.twist_type == 'exponential':
            t_normalized = np.linspace(0, 1, self.num_t)
            exponential_growth = np.power(2, 3 * t_normalized) - 1
            exponential_normalized = exponential_growth / (np.power(2, 3) - 1)
            base_angle = -shift0to1 * self._twist * t_length
            total_range = self._twist * t_length
            self.psi = base_angle + exponential_normalized * total_range
        else:
            raise ValueError(f"未知的扭转类型: {self.twist_type}")

    def rotation_matrix_around_vector(self, v, psi):
        """根据任意单位向量 v 和旋转角度 psi 生成旋转矩阵"""
        # 使用JIT优化版本
        return rotation_matrix_around_vector_jit(v, psi)

    def calculate_spiral_parameters(self):
        """计算指数螺旋的参数"""
        R_top = self.top / 2
        R_bottom = self.bottom / 2

        if R_top > 0:
            self.b = math.log(R_bottom / R_top)
        else:
            self.b = 0

        print(f"指数螺旋参数: 顶部半径={R_top}, 底部半径={R_bottom}, 指数因子 b={self.b:.4f}")

    def calculate_spiral_coords(self):
        """计算非线性螺旋线的坐标"""
        R_top = self.top / 2
        R = R_top * np.exp(self.b * self.t_param)
        theta = 2 * np.pi * self.n_turns * self.t_param

        x = R * np.sin(theta) * self.r
        y = R * np.cos(theta)

        if abs(self.b) > 1e-6:
            z = self.high * (np.exp(self.b * self.t_param) - 1) / (np.exp(self.b) - 1)
        else:
            z = self.t_param * self.high

        self.R = R
        return x, y, z

    def analyze_spiral_properties(self):
        """分析螺旋线的特性"""
        x, y, z = self.calculate_spiral_coords()
        dx, dy, dz = np.diff(x), np.diff(y), np.diff(z)
        distances = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        dR = np.diff(self.R)

        actual_height = z[-1] - z[0]
        actual_radius_diff = self.R[-1] - self.R[0]

        if actual_height > 0:
            actual_side_angle_deg = math.degrees(math.atan(actual_radius_diff / actual_height))
            actual_apex_angle_deg = 2 * actual_side_angle_deg

            print(f"实际几何参数: 底部直径={2 * self.R[-1]:.2f}, 顶部直径={2 * self.R[0]:.2f}")
            print(
                f"高度={actual_height:.2f}, 侧面夹角={actual_side_angle_deg:.2f}°, 锥顶角={actual_apex_angle_deg:.2f}°")

        print(f"螺旋线特性: 总长度={np.sum(distances):.2f}, 平均间距={np.mean(distances):.4f}")
        print(f"半径变化范围: {self.R[0]:.2f} -> {self.R[-1]:.2f}")

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
        """生成两条螺旋轨道线"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()
        dx, dy, dz = np.gradient(x_spiral, self.t_param), np.gradient(y_spiral, self.t_param), np.gradient(z_spiral,
                                                                                                           self.t_param)
        ddx, ddy, ddz = np.gradient(dx, self.t_param), np.gradient(dy, self.t_param), np.gradient(dz, self.t_param)

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

        center_points = np.column_stack((x_spiral, y_spiral, z_spiral))
        return center_points, [T_unit, N_unit, B_unit]

    def sweep_section(self):
        """使用断面插值扫掠方法生成扫掠曲面"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        guide_lines = {}
        swept_sections = []

        # 确保断面点数相同
        min_points = min(len(self.end_x), len(self.start_x))
        end_x, end_y = self.end_x[:min_points], self.end_y[:min_points]
        start_x, start_y = self.start_x[:min_points], self.start_y[:min_points]

        # 初始化导轨线
        for j in range(1, min_points):
            guide_lines[j] = []

        # 使用并行处理加速
        if self.use_parallel and min_points > 10:
            print(f"使用并行处理，CPU核心数: {cpu_count()}")
            start_time = time.time()

            with Pool(processes=cpu_count()) as pool:
                results = []

                for i in range(self.num_t):
                    t = i / (self.num_t - 1)
                    x_blend = (1 - t) * start_x + t * end_x
                    y_blend = (1 - t) * start_y + t * end_y

                    # 并行处理每个点
                    results.append(pool.apply_async(self._process_section_point,
                                                    (i, center_points[i], T_unit[i], N_unit[i], B_unit[i],
                                                     x_blend, y_blend, self.psi[i], self.exp_wave(i), self.a[i])))

                # 收集结果
                for i, result in enumerate(results):
                    section_points, guide_updates = result.get()

                    # 更新导轨线
                    for j, point in guide_updates:
                        if j in guide_lines:
                            guide_lines[j].append(point)

                    # 保存断面
                    if not np.allclose(section_points[0], section_points[-1]):
                        section_points.append(section_points[0])

                    if i == 0 or (i + 1) % sections_mod_n == 0:
                        swept_sections.append(section_points)

            end_time = time.time()
            print(f"并行处理完成，耗时: {end_time - start_time:.2f}秒")
        else:
            # 串行处理
            start_time = time.time()
            for i in range(self.num_t):
                t = i / (self.num_t - 1)
                x_blend = (1 - t) * start_x + t * end_x
                y_blend = (1 - t) * start_y + t * end_y
                section_points = []

                for j in range(len(x_blend)):
                    R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i]) * self.exp_wave(i)
                    B_term1 = self.sign * x_blend[j] * B_unit[i]
                    N_term1 = self.sign * y_blend[j] * N_unit[i]
                    vector = np.dot(R_theta, (N_term1 + B_term1))
                    global_point = center_points[i] + self.a[i] * vector
                    section_points.append(global_point.tolist())

                    if j >= 1:
                        guide_lines[j].append(global_point.tolist())

                if not np.allclose(section_points[0], section_points[-1]):
                    section_points.append(section_points[0])

                if i == 0 or (i + 1) % sections_mod_n == 0:
                    swept_sections.append(section_points)

            end_time = time.time()
            print(f"串行处理完成，耗时: {end_time - start_time:.2f}秒")

        return swept_sections, center_points.tolist(), guide_lines

    def _process_section_point(self, i, center_point, T_vec, N_vec, B_vec, x_blend, y_blend, psi_val, exp_wave_val,
                               a_val):
        """处理单个断面点的辅助函数（用于并行处理）"""
        section_points = []
        guide_updates = []

        for j in range(len(x_blend)):
            R_theta = self.rotation_matrix_around_vector(T_vec, psi_val) * exp_wave_val
            B_term1 = self.sign * x_blend[j] * B_vec
            N_term1 = self.sign * y_blend[j] * N_vec
            vector = np.dot(R_theta, (N_term1 + B_term1))
            global_point = center_point + a_val * vector
            section_points.append(global_point.tolist())

            if j >= 1:
                guide_updates.append((j, global_point.tolist()))

        return section_points, guide_updates

    def _precompute_exp_wave(self):
        """预计算exp_wave的值 - 15波段余弦波形"""
        print("开始预计算exp_wave波形...")
        start_time = time.time()

        def objective(k):
            t_samples = np.linspace(0, self.n_turns * 2 * np.pi, 100000)
            freq = np.power(2, k * t_samples) / (2 * np.pi)
            phase = np.trapezoid(freq, t_samples)
            return abs(phase - self.bands+0.1)

        res = minimize(objective, x0=0.1, bounds=[(0.001, 1)])
        k = res.x[0]
        t_normalized = self.t_param

        freq = np.power(2, k * t_normalized * (self.n_turns * 2 * np.pi)) / (2 * np.pi)
        phase = np.cumsum(freq) * (t_normalized[1] - t_normalized[0]) * (self.n_turns * 2 * np.pi)
        phase_normalized = phase % 1
        y = np.zeros_like(t_normalized)

        for i in range(len(t_normalized)):
            if i > 0 and phase_normalized[i] < phase_normalized[i - 1] - 0.5:
                y[i] = phi_squared
            else:
                t_val = phase_normalized[i]
                y[i] = 1 + (phi_squared - 1) * 0.5 * (1 + np.cos(np.pi * t_val))

        if self.amp_nonlinear:
            amplitude = np.power(phi, t_normalized * self.n_turns)
        else:
            amplitude = np.ones_like(t_normalized)

        self.exp_wave_values = amplitude * y * self.global_a
        actual_bands = phase[-1] - phase[0]

        end_time = time.time()
        print(f"波形预计算完成，耗时: {end_time - start_time:.2f}秒")
        print(f"计算得到的k值: {k:.6f}, 目标波段数: 15, 实际波段数: {actual_bands:.2f}")

        # self._plot_waveform(t_normalized, y, actual_bands)

    def _plot_waveform(self, t, y, actual_bands):
        """绘制波形图"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(t, y, 'b-', linewidth=1.5, label=f'Waveform ({actual_bands:.1f} bands)')
            ax.set_title('Combined exp_wave Waveform', fontsize=14)
            ax.set_xlabel('Normalized Time (0-1)', fontsize=12)
            ax.set_ylabel('Amplitude', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7)

            # 检测跳变点
            jump_points = []
            for i in range(1, len(t)):
                if i > 0 and (y[i] > y[i - 1] + 0.5 or (y[i] > 2.0 and y[i - 1] < 1.5)):
                    jump_points.append(i)
                    ax.plot(t[i], y[i], 'ro', markersize=5)

            if jump_points:
                ax.legend(['Waveform', 'Jump points'], loc='upper right')
            else:
                ax.legend(['Waveform'], loc='upper right')

            stats_text = (f"Target bands: 15\nActual bands: {actual_bands:.1f}\n"
                          f"Min amplitude: {min(y):.3f}\nMax amplitude: {max(y):.3f}")
            ax.text(0.02, 0.95, stats_text, transform=ax.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            ax.axhline(y=2.618, color='r', linestyle='--', alpha=0.5, label='φ² (2.618)')
            ax.axhline(y=1.0, color='g', linestyle='--', alpha=0.5, label='Min (1.0)')
            plt.savefig('combined_exp_wave_waveform.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("Waveform plot saved as 'combined_exp_wave_waveform.png'")

        except ImportError:
            print("Warning: matplotlib not installed, skipping waveform plot")
        except Exception as e:
            print(f"Error generating waveform plot: {str(e)}")

    def exp_wave(self, t_index):
        return self.exp_wave_values[t_index]

    def segment_egghead_points_by_jump(self, points):
        """根据锯齿波跳变点分割点曲线，并在段间添加混接曲线"""
        segments = []  # 存储分割后的点段
        current_segment = [points[0]]
        jump_points = []  # 存储混接曲线中的B6点

        # 使用预计算的波形值检测跳变点
        amp_scale = np.percentile(np.abs(self.exp_wave_values), 95)
        jump_threshold = 0.5 * amp_scale

        # 首先对曲线进行离散化处理
        discrete_points = []
        for i in range(len(points) - 1):
            discrete_points.append(points[i])

            prev_wave = self.exp_wave_values[i]
            next_wave = self.exp_wave_values[i + 1]

            if abs(prev_wave - next_wave) > jump_threshold:
                discrete_points.append(None)  # 标记跳变点

        discrete_points.append(points[-1])

        # 根据离散点创建分段
        for point in discrete_points:
            if point is None:  # 跳变点
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
            else:
                current_segment.append(point)

        if current_segment:
            segments.append(current_segment)

        # 在相邻段之间添加混接曲线
        blended_segments = []
        for i in range(len(segments)):
            blended_segments.append(segments[i])

            if i < len(segments) - 1:
                prev_seg = segments[i]
                next_seg = segments[i + 1]

                # 确保有足够的点计算曲率变化率
                if len(prev_seg) >= 4 and len(next_seg) >= 5:
                    # 获取前一段的最后四个点
                    p_prev2 = prev_seg[-3]  # 倒数第三个点
                    p_prev = prev_seg[-2]  # 倒数第二个点
                    p0 = prev_seg[-1]  # 最后一个点

                    # 获取后一段的前五个点
                    p1 = next_seg[0]  # 第一个点
                    p2 = next_seg[1]  # 第二个点
                    p3 = next_seg[2]  # 第三个点
                    p4 = next_seg[3]  # 第四个点（用于曲率变化率）

                    # 创建G4-G4混接曲线
                    blend_points, B6_point = self.create_g4_g4_blend_curve(
                        p_prev2, p_prev, p0, p1, p2, p3, p4
                    )
                    blended_segments.append(blend_points)

                    # 收集混接曲线中的B6点
                    jump_points.append(B6_point)
                    # print(f"在段{i}和{i + 1}之间添加了G4混接曲线，包含{len(blend_points)}个点")
                else:
                    print(f"警告: 段{i}或{i + 1}点数不足，无法创建G4混接曲线")
                    # 添加简单线性过渡作为后备方案
                    blend_points = [segments[i][-1], segments[i + 1][0]]
                    blended_segments.append(blend_points)

        print(f"点曲线被分成 {len(blended_segments)} 段")
        print(f"收集到 {len(jump_points)} 个B6跳变点")
        return blended_segments, jump_points  # 返回分段和跳变点列表

    def create_g4_g4_blend_curve(self, p_prev2, p_prev, p0, p1, p2, p3, p4):
        """优化后的混接曲线生成函数，使用8次贝塞尔曲线，返回曲线点和B6点"""
        # 将点转换为NumPy数组
        p_prev2 = np.array(p_prev2)
        p_prev = np.array(p_prev)
        p0 = np.array(p0)  # s点
        p1 = np.array(p1)  # e点
        p2 = np.array(p2)
        p3 = np.array(p3)
        p4 = np.array(p4)

        # 计算前一段在p0处的导数
        tangent_in = p0 - p_prev  # 一阶导数（切向量）
        curvature_in = (p_prev - 2 * p_prev2 + p0)  # 二阶导数（曲率向量）

        # 计算后一段在p1处的导数
        tangent_out = p2 - p1  # 一阶导数（切向量）
        curvature_out = (p3 - 2 * p2 + p1)  # 二阶导数（曲率向量）

        # 归一化向量（防止零除）
        tangent_in = tangent_in / (np.linalg.norm(tangent_in) + 1e-6)
        tangent_out = tangent_out / (np.linalg.norm(tangent_out) + 1e-6)

        # 使用8次贝塞尔曲线（9个控制点）
        dist = np.linalg.norm(p1 - p0)
        n = 8  # 贝塞尔曲线阶数

        # 基础控制点计算（满足G3连续性条件）
        B0 = p0  # 起点
        B1 = p0 + tangent_in * 0.2 * dist
        B2 = p0 + tangent_in * 0.4 * dist + curvature_in * 0.1 * dist
        B3 = p0 + tangent_in * 0.6 * dist + curvature_in * 0.2 * dist

        B8 = p1  # 终点
        B7 = p1 - tangent_out * 0.2 * dist
        B6 = p1 - tangent_out * 0.4 * dist + curvature_out * 0.1 * dist
        B5 = p1 - tangent_out * 0.6 * dist + curvature_out * 0.2 * dist

        # 直接使用中点作为B4（简化处理）
        B4 = (B3 + B5) / 2

        # 最终控制点
        control_points = [B0, B1, B2, B3, B4, B5, B6, B7, B8]

        # 生成8次贝塞尔曲线点 - 使用JIT优化版本
        curve_points = bezier_curve_points_jit(np.array(control_points), 20)

        # 返回曲线点和B6点
        return curve_points, B4.tolist()
    def save_to_dxf(self, filename):
        """保存到DXF文件，为每个点生成独立的导轨线，并添加扫掠断面和所有跳变点"""
        # 定义颜色方案
        colors = {
            'sections': 3,  # 绿色 - 扫掠断面
            'axis': 7,  # 黑色 - 中心轴
            'end_section_lines': 1,
            'jump_points': 6
        }
        # 定义排除的颜色（使用集合提高查找效率）
        excluded_colors = {3, 7, 1, 6}
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, guide_lines = self.sweep_section()

        # 添加中心轴（黑色）
        z_coords = [p[2] for p in center_points]
        z_axis_length = max(z_coords) - min(z_coords)
        line = msp.add_line((0, 0, -30), (0, 0, max(z_coords)+z_axis_length / 2))
        line.dxf.color = colors['axis']

        # 添加所有扫掠断面（绿色）
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        # 预生成可用颜色列表（排除特定颜色）
        available_colors = [i for i in range(1, 256) if i not in excluded_colors]
        all_jump_points = []
        # 为每条导轨线添加独立的图层和颜色
        for j, points in enumerate(guide_lines.values()):
            # 创建图层
            layer_name = f"guide_{j}"
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name)

            # 从可用颜色中选择颜色（循环使用）
            color_index = available_colors[j % len(available_colors)]
            # 收集所有跳变点

            # 对导轨线进行分段处理并收集跳变点
            segments, jump_points = self.segment_egghead_points_by_jump(points)
            if j % 2 == 1:
                all_jump_points.extend(jump_points)  # 添加奇数点到总跳变点列表

            for seg_idx, seg in enumerate(segments):
                if len(seg) >= 2:
                    spline = msp.add_spline(seg)
                    spline.dxf.layer = layer_name
                    spline.dxf.color = color_index
                elif len(seg) == 1:
                    point = msp.add_point(seg[0])
                    point.dxf.layer = layer_name
                    point.dxf.color = color_index

        # 添加特定位置的投影线（n_turns=0, 0.5, 1.5, 2）
        # 计算每个位置对应的索引
        target_turns = [0, 0.5, 1.5, 2,2.5]

        # 为每个目标位置添加投影线
        for turn in target_turns:
            # 计算该圈数对应的t值
            t_val = turn / self.n_turns
            # 计算对应的索引
            idx = int(t_val * (self.num_t - 1))

            # 获取该索引对应的扫掠断面
            section_idx = idx // sections_mod_n  # 假设每sections_mod_n个点保存一个断面

            # 获取目标位置前后断面
            start_idx = max(0, section_idx - 1)  # 前1个断面
            end_idx = min(len(swept_sections), section_idx + 2)

            # 为每个断面添加投影线
            for i in range(start_idx, end_idx):
                if i < len(swept_sections):
                    section = swept_sections[i]
                    # 找到该断面上距离z轴最近的点
                    min_point = min(section, key=lambda p: np.sqrt(p[0] ** 2 + p[1] ** 2))
                    proj_point = [0, 0, min_point[2]]
                    line = msp.add_line(min_point, proj_point)
                    line.dxf.color = colors['end_section_lines']

        # 添加所有跳变点（红色）
        if all_jump_points:
            # 创建跳变点图层
            if "jump_points" not in doc.layers:
                doc.layers.new(name="jump_points")

            # 添加所有跳变点
            for point in all_jump_points:
                msp.add_point(point, dxfattribs={
                    'layer': "jump_points",
                    'color': colors['jump_points']
                })

            print(f"添加了 {len(all_jump_points)} 个跳变点到DXF文件")

        doc.saveas(filename)
        print(f"成功保存所有导轨线、扫掠断面和跳变点到 {filename}")


if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    print("当psi越来越大，则是顺时针旋转；若是越来越小 → 则是逆时针旋转")
    new_bottom, new_h, new_amp = 160, 240, 2.5
    target_side_angle_deg = 13.282525  # 用户要求的侧面夹角 11.75°是基于地磁偏角

    # 定义不同的bands值
    bands_list = [17, 23, 19, 21]

    for bands_value in bands_list:
        # 使用目标侧面夹角计算top直径并创建模型
        generator_right = SpiralSweepGenerator(
            'start 舒伯格蛋咬一口曲线.dxf', 'end 舒伯格蛋咬一口曲线.dxf',
            bottom=new_bottom,
            high=new_h,
            amp=new_amp,
            alpha_deg=target_side_angle_deg,  # 添加目标侧面夹角参数
            dxf_points=16,  # 指定DXF曲线重建点数
            twist_type='exponential',  # linear线性扭转，exponential非线性扭转
            use_parallel=True,  # 启用并行处理
            bands=bands_value  # 使用不同的bands值
        )

        # 设置其他参数并生成dxf文件
        generator_right.sign = 1  # 管旋转180
        generator_right.r = -1
        generator_right.twist = twist_angle

        # 分析螺旋特性
        generator_right.analyze_spiral_properties()

        # 保存到DXF文件
        generator_right.save_to_dxf(f'波纹螺旋锥管_滑滑梯_多规扫掠{bands_value}段波.dxf')

        print(f"已生成 {bands_value} 段波的文件")