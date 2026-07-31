import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib
from matplotlib.path import Path
import matplotlib.patches as patches
from scipy import interpolate
from math import cos, sin, atan2, pi, sqrt, hypot, gcd
import ezdxf
from ezdxf import zoom
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import colorsys
import math
import warnings
from numba import jit, njit
import time
import tempfile  # 添加这行导入
import shutil    # 添加这行导入

# 忽略PNG相关的警告
warnings.filterwarnings("ignore", category=UserWarning)

# 内置高级参数
ADVANCED_PARAMS = {
    'saturation': 0.8,
    'value': 1,
    'export_dpi': 300,
    'pen_size': 0.5,
    'pen_alpha': 1,
    'auto_save': True  # 新增：是否自动保存历史记录
}


class DXFCurveReader:
    """读取DXF文件中的贝塞尔曲线"""

    def __init__(self):
        self.curves = []
        self.original_curves = []
        self._length_cache = {}

    def read_dxf(self, filename):
        """读取DXF文件并提取曲线"""
        try:
            doc = ezdxf.readfile(filename)
            msp = doc.modelspace()

            # 提取所有样条曲线(贝塞尔曲线)
            splines = msp.query('SPLINE')
            self.curves = []
            self._length_cache.clear()

            for spline in splines:
                curve_points = self.extract_spline_points(spline)
                if len(curve_points) > 2:
                    self.curves.append(curve_points)

            # 保存原始曲线副本
            self.original_curves = [curve.copy() for curve in self.curves]

            return len(self.curves) > 0
        except Exception as e:
            print(f"读取DXF文件错误: {e}")
            return False

    def extract_spline_points(self, spline, num_points=200):
        """从样条曲线提取点"""
        points = []

        if spline.control_points is not None and len(spline.control_points) > 0:
            ctrl_points = np.array([p[:2] for p in spline.control_points])

            if spline.closed:
                ctrl_points = np.vstack([ctrl_points, ctrl_points[0:1]])

            t = np.linspace(0, 1, len(ctrl_points))
            t_new = np.linspace(0, 1, num_points)

            if len(ctrl_points) >= 4:
                x_spline = interpolate.CubicSpline(t, ctrl_points[:, 0])
                y_spline = interpolate.CubicSpline(t, ctrl_points[:, 1])

                x_new = x_spline(t_new)
                y_new = y_spline(t_new)
                points = np.column_stack([x_new, y_new])
            else:
                if len(ctrl_points) > 1:
                    tck, u = interpolate.splprep([ctrl_points[:, 0], ctrl_points[:, 1]], s=0)
                    points = np.column_stack(interpolate.splev(np.linspace(0, 1, num_points), tck))
        else:
            if hasattr(spline, 'fit_points') and spline.fit_points is not None:
                fit_points = np.array([p[:2] for p in spline.fit_points])
                if len(fit_points) > 1:
                    points = self.linear_interpolate_curve(fit_points, num_points)

        return points if len(points) > 0 else np.array([[0, 0], [1, 1]])

    def linear_interpolate_curve(self, points, num_points):
        """线性插值生成曲线点"""
        if len(points) < 2:
            return points

        diffs = np.diff(points, axis=0)
        segment_lengths = np.hypot(diffs[:, 0], diffs[:, 1])
        cumulative_lengths = np.insert(np.cumsum(segment_lengths), 0, 0)
        total_length = cumulative_lengths[-1]

        new_lengths = np.linspace(0, total_length, num_points)
        new_points = []

        for i, length in enumerate(new_lengths):
            idx = np.searchsorted(cumulative_lengths, length, side='right') - 1
            idx = max(0, min(idx, len(points) - 2))

            segment_start_length = cumulative_lengths[idx]
            segment_end_length = cumulative_lengths[idx + 1]
            t = (length - segment_start_length) / (
                    segment_end_length - segment_start_length) if segment_end_length > segment_start_length else 0

            interpolated_point = points[idx] + t * (points[idx + 1] - points[idx])
            new_points.append(interpolated_point)

        return np.array(new_points)

    def get_curve_bounds(self, curve_index=0):
        """获取曲线的边界"""
        if curve_index < len(self.curves):
            points = self.curves[curve_index]
            min_coords = np.min(points, axis=0)
            max_coords = np.max(points, axis=0)
            return (*min_coords, *max_coords)
        return (0, 0, 0, 0)

    def calculate_curve_length(self, curve_index=0):
        """计算曲线总长度"""
        if curve_index in self._length_cache:
            return self._length_cache[curve_index]

        if curve_index < len(self.curves):
            points = self.curves[curve_index]
            if len(points) < 2:
                return 0

            diffs = np.diff(points, axis=0)
            total_length = np.sum(np.hypot(diffs[:, 0], diffs[:, 1]))

            self._length_cache[curve_index] = total_length
            return total_length
        return 0

    def scale_curves_to_target_length(self, reference_curve_index, target_length):
        """将所有曲线基于参考曲线缩放以达到目标长度"""
        if reference_curve_index >= len(self.curves):
            return False, "参考曲线索引超出范围"

        current_length = self.calculate_curve_length(reference_curve_index)

        if current_length == 0:
            return False, "参考曲线长度为0，无法缩放"

        scale_factor = target_length / current_length

        if scale_factor <= 0:
            return False, "缩放因子必须为正数"

        ref_points = self.curves[reference_curve_index]
        center = np.mean(ref_points, axis=0)

        for i in range(len(self.curves)):
            self.curves[i] = (self.curves[i] - center) * scale_factor + center

        self._length_cache.clear()

        return True, f"成功缩放曲线，缩放因子: {scale_factor:.4f}"

    def reset_to_original_curves(self):
        """重置为原始曲线"""
        if len(self.original_curves) > 0:
            self.curves = [curve.copy() for curve in self.original_curves]
            self._length_cache.clear()
            return True, "已重置为原始曲线"
        return False, "没有原始曲线数据"


