#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NS V8: 3D Sobolev 退化诊断 + PKS-EVMP 严格化
══════════════════════════════════════════════════════
从 V7 的 2D 升级到 3D 伪谱方法，验证：
1. 3D 下 H^s Sobolev 范数是否出现更快速的衰减
2. PKS 双曲锥几何 xy=1 在 3D 下的 EVMP ratio
3. 窦华书机制 (Type II Sobolev degeneration) 是否在 3D 激活

关键差异 vs V7 2D:
- 涡量-向量形式 (ω = ∇×u) 而非标量涡量
- 3D 漩涡拉伸项 (ω·∇)u → 能量级联加速
- PKS 锥: 双曲旋转体 z = 1/(x²+y²)^(1/2)

2026-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys
from math import sqrt, pi, log

od = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════
# 1. 3D 谱方法设置
# ═══════════════════════════════════════════════════════════════════

N = 32  # 每维分辨率 (32³ = 32768 点)
L = 2 * pi  # 域大小
dx = L / N

# 波数
k = np.fft.fftfreq(N, d=1/N) * 2 * pi / L
kx, ky, kz = np.meshgrid(k, k, k, indexing='ij')
k2 = kx**2 + ky**2 + kz**2
k2[0,0,0] = 1.0  # 避免除零

# 物理空间
x = np.linspace(0, L, N, endpoint=False)
X, Y, Z = np.meshgrid(x, x, x, indexing='ij')

# ═══════════════════════════════════════════════════════════════════
# 2. PKS 双曲锥 (3D)
# ═══════════════════════════════════════════════════════════════════

def pks_cone_field():
    """PKS 双曲锥 xy=1 在 3D 下的旋转体: r_cone"""

    # 以原点为中心, z=0 平面上的径向距离
    R = np.sqrt(X**2 + Y**2)

    # 双曲锥: z = ±1/R  (xy=1 的旋转体等价形式)
    # 公式: 若 xy=1, 则距离旋转轴的距离 = 1/z
    # 转换为: r² = x²+y² = A²/z², 即内部区域满足 r·z ≤ A
    # 我们使用更简单的形式: r² + z² ≥ r_min, 截出锥形空间

    cone_radius = 1.0 / (np.abs(Z) + 0.01)  # 锥的局部半径
    mask = (R < cone_radius) & (R < L/3)  # PKS 锥内部
    return mask.astype(float)

def pks_radial_vector():
    """PKS 锥径向单位矢量 (从旋转轴向外)"""
    R = np.sqrt(X**2 + Y**2) + 1e-8
    rx = X / R
    ry = Y / R
    rz = np.zeros_like(rx)
    return rx, ry, rz

# ═══════════════════════════════════════════════════════════════════
# 3. 3D 伪谱 NS 求解器
# ═══════════════════════════════════════════════════════════════════

