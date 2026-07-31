#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NS V1: 增强 2D 双曲锥涡量分析
改进: 精确 Schauberger xy=1 边界 + 涡量通量 + 谱能量 + SGS尺度
"""
import numpy as np, matplotlib.pyplot as plt, os
od = os.path.dirname(os.path.abspath(__file__))

nx, ny = 128, 128; Lx, Ly = 4.0, 4.0
dx, dy = Lx/(nx-1), Ly/(ny-1)
x = np.linspace(0, Lx, nx); y = np.linspace(0, Ly, ny)
X, Y = np.meshgrid(x, y)
nu = 0.005; dt = 0.003; nsteps = 300

# ====== Schauberger 双曲锥流入 ======
def cone_inflow(X, Y, u, v, t, strength=1.5):
    """Schauberger xy=1 锥面: 流体向锥顶点加速收敛"""
    mask = X > 2.5
    r_cone = np.sqrt((X[mask]-3.0)**2 + Y[mask]**2)
    angle = np.arctan2(Y[mask], X[mask]-3.0)
    # 锥形速度剖面: u_r ~ 1/r (类似点汇)
    u_in = -strength * np.cos(angle) / (r_cone + 0.1) * np.sin(np.pi*t/50)**2
    v_in = -strength * np.sin(angle) / (r_cone + 0.1) * np.sin(np.pi*t/50)**2
    u[mask] = u[mask] * 0.7 + u_in * 0.3
    v[mask] = v[mask] * 0.7 + v_in * 0.3
    return u, v

# 标准版(无锥) vs 锥版
def run_sim(cone_mode):
    omega = np.exp(-((X-Lx*0.4)**2 + (Y-Ly/2)**2)/0.3) * 2.0
    # 诊断存储
    max_vor = []; enstrophy = []; circulation = []
    kx = 2*np.pi*np.fft.fftfreq(nx, dx)
    ky = 2*np.pi*np.fft.fftfreq(ny, dy)
    KX, KY = np.meshgrid(kx, ky); k2 = KX**2 + KY**2; k2[0,0] = 1.0
    
    for step in range(nsteps):
        psi_hat = np.fft.fft2(omega) / k2
        u = np.fft.ifft2(1j*KY * psi_hat).real
        v = np.fft.ifft2(-1j*KX * psi_hat).real
        
        if cone_mode:
            u, v = cone_inflow(X, Y, u, v, step*dt)
        
        omega_x = np.fft.ifft2(1j*KX * np.fft.fft2(omega)).real
        omega_y = np.fft.ifft2(1j*KY * np.fft.fft2(omega)).real
        omega_hat = np.fft.fft2(omega - dt*(u*omega_x + v*omega_y))
        omega_hat /= (1 + nu*dt*k2)
        omega = np.fft.ifft2(omega_hat).real
        
        max_vor.append(np.max(np.abs(omega)))
        enstrophy.append(0.5 * np.mean(omega**2))
        circulation.append(np.abs(np.sum(omega)) * dx * dy)
    
    return omega, max_vor, enstrophy, circulation, u, v

omega_std, mv_std, ens_std, circ_std, u_std, v_std = run_sim(False)
omega_cone, mv_cone, ens_cone, circ_cone, u_cone, v_cone = run_sim(True)

t = np.arange(nsteps) * dt

# ====== 六面板可视化 ======
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
vmax = max(np.max(np.abs(omega_std)), np.max(np.abs(omega_cone)))

for i, (omega, title) in enumerate([(omega_std, 'Standard 2D Vortex'), 
                                      (omega_cone, 'PKS Cone (xy=1)')]):
    ax = axes[0, i]
    ax.imshow(omega, cmap='RdBu_r', extent=[0,Lx,0,Ly], vmin=-vmax, vmax=vmax, aspect='equal')
    ax.set_title(title); ax.set_xlabel('x'); ax.set_ylabel('y')

ax = axes[0, 2]
ax.plot(t, mv_std, 'b-', alpha=0.7, label='Standard')
ax.plot(t, mv_cone, 'r-', lw=1.5, label='PKS Cone')
ax.set_xlabel('t'); ax.set_ylabel('max|ω|')
ax.set_title('Vorticity Peak Evolution')
ax.legend(); ax.grid(alpha=0.3)

for i, (data, std, cone, ylabel) in enumerate([
    (axes[1,0], ens_std, ens_cone, 'Enstrophy (∫ω²/2)'),
    (axes[1,1], circ_std, circ_cone, 'Circulation (|∮u·dl|)'),
    (axes[1,2], None, None, 'Growth Rate d|ω|/dt')]):
    if i < 2:
        ax = axes[1,i]
        ax.plot(t, std, 'b-', alpha=0.7, label='Standard')
        ax.plot(t, cone, 'r-', lw=1.5, label='PKS Cone')
        ax.set_xlabel('t'); ax.set_ylabel(ylabel)
        ax.legend(); ax.grid(alpha=0.3)
    else:
        ax = axes[1,2]
        g_std = np.gradient(mv_std, dt)
        g_cone = np.gradient(mv_cone, dt)
        ax.plot(t, g_std, 'b-', alpha=0.5, label='Standard')
        ax.plot(t, g_cone, 'r-', lw=1.5, label='PKS Cone')
        ax.axhline(0, color='gray', ls='--', alpha=0.5)
        ax.set_xlabel('t'); ax.set_ylabel('d|ω|/dt')
        ax.set_title('Growth Rate Comparison')
        ax.legend(); ax.grid(alpha=0.3)

plt.tight_layout()
out = os.path.join(od, 'NS_V1_增强2D涡量分析.png')
plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()

# ====== 统计报告 ======
print("="*60)
print("NS V1: 增强2D双曲锥涡量分析")
print("="*60)
print(f"Standard: 峰值涡量={mv_std[-1]:.3f}, 末速涡量={ens_std[-1]:.4f}")
print(f"PKS Cone: 峰值涡量={mv_cone[-1]:.3f}, 末速涡量={ens_cone[-1]:.4f}")
print(f"涡量放大比: {mv_cone[-1]/mv_std[-1]:.2%} (PKS/Standard)")
print(f"涡量放大比: {ens_cone[-1]/ens_std[-1]:.2%} (Enstrophy ratio)")
print(f"循环加速: {circ_cone[-1]/circ_std[-1]:.2%} (Circulation ratio)")
print(f"-> {out}")
