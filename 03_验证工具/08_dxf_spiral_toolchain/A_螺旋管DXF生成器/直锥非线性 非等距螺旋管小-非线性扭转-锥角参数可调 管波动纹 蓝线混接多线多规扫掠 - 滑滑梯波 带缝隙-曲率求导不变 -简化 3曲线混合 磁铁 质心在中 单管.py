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
silver_ratio=np.sqrt(2)
multiple=phi
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
    def __init__(self, start_dxf_path, end_dxf_path, bottom=300, high=300, n_turns=1.5,
                 sign_spiral_dir=1, sign=1, twist=1, amp=1, alpha_deg=11, global_a=1, collect_n=50,
                 amp_nonlinear=False, dxf_points=19, twist_type='linear', bands=15, use_parallel=True,
                 phase_dif=0, k=0.2):
        """初始化螺旋扫掠生成器 - 简化版本，去除middle断面"""
        # 固定参数设置
        self.bands = 15  # 固定为15波段
        self.phase_dif = 0  # 固定相位差为0

        # 其他初始化代码保持不变...
        self.amp_nonlinear = amp_nonlinear
        self.bottom = bottom * global_a
        self.high = high * global_a
        self.n_turns = n_turns
        self.num_t = 945
        self.t_param = np.linspace(0, 1, self.num_t)
        self.r = sign_spiral_dir
        self._twist = twist
        self.twist_type = twist_type
        self._sign = sign
        self.dxf_points = dxf_points
        self.alpha_deg = alpha_deg
        self.amp_initial = amp
        self.a = np.linspace(1, phi_small, self.num_t)
        self.collect_n = collect_n
        self.global_a = global_a
        self.jump_points = []
        self.use_parallel = use_parallel
        self.k = k
        # 移除middle_turn参数

        # 计算顶部直径
        self.top = self.calculate_top_diameter_from_alpha(self.alpha_deg)

        # 计算指数螺旋参数
        self.calculate_spiral_parameters()

        # 直接从DXF文件加载两个断面数据（去除middle断面）
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
        theta = 2 * np.pi * self.n_turns * self.t_param + self.phase_dif  # 添加相位差

        x = R * np.sin(theta) * self.r
        y = R * np.cos(theta)

        # 修改 z 的计算公式，使其与 R 形成相乘为 1 的关系
        if abs(self.b) > 1e-6:
            # 原来的公式：z = self.high * (np.exp(self.b * self.t_param) - 1) / (np.exp(self.b) - 1)
            # 修改为与 R 形成互逆关系
            z = self.high * (1 - np.exp(-self.b * self.t_param)) / (1 - np.exp(-self.b))
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

    def load_section_from_dxf(self, dxf_path, section_type):
        """从DXF文件加载断面数据并进行归一化和缩放"""
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # 查找第一条SPLINE
            for entity in msp:
                if entity.dxftype() == 'SPLINE':
                    spline_tool = entity.construction_tool()
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
                    elif section_type == 'middle':
                        self.middle_x, self.middle_y = x_norm, y_norm
                    else:
                        self.end_x, self.end_y = x_norm, y_norm

                    print(f"成功加载 {dxf_path}: 重建为 {self.dxf_points} 点, 基准点索引 {base_point_index}")
                    print(f"缩放因子: {scale_factor:.6f}, 等效半径: {equivalent_radius * scale_factor:.6f}")
                    return

            raise RuntimeError(f"未在DXF文件中找到样条曲线: {dxf_path}")

        except Exception as e:
            raise RuntimeError(f"加载DXF文件失败: {dxf_path} - {type(e).__name__}: {str(e)}")


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
            t_samples = np.linspace(0, self.n_turns * 2 * np.pi, 10000)
            freq = np.power(np.sqrt(2), k * t_samples) / (2 * np.pi)
            phase = np.trapezoid(freq, t_samples)
            return abs(phase - self.bands+0.1)  #若+0.1出水口就是窄口

        res = minimize(objective, x0=0.1, bounds=[(0.001, 1)])
        self.k = res.x[0]
        t_normalized = self.t_param

        freq = np.power(np.sqrt(2), self.k * t_normalized * (self.n_turns * 2 * np.pi)) / (2 * np.pi)
        phase = np.cumsum(freq) * (t_normalized[1] - t_normalized[0]) * (self.n_turns * 2 * np.pi)
        phase_normalized = phase % 1
        y = np.zeros_like(t_normalized)

        # 检测跳变点并找到最后一段band的起点位置
        band_starts = []
        for i in range(len(t_normalized)):
            if i > 0 and phase_normalized[i] < phase_normalized[i - 1] - 0.5:
                y[i] = multiple
                # 记录跳变点（band结束点）
                if i < len(t_normalized) - 1:
                    # 下一个点就是新band的起点
                    band_starts.append(i + 1)
            else:
                t_val = phase_normalized[i]
                y[i] = 1 + (multiple - 1) * 0.5 * (1 + np.cos(np.pi * t_val))

        # 设置middle_turn为最后一段band的起点位置
        if band_starts:
            last_band_start_index = band_starts[-1]
            last_band_start_t = t_normalized[last_band_start_index]
            self.middle_turn = last_band_start_t * self.n_turns
            print(f"自动设置middle_turn为最后一段band的起点位置: {self.middle_turn:.4f}")
        else:
            print("警告: 未检测到band起点，使用默认middle_turn值")

        if self.amp_nonlinear:
            amplitude = np.power(phi, t_normalized * self.n_turns)
        else:
            amplitude = np.ones_like(t_normalized)

        self.exp_wave_values = amplitude * y * self.global_a
        actual_bands = phase[-1] - phase[0]

        end_time = time.time()
        print(f"波形预计算完成，耗时: {end_time - start_time:.2f}秒")
        print(f"计算得到的k值: {self.k:.6f}, 目标波段数: 15, 实际波段数: {actual_bands:.2f}")

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
        """根据锯齿波跳变点分割点曲线，并在段间添加混接曲线（最后一个跳变不需要混接）"""
        segments = []  # 存储分割后的点段
        current_segment = [points[0]]
        jump_points = []  # 存储混接曲线中的B4点和最后一点

        # 使用预计算的波形值检测跳变点
        amp_scale = np.percentile(np.abs(self.exp_wave_values), 95)
        jump_threshold = 0.5 * amp_scale

        # 首先对曲线进行离散化处理
        discrete_points = []
        for i in range(len(points) - 1):
            discrete_points.append(points[i])

            prev_wave = self.exp_wave_values[i]
            next_wave = self.exp_wave_values[i + 1]

            # 跳过最后一个跳变点（不在最后一个跳变点处分段）
            if abs(prev_wave - next_wave) > jump_threshold and i < len(points) - 2:
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

        # 在相邻段之间添加混接曲线（跳过最后一段之后的混接）
        blended_segments = []
        for i in range(len(segments)):
            blended_segments.append(segments[i])

            # 跳过最后一段之后的混接
            if i < len(segments) - 1:  # 修改这里，确保不会在最后一段后添加混接
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
                    blend_points, B4_point = self.create_g4_g4_blend_curve(
                        p_prev2, p_prev, p0, p1, p2, p3, p4
                    )
                    blended_segments.append(blend_points)

                    # 收集混接曲线中的B4点
                    jump_points.append(B4_point)
                else:
                    print(f"警告: 段{i}或{i + 1}点数不足，无法创建G4混接曲线")
                    # 添加简单线性过渡作为后备方案
                    blend_points = [segments[i][-1], segments[i + 1][0]]
                    blended_segments.append(blend_points)
                    # 收集线性过渡的起点
                    jump_points.append(segments[i][-1])

        # # 添加最后一段的最后一点到跳变点列表
        # if segments and segments[-1]:
        #     last_point = segments[-1][-1]
        #     jump_points.append(last_point)

        print(f"点曲线被分成 {len(blended_segments)} 段")
        print(f"收集到 {len(jump_points)} 个跳变点")
        return blended_segments, jump_points  # 返回分段和跳变点列表

    def create_g4_g4_blend_curve(self, p_prev2, p_prev, p0, p1, p2, p3, p4):
        """优化后的混接曲线生成函数，使用等比序列优化控制点系数"""
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

        # 使用等比序列优化控制点系数
        # 创建一个等比序列，从较小的值开始，逐渐增加
        geometric_sequence = [phi_small * (3/4)**(3 - i) for i in range(4)] # 等比序列最大为phi_small

        # 基础控制点计算（满足G3连续性条件）
        B0 = p0  # 起点
        B1 = p0 + tangent_in * geometric_sequence[0] * dist
        B2 = p0 + tangent_in * geometric_sequence[1] * dist + curvature_in * geometric_sequence[0] * 0.5 * dist
        B3 = p0 + tangent_in * geometric_sequence[2] * dist + curvature_in * geometric_sequence[1] * 0.5 * dist

        B8 = p1  # 终点
        B7 = p1 - tangent_out * geometric_sequence[0] * dist
        B6 = p1 - tangent_out * geometric_sequence[1] * dist + curvature_out * geometric_sequence[0] * 0.5 * dist
        B5 = p1 - tangent_out * geometric_sequence[2] * dist + curvature_out * geometric_sequence[1] * 0.5 * dist

        # 使用等比序列的最后一个值确定中点B4
        B4 = B3 + (B5 - B3) * geometric_sequence[3]

        # 最终控制点
        control_points = [B0, B1, B2, B3, B4, B5, B6, B7, B8]

        # 生成8次贝塞尔曲线点 - 使用JIT优化版本
        curve_points = bezier_curve_points_jit(np.array(control_points), 20)

        # 返回曲线点和B4点
        return curve_points, B4.tolist()


    def sweep_section(self):
        """使用断面插值扫掠方法生成扫掠曲面，只使用start和end两个断面"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        guide_lines = {}
        swept_sections = []
        last_center_points = []  # 初始化 last_center_points 列表

        # 确保两个断面点数相同
        min_points = min(len(self.start_x), len(self.end_x))
        start_x, start_y = self.start_x[:min_points], self.start_y[:min_points]
        end_x, end_y = self.end_x[:min_points], self.end_y[:min_points]

        # 初始化导轨线
        for j in range(1, min_points):
            guide_lines[j] = []

        # 预计算非线性混合系数
        t_normalized = np.linspace(0, 1, self.num_t)

        # 使用指数变化的频率计算混合系数
        freq = np.power(np.sqrt(2), self.k * t_normalized)
        # 归一化频率到[0,1]范围
        min_freq, max_freq = np.min(freq), np.max(freq)
        blend_factors = (freq - min_freq) / (max_freq - min_freq)

        # 使用并行处理加速
        if self.use_parallel and min_points > 10:
            print(f"使用并行处理，CPU核心数: {cpu_count()}")
            start_time = time.time()

            with Pool(processes=cpu_count()) as pool:
                results = []

                for i in range(self.num_t):
                    # 直接使用混合系数从起始断面到结束断面
                    t_blend = blend_factors[i]
                    x_blend = (1 - t_blend) * start_x + t_blend * end_x
                    y_blend = (1 - t_blend) * start_y + t_blend * end_y

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

            # 添加 center_points[-1] 到 last_center_points
            last_center_points.append(center_points[-1].tolist())

            end_time = time.time()
            print(f"并行处理完成，耗时: {end_time - start_time:.2f}秒")
        else:
            # 串行处理
            start_time = time.time()
            for i in range(self.num_t):
                # 直接使用混合系数从起始断面到结束断面
                t_blend = blend_factors[i]
                x_blend = (1 - t_blend) * start_x + t_blend * end_x
                y_blend = (1 - t_blend) * start_y + t_blend * end_y

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

            # 添加 center_points[-1] 到 last_center_points
            last_center_points.append(center_points[-1].tolist())

            end_time = time.time()
            print(f"串行处理完成，耗时: {end_time - start_time:.2f}秒")

        return swept_sections, center_points.tolist(), guide_lines, last_center_points

    def save_to_dxf(self, filename, bands_list=None):
        """简化版保存函数，去除middle断面相关代码"""
        # 定义颜色方案
        colors = {
            'sections': 3,  # 绿色 - 扫掠断面
            'axis': 8,  # 黑色 - 中心轴
            'end_section_lines': 1,
            'new_end_section_lines': 9,  # 灰色 - 新增的投影线类型
            'jump_points': 6,
            'circles': 4,  # 青色 - 同心圆
            'last_center_points': 5  # 蓝色 - 最后中心点
        }

        # 定义排除的颜色
        excluded_colors = {3, 8, 9, 1, 6, 4, 2, 5}
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()
        inner_dia = 5.3
        thickness = 1.2
        outer_dia = inner_dia + thickness * 2
        outer_radius = outer_dia / 2

        # 生成并添加所有曲线
        swept_sections, center_points, guide_lines, last_center_points = self.sweep_section()

        # 重新生成螺旋曲线以获取T_unit, N_unit, B_unit
        _, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        target_turns = np.arange(0, self.n_turns + 0.5, 0.5)
        find_z_min = float('inf')

        # 为每个目标位置添加投影线
        n_points = 36
        half_points = n_points // 2
        toward_in = 1

        for i, turn in enumerate(target_turns):
            t_val = turn / self.n_turns
            idx = int(t_val * (self.num_t - 1))

            indices = []
            for offset in range(-half_points, half_points + 1):
                current_idx = idx + offset
                if 0 <= current_idx < len(center_points):
                    indices.append(current_idx)

            avg_position = np.zeros(3)
            for j in indices:
                avg_position += np.array(center_points[j])
            avg_position /= len(indices)

            radial_direction = np.array([-avg_position[0], -avg_position[1], 0])
            if np.linalg.norm(radial_direction) > 1e-6:
                radial_direction = radial_direction / np.linalg.norm(radial_direction)
            else:
                radial_direction = np.array([1, 0, 0])

            perpendicular = np.array([-radial_direction[1], radial_direction[0], 0])

            avg_tangent = np.zeros(3)
            for j in indices:
                if 0 <= j < len(T_unit):
                    avg_tangent += T_unit[j]

            if np.linalg.norm(avg_tangent) > 1e-6:
                avg_tangent = avg_tangent / np.linalg.norm(avg_tangent)
                tangent_xy = np.array([avg_tangent[0], avg_tangent[1], 0])
                if np.linalg.norm(tangent_xy) > 1e-6:
                    tangent_xy = tangent_xy / np.linalg.norm(tangent_xy)
                    dot_product = np.dot(perpendicular, tangent_xy)
                    if dot_product < 0:
                        perpendicular = -perpendicular

            positions = np.linspace(-outer_radius + toward_in, outer_radius - toward_in, len(indices))

            for k, j in enumerate(indices):
                center_point = center_points[j]
                projection_length = math.sqrt(center_point[0] ** 2 + center_point[1] ** 2)

                # 原始投影线
                proj_point_original = [
                    positions[k] * perpendicular[0],
                    positions[k] * perpendicular[1],
                    center_point[2] - projection_length
                ]
                line_original = msp.add_line(center_point, proj_point_original)
                line_original.dxf.color = colors['end_section_lines']

                # 新增投影线
                proj_point_new = [
                    positions[k] * perpendicular[0],
                    positions[k] * perpendicular[1],
                    center_point[2]
                ]
                line_new = msp.add_line(center_point, proj_point_new)
                line_new.dxf.color = colors['new_end_section_lines']

                if i != len(target_turns) - 1 and center_point[2] < find_z_min:
                    find_z_min = center_point[2]

        # 总是添加中心轴和同心圆（因为现在只生成一个文件）
        z_coords = [p[2] for p in center_points]
        z_max = max(z_coords)
        line = msp.add_line((0, 0, find_z_min), (0, 0, z_max + 6))
        line.dxf.color = colors['axis']

        circle_center = (0, 0, find_z_min)
        circle_outer = msp.add_circle(circle_center, outer_radius)
        circle_outer.dxf.color = colors['circles']

        circle_inner = msp.add_circle(circle_center, inner_dia / 2)
        circle_inner.dxf.color = colors['circles']

        # 导轨线处理
        available_colors = [i for i in range(1, 256) if i not in excluded_colors]
        all_jump_points = []

        for j, points in enumerate(guide_lines.values()):
            layer_name = f"guide_{j}"
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name)

            color_index = available_colors[j % len(available_colors)]
            segments, jump_points = self.segment_egghead_points_by_jump(points)

            if j % 2 == 1 and j != 17:
                all_jump_points.extend(jump_points)

            for seg in segments:
                if len(seg) >= 2:
                    spline = msp.add_spline(seg)
                    spline.dxf.layer = layer_name
                    spline.dxf.color = color_index
                elif len(seg) == 1:
                    point = msp.add_point(seg[0])
                    point.dxf.layer = layer_name
                    point.dxf.color = color_index

        # 添加扫掠断面
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        # 添加跳变点
        if all_jump_points:
            if "jump_points" not in doc.layers:
                doc.layers.new(name="jump_points")

            for point in all_jump_points:
                msp.add_point(point, dxfattribs={
                    'layer': "jump_points",
                    'color': colors['jump_points']
                })

        # 添加最后中心点
        if last_center_points:
            if "last_center_points" not in doc.layers:
                doc.layers.new(name="last_center_points")

            for point in last_center_points:
                msp.add_point(point, dxfattribs={
                    'layer': "last_center_points",
                    'color': colors['last_center_points']
                })

        doc.saveas(filename)
        print(f"成功保存15波段波纹螺旋锥管到 {filename}")

# 主程序也需要相应修改
if __name__ == "__main__":
    # 简化主程序，只使用两个断面文件
    curve_generator = SpiralSweepGenerator(
        'start 舒伯格蛋咬一口曲线.dxf', 'end 舒伯格蛋咬一口曲线.dxf',
        bottom=61,
        high=61 * silver_ratio,
        amp=4,
        alpha_deg=6.7315,
        dxf_points=19,
        twist_type='linear',
        use_parallel=False,
        bands=15,  # 固定为15
        phase_dif=0,  # 固定为0
    )

    curve_generator.sign = 1
    curve_generator.r = -1
    curve_generator.twist = twist_angle

    curve_generator.analyze_spiral_properties()
    curve_generator.save_to_dxf('波纹螺旋锥管_15段波.dxf')

    print("已生成15段波文件")