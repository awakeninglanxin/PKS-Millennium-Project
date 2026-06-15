import numpy as np
import ezdxf
import math
from scipy.optimize import minimize
from scipy.interpolate import splprep, splev
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
phi = (np.sqrt(5) + 1) / 2
phi_small = (np.sqrt(5) - 1) / 2
phi_squared = phi**2
# 计算φ的三次方
phi_cubic = phi ** 3  # 添加这行计算φ的三次方
sections_mod_n=21
twist_angle=1/phi_squared #137.5°
class SpiralSweepGenerator:
    def __init__(self, start_dxf_path, end_dxf_path, bottom=300, high=300, n_turns=2, sign_spiral_dir=1,
                 sign=1, twist=1, amp=1, alpha_deg=11,global_a=1, collect_n=50, amp_nonlinear=False, dxf_points=16,
                 twist_type='linear'):
        """
        初始化螺旋扫掠生成器 - 只支持DXF文件
        增加dxf_points参数控制DXF曲线重建点数
        """
        self.amp_nonlinear = amp_nonlinear
        self.bottom = bottom*global_a
        self.high = high*global_a
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
        self.a = np.linspace(1, 1 / 3, self.num_t)
        self.collect_n = collect_n
        self.global_a = global_a

        # 计算顶部直径
        self.top = self.calculate_top_diameter_from_alpha(self.alpha_deg)

        # 计算指数螺旋参数
        self.calculate_spiral_parameters()

        # 直接从DXF文件加载断面数据
        self.load_section_from_dxf(start_dxf_path, section_type='start')
        self.load_section_from_dxf(end_dxf_path, section_type='end')

        self.update_parameters()
        self._precompute_exp_wave()  # 确保在初始化时调用预计算波形

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
                            dist = math.sqrt(x**2 + y**2)
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
        distances = np.sqrt(x**2 + y**2)

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
        """使用断面插值扫掠方法生成扫掠曲面，为每个点生成独立的导轨线"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors

        # 使用字典存储每条导轨线的点
        guide_lines = {}
        swept_sections = []  # 保留扫掠断面用于其他功能

        # 确保断面数据是NumPy数组
        if not isinstance(self.end_x, np.ndarray):
            self.end_x = np.array(self.end_x)
            self.end_y = np.array(self.end_y)
        if not isinstance(self.start_x, np.ndarray):
            self.start_x = np.array(self.start_x)
            self.start_y = np.array(self.start_y)

        # 确保两个断面点数相同
        min_points = min(len(self.end_x), len(self.start_x))
        end_x = self.end_x[:min_points]  # 此处加了负号在前代表以Y轴镜像翻了一下
        end_y = self.end_y[:min_points]
        start_x = self.start_x[:min_points]  # 此处加了负号在前代表以Y轴镜像翻了一下
        start_y = self.start_y[:min_points]

        # 初始化导轨线字典 - 从1开始而不是0
        for j in range(1, min_points):  # 从1开始而不是0
            guide_lines[j] = []  # 对应guide_lines[j]也要改

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

                # 将点添加到对应的导轨线 - 注意索引j从1开始
                if j >= 1:  # 只处理索引1及以上的点
                    guide_lines[j].append(global_point)
                section_points.append(global_point)

            # 闭合处理 - 添加第一个点作为最后一个点（仅对断面，导轨线不需要）
            if not np.allclose(section_points[0], section_points[-1]):
                section_points.append(section_points[0])

            # 仅保存部分断面以节省内存
            if i == 0 or (i + 1) % sections_mod_n == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), guide_lines

    def _precompute_exp_wave(self):
        """预计算exp_wave的值 - 15波段余弦波形"""
        # 定义目标波段数量
        target_bands = 15


        # 优化函数计算k值
        def objective(k):
            t_samples = np.linspace(0, self.n_turns * 2 * np.pi, 100000)
            freq = np.power(2, k * t_samples) / (2 * np.pi)
            phase = np.trapezoid(freq, t_samples)
            return abs(phase - target_bands + 0.1)

        # 优化求解k值
        res = minimize(objective, x0=0.1, bounds=[(0.001, 1)])
        k = res.x[0]

        # 计算时间序列
        t_normalized = self.t_param

        # 计算频率和相位
        freq = np.power(2, k * t_normalized * (self.n_turns * 2 * np.pi)) / (2 * np.pi)
        phase = np.cumsum(freq) * (t_normalized[1] - t_normalized[0]) * (self.n_turns * 2 * np.pi)
        # 归一化相位
        phase_normalized = phase % 1
        # 使用余弦函数生成波形
        y = np.zeros_like(t_normalized)

        # 生成波形
        for i in range(len(t_normalized)):
            # 检测相位跳变点
            if i > 0 and phase_normalized[i] < phase_normalized[i - 1] - 0.5:
                y[i] = phi_cubic  # 波段开始，设为φ的三次方
            else:
                # 直接使用t_val作为参数
                t_val = phase_normalized[i]

                # 余弦函数平滑下降，使用φ的三次方到1的范围
                y[i] = 1 + (phi_cubic - 1) * 0.5 * (1 + np.cos(np.pi * t_val))

        # 计算振幅
        if self.amp_nonlinear:
            amplitude = np.power(phi, t_normalized * self.n_turns)
        else:
            amplitude = np.ones_like(t_normalized)

        self.exp_wave_values = amplitude * y * self.global_a

        # 验证结果
        actual_bands = phase[-1] - phase[0]
        print(f"计算得到的k值: {k:.6f}")
        print(f"目标波段数: 15, 实际波段数: {actual_bands:.2f}")
        print(f"波形范围: {y.min():.3f} 到 {y.max():.3f}")

        # 绘制波形图
        self._plot_waveform(t_normalized, y, actual_bands)


    def _plot_waveform(self, t, y, actual_bands):
        """绘制波形图以便检查 - 避免中文字符问题"""
        try:

            # 创建图形和坐标轴
            fig, ax = plt.subplots(figsize=(12, 6))

            # 绘制波形 - 使用英文标签避免中文问题
            ax.plot(t, y, 'b-', linewidth=1.5, label=f'Waveform ({actual_bands:.1f} bands)')

            # 添加标题和标签 - 全部使用英文
            ax.set_title('Combined exp_wave Waveform (15 bands with cosine shape)', fontsize=14)
            ax.set_xlabel('Normalized Time (0-1)', fontsize=12)
            ax.set_ylabel('Amplitude', fontsize=12)

            # 添加网格
            ax.grid(True, linestyle='--', alpha=0.7)

            # 检测并标记跳变点
            jump_points = []
            for i in range(1, len(t)):
                # 检测相位跳变点
                if i > 0 and (y[i] > y[i - 1] + 0.5 or (y[i] > 2.0 and y[i - 1] < 1.5)):
                    jump_points.append(i)
                    ax.plot(t[i], y[i], 'ro', markersize=5)

            # 添加图例
            if jump_points:
                ax.legend(['Waveform', 'Jump points'], loc='upper right')
            else:
                ax.legend(['Waveform'], loc='upper right')

            # 添加波形信息注释
            stats_text = (f"Target bands: 15\n"
                          f"Actual bands: {actual_bands:.1f}\n"
                          f"Min amplitude: {min(y):.3f}\n"
                          f"Max amplitude: {max(y):.3f}\n"
                          f"Waveform shape: cosine-based")
            ax.text(0.02, 0.95, stats_text, transform=ax.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            # 添加参考线
            ax.axhline(y=2.618, color='r', linestyle='--', alpha=0.5, label='φ² (2.618)')
            ax.axhline(y=1.0, color='g', linestyle='--', alpha=0.5, label='Min (1.0)')

            # 保存图像 - 使用英文文件名
            plt.savefig('combined_exp_wave_waveform.png', dpi=300, bbox_inches='tight')
            print("Waveform plot saved as 'combined_exp_wave_waveform.png'")

            plt.close()

        except ImportError:
            print("Warning: matplotlib not installed, skipping waveform plot")
        except Exception as e:
            print(f"Error generating waveform plot: {str(e)}")

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
        shift0to1 = phi_small
        exponential_coef = 3
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
        distances = np.sqrt(dx**2 + dy**2 + dz ** 2)

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

    def segment_egghead_points_by_jump(self, points):
        """根据锯齿波跳变点分割点曲线，并在段间添加混接曲线"""
        segments = []  # 存储分割后的点段
        current_segment = [points[0]]

        # 使用预计算的波形值检测跳变点
        amp_scale = np.percentile(np.abs(self.exp_wave_values), 95)
        jump_threshold = 0.5 * amp_scale
        jump_points = []  # 记录跳变点位置

        # 首先对曲线进行离散化处理
        discrete_points = []
        for i in range(len(points) - 1):
            discrete_points.append(points[i])

            prev_wave = self.exp_wave_values[i]
            next_wave = self.exp_wave_values[i + 1]

            if abs(prev_wave - next_wave) > jump_threshold:
                discrete_points.append(None)  # 标记跳变点
                jump_points.append(i)
                print(f"检测到跳变点: 索引 {i}, 波形值从 {prev_wave:.4f} 降到 {next_wave:.4f}")

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
                    blend_points = self.create_g4_g4_blend_curve(
                        p_prev2, p_prev, p0, p1, p2, p3, p4
                    )
                    blended_segments.append(blend_points)
                    print(f"在段{i}和{i + 1}之间添加了G4-G4混接曲线，包含{len(blend_points)}个点")
                else:
                    print(f"警告: 段{i}或{i + 1}点数不足，无法创建G4混接曲线")
                    # 添加简单线性过渡作为后备方案
                    blend_points = [segments[i][-1], segments[i + 1][0]]
                    blended_segments.append(blend_points)

        print(f"点曲线被分成 {len(blended_segments)} 段")
        print(f"检测到 {len(jump_points)} 个跳变点")
        return blended_segments

    def create_g4_g4_blend_curve(self, p_prev2, p_prev, p0, p1, p2, p3, p4):
        """
        创建混接曲线：前点G4曲率连续，后点G4曲率连续（使用8次贝塞尔曲线）
        :param p_prev2: 前一段倒数第三个点（用于计算曲率变化率）
        :param p_prev: 前一段倒数第二个点
        :param p0: 前一段最后一个点（G4连续点）
        :param p1: 后一段第一个点（G4连续点）
        :param p2: 后一段第二个点
        :param p3: 后一段第三个点
        :param p4: 后一段第四个点（用于计算曲率变化率）
        :return: 混接曲线点列表
        """
        # 将点转换为NumPy数组
        p_prev2 = np.array(p_prev2)
        p_prev = np.array(p_prev)
        p0 = np.array(p0)
        p1 = np.array(p1)
        p2 = np.array(p2)
        p3 = np.array(p3)
        p4 = np.array(p4)

        # 计算前一段在p0处的导数
        tangent_in = p0 - p_prev  # 一阶导数（切向量）
        curvature_in = (p_prev - 2 * p_prev2 + p0)  # 二阶导数（曲率向量）
        jerk_in = (p0 - 3 * p_prev + 3 * p_prev2 - self.get_prev_point(p_prev2))  # 三阶导数（曲率变化率）

        # 计算后一段在p1处的导数
        tangent_out = p2 - p1  # 一阶导数（切向量）
        curvature_out = (p3 - 2 * p2 + p1)  # 二阶导数（曲率向量）
        jerk_out = (p4 - 3 * p3 + 3 * p2 - p1)  # 三阶导数（曲率变化率）

        # 归一化向量（防止零除）
        tangent_in = tangent_in / (np.linalg.norm(tangent_in) + 1e-6)
        tangent_out = tangent_out / (np.linalg.norm(tangent_out) + 1e-6)

        # 使用8次贝塞尔曲线（9个控制点）
        dist = np.linalg.norm(p1 - p0)
        n = 8  # 贝塞尔曲线阶数

        # 控制点计算（满足G4连续性条件）
        B0 = p0  # 起点

        # p0处的G4连续条件
        B1 = p0 + tangent_in * 0.2 * dist  # 一阶连续
        B2 = p0 + tangent_in * 0.4 * dist + curvature_in * 0.1 * dist  # 二阶连续
        B3 = p0 + tangent_in * 0.6 * dist + curvature_in * 0.2 * dist + jerk_in * 0.05 * dist  # 三阶连续

        # p1处的G4连续条件
        B8 = p1  # 终点
        B7 = p1 - tangent_out * 0.2 * dist  # 一阶连续
        B6 = p1 - tangent_out * 0.4 * dist + curvature_out * 0.1 * dist  # 二阶连续
        B5 = p1 - tangent_out * 0.6 * dist + curvature_out * 0.2 * dist + jerk_out * 0.05 * dist  # 三阶连续

        # 中间控制点（自由参数，用于平滑过渡）
        B4 = (B3 + B5) / 2  # 中间点取平均

        # 生成8次贝塞尔曲线点
        num_points = 30
        blend_points = []
        for t in np.linspace(0, 1, num_points):
            # 8次贝塞尔曲线公式
            mt = 1 - t
            t2 = t * t
            t3 = t2 * t
            t4 = t3 * t
            t5 = t4 * t
            t6 = t5 * t
            t7 = t6 * t
            t8 = t7 * t

            mt2 = mt * mt
            mt3 = mt2 * mt
            mt4 = mt3 * mt
            mt5 = mt4 * mt
            mt6 = mt5 * mt
            mt7 = mt6 * mt
            mt8 = mt7 * mt

            point = (
                    mt8 * B0 +
                    8 * mt7 * t * B1 +
                    28 * mt6 * t2 * B2 +
                    56 * mt5 * t3 * B3 +
                    70 * mt4 * t4 * B4 +
                    56 * mt3 * t5 * B5 +
                    28 * mt2 * t6 * B6 +
                    8 * mt * t7 * B7 +
                    t8 * B8
            )
            blend_points.append(point.tolist())

        return blend_points

    def get_prev_point(self, p_prev2):
        """辅助函数：获取前一段倒数第四个点（简化实现）"""
        # 实际实现应根据数据结构获取前一点
        return p_prev2  # 简化处理

    def save_to_dxf(self, filename):
        """保存到DXF文件，为每个点生成独立的导轨线，并添加扫掠断面"""
        # 定义颜色方案
        colors = {
            'sections': 3,  # 绿色 - 扫掠断面
            'axis': 7,  # 黑色 - 中心轴
            'end_section_lines': 1  # 品红色 - 首尾断面连线
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, guide_lines = self.sweep_section()

        # 添加中心轴（黑色）
        z_coords = [p[2] for p in center_points]
        z_axis_length = max(z_coords) - min(z_coords)
        line = msp.add_line((0, 0, -z_axis_length / 3), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        # 添加所有扫掠断面（绿色）
        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        # 定义排除的颜色
        excluded_colors = [3, 7, 1]  # 绿色、黑色和品红色

        # 为每条导轨线添加独立的图层和颜色
        for j, points in guide_lines.items():
            # 创建图层
            layer_name = f"guide_{j}"
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name)

            # 使用循环颜色索引 (1-255)，跳过排除的颜色
            color_index = (j % 254) + 1
            while color_index in excluded_colors:
                color_index = (color_index + 1) % 255
                if color_index == 0:
                    color_index = 1

            # 对导轨线进行分段处理
            segments = self.segment_egghead_points_by_jump(points)

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
        target_turns = [0, 0.5, 1.5, 2]

        # 为每个目标位置添加投影线
        for turn in target_turns:
            # 计算该圈数对应的t值
            t_val = turn / self.n_turns
            # 计算对应的索引
            idx = int(t_val * (self.num_t - 1))

            # 获取该索引对应的扫掠断面
            section_idx = idx // sections_mod_n  # 假设每sections_mod_n个点保存一个断面

            # 获取目标位置前后断面
            start_idx = max(0, section_idx - 3) #前3个断面
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

        doc.saveas(filename)
        print(f"成功保存所有导轨线和扫掠断面到 {filename}")
if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    print("当psi越来越大，则是顺时针旋转；若是越来越小 → 则是逆时针旋转")
    new_bottom, new_h, new_amp = 108, 144, 3
    target_side_angle_deg = 13.282525  # 用户要求的侧面夹角 11.75°是基于地磁偏角

    # 使用目标侧面夹角计算top直径并创建模型
    generator_right = SpiralSweepGenerator(
        'start 舒伯格蛋咬一口曲线.dxf', 'end 舒伯格蛋咬一口曲线.dxf',
        bottom=new_bottom,
        high=new_h,
        amp=new_amp,
        dxf_points=16,  # 指定DXF曲线重建点数
        twist_type='exponential'  # linear线性扭转，exponential非线性扭转
    )

    # 设置其他参数并生成dxf文件
    generator_right.sign = 1  # 管旋转180
    generator_right.r = -1
    generator_right.twist = twist_angle
    generator_right.save_to_dxf('波纹螺旋锥管 指数螺旋_phi_滑滑梯_多规扫掠.dxf')