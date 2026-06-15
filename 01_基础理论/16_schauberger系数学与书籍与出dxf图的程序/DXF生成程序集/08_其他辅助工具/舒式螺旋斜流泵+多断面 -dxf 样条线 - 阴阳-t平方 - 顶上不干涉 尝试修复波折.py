import numpy as np
import ezdxf
from scipy.interpolate import splprep, splev
from scipy.linalg import norm
from scipy.linalg import solve
from scipy.sparse import diags

def x(t, a):
    """Calculate x coordinate for section curve"""
    return -a * np.pi * np.sin(t) / t


def y(t, a):
    """Calculate y coordinate for section curve"""
    return a * np.pi * np.cos(t) / t


class BSpline:
    def __init__(self, degree):
        self.degree = degree

    def basis(self, knots, u, i, k):
        """Compute B-spline basis function value"""
        if k == 0:
            return 1.0 if knots[i] <= u <= knots[i + 1] else 0.0

        denom1 = knots[i + k] - knots[i]
        denom2 = knots[i + k + 1] - knots[i + 1]

        term1 = 0 if denom1 == 0 else ((u - knots[i]) / denom1) * self.basis(knots, u, i, k - 1)
        term2 = 0 if denom2 == 0 else ((knots[i + k + 1] - u) / denom2) * self.basis(knots, u, i + 1, k - 1)

        return term1 + term2

    def fit(self, points, n_control=None):
        """Fit B-spline curve to points"""
        if n_control is None:
            n_control = len(points)

        # Generate knot vector
        n = n_control - 1
        k = self.degree
        m = n + k + 1
        knots = np.zeros(m + 1)

        # Set end knots
        knots[-(k + 1):] = 1.0

        # Set internal knots
        if n > k:
            internal_knots = np.linspace(0, 1, n - k + 2)[1:-1]
            knots[k + 1:-k - 1] = internal_knots

        # Generate parameter values
        u = np.linspace(0, 1, len(points))

        # Build coefficient matrix
        A = np.zeros((len(points), n_control))
        for i in range(len(points)):
            for j in range(n_control):
                A[i, j] = self.basis(knots, u[i], j, k)

        # Solve for control points
        control_points = np.zeros((n_control, points.shape[1]))
        for dim in range(points.shape[1]):
            # Add regularization for stability
            lambda_reg = 1e-6
            AA = A.T @ A + lambda_reg * np.eye(n_control)
            b = A.T @ points[:, dim]
            control_points[:, dim] = solve(AA, b)

        return knots, control_points

    def evaluate(self, knots, control_points, u):
        """Evaluate B-spline curve at parameter value u"""
        point = np.zeros(control_points.shape[1])
        for i in range(len(control_points)):
            basis = self.basis(knots, u, i, self.degree)
            point += basis * control_points[i]
        return point

