#!/usr/bin/env python3
"""
逆M水滴 LBM v9d — 大摆幅×20 + 长时×5
v9c→v9d：摆幅0.018→0.36(20×), 40000步(5×), 450×300网格
→ 大幅度上下扫掠入流，长尾流充分发育
"""
import numpy as np, os, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 输出目录适配：优先当前目��, 其次Windows本地路径
OUT_DIR = 'cfd_out'
os.makedirs(OUT_DIR, exist_ok=True)

# CSV路径: GPU服务器上在当前目录, Windows上在本地
CSV_PATH = 'droplet_invM_analytic.csv'
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.join(
        r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M水滴CFD流体实验',
        'droplet_invM_analytic.csv')
CSV = np.loadtxt(CSV_PATH, delimiter=',', skiprows=1)

# ═══════ D2Q9 LBM 常量 ═══════
w   = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])
cx  = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1], np.int32)
cy  = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1], np.int32)
opp = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], np.int32)

# ═══════ 摆放入流参数 ═══════
# 核心改动: 入流在垂直方向正弦摆动
SWAY_AMPLITUDE = 0.12      # 垂直速度幅值 (7×原版=BGK稳定上限, Ma~0.23)
SWAY_PERIOD    = 300       # 摆动周期(步) — 约133个周期覆盖40000步
SWAY_PHASE     = 0.0       # 初始相位

def load_mask(NX, NY, scale, cx0, cy0):
    px = (CSV[:,0]*scale + cx0).astype(np.float64)
    py = (CSV[:,1]*scale + cy0).astype(np.float64)
    xx, yy = np.meshgrid(np.arange(NX+2), np.arange(NY+2), indexing='ij')
    return Path(np.column_stack((px, py))).contains_points(
        np.column_stack((xx.ravel(), yy.ravel()))).reshape(NX+2, NY+2)

# ═══════ 仿真参数 ═══════
NX, NY = 420, 240
u0 = 0.06; tau = 0.65; omega = 1.0/tau
scale = 125.0 / 5.333
cx0 = int(NX * 0.22); cy0 = NY // 2
D_est = 125
Re_est = 3 * u0 * D_est / (tau - 0.5)
STEPS = 40000; SAVE_EVERY = 100
FPS_SLOW = 24  # 标准帧率

print(f'{"="*50}')
print(f'  Inverse-M Droplet LBM v9d')
print(f'  N={NX}x{NY}  u0={u0}  tau={tau}  Re~{Re_est:.0f}')
print(f'  sway={SWAY_AMPLITUDE}(x20)  T={SWAY_PERIOD}')
print(f'  steps={STEPS}(x5)  frames={STEPS//SAVE_EVERY}  fps={FPS_SLOW}')
print(f'{"="*50}')

# ═══════ 初始化 ═══════
mask = load_mask(NX, NY, scale, cx0, cy0)
mask1 = mask[1:-1, 1:-1]

f = np.zeros((NX+2, NY+2, 9))
for k in range(9): f[:,:,k] = w[k]
rho = np.ones((NX+2, NY+2))
ux = np.zeros((NX+2, NY+2))
uy = np.zeros((NX+2, NY+2))
frames = []

# ═══════ 主仿真循环 ═══════
for t in range(STEPS):
    # — 碰撞 —
    rho = np.sum(f, 2)
    de = rho + 1e-10
    ux = (f[:,:,1] + f[:,:,5] + f[:,:,8] - f[:,:,3] - f[:,:,6] - f[:,:,7]) / de
    uy = (f[:,:,2] + f[:,:,5] + f[:,:,6] - f[:,:,4] - f[:,:,7] - f[:,:,8]) / de
    ux[mask] = 0; uy[mask] = 0

    ux2 = ux**2; uy2 = uy**2; u2 = ux2 + uy2
    for k in range(9):
        cu = 3 * (cx[k]*ux + cy[k]*uy)
        f[:,:,k] -= omega * (f[:,:,k] - w[k]*rho * (1 + cu + 0.5*cu*cu - 1.5*u2))

    # — 流(streaming) —
    fb = np.zeros_like(f)
    for k in range(9):
        fb[:,:,k] = np.roll(np.roll(f[:,:,k], -cx[k], 0), -cy[k], 1)
    for k in range(9):
        f[:,:,k] = np.roll(np.roll(f[:,:,k], cx[k], 0), cy[k], 1)
    # 反弹边界
    for k in range(9):
        f[mask, k] = fb[mask, opp[k]]

    # ═══════ ★ 摆动入流边界 (核心改动) ★ ═══════
    jy = np.arange(2, NY)
    # 垂直摆动速度: 正弦波, 空间上中心最大、边界衰减
    sway_phase = 2.0 * math.pi * t / SWAY_PERIOD + SWAY_PHASE
    uy_sway = SWAY_AMPLITUDE * np.sin(sway_phase)

    # Zou-He 入流边界 (左边界 x=1), 含横向速度uy_sway
    # 已知: u_in = (u0, uy_sway)
    # 未知: rho_in, f1, f5, f8 (三个进入域内的分布函数)
    # 公式:
    #   rho_in = (f0 + f2 + f4 + 2*(f3+f6+f7)) / (1 - u0)
    #   f1 = f3 + (2/3)*rho_in*u0
    #   f5 = f7 - 0.5*(f2-f4) + 0.5*rho_in*uy_sway + (1/6)*rho_in*u0
    #   f8 = f6 + 0.5*(f2-f4) + 0.5*rho_in*uy_sway + (1/6)*rho_in*u0

    f0_in = f[1, jy, 0]; f2_in = f[1, jy, 2]; f3_in = f[1, jy, 3]
    f4_in = f[1, jy, 4]; f6_in = f[1, jy, 6]; f7_in = f[1, jy, 7]

    rho_in = (f0_in + f2_in + f4_in + 2.0*(f3_in + f6_in + f7_in)) / (1.0 - u0)

    f[1, jy, 1] = f3_in + (2.0/3.0) * rho_in * u0
    f[1, jy, 5] = f7_in - 0.5*(f2_in - f4_in) + 0.5*rho_in*uy_sway + (1.0/6.0)*rho_in*u0
    f[1, jy, 8] = f6_in + 0.5*(f2_in - f4_in) + 0.5*rho_in*uy_sway + (1.0/6.0)*rho_in*u0

    # 出口 (右边界 x=NX): 自由出流
    f[NX, jy, :] = f[NX-1, jy, :]

    # — 保帧 —
    if t % SAVE_EVERY == 0 or t == STEPS-1:
        vort = (np.roll(uy, -1, 0) - np.roll(uy, 1, 0)
              - np.roll(ux, -1, 1) + np.roll(ux, 1, 1)) * 0.5
        vort[mask] = 0
        frames.append(vort[1:-1, 1:-1].copy())
        if t % 500 == 0:
            vel = np.sqrt(ux**2 + uy**2); vel[mask] = 0
            print(f'  t={t:>4d}  frames={len(frames)}  '
                  f'max|v|={vel.max():.4f}  uy_sway={uy_sway:+.4f}')

