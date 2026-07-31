import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib

# 设置Matplotlib使用支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

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

# 忽略PNG相关的警告
warnings.filterwarnings("ignore", category=UserWarning)


class DXFCurveReader:
    """读取DXF文件中的贝塞尔曲线"""

    def __init__(self):
        self.curves = []
        self.original_curves = []  # 存储原始曲线，用于缩放恢复

    def read_dxf(self, filename):
        """读取DXF文件并提取曲线"""
        try:
            doc = ezdxf.readfile(filename)
            msp = doc.modelspace()

            # 提取所有样条曲线(贝塞尔曲线)
            splines = msp.query('SPLINE')
            self.curves = []
            self.original_curves = []  # 重置原始曲线

            for spline in splines:
                curve_points = self.extract_spline_points(spline)
                if len(curve_points) > 2:  # 确保是有效曲线
                    self.curves.append(curve_points)
                    # 保存原始曲线
                    self.original_curves.append(curve_points.copy())

            return len(self.curves) > 0
        except Exception as e:
            print(f"读取DXF文件错误: {e}")
            return False

    def extract_spline_points(self, spline, num_points=200):
        """从样条曲线提取点"""
        points = []

        # 获取样条曲线的控制点
        if spline.control_points is not None and len(spline.control_points) > 0:
            # 使用控制点生成平滑曲线
            ctrl_points = np.array([p[:2] for p in spline.control_points])

            # 如果曲线是闭合的，添加第一个点到末尾
            if spline.closed:
                ctrl_points = np.vstack([ctrl_points, ctrl_points[0:1]])

            # 创建参数化曲线
            t = np.linspace(0, 1, len(ctrl_points))
            t_new = np.linspace(0, 1, num_points)

            # 使用三次样条插值
            if len(ctrl_points) >= 4:
                x_spline = interpolate.CubicSpline(t, ctrl_points[:, 0])
                y_spline = interpolate.CubicSpline(t, ctrl_points[:, 1])

                x_new = x_spline(t_new)
                y_new = y_spline(t_new)
                points = np.column_stack([x_new, y_new])
            else:
                # 点太少，直接使用线性插值
                points = self.linear_interpolate_curve(ctrl_points, num_points)
        else:
            # 如果没有控制点，尝试使用拟合点
            if hasattr(spline, 'fit_points') and spline.fit_points is not None:
                fit_points = np.array([p[:2] for p in spline.fit_points])
                points = self.linear_interpolate_curve(fit_points, num_points)

        return points

    def linear_interpolate_curve(self, points, num_points):
        """线性插值生成曲线点"""
        if len(points) < 2:
            return points

        # 计算总长度
        total_length = 0
        lengths = [0]
        for i in range(1, len(points)):
            dx = points[i, 0] - points[i - 1, 0]
            dy = points[i, 1] - points[i - 1, 1]
            segment_len = hypot(dx, dy)
            total_length += segment_len
            lengths.append(total_length)

        # 等距采样
        new_lengths = np.linspace(0, total_length, num_points)

        # 线性插值
        new_points = []
        for l in new_lengths:
            # 找到对应的线段
            for i in range(1, len(lengths)):
                if l <= lengths[i]:
                    t = (l - lengths[i - 1]) / (lengths[i] - lengths[i - 1])
                    x = points[i - 1, 0] + t * (points[i, 0] - points[i - 1, 0])
                    y = points[i - 1, 1] + t * (points[i, 1] - points[i - 1, 1])
                    new_points.append([x, y])
                    break

        return np.array(new_points)

    def get_curve_bounds(self, curve_index=0):
        """获取曲线的边界"""
        if curve_index < len(self.curves):
            points = self.curves[curve_index]
            min_x, min_y = np.min(points, axis=0)
            max_x, max_y = np.max(points, axis=0)
            return (min_x, min_y, max_x, max_y)
        return (0, 0, 0, 0)

    def calculate_curve_length(self, curve_index=0):
        """计算曲线总长度"""
        if curve_index < len(self.curves):
            points = self.curves[curve_index]
            total_length = 0
            for i in range(1, len(points)):
                dx = points[i, 0] - points[i - 1, 0]
                dy = points[i, 1] - points[i - 1, 1]
                total_length += hypot(dx, dy)
            return total_length
        return 0

    def scale_curves_to_target_length(self, reference_curve_index, target_length):
        """将所有曲线基于参考曲线缩放以达到目标长度"""
        if reference_curve_index >= len(self.curves):
            return False, "参考曲线索引超出范围"

        # 计算参考曲线的当前长度
        current_length = self.calculate_curve_length(reference_curve_index)

        if current_length == 0:
            return False, "参考曲线长度为0，无法缩放"

        # 计算缩放因子
        scale_factor = target_length / current_length

        if scale_factor <= 0:
            return False, "缩放因子必须为正数"

        # 计算参考曲线的中心点（用于缩放中心）
        ref_points = self.curves[reference_curve_index]
        center_x = np.mean(ref_points[:, 0])
        center_y = np.mean(ref_points[:, 1])
        center = np.array([center_x, center_y])

        # 缩放所有曲线
        for i in range(len(self.curves)):
            # 将曲线点平移到中心点
            translated_points = self.curves[i] - center

            # 缩放曲线
            scaled_points = translated_points * scale_factor

            # 将曲线点平移回原位置
            self.curves[i] = scaled_points + center

        return True, f"成功缩放曲线，缩放因子: {scale_factor:.4f}"

    def reset_to_original_curves(self):
        """重置为原始曲线"""
        if len(self.original_curves) > 0:
            self.curves = [curve.copy() for curve in self.original_curves]
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
        self.curve_points = np.array(curve_points)
        self.discrete_curve = None
        self.pen_trace = None
        self.colors = []
        self.closure_ensured = False
        self.curvature_checked = False

        # 计算曲线总长度
        self.curve_length = 0
        for i in range(1, len(self.curve_points)):
            dx = self.curve_points[i, 0] - self.curve_points[i - 1, 0]
            dy = self.curve_points[i, 1] - self.curve_points[i - 1, 1]
            self.curve_length += hypot(dx, dy)

    def discrete_curve_by_chord_length(self, num_points=1000):
        """将曲线按等弦长离散化"""
        if self.curve_points is None or len(self.curve_points) < 2:
            return None

        # 计算曲线总长度
        total_length = 0
        lengths = [0]
        for i in range(1, len(self.curve_points)):
            dx = self.curve_points[i, 0] - self.curve_points[i - 1, 0]
            dy = self.curve_points[i, 1] - self.curve_points[i - 1, 1]
            segment_len = hypot(dx, dy)
            total_length += segment_len
            lengths.append(total_length)

        # 等弦长重新采样
        new_lengths = np.linspace(0, total_length, num_points)

        # 参数化插值
        t = np.array(lengths) / total_length
        x_spline = interpolate.CubicSpline(t, self.curve_points[:, 0])
        y_spline = interpolate.CubicSpline(t, self.curve_points[:, 1])

        t_new = new_lengths / total_length
        self.discrete_curve = np.column_stack([x_spline(t_new), y_spline(t_new)])
        return self.discrete_curve

    def calculate_curvature_radius(self, points, i):
        """计算曲线上第i点处的曲率半径"""
        n = len(points)

        if i == 0:
            p0, p1, p2 = points[0], points[1], points[2]
        elif i == n - 1:
            p0, p1, p2 = points[n - 3], points[n - 2], points[n - 1]
        else:
            p0, p1, p2 = points[i - 1], points[i], points[i + 1]

        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        d2x = dx2 - dx1
        d2y = dy2 - dy1

        dx = (dx1 + dx2) / 2
        dy = (dy1 + dy2) / 2

        denominator = (dx * dx + dy * dy) ** 1.5
        if denominator < 1e-10:
            return float('inf')

        curvature = abs(dx * d2y - dy * d2x) / denominator
        if curvature < 1e-10:
            return float('inf')

        return 1.0 / curvature

    def check_curvature_constraint(self, gear_radius):
        """检查曲率约束"""
        if self.discrete_curve is None:
            self.discrete_curve_by_chord_length(1000)

        n = len(self.discrete_curve)
        if n < 3:
            return True, 0, []

        min_radius = float('inf')
        problematic_points = []

        for i in range(n):
            radius = self.calculate_curvature_radius(self.discrete_curve, i)
            if radius < min_radius:
                min_radius = radius

            if radius < gear_radius * 1.1:
                problematic_points.append((i, radius))

        self.min_curvature_radius = min_radius
        self.curvature_checked = True

        if len(problematic_points) > 0:
            return False, min_radius, problematic_points
        else:
            return True, min_radius, []

    def calculate_gear_radius(self):
        """计算小圆半径"""
        return (self.gear_ratio_num / self.gear_ratio_den) * self.curve_length / (2 * pi)

    def calculate_pen_distance(self, gear_radius):
        """计算笔尖距离"""
        return (self.pen_position_num / self.pen_position_den) * gear_radius

    def find_optimal_gear_ratio(self, target_ratio):
        """找到最优齿轮比"""
        best_num, best_den = 1, 1
        best_error = float('inf')

        for den in range(1, 101):
            num = round(target_ratio * den)
            if num < 1:
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
        """生成HSV渐变颜色"""
        hue = cycle_count / total_cycles
        hue = hue % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return (r, g, b)

    def simulate_gear_motion(self, num_rotations=10):
        """模拟齿轮运动"""
        if self.curve_points is None:
            return None, [], False, 0

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

        pen_path = []
        current_angle = 0
        self.colors = []

        total_steps = int(adjusted_rotations * n)

        for step in range(total_steps):
            i = step % n
            next_i = (i + 1) % n

            current_point = self.discrete_curve[i]
            next_point = self.discrete_curve[next_i]

            tangent = next_point - current_point
            tangent_length = hypot(tangent[0], tangent[1])

            if tangent_length > 0:
                tangent = tangent / tangent_length
                normal = np.array([-tangent[1], tangent[0]])

                if self.rotation_direction == 1:
                    normal = -normal

                gear_center = current_point + normal * gear_radius
                rotation_angle = self.rotation_direction * tangent_length / gear_radius
                current_angle += rotation_angle

                pen_x = gear_center[0] + pen_distance * cos(current_angle)
                pen_y = gear_center[1] + pen_distance * sin(current_angle)

                pen_path.append([pen_x, pen_y])

                cycle_count = step / n
                color = self.hsv_color_gradient(cycle_count, adjusted_rotations)
                self.colors.append(color)

        self.pen_trace = np.array(pen_path)

        if len(self.pen_trace) > 1:
            start_point = self.pen_trace[0]
            end_point = self.pen_trace[-1]
            distance = math.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1])

            if distance < 0.001:
                print("图案闭合成功！")
                self.closure_ensured = True
            else:
                print(f"图案闭合误差: {distance:.6f}")
                self.closure_ensured = False

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
        self.root.title("任意曲线万花尺生成器（带曲线缩放功能）")
        self.root.geometry("1200x800")

        self.dxf_reader = DXFCurveReader()
        self.spirograph = ArbitrarySpirograph()
        self.current_curve_index = 0
        self.curve_colors = []
        self.curve_directions = {}

        self.setup_ui()
        self.update_status("请加载DXF文件")

    def setup_ui(self):
        """设置用户界面"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制面板（左侧）
        control_frame = tk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)

        # 文件操作
        file_frame = tk.LabelFrame(control_frame, text="文件操作", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(file_frame, text="加载DXF文件", command=self.load_dxf_file).pack(fill=tk.X)

        export_frame = tk.Frame(file_frame)
        export_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Button(export_frame, text="保存PNG", command=self.save_png, bg="lightgreen").pack(side=tk.LEFT, fill=tk.X,
                                                                                             expand=True)

        # 曲线信息
        info_frame = tk.LabelFrame(control_frame, text="曲线信息", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.curve_length_var = tk.StringVar(value="曲线长度: 未加载")
        tk.Label(info_frame, textvariable=self.curve_length_var).pack(anchor=tk.W)

        self.closure_status_var = tk.StringVar(value="闭合状态: 未生成")
        tk.Label(info_frame, textvariable=self.closure_status_var).pack(anchor=tk.W)

        self.curvature_status_var = tk.StringVar(value="曲率状态: 未检查")
        tk.Label(info_frame, textvariable=self.curvature_status_var).pack(anchor=tk.W)

        # 曲线缩放功能
        self.scale_frame = tk.LabelFrame(control_frame, text="曲线缩放", padx=10, pady=10)
        self.scale_frame.pack(fill=tk.X, pady=(0, 10))

        # 参考曲线选择
        ref_curve_frame = tk.Frame(self.scale_frame)
        ref_curve_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(ref_curve_frame, text="参考曲线:").pack(side=tk.LEFT)
        self.ref_curve_var = tk.StringVar(value="曲线1")
        self.ref_curve_combo = ttk.Combobox(ref_curve_frame, textvariable=self.ref_curve_var, state="readonly",
                                            width=10)
        self.ref_curve_combo.pack(side=tk.LEFT, padx=(5, 0))

        # 目标长度设置
        target_length_frame = tk.Frame(self.scale_frame)
        target_length_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(target_length_frame, text="目标长度:").pack(side=tk.LEFT)
        self.target_length_var = tk.DoubleVar(value=4415.04)
        tk.Entry(target_length_frame, textvariable=self.target_length_var, width=10).pack(side=tk.LEFT, padx=(5, 0))

        # 缩放按钮
        scale_button_frame = tk.Frame(self.scale_frame)
        scale_button_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Button(scale_button_frame, text="缩放曲线", command=self.scale_curves, bg="lightyellow").pack(side=tk.LEFT,
                                                                                                         fill=tk.X,
                                                                                                         expand=True)
        tk.Button(scale_button_frame, text="重置曲线", command=self.reset_curves, bg="lightcoral").pack(side=tk.LEFT,
                                                                                                        fill=tk.X,
                                                                                                        expand=True,
                                                                                                        padx=(5, 0))

        # 曲线选择
        self.curve_selector_frame = tk.LabelFrame(control_frame, text="曲线选择", padx=10, pady=10)
        self.curve_selector_frame.pack(fill=tk.X, pady=(0, 10))

        self.curve_var = tk.StringVar()
        self.curve_selector = ttk.Combobox(self.curve_selector_frame, textvariable=self.curve_var, state="readonly")
        self.curve_selector.pack(fill=tk.X)
        self.curve_selector.bind("<<ComboboxSelected>>", self.on_curve_selected)

        # 参数设置
        param_frame = tk.LabelFrame(control_frame, text="万花尺参数", padx=10, pady=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))

        # 齿轮比
        gear_frame = tk.Frame(param_frame)
        gear_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(gear_frame, text="齿轮比:").pack(side=tk.LEFT)
        self.gear_num_var = tk.IntVar(value=1)
        tk.Spinbox(gear_frame, from_=1, to=100, width=5, textvariable=self.gear_num_var).pack(side=tk.LEFT, padx=(5, 2))
        tk.Label(gear_frame, text="/").pack(side=tk.LEFT)
        self.gear_den_var = tk.IntVar(value=1)
        tk.Spinbox(gear_frame, from_=1, to=100, width=5, textvariable=self.gear_den_var).pack(side=tk.LEFT, padx=(2, 5))
        tk.Button(gear_frame, text="自动调整", command=self.auto_adjust_gear).pack(side=tk.LEFT, padx=(10, 0))

        # 笔尖位置
        pen_frame = tk.Frame(param_frame)
        pen_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(pen_frame, text="笔尖位置:").pack(side=tk.LEFT)
        self.pen_num_var = tk.IntVar(value=1)
        tk.Spinbox(pen_frame, from_=1, to=100, width=5, textvariable=self.pen_num_var).pack(side=tk.LEFT, padx=(5, 2))
        tk.Label(pen_frame, text="/").pack(side=tk.LEFT)
        self.pen_den_var = tk.IntVar(value=1)
        tk.Spinbox(pen_frame, from_=1, to=100, width=5, textvariable=self.pen_den_var).pack(side=tk.LEFT, padx=(2, 5))

        # 旋转设置
        rotate_frame = tk.Frame(param_frame)
        rotate_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(rotate_frame, text="旋转圈数:").pack(side=tk.LEFT)
        self.rotations_var = tk.IntVar(value=10)
        tk.Spinbox(rotate_frame, from_=1, to=100, textvariable=self.rotations_var, width=10).pack(side=tk.LEFT,
                                                                                                  padx=(10, 0))
        tk.Button(rotate_frame, text="自动设置完美圈数", command=self.auto_set_perfect_rotations).pack(side=tk.LEFT,
                                                                                                       padx=(10, 0))

        # 方向设置
        dir_frame = tk.Frame(param_frame)
        dir_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(dir_frame, text="方向:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value="内部")
        tk.Radiobutton(dir_frame, text="内部", variable=self.dir_var, value="内部").pack(side=tk.LEFT, padx=(10, 0))
        tk.Radiobutton(dir_frame, text="外部", variable=self.dir_var, value="外部").pack(side=tk.LEFT, padx=(10, 0))

        # 操作按钮
        button_frame = tk.Frame(param_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Button(button_frame, text="检查曲率", command=self.check_curvature, bg="lightcoral", height=2).pack(
            fill=tk.X, pady=(0, 5))
        tk.Button(button_frame, text="生成图案", command=self.generate_pattern, bg="lightblue", height=2).pack(
            fill=tk.X, pady=(0, 5))
        tk.Button(button_frame, text="清除", command=self.clear_pattern).pack(fill=tk.X)

        # 状态显示
        status_frame = tk.Frame(control_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

        # 图形显示区域
        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()

    def generate_curve_colors(self, num_curves):
        """生成曲线颜色列表"""
        colors = []
        for i in range(num_curves):
            hue = i / max(num_curves, 1)
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            colors.append((r, g, b))
        return colors

    def load_dxf_file(self):
        """加载DXF文件"""
        filename = filedialog.askopenfilename(
            title="选择DXF文件",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )

        if filename:
            self.update_status("正在读取DXF文件...")
            if self.dxf_reader.read_dxf(filename):
                curve_count = len(self.dxf_reader.curves)
                self.update_status(f"成功加载 {curve_count} 条曲线")

                if curve_count > 0:
                    # 生成曲线颜色
                    self.curve_colors = self.generate_curve_colors(curve_count)

                    # 初始化每条曲线的方向为内部
                    for i in range(curve_count):
                        self.curve_directions[i] = "内部"

                    # 更新曲线选择器
                    curves = [f"曲线 {i + 1}" for i in range(curve_count)]
                    self.curve_selector['values'] = curves
                    self.curve_selector.set(curves[0])
                    self.current_curve_index = 0

                    # 更新参考曲线选择器
                    self.ref_curve_combo['values'] = curves
                    self.ref_curve_combo.set(curves[0])

                    self.display_all_curves()
                    curve_length = self.dxf_reader.calculate_curve_length(0)
                    self.curve_length_var.set(f"曲线长度: {curve_length:.2f}")

                    # 显示曲线选择器
                    self.curve_selector_frame.pack(fill=tk.X, pady=(0, 10))
                    # 显示缩放功能
                    self.scale_frame.pack(fill=tk.X, pady=(0, 10))
                else:
                    self.curve_selector_frame.pack_forget()
                    self.scale_frame.pack_forget()
            else:
                messagebox.showerror("错误", "无法读取DXF文件")

    def scale_curves(self):
        """缩放曲线到目标长度"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "请先加载DXF文件")
            return

        try:
            # 获取参考曲线索引
            ref_curve_str = self.ref_curve_var.get()
            if not ref_curve_str.startswith("曲线 "):
                messagebox.showerror("错误", "请选择有效的参考曲线")
                return

            ref_curve_index = int(ref_curve_str.split(" ")[1]) - 1

            # 获取目标长度
            target_length = self.target_length_var.get()
            if target_length <= 0:
                messagebox.showerror("错误", "目标长度必须为正数")
                return

            # 执行缩放
            success, message = self.dxf_reader.scale_curves_to_target_length(ref_curve_index, target_length)

            if success:
                self.update_status(message)
                # 重新显示曲线
                self.display_all_curves()
                # 更新当前曲线长度显示
                curve_length = self.dxf_reader.calculate_curve_length(self.current_curve_index)
                self.curve_length_var.set(f"曲线长度: {curve_length:.2f}")
            else:
                messagebox.showerror("错误", message)

        except Exception as e:
            messagebox.showerror("错误", f"缩放曲线时出错: {str(e)}")

    def reset_curves(self):
        """重置曲线为原始状态"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "没有可重置的曲线")
            return

        success, message = self.dxf_reader.reset_to_original_curves()

        if success:
            self.update_status(message)
            # 重新显示曲线
            self.display_all_curves()
            # 更新当前曲线长度显示
            curve_length = self.dxf_reader.calculate_curve_length(self.current_curve_index)
            self.curve_length_var.set(f"曲线长度: {curve_length:.2f}")
        else:
            messagebox.showerror("错误", message)

    def display_all_curves(self):
        """显示所有曲线，每条用不同颜色"""
        if len(self.dxf_reader.curves) == 0:
            return

        self.ax.clear()

        # 绘制所有曲线
        for i, curve_points in enumerate(self.dxf_reader.curves):
            color = self.curve_colors[i] if i < len(self.curve_colors) else (1, 0, 0)
            label = f"曲线 {i + 1}"
            self.ax.plot(curve_points[:, 0], curve_points[:, 1], color=color, linewidth=2, label=label)

        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.legend()

        # 自动调整视图
        all_points = np.vstack(self.dxf_reader.curves)
        min_x, min_y = np.min(all_points, axis=0)
        max_x, max_y = np.max(all_points, axis=0)
        padding = max((max_x - min_x) * 0.1, (max_y - min_y) * 0.1, 1.0)
        self.ax.set_xlim(min_x - padding, max_x + padding)
        self.ax.set_ylim(min_y - padding, max_y + padding)

        self.canvas.draw()

        # 重置状态显示
        self.closure_status_var.set("闭合状态: 未生成图案")
        self.curvature_status_var.set("曲率状态: 未检查")

    def on_curve_selected(self, event):
        """当选择不同曲线时"""
        selected = self.curve_selector.get()
        if selected.startswith("曲线 "):
            self.current_curve_index = int(selected.split(" ")[1]) - 1

            # 更新曲线长度显示
            curve_length = self.dxf_reader.calculate_curve_length(self.current_curve_index)
            self.curve_length_var.set(f"曲线长度: {curve_length:.2f}")

    def auto_set_perfect_rotations(self):
        """自动设置完美圈数"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "请先加载DXF文件")
            return

        try:
            # 设置当前曲线
            curve_points = self.dxf_reader.curves[self.current_curve_index]
            self.spirograph.set_curve(curve_points)

            # 设置参数
            gear_num = self.gear_num_var.get()
            gear_den = self.gear_den_var.get()
            pen_num = self.pen_num_var.get()
            pen_den = self.pen_den_var.get()

            self.spirograph.set_parameters(gear_num, gear_den, pen_num, pen_den, 1)

            # 计算完美圈数
            perfect_rotations = self.spirograph.calculate_perfect_rotations()
            self.rotations_var.set(perfect_rotations)

            self.update_status(f"已自动设置为完美闭合圈数: {perfect_rotations}")

        except Exception as e:
            messagebox.showerror("错误", f"计算完美圈数时出错: {str(e)}")

    def check_curvature(self):
        """检查曲率"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "请先加载DXF文件")
            return

        try:
            # 设置当前曲线
            curve_points = self.dxf_reader.curves[self.current_curve_index]
            self.spirograph.set_curve(curve_points)

            # 设置参数
            gear_num = self.gear_num_var.get()
            gear_den = self.gear_den_var.get()
            pen_num = self.pen_num_var.get()
            pen_den = self.pen_den_var.get()
            direction = 1 if self.dir_var.get() == "内部" else -1

            self.spirograph.set_parameters(gear_num, gear_den, pen_num, pen_den, direction)

            # 计算齿轮半径
            gear_radius = self.spirograph.calculate_gear_radius()

            # 检查曲率
            curvature_ok, min_radius, problematic_points = self.spirograph.check_curvature_constraint(gear_radius)

            if curvature_ok:
                self.curvature_status_var.set(f"曲率状态: ✓ 半径{min_radius:.2f} > 齿轮{gear_radius:.2f}")
                self.update_status("曲率检查通过")
            else:
                self.curvature_status_var.set(f"曲率状态: ⚠ 半径{min_radius:.2f} < 齿轮{gear_radius:.2f}")
                self.update_status(f"曲率检查失败: {len(problematic_points)}个点不满足")

        except Exception as e:
            messagebox.showerror("错误", f"曲率检查时出错: {str(e)}")

    def generate_pattern(self):
        """生成图案"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "请先加载DXF文件")
            return

        self.update_status("正在生成图案...")

        try:
            # 设置当前曲线
            curve_points = self.dxf_reader.curves[self.current_curve_index]
            self.spirograph.set_curve(curve_points)

            # 设置参数
            gear_num = self.gear_num_var.get()
            gear_den = self.gear_den_var.get()
            pen_num = self.pen_num_var.get()
            pen_den = self.pen_den_var.get()
            rotations = self.rotations_var.get()
            direction = 1 if self.dir_var.get() == "内部" else -1

            self.spirograph.set_parameters(gear_num, gear_den, pen_num, pen_den, direction)

            # 生成图案
            pen_trace, colors, curvature_ok, min_radius = self.spirograph.simulate_gear_motion(rotations)

            if pen_trace is not None and len(colors) > 0:
                # 清空图形
                self.ax.clear()

                # 绘制所有原始曲线
                for i, curve_pts in enumerate(self.dxf_reader.curves):
                    curve_color = self.curve_colors[i] if i < len(self.curve_colors) else (1, 0, 0)
                    label = f"曲线 {i + 1}"
                    self.ax.plot(curve_pts[:, 0], curve_pts[:, 1], color=curve_color, linewidth=2, label=label)

                # 绘制万花尺图案
                for i in range(len(pen_trace) - 1):
                    x_values = [pen_trace[i, 0], pen_trace[i + 1, 0]]
                    y_values = [pen_trace[i, 1], pen_trace[i + 1, 1]]
                    self.ax.plot(x_values, y_values, color=colors[i], linewidth=0.5, alpha=0.7)

                # 添加图例
                self.ax.legend()
                self.ax.set_aspect('equal')
                self.ax.grid(True, linestyle='--', alpha=0.7)

                # 自动调整视图
                all_points = np.vstack(self.dxf_reader.curves)
                min_x, min_y = np.min(all_points, axis=0)
                max_x, max_y = np.max(all_points, axis=0)
                padding = max((max_x - min_x) * 0.1, (max_y - min_y) * 0.1, 1.0)
                self.ax.set_xlim(min_x - padding, max_x + padding)
                self.ax.set_ylim(min_y - padding, max_y + padding)

                self.canvas.draw()

                if self.spirograph.closure_ensured:
                    self.closure_status_var.set("闭合状态: ✓ 已闭合")
                else:
                    self.closure_status_var.set("闭合状态: ⚠ 有误差")

                self.update_status("图案生成完成")
            else:
                self.update_status("生成图案失败")

        except Exception as e:
            messagebox.showerror("错误", f"生成图案时出错: {str(e)}")

    def clear_pattern(self):
        """清除图案"""
        if len(self.dxf_reader.curves) > 0:
            self.display_all_curves()
        self.update_status("图案已清除")

    def save_png(self):
        """保存PNG图像"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "没有可保存的图像")
            return

        filename = filedialog.asksaveasfilename(
            title="保存PNG图像",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight',
                                 facecolor='white', edgecolor='none')
                self.update_status(f"图像已保存: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存图像失败: {str(e)}")

    def auto_adjust_gear(self):
        """自动调整齿轮比"""
        if len(self.dxf_reader.curves) == 0:
            messagebox.showwarning("警告", "请先加载DXF文件")
            return

        target_ratio = self.gear_num_var.get() / self.gear_den_var.get()
        num, den = self.spirograph.find_optimal_gear_ratio(target_ratio)

        self.gear_num_var.set(num)
        self.gear_den_var.set(den)
        self.update_status(f"齿轮比已调整为 {num}/{den}")

    def update_status(self, message):
        """更新状态"""
        self.status_var.set(message)
        self.root.update()


def main():
    """主函数"""
    root = tk.Tk()
    app = SpirographApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()