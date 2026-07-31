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
        # 默认参数配置 - enable_circles 默认为 True
        self.default_config = {
            "t_min": 0,
            "t_max": 1,
            "diameter": 250,
            "pitch": 5,
            "pitch_multi": 10,
            "taper_angle": 44,
            "sign": 1,
            "num_t": None,
            "output_file": "斜螺丝锥顶角88°加圆圈.dxf",
            "section_file": "三角牙82度.dxf",
            "triangle_size": 1,
            "depth": 0,
            "twist_enabled": True,
            "dynamic_scaling": False,
            "show_cone_vertex": True,
            "calculate_optimal_pitch_multi": True,
            "enable_circles": True,
            "circle_radius": 1,
            "circle_dynamic_scaling": True,
            "circle_offset": 0.0,
            "circle_segments": 16,  # 圆圈分段数
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
        self.config["num_t"] = self.config["num_t"] or int(self.h * 4)
        self.taper_ratio = math.tan(math.radians(self.config["taper_angle"]))

        # 基础参数
        self.t_min, self.t_max = self.config["t_min"], self.config["t_max"]
        self.pitch = self.config["pitch"]
        self.r = self.h * self.taper_ratio
        self.h_div_pitch = self.h * np.pi / self.pitch
        self.base_r = self.config["diameter"] / 2 + (self.pitch / self.h) * self.r

        # 其他参数
        self.num_t = self.config["num_t"]
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

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

    def print_parameter_explanation(self):
        """打印参数说明"""
        print("\n=== 参数说明 ===")
        print(f"螺旋线总高度: {self.h:.2f} mm")
        print(f"锥角度: {self.config['taper_angle']}°")
        print(f"锥形顶点高度: {self.cone_vertex[2]:.2f} mm")
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
        """在三角形中心生成圆圈点，确保section_points[0]作为第一个控制点"""
        # 计算三角形中心
        center = np.mean(self.section_points, axis=0)

        # 获取第一个控制点
        first_point = self.section_points[0]

        # 计算初始角度（从第一个控制点到中心的连线角度）
        dx = first_point[0] - center[0]
        dy = first_point[1] - center[1]
        start_angle = math.atan2(dy, dx)

        # 生成圆圈点
        circle_segments = self.config["circle_segments"]
        circle_points = []

        # 确保第一个点与section_points[0]对齐
        for i in range(circle_segments):
            angle = start_angle + 2 * math.pi * i / circle_segments
            x = center[0] + self.config["circle_radius"] * math.cos(angle)
            y = center[1] + self.config["circle_radius"] * math.sin(angle)
            circle_points.append([x, y])

        # 确保圆圈闭合
        if not np.allclose(circle_points[0], circle_points[-1]):
            circle_points.append(circle_points[0])

        self.circle_points = np.array(circle_points)
        print(f"生成圆圈点: {len(self.circle_points)} 个点，第一个点与断面第一个点对齐")

    def calculate_spiral_coords(self):
        """计算螺旋线坐标"""
        effective_r = max(0.1, self.base_r - self.config["depth"])
        t = self.t_spiral

        x = (effective_r - t * self.r) * np.cos(t * self.h_div_pitch)
        y = (effective_r - t * self.r) * np.sin(t * self.h_div_pitch) * self.config["sign"]
        z = t * self.h

        return x, y, z

    def generate_frenet_frame(self, x, y, z):
        """生成Frenet标架（切向量、法向量、副法向量）"""
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

    def sweep_section(self):
        """生成扫掠断面和圆圈"""
        x, y, z = self.calculate_spiral_coords()
        T, N, B = self.generate_frenet_frame(x, y, z)

        swept_sections = []
        swept_circles = []  # 存储扫掠后的圆圈
        twist_angle = -math.radians(self.config["taper_angle"]) if self.config["twist_enabled"] else 0

        print("开始生成扫掠几何体...")

        for i in range(self.num_t):
            section_points = []
            circle_points = []  # 当前断面的圆圈点

            current_r = self.base_r - self.t_spiral[i] * self.r

            # 计算缩放比例
            scale = current_r / self.base_r if self.config["dynamic_scaling"] else 1.0

            # 计算圆圈缩放比例
            circle_scale = current_r / self.base_r if self.config["circle_dynamic_scaling"] else 1.0

            # 计算旋转矩阵
            R_twist = self.rotation_matrix(T[i], twist_angle)
            R_combined = self.rotation_matrix(T[i], 0) @ R_twist

            # 处理三角形断面
            for j in range(len(self.section_points)):
                # 应用缩放
                x_val = self.section_points[j][0] * self.pitch * scale
                y_val = self.section_points[j][1] * self.pitch * scale

                # 应用旋转和偏移
                vector = R_combined @ (y_val * N[i] + x_val * B[i])
                point = [x[i] + vector[0], y[i] + vector[1], z[i] + vector[2]]
                section_points.append(point)

            swept_sections.append(section_points)

            # 处理圆圈 - 应用与三角形相同的变换
            if self.config["enable_circles"]:
                for j in range(len(self.circle_points)):
                    # 应用缩放（使用圆圈缩放比例）
                    x_val = self.circle_points[j][0] * self.pitch * circle_scale
                    y_val = self.circle_points[j][1] * self.pitch * circle_scale

                    # 应用旋转和偏移（与三角形使用相同的旋转矩阵）
                    vector = R_combined @ (y_val * B[i] + x_val * T[i])

                    # 计算圆圈中心点（三角形断面的中心）
                    section_center = np.mean(section_points, axis=0)

                    # 计算圆圈法向量（与断面相同）
                    if len(section_points) >= 3:
                        p1, p2, p3 = section_points[0], section_points[1], section_points[2]
                        v1 = np.array(p2) - np.array(p1)
                        v2 = np.array(p3) - np.array(p1)
                        normal = np.cross(v1, v2)

                        # 新增：计算v3向量并旋转法向量
                        v3 = np.array(p1) - np.array(section_center)
                        v3_norm = np.linalg.norm(v3)
                        if v3_norm > 0:
                            v3 = v3 / v3_norm  # 归一化
                            # 创建绕v3轴旋转90度的旋转矩阵
                            R_rotate = self.rotation_matrix(v3, math.pi / 2)
                            # 应用旋转
                            normal = R_rotate @ normal

                        normal_norm = np.linalg.norm(normal)
                        if normal_norm > 0:
                            normal = normal / normal_norm
                        else:
                            normal = T[i]  # 备用方案
                    else:
                        normal = T[i]  # 备用方案

                    # 应用圆圈偏移
                    circle_offset_vector = normal * self.config["circle_offset"]
                    point = [x[i] + vector[0] + circle_offset_vector[0],
                             y[i] + vector[1] + circle_offset_vector[1],
                             z[i] + vector[2] + circle_offset_vector[2]]
                    circle_points.append(point)

                swept_circles.append(circle_points)

        center_points = [[x[i], y[i], z[i]] for i in range(self.num_t)]
        return swept_sections, center_points, swept_circles

    def save_to_dxf(self, filename=None):
        """保存为DXF文件"""
        output_file = filename or self.config["output_file"]
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, swept_circles = self.sweep_section()

        # 添加中心螺旋线
        if len(center_points) > 1:
            try:
                msp.add_spline(center_points).dxf.color = 1
            except Exception as e:
                print(f"添加中心螺旋线时出错: {e}")

        # 添加扫掠断面（保持为polyline3d）
        for i, section in enumerate(swept_sections):
            if len(section) > 2:
                try:
                    polyline = msp.add_polyline3d(section)
                    polyline.close(True)
                    polyline.dxf.color = 3
                except Exception as e:
                    print(f"添加断面 {i} 时出错: {e}")

        # 添加圆圈 - 使用spline替代polyline3d
        if self.config["enable_circles"] and swept_circles:
            circles_added = 0
            for i, circle in enumerate(swept_circles):
                if len(circle) > 2:
                    try:
                        # 使用spline创建平滑的圆圈
                        spline = msp.add_spline(circle)
                        spline.dxf.color = 4
                        circles_added += 1
                    except Exception as e:
                        if i < 3:
                            print(f"添加圆圈 {i} 时出错: {e}")
            print(f"成功添加 {circles_added} 个圆圈（使用spline）")

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
            except Exception as e:
                print(f"添加端面圆时出错: {e}")

        # 保存文件
        try:
            doc.saveas(output_file)
            print(f"成功保存到 {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")


def main():
    """简化的主函数 - 直接使用默认参数"""
    # 创建生成器实例
    generator = SpiralSweepGenerator()

    # 生成并保存DXF文件
    generator.save_to_dxf()


if __name__ == "__main__":
    main()