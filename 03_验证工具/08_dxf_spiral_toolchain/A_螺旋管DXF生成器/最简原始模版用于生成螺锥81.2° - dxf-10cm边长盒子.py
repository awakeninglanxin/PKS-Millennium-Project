import numpy as np
import ezdxf
import matplotlib.pyplot as plt
import argparse
import json
import os
import math

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class SpiralSweepGenerator:
    def __init__(self, spline_data_path=None, config_file=None, **kwargs):
        # 默认参数配置
        self.default_config = {
            "t_min": 0,
            "t_max": 1,
            "diameter": 80,  # 锥底直径
            "pitch": 5,  # 锥螺距
            "pitch_multi": 7,  # 锥螺线圈匝数
            "taper_angle": 81.2 / 2,  # 锥顶角度除以2的值
            "sign": 1,  # 1顺牙攻，-1反牙攻
            "num_t": None,  # 总扫掠断面的数量
            "output_file": "斜螺丝锥顶角81.2°.dxf",
            "section_file": "三角牙82度.dxf",
            "triangle_size": 1,  # 扫掠断面大小
            "depth": 0,  # 攻牙向中轴的深度
            "twist_enabled": True,  # 断面扭转与锥倾斜角一致
            "dynamic_scaling": False,  # 断面缩放开关
            "show_cone_vertex": True,  # 是否显示锥形顶点
            "calculate_optimal_pitch_multi": True  # 是否计算最佳螺线圈匝数
        }

        self.config = self.load_config(config_file, kwargs)

        # 使用pitch_multi计算总高度
        self.h = (self.config["pitch_multi"] + 2) * self.config["pitch"]

        if self.config["num_t"] is None:
            self.config["num_t"] = int(self.h * 4)

        # 计算锥度比
        self.taper_ratio = math.tan(math.radians(self.config["taper_angle"]))

        self.t_min, self.t_max = self.config["t_min"], self.config["t_max"]
        self.pitch = self.config["pitch"]  # 先定义pitch

        # 先计算基础几何参数
        self.r = self.h * self.taper_ratio
        self.h_div_pitch = self.h * np.pi / self.pitch
        self.r_diff = (self.pitch / self.h) * self.r  # 半径修正量

        # 然后计算考虑修正后的基础半径
        self.base_r = self.config["diameter"] / 2 + self.r_diff

        # 其他参数
        self.pitch_multi = self.config["pitch_multi"] + 2
        self.num_t, self.sign = self.config["num_t"], self.config["sign"]
        self.triangle_size = self.config["triangle_size"]
        self.depth = self.config["depth"]
        self.twist_enabled = self.config["twist_enabled"]
        self.dynamic_scaling = self.config["dynamic_scaling"]
        self.show_cone_vertex = self.config["show_cone_vertex"]
        self.calculate_optimal_pitch_multi = self.config["calculate_optimal_pitch_multi"]
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)

        # 计算锥形顶点
        self.cone_vertex = self.calculate_cone_vertex()

        # 计算最佳pitch_multi
        if self.calculate_optimal_pitch_multi:
            self.optimal_pitch_multi = self.calculate_optimal_pitch_multi_value()

        # 打印参数说明
        self.print_parameter_explanation()

        section_path = spline_data_path or self.config["section_file"]
        if section_path and os.path.exists(section_path):
            self.load_section_data(section_path)
        else:
            print(f"警告: 断面文件 {section_path} 不存在")

    def calculate_cone_vertex(self):
        """计算锥形顶点位置"""
        # 锥形顶点位于锥形轴线上，高度为 h_vertex
        # 根据锥角度计算：tan(taper_angle) = base_r / h_vertex
        # 所以 h_vertex = base_r / tan(taper_angle)
        h_vertex = self.base_r / self.taper_ratio

        # 顶点位置 (0, 0, h_vertex)
        return (0, 0, h_vertex)

    def calculate_optimal_pitch_multi_value(self):
        """计算螺旋线占满整个圆锥时的最佳pitch_multi值"""
        # 方法1: 基于圆锥高度计算
        # 圆锥高度 h_cone = base_r / tan(taper_angle)
        h_cone = self.base_r / self.taper_ratio

        # 螺旋线总高度 h_spiral = pitch_multi * pitch
        # 当 h_spiral = h_cone 时，螺旋线刚好到达圆锥顶点
        optimal_pitch_multi_by_height = h_cone / self.pitch

        # 方法2: 基于螺旋线长度计算
        # 螺旋线长度 L = √(h^2 + (2πR_avg)^2) * n_turns
        # 其中 R_avg 是平均半径，n_turns 是圈数
        # 圆锥母线长度 L_cone = √(h_cone^2 + base_r^2)
        L_cone = math.sqrt(h_cone ** 2 + self.base_r ** 2)

        # 单圈螺旋线长度 L_turn = √(pitch^2 + (2πR_avg)^2)
        # 平均半径 R_avg = base_r / 2 (假设线性变化)
        R_avg = self.base_r / 2
        L_turn = math.sqrt(self.pitch ** 2 + (2 * math.pi * R_avg) ** 2)

        # 螺旋线圈数 n_turns = h_cone / pitch
        n_turns = h_cone / self.pitch

        # 螺旋线总长度 L_spiral = L_turn * n_turns
        # 当 L_spiral = L_cone 时，螺旋线刚好覆盖圆锥母线
        # 所以 n_turns = L_cone / L_turn
        optimal_n_turns = L_cone / L_turn
        optimal_pitch_multi_by_length = optimal_n_turns

        # 方法3: 基于螺旋线覆盖圆锥表面积
        # 圆锥侧面积 A_cone = π * base_r * L_cone
        A_cone = math.pi * self.base_r * L_cone

        # 单圈螺旋线近似覆盖的侧面积 A_turn = pitch * 2πR_avg
        A_turn = self.pitch * 2 * math.pi * R_avg

        # 螺旋线圈数 n_turns = A_cone / A_turn
        optimal_n_turns_by_area = A_cone / A_turn
        optimal_pitch_multi_by_area = optimal_n_turns_by_area

        # 返回三种方法的平均值，作为推荐值
        optimal_pitch_multi = (optimal_pitch_multi_by_height +
                               optimal_pitch_multi_by_length +
                               optimal_pitch_multi_by_area) / 3

        # 确保至少为1
        optimal_pitch_multi = max(1, optimal_pitch_multi)

        return {
            "by_height": optimal_pitch_multi_by_height,
            "by_length": optimal_pitch_multi_by_length,
            "by_area": optimal_pitch_multi_by_area,
            "recommended": optimal_pitch_multi
        }

    def print_parameter_explanation(self):
        """打印参数说明"""
        print("\n=== 参数说明 ===")
        turns = self.h / self.pitch

        print(f"pitch_multi = {self.pitch_multi} 代表螺距倍数")
        print(f"pitch = {self.pitch} mm 螺距")
        print(f"   → 螺旋线总高度: {self.h:.2f} mm (pitch_multi × pitch = {self.pitch_multi} × {self.pitch})")
        print(f"   → 螺旋线圈数: {turns:.2f} 圈")

        taper_angle = self.config["taper_angle"]
        taper_ratio = self.taper_ratio
        print(f"taper_angle = {taper_angle}° 代表锥角度")
        print(f"   → 锥度比: {taper_ratio:.4f} (tan({taper_angle}°))")

        # 显示锥形顶点信息
        if self.show_cone_vertex:
            h_vertex = self.cone_vertex[2]
            print(f"   → 锥形顶点高度: {h_vertex:.2f} mm")
            print(f"   → 锥形顶点位置: (0, 0, {h_vertex:.2f})")

        if self.twist_enabled:
            print(f"   → 扭转功能: 已启用，断面在整个螺旋线上保持固定扭转角度{taper_angle}°")
        else:
            print(f"   → 扭转功能: 未启用")

        if self.dynamic_scaling:
            print(f"   → 动态缩放: 已启用，断面大小随半径变化")
        else:
            print(f"   → 动态缩放: 未启用，断面大小保持恒定")

        print(f"diameter = {self.config['diameter']} mm 螺纹最大直径")
        print(f"triangle_size = {self.triangle_size} 攻牙断面基础大小")
        print(f"depth = {self.depth} mm 攻牙深度")
        print(f"num_t = {self.num_t} 分段数量")

        # 显示最佳pitch_multi建议
        if self.calculate_optimal_pitch_multi and hasattr(self, 'optimal_pitch_multi'):
            print(f"\n=== 最佳pitch_multi建议 ===")
            print(f"当前pitch_multi: {self.pitch_multi}")
            print(f"基于高度计算: {self.optimal_pitch_multi['by_height']:.2f} (螺旋线到达圆锥顶点)")
            print(f"基于长度计算: {self.optimal_pitch_multi['by_length']:.2f} (螺旋线长度等于圆锥母线长度)")
            print(f"基于面积计算: {self.optimal_pitch_multi['by_area']:.2f} (螺旋线覆盖圆锥侧面积)")
            print(f"推荐pitch_multi: {self.optimal_pitch_multi['recommended']:.2f}")

            # 比较当前值与推荐值
            if self.pitch_multi < self.optimal_pitch_multi['recommended']:
                print(f"建议: 当前pitch_multi偏小，螺旋线可能无法完全覆盖圆锥")
            elif self.pitch_multi > self.optimal_pitch_multi['recommended']:
                print(f"建议: 当前pitch_multi偏大，螺旋线可能会超出圆锥范围")
            else:
                print(f"建议: 当前pitch_multi接近推荐值")

        print("===============\n")

    def load_config(self, config_file=None, override_params=None):
        config = self.default_config.copy()
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    if "taper_ratio" in file_config and "taper_angle" not in file_config:
                        taper_ratio = file_config["taper_ratio"]
                        taper_angle = math.degrees(math.atan(taper_ratio))
                        file_config["taper_angle"] = taper_angle
                        print(f"已将锥度比 {taper_ratio} 转换为锥角度 {taper_angle:.2f}°")
                    config.update(file_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")

        if override_params:
            if "taper_ratio" in override_params and "taper_angle" not in override_params:
                taper_ratio = override_params["taper_ratio"]
                taper_angle = math.degrees(math.atan(taper_ratio))
                override_params["taper_angle"] = taper_angle
                print(f"已将锥度比 {taper_ratio} 转换为锥角度 {taper_angle:.2f}°")
            config.update({k: v for k, v in override_params.items() if v is not None})

        return config

    def scale_section_data(self, points, scale_factor):
        """缩放断面数据，以几何中心为基准"""
        if scale_factor == 1.0:
            return points

        center = np.mean(points, axis=0)
        translated_points = points - center
        scaled_points = translated_points * scale_factor
        final_points = scaled_points + center

        return final_points

    def load_section_data(self, filepath):
        try:
            doc = ezdxf.readfile(filepath)
            all_points = []
            for entity in doc.modelspace():
                if entity.dxftype() == 'POINT':
                    all_points.append([entity.dxf.location.x, entity.dxf.location.y])

            if len(all_points) < 3:
                print("DXF文件中必须包含至少3个点")
                return None

            all_points = np.array(all_points)
            self.original_section_points = all_points.copy()

            # 应用缩放
            if self.triangle_size != 1.0:
                all_points = self.scale_section_data(all_points, self.triangle_size)

            # 确保断面闭合
            if not np.allclose(all_points[0], all_points[-1]):
                all_points = np.append(all_points, [all_points[0]], axis=0)

            self.section_x, self.section_y = all_points[:, 0], all_points[:, 1]
            print(f"成功加载断面文件: {filepath}")
            return all_points
        except Exception as e:
            print(f"处理DXF文件时出错: {e}")
            return None

    def calculate_spiral_coords(self):
        # 计算考虑深度后的有效基圆半径
        effective_base_r = self.base_r - self.depth

        # 确保半径不为负
        if effective_base_r <= 0:
            print(f"警告: 深度{depth}过大，导致基圆半径为负，已自动调整")
            effective_base_r = max(0.1, effective_base_r)  # 最小半径为0.1mm

        x = (effective_base_r - self.t_spiral * self.r) * np.cos(self.t_spiral * self.h_div_pitch)
        y = (effective_base_r - self.t_spiral * self.r) * np.sin(self.t_spiral * self.h_div_pitch) * self.sign
        z = self.t_spiral * self.h
        return x, y, z

    def generate_spiral_curves(self):
        x, y, z = self.calculate_spiral_coords()
        dx, dy, dz = np.gradient(x, self.t_spiral), np.gradient(y, self.t_spiral), np.gradient(z, self.t_spiral)
        ddx, ddy, ddz = np.gradient(dx, self.t_spiral), np.gradient(dy, self.t_spiral), np.gradient(dz, self.t_spiral)

        T_unit, N_unit, B_unit = np.zeros((self.num_t, 3)), np.zeros((self.num_t, 3)), np.zeros((self.num_t, 3))

        for i in range(self.num_t):
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)
            N = np.array([ddx[i], ddy[i], ddz[i]])
            N_unit[i] = N / np.linalg.norm(N)
            B = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B / np.linalg.norm(B)

        center_points = [[x[i], y[i], z[i]] for i in range(self.num_t)]
        return np.array(center_points), [T_unit, N_unit, B_unit]

    def rotation_matrix_around_vector(self, v, psi):
        v = v / np.linalg.norm(v)
        vx, vy, vz = v
        K = np.array([[0, -vz, vy], [vz, 0, -vx], [-vy, vx, 0]])
        return np.eye(3) + np.sin(psi) * K + (1 - np.cos(psi)) * np.dot(K, K)

    def sweep_section(self):
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections, egghead_points = [], []

        # 使用固定的扭转角度
        twist_angle_fixed = -math.radians(self.config["taper_angle"])

        if self.dynamic_scaling:
            print("断面生成信息（动态缩放）:")
        else:
            print("断面生成信息（固定大小）:")

        for i in range(self.num_t):
            section_points = []

            # 使用固定的扭转角度
            if self.twist_enabled:
                twist_angle = twist_angle_fixed
            else:
                twist_angle = 0

            # 计算当前半径
            t_value = self.t_spiral[i]
            current_r = self.base_r - t_value * self.r

            # 简化的缩放逻辑
            if self.dynamic_scaling:
                # 动态缩放：断面大小随半径变化
                scale_factor = current_r / self.base_r
            else:
                # 固定大小：断面大小不变
                scale_factor = 1.0

            for j in range(len(self.section_x)):
                # 应用扭转旋转矩阵
                R_twist = self.rotation_matrix_around_vector(T_unit[i], twist_angle)
                R_theta = self.rotation_matrix_around_vector(T_unit[i], 0)
                R_combined = np.dot(R_theta, R_twist)

                # 应用缩放
                x_val = self.section_x[j] * self.pitch * scale_factor
                y_val = self.section_y[j] * self.pitch * scale_factor

                vector = np.dot(R_combined, (y_val * N_unit[i] + x_val * B_unit[i]))
                point = [center_points[i][k] + vector[k] for k in range(3)]

                if j == 0:
                    egghead_points.append(point)
                section_points.append(point)

            swept_sections.append(section_points)

            # 打印关键点的信息
            if i < 3 or i >= self.num_t - 3 or i % (self.num_t // 10) == 0:
                if self.dynamic_scaling:
                    print(f"点 {i:3d}: t={t_value:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放比例={scale_factor:.3f}, 扭转角度={math.degrees(twist_angle):.2f}°")
                else:
                    print(f"点 {i:3d}: t={t_value:.3f}, 半径={current_r:.3f}mm, "
                          f"缩放比例=1.000(固定), 扭转角度={math.degrees(twist_angle):.2f}°")

        return swept_sections, center_points.tolist(), egghead_points, [T_unit, N_unit, B_unit]

    def save_to_dxf(self, filename=None):
        output_file = filename or self.config["output_file"]
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, egghead_points, frame_vectors = self.sweep_section()

        # 添加中心螺旋线
        spline = msp.add_spline(center_points)
        spline.dxf.color = 1

        # 添加蛋尖螺旋线
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = 5

        # 添加扫掠断面
        for i, section in enumerate(swept_sections):
            polygon = msp.add_polyline3d(section)
            polygon.close(True)
            polygon.dxf.color = 3

        # 修正端面圆计算
        if center_points:
            # 找到螺旋线两端高度减去一个螺距对应的参数t值
            start_z_target = self.pitch  # 起点高度减去一个螺距（从0开始）
            end_z_target = self.h - self.pitch  # 终点高度减去一个螺距

            # 通过插值找到对应的t值
            z_coords = [point[2] for point in center_points]

            # 找到最接近目标高度的点
            start_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - start_z_target))
            end_idx = min(range(len(z_coords)), key=lambda i: abs(z_coords[i] - end_z_target))

            # 计算对应的半径 - 使用与螺旋线相同的公式
            t_start = self.t_spiral[start_idx]
            t_end = self.t_spiral[end_idx]

            # 使用与calculate_spiral_coords相同的公式计算半径（考虑深度）
            effective_base_r = self.base_r - self.depth
            r_start = effective_base_r - t_start * self.r
            r_end = effective_base_r - t_end * self.r

            # 使用正确的高度和半径添加端面圆
            msp.add_circle(center=(0, 0, start_z_target), radius=r_start).dxf.color = 7
            msp.add_circle(center=(0, 0, end_z_target), radius=r_end).dxf.color = 7

        # 添加锥形顶点和母线
        if self.show_cone_vertex:
            # 添加锥形顶点
            msp.add_point(self.cone_vertex, dxfattribs={'color': 7})

            # 添加从顶点到底面圆周的母线
            num_generatrices = 8  # 母线数量
            for i in range(num_generatrices):
                angle = 2 * math.pi * i / num_generatrices

                # 母线使用原始材料的半径（不考虑深度）
                x_end = self.base_r * math.cos(angle)
                y_end = self.base_r * math.sin(angle) * self.sign
                z_end = 0

                # 添加母线
                msp.add_line(self.cone_vertex, (x_end, y_end, z_end), dxfattribs={'color': 6, 'linetype': 'DASHED'})

                # 添加从顶点到顶部圆周的母线
                if center_points:
                    # 使用原始材料的顶部半径（不考虑深度）
                    x_top_end = (self.base_r - self.t_max * self.r) * math.cos(angle)
                    y_top_end = (self.base_r - self.t_max * self.r) * math.sin(angle) * self.sign
                    z_top_end = self.h

                    msp.add_line(self.cone_vertex, (x_top_end, y_top_end, z_top_end),
                                 dxfattribs={'color': 6, 'linetype': 'DASHED'})

        # 添加参数说明文本
        texts = []
        if self.twist_enabled:
            texts.append(f"固定扭转角度: {self.config['taper_angle']}°")

        if self.dynamic_scaling:
            texts.append("动态缩放: 已启用")
        else:
            texts.append("动态缩放: 未启用")

        if self.show_cone_vertex:
            texts.append(f"锥形顶点: (0, 0, {self.cone_vertex[2]:.2f})")

        if self.calculate_optimal_pitch_multi and hasattr(self, 'optimal_pitch_multi'):
            texts.append(f"推荐pitch_multi: {self.optimal_pitch_multi['recommended']:.2f}")

        for i, text in enumerate(texts):
            msp.add_text(
                text,
                dxfattribs={
                    'height': 0.5,
                    'color': 2 + i,
                    'insert': (0, -self.base_r - 5 - i)
                }
            )

        doc.saveas(output_file)
        print(f"成功保存到 {output_file}")
        print(f"扭转功能: {'已启用' if self.twist_enabled else '未启用'}")
        print(f"动态缩放: {'已启用' if self.dynamic_scaling else '未启用'}")

        # 简化打印信息
        if self.dynamic_scaling:
            print(f"断面大小随半径变化")
        else:
            print(f"断面大小保持恒定: {self.triangle_size:.3f}")

        if self.twist_enabled:
            print(f"断面在整个螺旋线上保持固定扭转角度{self.config['taper_angle']}°")

        if self.show_cone_vertex:
            print(f"锥形顶点位置: (0, 0, {self.cone_vertex[2]:.2f})")

        if self.calculate_optimal_pitch_multi and hasattr(self, 'optimal_pitch_multi'):
            print(f"推荐pitch_multi: {self.optimal_pitch_multi['recommended']:.2f}")

        # 打印端面圆信息
        if center_points:
            print(f"底部端面圆: 高度={start_z_target:.2f}mm, 半径={r_start:.2f}mm")
            print(f"顶部端面圆: 高度={end_z_target:.2f}mm, 半径={r_end:.2f}mm")