class SpiralSweepGenerator:
    """Spiral sweep generator class for creating 3D spiral curves"""

    def __init__(self, t_min=0, t_max=6 * np.pi, d=4.31, z_v=2, amp=0.6,
                 sign_spiral_dir=1, sign=1, twist=-1, f=1.5, angle=0.588, b=1.6, c=1):
        self.t_min = t_min
        self.t_max = t_max
        self.t_length = t_max - t_min
        self.b = b
        self.f = f
        self.angle = angle
        self.c = c
        self.d = d
        self.z_v = z_v
        self.amp = amp
        self.num_t = 42
        self.t_spiral = np.linspace(self.t_min, self.t_max, self.num_t)
        self.a = np.linspace(self.amp, self.amp / 12, self.num_t)
        self.r = sign_spiral_dir
        self.twist = twist
        self.sign = sign
        self.set_default_psi()
        # self.phi = (np.sqrt(5) - 1) / 2
        self.phi = 0.618

        # Generate the initial section curve
        t_section = np.linspace(np.pi, 2.5 * np.pi, 16)
        self.section_x, self.section_y = self.change_section(t_section, self.amp)

    def set_default_psi(self):
        """Set default psi values"""
        self.psi = np.linspace(0, self.twist * self.t_length / 2, self.num_t)

    def set_custom_psi(self, start, end):
        """Set custom psi values"""
        self.psi = np.linspace(self.twist * start, self.twist * end, self.num_t)

    def change_section(self, t_values, a):
        """Generate section curve using given x(t) and y(t) equations"""
        x_vals = x(t_values, a)
        y_vals = y(t_values, a)
        return x_vals, y_vals

    def generate_base_spirals(self, a_list=[180, 180, 180], n_list=[0, 2, 4]):
        """Generate base spiral curves"""
        if len(a_list) != len(n_list):
            raise ValueError("a_list and n_list must have the same length")

        points_per_spiral = self.num_t // len(a_list)
        all_points = []

        for i in range(len(a_list)):
            t = np.linspace(0, 2 * np.pi, points_per_spiral)
            a = a_list[i]
            n = n_list[i]

            r = 2 * np.pi * np.power(self.phi, t / (a * np.pi / 180)) * np.power(self.phi, n)
            x = r * np.cos(t)
            y = r * np.sin(t)

            if i > 0 and len(all_points) > 0:
                prev_point = all_points[-1]
                curr_start = np.array([x[0], y[0]])
                scale = np.sqrt(np.sum(prev_point ** 2)) / np.sqrt(np.sum(curr_start ** 2))
                x *= scale
                y *= scale

            points = np.column_stack((x, y))
            all_points.extend(points)

        return np.array(all_points)

    def get_cone_profile(self, t):
        """Calculate cone height and radius for given parameter"""
        t_max = np.log(18) / self.phi
        if np.any(t > t_max):
            return 0, 0

        z = 2 * np.pi / np.exp(t * np.log(self.phi))
        cone_angle = np.pi / 6
        r = z * np.tan(cone_angle)

        return z, r

    def calculate_spiral_coords(self):
        """Project spiral onto cone surface"""
        spiral_points = self.generate_base_spirals()
        t_max = np.log(18) / self.phi
        t_values = np.linspace(0, t_max, len(spiral_points))

        projected_points = []

        for i, point in enumerate(spiral_points):
            r_original = np.sqrt(point[0] ** 2 + point[1] ** 2)
            if r_original < 1e-10:
                continue

            z_cone, r_cone = self.get_cone_profile(t_values[i])

            if z_cone == 0 or r_cone == 0:
                continue

            scale = r_cone / r_original
            x_proj = point[0] * scale
            y_proj = point[1] * scale

            projected_points.append([x_proj, y_proj, z_cone])

        if not projected_points:
            print("Warning: No valid projected points generated")
            return np.zeros((1, 3))

        points_array = np.array(projected_points)
        return points_array

    def generate_spiral_curves(self):
        """Generate spiral curves with their frame vectors"""
        # Get projected points
        points = self.calculate_spiral_coords()

        # Separate coordinates
        x_spiral = points[:, 0]
        y_spiral = points[:, 1]
        z_spiral = points[:, 2]

        # Fit curve using Rhino-like method
        x_fit, y_fit, z_fit, tck = self.fit_curve_rhino_like(
            points,
            degree=7,
            angle_tolerance=0.05
        )

        # Calculate derivatives
        dx = np.gradient(x_fit, self.t_spiral)
        dy = np.gradient(y_fit, self.t_spiral)
        dz = np.gradient(z_fit, self.t_spiral)

        ddx = np.gradient(dx, self.t_spiral)
        ddy = np.gradient(dy, self.t_spiral)
        ddz = np.gradient(dz, self.t_spiral)

        # Initialize unit vectors
        T_unit = np.zeros((self.num_t, 3))
        N_unit = np.zeros((self.num_t, 3))
        B_unit = np.zeros((self.num_t, 3))

        # Calculate Frenet frame
        for i in range(self.num_t):
            T = np.array([dx[i], dy[i], dz[i]])
            T_unit[i] = T / np.linalg.norm(T)

            N = np.array([ddx[i], ddy[i], ddz[i]])
            N_unit[i] = N / np.linalg.norm(N)

            B = np.cross(T_unit[i], N_unit[i])
            B_unit[i] = B / np.linalg.norm(B)

        center_points = np.column_stack((x_fit, y_fit, z_fit))
        return center_points, [T_unit, N_unit, B_unit]

    @staticmethod
    def fit_curve_rhino_like(points, degree=7, angle_tolerance=0.1, centripetal=True):
        """Fit curve using Rhino-like algorithm with pure Python implementation"""
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Input points must be a (N, 3) shaped array")

        # 计算参数化坐标
        if centripetal:
            chord_lengths = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
            u = np.zeros(len(points))
            u[1:] = np.cumsum(np.sqrt(chord_lengths))
        else:
            chord_lengths = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
            u = np.zeros(len(points))
            u[1:] = np.cumsum(chord_lengths)

        u = u / u[-1]

        # 计算角度变化
        angles = np.zeros(len(points) - 2)
        for i in range(1, len(points) - 1):
            v1 = points[i] - points[i - 1]
            v2 = points[i + 1] - points[i]
            angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
            angles[i - 1] = angle

        # 确定控制点数量
        significant_changes = np.sum(angles > angle_tolerance)
        n_control = min(max(degree + 1, significant_changes + degree), len(points))

        # 创建B样条曲线对象
        spline = BSpline(degree)

        # 拟合曲线
        knots, control_points = spline.fit(points, n_control)

        # 评估拟合点
        u_eval = np.linspace(0, 1, len(points))
        fitted_points = np.array([spline.evaluate(knots, control_points, u_val) for u_val in u_eval])

        # 计算拟合误差
        errors = np.sqrt(np.sum((fitted_points - points) ** 2, axis=1))
        max_error = np.max(errors)

        # 如果误差过大，增加控制点重新拟合
        if max_error > 0.01 and n_control < len(points) - 1:
            n_control += 2
            knots, control_points = spline.fit(points, n_control)
            fitted_points = np.array([spline.evaluate(knots, control_points, u_val) for u_val in u_eval])

        return fitted_points[:, 0], fitted_points[:, 1], fitted_points[:, 2], (knots, control_points, degree)

    def rotation_matrix_around_vector(self, v, psi):
        """Calculate rotation matrix around vector v by angle psi"""
        v = v / np.linalg.norm(v)
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
        """Generate swept sections along the spiral curve"""
        center_points, frame_vectors = self.generate_spiral_curves()
        T_unit, N_unit, B_unit = frame_vectors
        swept_sections = []
        egghead_points = []

        t_values = np.linspace(np.pi, 3 * np.pi, 36)

        for i in range(self.num_t):
            new_section_x, new_section_y = self.change_section(t_values, self.a[i])
            section_points = []

            for j in range(len(new_section_x)):
                R_theta = self.rotation_matrix_around_vector(T_unit[i], self.psi[i])

                B_term = self.sign * new_section_x[j] * B_unit[i]
                N_term = self.sign * new_section_y[j] * N_unit[i]
                vector = np.dot(R_theta, (N_term + B_term))
                global_point = center_points[i] + vector

                if j == 0:
                    egghead_points.append(global_point.tolist())

                section_points.append(global_point.tolist())

            if i == 0 or (i + 1) % 7 == 0:
                swept_sections.append(section_points)

        return swept_sections, center_points.tolist(), egghead_points

    def save_to_dxf(self, filename):
        """Save the generated curves to a DXF file"""
        colors = {
            'center_line': 1,
            'egg_tip': 5,
            'sections': 3,
            'axis': 4
        }

        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()

        swept_sections, center_points, egghead_points = self.sweep_section()

        spline = msp.add_spline(center_points)
        spline.dxf.color = colors['center_line']

        spline = msp.add_spline(egghead_points)
        spline.dxf.color = colors['egg_tip']

        for section in swept_sections:
            spline = msp.add_spline(section)
            spline.dxf.color = colors['sections']

        z_coords = [p[2] for p in center_points]
        line = msp.add_line((0, 0, min(z_coords)), (0, 0, max(z_coords)))
        line.dxf.color = colors['axis']

        doc.saveas(filename)
        print(f"Successfully saved all curves to {filename}")


def main():
    """Main function to generate different spiral models"""
    print("Generating different spiral models...")

    generator = SpiralSweepGenerator()

    # Model 1: Right-facing spiral
    generator.sign = 1
    generator.r = -1
    generator.twist = 1
    generator.save_to_dxf('spiral_1.dxf')
    print("Model 1 generated")

    # Model 2: Left-facing spiral
    generator.sign = -1
    generator.r = -1
    generator.set_default_psi()
    generator.save_to_dxf('spiral_2.dxf')
    print("Model 2 generated")

    # Model 3: Custom twisted spiral
    generator.sign = 1
    generator.r = -1
    generator.set_custom_psi(-np.pi / 2, generator.t_length / 2 - np.pi / 2)
    generator.save_to_dxf('spiral_3.dxf')
    print("Model 3 generated")


if __name__ == "__main__":
    main()