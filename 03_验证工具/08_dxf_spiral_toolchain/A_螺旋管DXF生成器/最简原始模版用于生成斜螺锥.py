import numpy as np
import ezdxf
import pandas as pd
import matplotlib.pyplot as plt


class SpiralSweepGenerator:
    def __init__(self, spline_data_path, t_min=0, t_max=1, diameter=21.25, pitch=1.27/2, high=20, taper_ratio=0.0704,sign=1):
        """
        初始化螺旋扫掠生成器
        """
        self.t_min = t_min
        self.t_max = t_max
        self.base_r = diameter/2
        self.pitch = pitch
        self.num_t = 125
        self.sign = sign
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.r = high*taper_ratio
        self.h_div_pitch=high*np.pi/pitch
        self.h=high
        self.load_section_data(spline_data_path)

    def load_section_data(self, filepath):
        """从DXF文件中加载点，并用直线段连接所有点形成封闭曲线"""
        try:
            # 读取DXF文件
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()

            # 存储2D断面的所有点
            all_points = []

            # 假设DXF文件中包含若干点
            for entity in msp:
                if entity.dxftype() == 'POINT':
                    # 对于点，提取其坐标
                    all_points.append([entity.dxf.location.x, entity.dxf.location.y])

            # 如果没有找到足够的点，则返回
            if len(all_points) < 3:
                print("警告：DXF文件中必须包含至少3个点")
                return None

            # 转换为numpy数组
            all_points = np.array(all_points)

            # 确保断面是闭合的
            if not np.allclose(all_points[0], all_points[-1]):
                all_points = np.append(all_points, [all_points[0]], axis=0)

            # 绘制连接后的封闭曲线
            plt.figure(figsize=(8, 8))
            plt.plot(all_points[:, 0], all_points[:, 1], marker='o', markersize=3, linestyle='-', color='b',
                     label='断面曲线（直线连接）')
            plt.gca().set_aspect('equal', adjustable='box')
            plt.title('加载的2D断面曲线（直线段连接）')
            plt.xlabel('X')
            plt.ylabel('Y')
            plt.grid(True)
            plt.legend()
            plt.show()

            # 将断面数据分配给对象的属性
            self.section_x = all_points[:, 0]
            self.section_y = all_points[:, 1]

            return all_points

        except ezdxf.DXFError as e:
            print(f"DXF文件格式错误: {str(e)}")
            return None
        except Exception as e:
            print(f"处理DXF文件时出错: {str(e)}")
            return None

    def calculate_spiral_coords(self):
        """计算螺旋线的坐标"""
        # 使用新的参数方程来计算螺旋坐标
        x = (self.base_r - self.t_spiral * self.r) * np.cos(self.t_spiral*self.h_div_pitch)
        y = (self.base_r - self.t_spiral * self.r) * np.sin(self.t_spiral*self.h_div_pitch)
        z = self.t_spiral * self.h
        return x, y, z

    def generate_spiral_curves(self):
        """生成两条螺旋轨道线，确保断面正确对齐"""
        x_spiral, y_spiral, z_spiral = self.calculate_spiral_coords()

        # 计算切线向量
        dx = np.gradient(x_spiral, self.t_spiral)
        dy = np.gradient(y_spiral, self.t_spiral)
        dz = np.gradient(z_spiral, self.t_spiral)

        ddx = np.gradient(dx, self.t_spiral)
        ddy = np.gradient(dy, self.t_spiral)
        ddz = np.gradient(dz, self.t_spiral)

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

    def sweep_section(self):
        """使用正确对齐的断面进行扫掠"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        def x(j):
            return self.section_x[j] * self.pitch

        def y(j):
            return self.section_y[j] * self.pitch

        for i in range(self.num_t):
            section_points = []
            for j in range(len(self.section_x)):
                # 在法向量-副法向量平面内构建点
                R_theta = self.rotation_matrix_around_vector(T_unit[i], 0)
                # 计算 ellipse2 的每个点的坐标
                B_term1 = self.sign * x(j) * B_unit[i]
                N_term1 = self.sign * y(j) * N_unit[i]
                vector = np.dot(R_theta, (N_term1 + B_term1))
                global_point = [
                    center_points[i][0] + vector[0],
                    center_points[i][1] + vector[1],
                    center_points[i][2] + vector[2]
                ]
                if j == 0:
                    # 计算并存储蛋尖点的实际3D坐标
                    egghead_point = [
                        center_points[i][0] + vector[0],
                        center_points[i][1] + vector[1],
                        center_points[i][2] + vector[2]
                    ]
                    egghead_points.append(egghead_point)
                section_points.append(global_point)

            swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

    def save_to_dxf(self, filename):
        """保存到DXF文件"""
        # 定义颜色方案
        colors = {
            'center_line': 1,  # 红色
            'egg_tip': 5,  # 蓝色
            'sections': 3,  # 绿色
            'axis': 7  # 黄色
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        # 生成并添加所有曲线
        swept_sections, center_points, egghead_points = self.sweep_section()

        # 添加中心线
        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        # 添加蛋尖线
        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        # 添加所有扫掠断面
        for section in swept_sections:
            # 遍历每个断面点，并使用相邻点作为线段的起点和终点
            for i in range(len(section) - 1):  # 确保至少有两个点
                start_point = section[i]
                end_point = section[i + 1]
                msp.add_line(start_point, end_point).dxf.color = colors['sections']

        # 添加中心轴
        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


# 使用示例
if __name__ == "__main__":
    # 创建口朝右下的模型
    print("以下对应阴阳：")
    print("生成口朝右下的模型d为正...")
    generator_right = SpiralSweepGenerator('三角牙60度.dxf')
    generator_right.sign = 1  #
    generator_right.save_to_dxf('斜螺丝锥.dxf')