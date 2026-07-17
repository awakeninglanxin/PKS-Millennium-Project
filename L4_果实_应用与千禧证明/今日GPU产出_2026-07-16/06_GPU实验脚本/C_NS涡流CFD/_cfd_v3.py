# -*- coding: utf-8 -*-
"""PKS Cone 涡流可视化 v3 — CPU参数+GPU涡量+等值面"""
import cupy as cp, numpy as np, time, os

OUT = '/root/autodl-tmp/cfd_vortex'
os.makedirs(OUT, exist_ok=True)
cp.cuda.Device(0).use()

print("=" * 60)
print("PKS 双曲锥 涡管可视化 v3")
print("=" * 60)

N = 256
L = 4.0
x = np.linspace(-L, L, N, dtype=np.float32)
y = np.linspace(-L, L, N, dtype=np.float32)
z = np.linspace(-L * 1.5, 0.5, N, dtype=np.float32)
dx = x[1] - x[0]

X, Y, Z = cp.meshgrid(cp.asarray(x), cp.asarray(y), cp.asarray(z), indexing='ij')
R = cp.sqrt(X**2 + Y**2)
theta = cp.arctan2(Y, X)

# ======= PKS 双曲锥 =======
a = 0.6; eps = 0.1
cone_surf = cp.abs(Z + a / (R + eps)) < 0.25
cone_surf &= (R < 3.0) & (R > 0.25)
cone_surf &= (Z > -L * 1.4) & (Z < -0.15)

# ======= 螺旋涡管参数 (纯CPU) =======
n_turns = 6
n_pts = 300
t_vals = np.linspace(0, 2 * np.pi * n_turns, n_pts)
r_vals = 2.2 * np.exp(-t_vals / (2 * np.pi * n_turns * 0.8))
r_vals = np.clip(r_vals, 0.35, 2.8)
z_vals = -a / (r_vals + eps)
th_vals = t_vals

x_vals = r_vals * np.cos(th_vals)
y_vals = r_vals * np.sin(th_vals)

# 涡管切向 (数值差分)
dx_vals = np.diff(x_vals); dy_vals = np.diff(y_vals); dz_vals = np.diff(z_vals)
norms = np.sqrt(dx_vals**2 + dy_vals**2 + dz_vals**2) + 1e-10
nx_vals = np.append(dx_vals, dx_vals[-1]) / np.append(norms, norms[-1])
ny_vals = np.append(dy_vals, dy_vals[-1]) / np.append(norms, norms[-1])
nz_vals = np.append(dz_vals, dz_vals[-1]) / np.append(norms, norms[-1])

print(f"  涡管线: {n_pts} pts, {n_turns} turns, R: {r_vals[0]:.1f}→{r_vals[-1]:.2f}")

# ======= GPU 累加涡量场 =======
omega_x = cp.zeros((N, N, N), dtype=cp.float32)
omega_y = cp.zeros((N, N, N), dtype=cp.float32)
omega_z = cp.zeros((N, N, N), dtype=cp.float32)

t0 = time.time()
for i in range(n_pts):
    x0 = cp.float32(x_vals[i])
    y0 = cp.float32(y_vals[i])
    z0 = cp.float32(z_vals[i])
    core_r = 0.12 + 0.05 * i / n_pts
    
    dx_v = X - x0; dy_v = Y - y0; dz_v = Z - z0
    dist = cp.sqrt(dx_v**2 + dy_v**2 + dz_v**2)
    
    strength = 0.8 * (1 + 0.5 * i / n_pts)
    gauss = strength * cp.exp(-dist**2 / (2 * core_r**2))
    gauss *= (dist < 5 * core_r)
    
    omega_x += gauss * cp.float32(nx_vals[i])
    omega_y += gauss * cp.float32(ny_vals[i])
    omega_z += gauss * cp.float32(nz_vals[i])

dt = time.time() - t0
print(f"  主涡管生成: {dt:.1f}s")

