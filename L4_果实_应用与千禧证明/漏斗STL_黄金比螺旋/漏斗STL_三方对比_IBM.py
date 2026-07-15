"""
PKS 漏斗 STL 三方对比 CFD — IBM 沉浸边界法
黄金比螺旋漏斗: 光滑墙壁 vs 8bands vs 16bands
Z+ = 大口(入水), Z- = 小口(出水)

关键修复 (vs V8):
- 用真实 STL 几何 (IBM方法), 非 ad-hoc 体力
- 力不依赖 u_mag (去掉正反馈)
- 三组对照: 同网格, 同初始条件, 仅漏斗形状不同
"""
import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
from scipy.integrate import trapezoid
import struct, os, sys
from matplotlib import pyplot as plt

# ============================================================
# 1. STL 解析器 — 构造 SDF 距离场
# ============================================================

def load_stl_binary(path, max_tri=None):
    """读取二进制 STL, 返回顶点数组 (N,9) = [v1x,v1y,v1z, v2x,...,v3z]"""
    with open(path, 'rb') as f:
        f.read(80)  # header
        n_tri = struct.unpack('<I', f.read(4))[0]
        if max_tri:
            n_tri = min(n_tri, max_tri)
        tris = np.zeros((n_tri, 9), dtype=np.float32)
        for i in range(n_tri):
            data = f.read(50)
            if len(data) < 50:
                tris = tris[:i]
                break
            # Skip normal (12 bytes), read 3 vertices (36 bytes)
            tris[i] = struct.unpack('<9f', data[12:48])
        return tris

