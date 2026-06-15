import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def extract_spline_from_dxf(dxf_path, num_points=108):
    """
    从DXF文件中提取SPLINE曲线数据，并将参数范围映射到0-2π。

    Args:
        dxf_path (str): DXF文件的路径
        num_points (int): 采样点数量，默认34

    Returns:
        numpy.ndarray: 包含(t, x, y)数据的数组，t范围为0到2π
    """
    if not Path(dxf_path).exists():
        raise FileNotFoundError(f"文件不存在: {dxf_path}")

    try:
        # 读取DXF文件
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 存储所有点
        all_points = []
        spline_count = 0

        # 只处理SPLINE类型
        for entity in msp:
            if entity.dxftype() == 'SPLINE':
                spline_count += 1
                print(f"处理第 {spline_count} 条样条曲线")

                # 获取样条曲线工具
                spline_tool = entity.construction_tool()

                # 在0到1之间均匀采样
                t_local = np.linspace(0, 1, num_points)
                points = spline_tool.approximate(num_points - 1)

                # 将参数映射到0到2π
                t_global = t_local * 2 * np.pi

                # 收集点数据
                for t, p in zip(t_global, points):
                    all_points.append((t, p[0], p[1]))

        if spline_count == 0:
            print("警告：未在DXF文件中找到SPLINE类型的曲线")
            return None

        # 转换为numpy数组
        points = np.array(all_points)

        print(f"\n处理完成:")
        print(f"共发现 {spline_count} 条样条曲线")
        print(f"提取了 {len(points)} 个数据点")
        print(f"参数范围: {points[:, 0].min():.2f} 到 {points[:, 0].max():.2f}")
        print(f"x范围: {points[:, 1].min():.2f} 到 {points[:, 1].max():.2f}")
        print(f"y范围: {points[:, 2].min():.2f} 到 {points[:, 2].max():.2f}")

        return points

    except ezdxf.DXFError as e:
        print(f"DXF文件格式错误: {str(e)}")
        return None
    except Exception as e:
        print(f"处理DXF文件时出错: {str(e)}")
        return None


def visualize_spline(points):
    """
    可视化样条曲线数据，并标注象限。

    Args:
        points (numpy.ndarray): 包含(t, x, y)数据的数组
    """
    if points is None or len(points) == 0:
        print("没有点可以显示")
        return

    plt.figure(figsize=(10, 10))

    # 绘制曲线点
    plt.scatter(points[:, 1], points[:, 2], s=1, c=points[:, 0], cmap='viridis')

    # 添加坐标轴
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

    # 标注象限
    x_max = max(abs(points[:, 1].max()), abs(points[:, 1].min()))
    y_max = max(abs(points[:, 2].max()), abs(points[:, 2].min()))
    margin = max(x_max, y_max) * 0.1

    plt.text(x_max - margin, y_max - margin, 'I', fontsize=12)
    plt.text(-x_max + margin, y_max - margin, 'II', fontsize=12)
    plt.text(-x_max + margin, -y_max + margin, 'III', fontsize=12)
    plt.text(x_max - margin, -y_max + margin, 'IV', fontsize=12)

    # 添加颜色条显示参数值
    cbar = plt.colorbar()
    cbar.set_label('参数 t (0 到 2π)')

    plt.axis('equal')
    plt.grid(True, alpha=0.3)
    plt.title('样条曲线')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()


def save_points_to_csv(points, output_path):
    """
    将点坐标保存为CSV文件。

    Args:
        points (numpy.ndarray): 包含(t, x, y)数据的数组
        output_path (str): 输出CSV文件的路径
    """
    if points is None or len(points) == 0:
        print("没有点可以保存")
        return

    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 保存时保留更多小数位
        np.savetxt(output_path, points,
                   fmt='%.6f',  # 保存6位小数
                   delimiter=',',
                   header='t,x,y',
                   comments='')
        print(f"点坐标已保存到 {output_path}")
    except Exception as e:
        print(f"保存CSV文件时出错: {str(e)}")


if __name__ == "__main__":
    import sys
    import os
    import argparse

    parser = argparse.ArgumentParser(description='从DXF文件提取样条曲线数据')
    parser.add_argument('dxf_path', nargs='?', default="太极曲线108点.dxf",
                        help='DXF文件路径')
    parser.add_argument('--output', '-o', default="太极曲线.csv",
                        help='输出CSV文件路径')
    parser.add_argument('--points', '-n', type=int, default=108,
                        help='采样点数量')
    parser.add_argument('--no-plot', action='store_true',
                        help='不显示可视化图形')

    args = parser.parse_args()

    print(f"正在处理文件: {args.dxf_path}")
    points = extract_spline_from_dxf(args.dxf_path, args.points)

    if points is not None and len(points) > 0:
        if not args.no_plot:
            visualize_spline(points)
        save_points_to_csv(points, args.output)
    else:
        print("未能成功提取样条曲线数据")