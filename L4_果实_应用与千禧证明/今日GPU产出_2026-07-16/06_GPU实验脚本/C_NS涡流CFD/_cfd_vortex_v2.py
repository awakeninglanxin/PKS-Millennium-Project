# -*- coding: utf-8 -*-
"""PKS Cone 涡流可视化 v2 — 解析涡管+GPU等值面"""
import cupy as cp, numpy as np, time, os

OUT = '/root/autodl-tmp/cfd_vortex'
os.makedirs(OUT, exist_ok=True)
cp.cuda.Device(0).use()

print("="*60)
print("PKS 双曲锥 涡管可视化 v2")
print("方法: 解析Burgers涡管+锥面螺旋扰动+等值面")
print("="*60)

N = 256
L = 4.0
x = cp.linspace(-L, L, N, dtype=cp.float32)
y = cp.linspace(-L, L, N, dtype=cp.float32)
z = cp.linspace(-L*1.5, 0.5, N, dtype=cp.float32)
dx = x[1] - x[0]

X, Y, Z = cp.meshgrid(x, y, z, indexing='ij')
R = cp.sqrt(X**2 + Y**2)
theta = cp.arctan2(Y, X)

# ======= PKS 双曲锥几何 =======
# z = -a / (R + eps) — 双曲线锥面
a = 0.6; eps = 0.1
cone_surf = cp.abs(Z + a / (R + eps)) < 0.25
cone_surf &= (R < 3.0) & (R > 0.25)
cone_surf &= (Z > -L*1.4) & (Z < -0.15)

# ======= 主涡管: Burgers 涡旋沿锥面螺线 =======
# 螺线: R_down(t) = R0 * exp(-t/T), Z_down(t) = -a/R(t)
# 涡管沿这条螺线布置
n_turns = 6
t_params = cp.linspace(0, 2*cp.pi*n_turns, 300)
R_spiral = 2.2 * cp.exp(-t_params/(2*cp.pi*n_turns*0.8))
R_spiral = cp.clip(R_spiral, 0.35, 2.8)
Z_spiral = -a / (R_spiral + eps)
theta_spiral = t_params

# 生成涡管: 对每个螺线点，在3D空间累加 Burgers 涡旋
omega_x = cp.zeros((N,N,N), dtype=cp.float32)
omega_y = cp.zeros((N,N,N), dtype=cp.float32)
omega_z = cp.zeros((N,N,N), dtype=cp.float32)

t0 = time.time()
for i in range(len(t_params)):
    r0 = float(R_spiral[i])
    z0 = float(Z_spiral[i])
    th0 = float(theta_spiral[i])
    x0 = r0 * cp.cos(cp.float32(th0))
    y0 = r0 * cp.sin(cp.float32(th0))
    z0_f = cp.float32(z0)
    
    # Burgers 涡旋核半径 (从顶到底收缩)
    core_r = 0.12 + 0.05 * i / len(t_params)
    
    # 点到涡管中心的距离
    dx_v = X - x0; dy_v = Y - y0; dz_v = Z - z0_f
    dist = cp.sqrt(dx_v**2 + dy_v**2 + dz_v**2)
    
    # 涡管方向 (沿螺线的切向)
    if i < len(t_params) - 1:
        n0 = cp.cos(cp.float32(theta_spiral[i])).get() * R_spiral[i].get()
        n1 = cp.cos(cp.float32(theta_spiral[i+1])).get() * R_spiral[i+1].get()
        n2 = cp.sin(cp.float32(theta_spiral[i])).get() * R_spiral[i].get()
        n3 = cp.sin(cp.float32(theta_spiral[i+1])).get() * R_spiral[i+1].get()
        nx = float(n1 - n0)
        ny = float(n3 - n2)
        nz = float(Z_spiral[i+1].get() - Z_spiral[i].get())
        norm = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-10
        nx, ny, nz = nx/norm, ny/norm, nz/norm
    else:
        nx, ny, nz = 0, -1, 0
    
    # Burgers 涡旋: ω ∝ exp(-r²/2σ²) × 螺旋方向
    strength = 0.8 * (1 + 0.5 * i / len(t_params))
    gauss = strength * cp.exp(-dist**2 / (2 * core_r**2))
    gauss *= (dist < 5*core_r)  # 截断
    
    omega_x += gauss * cp.float32(nx)
    omega_y += gauss * cp.float32(ny)
    omega_z += gauss * cp.float32(nz)

dt = time.time() - t0
print(f"  涡管生成: {dt:.1f}s")