def solve_3d_ns(nu, dt, n_steps, use_pks_cone=True, cone_strength=0.5, save_every=10):
    """
    3D 不可压 NS: ∂u/∂t + (u·∇)u = -∇p + ν∇²u
    涡量形式: ∂ω/∂t + (u·∇)ω = (ω·∇)u + ν∇²ω

    伪谱方法: 傅里叶变换 + 2/3 去假频
    """

    # 初始条件: Taylor-Green 涡旋
    ux = np.sin(X) * np.cos(Y) * np.cos(Z)
    uy = -np.cos(X) * np.sin(Y) * np.cos(Z)
    uz = np.zeros_like(ux)

    # 转换到谱空间
    ux_hat = np.fft.fftn(ux)
    uy_hat = np.fft.fftn(uy)
    uz_hat = np.fft.fftn(uz)

    # PKS 锥
    pks_mask = pks_cone_field()
    pks_rx, pks_ry, pks_rz = pks_radial_vector()

    # 追踪量
    history = {
        't': [], 'energy': [], 'enstrophy': [],
        'h1_norm': [], 'h2_norm': [], 'h3_norm': [], 'h4_norm': [],
        'max_vorticity': [], 'evmp_ratio': []
    }

    for step in range(n_steps):
        # 去假频 (2/3 规则)
        kmax = N // 3

        # 非线性项: (u·∇)u → 在物理空间计算
        ux = np.fft.ifftn(ux_hat).real
        uy = np.fft.ifftn(uy_hat).real
        uz = np.fft.ifftn(uz_hat).real

        # 计算涡量 ω = ∇×u
        wx_hat = 1j * (ky * uz_hat - kz * uy_hat)
        wy_hat = 1j * (kz * ux_hat - kx * uz_hat)
        wz_hat = 1j * (kx * uy_hat - ky * ux_hat)

        # 非线性对流: (u·∇)u
        dux_dx = np.fft.ifftn(1j * kx * ux_hat).real
        dux_dy = np.fft.ifftn(1j * ky * ux_hat).real
        dux_dz = np.fft.ifftn(1j * kz * ux_hat).real
        duy_dx = np.fft.ifftn(1j * kx * uy_hat).real
        duy_dy = np.fft.ifftn(1j * ky * uy_hat).real
        duy_dz = np.fft.ifftn(1j * kz * uy_hat).real
        duz_dx = np.fft.ifftn(1j * kx * uz_hat).real
        duz_dy = np.fft.ifftn(1j * ky * uz_hat).real
        duz_dz = np.fft.ifftn(1j * kz * uz_hat).real

        NL_x = ux * dux_dx + uy * dux_dy + uz * dux_dz
        NL_y = ux * duy_dx + uy * duy_dy + uz * duy_dz
        NL_z = ux * duz_dx + uy * duz_dy + uz * duz_dz

        NL_x_hat = np.fft.fftn(NL_x)
        NL_y_hat = np.fft.fftn(NL_y)
        NL_z_hat = np.fft.fftn(NL_z)

        # 截断高频
        mask_k = (np.abs(kx) < kmax) & (np.abs(ky) < kmax) & (np.abs(kz) < kmax)
        NL_x_hat[~mask_k] = 0
        NL_y_hat[~mask_k] = 0
        NL_z_hat[~mask_k] = 0

        # 投影到无散 (消去压力梯度)
        div_NL = kx * NL_x_hat + ky * NL_y_hat + kz * NL_z_hat
        k2_proj = k2.copy()
        k2_proj[0,0,0] = 1.0

        NL_x_hat -= kx * div_NL / k2_proj
        NL_y_hat -= ky * div_NL / k2_proj
        NL_z_hat -= kz * div_NL / k2_proj

        # 时间推进: 半隐式 (粘性项显式, 对流项 Euler)
        decay = np.exp(-nu * k2 * dt)

        ux_hat = (ux_hat - dt * NL_x_hat) * decay
        uy_hat = (uy_hat - dt * NL_y_hat) * decay
        uz_hat = (uz_hat - dt * NL_z_hat) * decay

        # PKS 锥约束: 在锥内部施加额外的几何约束力
        if use_pks_cone:
            ux = np.fft.ifftn(ux_hat).real
            uy = np.fft.ifftn(uy_hat).real
            uz = np.fft.ifftn(uz_hat).real

            # 锥约束: 在锥内部施加朝向锥面的力
            R = np.sqrt(X**2 + Y**2) + 1e-8
            cone_r = 1.0 / (np.abs(Z) + 0.01)
            inside_cone = (R < cone_r * 0.9) & (R < L/4)

            # PKS 锥约束力 = 混合项 (ab=1 极性)
            u_mag = np.sqrt(ux**2 + uy**2 + uz**2)
            cone_force = cone_strength * (cone_r - R) / (cone_r + 1e-8) * inside_cone

            dux_cone = cone_force * pks_rx * u_mag
            duy_cone = cone_force * pks_ry * u_mag
            duz_cone = -cone_force * np.sign(Z) * u_mag

            ux += dt * dux_cone
            uy += dt * duy_cone
            uz += dt * duz_cone

            ux_hat = np.fft.fftn(ux)
            uy_hat = np.fft.fftn(uy)
            uz_hat = np.fft.fftn(uz)

        # 追踪
        if step % save_every == 0:
            ux = np.fft.ifftn(ux_hat).real
            uy = np.fft.ifftn(uy_hat).real
            uz = np.fft.ifftn(uz_hat).real

            t = step * dt
            energy = 0.5 * np.mean(ux**2 + uy**2 + uz**2)

            # 涡量
            wx = np.fft.ifftn(wx_hat).real
            wy = np.fft.ifftn(wy_hat).real
            wz = np.fft.ifftn(wz_hat).real
            enstrophy = 0.5 * np.mean(wx**2 + wy**2 + wz**2)
            max_w = np.max(np.sqrt(wx**2 + wy**2 + wz**2))

            # Sobolev 范数: ||u||_H^s = [Σ (1+|k|²)^s |û|²]^(1/2)
            u_mag_sq = np.abs(ux_hat)**2 + np.abs(uy_hat)**2 + np.abs(uz_hat)**2
            h1 = np.sqrt(np.sum((1 + k2) * u_mag_sq)) / N**3
            h2 = np.sqrt(np.sum((1 + k2)**2 * u_mag_sq)) / N**3
            h3 = np.sqrt(np.sum((1 + k2)**3 * u_mag_sq)) / N**3
            h4 = np.sqrt(np.sum((1 + k2)**4 * u_mag_sq)) / N**3

            # EVMP 严格化: (∇E · r̂) / |u|²
            # ∇E = (∂E/∂x, ∂E/∂y, ∂E/∂z)
            E = 0.5 * (ux**2 + uy**2 + uz**2)
            dE_dx = np.fft.ifftn(1j * kx * np.fft.fftn(E)).real
            dE_dy = np.fft.ifftn(1j * ky * np.fft.fftn(E)).real
            dE_dz = np.fft.ifftn(1j * kz * np.fft.fftn(E)).real

            gradE_dot_r = dE_dx * pks_rx + dE_dy * pks_ry + dE_dz * pks_rz
            u_sq = ux**2 + uy**2 + uz**2 + 1e-8
            evmp = np.mean(np.abs(gradE_dot_r) / u_sq)

            history['t'].append(t)
            history['energy'].append(energy)
            history['enstrophy'].append(enstrophy)
            history['h1_norm'].append(h1)
            history['h2_norm'].append(h2)
            history['h3_norm'].append(h3)
            history['h4_norm'].append(h4)
            history['max_vorticity'].append(max_w)
            history['evmp_ratio'].append(evmp)

            if step % (save_every * 20) == 0:
                print(f"  t={t:.3f}: E={energy:.4f}, H³={h3:.3f}, max|ω|={max_w:.3f}, EVMP={evmp:.3f}")

    for key in history:
        if key != 't':
            history[key] = np.array(history[key])
    return history

