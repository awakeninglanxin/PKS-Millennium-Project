"""
PKS 黄金比螺旋漏斗 — STL→IBM 三方对比 CFD
光滑墙壁 vs 8bands vs 16bands
归一化到统一尺寸后对比形状对涡量的影响

Z+ = 大口(入水) | Z- = 小口(出水) | 底部口径最小
"""
import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import struct, os, sys
from matplotlib import pyplot as plt

# ============================================================
# 1. STL → r(z) 截面曲线提取
# ============================================================
def extract_profile(stl_path, sample_every=200, n_z=60):
    """从STL提取轴对称 r(z) 曲线"""
    raw = np.fromfile(stl_path, dtype=np.uint8, offset=84)
    n_avail = len(raw) // 50
    v_all = []
    for i in range(0, min(n_avail, 150000), sample_every):
        off = i * 50
        v_all.extend([
            np.frombuffer(raw[off+12:off+24].tobytes(), np.float32),
            np.frombuffer(raw[off+24:off+36].tobytes(), np.float32),
            np.frombuffer(raw[off+36:off+48].tobytes(), np.float32),
        ])
    v = np.array(v_all)
    xs, ys, zs = v[:,0], v[:,1], v[:,2]
    r = np.sqrt(xs**2 + ys**2)
    
    # 分层统计最大半径
    z_edges = np.linspace(zs.min(), zs.max(), n_z+1)
    z_centers = (z_edges[:-1] + z_edges[1:]) / 2
    r_max = np.array([
        r[(zs>=z_edges[i]) & (zs<z_edges[i+1])].max() 
        if ((zs>=z_edges[i]) & (zs<z_edges[i+1])).any() and r[(zs>=z_edges[i]) & (zs<z_edges[i+1])].max() > 0
        else np.nan 
        for i in range(n_z)
    ])
    
    # 插值 NaN
    valid = np.isfinite(r_max)
    if valid.sum() < 2:
        return z_centers, r_max, zs.min(), zs.max()
    r_max = np.interp(z_centers, z_centers[valid], r_max[valid])
    
    return z_centers, r_max, zs.min(), zs.max()