# ======= 次级小涡管 =======
t0 = time.time()
n_small = 80
for i in range(n_small):
    t_s = i * 2 * np.pi * 12 / n_small
    r_s = 1.8 * np.exp(-t_s / (2 * np.pi * 12 * 0.6))
    r_s = np.clip(r_s, 0.5, 2.6)
    th_s = t_s + 0.3 * np.sin(t_s)
    z_s_val = -a / (r_s + eps) - 0.1
    
    x0 = cp.float32(r_s * np.cos(th_s))
    y0 = cp.float32(r_s * np.sin(th_s))
    z0 = cp.float32(z_s_val)
    core_r = 0.06
    
    dx_v = X - x0; dy_v = Y - y0; dz_v = Z - z0
    dist = cp.sqrt(dx_v**2 + dy_v**2 + dz_v**2)
    
    strength = 0.4 * np.random.uniform(0.5, 1.5)
    gauss = strength * cp.exp(-dist**2 / (2 * core_r**2)) * (dist < 3 * core_r)
    
    omega_x += -gauss * cp.sin(cp.float32(th_s))
    omega_y += gauss * cp.cos(cp.float32(th_s))

print(f"  次级涡: {time.time()-t0:.1f}s")

# ======= 锥壁面边界层 =======
t0 = time.time()
boundary = cone_surf & (Z > -L * 1.3)
omega_z[boundary] += 0.15 * cp.sin(theta[boundary] * 3) * cp.exp(-(Z[boundary] + 1.0)**2 / 0.5)
# 入口扰动
inlet = (Z > -0.3) & (Z < -0.05) & (R < 2.5) & (R > 0.3)
omega_z[inlet] += 0.5 * cp.sin(theta[inlet]) * cp.exp(-(R[inlet] - 1.2)**2 / 0.15)
print(f"  边界层+入口: {time.time()-t0:.1f}s")

# ======= 涡量幅值 =======
omega_mag = cp.sqrt(omega_x**2 + omega_y**2 + omega_z**2)
omega_max = float(cp.max(omega_mag))
print(f"\n  涡量: max={omega_max:.3f}")

# ======= 等值面 marching cubes =======
from skimage import measure
omega_cpu = cp.asnumpy(omega_mag)

iso_levels = [omega_max * p for p in [0.10, 0.22, 0.40]]
verts_list, faces_list = [], []

t0 = time.time()
for lvl in iso_levels:
    try:
        verts, faces, _, _ = measure.marching_cubes(omega_cpu, level=lvl, spacing=(dx, dx, dx))
        verts[:, 0] += float(x[0]); verts[:, 1] += float(y[0]); verts[:, 2] += float(z[0])
        verts_list.append(verts); faces_list.append(faces)
        pct = lvl / omega_max * 100
        print(f"  iso={pct:.0f}% | {len(verts):,} verts, {len(faces):,} faces")
    except Exception as e:
        print(f"  iso={lvl/omega_max*100:.0f}% | skip: {e}")

print(f"  等值面: {time.time()-t0:.1f}s")

# ======= 保存 =======
import pickle, json
data = {
    'verts_list': [v.tolist() for v in verts_list],
    'faces_list': [f.tolist() for f in faces_list],
    'iso_levels': [float(l) for l in iso_levels],
    'omega_max': omega_max,
    'bounds': [[float(x[0]), float(x[-1])], [float(y[0]), float(y[-1])], [float(z[0]), float(z[-1])]],
    'n_verts': [len(v) for v in verts_list],
    'n_faces': [len(f) for f in faces_list],
}
with open(f'{OUT}/isosurfaces.pkl', 'wb') as f:
    pickle.dump(data, f)

# XZ 截面 (Y=0)
mid = N // 2
omega_xz = cp.asnumpy(omega_mag[:, mid, :])
np.savez_compressed(f'{OUT}/omega_slice.npz', omega_xz=omega_xz, x=x, z=z)

# 统计
stats = {
    'omega_max': float(omega_max),
    'omega_mean': float(cp.mean(omega_mag[omega_mag > 0.01])),
    'n_iso_surfaces': len(verts_list),
    'total_verts': sum(len(v) for v in verts_list),
    'total_faces': sum(len(f) for f in faces_list),
    'cone_pts': int(cp.sum(cone_surf)),
}
with open(f'{OUT}/stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print(f"\n✅ {OUT}/")
print(f"   等值面: {len(verts_list)} 层, {stats['total_verts']:,} 顶点")
print(f"   XZ截面: {omega_xz.shape}")
