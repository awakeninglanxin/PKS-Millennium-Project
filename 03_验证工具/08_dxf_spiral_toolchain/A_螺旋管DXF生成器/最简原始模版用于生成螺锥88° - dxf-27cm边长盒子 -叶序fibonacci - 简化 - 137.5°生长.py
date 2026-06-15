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
            "diameter": 250,  # 圆台锥底直径
            "pitch": 5,  # 锥螺距的一半
            "pitch_multi": 10,  # 锥螺线圈匝数
            "taper_angle": 44,  # 锥顶角度除以2的值
            "sign": 1,  # 1顺牙攻，-1反牙攻
            "num_t": 432,  # 设置默认值（向日葵需要更多点）
            "output_file": "向日葵螺旋分布.dxf",
            "section_file": "三角牙82度.dxf",
            "triangle_size": 1,  # 扫掠断面大小
            "depth": 0,  # 攻牙向中轴的深度
            "twist_enabled": True,  # 断面扭转与锥倾斜角一致
            "dynamic_scaling": False,  # 断面缩放开关
            "show_cone_vertex": True,  # 是否显示锥形顶点和母线
            "calculate_optimal_pitch_multi": True,
            "enable_circles": True,
            "circle_radius": 0.8,
            "circle_dynamic_scaling": True,
            "circle_offset": 0,  # 举例：-3代表圆心沿表面向上偏移3mm
            "circle_segments": 16,
            "golden_angle": 137.5,  # 黄金角度（向日葵种子角度）
            "sunflower_mode": True,  # 启用向日葵模式
            "sunflower_c": 1.0,  # 向日葵分布的密度参数
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

        # 黄金角度（弧度）
        self.golden_angle_rad = math.radians(self.config["golden_angle"])

        # 打印参数说明
        self.print_parameter_explanation()

        # 加载断面数据
        section_path = self.config["section_file"]
        if section_path and os.path.exists(section_path):
            self.load_section_data(section_path)
        else:
            print(f"警告: 断面文件 {section_path} 不存在")

        # 初始化t_spiral
        self.t_spiral = self.generate_sunflower_distribution()

    def generate_sunflower_distribution(self):
        """生成向日葵种子式的黄金角分布"""
        print("使用向日葵种子分布模式（黄金角137.5°）")

        n = self.config["num_t"]
        c = self.config["sunflower_c"]  # 密度参数

        indices = np.arange(1, n + 1)

        # 向日葵种子分布公式
        r = np.sqrt(indices - 0.5) / np.sqrt(n - 0.5)  # 半径从0到1
        theta = indices * self.golden_angle_rad  # 黄金角累积

        # 将极坐标映射到t值
        t_values = r

        print(f"生成的向日葵分布点数: {n}")
        print(f"黄金角度: {self.config['golden_angle']}°")
        print(f"密度参数c: {c}")

        return t_values

    def calculate_spiral_coords(self):
        """按照向日葵分布计算螺旋线坐标"""
        t = self.t_spiral

        # 计算坐标
        effective_r = max(0.1, self.base_r - self.config["depth"])

        # 使用向日葵分布的角度
        n = len(t)
        indices = np.arange(1, n + 1)
        theta = indices * self.golden_angle_rad * self.config["sign"]

        # 计算半径和高度
        r_values = effective_r - t * self.r
        z_values = t * self.h

        # 计算笛卡尔坐标
        x = r_values * np.cos(theta)
        y = r_values * np.sin(theta)
        z = z_values

        # 打印分布信息
        print(f"向日葵分布统计:")
        print(f"  总点数: {n}")
        print(f"  t范围: [{t.min():.3f}, {t.max():.3f}]")
        print(f"  半径范围: [{r_values.min():.3f}, {r_values.max():.3f}]")
        print(f"  高度范围: [{z_values.min():.3f}, {z_values.max():.3f}]")
        print(f"  角度范围: [{theta.min():.3f}, {theta.max():.3f}] 弧度")

        return x, y, z

    def print_parameter_explanation(self):
        """打印参数说明"""
        print("\n=== 参数说明 ===")
        print(f"螺旋线总高度: {self.h:.2f} mm")
        print(f"锥角度: {self.config['taper_angle']}°")
        print(f"锥形顶点高度: {self.cone_vertex[2]:.2f} mm")
        print(f"分布模式: {'向日葵黄金角分布' if self.config['sunflower_mode'] else 'Fibonacci分布'}")
        if self.config["sunflower_mode"]:
            print(f"黄金角度: {self.config['golden_angle']}°")
            print(f"密度参数: {self.config['sunflower_c']}")
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
        """生成正确的Frenet标架 - 针对向日葵分布优化"""
        n = len(x)
        T, N, B = [], [], []

        # 使用中心差分法计算导数
        dx = np.gradient(x)
        dy = np.gradient(y)
        dz = np.gradient(z)

        # 计算二阶导数
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
                T_vec = np.array([0, 0, 1])
            T.append(T_vec)

            # 法向量
            N_vec = np.array([ddx[i], ddy[i], ddz[i]])
            N_norm = np.linalg.norm(N_vec)
            if N_norm > 1e-10:
                N_vec = N_vec / N_norm
            else:
                # 如果法向量太小，使用垂直于切向量的默认方向
                if abs(T_vec[2]) < 0.9:
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
                B_vec = np.cross(T_vec, np.array([0, 0, 1]))
                B_norm = np.linalg.norm(B_vec)
                if B_norm > 0:
                    B_vec = B_vec / B_norm
                else:
                    B_vec = np.array([1, 0, 0])

            B.append(B_vec)

            # Gram-Schmidt正交化
            N_proj = np.dot(N_vec, T_vec) * T_vec
            N_corrected = N_vec - N_proj
            N_norm_corrected = np.linalg.norm(N_corrected)
            if N_norm_corrected > 1e-10:
                N[i] = N_corrected / N_norm_corrected
            else:
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
        h_cone = self.base_r / self.taper_ratio
        optimal_pitch_multi_by_height = h_cone / self.pitch

        L_cone = math.sqrt(h_cone ** 2 + self.base_r ** 2)
        R_avg = self.base_r / 2
        L_turn = math.sqrt(self.pitch ** 2 + (2 * math.pi * R_avg) ** 2)
        optimal_n_turns = L_cone / L_turn
        optimal_pitch_multi_by_length = optimal_n_turns

        A_cone = math.pi * self.base_r * L_cone
        A_turn = self.pitch * 2 * math.pi * R_avg
        optimal_n_turns_by_area = A_cone / A_turn
        optimal_pitch_multi_by_area = optimal_n_turns_by_area

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
        """生成扫掠断面和圆圈 - 向日葵分布版本"""
        # 计算螺旋线坐标
        x, y, z = self.calculate_spiral_coords()
        T, N, B = self.generate_frenet_frame(x, y, z)

        swept_sections = []
        swept_circles = []
        egghead_points = []
        twist_angle = -math.radians(self.config["taper_angle"]) if self.config["twist_enabled"] else 0

        print("向日葵分布断面生成信息:")
        print(f"使用黄金角: {self.config['golden_angle']}°")

        # 生成向日葵分布的点
        n = len(x)

        # 统计信息
        total_sections = 0
        total_circles = 0
        circle_generation_info = []

        for i in range(n):
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

            # 判断是否生成圆圈：只在中间部分生成，首尾两圈不生成
            should_generate_circle = True
            circle_reason = ""

            # 计算当前点所在的圈数（基于t值）
            total_circles_approx = self.config["pitch_multi"] + 2
            current_circle = int(current_t * total_circles_approx) + 1

            if current_circle <= 1:  # 第一圈
                should_generate_circle = False
                circle_reason = "首圈跳过"
            elif current_circle >= total_circles_approx:  # 最后一圈
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
                total_circles += 1
                circle_generation_info.append(f"点{i}: 圈{current_circle}, t={current_t:.3f}, 半径={current_r:.1f}mm")
            else:
                swept_circles.append([])  # 添加空列表保持索引一致
                if circle_reason:
                    circle_generation_info.append(f"点{i}: 圈{current_circle}, t={current_t:.3f} - {circle_reason}")

            # 打印第一个和最后一个点的信息
            if i == 0 or i == n - 1:
                angle_deg = (i + 1) * self.config["golden_angle"] % 360
                circle_status = "生成圆圈" if should_generate_circle else f"未生成({circle_reason})"
                if self.config["dynamic_scaling"]:
                    print(f"点 {i:3d}: 圈{current_circle}, 角度={angle_deg:6.1f}°, 半径={current_r:6.2f}mm, "
                          f"缩放={scale:.3f}, 圆圈:{circle_status}")
                else:
                    print(f"点 {i:3d}: 圈{current_circle}, 角度={angle_deg:6.1f}°, 半径={current_r:6.2f}mm, "
                          f"缩放=1.000(固定), 圆圈:{circle_status}")

        center_points = [[x[i], y[i], z[i]] for i in range(len(x))]

        # 打印详细的圆圈生成统计
        print(f"\n=== 圆圈生成统计 ===")
        print(f"总断面数量: {total_sections}")
        print(f"生成圆圈数量: {total_circles}")
        print(f"圆圈生成率: {total_circles / total_sections * 100:.1f}%")

        # 打印前5个和后5个圆圈生成信息
        print("\n圆圈生成详情（抽样）:")
        if len(circle_generation_info) > 10:
            for info in circle_generation_info[:5]:
                print(f"  {info}")
            print("  ...")
            for info in circle_generation_info[-5:]:
                print(f"  {info}")
        else:
            for info in circle_generation_info:
                print(f"  {info}")

        return swept_sections, center_points, swept_circles, egghead_points

    def save_to_dxf(self, filename=None):
        """保存为DXF文件 - 向日葵分布版本"""
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
        circle_indices = []
        for i, circle in enumerate(swept_circles):
            if len(circle) > 2:  # 只处理非空圆圈
                try:
                    spline = msp.add_spline(circle)
                    spline.dxf.color = 4
                    circles_added += 1
                    circle_indices.append(i)
                except Exception as e:
                    if i < 3:
                        print(f"添加圆圈 {i} 时出错: {e}")

        print(f"成功添加 {sections_added} 个扫掠断面")
        print(f"成功添加 {circles_added} 个圆圈")
        if circle_indices:
            print(f"圆圈分布范围: 点{circle_indices[0]} 到 点{circle_indices[-1]}")

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
                num_generatrices = 8
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
            print(f"成功保存到 {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")

        # 打印最终统计信息
        print(f"\n=== 向日葵分布完成统计 ===")
        print(f"分布模式: 黄金角 {self.config['golden_angle']}°")
        print(f"总控制点数: {len(swept_sections)}")
        print(f"生成圆圈数: {circles_added}")
        print(f"圆圈覆盖率: {circles_added / len(swept_sections) * 100:.1f}%")
        print(f"断面扭转: {'已启用' if self.config['twist_enabled'] else '未启用'}")
        print(f"动态缩放: {'已启用' if self.config['dynamic_scaling'] else '未启用'}")
        print(f"圆圈偏移: {self.config.get('circle_offset', 0.0)}mm")

        if self.config.get("show_cone_vertex", True):
            print(f"锥形顶点: (0, 0, {self.cone_vertex[2]:.2f})")

def main():
    generator = SpiralSweepGenerator()
    generator.save_to_dxf("向日葵黄金角分布.dxf")


if __name__ == "__main__":
    main()