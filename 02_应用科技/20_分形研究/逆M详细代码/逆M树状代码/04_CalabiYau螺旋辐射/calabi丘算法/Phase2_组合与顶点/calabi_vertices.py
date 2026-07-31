import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

n = 1
angle = 0.5

def calabi_yau(z, k1, k2, alpha, n):
    exp_k1 = np.exp(2 * np.pi * 1j * k1 / n)
    exp_k2 = np.exp(2 * np.pi * 1j * k2 / n)
    z1 = exp_k1 * (np.cosh(z) ** (2 / n))
    z2 = exp_k2 * (np.sinh(z) ** (2 / n))
    return np.real(z1), np.real(z2), np.cos(alpha) * np.imag(z1) + np.sin(alpha) * np.imag(z2)

def create_mesh(n, slices, position, scale, alpha):
    u = np.linspace(-1, 1, slices)
    v = np.linspace(0, np.pi / 2, slices)

    points = []

    for k1 in range(n):
        for k2 in range(n):
            for i in range(slices - 1):
                for j in range(slices - 1):
                    p0 = np.array(calabi_yau(u[i] + 1j * v[j], k1, k2, alpha, n)) * scale
                    p1 = np.array(calabi_yau(u[i + 1] + 1j * v[j], k1, k2, alpha, n)) * scale
                    p2 = np.array(calabi_yau(u[i] + 1j * v[j + 1], k1, k2, alpha, n)) * scale
                    p3 = np.array(calabi_yau(u[i + 1] + 1j * v[j + 1], k1, k2, alpha, n)) * scale

                    points.extend([p0, p1, p2, p3])

    points = np.array(points)
    if points.size == 0:
        return None

    mesh = trimesh.Trimesh(vertices=points + position)
    return mesh

# def update_plot(frame, slices_range, ax):
#     ax.cla()
#     count_red = 0
#     count_green = 0
#     mesh = create_mesh(n, frame, [0, 0, 0], 1, angle)
#     if mesh is not None:
#         x, y, z = mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2]
#         colors = np.where(x + y + z > 0, 'blue', np.where(x + y + z == 0, 'green', 'red'))
#         for i in range(len(colors)):
#             if colors[i] == 'red':
#                 count_red += 1
#             if colors[i] == 'green':
#                 count_green += 1
#         ax.scatter(x, y, z, c=colors)
#         ax.set_title(f'Slices: {frame}, Vertices: {len(mesh.vertices)}, r: {count_red}, g: {count_green}, b: {len(mesh.vertices) - count_red - count_green}')
#         ax.text(0.05, 0.85,0.85, 'when x+y+z>0 is blue; =0 is green, <0 is red', transform=ax.transAxes, fontsize=12, verticalalignment='center_baseline')
#         ax.view_init(elev=0, azim=135)
#     return ax

def update_plot(frame, slices_range, ax):
    ax.cla()
    count_red = 0
    count_green = 0
    mesh = create_mesh(n, frame, [0, 0, 0], 1, angle)
    if mesh is not None:
        x, y, z = mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2]
        colors = np.where(x*y*z > 0, 'blue', np.where(x*y*z == 0, 'green', 'red'))
        for i in range(len(colors)):
            if colors[i] == 'red':
                count_red += 1
            if colors[i] == 'green':
                count_green += 1
        ax.scatter(x, y, z, c=colors)
        ax.set_title(f'Slices: {frame}, Vertices: {len(mesh.vertices)}, r: {count_red}, g: {count_green}, b: {len(mesh.vertices) - count_red - count_green}')
        ax.text(0.05, 0.85,0.85, 'when xyz>0 is blue; =0 is green, <0 is red', transform=ax.transAxes, fontsize=12, verticalalignment='center_baseline')
        ax.view_init(elev=0, azim=135)
    return ax

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

slices_range = range(1, 109)

ani = FuncAnimation(fig, update_plot, frames=slices_range, fargs=(slices_range, ax), interval=200, blit=False)
writer = PillowWriter(fps=2)
ani.save('3d_animation 0.5.gif', writer=writer)

# plt.show()  # If you want to display the plot during development