class ArbitrarySpirograph:
    """任意曲线万花尺生成器"""

    def __init__(self):
        self.curve_points = None
        self.discrete_curve = None
        self.pen_trace = None
        self.curve_length = 0
        self.gear_ratio_num = 1
        self.gear_ratio_den = 1
        self.pen_position_num = 1
        self.pen_position_den = 1
        self.rotation_direction = 1
        self.colors = []
        self.closure_ensured = False
        self.curvature_checked = False
        self.min_curvature_radius = float('inf')

    def set_curve(self, curve_points):
        """设置外轮廓曲线并计算长度"""
        self.curve_points = np.array(curve_points, dtype=np.float64)
        self.discrete_curve = None
        self.pen_trace = None
        self.colors = []
        self.closure_ensured = False
        self.curvature_checked = False

        if len(self.curve_points) > 1:
            diffs = np.diff(self.curve_points, axis=0)
            self.curve_length = np.sum(np.hypot(diffs[:, 0], diffs[:, 1]))
        else:
            self.curve_length = 0

    def discrete_curve_by_chord_length(self, num_points=1000):
        """将曲线按等弦长离散化"""
        if self.curve_points is None or len(self.curve_points) < 2:
            return None

        diffs = np.diff(self.curve_points, axis=0)
        segment_lengths = np.hypot(diffs[:, 0], diffs[:, 1])
        cumulative_lengths = np.insert(np.cumsum(segment_lengths), 0, 0)
        total_length = cumulative_lengths[-1]

        new_lengths = np.linspace(0, total_length, num_points)

        t = cumulative_lengths / total_length

        try:
            x_interp = interpolate.Akima1DInterpolator(t, self.curve_points[:, 0])
            y_interp = interpolate.Akima1DInterpolator(t, self.curve_points[:, 1])

            t_new = new_lengths / total_length
            x_new = x_interp(t_new)
            y_new = y_interp(t_new)
        except:
            x_new = np.interp(new_lengths, cumulative_lengths, self.curve_points[:, 0])
            y_new = np.interp(new_lengths, cumulative_lengths, self.curve_points[:, 1])

        self.discrete_curve = np.column_stack([x_new, y_new])
        return self.discrete_curve

    def calculate_curvature_radius(self, points, i):
        """计算曲线上第i点处的曲率半径"""
        if len(points) < 3 or i < 1 or i >= len(points) - 1:
            return float('inf')

        p0, p1, p2 = points[i - 1], points[i], points[i + 1]

        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        cross = abs(dx1 * dy2 - dy1 * dx2)
        dot1 = dx1 * dx1 + dy1 * dy1
        dot2 = dx2 * dx2 + dy2 * dy2
        dot_product = dx1 * dx2 + dy1 * dy2

        denominator = dot1 * dot2 - dot_product * dot_product

        if denominator > 1e-10:
            radius = 0.5 * sqrt(dot1 + dot2) * sqrt(dot1 * dot2) / (cross + 1e-10)
            return radius

        return float('inf')

    def check_curvature_constraint(self, gear_radius):
        """检查曲率约束"""
        if self.discrete_curve is None:
            self.discrete_curve_by_chord_length(1000)

        n = len(self.discrete_curve)
        if n < 3:
            return True, float('inf'), []

        min_radius = float('inf')
        problematic_points = []

        for i in range(1, n - 1):
            radius = self.calculate_curvature_radius(self.discrete_curve, i)
            if radius < min_radius:
                min_radius = radius

            if radius < gear_radius * 1.01:
                problematic_points.append((i, radius))

        self.min_curvature_radius = min_radius
        self.curvature_checked = True

        if len(problematic_points) > 0:
            return False, min_radius, problematic_points
        else:
            return True, min_radius, []

    def calculate_gear_radius(self):
        """计算小圆半径"""
        return (self.gear_ratio_num / self.gear_ratio_den) * self.curve_length / (2 * np.pi)

    def calculate_pen_distance(self, gear_radius):
        """计算笔尖距离"""
        return (self.pen_position_num / self.pen_position_den) * gear_radius

    def find_optimal_gear_ratio(self, target_ratio):
        """找到最优齿轮比"""
        best_num, best_den = 1, 1
        best_error = float('inf')

        max_den = min(50, int(100 / target_ratio) + 10)

        for den in range(1, max_den + 1):
            num = max(1, round(target_ratio * den))
            if num > 100:
                continue

            error = abs(num / den - target_ratio)
            if error < best_error:
                best_error = error
                best_num, best_den = num, den

                if error < 0.001:
                    break

        return best_num, best_den

    def calculate_perfect_rotations(self):
        """计算完美闭合的旋转圈数"""
        if self.curve_length == 0:
            return 10

        p = self.gear_ratio_num
        q = self.gear_ratio_den
        a = self.pen_position_num
        b = self.pen_position_den

        gcd_pa = math.gcd(p, a)
        gcd_qb = math.gcd(q, b)

        p_simple = p // gcd_pa
        a_simple = a // gcd_pa
        q_simple = q // gcd_qb
        b_simple = b // gcd_qb

        numerator = p_simple * a_simple
        denominator = q_simple * b_simple

        gcd_val = math.gcd(numerator, denominator)
        perfect_rotations = denominator // gcd_val

        if perfect_rotations < 1:
            perfect_rotations = 1

        return perfect_rotations

    def ensure_pattern_closure(self, num_rotations):
        """确保图案闭合"""
        perfect_rotations = self.calculate_perfect_rotations()

        if num_rotations < perfect_rotations:
            adjusted_rotations = perfect_rotations
        else:
            adjusted_rotations = math.ceil(num_rotations / perfect_rotations) * perfect_rotations

        if adjusted_rotations != num_rotations:
            print(f"圈数已从 {num_rotations} 调整为 {adjusted_rotations} 以确保图案完美闭合")

        return adjusted_rotations

    def hsv_color_gradient(self, cycle_count, total_cycles, saturation=0.8, value=0.9):
        """生成HSV渐变颜色（使用文件2的正确算法）"""
        hue = cycle_count / total_cycles
        hue = hue % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return (r, g, b)

    def simulate_gear_motion(self, num_rotations=10):
        """模拟齿轮运动"""
        if self.curve_points is None:
            return None, [], False, 0

        start_time = time.time()

        adjusted_rotations = self.ensure_pattern_closure(num_rotations)

        if self.discrete_curve is None:
            self.discrete_curve_by_chord_length(1000)

        n = len(self.discrete_curve)
        if n < 2:
            return None, [], False, 0

        gear_radius = self.calculate_gear_radius()
        pen_distance = self.calculate_pen_distance(gear_radius)

        print(f"曲线长度: {self.curve_length:.2f}")
        print(f"齿轮半径: {gear_radius:.2f}")
        print(f"笔尖距离: {pen_distance:.2f}")
        print(f"齿轮比: {self.gear_ratio_num}/{self.gear_ratio_den}")
        print(f"笔尖位置: {self.pen_position_num}/{self.pen_position_den}")
        print(f"完美闭合圈数: {self.calculate_perfect_rotations()}")
        print(f"调整后的圈数: {adjusted_rotations}")

        curvature_ok, min_radius, problematic_points = self.check_curvature_constraint(gear_radius)
        if not curvature_ok:
            print(f"警告: 曲线最小曲率半径 {min_radius:.2f} 小于齿轮半径 {gear_radius:.2f}")

        total_steps = int(adjusted_rotations * n)
        pen_path = np.zeros((total_steps, 2))
        current_angle = 0.0

        for step in range(total_steps):
            i = step % n
            next_i = (i + 1) % n

            current_point = self.discrete_curve[i]
            next_point = self.discrete_curve[next_i]

            dx = next_point[0] - current_point[0]
            dy = next_point[1] - current_point[1]
            tangent_length = sqrt(dx * dx + dy * dy)

            if tangent_length > 1e-10:
                tangent_x = dx / tangent_length
                tangent_y = dy / tangent_length

                if self.rotation_direction == 1:
                    normal_x = -tangent_y
                    normal_y = tangent_x
                else:
                    normal_x = tangent_y
                    normal_y = -tangent_x

                gear_center_x = current_point[0] + normal_x * gear_radius
                gear_center_y = current_point[1] + normal_y * gear_radius

                rotation_angle = self.rotation_direction * tangent_length / gear_radius
                current_angle += rotation_angle

                pen_x = gear_center_x + pen_distance * cos(current_angle)
                pen_y = gear_center_y + pen_distance * sin(current_angle)

                pen_path[step] = [pen_x, pen_y]
            else:
                pen_path[step] = current_point

        # 使用文件2的正确HSV渐变算法生成颜色
        self.colors = []
        for step in range(total_steps):
            cycle_count = step / n
            color = self.hsv_color_gradient(cycle_count, adjusted_rotations,
                                            ADVANCED_PARAMS['saturation'],
                                            ADVANCED_PARAMS['value'])
            self.colors.append(color)

        self.pen_trace = pen_path

        if len(self.pen_trace) > 1:
            start_point = self.pen_trace[0]
            end_point = self.pen_trace[-1]
            distance = np.linalg.norm(end_point - start_point)

            if distance < 0.001:
                print("图案闭合成功！")
                self.closure_ensured = True
            else:
                print(f"图案闭合误差: {distance:.6f}")
                self.closure_ensured = False

        elapsed_time = time.time() - start_time
        print(f"模拟完成，耗时: {elapsed_time:.2f}秒")

        return self.pen_trace, self.colors, curvature_ok, min_radius

    def set_parameters(self, gear_ratio_num, gear_ratio_den, pen_position_num, pen_position_den, rotation_direction=1):
        """设置参数"""
        self.gear_ratio_num = gear_ratio_num
        self.gear_ratio_den = gear_ratio_den
        self.pen_position_num = pen_position_num
        self.pen_position_den = pen_position_den
        self.rotation_direction = rotation_direction

        self.discrete_curve = None
        self.pen_trace = None
        self.colors = []
        self.closure_ensured = False
        self.curvature_checked = False