# ======= 次级涡管: 沿锥面的小尺度螺旋 =======
t0 = time.time()
n_small = 100
for i in range(n_small):
    t_s = i * 2*cp.pi * 12 / n_small
    r_s = 1.8 * cp.exp(-t_s/(2*cp.pi*12*0.6))
    r_s = float(cp.clip(r_s, 0.5, 2.6))
    th_s = float(t_s) + 0.3 * np.sin(float(t_s))
    z_s = -a / (r_s + eps) - 0.1
    
    x0 = r_s * np.cos(th_s); y0 = r_s * np.sin(th_s)
    core_r = 0.06
    dx_v = X - cp.float32(x0)
    dy_v = Y - cp.float32(y0)
    dz_v = Z - cp.float32(z_s)
    dist = cp.sqrt(dx_v**2 + dy_v**2 + dz_v**2)
    
    # 环向涡
    strength = 0.4 * np.random.uniform(0.5, 1.5)
    gauss = strength * cp.exp(-dist**2 / (2*core_r**2)) * (dist < 3*core_r)
    
    omega_x += -gauss * cp.sin(cp.float32(th_s))
    omega_y += gauss * cp.cos(cp.float32(th_s))
    omega_z += gauss * 0.3

dt2 = time.time() - t0
print(f"  次级涡: {dt2:.1f}s")

# ======= 壁面边界层涡量 =======
t0 = time.time()
boundary = cone_surf & (Z > -L*1.3)
omega_z[boundary] += 0.15 * cp.sin(theta[boundary] * 3) * cp.exp(-(Z[boundary]+1.0)**2/0.5)

# 入口螺旋扰动
inlet = (Z > -0.3) & (Z < -0.05) & (R < 2.5) & (R > 0.3)
omega_z[inlet] += 0.5 * cp.sin(theta[inlet]) * cp.exp(-(R[inlet]-1.2)**2/0.15)
dt3 = time.time() - t0
print(f"  边界层: {dt3:.1f}s")

# ======= 涡量幅值 =======
omega_mag = cp.sqrt(omega_x**2 + omega_y**2 + omega_z**2)
omega_max = float(cp.max(omega_mag))
omega_mean = float(cp.mean(omega_mag[omega_mag > 0.01]))
print(f"\n  涡量: max={omega_max:.3f} mean={omega_mean:.3f}")

# ======= 等值面提取: marching cubes (CPU) =======
# 降采样到 128³ 做 marching cubes
print("\n  等值面提取...")
from skimage import measure
t0 = time.time()

# 取3个等值面层次
omega_np = cp.asnumpy(omega_mag)
iso_levels = [omega_max * 0.12, omega_max * 0.25, omega_max * 0.45]

verts_list, faces_list, level_list = [], [], []
for lvl in iso_levels:
    try:
        verts, faces, _, _ = measure.marching_cubes(omega_np, level=lvl, spacing=(dx,dx,dx))
        verts[:, 0] += float(x[0])
        verts[:, 1] += float(y[0])
        verts[:, 2] += float(z[0])
        verts_list.append(verts)
        faces_list.append(faces)
        level_list.append(lvl)
        print(f"  iso={lvl/omega_max*100:.0f}% | {len(verts):,} verts, {len(faces):,} faces")
    except Exception as e:
        print(f"  iso={lvl/omega_max*100:.0f}% | 跳过 ({e})")

dt4 = time.time() - t0
print(f"  等值面: {dt4:.1f}s")

# ======= 保存 =======
import pickle
data = {
    'verts_list': [v.tolist() for v in verts_list],
    'faces_list': [f.tolist() for f in faces_list],
    'iso_levels': [float(l) for l in level_list],
    'omega_max': omega_max,
    'grid_shape': [N,N,N],
    'bounds': [[float(x[0]), float(x[-1])], [float(y[0]), float(y[-1])], [float(z[0]), float(z[-1])]],
}
with open(f'{OUT}/isosurfaces.pkl', 'wb') as f:
    pickle.dump(data, f)

# 截面图数据 (XZ平面, Y=0)
mid = N // 2
omega_xz = cp.asnumpy(omega_mag[:, mid, :])
np.savez_compressed(f'{OUT}/omega_slice.npz', omega_xz=omega_xz, x=np.asnumpy(x), z=np.asnumpy(z))

# 下载涡量核心数值
np.savez_compressed(f'{OUT}/omega_3d_down.npz', 
    omega_down=cp.asnumpy(omega_mag[::4, ::4, ::4]),
    omega_z_down=cp.asnumpy(omega_z[::4, ::4, ::4]))

print(f"\n✅ 全部保存: {OUT}/")