def main():
    parser = argparse.ArgumentParser(description="螺旋扫掠生成器")
    parser.add_argument("--section-file", help="断面DXF文件路径")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output", help="输出DXF文件路径")
    parser.add_argument("--t-min", type=float, help="t_min参数")
    parser.add_argument("--t-max", type=float, help="t_max参数")
    parser.add_argument("--diameter", type=float, help="直径")
    parser.add_argument("--pitch", type=float, help="螺距")
    parser.add_argument("--pitch-multi", type=float, help="螺距倍数")
    parser.add_argument("--taper-angle", type=float, help="锥角度（度）")
    parser.add_argument("--taper-ratio", type=float, help="锥度比（兼容旧参数）")
    parser.add_argument("--sign", type=int, choices=[-1, 1], help="方向符号")
    parser.add_argument("--num-t", type=int, help="分段数量")
    parser.add_argument("--triangle-size", type=float, help="三角形截面大小")
    parser.add_argument("--depth", type=float, help="攻牙深度")
    parser.add_argument("--no-dynamic-scaling", action="store_true", help="禁用动态缩放")
    parser.add_argument("--no-twist", action="store_true", help="禁用扭转功能")
    parser.add_argument("--show-config", action="store_true", help="显示当前配置")

    args = parser.parse_args()

    kwargs = {k: v for k, v in vars(args).items() if
              v is not None and k not in ['show_config', 'no_twist', 'no_dynamic_scaling']}

    # 处理扭转开关
    if args.no_twist:
        kwargs["twist_enabled"] = False

    # 处理动态缩放开关
    if args.no_dynamic_scaling:
        kwargs["dynamic_scaling"] = False

    generator = SpiralSweepGenerator(**kwargs)

    if args.show_config:
        print("\n当前参数配置:")
        for key, value in generator.config.items():
            print(f"{key:20}: {value}")

    generator.save_to_dxf()


if __name__ == "__main__":
    main()