class SpirographApp:
    """万花尺应用程序界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("任意曲线万花尺生成器（多曲线支持）")
        self.root.geometry("1200x800")

        self.dxf_reader = DXFCurveReader()
        self.spirograph = ArbitrarySpirograph()
        self.current_curve_index = 0
        self.curve_colors = []
        self.curve_directions = {}
        self.generated_patterns = []

        # 新增：历史记录相关
        self.history_dir = tempfile.mkdtemp(prefix="spirograph_history_")
        self.history_files = []  # 存储历史文件路径
        self.current_history_index = -1

        # 新增：背景图像
        self.background_image = None
        self.background_ax = None

        self.setup_ui()
        self.update_status("请加载DXF文件")

        # 程序退出时清理临时文件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """程序退出时清理临时文件"""
        try:
            if os.path.exists(self.history_dir):
                shutil.rmtree(self.history_dir)
        except:
            pass
        self.root.destroy()

    def setup_ui(self):
        """设置用户界面"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧控制面板
        left_frame = tk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # 文件操作区域
        file_frame = tk.LabelFrame(left_frame, text="文件操作", padx=8, pady=8)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(file_frame, text="加载DXF文件", command=self.load_dxf_file).pack(fill=tk.X)
        tk.Button(file_frame, text="保存PNG", command=self.export_pattern, bg="lightgreen").pack(fill=tk.X, pady=(5, 0))

        # 曲线信息区域
        info_frame = tk.LabelFrame(left_frame, text="曲线信息", padx=8, pady=8)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.curve_length_var = tk.StringVar(value="曲线长度: 0.00")
        tk.Label(info_frame, textvariable=self.curve_length_var).pack(anchor=tk.W)

        self.closure_status_var = tk.StringVar(value="闭合状态: 未检测")
        tk.Label(info_frame, textvariable=self.closure_status_var).pack(anchor=tk.W)

        self.curvature_status_var = tk.StringVar(value="曲率状态: 未检测")
        tk.Label(info_frame, textvariable=self.curvature_status_var).pack(anchor=tk.W)

        # 万花尺参数区域
        param_frame = tk.LabelFrame(left_frame, text="万花尺参数", padx=8, pady=8)
        param_frame.pack(fill=tk.X, pady=(0, 10))

        # 齿轮比
        gear_frame = tk.Frame(param_frame)
        gear_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(gear_frame, text="齿轮比:").pack(side=tk.LEFT)

        self.gear_num_var = tk.StringVar(value="1")
        self.gear_den_var = tk.StringVar(value="24")
        gear_num_entry = tk.Entry(gear_frame, textvariable=self.gear_num_var, width=5)
        gear_num_entry.pack(side=tk.LEFT, padx=(5, 0))
        tk.Label(gear_frame, text="/").pack(side=tk.LEFT)
        gear_den_entry = tk.Entry(gear_frame, textvariable=self.gear_den_var, width=5)
        gear_den_entry.pack(side=tk.LEFT)

        tk.Button(gear_frame, text="自动", command=self.auto_gear_ratio, width=5).pack(side=tk.RIGHT)

        # 笔尖位置
        pen_frame = tk.Frame(param_frame)
        pen_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(pen_frame, text="笔尖位置:").pack(side=tk.LEFT)

        self.pen_num_var = tk.StringVar(value="1")
        self.pen_den_var = tk.StringVar(value="10")
        pen_num_entry = tk.Entry(pen_frame, textvariable=self.pen_num_var, width=5)
        pen_num_entry.pack(side=tk.LEFT, padx=(5, 0))
        tk.Label(pen_frame, text="/").pack(side=tk.LEFT)
        pen_den_entry = tk.Entry(pen_frame, textvariable=self.pen_den_var, width=5)
        pen_den_entry.pack(side=tk.LEFT)

        tk.Button(pen_frame, text="自动", command=self.auto_pen_position, width=5).pack(side=tk.RIGHT)

        # 旋转圈数
        rotation_frame = tk.Frame(param_frame)
        rotation_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(rotation_frame, text="旋转圈数:").pack(side=tk.LEFT)

        self.rotation_var = tk.StringVar(value="60")
        rotation_entry = tk.Entry(rotation_frame, textvariable=self.rotation_var, width=10)
        rotation_entry.pack(side=tk.LEFT, padx=(5, 0))

        tk.Button(rotation_frame, text="自动圈数", command=self.auto_rotations, width=8).pack(side=tk.RIGHT)

        # 方向选择
        direction_frame = tk.Frame(param_frame)
        direction_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(direction_frame, text="方向:").pack(side=tk.LEFT)

        self.direction_var = tk.StringVar(value="1")
        tk.Radiobutton(direction_frame, text="内部", variable=self.direction_var, value="1").pack(side=tk.LEFT)
        tk.Radiobutton(direction_frame, text="外部", variable=self.direction_var, value="-1").pack(side=tk.LEFT)

        # 操作按钮
        button_frame = tk.Frame(param_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(button_frame, text="检查曲率", command=self.check_curvature).pack(side=tk.LEFT, expand=True)
        tk.Button(button_frame, text="生成图案", command=self.generate_pattern).pack(side=tk.LEFT, expand=True,
                                                                                     padx=(5, 0))
        tk.Button(button_frame, text="撤回", command=self.undo_pattern).pack(side=tk.LEFT, expand=True,
                                                                             padx=(5, 0))  # 新增撤回按钮
        tk.Button(button_frame, text="清除图案", command=self.clear_patterns).pack(side=tk.LEFT, expand=True,
                                                                                   padx=(5, 0))

        # 曲线选择区域
        curve_frame = tk.LabelFrame(left_frame, text="曲线选择", padx=8, pady=8)
        curve_frame.pack(fill=tk.X, pady=(0, 10))

        self.curve_selector = ttk.Combobox(curve_frame, state="readonly")
        self.curve_selector.pack(fill=tk.X)
        self.curve_selector.bind("<<ComboboxSelected>>", self.on_curve_selected)

        # 曲线缩放区域
        scale_frame = tk.LabelFrame(left_frame, text="曲线缩放", padx=8, pady=8)
        scale_frame.pack(fill=tk.X)

        # 参考曲线
        ref_frame = tk.Frame(scale_frame)
        ref_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(ref_frame, text="参考曲线:").pack(side=tk.LEFT)

        self.ref_curve_var = tk.StringVar(value="1")
        ref_curve_spin = tk.Spinbox(ref_frame, from_=1, to=100, textvariable=self.ref_curve_var, width=5)
        ref_curve_spin.pack(side=tk.RIGHT)

        # 目标长度
        target_frame = tk.Frame(scale_frame)
        target_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(target_frame, text="目标长度:").pack(side=tk.LEFT)

        self.target_length_var = tk.StringVar(value="4410")
        target_entry = tk.Entry(target_frame, textvariable=self.target_length_var, width=10)
        target_entry.pack(side=tk.RIGHT)

        # 缩放按钮
        scale_button_frame = tk.Frame(scale_frame)
        scale_button_frame.pack(fill=tk.X)

        tk.Button(scale_button_frame, text="缩放曲线", command=self.scale_curves).pack(side=tk.LEFT, expand=True)
        tk.Button(scale_button_frame, text="重置", command=self.reset_curves).pack(side=tk.LEFT, expand=True,
                                                                                   padx=(5, 0))

        # 右侧绘图区域
        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加工具栏
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        self.canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)

    def load_dxf_file(self):
        """加载DXF文件"""
        file_path = filedialog.askopenfilename(filetypes=[("DXF文件", "*.dxf")])
        if file_path:
            success = self.dxf_reader.read_dxf(file_path)
            if success:
                self.update_curve_selector()
                self.plot_curves()
                self.update_curve_info()
                self.update_status(f"成功加载 {len(self.dxf_reader.curves)} 条曲线")
            else:
                self.update_status("加载DXF文件失败")

    def update_curve_selector(self):
        """更新曲线选择器"""
        curves = [f"曲线 {i + 1}" for i in range(len(self.dxf_reader.curves))]
        self.curve_selector["values"] = curves
        if curves:
            self.curve_selector.current(0)
            self.current_curve_index = 0

    def on_curve_selected(self, event):
        """曲线选择事件处理"""
        selected = self.curve_selector.current()
        if selected >= 0:
            self.current_curve_index = selected
            self.plot_curves()
            self.update_curve_info()

    def update_curve_info(self):
        """更新曲线信息显示"""
        if self.current_curve_index < len(self.dxf_reader.curves):
            curve_length = self.dxf_reader.calculate_curve_length(self.current_curve_index)
            self.curve_length_var.set(f"曲线长度: {curve_length:.2f}")

            # 更新目标长度输入框为当前曲线长度
            self.target_length_var.set(f"{curve_length:.0f}")

    def auto_gear_ratio(self):
        """自动计算齿轮比"""
        # 这里可以实现自动计算逻辑
        self.update_status("自动齿轮比功能待实现")

    def auto_pen_position(self):
        """自动计算笔尖位置"""
        # 这里可以实现自动计算逻辑
        self.update_status("自动笔尖位置功能待实现")

    def auto_rotations(self):
        """自动计算旋转圈数"""
        try:
            gear_num = int(self.gear_num_var.get())
            gear_den = int(self.gear_den_var.get())
            pen_num = int(self.pen_num_var.get())
            pen_den = int(self.pen_den_var.get())

            self.spirograph.set_parameters(gear_num, gear_den, pen_num, pen_den, 1)
            recommended = self.spirograph.calculate_perfect_rotations()
            self.rotation_var.set(str(recommended))
            self.update_status(f"已自动设置推荐圈数: {recommended}")
        except ValueError:
            self.update_status("参数错误: 请输入有效的数字")

    def check_curvature(self):
        """检查曲率约束"""
        if self.current_curve_index >= len(self.dxf_reader.curves):
            self.update_status("错误: 当前曲线索引无效")
            return

        try:
            gear_num = int(self.gear_num_var.get())
            gear_den = int(self.gear_den_var.get())

            curve_points = self.dxf_reader.curves[self.current_curve_index]
            self.spirograph.set_curve(curve_points)
            self.spirograph.set_parameters(gear_num, gear_den, 1, 1, 1)

            gear_radius = self.spirograph.calculate_gear_radius()
            curvature_ok, min_radius, problematic_points = self.spirograph.check_curvature_constraint(gear_radius)

            if curvature_ok:
                self.curvature_status_var.set(f"曲率状态: √半径{min_radius:.2f} > 齿轮半径")
                self.update_status("曲率检查通过")
            else:
                self.curvature_status_var.set(f"曲率状态: ×半径{min_radius:.2f} < 齿轮半径")
                self.update_status(f"警告: 曲线最小曲率半径 {min_radius:.2f} 小于齿轮半径 {gear_radius:.2f}")

        except ValueError:
            self.update_status("参数错误: 请输入有效的数字")

    def save_current_state(self):
        """保存当前状态到历史记录"""
        if not ADVANCED_PARAMS['auto_save']:
            return

        # 保存当前画布为PNG
        timestamp = int(time.time() * 1000)
        filename = f"history_{timestamp}.png"
        filepath = os.path.join(self.history_dir, filename)

        try:
            # 保存当前图像（包括所有曲线和图案）
            # 关键修改：使用正确的DPI和方向
            self.figure.savefig(filepath, dpi=150, bbox_inches='tight',
                                transparent=True, facecolor='none', edgecolor='none',
                                orientation='landscape')  # 确保横向保存

            # 添加到历史记录
            self.history_files.append(filepath)
            self.current_history_index = len(self.history_files) - 1

            # 限制历史记录数量（最多10个）
            if len(self.history_files) > 10:
                # 删除最旧的文件
                old_file = self.history_files.pop(0)
                if os.path.exists(old_file):
                    os.remove(old_file)
                self.current_history_index = len(self.history_files) - 1

        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_history_state(self, index):
        """加载指定的历史记录状态"""
        if index < 0 or index >= len(self.history_files):
            return False

        try:
            filepath = self.history_files[index]
            if not os.path.exists(filepath):
                return False

            # 清除当前画布
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_aspect('equal', adjustable='datalim')
            ax.grid(False)

            # 绘制原始曲线
            for i, curve in enumerate(self.dxf_reader.curves):
                color = 'blue' if i == self.current_curve_index else 'gray'
                alpha = 0.7 if i == self.current_curve_index else 0.3
                linewidth = 2 if i == self.current_curve_index else 1
                ax.plot(curve[:, 0], curve[:, 1], color=color, alpha=alpha, linewidth=linewidth)

            # 加载历史图像作为背景
            img = plt.imread(filepath)
            # 获取当前坐标范围
            x_min, x_max = ax.get_xlim()*1.25
            y_min, y_max = ax.get_ylim()*1.25

            # 显示图像
            ax.imshow(img, extent=[x_min, x_max, y_min, y_max], aspect='auto', alpha=0.7)

            self.canvas.draw()
            self.current_history_index = index
            return True

        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return False

    def undo_pattern(self):
        """撤回最近生成的图案"""
        if len(self.history_files) <= 0:
            self.update_status("没有可撤回的操作")
            return

        # 回退到上一个历史记录
        target_index = self.current_history_index - 1
        if target_index < 0:
            # 如果是第一个历史记录，清除所有图案
            self.generated_patterns.clear()
            self.plot_curves()
            self.update_status("已撤回所有图案")
            return

        try:
            # 更新生成的图案列表，移除最后一个图案
            if len(self.generated_patterns) > 0:
                self.generated_patterns.pop()

            # 清除当前画布
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_aspect('equal', adjustable='datalim')
            ax.grid(False)

            # 绘制原始曲线
            for i, curve in enumerate(self.dxf_reader.curves):
                color = 'gray'
                alpha = 0.3
                linewidth = 1
                ax.plot(curve[:, 0], curve[:, 1], color=color, alpha=alpha, linewidth=linewidth)

            # 加载历史PNG图片
            filepath = self.history_files[target_index]
            if os.path.exists(filepath):
                # 获取当前图形的边界
                all_x = []
                all_y = []
                for curve in self.dxf_reader.curves:
                    all_x.extend(curve[:, 1])
                    all_y.extend(curve[:, 0])

                if all_x and all_y:
                    x_min, x_max = min(all_x), max(all_x)
                    y_min, y_max = min(all_y), max(all_y)
                    x_center = (x_min + x_max) / 2
                    y_center = (y_min + y_max) / 2
                    width = (x_max - x_min) * 2.25
                    height = (y_max - y_min) * 2.25

                    # 设置坐标轴范围
                    ax.set_xlim(x_center - width / 2, x_center + width / 2)
                    ax.set_ylim(y_center - height / 2, y_center + height / 2)

                # 加载并显示历史PNG - 关键修改：正确处理图片方向
                img = plt.imread(filepath)

                # 获取图片的尺寸和方向
                img_height, img_width = img.shape[0], img.shape[1]

                # 根据图片方向调整显示方式
                if img_height > img_width:
                    # 竖屏图片，可能需要转置
                    img = np.rot90(img, 1)  # 旋转90度

                # 获取当前坐标范围
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()

                # 显示历史图片 - 使用正确的extent
                ax.imshow(img, extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
                          aspect='auto', alpha=1.0, origin='upper')

                # 重新绘制当前生成的图案（如果有）
                for pattern in self.generated_patterns:
                    pen_trace, colors = pattern
                    x = pen_trace[:, 0]
                    y = pen_trace[:, 1]
                    ax.scatter(x, y, c=colors, s=ADVANCED_PARAMS['pen_size'] * 2,
                               alpha=ADVANCED_PARAMS['pen_alpha'])

            self.canvas.draw()
            self.current_history_index = target_index
            self.update_status(f"已撤回图案，当前历史: {target_index + 1}/{len(self.history_files)}")

        except Exception as e:
            print(f"撤回失败: {e}")
            self.update_status("撤回失败")

    def generate_pattern(self):
        """生成图案"""
        # 先生成图案
        try:
            gear_num = int(self.gear_num_var.get())
            gear_den = int(self.gear_den_var.get())
            pen_num = int(self.pen_num_var.get())
            pen_den = int(self.pen_den_var.get())
            direction = int(self.direction_var.get())
            rotations = int(self.rotation_var.get())

            if self.current_curve_index >= len(self.dxf_reader.curves):
                self.update_status("错误: 当前曲线索引无效")
                return

            # 设置当前曲线
            curve_points = self.dxf_reader.curves[self.current_curve_index]
            self.spirograph.set_curve(curve_points)

            # 设置参数
            self.spirograph.set_parameters(gear_num, gear_den, pen_num, pen_den, direction)

            # 模拟运动
            pen_trace, colors, curvature_ok, min_radius = self.spirograph.simulate_gear_motion(rotations)

            if pen_trace is not None:
                # 保存当前状态到历史记录
                self.save_current_state()

                # 保存生成的图案
                self.generated_patterns.append((pen_trace, colors))
                self.plot_curves()

                # 更新闭合状态
                if self.spirograph.closure_ensured:
                    self.closure_status_var.set("闭合状态: √完美闭合")
                else:
                    closure_error = np.linalg.norm(pen_trace[-1] - pen_trace[0])
                    self.closure_status_var.set(f"闭合状态: △有误差({closure_error:.4f})")

                # 更新曲率状态
                gear_radius = self.spirograph.calculate_gear_radius()
                if curvature_ok:
                    self.curvature_status_var.set(f"曲率状态: √半径{min_radius:.2f} > 齿轮半径")
                else:
                    self.curvature_status_var.set(f"曲率状态: ×半径{min_radius:.2f} < 齿轮半径")

                self.update_status(f"图案生成完成 (最小曲率半径: {min_radius:.2f})")

        except ValueError:
            self.update_status("参数错误: 请输入有效的数字")

    def clear_patterns(self):
        """清除所有生成的图案"""
        self.generated_patterns.clear()
        self.plot_curves()
        self.update_status("已清除所有图案")

    def scale_curves(self):
        """缩放曲线到目标长度"""
        try:
            target_length = float(self.target_length_var.get())
            ref_curve_index = int(self.ref_curve_var.get()) - 1

            if ref_curve_index < 0 or ref_curve_index >= len(self.dxf_reader.curves):
                self.update_status("错误: 参考曲线索引无效")
                return

            success, msg = self.dxf_reader.scale_curves_to_target_length(ref_curve_index, target_length)
            self.plot_curves()
            self.update_curve_info()
            self.update_status(msg)
        except ValueError:
            self.update_status("错误: 请输入有效的数字")

    def reset_curves(self):
        """重置曲线到原始状态"""
        if len(self.dxf_reader.original_curves) > 0:
            success, msg = self.dxf_reader.reset_to_original_curves()
            self.plot_curves()
            self.update_curve_info()
            self.update_status(msg)
        else:
            self.update_status("没有原始曲线数据")

    def plot_curves(self):
        """绘制曲线和图案"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_aspect('equal', adjustable='datalim')
        ax.grid(False)  # 已修改为不显示网格

        # 绘制所有曲线
        for i, curve in enumerate(self.dxf_reader.curves):
            color = 'blue' if i == self.current_curve_index else 'gray'
            alpha = 0.7 if i == self.current_curve_index else 0.3
            linewidth = 2 if i == self.current_curve_index else 1
            ax.plot(curve[:, 0], curve[:, 1], color=color, alpha=alpha, linewidth=linewidth)

        # 绘制生成的图案
        for pattern in self.generated_patterns:
            pen_trace, colors = pattern
            x = pen_trace[:, 0]
            y = pen_trace[:, 1]
            ax.scatter(x, y, c=colors, s=ADVANCED_PARAMS['pen_size'] * 2, alpha=ADVANCED_PARAMS['pen_alpha'])

        # 新增：计算图形边界并设置坐标系为1.25倍
        if len(self.dxf_reader.curves) > 0 or len(self.generated_patterns) > 0:
            # 获取所有点的边界
            all_x = []
            all_y = []

            # 添加曲线的点
            for curve in self.dxf_reader.curves:
                all_x.extend(curve[:, 0])
                all_y.extend(curve[:, 1])

            # 添加图案的点
            for pattern in self.generated_patterns:
                pen_trace, _ = pattern
                all_x.extend(pen_trace[:, 0])
                all_y.extend(pen_trace[:, 1])

            if all_x and all_y:  # 确保有点存在
                x_min, x_max = min(all_x), max(all_x)
                y_min, y_max = min(all_y), max(all_y)

                # 计算中心点
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2

                # 计算宽度和高度
                width = (x_max - x_min) * 1.25  # 1.25倍
                height = (y_max - y_min) * 1.25  # 1.25倍

                # 设置坐标轴范围
                ax.set_xlim(x_center - width / 2, x_center + width / 2)
                ax.set_ylim(y_center - height / 2, y_center + height / 2)

        self.canvas.draw()

    def export_pattern(self):
        """导出图案为图片（不包含蓝色原曲线）"""
        if not self.generated_patterns:
            self.update_status("没有图案可导出")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 创建一个新的临时图形用于导出
                export_fig = Figure(figsize=(8, 6), dpi=ADVANCED_PARAMS['export_dpi'])
                export_ax = export_fig.add_subplot(111)
                export_ax.set_aspect('equal', adjustable='datalim')
                export_ax.grid(False)

                # 只绘制生成的图案，不绘制蓝色原曲线
                for pattern in self.generated_patterns:
                    pen_trace, colors = pattern
                    x = pen_trace[:, 0]
                    y = pen_trace[:, 1]
                    export_ax.scatter(x, y, c=colors, s=ADVANCED_PARAMS['pen_size'] * 2,
                                      alpha=ADVANCED_PARAMS['pen_alpha'])

                # 设置合适的坐标轴范围（基于图案的范围）
                if self.generated_patterns:
                    all_x = []
                    all_y = []
                    for pattern in self.generated_patterns:
                        pen_trace, _ = pattern
                        all_x.extend(pen_trace[:, 0])
                        all_y.extend(pen_trace[:, 1])

                    if all_x and all_y:
                        x_min, x_max = min(all_x), max(all_x)
                        y_min, y_max = min(all_y), max(all_y)

                        # 添加一些边距
                        x_margin = (x_max - x_min) * 0.1
                        y_margin = (y_max - y_min) * 0.1

                        export_ax.set_xlim(x_min - x_margin, x_max + x_margin)
                        export_ax.set_ylim(y_min - y_margin, y_max + y_margin)

                # 隐藏坐标轴
                export_ax.set_axis_off()

                # 保存图片（透明背景）
                export_fig.savefig(file_path, dpi=ADVANCED_PARAMS['export_dpi'],
                                   bbox_inches='tight', pad_inches=0.1,
                                   transparent=True, facecolor='none', edgecolor='none')

                # 清理临时图形
                import matplotlib.pyplot as plt
                plt.close(export_fig)

                self.update_status(f"图案已导出到: {file_path}（不包含原曲线）")

            except Exception as e:
                self.update_status(f"导出失败: {str(e)}")

    def update_status(self, message):
        """更新状态栏"""
        print(message)  # 在控制台也输出状态信息


def main():
    root = tk.Tk()
    app = SpirographApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()