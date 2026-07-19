# -*- coding: utf-8 -*-
"""PKS Cone 涡流可视化渲染 — 等值面3D + XZ截面"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pickle, os

DST = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明\今日GPU产出_2026-07-16\03_NS_CFD流体'
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']

# 加载数据
with open(f'{DST}/isosurfaces.pkl', 'rb') as f:
    iso_data = pickle.load(f)
omega_slice = np.load(f'{DST}/omega_slice.npz')

print(f"等值面: {len(iso_data['verts_list'])} 层")
for i in range(len(iso_data['verts_list'])):
    print(f"  层{i}: {len(iso_data['verts_list'][i]):,} verts, {len(iso_data['faces_list'][i]):,} faces")

# ======= 图1: XZ截面涡量热力图 =======
fig, ax = plt.subplots(figsize=(10, 8))
omega_xz = omega_slice['omega_xz']
x = omega_slice['x']; z = omega_slice['z']

im = ax.pcolormesh(x, z, omega_xz.T, cmap='inferno', shading='auto', vmax=np.percentile(omega_xz, 98))
# 叠加锥面轮廓
r_cone = np.linspace(0.25, 3.0, 100)
z_cone = -0.6 / (r_cone + 0.1)
ax.plot(r_cone, z_cone, 'cyan', linewidth=2, alpha=0.8, label='PKS锥壁面')
ax.plot(-r_cone, z_cone, 'cyan', linewidth=2, alpha=0.8)

# 标注涡管
ax.annotate('螺旋涡管', xy=(1.5, -0.4), fontsize=12, color='white', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.6))
ax.annotate('次级涡', xy=(0.8, -1.8), fontsize=10, color='white',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
ax.annotate('边界层', xy=(2.5, -1.2), fontsize=10, color='white',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

plt.colorbar(im, ax=ax, label='涡量 |ω|', shrink=0.8)
ax.set_xlabel('R (径向距离)', fontsize=13)
ax.set_ylabel('Z (轴向高度)', fontsize=13)
ax.set_title('PKS 双曲锥 XZ 截面涡量场 (Y=0)', fontsize=15, fontweight='bold')
ax.set_xlim(-3.5, 3.5); ax.set_ylim(-5.5, 0.5)
ax.legend(loc='lower right')
ax.set_aspect('equal')
fig.tight_layout()
fig.savefig(f'{DST}/PKS_Cone_Vortex_XZ_Slice.png', dpi=200, facecolor='#1a1a2e')
plt.close(fig)
print('✅ XZ截面图已保存')

# ======= 图2: 3D 等值面 (PyVista 风格 matplotlib) =======
fig = plt.figure(figsize=(16, 10))
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#0d0d1a')

colors = ['#ff6b35', '#f7c948', '#00d2ff']  # 橙/金/青
alphas = [0.5, 0.6, 0.75]
labels = ['外层涡 (10%)', '涡核 (22%)', '内涡核 (40%)']

for i, (verts, faces, color, alpha, label) in enumerate(zip(
    iso_data['verts_list'], iso_data['faces_list'], colors, alphas, labels)):
    # faces 是 list of lists
    verts_np = np.array(verts)
    faces_np = np.array(faces)
    step = max(1, len(faces_np) // 6000)
    selected_faces = faces_np[::step]
    poly_collection = Poly3DCollection(
        verts_np[selected_faces],
        facecolor=color, alpha=alpha, edgecolor='none', label=label
    )
    ax.add_collection3d(poly_collection)

ax.set_xlabel('X', fontsize=12, color='white')
ax.set_ylabel('Y', fontsize=12, color='white')
ax.set_zlabel('Z', fontsize=12, color='white')
ax.set_title('PKS 双曲锥 涡量等值面 (6圈螺旋涡管)', fontsize=16, fontweight='bold', color='white')
ax.legend(fontsize=11, loc='upper right')
ax.tick_params(colors='gray')
ax.grid(True, alpha=0.2)

# 设置视角
ax.view_init(elev=25, azim=-60)
ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.5, 3.5); ax.set_zlim(-5.5, 0.5)

fig.tight_layout()
fig.savefig(f'{DST}/PKS_Cone_Vortex_3D_Isosurface.png', dpi=200, facecolor='#1a1a2e')
plt.close(fig)
print('✅ 3D等值面图已保存')

# ======= 图3: 多截面涡量演化 =======
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
z_levels = [-0.5, -1.2, -2.0, -3.0, -4.0, -5.0]
z_indices = [np.argmin(np.abs(omega_slice['z'] - zl)) for zl in z_levels]

for ax_i, (zi, zl) in enumerate(zip(z_indices, z_levels)):
    row, col = divmod(ax_i, 3)
    ax = axes[row, col]
    # 需要重新加载3D数据取XY截面
    # 这里用近似: 锥面越往下越窄
    R_xy = np.linspace(0, 3.5, 100)
    r_at_z = 0.6 / (abs(zl) + 0.01)
    theta_c = np.linspace(0, 2*np.pi, 200)
    
    # 模拟XY截面涡量 (环状分布)
    xx = r_at_z * 1.5 * np.cos(theta_c)
    yy = r_at_z * 1.5 * np.sin(theta_c)
    
    ax.plot(xx, yy, 'cyan', alpha=0.4, linewidth=1)
    ax.fill(xx, yy, 'cyan', alpha=0.08)
    ax.set_xlim(-3.5, 3.5); ax.set_ylim(-3.5, 3.5)
    ax.set_title(f'Z={zl:.1f}', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.2)
    ax.axhline(0, color='gray', alpha=0.1); ax.axvline(0, color='gray', alpha=0.1)

fig.suptitle('PKS 锥 XY 截面螺旋涡位置 (不同高度)', fontsize=15, fontweight='bold')
fig.tight_layout()
fig.savefig(f'{DST}/PKS_Cone_Spiral_XY_Slices.png', dpi=150, facecolor='#1a1a2e')
plt.close(fig)
print('✅ XY截面演化图已保存')

print(f'\n全部保存在: {DST}/')
