import numpy as np
import trimesh

# Parameters
t_max = 1.5*np.pi  # Max value for parameter t
t_min = 0  # Min value for parameter t
d = 5  # Controls the horizontal shift
z_v = 0.5  # Linear rate of movement in the z-axis direction
num_t = 108  # Resolution of parameter t
num_theta = 36  # Resolution of ellipse angle
num_instances = 3  # Number of spiral instances
theta = np.linspace(np.pi, 3* np.pi, num_theta)
# Define t array
t = np.linspace(t_min, t_max, num_t)  # Avoid t = 0
phi = np.linspace(0, 0, num_t)  # Orientation
a = np.linspace(0.05, 0.1, num_t)

# Compute spiral components based on new equations
x_spiral = 1.618 ** (-t / (60 * np.pi / 180)) * -np.cos(t) * 2
y_spiral = 1.618 ** (-t / (60 * np.pi / 180)) * np.sin(t) * 2
z_spiral = t * z_v

# Initialize tangent (T), normal (N), and binormal (B) vectors
T_unit = np.zeros((num_t, 3))  # Tangent vector
N_unit = np.zeros((num_t, 3))  # Normal vector
B_unit = np.zeros((num_t, 3))  # Binormal vector

# Recalculate T(t), N(t), B(t) based on the updated spiral equations
for i in range(num_t):
    # Calculate derivatives for the spiral equations analytically
    factor = 1.618 ** (-t[i] / (60 * np.pi / 180))
    exp_derivative = (-1.618 ** (-t[i] / (60 * np.pi / 180))) * (1 / (60 * np.pi / 180)) * np.log(1.618)

    # First derivative (tangent vector components)
    dx_dt = exp_derivative * -np.cos(t[i]) * 2 + factor * np.sin(t[i]) * 2
    dy_dt = exp_derivative * np.sin(t[i]) * 2 + factor * np.cos(t[i]) * 2
    dz_dt = 1  # Assuming z_v is a constant (e.g., 1)
    T = np.array([dx_dt, dy_dt, dz_dt])
    T_unit[i] = T / np.linalg.norm(T)

    # Second derivative (normal vector components)
    d_exp_derivative_dt = exp_derivative * (-1 / (60 * np.pi / 180))  # Derivative of exp_derivative
    d2x_dt2 = (
            d_exp_derivative_dt * -np.cos(t[i]) * 2 + exp_derivative * np.sin(t[i]) * 2 +
            exp_derivative * np.sin(t[i]) * 2 + factor * np.cos(t[i]) * 2
    )
    d2y_dt2 = (
            d_exp_derivative_dt * np.sin(t[i]) * 2 + exp_derivative * np.cos(t[i]) * 2 +
            exp_derivative * np.cos(t[i]) * 2 - factor * np.sin(t[i]) * 2
    )
    d2z_dt2 = 0  # Since dz/dt is a constant, its second derivative is zero
    N = np.array([d2x_dt2, d2y_dt2, d2z_dt2])
    N_unit[i] = N / np.linalg.norm(N) if np.linalg.norm(N) != 0 else np.array([0, 0, 0])
    # Calculate binormal vector B(t) using cross product of T and N
    B = np.cross(T_unit[i], N_unit[i])
    B_unit[i] = B / np.linalg.norm(B) if np.linalg.norm(B) != 0 else np.array([0, 0, 0])

def rotation_matrix_z(theta):
    """
    Returns the rotation matrix for a rotation around the Z-axis by angle theta (in radians).
    """
    return np.array([[np.cos(theta), -np.sin(theta), 0],
                     [np.sin(theta), np.cos(theta), 0],
                     [0, 0, 1]])

# Function to generate rotation matrix around an arbitrary vector
def rotation_matrix_around_vector(v, psi):
    # Ensure v is a unit vector
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

# Psi values for rotation
psi = np.linspace(0, np.pi, num_t)  # Negative twist

# Initialize spiral shell surface coordinates
X_surface = np.zeros((num_t, num_theta))
Y_surface = np.zeros((num_t, num_theta))
Z_surface = np.zeros((num_t, num_theta))

# Ellipse parameterization functions
def x(theta, a):
    return -a * 2 * np.pi * np.sin(theta) / theta

def y(theta, a):
    return -a * 2 * np.pi * np.cos(theta) / theta

# Generate surface points C(t, theta)
for i in range(num_t):
    for j in range(num_theta):
        scale_factor = 1
        B_term = (x(theta[j], a[i]) * np.cos(phi[i]) - y(theta[j], a[i]) * np.sin(phi[i])) * B_unit[i]
        N_term = (x(theta[j], a[i]) * np.sin(phi[i]) + y(theta[j], a[i]) * np.cos(phi[i])) * N_unit[i]
        R_theta = rotation_matrix_around_vector(T_unit[i], psi[i])
        vector = np.dot(R_theta, (N_term + B_term))
        ellipse_point = scale_factor * vector
        X_surface[i, j] = x_spiral[i] + ellipse_point[0]
        Y_surface[i, j] = y_spiral[i] + ellipse_point[1]
        Z_surface[i, j] = z_spiral[i] + ellipse_point[2]

# Combine vertices for meshing
vertices_spiral = np.column_stack((X_surface.flatten(), Y_surface.flatten(), Z_surface.flatten()))
faces_spiral = []
for i in range(num_t - 1):
    for j in range(num_theta - 1):
        idx1 = i * num_theta + j
        idx2 = i * num_theta + (j + 1)
        idx3 = (i + 1) * num_theta + j
        idx4 = (i + 1) * num_theta + (j + 1)
        faces_spiral.append([idx1, idx2, idx4])
        faces_spiral.append([idx1, idx4, idx3])
faces_spiral = np.array(faces_spiral)

# 生成螺旋的圆周阵列
angle_step = 2 * np.pi / num_instances  # 每个螺旋之间的角度差
vertices_combined = []
faces_combined = []

for n in range(num_instances):
    # 旋转螺旋顶点
    rotation = rotation_matrix_z(n * angle_step)
    rotated_vertices_spiral = vertices_spiral.dot(rotation.T)

    # 将旋转后的螺旋顶点添加到总顶点列表
    vertices_combined.append(rotated_vertices_spiral)

    # 处理 faces 偏移
    faces_spiral_offset = faces_spiral + len(vertices_spiral) * n
    faces_combined.append(faces_spiral_offset)

# 合并所有螺旋顶点和面
vertices_combined = np.vstack(vertices_combined)
faces_combined = np.vstack(faces_combined)

# Use trimesh to create mesh and export as an OBJ file
mesh = trimesh.Trimesh(vertices=vertices_combined, faces=faces_combined)
mesh.export('spiral_fixed.obj')