# ═══════════════════════════════════════════════════════════════════
# 4. 主实验: Standard vs PKS 对照
# ═══════════════════════════════════════════════════════════════════

print("=" * 65)
print("NS V8: 3D Sobolev 退化诊断 + PKS-EVMP 严格化")
print(f"  分辨率: {N}³ = {N**3} 点")
print("=" * 65)

nu = 0.005
dt = 0.01
n_steps = 300

print(f"\n[Run 1] Standard 3D NS (无 PKS 锥)...")
hist_std = solve_3d_ns(nu, dt, n_steps, use_pks_cone=False, save_every=10)

print(f"\n[Run 2] PKS 3D NS (cone_strength=0.5)...")
hist_pks = solve_3d_ns(nu, dt, n_steps, use_pks_cone=True, cone_strength=0.5, save_every=10)

# ═══════════════════════════════════════════════════════════════════
# 5. 分析
# ═══════════════════════════════════════════════════════════════════

print(f"\n{'='*65}")
print(f"诊断结果对比")
print(f"{'='*65}")

# H³ 衰减率
h3_decay_std = hist_std['h3_norm'][-1] / (hist_std['h3_norm'][0] + 1e-12)
h3_decay_pks = hist_pks['h3_norm'][-1] / (hist_pks['h3_norm'][0] + 1e-12)
print(f"  H³ decay (Standard): {h3_decay_std:.3f} ({h3_decay_std*100:.1f}%)")
print(f"  H³ decay (PKS):      {h3_decay_pks:.3f} ({h3_decay_pks*100:.1f}%)")

# EVMP ratio
evmp_std_mean = np.mean(hist_std['evmp_ratio'])
evmp_pks_mean = np.mean(hist_pks['evmp_ratio'])
evmp_ratio_3d = evmp_pks_mean / (evmp_std_mean + 1e-12)
print(f"  EVMP mean (Standard): {evmp_std_mean:.4f}")
print(f"  EVMP mean (PKS):      {evmp_pks_mean:.4f}")
print(f"  EVMP PKS/Std ratio:   {evmp_ratio_3d:.3f}")

# Energy
print(f"\n  Energy final (Std):   {hist_std['energy'][-1]:.4f}")
print(f"  Energy final (PKS):   {hist_pks['energy'][-1]:.4f}")

# Max vorticity
print(f"  max|ω| final (Std):   {hist_std['max_vorticity'][-1]:.4f}")
print(f"  max|ω| final (PKS):   {hist_pks['max_vorticity'][-1]:.4f}")

# ═══════════════════════════════════════════════════════════════════
# 6. 可视化
# ═══════════════════════════════════════════════════════════════════

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# Panel 1: Energy
ax = axes[0,0]
ax.plot(hist_std['t'], hist_std['energy'], 'b-', lw=1.5, label='Standard 3D')
ax.plot(hist_pks['t'], hist_pks['energy'], 'r-', lw=1.5, label='PKS 3D')
ax.set_xlabel('t'); ax.set_ylabel('Kinetic Energy')
ax.set_title('能量衰减对比')
ax.legend(); ax.grid(alpha=0.3)

