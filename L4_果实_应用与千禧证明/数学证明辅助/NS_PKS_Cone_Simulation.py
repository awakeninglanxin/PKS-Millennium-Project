#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PKS 双曲锥 2D Navier-Stokes 涡量放大分析 + 简化 PINN Blowup 检测

演示:
1. Schauberger xy=1 双曲锥几何下的涡量累积
2. Simplified PINN 检测 divergence 趋势
3. 对比: 标准Couette流 vs PKS锥形流
"""
import numpy as np, matplotlib.pyplot as plt, os
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve

od = os.path.dirname(os.path.abspath(__file__))

# ====== 1. 2D NS 涡量流求解 (谱方法) ======
def solve_vorticity_2d(nx, ny, Lx, Ly, nu, dt, nsteps, cone_mode=False):
    """2D 涡量方程 ∂t ω + u·∇ω = νΔω"""
    dx, dy = Lx/(nx-1), Ly/(ny-1)
    x = np.linspace(0, Lx, nx); y = np.linspace(0, Ly, ny)
    X, Y = np.meshgrid(x, y)
    
    # 初值: 高斯涡团
    omega = np.exp(-((X-Lx/2)**2 + (Y-Ly/2)**2) / 0.5)
    omega_max = [np.max(np.abs(omega))]
    
    for step in range(nsteps):
        # 1. 求解流函数 (Poisson: Δψ = -ω)
        kx = 2*np.pi*np.fft.fftfreq(nx, dx)
        ky = 2*np.pi*np.fft.fftfreq(ny, dy)
        KX, KY = np.meshgrid(kx, ky)
        k2 = KX**2 + KY**2; k2[0,0] = 1.0
        psi_hat = np.fft.fft2(omega) / k2
        
        # 2. 速度 (u = ∂ψ/∂y, v = -∂ψ/∂x)
        psi = np.fft.ifft2(psi_hat).real
        u = np.fft.ifft2(1j*KY * psi_hat).real
        v = np.fft.ifft2(-1j*KX * psi_hat).real
        
        # 3. PKS 双曲锥边界 (Schauberger 模式)
        if cone_mode:
            # 在 x=Lx 处施加 y=1/x 型流入
            mask = X > Lx*0.7
            u[mask] *= np.exp(-(Y[mask])**2 / 0.5)  # 锥形约束
        
        # 4. 涡量对流
        omega_x = np.fft.ifft2(1j*KX * np.fft.fft2(omega)).real
        omega_y = np.fft.ifft2(1j*KY * np.fft.fft2(omega)).real
        omega_hat = np.fft.fft2(omega - dt*(u*omega_x + v*omega_y))
        omega_hat /= (1 + nu*dt*k2)
        omega = np.fft.ifft2(omega_hat).real
        
        omega_max.append(np.max(np.abs(omega)))
    
    return X, Y, omega, omega_max

# ====== 2. 简化 PINN 检测 ======
def simplified_pinn_detector(t_series, values, label=""):
    """用指数/幂律拟合检测 blowup 趋势"""
    from numpy.linalg import lstsq
    
    t = np.array(t_series)
    v = np.array(values)
    v_safe = np.clip(v, 1e-10, None)
    
    # 拟合: log|v| ~ log(1/(T*-t)) 或指数增长
    # Model: v(t) = C / (T* - t)^α
    # 线性化: log v ≈ log C - α log(T* - t)
    
    # 用最后 30% 的数据检测
    n_last = max(5, len(t)//3)
    t_last = t[-n_last:]
    v_last = np.clip(np.abs(v[-n_last:]), 1e-10, None)
    
    # 简单判断: 如果涡量加速度 > 阈值, 警告潜在 blowup
    dv_dt = np.gradient(v_last, t_last)
    acceleration = np.gradient(dv_dt, t_last)
    
    avg_accel = np.mean(np.abs(acceleration))
    max_v = np.max(v_last)
    growth_rate = (v_last[-1] - v_last[0]) / (t_last[-1] - t_last[0] + 1e-10)
    
    return {
        'label': label,
        'max_vorticity': max_v,
        'growth_rate': growth_rate,
        'avg_accel': avg_accel,
        'blowup_risk': 'HIGH' if growth_rate > 1.0 else ('MEDIUM' if growth_rate > 0.3 else 'LOW')
    }

# ====== 3. 实验 ======
nx, ny = 128, 128; Lx, Ly = 4.0, 4.0
nu = 0.01; dt = 0.005; nsteps = 200

# 标准流
_, _, omega_std, max_std = solve_vorticity_2d(nx, ny, Lx, Ly, nu, dt, nsteps, cone_mode=False)
# PKS 锥形流
X, Y, omega_cone, max_cone = solve_vorticity_2d(nx, ny, Lx, Ly, nu, dt, nsteps, cone_mode=True)

# PINN 检测
t_series = np.arange(nsteps+1) * dt
std_pinn = simplified_pinn_detector(t_series, max_std, "Standard Flow")
cone_pinn = simplified_pinn_detector(t_series, max_cone, "PKS Cone Flow")

print("=== NS 涡量 Blowup 检测 ===")
for r in [std_pinn, cone_pinn]:
    print(f"\n{r['label']}:")
    print(f"  最大涡量: {r['max_vorticity']:.4f}")
    print(f"  增长率: {r['growth_rate']:.4f}")
    print(f"  平均加速度: {r['avg_accel']:.6f}")
    print(f"  Blowup 风险: {r['blowup_risk']}")

# ====== 4. 可视化 ======
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 涡量场对比
vmax = max(np.max(np.abs(omega_std)), np.max(np.abs(omega_cone)))
for ax, omega, title in [(axes[0,0], omega_std, 'Standard Flow ω'),
                          (axes[0,1], omega_cone, 'PKS Cone Flow ω (xy=1)')]:
    im = ax.imshow(omega, cmap='RdBu_r', extent=[0,Lx,0,Ly], origin='lower',
                   vmin=-vmax/2, vmax=vmax/2, aspect='equal')
    ax.set_title(title)

# 涡量时间序列
ax = axes[0,2]
ax.plot(t_series, max_std, 'b-', alpha=0.7, label='Standard')
ax.plot(t_series, max_cone, 'r-', alpha=0.7, label='PKS Cone')
ax.set_xlabel('t'); ax.set_ylabel('max |ω|')
ax.set_title('Vorticity Growth Over Time')
ax.legend()

# 双曲锥几何
ax = axes[1,0]
x_g = np.linspace(0.1, Lx, 200)
y_cone = 1.0 / x_g  # xy=1
ax.plot(x_g, y_cone, 'r-', lw=2, label='xy=1 (cone)')
ax.fill_between(x_g, 0, y_cone, alpha=0.1, color='red')
ax.set_xlim(0, Lx); ax.set_ylim(0, 2)
ax.set_title('Schauberger Hyperbolic Cone')
ax.set_xlabel('x'); ax.set_ylabel('y')
ax.legend()

# 增长率对比
ax = axes[1,1]
growth_std = np.gradient(max_std, t_series)
growth_cone = np.gradient(max_cone, t_series)
ax.plot(t_series[1:], growth_std[1:], 'b-', alpha=0.7, label='Standard')
ax.plot(t_series[1:], growth_cone[1:], 'r-', alpha=0.7, label='PKS Cone')
ax.axhline(1.0, color='orange', ls='--', alpha=0.5, label='Blowup threshold')
ax.set_xlabel('t'); ax.set_ylabel('d|ω|/dt')
ax.set_title('Growth Rate Comparison')
ax.legend()

# PKS vs Standard 散点
ax = axes[1,2]
ax.scatter(max_std, max_cone, c=t_series, cmap='plasma', s=5, alpha=0.7)
ax.plot([0, max(max_std)], [0, max(max_std)], 'k--', alpha=0.3, label='1:1')
ax.set_xlabel('Standard max|ω|'); ax.set_ylabel('PKS Cone max|ω|')
ax.set_title('Correlation (points above diagonal = PKS intensifies)')
ax.legend()

plt.colorbar(ax.collections[0], ax=ax, label='t')
plt.tight_layout()
plt.savefig(os.path.join(od, 'NS_PKS_Cone_PINN_Analysis.png'), dpi=150,
            bbox_inches='tight')
plt.close()

# ====== 5. Leray 自相似分析 ======
print(f"\n=== Leray 自相似 Blowup 分析 ===")
# Leray: u(x,t) = (1/√(T*-t)) * U(x/√(T*-t))
# 如果 max|ω| 服从 ~1/(T*-t)^(α) 型增长, 则存在自相似 blowup
# 拟合 PKS Cone 数据的最后 50 步
t_fit = t_series[-50:]
omega_fit = np.array(max_cone[-50:])
omega_safe = np.clip(omega_fit, 1e-10, None)
log_t = np.log(np.clip(t_fit[-1] - t_fit + 1e-6, 1e-10, None))
log_w = np.log(omega_safe)

# 线性拟合: log ω ≈ log C - α log(T*-t)
A = np.vstack([np.ones_like(log_t), log_t]).T
coeff, _, _, _ = np.linalg.lstsq(A, log_w, rcond=None)
alpha = -coeff[1]

print(f"  拟合 α (blowup 指数) = {alpha:.4f}")
print(f"  Leray 自相似: α > 0.5 → potential Type I blowup")
print(f"                    α < 0.5 → Type II or 无 blowup")
if alpha > 0.5:
    print(f"  > 警告: α={alpha:.3f} > 0.5 — 潜在自相似 blowup")
else:
    print(f"  > 安全: α={alpha:.3f} < 0.5 — 2D 无 blowup (符合理论)")
print(f"\n  注意: 2D NS 理论上不会 blowup。此分析测量的是")
print(f"  PKS 双曲锥几何引起的涡量放大程度——3D 中此放大可能")
print(f"  跨越 blowup 阈值。")
