import ezdxf
import math
import os
import numpy as np
from typing import List, Tuple, Optional


class SpirographGenerator:
    """
    万花尺DXF生成器 - 删除绿色外侧和蓝色内侧尖峰点
    """

    def __init__(self):
        self.doc = None
        self.msp = None

    def load_dxf(self, dxf_filename: str) -> bool:
        """加载DXF文件"""
        try:
            if not os.path.exists(dxf_filename):
                print(f"错误: 文件 {dxf_filename} 不存在")
                return False

            self.doc = ezdxf.readfile(dxf_filename)
            self.msp = self.doc.modelspace()
            print(f"成功加载DXF文件: {dxf_filename}")
            return True
        except Exception as e:
            print(f"加载DXF文件失败: {e}")
            return False

    def extract_contour_curves(self) -> List[List[Tuple[float, float]]]:
        """从DXF中提取SPLINE轮廓曲线"""
        contours = []
        spline_count = 0

        for entity in self.msp:
            if entity.dxftype() == 'SPLINE':
                spline_count += 1
                points = self._entity_to_points(entity)
                if points and len(points) > 2:
                    contours.append(points)
                    print(f"找到第 {spline_count} 条SPLINE曲线，包含 {len(points)} 个点")
                else:
                    print(f"第 {spline_count} 条SPLINE曲线转换失败或点数不足")

        print(f"总共找到 {spline_count} 条SPLINE曲线，成功转换 {len(contours)} 条")
        return contours

    def _entity_to_points(self, entity) -> List[Tuple[float, float]]:
        """专门处理SPLINE曲线转换为点列表"""
        points = []

        if entity.dxftype() != 'SPLINE':
            return points

        try:
            # 使用flattening方法获取离散点
            if hasattr(entity, 'flattening'):
                try:
                    flattened = entity.flattening(distance=0.01, segments=16)
                    for point in flattened:
                        points.append((point[0], point[1]))
                    return points
                except Exception as e:
                    print(f"flattening方法失败: {e}")

            # 备用方法: 在参数空间均匀采样
            sample_points = 200
            for t in np.linspace(0, 1, sample_points):
                try:
                    point = entity.point(t)
                    points.append((point[0], point[1]))
                except:
                    continue

        except Exception as e:
            print(f"处理SPLINE曲线时出错: {e}")

        return points

    def _calculate_contour_length(self, points: List[Tuple[float, float]]) -> float:
        """计算轮廓长度"""
        length = 0.0
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            length += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return length

    def _is_closed(self, points: List[Tuple[float, float]]) -> bool:
        """检查轮廓是否封闭"""
        if len(points) < 3:
            return False

        first = points[0]
        last = points[-1]
        distance = math.sqrt((last[0] - first[0]) ** 2 + (last[1] - first[1]) ** 2)
        return distance < 0.001

    def _close_contour(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """封闭轮廓"""
        if not self._is_closed(points) and len(points) > 1:
            points.append(points[0])
        return points

    def _divide_contour_evenly(self, points: List[Tuple[float, float]], num_divisions: int) -> List[
        Tuple[float, float]]:
        """沿轮廓均匀分割点（确保首尾相接）"""
        if len(points) < 2:
            return points

        # 确保轮廓封闭
        if not self._is_closed(points):
            points = self._close_contour(points)

        # 计算轮廓总长度
        total_length = self._calculate_contour_length(points)

        # 计算每段长度
        segment_lengths = []
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            segment_lengths.append(length)

        # 生成均匀分割点
        division_points = []
        target_spacing = total_length / num_divisions
        current_distance = 0
        segment_index = 0
        segment_progress = 0

        for i in range(num_divisions):
            target_distance = i * target_spacing

            # 找到目标距离所在的线段
            while (segment_index < len(segment_lengths) and
                   current_distance + segment_lengths[segment_index] < target_distance):
                current_distance += segment_lengths[segment_index]
                segment_index += 1
                segment_progress = 0

            if segment_index >= len(segment_lengths):
                break

            # 在线段上插值
            segment_start = points[segment_index]
            segment_end = points[segment_index + 1]
            segment_length = segment_lengths[segment_index]
            segment_progress = (target_distance - current_distance) / segment_length
            segment_progress = max(0, min(1, segment_progress))

            x = segment_start[0] + segment_progress * (segment_end[0] - segment_start[0])
            y = segment_start[1] + segment_progress * (segment_end[1] - segment_start[1])
            division_points.append((x, y))

        # 确保首尾相接 - 添加起点作为终点
        if len(division_points) > 0 and self._is_closed(points):
            division_points.append(division_points[0])

        return division_points

    def _calculate_normal(self, points: List[Tuple[float, float]], index: int) -> Tuple[float, float]:
        """计算法线方向"""
        n = len(points)
        if n < 3:
            return (1, 0)

        # 使用前后点计算切线方向
        prev_index = (index - 1) % n
        next_index = (index + 1) % n

        prev_point = points[prev_index]
        next_point = points[next_index]

        # 计算切线方向
        tangent_x = next_point[0] - prev_point[0]
        tangent_y = next_point[1] - prev_point[1]

        tangent_length = math.sqrt(tangent_x ** 2 + tangent_y ** 2)
        if tangent_length < 1e-10:
            return (1, 0)

        # 单位化切线并计算法线
        tangent_x /= tangent_length
        tangent_y /= tangent_length
        normal_x = -tangent_y
        normal_y = tangent_x

        return (normal_x, normal_y)

    def _true_sawtooth_wave(self, phase: float, tooth_count: int) -> float:
        """真正的锯齿波函数（非平滑），振幅范围从-1到1"""
        # 计算当前点在哪个齿牙周期内
        tooth_phase = phase * tooth_count
        tooth_index = int(tooth_phase)
        tooth_local_phase = tooth_phase - tooth_index

        # 真正的锯齿波：线性上升，然后突变下降
        if tooth_local_phase < 0.5:
            # 上升段：从-1线性上升到1
            value = -1 + 4 * tooth_local_phase
        else:
            # 下降段：从1线性下降到-1
            value = 1 - 4 * (tooth_local_phase - 0.5)

        return value

    def _calculate_tooth_metrics(self, points: List[Tuple[float, float]],
                                 contour_points: List[Tuple[float, float]],
                                 curve_type: str, tooth_count: int) -> Tuple[float, float]:
        """计算锯齿的深度和间距（脉宽）"""
        if len(points) < 10:
            return 0.0, 0.0

        # 计算锯齿深度 - 找到锯齿波的最大偏移量
        max_depth = 0.0
        for i, point in enumerate(points):
            # 找到轮廓线上最近的点
            closest_contour_point = self._find_closest_contour_point(point, contour_points)
            # 计算点到轮廓线的距离
            distance = math.sqrt((point[0] - closest_contour_point[0]) ** 2 +
                                 (point[1] - closest_contour_point[1]) ** 2)
            if distance > max_depth:
                max_depth = distance

        # 计算锯齿间距（脉宽）- 使用轮廓长度和齿数计算弦长
        contour_length = self._calculate_contour_length(contour_points)
        tooth_spacing = contour_length / tooth_count  # 弦长 = 轮廓长度 / 齿数

        return max_depth, tooth_spacing

    def _remove_peak_points(self, points: List[Tuple[float, float]], window_size: int = 5,
                            curve_type: str = "outer", contour_points: List[Tuple[float, float]] = None) -> List[
        Tuple[float, float]]:
        """
        删除尖峰点，保留谷点
        通过检测局部曲率变化来识别尖峰
        只删除绿色外侧和蓝色内侧的尖峰点
        """
        if len(points) < window_size * 2 + 1:
            return points

        # 计算每个点的曲率（通过相邻点的角度变化）
        curvatures = []
        for i in range(len(points)):
            # 使用循环边界处理首尾点
            prev_index = (i - window_size) % len(points)
            next_index = (i + window_size) % len(points)

            # 计算前后向量
            prev_point = points[prev_index]
            next_point = points[next_index]
            current_point = points[i]

            # 向量1: 从前点到当前点
            vec1_x = current_point[0] - prev_point[0]
            vec1_y = current_point[1] - prev_point[1]

            # 向量2: 从当前点到后点
            vec2_x = next_point[0] - current_point[0]
            vec2_y = next_point[1] - current_point[1]

            # 计算向量夹角（余弦值）
            dot_product = vec1_x * vec2_x + vec1_y * vec2_y
            mag1 = math.sqrt(vec1_x ** 2 + vec1_y ** 2)
            mag2 = math.sqrt(vec2_x ** 2 + vec2_y ** 2)

            if mag1 > 1e-10 and mag2 > 1e-10:
                cosine = dot_product / (mag1 * mag2)
                cosine = max(-1, min(1, cosine))  # 确保在有效范围内
                angle = math.acos(cosine)
                curvatures.append(angle)
            else:
                curvatures.append(0)

        # 找出曲率最大的点（尖峰）
        peak_indices = []
        for i in range(len(points)):
            # 检查是否是局部最大值
            is_peak = True
            for j in range(1, window_size + 1):
                prev_idx = (i - j) % len(points)
                next_idx = (i + j) % len(points)

                if curvatures[prev_idx] > curvatures[i] or curvatures[next_idx] > curvatures[i]:
                    is_peak = False
                    break

            # 只删除曲率大于阈值的尖峰
            if is_peak and curvatures[i] > math.pi / 2:  # 90度阈值
                # 对于外侧曲线（绿色），只删除向外凸出的尖峰
                # 对于内侧曲线（蓝色），只删除向内凹入的尖峰
                if self._is_outer_peak(points, i, contour_points, curve_type):
                    peak_indices.append(i)

        # 删除尖峰点（从后往前删除，避免索引变化）
        for idx in sorted(peak_indices, reverse=True):
            if 0 <= idx < len(points):  # 包括首尾点
                del points[idx]

        print(f"删除了 {len(peak_indices)} 个{curve_type}尖峰点")
        return points

    def _is_outer_peak(self, points: List[Tuple[float, float]], index: int,
                       contour_points: List[Tuple[float, float]], curve_type: str) -> bool:
        """判断是否是外侧尖峰（绿色）或内侧尖峰（蓝色）"""
        if curve_type == "outer":
            # 对于外侧曲线，检查点是否在轮廓线外侧
            if index < len(points) and contour_points is not None:
                # 找到轮廓线上最近的点
                contour_point = self._find_closest_contour_point(points[index], contour_points)
                # 计算点到轮廓线的距离和方向
                dx = points[index][0] - contour_point[0]
                dy = points[index][1] - contour_point[1]

                # 计算法线方向
                normal = self._calculate_normal(contour_points,
                                                self._find_contour_point_index(contour_point, contour_points))

                # 检查点是否在法线方向上（外侧）
                dot_product = dx * normal[0] + dy * normal[1]
                return dot_product > 0  # 正值表示在外侧
        elif curve_type == "inner":
            # 对于内侧曲线，检查点是否在轮廓线内侧
            if index < len(points) and contour_points is not None:
                # 找到轮廓线上最近的点
                contour_point = self._find_closest_contour_point(points[index], contour_points)
                # 计算点到轮廓线的距离和方向
                dx = points[index][0] - contour_point[0]
                dy = points[index][1] - contour_point[1]

                # 计算法线方向
                normal = self._calculate_normal(contour_points,
                                                self._find_contour_point_index(contour_point, contour_points))

                # 检查点是否在法线反方向上（内侧）
                dot_product = dx * normal[0] + dy * normal[1]
                return dot_product < 0  # 负值表示在内侧

        return True  # 默认情况下删除所有尖峰

    def _find_closest_contour_point(self, point: Tuple[float, float],
                                    contour_points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """找到轮廓线上离给定点最近的点"""
        min_distance = float('inf')
        closest_point = contour_points[0] if contour_points else (0, 0)

        for contour_point in contour_points:
            distance = math.sqrt((point[0] - contour_point[0]) ** 2 + (point[1] - contour_point[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_point = contour_point

        return closest_point

    def _find_contour_point_index(self, point: Tuple[float, float],
                                  contour_points: List[Tuple[float, float]]) -> int:
        """找到点在轮廓线上的索引"""
        for i, contour_point in enumerate(contour_points):
            if abs(contour_point[0] - point[0]) < 1e-10 and abs(contour_point[1] - point[1]) < 1e-10:
                return i
        return 0  # 默认返回第一个点

    def _find_optimal_parameters(self, contour_points: List[Tuple[float, float]],
                                 tooth_count: int) -> int:
        """自动寻找最佳参数确保首尾相接"""
        # 确保轮廓封闭
        if not self._is_closed(contour_points):
            contour_points = self._close_contour(contour_points)

        # 尝试不同的齿数
        best_tooth_count = tooth_count
        best_gap = float('inf')

        # 测试相邻的齿数
        for tooth_adjust in [-1, 0, 1]:
            test_tooth_count = tooth_count + tooth_adjust
            if test_tooth_count < 3:  # 齿数不能太少
                continue

            # 生成测试曲线
            test_points = self._generate_sawtooth_curve(
                contour_points, test_tooth_count, 1.0, True, "outer"
            )

            if len(test_points) < 2:
                continue

            # 计算首尾间隙
            first_point = test_points[0]
            last_point = test_points[-1]
            gap = math.sqrt((last_point[0] - first_point[0]) ** 2 +
                            (last_point[1] - first_point[1]) ** 2)

            if gap < best_gap:
                best_gap = gap
                best_tooth_count = test_tooth_count

        print(f"最佳齿数: {best_tooth_count} (原始: {tooth_count}), 首尾间隙: {best_gap:.6f}")

        return best_tooth_count

    def _generate_sawtooth_curve(self, contour_points: List[Tuple[float, float]],
                                 tooth_count: int, amplitude: float, is_outer: bool, curve_type: str) -> List[
        Tuple[float, float]]:
        """生成锯齿波曲线，然后删除尖峰点"""
        # 确保轮廓封闭
        if not self._is_closed(contour_points):
            contour_points = self._close_contour(contour_points)

        # 使用足够多的分割点确保精度
        division_points = self._divide_contour_evenly(contour_points, tooth_count * 20)

        if len(division_points) < 2:
            return []

        result_points = []

        for i, point in enumerate(division_points):
            if i >= len(division_points) - 1:  # 跳过最后一个点（与第一个点相同）
                continue

            # 计算法线方向
            normal = self._calculate_normal(division_points, i)

            # 计算相位（确保在0-1范围内）
            phase = i / (len(division_points) - 1)

            # 使用真正的锯齿波函数（振幅范围从-1到1）
            sawtooth_value = self._true_sawtooth_wave(phase, tooth_count)

            # 计算总偏移（直接使用振幅乘以锯齿波值）
            total_offset = amplitude * sawtooth_value
            if not is_outer:
                total_offset = -total_offset

            # 计算新点
            new_x = point[0] + normal[0] * total_offset
            new_y = point[1] + normal[1] * total_offset
            result_points.append((new_x, new_y))

        # 删除尖峰点，但只删除绿色外侧和蓝色内侧的尖峰点
        result_points = self._remove_peak_points(result_points, curve_type=curve_type, contour_points=contour_points)

        # 确保首尾相接 - 添加起点作为终点
        if len(result_points) > 0:
            result_points.append(result_points[0])

        return result_points

    def generate_spirograph(self, contour_points: List[Tuple[float, float]],
                            outer_teeth: int, inner_teeth: int,
                            amplitude_outer: float, amplitude_inner: float) -> dict:
        """生成万花尺曲线（删除绿色外侧和蓝色内侧尖峰点）"""
        # 确保轮廓封闭
        if not self._is_closed(contour_points):
            contour_points = self._close_contour(contour_points)

        # 计算轮廓长度
        contour_length = self._calculate_contour_length(contour_points)
        print(f"轮廓长度: {contour_length:.2f} 单位")

        # 自动寻找最佳参数确保首尾相接
        print("正在自动调整参数确保首尾相接...")
        optimal_outer_teeth = self._find_optimal_parameters(
            contour_points, outer_teeth
        )

        optimal_inner_teeth = self._find_optimal_parameters(
            contour_points, inner_teeth
        )

        # 生成外侧锯齿波曲线（绿色），删除外侧尖峰点
        print("生成外侧锯齿波曲线并删除外侧尖峰点...")
        outer_points = self._generate_sawtooth_curve(
            contour_points, optimal_outer_teeth, amplitude_outer, True, "outer"
        )

        # 生成内侧锯齿波曲线（蓝色），删除内侧尖峰点
        print("生成内侧锯齿波曲线并删除内侧尖峰点...")
        inner_points = self._generate_sawtooth_curve(
            contour_points, optimal_inner_teeth, amplitude_inner, False, "inner"
        )

        # 计算锯齿深度和间距
        outer_depth, outer_spacing = self._calculate_tooth_metrics(outer_points, contour_points, "outer",
                                                                   optimal_outer_teeth)
        inner_depth, inner_spacing = self._calculate_tooth_metrics(inner_points, contour_points, "inner",
                                                                   optimal_inner_teeth)

        return {
            'contour': contour_points,  # 红色轮廓线（保留所有点）
            'outer': outer_points,  # 绿色外侧锯齿波（删除外侧尖峰）
            'inner': inner_points,  # 蓝色内侧锯齿波（删除内侧尖峰）
            'outer_depth': outer_depth,
            'outer_spacing': outer_spacing,
            'inner_depth': inner_depth,
            'inner_spacing': inner_spacing,
            'outer_teeth': optimal_outer_teeth,
            'inner_teeth': optimal_inner_teeth
        }

    def save_spirograph(self, spirograph_data: dict, output_filename: str):
        """保存万花尺到DXF文件"""
        # 创建新的DXF文档
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # 设置图层颜色
        layer_colors = {
            'contour': 1,  # 红色 - 轮廓线
            'outer': 3,  # 绿色 - 外侧锯齿波
            'inner': 5  # 蓝色 - 内侧锯齿波
        }

        # 添加图层
        for layer_name, color in layer_colors.items():
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name, dxfattribs={'color': color})

        # 添加红色轮廓线
        if 'contour' in spirograph_data and spirograph_data['contour']:
            points = spirograph_data['contour']
            if len(points) > 1:
                msp.add_lwpolyline(points, dxfattribs={'layer': 'contour'})

        # 添加绿色外侧锯齿波（删除外侧尖峰）
        if 'outer' in spirograph_data and spirograph_data['outer']:
            points = spirograph_data['outer']
            if len(points) > 1:
                msp.add_lwpolyline(points, dxfattribs={'layer': 'outer'})

        # 添加蓝色内侧锯齿波（删除内侧尖峰）
        if 'inner' in spirograph_data and spirograph_data['inner']:
            points = spirograph_data['inner']
            if len(points) > 1:
                msp.add_lwpolyline(points, dxfattribs={'layer': 'inner'})

        # 保存文件
        try:
            doc.saveas(output_filename)
            print(f"万花尺（删除绿色外侧和蓝色内侧尖峰）已保存到: {output_filename}")
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False

    def print_statistics(self, spirograph_data: dict, outer_teeth: int, inner_teeth: int,
                         amplitude_outer: float, amplitude_inner: float):
        """打印统计信息"""
        print("=" * 70)
        print("万花尺生成统计（删除绿色外侧和蓝色内侧尖峰点）")
        print("=" * 70)

        if 'contour' in spirograph_data:
            print(f"轮廓线点数: {len(spirograph_data['contour'])}")

        # 使用优化后的齿数
        actual_outer_teeth = spirograph_data.get('outer_teeth', outer_teeth)
        actual_inner_teeth = spirograph_data.get('inner_teeth', inner_teeth)

        print(f"外侧锯齿波齿数: {actual_outer_teeth}")
        print(f"外侧锯齿波振幅: {amplitude_outer:.2f}")

        print(f"内侧锯齿波齿数: {actual_inner_teeth}")
        print(f"内侧锯齿波振幅: {amplitude_inner:.2f}")

        if 'outer' in spirograph_data:
            first_point = spirograph_data['outer'][0]
            last_point = spirograph_data['outer'][-1]
            gap = math.sqrt((last_point[0] - first_point[0]) ** 2 +
                            (last_point[1] - first_point[1]) ** 2)
            print(f"外侧锯齿波首尾间隙: {gap:.6f}")
            print(f"外侧锯齿波点数: {len(spirograph_data['outer'])}")

        if 'inner' in spirograph_data:
            first_point = spirograph_data['inner'][0]
            last_point = spirograph_data['inner'][-1]
            gap = math.sqrt((last_point[0] - first_point[0]) ** 2 +
                            (last_point[1] - first_point[1]) ** 2)
            print(f"内侧锯齿波首尾间隙: {gap:.6f}")
            print(f"内侧锯齿波点数: {len(spirograph_data['inner'])}")

        # 打印锯齿深度和间距
        if 'outer_depth' in spirograph_data and 'outer_spacing' in spirograph_data:
            print(f"锯齿深度: {spirograph_data['outer_depth']:.3f} mm")
            print(f"锯齿间距: {spirograph_data['outer_spacing']:.3f} mm")

        print("=" * 70)


def main():
    """主函数"""
    print("=" * 70)
    print("万花尺DXF生成器 - 删除绿色外侧和蓝色内侧尖峰点")
    print("使用真正锯齿波（振幅范围-1到1），删除绿色外侧和蓝色内侧尖峰")
    print("=" * 70)

    # 创建生成器实例
    generator = SpirographGenerator()

    # 获取输入文件
    dxf_filename = input("请输入DXF文件路径: ").strip().strip('"')
    if not dxf_filename:
        dxf_filename = "曲线E.dxf"

    # 加载DXF文件
    if not generator.load_dxf(dxf_filename):
        return

    # 提取轮廓曲线
    contours = generator.extract_contour_curves()
    if not contours:
        print("未找到有效的SPLINE曲线")
        return

    # 让用户选择轮廓
    if len(contours) > 1:
        print(f"找到 {len(contours)} 条轮廓曲线，请选择:")
        for i, contour in enumerate(contours):
            print(f"{i + 1} - 包含 {len(contour)} 个点")

        try:
            choice = int(input("请选择轮廓曲线 (默认1): ") or "1") - 1
            if choice < 0 or choice >= len(contours):
                choice = 0
                print("选择无效，使用第一条轮廓")
        except:
            choice = 0
            print("使用第一条轮廓曲线")
    else:
        choice = 0

    contour_points = contours[choice]
    print(f"使用第 {choice + 1} 条轮廓曲线，包含 {len(contour_points)} 个点")

    # 获取用户参数
    try:
        outer_teeth = int(input("外侧锯齿波齿数 (默认360): ") or "360")
        inner_teeth = int(input("内侧锯齿波齿数 (默认360): ") or "360")
        amplitude_outer = float(input("外侧锯齿波振幅 (默认2.0): ") or "2.0")
        amplitude_inner = float(input("内侧锯齿波振幅 (默认2.0): ") or "2.0")
    except ValueError:
        print("输入参数无效，使用默认值")
        outer_teeth, inner_teeth = 360, 360
        amplitude_outer, amplitude_inner = 2.0, 2.0

    # 生成万花尺
    print("正在生成万花尺（将删除绿色外侧和蓝色内侧尖峰点）...")
    spirograph_data = generator.generate_spirograph(
        contour_points, outer_teeth, inner_teeth,
        amplitude_outer, amplitude_inner
    )

    # 生成输出文件名
    base_name = os.path.splitext(dxf_filename)[0]
    output_filename = f"{base_name}_万花尺.dxf"

    # 保存万花尺
    generator.save_spirograph(spirograph_data, output_filename)

    # 打印统计信息
    generator.print_statistics(
        spirograph_data, outer_teeth, inner_teeth,
        amplitude_outer, amplitude_inner
    )

    print(f"万花尺已生成并保存到: {output_filename}")


if __name__ == "__main__":
    # 检查是否有ezdxf库
    try:
        import ezdxf
    except ImportError:
        print("错误: 需要安装ezdxf库")
        print("请运行: pip install ezdxf")
        exit(1)

    # 直接运行主功能
    main()