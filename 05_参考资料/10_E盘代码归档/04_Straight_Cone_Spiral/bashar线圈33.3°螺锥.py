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
            "diameter": 293.62+16.558*2,#圆台锥底直径
            "pitch": 22,#锥垂直螺距的一半
            "pitch_multi":10,#锥螺线圈匝数
            "taper_angle": 33.3/2,#锥顶角度除以2的值,锥面角
            "sign": 1,#1顺牙攻，-1反牙攻
            "num_t": 150,  # 设置默认值
            "output_file": "斜螺丝锥顶角90°加圆圈.dxf",
            "section_file": "三角牙82度.dxf",
            "triangle_size": 1,#扫掠断面大小
            "depth": 0,#攻牙向中轴的深度
            "twist_enabled": True,#断面扭转与锥倾斜角一致
            "dynamic_scaling": False,# 断面缩放开关
            "show_cone_vertex": True,# 是否显示锥形顶点和母线
            "calculate_optimal_pitch_multi": True,
            "enable_circles": True,
            "circle_radius": 0.9,
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
        self.base_r =self.config["diameter"] / 2 + 2*self.pitch* self.taper_ratio

        # 其他参数
        self.num_t = self.config["num_t"] + 1
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

        # 初始化t_spiral - 使用线性分布
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

    def calculate_spiral_coords(self):
        """计算螺旋线坐标 - 使用线性分布的t值"""
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
        print(f"控制点数量: {self.num_t}")
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
        """生成Frenet标架"""
        dx, dy, dz = np.gradient(x), np.gradient(y), np.gradient(z)
        ddx, ddy, ddz = np.gradient(dx), np.gradient(dy), np.gradient(dz)

        T, N, B = [], [], []
        for i in range(len(x)):
            T_vec = np.array([dx[i], dy[i], dz[i]])
            T_norm = np.linalg.norm(T_vec)
            T.append(T_vec / T_norm if T_norm > 0 else T_vec)

            N_vec = np.array([ddx[i], ddy[i], ddz[i]])
            N_norm = np.linalg.norm(N_vec)
            N.append(N_vec / N_norm if N_norm > 0 else N_vec)

            B_vec = np.cross(T[i], N[i])
            B_norm = np.linalg.norm(B_vec)
            B.append(B_vec / B_norm if B_norm > 0 else B_vec)

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
        """生成扫掠断面和圆圈"""
        # 计算螺旋线坐标
        x, y, z = self.calculate_spiral_coords()
        T, N, B = self.generate_frenet_frame(x, y, z)

        swept_sections = []
        swept_circles = []
        egghead_points = []  # 新增：蛋尖螺旋线点集合
        twist_angle = -math.radians(self.config["taper_angle"]) if self.config["twist_enabled"] else 0

        # 打印断面生成信息
        if self.config["dynamic_scaling"]:
            print("断面生成信息（动态缩放）:")
        else:
            print("断面生成信息（固定大小）:")

        # 使用线性分布的截面索引
        section_indices = list(range(len(x)))

        # 计算总圈数
        total_circles = self.config["pitch_multi"] + 2

        # 计算每圈包含的截面数量（近似值）
        sections_per_circle = len(x) // total_circles

        # 计算第二圈开始和倒数第二圈结束的索引范围
        start_circle_index = 1  # 第二圈（从0开始计数）
        end_circle_index = total_circles - 2  # 倒数第二圈

        circle_start_index = start_circle_index * sections_per_circle
        circle_end_index = (end_circle_index + 1) * sections_per_circle

        # 确保索引不越界
        circle_start_index = min(circle_start_index, len(x) - 1)
        circle_end_index = min(circle_end_index, len(x))

        print(f"圆圈扫掠范围: 第{start_circle_index + 1}圈到第{end_circle_index + 1}圈")
        print(f"索引范围: {circle_start_index} 到 {circle_end_index - 1}")
        print(f"圆圈扫掠截面数量: {circle_end_index - circle_start_index}")

        # 生成截面
        for idx, i in enumerate(section_indices):
            section_points = []
            circle_points = []

            current_r = self.base_r - self.t_spiral[i] * self.r

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

                # 新增：如果是第一个点，添加到egghead_points
                if j == 0:
                    egghead_points.append(point)

            swept_sections.append(section_points)

            # 处理圆圈（如果启用）- 只在第二圈到倒数第二圈之间生成
            if (self.config.get("enable_circles", True) and
                    circle_start_index <= i < circle_end_index):

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
            else:
                # 不在圆圈扫掠范围内的截面，添加空列表
                swept_circles.append([])

            # 只打印第一个和最后一个点的信息
            if idx == 0 or idx == len(section_indices) - 1:
                if self.config["dynamic_scaling"]:
                    print(f"点 {i:3d}: t={self.t_spiral[i]:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放比例={scale:.3f}, 扭转角度={math.degrees(twist_angle):.2f}°")
                else:
                    print(f"点 {i:3d}: t={self.t_spiral[i]:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放比例=1.000(固定), 扭转角度={math.degrees(twist_angle):.2f}°")

        center_points = [[x[i], y[i], z[i]] for i in range(len(x))]
        return swept_sections, center_points, swept_circles, egghead_points

    def save_to_dxf(self, filename=None):
        """保存为DXF文件"""
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
        print(f"成功添加 {sections_added} 个扫掠断面")

        # 计算总圈数和每圈包含的截面数量
        total_circles = self.config["pitch_multi"] + 2
        sections_per_circle = len(center_points) // total_circles

        # 添加圆圈 - 只添加非空的圆圈（第2圈到倒数第2圈）
        if self.config.get("enable_circles", True) and swept_circles:
            circles_added = 0
            empty_circles = 0
            start_circle_points = []  # 存储每圈起点处的圆圈

            for i, circle in enumerate(swept_circles):
                if len(circle) > 2:  # 只处理非空圆圈
                    try:
                        # 检查是否是每圈的起点
                        if i % sections_per_circle == 0:
                            # 添加起点处的圆圈（深朱红色）
                            spline = msp.add_spline(circle)
                            spline.dxf.color = 12
                            start_circle_points.append(circle[0])  # 保存第一个点
                        else:
                            # 添加普通圆圈（青色）
                            spline = msp.add_spline(circle)
                            spline.dxf.color = 4
                        circles_added += 1
                    except Exception as e:
                        if i < 5 or i > len(swept_circles) - 5:
                            print(f"添加圆圈 {i} 时出错: {e}")
                else:
                    empty_circles += 1

            print(f"成功添加 {circles_added} 个圆圈（第2圈到倒数第2圈）")
            if empty_circles > 0:
                print(f"跳过了 {empty_circles} 个空圆圈（首尾两圈）")

        # 添加端面圆
        if len(center_points) > 1:
            try:
                # 计算总圈数
                # 底部和顶部端面圆（黑色）
                start_z, end_z = self.pitch * 2, self.h - self.pitch * 2
                z_coords = [p[2] for p in center_points]

                # 添加底部端面圆
                start_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - start_z))
                t_start = self.t_spiral[start_idx]
                r_start = max(0.1, self.base_r - t_start * self.r)
                if r_start > 0:
                    msp.add_circle(center=(0, 0, start_z), radius=r_start).dxf.color = 7

                # 添加顶部端面圆
                end_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - end_z))
                t_end = self.t_spiral[end_idx]
                r_end = max(0.1, self.base_r - t_end * self.r)
                if r_end > 0:
                    msp.add_circle(center=(0, 0, end_z), radius=r_end).dxf.color = 7

                print(f"底部端面圆: 高度={start_z:.2f}mm, 半径={r_start:.2f}mm")
                print(f"顶部端面圆: 高度={end_z:.2f}mm, 半径={r_end:.2f}mm")
                # 添加端面圆
                for i in range(1,total_circles + 1):  # 增加一个循环用于最后一个圆心
                    # 计算当前圈的起始索引
                    if i < total_circles:
                        circle_start_idx = i * sections_per_circle
                    else:
                        # 最后一个圆圈的圆心索引
                        circle_start_idx = len(center_points) - 1

                    if circle_start_idx >= len(center_points):
                        circle_start_idx = len(center_points) - 1

                    # 获取当前圈的圆心位置
                    circle_center = center_points[circle_start_idx]
                    z_pos = circle_center[2]

                    # 计算当前半径
                    t_current = self.t_spiral[circle_start_idx]
                    r_current = max(0.1, self.base_r - t_current * self.r)

                    color = 11  # 粉色

                    if r_current > 0:
                        msp.add_circle(
                            center=(0, 0, z_pos),
                            radius=r_current
                        ).dxf.color = color

                        print(
                            f"端面圆 {i if i < total_circles else 'last'}: 高度={z_pos:.2f}mm, 半径={r_current:.2f}mm")

                print(f"共添加了 {total_circles + 1} 个端面圆（包含最后一个圆圈）")
            except Exception as e:
                print(f"添加端面圆时出错: {e}")


        # 添加锥形母线
        if self.config.get("show_cone_vertex", True) and hasattr(self, 'cone_vertex'):
            try:
                num_generatrices = 4
                for i in range(num_generatrices):
                    angle = 2 * math.pi * i / num_generatrices
                    x_end = self.base_r * math.cos(angle)
                    y_end = self.base_r * math.sin(angle) * self.config.get("sign", 1)
                    z_end = 0
                    msp.add_line(self.cone_vertex, (x_end, y_end, z_end),
                                 dxfattribs={'color': 6, 'linetype': 'DASHED', 'layer': 'CONE_GENERATRIX'})
                print(f"添加了 {num_generatrices} 条锥形母线")
            except Exception as e:
                print(f"添加锥形母线时出错: {e}")

        # 保存文件
        try:
            doc.saveas(output_file)
            print(f"成功保存到 {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")

        # 打印最终信息
        print(f"\n=== 导出总结 ===")
        print(f"控制点总数: {self.num_t}")
        print(f"扫掠断面: {sections_added} 个")
        print(f"圆圈扫掠: {circles_added} 个（第2圈到倒数第2圈）")
        print(f"起点圆圈: {len(start_circle_points)} 个（红色）")
        print(f"端面圆总数: {total_circles} 个（底部和顶部白色，中间绿色）")
        print(f"扭转功能: {'已启用' if self.config['twist_enabled'] else '未启用'}")
        print(f"动态缩放: {'已启用' if self.config['dynamic_scaling'] else '未启用'}")
        print(f"蛋尖螺旋线: 已添加，包含 {len(egghead_points)} 个点")

        if self.config["dynamic_scaling"]:
            print(f"断面大小随半径变化")
        else:
            print(f"断面大小保持恒定: {self.config['triangle_size']:.3f}")

        if self.config["twist_enabled"]:
            print(f"断面在整个螺旋线上保持固定扭转角度{self.config['taper_angle']}°")

        if self.config.get("show_cone_vertex", True):
            print(f"锥形顶点位置: (0, 0, {self.cone_vertex[2]:.2f})")

        if self.config.get("calculate_optimal_pitch_multi", True):
            optimal_info = self.calculate_optimal_pitch_multi_value()
            print(f"推荐pitch_multi: {optimal_info['recommended']:.2f}")

        print("===============")


# 在main函数中使用
def main():
    generator = SpiralSweepGenerator()
    generator.save_to_dxf("塔锥线性分布.dxf")


if __name__ == "__main__":
    main()