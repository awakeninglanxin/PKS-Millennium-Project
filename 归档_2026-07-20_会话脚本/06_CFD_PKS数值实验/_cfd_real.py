# -*- coding: utf-8 -*-
"""PKS Cone 3D 涡流可视化 — RTX 4090 256³ 谱法"""
import cupy as cp, numpy as np, time, os

OUT = '/root/autodl-tmp/cfd_vortex'
os.makedirs(OUT, exist_ok=True)
cp.cuda.Device(0).use()

print("="*60)
print("PKS 双曲锥 3D 涡流模拟")
print("网格: 256³ | Re≈800 | 谱法 + 涡量等值面")
print("="*60)

N = 256
# 物理参数
nu = 1.0 / 800      # 运动粘度 (Re≈800 — 足以产生涡街)
dt = 0.005           # 时间步长
n_steps = 200        # 总步数
save_every = 10      # 每10步保存一帧

# 谱网格
kx = cp.fft.fftfreq(N, d=1./N).astype(cp.float32) * 2*cp.pi  # 物理尺度 2π
ky = cp.fft.fftfreq(N, d=1./N).astype(cp.float32) * 2*cp.pi
kz = cp.fft.fftfreq(N, d=1./N).astype(cp.float32) * 2*cp.pi
Kx, Ky, Kz = cp.meshgrid(kx, ky, kz, indexing='ij')
K2 = Kx**2 + Ky**2 + Kz**2
K2 = cp.maximum(K2, 1e-12)
inv_K2 = 1.0 / K2

# 物理网格
L = 6.0
x = cp.linspace(-L, L, N, dtype=cp.float32)
y = cp.linspace(-L, L, N, dtype=cp.float32)
z = cp.linspace(-L, 0, N, dtype=cp.float32)
X, Y, Z = cp.meshgrid(x, y, z, indexing='ij')
R = cp.sqrt(X**2 + Y**2)

# ======= PKS 锥壁面 (流速边界) =======
# 双曲锥: z_con = -1/R (截断在 z>-L)
cone_r_max = 2.5
cone_r_min = 0.3
cone = (Z <= -0.6 * cp.maximum(R, cone_r_min)) & (R <= cone_r_max) & (Z > -L*0.8)

# 入口: 顶部速度沿锥面螺旋注入
inlet = (Z > -0.15) & (R <= cone_r_max) & (R >= cone_r_min)
u_inlet = cp.zeros((3, N, N, N), dtype=cp.float32)
# 螺旋速度: 切向 + 轴向
theta = cp.arctan2(Y, X)
u_inlet[0, inlet] = -cp.sin(theta[inlet]) * 1.5   # Vx 切向
u_inlet[1, inlet] = cp.cos(theta[inlet]) * 1.5    # Vy 切向  
u_inlet[2, inlet] = -0.8                           # Vz 向下
u_inlet[:, inlet] *= cp.exp(-((R[inlet]-1.0)**2)/0.3)[:, None].T.squeeze()

print(f"  锥体网格: {int(cp.sum(cone)):,} pt | 入口网格: {int(cp.sum(inlet)):,} pt")

# ======= 时步迭代 =======
u_k = cp.zeros((3, N, N, N), dtype=cp.complex64)
omega_frames = []