def build_sdf_from_stl(tris, grid_shape, bounds, margin=0.05):
    """
    从 STL 三角面片构造符号距离场 (SDF).
    正值 = 外部(固体), 负值 = 内部(流体), 0 = 壁面
    
    Args:
        tris: (N,9) 三角面片
        grid_shape: (nx, ny, nz)
        bounds: [xmin,xmax,ymin,ymax,zmin,zmax]
    Returns:
        sdf: (nx,ny,nz) 距离场
    """
    nx, ny, nz = grid_shape
    x = np.linspace(bounds[0], bounds[1], nx)
    y = np.linspace(bounds[2], bounds[3], ny)
    z = np.linspace(bounds[4], bounds[5], nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # 简化的 SDF: 对每个格点, 找最近的三角面片距离
    # 完整 SDF 太慢，这里用采样法: 在 Z 的每层, 找该层三角截面的最近距离
    sdf = np.full((nx, ny, nz), 1e6, dtype=np.float32)
    
    # 提取所有顶点并计算每层的截面
    all_v = tris.reshape(-1, 3)
    
    # 对每层 Z, 找该层截面半径
    z_min, z_max = bounds[4], bounds[5]
    dz = (z_max - z_min) / nz
    
    for k in range(nz):
        zk = z[k]
        # 找 STL 中接近该 Z 高度的顶点
        mask = np.abs(all_v[:, 2] - zk) < dz * 2
        if not mask.any():
            # 用最近的 Z 层插值
            closest_k = np.argmin(np.abs(all_v[:, 2] - zk))
            # 用该层的横截面半径
            pass
        
        z_verts = all_v[mask]
        if len(z_verts) > 0:
            # 该层横截面半径 = max(|x|+|y| 或者 sqrt(x²+y²))
            radii = np.sqrt(z_verts[:, 0]**2 + z_verts[:, 1]**2)
            r_wall = np.max(radii) if len(radii) > 0 else 1e6
        else:
            # 插值: 找最近的两层
            continue
        
        # 对格点阵: 距离 = r_wall - sqrt(X²+Y²)
        for j in range(ny):
            for i in range(nx):
                r_point = np.sqrt(X[i,j,k]**2 + Y[i,j,k]**2)
                # 正值 = 在壁外(固体), 负值 = 在壁内(流体)
                sdf[i,j,k] = r_point - r_wall
    
    # 清理: 无穷大替换为最大值
    sdf[sdf > 1e5] = sdf[sdf < 1e5].max()
    
    # 顶面和底面边界
    # Z+ 入口区域: 全是流体
    top_k = int(0.95 * nz)  # 顶部不设壁
    for k in range(top_k, nz):
        sdf[:,:,k] = -1.0  # 确保顶部区域是流体
        
    return sdf


def compute_ibm_force(sdf, u, v, w, dt, penalty=10.0):
    """
    IBM 体积力: 对壁内区域 (sdf>0) 施加惩罚力, 把速度推到0
    不依赖 u_mag, 仅用 sdf 的距离权重
    """
    nx, ny, nz = sdf.shape
    
    # 壁面区域 mask: sdf > 0 = 固体
    wall = np.clip(sdf, 0, None) / (np.max(sdf) + 1e-8)  # 归一化到 [0,1]
    
    # 惩罚力 = -penalty * wall * velocity (无滑移)
    fx = -penalty * wall * u
    fy = -penalty * wall * v
    fz = -penalty * wall * w
    
    return fx, fy, fz


# ============================================================
# 2. 3D 伪谱 NS 求解器
# ============================================================

def solve_ns_3d(nx, ny, nz, dt, steps, nu, sdf, cone_label="funnel"):
    """3D 伪谱 NS 求解器 + IBM 壁面"""
    
    L = 2.0
    x = np.linspace(-L/2, L/2, nx)
    y = np.linspace(-L/2, L/2, ny)
    z = np.linspace(-L/2, L/2, nz)
    dx = x[1] - x[0]
    
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # 波数
    kx = 2j*np.pi*fftfreq(nx, dx)
    ky = 2j*np.pi*fftfreq(ny, dx)
    kz = 2j*np.pi*fftfreq(nz, dx)
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
    k2 = KX**2 + KY**2 + KZ**2
    k2[0,0,0] = 1.0  # 避免除零
    dealias = (np.abs(KX.imag*dx) < np.pi*2/3) & \
              (np.abs(KY.imag*dx) < np.pi*2/3) & \
              (np.abs(KZ.imag*dx) < np.pi*2/3)
    
    # 初始条件: Taylor-Green 涡
    u =  np.sin(X) * np.cos(Y) * np.cos(Z)
    v = -np.cos(X) * np.sin(Y) * np.cos(Z)
    w =  np.zeros_like(u)
    
    # 历史记录
    max_vort = []
    enstrophy = []
    H3_norm = []
    
    print(f"  [{cone_label}] 开始仿真: {steps} 步, dt={dt}, nu={nu}")
    
    for step in range(steps):
        # 计算涡量
        ux = np.fft.ifftn(KX * np.fft.fftn(u)).real
        uy = np.fft.ifftn(KY * np.fft.fftn(u)).real
        uz = np.fft.ifftn(KZ * np.fft.fftn(u)).real
        vx = np.fft.ifftn(KX * np.fft.fftn(v)).real
        vy = np.fft.ifftn(KY * np.fft.fftn(v)).real
        wz = np.fft.ifftn(KZ * np.fft.fftn(w)).real
        
        # 涡量 ω = ∇×u
        wx = np.fft.ifftn(KY*np.fft.fftn(w) - KZ*np.fft.fftn(v)).real
        wy = np.fft.ifftn(KZ*np.fft.fftn(u) - KX*np.fft.fftn(w)).real
        omega_z = np.fft.ifftn(KX*np.fft.fftn(v) - KY*np.fft.fftn(u)).real
        
        omega_mag = np.sqrt(wx**2 + wy**2 + omega_z**2)
        
        # 非线性项
        Nx = -(u*ux + v*uy + w*uz)
        Ny = -(u*vx + v*vy + w*wz)  # 简化: z 导数用 central diff
        # 实际 3D 非线性项需要完整的 z 分量
        wz_nl = -wz  # placeholder - 保持保守
        
        # IBM 壁面力
        fx, fy, fz = compute_ibm_force(sdf, u, v, w, dt)
        
        Nx += fx
        Ny += fy
        
        # 频谱
        Nx_k = np.fft.fftn(Nx)
        Ny_k = np.fft.fftn(Ny)
        u_k = np.fft.fftn(u)
        v_k = np.fft.fftn(v)
        w_k = np.fft.fftn(w)
        
        # 投影: P = I - kk^T/k^2
        div_N = KX*Nx_k + KY*Ny_k
        Nx_k_proj = Nx_k - KX * div_N / k2
        Ny_k_proj = Ny_k - KY * div_N / k2
        
        # 粘性项
        visc = np.exp(-nu * k2.real * dt)
        
        # 更新
        u_k = visc * dealias * (u_k + dt * Nx_k_proj)
        v_k = visc * dealias * (v_k + dt * Ny_k_proj)
        w_k = visc * dealias * (w_k + dt * (-KZ*div_N/k2))
        
        u = np.fft.ifftn(u_k).real
        v = np.fft.ifftn(v_k).real
        w = np.fft.ifftn(w_k).real
        
        if step % 25 == 0:
            max_omega = omega_mag.max()
            ens = 0.5 * np.mean(omega_mag**2)
            H3_val = np.mean(omega_mag**6)**(1/6)  # 近似 H³ 范数
            
            max_vort.append(max_omega)
            enstrophy.append(ens)
            H3_norm.append(H3_val)
            
            if step % 100 == 0:
                print(f"  [{cone_label}] step {step:4d}: max|ω|={max_omega:.3f}, H³≈{H3_val:.3f}")
    
    return {
        'label': cone_label,
        'max_vort': np.array(max_vort),
        'enstrophy': np.array(enstrophy),
        'H3_norm': np.array(H3_norm),
        'u_final': u, 'v_final': v, 'w_final': w,
    }


# ============================================================
# 3. 主程序: 三方对比
# ============================================================

def main():
    base = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件'
    stl_files = [
        ('光滑墙壁', os.path.join(base, '黄金比螺旋漏斗光滑墙壁.stl')),
        ('8bands',   os.path.join(base, '黄金比螺旋漏斗8bands.stl')),
        ('16bands',  os.path.join(base, '黄金比螺旋漏斗16bands.stl')),
    ]
    
    # 网格和物理参数
    nx, ny, nz = 32, 32, 32  # 3D 网格
    L = 2.0
    bounds = [-L/2, L/2, -L/2, L/2, -L/2, L/2]
    dt = 0.002
    steps = 200
    nu = 0.01
    
    print("="*60)
    print("PKS 漏斗 STL 三方对比 CFD 仿真")
    print(f"网格: {nx}³ | dt={dt} | steps={steps} | nu={nu}")
    print("="*60)
    
    results = {}
    
    for label, stl_path in stl_files:
        print(f"\n--- 加载 STL: {label} ---")
        tris = load_stl_binary(stl_path, max_tri=50000)
        print(f"  三角面: {len(tris)}")
        
        # 提取几何范围
        all_v = tris.reshape(-1, 3)
        print(f"  X: [{all_v[:,0].min():.2f}, {all_v[:,0].max():.2f}]")
        print(f"  Y: [{all_v[:,1].min():.2f}, {all_v[:,1].max():.2f}]")
        print(f"  Z: [{all_v[:,2].min():.2f}, {all_v[:,2].max():.2f}]")
        
        # 构建 SDF
        sdf = build_sdf_from_stl(tris, (nx, ny, nz), bounds)
        
        # 运行仿真
        result = solve_ns_3d(nx, ny, nz, dt, steps, nu, sdf, label)
        results[label] = result
    
    # ============================================================
    # 4. 可视化对比
    # ============================================================
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    colors = {'光滑墙壁': 'blue', '8bands': 'green', '16bands': 'red'}
    
    # Row 1: max|ω| 和 enstrophy
    times = np.arange(0, steps, 25) * dt
    
    ax = axes[0, 0]
    for label, res in results.items():
        ax.plot(times[:len(res['max_vort'])], res['max_vort'], 
                color=colors[label], label=label, linewidth=2)
    ax.set_ylabel('max|ω|')
    ax.set_title('Max Vorticity')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[0, 1]
    for label, res in results.items():
        ax.plot(times[:len(res['enstrophy'])], res['enstrophy'],
                color=colors[label], linewidth=2)
    ax.set_ylabel('Enstrophy ½⟨|ω|²⟩')
    ax.set_title('Enstrophy')
    ax.grid(True, alpha=0.3)
    
    ax = axes[0, 2]
    for label, res in results.items():
        ax.plot(times[:len(res['H3_norm'])], res['H3_norm'],
                color=colors[label], linewidth=2)
    ax.set_ylabel('H³ 范数 ≈ ⟨|ω|⁶⟩^(1/6)')
    ax.set_title('H³ Sobolev Norm')
    ax.grid(True, alpha=0.3)
    
    # Row 2: 终态 XY 截面 (z=0) 涡量场
    for ci, (label, res) in enumerate(results.items()):
        ax = axes[1, ci]
        k_mid = nz // 2
        omega_final = np.sqrt(
            np.gradient(res['w_final'], axis=1)**2 +  # ∂w/∂y
            np.gradient(res['v_final'], axis=0)**2    # ∂v/∂x (简化)
        )
        omega_slice = omega_final[:,:,k_mid] if omega_final.ndim == 3 else omega_final[:,:,k_mid]
        im = ax.imshow(omega_slice.T, origin='lower', cmap='RdBu_r',
                       extent=[bounds[0],bounds[1],bounds[2],bounds[3]])
        ax.set_title(f'{label}\n|ω| @ z=0 slice')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        plt.colorbar(im, ax=ax)
    
    # Summary
    fig.suptitle('PKS 漏斗对比: 光滑墙壁 vs 8bands vs 16bands\n'
                 '真实STL几何 → IBM沉浸边界法',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_dir = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\L4_果实_应用与千禧证明'
    out_png = os.path.join(out_dir, '漏斗STL_三方对比_IBM.png')
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
    print(f"\n[完成] 保存到 {out_png}")
    
    # 数值总结
    print("\n" + "="*60)
    print("三方对比总结")
    print("="*60)
    for label, res in results.items():
        mv = res['max_vort']
        ens = res['enstrophy']
        print(f"  {label:8s}: max|ω|={mv.max():.3f}, "
              f"final enstrophy={ens[-1]:.4f}, "
              f"growth={mv[-1]/mv[0]:.2f}x")

if __name__ == '__main__':
    main()
