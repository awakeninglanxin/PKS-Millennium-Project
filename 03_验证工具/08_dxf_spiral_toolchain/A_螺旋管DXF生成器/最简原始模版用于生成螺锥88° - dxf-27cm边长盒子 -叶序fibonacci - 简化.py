import numpy as np
import ezdxf
import matplotlib.pyplot as plt
import json
import os
import math

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class SpiralSweepGenerator:
    def __init__(self, config_file=None):
        # 默认参数配置
        self.default_config = {
            "t_min": 0,
            "t_max": 1,
            "diameter": 250,#圆台锥底直径
            "pitch": 5,#锥螺距的一半
            "pitch_multi": 10,#锥螺线圈匝数
            "taper_angle": 44,#锥顶角度除以2的值
            "sign": 1,#1顺牙攻，-1反牙攻
            "num_t": 50,  # 设置默认值
            "output_file": "斜螺丝锥顶角88°加圆圈.dxf",
            "section_file": "三角牙82度.dxf",
            "triangle_size": 1,#扫掠断面大小
            "depth": 0,#攻牙向中轴的深度
            "twist_enabled": True,#断面扭转与锥倾斜角一致
            "dynamic_scaling": False,# 断面缩放开关
            "show_cone_vertex": True,# 是否显示锥形顶点和母线
            "calculate_optimal_pitch_multi": True,
            "enable_circles": True,
            "circle_radius": 0.8,
            "circle_dynamic_scaling": True,
            "circle_offset": 0, #举例：-3代表圆心沿表面向上偏移3mm
            "circle_segments": 16,
        }

        # 加载配置
        self.config = self.default_config.copy()
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")

        # 计算基本几何参数
        self.h = (self.config["pitch_multi"] + 2) * self.config["pitch"] * 2
        self.taper_ratio = math.tan(math.radians(self.config["taper_angle"]))

        # 基础参数
        self.t_min, self.t_max = self.config["t_min"], self.config["t_max"]
        self.pitch = self.config["pitch"]
        self.r = self.h * self.taper_ratio
        self.h_div_pitch = self.h * np.pi / self.pitch
        self.base_r = self.config["diameter"] / 2 + (self.pitch / self.h) * self.r

        # 其他参数
        self.num_t = self.config["num_t"]

        # 计算锥形顶点
        self.cone_vertex = (0, 0, self.base_r / self.taper_ratio)

        # 打印参数说明
        self.print_parameter_explanation()

        # 加载断面数据
        section_path = self.config["section_file"]
        if section_path and os.path.exists(section_path):
            self.load_section_data(section_path)
        else:
            print(f"警告: 断面文件 {section_path} 不存在")

        # 初始化t_spiral
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

    def generate_fibonacci_sequence(self, length, multi_val):
        """生成指定长度的Fibonacci数列"""
        if length <= 0:
            return []
        elif length == 1:
            return [2 * multi_val]  # 修正：乘以multi_val
        elif length == 2:
            return [2 * multi_val, 1 * multi_val]  # 修正：乘以multi_val

        # 从最小的合理值开始
        fib_seq = [2, 1]
        fib_seq_multi = []
        for i in range(2, length):
            next_val = fib_seq[i - 1] + fib_seq[i - 2]
            fib_seq.append(next_val)
        for i in fib_seq:
            fib_seq_multi.append(i * multi_val)
        return fib_seq_multi

    def adjust_to_total(self, sections, target_total):
        """调整截面数量，使总和精确等于目标值"""
        current_total = sum(sections)
        diff = target_total - current_total

        if diff == 0:
            return sections

        # 复制列表以避免修改原数据
        adjusted = sections.copy()

        if diff > 0:
            # 需要增加截面数量
            for i in range(diff):
                # 在截面数量最少的圈增加
                min_index = adjusted.index(min(adjusted))
                adjusted[min_index] += 1
        else:
            # 需要减少截面数量
            for i in range(abs(diff)):
                # 在截面数量最多的圈减少（但至少保留1个）
                max_index = adjusted.index(max(adjusted))
                if adjusted[max_index] > 1:
                    adjusted[max_index] -= 1

        return adjusted

    def generate_fibonacci_distribution(self):
        """生成非归一化的Fibonacci数列分布"""
        total_circles = self.config["pitch_multi"] + 2  # 总圈数
        fibonacci_length = total_circles  # 修复：Fibonacci数列长度应该等于总圈数

        # 生成Fibonacci数列 - 倍数参数直接影响最终截面数量
        fib_seq = self.generate_fibonacci_sequence(fibonacci_length, 1) #multi_val决定旋转断面每圈的阵列数量

        # 取所有数值作为各圈的截面数量
        circle_sections = fib_seq

        # 调整顺序使第1圈对应t=0，最后一圈对应t=1
        circle_sections = circle_sections[::-1]

        # 直接使用原始Fibonacci数列值，不进行归一化
        # 仅确保每个圈至少有1个截面
        adjusted_sections = [max(1, count) for count in circle_sections]

        # 打印各圈分布
        print("非归一化的各圈截面数量分布:")
        for i, count in enumerate(adjusted_sections):
            print(f"  第{i + 1}圈: {count}个截面")

        return adjusted_sections

    def calculate_spiral_coords(self):
        """按照Fibonacci数列分布计算螺旋线坐标"""
        # 生成各圈截面数量分布
        circle_sections = self.generate_fibonacci_distribution()

        # 计算实际使用的截面总数
        actual_num_t = sum(circle_sections)
        print(f"实际使用的截面总数: {actual_num_t} (由Fibonacci数列决定)")

        # 计算每圈的t值范围 - 修复：避免圈与圈之间产生重复断面
        t_values = []
        total_circles = len(circle_sections)

        for circle_idx, sections_count in enumerate(circle_sections):
            # 计算当前圈的t范围 (从0到1线性分布)
            t_start = circle_idx / total_circles
            t_end = (circle_idx + 1) / total_circles

            # 修复：使用endpoint=False避免在圈边界产生重复断面
            if circle_idx < total_circles - 1:
                # 非最后一圈：不包含结束点
                circle_t_values = np.linspace(t_start, t_end, sections_count, endpoint=False)
            else:
                # 最后一圈：包含结束点
                circle_t_values = np.linspace(t_start, t_end, sections_count, endpoint=True)

            t_values.extend(circle_t_values)

        # 更新t_spiral为计算出的非均匀分布值
        self.t_spiral = np.array(t_values)
        self.num_t = len(self.t_spiral)  # 更新实际控制点数量

        # 计算坐标
        effective_r = max(0.1, self.base_r - self.config["depth"])
        t = self.t_spiral

        x = (effective_r - t * self.r) * np.cos(t * self.h_div_pitch)
        y = (effective_r - t * self.r) * np.sin(t * self.h_div_pitch) * self.config["sign"]
        z = t * self.h

        return x, y, z

    def print_parameter_explanation(self):
        """打印参数说明"""
        print("\n=== 参数说明 ===")
        print(f"螺旋线总高度: {self.h:.2f} mm")
        print(f"锥角度: {self.config['taper_angle']}°")
        print(f"锥形顶点高度: {self.cone_vertex[2]:.2f} mm")
        print(f"总圈数: {self.config['pitch_multi'] + 2}")
        print(f"Fibonacci数列长度: {self.config['pitch_multi'] + 3}")
        print(f"总截面数量: {self.num_t}")
        print(f"圆圈功能: {'已启用（默认）' if self.config['enable_circles'] else '未启用'}")
        if self.config["enable_circles"]:
            print(f"圆圈半径: {self.config['circle_radius']} mm")
            print(f"圆圈偏移: {self.config['circle_offset']} mm")
            print(f"圆圈动态缩放: {'已启用' if self.config['circle_dynamic_scaling'] else '未启用'}")
        print("===============\n")

    def load_section_data(self, filepath):
        """加载断面DXF文件并生成圆圈点"""
        try:
            doc = ezdxf.readfile(filepath)
            points = []
            for entity in doc.modelspace():
                if entity.dxftype() == 'POINT':
                    points.append([entity.dxf.location.x, entity.dxf.location.y])

            if len(points) < 3:
                print("DXF文件中必须包含至少3个点")
                return

            points = np.array(points)

            # 应用缩放
            if self.config["triangle_size"] != 1.0:
                center = np.mean(points, axis=0)
                points = (points - center) * self.config["triangle_size"] + center

            # 确保断面闭合
            if not np.allclose(points[0], points[-1]):
                points = np.append(points, [points[0]], axis=0)

            self.section_points = points

            # 生成圆圈点
            self.generate_circle_points()

            print(f"成功加载断面文件: {filepath}")
        except Exception as e:
            print(f"加载断面文件时出错: {e}")

    def generate_circle_points(self):
        """在三角形中心生成圆圈点"""
        # 计算三角形中心
        center = np.mean(self.section_points, axis=0)

        # 获取第一个控制点
        first_point = self.section_points[0]

        # 计算初始角度
        dx = first_point[0] - center[0]
        dy = first_point[1] - center[1]
        start_angle = math.atan2(dy, dx)

        # 生成圆圈点
        circle_segments = self.config["circle_segments"]
        circle_points = []

        for i in range(circle_segments):
            angle = start_angle + 2 * math.pi * i / circle_segments
            x = center[0] + self.config["circle_radius"] * math.cos(angle)
            y = center[1] + self.config["circle_radius"] * math.sin(angle)
            circle_points.append([x, y])

        # 确保圆圈闭合
        if not np.allclose(circle_points[0], circle_points[-1]):
            circle_points.append(circle_points[0])

        self.circle_points = np.array(circle_points)
        print(f"生成圆圈点: {len(self.circle_points)} 个点")

    def generate_frenet_frame(self, x, y, z):
        """生成正确的Frenet标架 - 修复断面朝向问题"""
        n = len(x)
        T, N, B = [], [], []

        # 使用中心差分法计算更精确的导数
        dx = np.zeros(n)
        dy = np.zeros(n)
        dz = np.zeros(n)

        # 内部点使用中心差分
        for i in range(1, n - 1):
            dx[i] = (x[i + 1] - x[i - 1]) / 2.0
            dy[i] = (y[i + 1] - y[i - 1]) / 2.0
            dz[i] = (z[i + 1] - z[i - 1]) / 2.0

        # 边界点使用前向/后向差分
        dx[0], dy[0], dz[0] = x[1] - x[0], y[1] - y[0], z[1] - z[0]
        dx[-1], dy[-1], dz[-1] = x[-1] - x[-2], y[-1] - y[-2], z[-1] - z[-2]

        # 计算二阶导数（用于法向量）
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        ddz = np.gradient(dz)

        for i in range(n):
            # 切向量（单位化）
            T_vec = np.array([dx[i], dy[i], dz[i]])
            T_norm = np.linalg.norm(T_vec)
            if T_norm > 1e-10:
                T_vec = T_vec / T_norm
            else:
                # 避免零向量，使用默认方向
                T_vec = np.array([0, 0, 1])
            T.append(T_vec)

            # 法向量（使用改进的计算方法）
            if i == 0:
                # 第一个点：使用前向差分
                N_vec = np.array([ddx[1], ddy[1], ddz[1]])
            elif i == n - 1:
                # 最后一个点：使用后向差分
                N_vec = np.array([ddx[-2], ddy[-2], ddz[-2]])
            else:
                # 内部点：使用中心平均
                N_vec = np.array([(ddx[i - 1] + ddx[i] + ddx[i + 1]) / 3,
                                  (ddy[i - 1] + ddy[i] + ddy[i + 1]) / 3,
                                  (ddz[i - 1] + ddz[i] + ddz[i + 1]) / 3])

            N_norm = np.linalg.norm(N_vec)
            if N_norm > 1e-10:
                N_vec = N_vec / N_norm
            else:
                # 如果法向量太小，使用垂直于切向量的默认方向
                if abs(T_vec[2]) < 0.9:  # 不接近垂直方向
                    N_vec = np.array([-T_vec[1], T_vec[0], 0])
                else:
                    N_vec = np.array([1, 0, 0])
                N_norm = np.linalg.norm(N_vec)
                if N_norm > 0:
                    N_vec = N_vec / N_norm

            N.append(N_vec)

            # 副法向量（叉积）
            B_vec = np.cross(T_vec, N_vec)
            B_norm = np.linalg.norm(B_vec)
            if B_norm > 1e-10:
                B_vec = B_vec / B_norm
            else:
                # 如果叉积为零，构造垂直向量
                B_vec = np.cross(T_vec, np.array([0, 0, 1]))
                B_norm = np.linalg.norm(B_vec)
                if B_norm > 0:
                    B_vec = B_vec / B_norm
                else:
                    B_vec = np.array([1, 0, 0])

            B.append(B_vec)

            # 确保N与T垂直（Gram-Schmidt正交化）
            N_proj = np.dot(N_vec, T_vec) * T_vec
            N_corrected = N_vec - N_proj
            N_norm_corrected = np.linalg.norm(N_corrected)
            if N_norm_corrected > 1e-10:
                N[i] = N_corrected / N_norm_corrected
            else:
                # 如果校正后法向量太小，使用默认垂直方向
                if abs(T_vec[2]) < 0.9:
                    N[i] = np.array([-T_vec[1], T_vec[0], 0])
                    N_norm_temp = np.linalg.norm(N[i])
                    if N_norm_temp > 0:
                        N[i] = N[i] / N_norm_temp

            # 重新计算B确保正交
            B[i] = np.cross(T[i], N[i])
            B_norm_final = np.linalg.norm(B[i])
            if B_norm_final > 0:
                B[i] = B[i] / B_norm_final

        return np.array(T), np.array(N), np.array(B)

    def rotation_matrix(self, axis, angle):
        """绕轴旋转矩阵"""
        axis_norm = np.linalg.norm(axis)
        if axis_norm == 0:
            return np.eye(3)
        axis = axis / axis_norm
        x, y, z = axis
        K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
        return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K

    def calculate_optimal_pitch_multi_value(self):
        """计算螺旋线占满整个圆锥时的最佳pitch_multi值"""
        # 方法1: 基于圆锥高度计算
        h_cone = self.base_r / self.taper_ratio
        optimal_pitch_multi_by_height = h_cone / self.pitch

        # 方法2: 基于螺旋线长度计算
        L_cone = math.sqrt(h_cone ** 2 + self.base_r ** 2)
        R_avg = self.base_r / 2
        L_turn = math.sqrt(self.pitch ** 2 + (2 * math.pi * R_avg) ** 2)
        optimal_n_turns = L_cone / L_turn
        optimal_pitch_multi_by_length = optimal_n_turns

        # 方法3: 基于螺旋线覆盖圆锥表面积
        A_cone = math.pi * self.base_r * L_cone
        A_turn = self.pitch * 2 * math.pi * R_avg
        optimal_n_turns_by_area = A_cone / A_turn
        optimal_pitch_multi_by_area = optimal_n_turns_by_area

        # 返回三种方法的平均值，作为推荐值
        optimal_pitch_multi = (optimal_pitch_multi_by_height +
                               optimal_pitch_multi_by_length +
                               optimal_pitch_multi_by_area) / 3
        optimal_pitch_multi = max(1, optimal_pitch_multi) / 2
        return {
            "by_height": optimal_pitch_multi_by_height,
            "by_length": optimal_pitch_multi_by_length,
            "by_area": optimal_pitch_multi_by_area,
            "recommended": optimal_pitch_multi
        }

    def sweep_section(self):
        """生成扫掠断面和圆圈 - Fibonacci分布版本"""
        # 计算螺旋线坐标
        x, y, z = self.calculate_spiral_coords()
        T, N, B = self.generate_frenet_frame(x, y, z)

        swept_sections = []
        swept_circles = []
        egghead_points = []
        twist_angle = -math.radians(self.config["taper_angle"]) if self.config["twist_enabled"] else 0

        # 打印断面生成信息
        if self.config["dynamic_scaling"]:
            print("断面生成信息（动态缩放）:")
        else:
            print("断面生成信息（固定大小）:")

        # 生成Fibonacci分布
        circle_sections = self.generate_fibonacci_distribution()
        total_circles_count = len(circle_sections)

        # 计算每圈的t值范围
        t_per_circle = (self.t_max - self.t_min) / total_circles_count

        # 为每圈生成对应的截面索引
        section_indices = []
        current_index = 0
        for circle_idx, sections_count in enumerate(circle_sections):
            # 为当前圈生成均匀分布的索引
            indices = np.linspace(current_index, current_index + sections_count - 1, sections_count, dtype=int)
            section_indices.extend(indices)
            current_index += sections_count

        # 确保索引不越界
        section_indices = [min(idx, len(x) - 1) for idx in section_indices]

        # 统计信息
        total_sections = 0
        total_circles_generated = 0
        circle_generation_info = []

        # 生成截面
        for idx, i in enumerate(section_indices):
            section_points = []
            circle_points = []

            current_r = self.base_r - self.t_spiral[i] * self.r
            current_t = self.t_spiral[i]

            # 计算缩放比例
            scale = current_r / self.base_r if self.config["dynamic_scaling"] else 1.0
            circle_scale = current_r / self.base_r if self.config.get("circle_dynamic_scaling", True) else 1.0

            # 计算旋转矩阵
            R_twist = self.rotation_matrix(T[i], twist_angle)
            R_combined = self.rotation_matrix(T[i], 0) @ R_twist

            # 处理三角形断面
            for j in range(len(self.section_points)):
                x_val = self.section_points[j][0] * self.pitch * scale
                y_val = self.section_points[j][1] * self.pitch * scale
                vector = R_combined @ (y_val * N[i] + x_val * B[i])
                point = [x[i] + vector[0], y[i] + vector[1], z[i] + vector[2]]
                section_points.append(point)

                # 记录蛋尖点
                if j == 0:
                    egghead_points.append(point)

            swept_sections.append(section_points)
            total_sections += 1

            # 判断是否生成圆圈：只在中间圈数生成，首尾两圈不生成
            should_generate_circle = True
            circle_reason = ""

            # 计算当前点所在的圈数
            current_circle = int(current_t / t_per_circle) + 1

            if current_circle <= 1:  # 第一圈
                should_generate_circle = False
                circle_reason = "首圈跳过"
            elif current_circle >= total_circles_count:  # 最后一圈
                should_generate_circle = False
                circle_reason = "尾圈跳过"
            elif current_t < 0.05 or current_t > 0.95:  # 首尾5%区域
                should_generate_circle = False
                circle_reason = "首尾区域跳过"

            # 处理圆圈（如果启用且符合条件）
            if self.config.get("enable_circles", True) and should_generate_circle:
                for j in range(len(self.circle_points)):
                    x_val = self.circle_points[j][0] * self.pitch * circle_scale
                    y_val = self.circle_points[j][1] * self.pitch
                    vector = R_combined @ (y_val * B[i] + x_val * T[i])

                    # 计算法向量
                    if len(section_points) >= 3:
                        p1, p2, p3 = section_points[0], section_points[1], section_points[2]
                        v1 = np.array(p2) - np.array(p1)
                        v2 = np.array(p3) - np.array(p1)
                        normal = np.cross(v1, v2)
                        section_center = np.mean(section_points, axis=0)
                        v3 = np.array(p1) - np.array(section_center)
                        v3_norm = np.linalg.norm(v3)
                        if v3_norm > 0:
                            v3 = v3 / v3_norm
                            R_rotate = self.rotation_matrix(v3, math.pi / 2)
                            normal = R_rotate @ normal
                        normal_norm = np.linalg.norm(normal)
                        if normal_norm > 0:
                            normal = normal / normal_norm
                        else:
                            normal = T[i]
                    else:
                        normal = T[i]

                    # 应用圆圈偏移
                    circle_offset = self.config.get("circle_offset", 0.0)
                    circle_offset_vector = normal * circle_offset
                    point = [x[i] + vector[0] + circle_offset_vector[0],
                             y[i] + vector[1] + circle_offset_vector[1],
                             z[i] + vector[2] + circle_offset_vector[2]]
                    circle_points.append(point)

                swept_circles.append(circle_points)
                total_circles_generated += 1
                circle_generation_info.append(f"点{i}: 圈{current_circle}, t={current_t:.3f}, 半径={current_r:.1f}mm")
            else:
                swept_circles.append([])  # 添加空列表保持索引一致
                if circle_reason:
                    circle_generation_info.append(f"点{i}: 圈{current_circle}, t={current_t:.3f} - {circle_reason}")

            # 只打印第一个和最后一个点的信息
            if idx == 0 or idx == len(section_indices) - 1:
                circle_status = "生成圆圈" if should_generate_circle else f"未生成({circle_reason})"
                if self.config["dynamic_scaling"]:
                    print(f"点 {i:3d}: 圈{current_circle}, t={current_t:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放={scale:.3f}, 扭转角度={math.degrees(twist_angle):.2f}°, 圆圈:{circle_status}")
                else:
                    print(f"点 {i:3d}: 圈{current_circle}, t={current_t:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放=1.000(固定), 扭转角度={math.degrees(twist_angle):.2f}°, 圆圈:{circle_status}")

        center_points = [[x[i], y[i], z[i]] for i in range(len(x))]

        # 打印详细的圆圈生成统计
        print(f"\n=== 圆圈生成统计 ===")
        print(f"总断面数量: {total_sections}")
        print(f"总圈数: {total_circles_count}")
        print(f"生成圆圈数量: {total_circles_generated}")
        print(f"圆圈生成率: {total_circles_generated / total_sections * 100:.1f}%")

        # 按圈数统计圆圈生成情况
        circle_stats = {}
        for info in circle_generation_info:
            if "圈" in info:
                circle_num = int(info.split("圈")[1].split(",")[0])
                if circle_num not in circle_stats:
                    circle_stats[circle_num] = {"total": 0, "generated": 0}
                circle_stats[circle_num]["total"] += 1
                if "生成圆圈" in info:
                    circle_stats[circle_num]["generated"] += 1

        print("\n各圈圆圈生成情况:")
        for circle_num in sorted(circle_stats.keys()):
            stats = circle_stats[circle_num]
            rate = stats["generated"] / stats["total"] * 100 if stats["total"] > 0 else 0
            status = "全部生成" if rate == 100 else "部分生成" if rate > 0 else "未生成"
            print(f"  圈{circle_num}: {stats['generated']}/{stats['total']} ({rate:.1f}%) - {status}")

        return swept_sections, center_points, swept_circles, egghead_points

    def save_to_dxf(self, filename=None):
        """保存为DXF文件 - Fibonacci分布版本"""
        output_file = filename or self.config["output_file"]
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, swept_circles, egghead_points = self.sweep_section()

        # 添加锥形顶点到DXF
        if self.config.get("show_cone_vertex", True) and hasattr(self, 'cone_vertex'):
            try:
                msp.add_point(self.cone_vertex, dxfattribs={'color': 7, 'layer': 'CONE_VERTEX'})
                print(f"锥形顶点已添加到DXF: {self.cone_vertex}")
            except Exception as e:
                print(f"添加锥形顶点时出错: {e}")

        # 添加中心螺旋线
        if len(center_points) > 1:
            try:
                msp.add_spline(center_points).dxf.color = 1
            except Exception as e:
                print(f"添加中心螺旋线时出错: {e}")

        # 添加蛋尖螺旋线
        if len(egghead_points) > 1:
            try:
                msp.add_spline(egghead_points).dxf.color = 5
                print(f"蛋尖螺旋线已添加到DXF，包含 {len(egghead_points)} 个点")
            except Exception as e:
                print(f"添加蛋尖螺旋线时出错: {e}")

        # 添加扫掠断面
        sections_added = 0
        for i, section in enumerate(swept_sections):
            if len(section) > 2:
                try:
                    polyline = msp.add_polyline3d(section)
                    polyline.close(True)
                    polyline.dxf.color = 3
                    sections_added += 1
                except Exception as e:
                    print(f"添加断面 {i} 时出错: {e}")

        # 添加圆圈（只添加非空的圆圈）
        circles_added = 0
        circle_circle_stats = {}  # 统计各圈的圆圈数量
        circle_start_index = None
        circle_end_index = None

        for i, circle in enumerate(swept_circles):
            if len(circle) > 2:  # 只处理非空圆圈
                try:
                    spline = msp.add_spline(circle)
                    spline.dxf.color = 4
                    circles_added += 1

                    # 记录圆圈的开始和结束索引
                    if circle_start_index is None:
                        circle_start_index = i
                    circle_end_index = i

                    # 统计圈数信息
                    current_t = self.t_spiral[i]
                    total_circles = len(self.generate_fibonacci_distribution())
                    current_circle = int(current_t * total_circles) + 1
                    if current_circle not in circle_circle_stats:
                        circle_circle_stats[current_circle] = 0
                    circle_circle_stats[current_circle] += 1

                except Exception as e:
                    if i < 3:
                        print(f"添加圆圈 {i} 时出错: {e}")

        print(f"成功添加 {sections_added} 个扫掠断面")
        print(f"成功添加 {circles_added} 个圆圈")

        # 打印详细的圆圈分布信息
        if circle_circle_stats:
            print("\n=== 圆圈分布统计 ===")
            print("各圈圆圈数量分布:")
            total_circles_count = len(self.generate_fibonacci_distribution())
            circles_with_circles = 0
            circles_without_circles = 0

            for circle_num in range(1, total_circles_count + 1):
                if circle_num in circle_circle_stats:
                    count = circle_circle_stats[circle_num]
                    print(f"  圈{circle_num}: {count}个圆圈")
                    circles_with_circles += 1
                else:
                    if circle_num == 1:
                        print(f"  圈{circle_num}: 0个圆圈 (首圈跳过)")
                    elif circle_num == total_circles_count:
                        print(f"  圈{circle_num}: 0个圆圈 (尾圈跳过)")
                    else:
                        print(f"  圈{circle_num}: 0个圆圈")
                    circles_without_circles += 1

            print(f"\n圆圈覆盖圈数: {circles_with_circles}/{total_circles_count}")
            print(f"圆圈覆盖率: {circles_with_circles / total_circles_count * 100:.1f}%")

            if circle_start_index is not None and circle_end_index is not None:
                start_t = self.t_spiral[circle_start_index]
                end_t = self.t_spiral[circle_end_index]
                start_circle = int(start_t * total_circles_count) + 1
                end_circle = int(end_t * total_circles_count) + 1
                print(f"圆圈分布范围: 圈{start_circle} 到 圈{end_circle}")
                print(f"参数t范围: {start_t:.3f} 到 {end_t:.3f}")

        # 添加端面圆
        if len(center_points) > 1:
            try:
                start_z, end_z = self.pitch * 2, self.h - self.pitch * 2
                z_coords = [p[2] for p in center_points]
                start_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - start_z))
                end_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - end_z))
                t_start, t_end = self.t_spiral[start_idx], self.t_spiral[end_idx]
                r_start = max(0.1, self.base_r - t_start * self.r)
                r_end = max(0.1, self.base_r - t_end * self.r)
                if r_start > 0:
                    msp.add_circle(center=(0, 0, start_z), radius=r_start).dxf.color = 7
                if r_end > 0:
                    msp.add_circle(center=(0, 0, end_z), radius=r_end).dxf.color = 7

                print(f"底部端面圆: 高度={start_z:.2f}mm, 半径={r_start:.2f}mm")
                print(f"顶部端面圆: 高度={end_z:.2f}mm, 半径={r_end:.2f}mm")
            except Exception as e:
                print(f"添加端面圆时出错: {e}")

        # 添加锥形母线
        if self.config.get("show_cone_vertex", True) and hasattr(self, 'cone_vertex'):
            try:
                num_generatrices = 4
                generatrices_added = 0
                for i in range(num_generatrices):
                    angle = 2 * math.pi * i / num_generatrices
                    x_end = self.base_r * math.cos(angle)
                    y_end = self.base_r * math.sin(angle) * self.config.get("sign", 1)
                    z_end = 0

                    msp.add_line(self.cone_vertex, (x_end, y_end, z_end),
                                 dxfattribs={'color': 6, 'linetype': 'DASHED', 'layer': 'CONE_GENERATRIX'})
                    generatrices_added += 1

                print(f"添加了 {generatrices_added} 条锥形母线")
            except Exception as e:
                print(f"添加锥形母线时出错: {e}")

        # 保存文件
        try:
            doc.saveas(output_file)
            print(f"\n✅ 成功保存到 {output_file}")
        except Exception as e:
            print(f"❌ 保存文件时出错: {e}")

        # 打印最终统计信息
        print(f"\n=== Fibonacci分布完成统计 ===")
        print(f"分布模式: Fibonacci数列分布")
        print(f"总圈数: {len(self.generate_fibonacci_distribution())}")
        print(f"总控制点数: {len(swept_sections)}")
        print(f"生成圆圈数: {circles_added}")
        print(f"圆圈生成率: {circles_added / len(swept_sections) * 100:.1f}%")

        # Fibonacci分布特有信息
        fib_sequence = self.generate_fibonacci_distribution()
        print(f"Fibonacci数列: {fib_sequence}")
        print(f"各圈截面分布:")
        for i, count in enumerate(fib_sequence):
            circle_status = "有圆圈" if (i + 1) in circle_circle_stats else "无圆圈"
            if i == 0:
                circle_status = "首圈(无圆圈)"
            elif i == len(fib_sequence) - 1:
                circle_status = "尾圈(无圆圈)"
            print(f"  圈{i + 1}: {count}个截面 - {circle_status}")

        print(f"断面扭转: {'已启用' if self.config['twist_enabled'] else '未启用'}")
        print(f"动态缩放: {'已启用' if self.config['dynamic_scaling'] else '未启用'}")
        print(f"圆圈偏移: {self.config.get('circle_offset', 0.0)}mm")
        print(f"圆圈动态缩放: {'已启用' if self.config.get('circle_dynamic_scaling', True) else '未启用'}")

        if self.config.get("show_cone_vertex", True):
            print(f"锥形顶点: (0, 0, {self.cone_vertex[2]:.2f})")

        if self.config.get("calculate_optimal_pitch_multi", True):
            optimal_info = self.calculate_optimal_pitch_multi_value()
            print(f"推荐pitch_multi: {optimal_info['recommended']:.2f}")

        # 打印文件大小信息
        try:
            file_size = os.path.getsize(output_file)
            print(f"生成文件大小: {file_size / 1024:.1f} KB")
        except:
            pass

        print("=" * 50)

# 在main函数中使用
def main():
    generator = SpiralSweepGenerator()
    generator.save_to_dxf("塔锥Fibonacci分布.dxf")


if __name__ == "__main__":
    main()