t0 = time.time()
for step in range(n_steps):
    # 1. 速度场 FFT
    u_x = cp.fft.fftn(u_inlet[0] if step == 0 else u_phys[0])
    u_y = cp.fft.fftn(u_inlet[1] if step == 0 else u_phys[1])
    u_z = cp.fft.fftn(u_inlet[2] if step == 0 else u_phys[2])
    
    # 2. 旋度 → 涡量 (谱空间)
    omega_x_k = 1j * (Ky * u_z - Kz * u_y)
    omega_y_k = 1j * (Kz * u_x - Kx * u_z)
    omega_z_k = 1j * (Kx * u_y - Ky * u_x)
    
    # 3. 涡量 → 物理空间
    omega_x = cp.fft.ifftn(omega_x_k).real
    omega_y = cp.fft.ifftn(omega_y_k).real
    omega_z = cp.fft.ifftn(omega_z_k).real
    omega_mag = cp.sqrt(omega_x**2 + omega_y**2 + omega_z**2)
    
    # 4. 对流项 (涡量形式)
    # ω_t + (u·∇)ω = (ω·∇)u + ν∇²ω
    conv_x_k = 1j * (Ky * cp.fft.fftn(u_phys[1]*omega_z - u_phys[2]*omega_y) + 
                      Kz * cp.fft.fftn(u_phys[2]*omega_x - u_phys[0]*omega_z))
    conv_y_k = 1j * (Kz * cp.fft.fftn(u_phys[2]*omega_x - u_phys[0]*omega_z) +
                      Kx * cp.fft.fftn(u_phys[0]*omega_y - u_phys[1]*omega_x))
    conv_z_k = 1j * (Kx * cp.fft.fftn(u_phys[0]*omega_y - u_phys[1]*omega_x) +
                      Ky * cp.fft.fftn(u_phys[1]*omega_z - u_phys[2]*omega_y))
    
    # 5. 涡量拉伸项 (谱空间: i k × (ω⊗u))
    stretch_x = cp.fft.fftn(omega_x * u_phys[0] + omega_y * u_phys[1] + omega_z * u_phys[2])
    stretch_x_k = 1j * Kx * stretch_x
    
    # 简化: 主要用对流扩散
    # 粘性项: exp(-ν K² dt)
    decay = cp.exp(-nu * K2 * dt)
    
    # 6. 更新涡量
    omega_x_k_new = (omega_x_k - dt * (conv_x_k + stretch_x_k)) * decay
    omega_y_k_new = (omega_y_k - dt * conv_y_k) * decay
    omega_z_k_new = (omega_z_k - dt * conv_z_k) * decay
    
    # 7. 涡量 → 速度 (Biot-Savart: u = ∇×ψ, -∇²ψ=ω)
    psi_x_k = omega_x_k_new * inv_K2
    psi_y_k = omega_y_k_new * inv_K2
    psi_z_k = omega_z_k_new * inv_K2
    
    u_x_new = 1j * (Ky * psi_z_k - Kz * psi_y_k)
    u_y_new = 1j * (Kz * psi_x_k - Kx * psi_z_k)
    u_z_new = 1j * (Kx * psi_y_k - Ky * psi_x_k)
    
    u_phys = cp.stack([cp.fft.ifftn(u_x_new).real,
                       cp.fft.ifftn(u_y_new).real,
                       cp.fft.ifftn(u_z_new).real])
    
    # 8. 锥壁面约束: 无滑移
    u_phys[:, cone] = 0
    
    # 锥面螺旋驱动: 沿壁面注入角动量
    swirl = cp.exp(-((R-1.0)**2)/0.2) * cp.exp(-((Z+1.5)**2)/0.5)
    swirl_mask = (Z > -3) & (R > 0.4) & (R < 2.0) & (Z < -0.3)
    u_phys[0, swirl_mask] += cp.sin(theta[swirl_mask]) * 0.3 * swirl[swirl_mask]
    u_phys[1, swirl_mask] -= cp.cos(theta[swirl_mask]) * 0.3 * swirl[swirl_mask]
    
    # 9. 投影: 确保不可压 (谱空间 ∇·u = 0)
    # 已在 Biot-Savart 重建中隐含满足
    
    # 存入帧
    if step % save_every == 0:
        omega_val = float(cp.max(cp.abs(cp.fft.ifftn(omega_x_k_new).real)))
        ke = float(cp.mean(u_phys[0]**2+u_phys[1]**2+u_phys[2]**2))
        # 保存中截面涡量 (Y=0 切面)
        omega_slice = cp.asnumpy(cp.fft.ifftn(omega_y_k_new).real[:, N//2, :])
        omega_frames.append(omega_slice)
        print(f"  步{step:4d}/{n_steps} | max|ω|={omega_val:.3f} | KE={ke:.4f} | {time.time()-t0:.1f}s")

total_time = time.time() - t0
print(f"\n总耗时: {total_time:.1f}s ({total_time/n_steps*1000:.0f}ms/步)")

# ======= 保存 =======
import pickle
data = {
    'omega_frames': [f.tolist() for f in omega_frames],
    'n_steps': n_steps,
    'save_every': save_every,
    'N': N, 'Re': int(1/nu),
    'total_time': total_time,
    'x_range': [float(x[0]), float(x[-1])],
    'z_range': [float(z[0]), float(z[-1])],
}
with open(f'{OUT}/omega_frames.pkl', 'wb') as f:
    pickle.dump(data, f)
np.savez_compressed(f'{OUT}/omega_final.npz', 
    frames=np.stack([np.array(f) for f in omega_frames]),
    x=np.asnumpy(x), z=np.asnumpy(z))

print(f"✅ 数据保存: {OUT}/")
print(f"   帧数: {len(omega_frames)} | 帧间隔: {save_every}步")
print(f"   每个帧: {omega_frames[0].shape} (X×Z截面)")