# Panel 2: H³ norm
ax2 = axes[0,1]
ax2.plot(hist_std['t'], hist_std['h3_norm'], 'b-', lw=1.5, label=f'Std (decay {h3_decay_std*100:.1f}%)')
ax2.plot(hist_pks['t'], hist_pks['h3_norm'], 'r-', lw=1.5, label=f'PKS (decay {h3_decay_pks*100:.1f}%)')
ax2.set_xlabel('t'); ax2.set_ylabel('||u||_{H³}')
ax2.set_title('Sobolev H³ 范数衰减 (3D)')
ax2.legend(); ax2.grid(alpha=0.3)

# Panel 3: EVMP ratio
ax3 = axes[0,2]
ax3.plot(hist_std['t'], hist_std['evmp_ratio'], 'b-', lw=1, alpha=0.7, label=f'Std (mean={evmp_std_mean:.3f})')
ax3.plot(hist_pks['t'], hist_pks['evmp_ratio'], 'r-', lw=1, alpha=0.7, label=f'PKS (mean={evmp_pks_mean:.3f})')
ax3.set_xlabel('t'); ax3.set_ylabel('|∇E·r̂| / |u|²')
ax3.set_title(f'EVMP 严格化 (PKS/Std ratio = {evmp_ratio_3d:.3f})')
ax3.legend(); ax3.grid(alpha=0.3)

# Panel 4: Max vorticity
ax4 = axes[1,0]
ax4.plot(hist_std['t'], hist_std['max_vorticity'], 'b-', lw=1.5, label='Standard')
ax4.plot(hist_pks['t'], hist_pks['max_vorticity'], 'r-', lw=1.5, label='PKS')
ax4.set_xlabel('t'); ax4.set_ylabel('max |ω|')
ax4.set_title('最大涡量')
ax4.legend(); ax4.grid(alpha=0.3)

# Panel 5: Enstrophy
ax5 = axes[1,1]
ax5.plot(hist_std['t'], hist_std['enstrophy'], 'b-', lw=1.5, label='Standard')
ax5.plot(hist_pks['t'], hist_pks['enstrophy'], 'r-', lw=1.5, label='PKS')
ax5.set_xlabel('t'); ax5.set_ylabel('Enstrophy')
ax5.set_title('拟涡能')
ax5.legend(); ax5.grid(alpha=0.3)

# Panel 6: Summary
ax6 = axes[1,2]
ax6.axis('off')
lines = [
    "NS V8: 3D Sobolev 退化总结",
    f"",
    f"分辨率: {N}³ = {N**3} 点, ν={nu}, dt={dt}",
    f"H³ 衰减: Std={h3_decay_std*100:.1f}%, PKS={h3_decay_pks*100:.1f}%",
    f"EVMP PKS/Std = {evmp_ratio_3d:.3f}",
    f"",
    f"V7 (2D) EVMP ratio = 0.56",
    f"V8 (3D) EVMP ratio = {evmp_ratio_3d:.3f}",
    f"",
    f"判决:",
]
if evmp_ratio_3d < 0.8:
    lines.append("✅ PKS 几何在 3D 下同样稳定 EVMP")
    lines.append("✅ 窦华书机制在 PKS 锥约束下可控")
elif evmp_ratio_3d < 1.2:
    lines.append("⚠️ PKS 在 3D 下效果与标准相当")
    lines.append("⚠️ 需更高分辨率验证")
else:
    lines.append("🔴 PKS 在 3D 下 EVMP 反而更大")
    lines.append("🔴 锥约束参数需要调整")

for i, line in enumerate(lines):
    y = 0.92 - i * 0.055
    if line.startswith("NS V8:") or line.startswith("判决:"):
        ax6.text(0.05, y, line, fontsize=11, fontweight='bold', color='#2c3e50')
    elif line.startswith("✅"):
        ax6.text(0.05, y, line, fontsize=10, color='#27ae60', fontweight='bold')
    else:
        ax6.text(0.05, y, line, fontsize=9, color='#555555')

plt.suptitle('NS V8: 3D Sobolev 退化诊断 — PKS 双曲锥 + EVMP 严格化', fontsize=13, fontweight='bold')
plt.tight_layout()
out_path = os.path.join(od, 'NS_V8_3D_Sobolev.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n✅ 输出: {out_path}")