# ═══════ 渲染 — 涡量版 ═══════
print(f'\nRendering {len(frames)} frames — vorticity…')
fig, ax = plt.subplots(figsize=(10, 5))
vmax = abs(frames[-1]).max() * 0.3

def anim_vort(i):
    ax.clear()
    bg = np.zeros((NY, NX, 4)); bg[mask1.T, :] = [0.15, 0.18, 0.22, 1.0]
    ax.imshow(bg, extent=[0, NX, 0, NY], origin='lower')
    ax.imshow(frames[i].T, cmap='RdBu_r', origin='lower',
              extent=[0, NX, 0, NY], vmin=-vmax, vmax=vmax, alpha=0.88)
    ax.contour(mask1.T, levels=[0.5], colors='white', linewidths=1.2,
               extent=[0, NX, 0, NY])
    # 摆动箭头: 方向随出入流摆动
    t_phys = i * SAVE_EVERY
    sway_deg = math.degrees(math.atan2(
        SWAY_AMPLITUDE * math.sin(2*math.pi*t_phys/SWAY_PERIOD), u0))
    ax.arrow(8, NY*0.5, 18*math.cos(math.radians(sway_deg)),
             18*math.sin(math.radians(sway_deg)),
             head_width=4, head_length=6, fc='cyan', ec='cyan', lw=2, zorder=10)
    ax.set_title(f'Inverse-M Droplet v9d Re~{Re_est:.0f} t={t_phys} '
                 f'[sway x20 3fps]',
                 fontsize=12, fontweight='bold')
    ax.set_xlim(0, NX); ax.set_ylim(0, NY)

ani = animation.FuncAnimation(fig, anim_vort, frames=len(frames), interval=80)
gif_vort = os.path.join(OUT_DIR, 'droplet_MRT_v9d_sway_vorticity.gif')
ani.save(gif_vort, writer='pillow', fps=FPS_SLOW, dpi=80); plt.close(fig)
print(f'✅ {gif_vort} ({os.path.getsize(gif_vort)//1024}KB)')

# ═══════ 渲染 — 涡街版 (coolwarm) ═══════
print(f'Rendering {len(frames)} frames — vortex…')
fig2, ax2 = plt.subplots(figsize=(10, 5))
vmax2 = abs(frames[-1]).max() * 0.2

def anim_vortex(i):
    ax2.clear()
    bg = np.zeros((NY, NX, 4)); bg[mask1.T, :] = [0.12, 0.15, 0.20, 1.0]
    ax2.imshow(bg, extent=[0, NX, 0, NY], origin='lower')
    ax2.imshow(frames[i].T, cmap='coolwarm', origin='lower',
               extent=[0, NX, 0, NY], vmin=-vmax2, vmax=vmax2, alpha=0.90)
    ax2.contour(mask1.T, levels=[0.5], colors='#ffcc44', linewidths=1,
                extent=[0, NX, 0, NY])
    sway_deg2 = math.degrees(math.atan2(
        SWAY_AMPLITUDE * math.sin(2*math.pi*i*SAVE_EVERY/SWAY_PERIOD), u0))
    ax2.arrow(8, NY*0.5, 18*math.cos(math.radians(sway_deg2)),
              18*math.sin(math.radians(sway_deg2)),
              head_width=4, head_length=6, fc='#ff44aa', ec='#ff44aa', lw=2, zorder=10)
    ax2.set_title(f'Inverse-M Droplet Vortex v9d Re~{Re_est:.0f} f={i} '
                  f'[sway x20 3fps]', fontsize=12)
    ax2.set_xlim(0, NX); ax2.set_ylim(0, NY)

ani2 = animation.FuncAnimation(fig2, anim_vortex, frames=len(frames), interval=80)
gif_vortex = os.path.join(OUT_DIR, 'droplet_MRT_v9d_sway_vortex.gif')
ani2.save(gif_vortex, writer='pillow', fps=FPS_SLOW, dpi=80); plt.close(fig2)
print(f'✅ {gif_vortex} ({os.path.getsize(gif_vortex)//1024}KB)')
print('\nDone! v9c completed')