def make_axisymmetric_sdf(z_profile, r_profile, nx, ny, nz, L, 
                          band_perturbation=None):
    """
    从 r(z) 曲线构建轴对称 SDF
    sdf > 0 = 壁外(固体), sdf < 0 = 壁内(流体)
    
    band_perturbation: None(光滑), n_bands(叠加螺旋纹理)
    """
    x = np.linspace(-L/2, L/2, nx)
    y = np.linspace(-L/2, L/2, ny)
    z = np.linspace(-L/2, L/2, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    # 插值 r_wall(z)
    r_wall = np.interp(Z.flatten(), z_profile, r_profile).reshape(nx, ny, nz)
    
    # 基础距离: 正值=壁外
    sdf = R - r_wall
    
    # 叠加螺旋纹理
    if band_perturbation is not None:
        n_bands = band_perturbation
        z_norm = (Z - z_profile[0]) / (z_profile[-1] - z_profile[0])
        # 螺旋相位: theta + z
        phase = Theta + z_norm * n_bands * 2 * np.pi
        # 正弦扰动, 振幅 = 壁面厚度的 3%
        amp = 0.03 * r_wall.max()
        perturbation = amp * np.sin(n_bands * phase) * (r_wall / r_wall.max())
        sdf += perturbation
    
    return sdf, r_wall


# ============================================================
# 2. 3D 谱法 NS + IBM 求解器
# ============================================================
def solve_ns_ibm(sdf, nx, ny, nz, dt, steps, nu, label=""):
    """3D NS + IBM 壁面"""
    L = 2.0
    dx = L / nx
    x = np.linspace(-L/2, L/2, nx)
    
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    
    # 波数
    k = 2j * np.pi * fftfreq(nx, dx)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    k2 = KX**2 + KY**2 + KZ**2
    k2[0,0,0] = 1.0
    dealias = (np.abs(KX.imag * dx) < np.pi*2/3) & \
              (np.abs(KY.imag * dx) < np.pi*2/3) & \
              (np.abs(KZ.imag * dx) < np.pi*2/3)
    
    # Taylor-Green 涡
    u =  np.sin(2*np.pi*X/L) * np.cos(2*np.pi*Y/L) * np.cos(2*np.pi*Z/L)
    v = -np.cos(2*np.pi*X/L) * np.sin(2*np.pi*Y/L) * np.cos(2*np.pi*Z/L)
    w =  np.zeros_like(u)
    
    # 沿Z轴加一个向下的流动 (模拟进水)
    w_inlet_mask = (Z > 0.8 * L/2) & (sdf < 0)  # 顶部流体区
    w[w_inlet_mask] = -0.3  # 向下流入
    
    history = {'vort': [], 'enstrophy': [], 'H3': []}
    
    for step in range(steps):
        # 涡量
        u_k = fftn(u); v_k = fftn(v); w_k = fftn(w)
        wx_k = KY*w_k - KZ*v_k
        wy_k = KZ*u_k - KX*w_k
        wz_k = KX*v_k - KY*u_k
        wx = ifftn(wx_k).real; wy = ifftn(wy_k).real; wz = ifftn(wz_k).real
        omega_mag = np.sqrt(wx**2 + wy**2 + wz**2)
        
        # 非线性项 (对流行式: 物理空间)
        ux = ifftn(KX*u_k).real; uy = ifftn(KY*u_k).real; uz = ifftn(KZ*u_k).real
        vx = ifftn(KX*v_k).real; vy = ifftn(KY*v_k).real; vz = ifftn(KZ*v_k).real
        wx_p = ifftn(KX*w_k).real; wy_p = ifftn(KY*w_k).real; wz_p = ifftn(KZ*w_k).real
        
        Nx = -(u*ux + v*uy + w*uz)
        Ny = -(u*vx + v*vy + w*vz)
        Nz = -(u*wx_p + v*wy_p + w*wz_p)
        
        # IBM 壁面力 (不依赖 u_mag!)
        wall = np.clip(sdf, 0, None) / (sdf.max() + 1e-8)
        penalty = 8.0
        Nx += -penalty * wall * u
        Ny += -penalty * wall * v
        Nz += -penalty * wall * w
        
        # 谱空间投影
        Nx_k = fftn(Nx); Ny_k = fftn(Ny); Nz_k = fftn(Nz)
        div_N = KX*Nx_k + KY*Ny_k + KZ*Nz_k
        Nx_k -= KX * div_N / k2
        Ny_k -= KY * div_N / k2
        Nz_k -= KZ * div_N / k2
        
        # 粘性 + 更新
        visc = np.exp(-nu * k2.real * dt)
        u_k = visc * dealias * (u_k + dt * Nx_k)
        v_k = visc * dealias * (v_k + dt * Ny_k)
        w_k = visc * dealias * (w_k + dt * Nz_k)
        
        u = ifftn(u_k).real
        v = ifftn(v_k).real
        w = ifftn(w_k).real
        
        # 保持入口流动
        w[w_inlet_mask] = np.clip(w[w_inlet_mask], -0.5, 0.5)
        
        if step % 20 == 0:
            history['vort'].append(omega_mag.max())
            history['enstrophy'].append(0.5 * np.mean(omega_mag**2))
            history['H3'].append(np.mean(omega_mag**6)**(1/6))
        
        if step % 100 == 0:
            print(f"  [{label}] step {step:4d}: max|ω|={omega_mag.max():.4f}, "
                  f"H³={history['H3'][-1]:.4f}")
    
    return {
        'label': label,
        'vort': np.array(history['vort']),
        'enstrophy': np.array(history['enstrophy']),
        'H3': np.array(history['H3']),
        'u_final': u, 'v_final': v, 'w_final': w,
    }


# ============================================================
# 3. 主程序
# ============================================================
def main():
    base = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件'
    configs = [
        ('光滑墙壁', os.path.join(base, '黄金比螺旋漏斗光滑墙壁.stl'), None),
        ('8bands',   os.path.join(base, '黄金比螺旋漏斗8bands.stl'), 8),
        ('16bands',  os.path.join(base, '黄金比螺旋漏斗16bands.stl'), 16),
    ]
    
    nx = 48  # 48³ 网格
    L = 2.0
    dt = 0.002
    steps = 300
    nu = 0.008
    n_z_profile = 60
    
    # ---- 第一步: 提取并归一化所有 r(z) 曲线 ----
    profiles = {}
    for label, path, _ in configs:
        zc, rc, zmin, zmax = extract_profile(path, n_z=n_z_profile)
        profiles[label] = (zc, rc, zmin, zmax)
        print(f"{label}: z∈[{zmin:.1f},{zmax:.1f}], r∈[{rc.min():.1f},{rc.max():.1f}]")
    
    # 归一化: Z→[-L/3, L/3], R→[bottom_r, top_r]=[0.1, 0.8]
    z_target_min = -L/3  # 底部
    z_target_max = L/3   # 顶部
    r_bottom = 0.08
    r_top = 0.8
    
    print(f"\n归一化: Z→[{z_target_min:.2f},{z_target_max:.2f}], R→[{r_bottom},{r_top}]")
    
    results = {}
    
    for label, path, n_bands in configs:
        zc, rc, zmin, zmax = profiles[label]
        
        # Z 归一化
        z_norm = z_target_min + (zc - zmin) / (zmax - zmin) * (z_target_max - z_target_min)
        
        # R 归一化: 保持原始长径比, 调整到目标顶半径
        aspect = (zmax - zmin) / (rc.max() * 2)  # 长径比
        r_norm = r_bottom + (rc - rc.min()) / (rc.max() - rc.min()) * (r_top - r_bottom)
        
        print(f"\n--- {label} (bands={n_bands}) ---")
        print(f"  原始长径比={aspect:.2f}, 归一化后顶r={r_top}, 底r≈{r_bottom:.2f}")
        
        # 构建 SDF
        sdf, r_wall = make_axisymmetric_sdf(
            z_norm, r_norm, nx, nx, nx, L,
            band_perturbation=n_bands
        )
        
        # 仿真
        result = solve_ns_ibm(sdf, nx, nx, nx, dt, steps, nu, label)
        results[label] = result
    
    # ---- 第二步: 可视化 ----
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    colors = {'光滑墙壁': 'dodgerblue', '8bands': 'forestgreen', '16bands': 'crimson'}
    
    times = np.arange(0, steps, 20) * dt
    
    # Row 1: 时间序列
    for ci, metric in enumerate(['vort', 'enstrophy', 'H3']):
        ax = axes[0, ci]
        titles = {'vort': 'Max Vorticity', 'enstrophy': 'Enstrophy ½⟨|ω|²⟩', 
                   'H3': 'H³ Sobolev Norm'}
        ax.set_title(titles[metric])
        for label, res in results.items():
            data = res[metric]
            ax.plot(times[:len(data)], data, color=colors[label], 
                    label=label, linewidth=2)
        ax.set_xlabel('Time')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Row 2: 终态 XY 截面 (Z=0 中间层)
    k_mid = nx // 2
    for ci, (label, res) in enumerate(results.items()):
        ax = axes[1, ci]
        u, v, w = res['u_final'], res['v_final'], res['w_final']
        # 计算 Z=0 截面的涡量
        wx = np.gradient(w, axis=1) - np.gradient(v, axis=2)
        wy = np.gradient(u, axis=2) - np.gradient(w, axis=0)
        wz = np.gradient(v, axis=0) - np.gradient(u, axis=1)
        omega_slice = np.sqrt(wx[:,:,k_mid]**2 + wy[:,:,k_mid]**2 + wz[:,:,k_mid]**2)
        omega_slice = np.clip(omega_slice, 0, np.percentile(omega_slice, 99))
        
        im = ax.imshow(omega_slice.T, origin='lower', cmap='hot',
                       extent=[-L/2, L/2, -L/2, L/2])
        ax.set_title(f'{label}\n|ω| @ Z=0 slice (final)')
        plt.colorbar(im, ax=ax, shrink=0.8)
        
        # 叠加壁面轮廓
        r_wall_mid = np.interp(0, z_norm, r_norm)
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(r_wall_mid*np.cos(theta), r_wall_mid*np.sin(theta), 
                'w--', linewidth=1, alpha=0.5)
    
    fig.suptitle('PKS GOLDEN RATIO FUNNEL — STL→IBM CFD\n'
                 '光滑墙壁 vs 8螺旋带 vs 16螺旋带 (归一化同尺寸)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_dir = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明'
    out_png = os.path.join(out_dir, '漏斗STL_IBM_三方对比.png')
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
    print(f"\n[保存] {out_png}")
    
    # 数值摘要
    print("\n" + "="*60)
    print("三方对比总结")
    print("="*60)
    for label, res in results.items():
        v = res['vort']; e = res['enstrophy']; h3 = res['H3']
        print(f"  {label:8s}: max|ω|={v.max():.4f} (增长{v[-1]/v[0]:.2f}x), "
              f"H³ final={h3[-1]:.4f}")

if __name__ == '__main__':
    main()
