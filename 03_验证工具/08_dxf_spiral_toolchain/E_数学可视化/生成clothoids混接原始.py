import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
from scipy.optimize import minimize
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class ClothoidTransition:
    def __init__(self):
        self.R1 = None
        self.R2 = None
        self.k_max = None
        self.L = None
        self.curve_points = None

    def compute_tangent_angle(self, point, prev_point):
        """计算从prev_point到point的切线角度（弧度）"""
        dx = point[0] - prev_point[0]
        dy = point[1] - prev_point[1]
        return np.arctan2(dy, dx)

    def fresnel_integral(self, s, k_max):
        """计算菲涅尔积分：位置作为弧长s的函数，曲率变化率k_max"""
        # 曲率κ(s) = k_max * s
        # 角度变化θ(s) = ∫₀ˢ κ(u) du = k_max * s² / 2
        # 位置变化: x = ∫₀ˢ cos(θ(u)) du, y = ∫₀ˢ sin(θ(u)) du
        theta_func = lambda u: k_max * u ** 2 / 2
        x_integrand = lambda u: np.cos(theta_func(u))
        y_integrand = lambda u: np.sin(theta_func(u))
        x, _ = quad(x_integrand, 0, s)
        y, _ = quad(y_integrand, 0, s)
        return x, y

    def generate_clothoid_curve(self, start_point, start_angle, k_max, length, num_points=100):
        """生成clothoid曲线段从start_point开始，初始角度start_angle，曲率变化率k_max，长度length"""
        s_values = np.linspace(0, length, num_points)
        points = []
        for s in s_values:
            dx, dy = self.fresnel_integral(s, k_max)
            # 旋转到start_angle方向
            x_rot = dx * np.cos(start_angle) - dy * np.sin(start_angle)
            y_rot = dx * np.sin(start_angle) + dy * np.cos(start_angle)
            x = start_point[0] + x_rot
            y = start_point[1] + y_rot
            points.append((x, y))
        return points

    def generate_s_transition(self, P1, prev_P1, P2, prev_P2, k_max, L=None):
        """生成S形过渡曲线，自动计算R1基于端点位置和切线角度"""
        # 计算切线角度
        theta1 = self.compute_tangent_angle(P1, prev_P1)
        theta2 = self.compute_tangent_angle(P2, prev_P2)

        # 计算端点间距D
        D = np.sqrt((P2[0] - P1[0]) ** 2 + (P2[1] - P1[1]) ** 2)
        L_min = D * np.pi / 2
        if L is None:
            L = L_min
        elif L < L_min:
            print(f"警告: 曲线长度L={L}小于最小要求L_min={L_min}, 使用L_min")
            L = L_min

        # 定义目标函数来优化R1
        def objective(R1):
            R2 = 5 * R1  # 固定比例1:5
            # 生成S形曲线
            curve_points = self._generate_curve_with_R1(P1, theta1, R1, R2, k_max, L)
            if curve_points is None:
                return np.inf
            # 计算终点误差
            end_point = curve_points[-1]
            pos_error = np.sqrt((end_point[0] - P2[0]) ** 2 + (end_point[1] - P2[1]) ** 2)
            # 计算终点切线角度误差（近似）
            if len(curve_points) >= 2:
                dx = curve_points[-1][0] - curve_points[-2][0]
                dy = curve_points[-1][1] - curve_points[-2][1]
                curve_angle = np.arctan2(dy, dx)
                angle_error = abs(curve_angle - theta2)
            else:
                angle_error = np.pi
            return pos_error + angle_error * D  # 加权误差

        # 优化R1
        initial_guess = 10.0  # 初始猜测R1
        bounds = [(0.1, 1000.0)]  # R1的范围
        result = minimize(objective, initial_guess, bounds=bounds, method='L-BFGS-B')
        self.R1 = result.x[0]
        self.R2 = 5 * self.R1
        self.k_max = k_max
        self.L = L

        # 生成最终曲线
        self.curve_points = self._generate_curve_with_R1(P1, theta1, self.R1, self.R2, k_max, L)
        return self.curve_points

    def _generate_curve_with_R1(self, start_point, start_angle, R1, R2, k_max, L):
        """使用给定的R1生成S形曲线"""
        # 计算两个clothoid段的长度
        kappa1 = 1 / R1
        kappa2 = 1 / R2
        L1 = kappa1 / k_max  # 第一段长度
        L2 = kappa2 / k_max  # 第二段长度
        total_length = L1 + L2
        if total_length > L:
            # 调整k_max以满足长度L
            k_max_adj = (kappa1 + kappa2) / L
            L1 = kappa1 / k_max_adj
            L2 = kappa2 / k_max_adj
        else:
            k_max_adj = k_max

        # 生成第一段clothoid: 从曲率0到kappa1
        clothoid1 = self.generate_clothoid_curve(start_point, start_angle, k_max_adj, L1)
        end_point1 = clothoid1[-1]
        end_angle1 = start_angle + k_max_adj * L1 ** 2 / 2  # 角度变化

        # 生成第二段clothoid: 从曲率0到kappa2（方向相反）
        # 第二段起始曲率为0，但方向与第一段结束方向相反
        clothoid2 = self.generate_clothoid_curve(end_point1, end_angle1 + np.pi, -k_max_adj, L2)

        return clothoid1 + clothoid2

    def plot_curve(self, P1, prev_P1, P2, prev_P2):
        """绘制曲线、端点、切线方向"""
        plt.figure(figsize=(10, 6))

        # 绘制曲线
        if self.curve_points is not None:
            points = np.array(self.curve_points)
            plt.plot(points[:, 0], points[:, 1], 'b-', label='S形过渡曲线')

        # 绘制端点和前面点
        plt.plot(P1[0], P1[1], 'ro', label='端点P1')
        plt.plot(prev_P1[0], prev_P1[1], 'go', label='前面点prev_P1')
        plt.plot(P2[0], P2[1], 'ro', label='端点P2')
        plt.plot(prev_P2[0], prev_P2[1], 'go', label='前面点prev_P2')

        # 绘制切线方向
        theta1 = self.compute_tangent_angle(P1, prev_P1)
        theta2 = self.compute_tangent_angle(P2, prev_P2)
        length = 5.0
        plt.arrow(P1[0], P1[1], length * np.cos(theta1), length * np.sin(theta1),
                  head_width=1, head_length=1, fc='r', ec='r', label='切线P1')
        plt.arrow(P2[0], P2[1], length * np.cos(theta2), length * np.sin(theta2),
                  head_width=1, head_length=1, fc='r', ec='r', label='切线P2')

        plt.axis('equal')
        plt.grid(True)
        plt.legend()
        plt.title(f'S形过渡曲线 (R1={self.R1:.2f}, R2={self.R2:.2f}, k_max={self.k_max:.4f})')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()


# 测试用例
if __name__ == "__main__":
    # 定义端点和其他参数
    P1 = np.array([0, 0])
    prev_P1 = np.array([-10, 0])  # P1前面的点，用于计算切线
    P2 = np.array([50, 0])
    prev_P2 = np.array([60, 0])  # P2前面的点，用于计算切线
    k_max = 0.01  # 用户可调曲率变化率
    L = None  # 曲线长度，可选，如果None则使用最小长度

    # 创建对象并生成曲线
    clothoid = ClothoidTransition()
    curve_points = clothoid.generate_s_transition(P1, prev_P1, P2, prev_P2, k_max, L)

    # 输出结果
    print(f"自动计算出的R1: {clothoid.R1:.2f}")
    print(f"对应的R2: {clothoid.R2:.2f}")
    print(f"使用的曲线长度L: {clothoid.L:.2f}")
    print(f"端点间距D: {np.linalg.norm(P2 - P1):.2f}")
    print(f"最小长度要求L_min: {np.linalg.norm(P2 - P1) * np.pi / 2:.2f}")

    # 绘制曲线
    clothoid.plot_curve(P1, prev_P1, P2, prev_P2)
