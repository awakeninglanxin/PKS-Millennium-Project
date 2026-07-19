#!/usr/bin/env python3
"""逆M水滴绕流涡街动画 — 实心障碍 + 中文字体 | SOUL铁律"""
import numpy as np, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path

# ═══ SOUL铁律 #1: CJK字体必须在所有matplotlib导入后立即设置 ═══
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

this_dir = os.path.dirname(os.path.abspath(__file__))

def load_mask(csv, NX, NY, scale, cx0, cy0):
    px = (csv[:,0]*scale + cx0).astype(np.float64)
    py = (csv[:,1]*scale + cy0).astype(np.float64)
    xx, yy = np.meshgrid(np.arange(NX+2), np.arange(NY+2), indexing='ij')
    return Path(np.column_stack((px, py))).contains_points(
        np.column_stack((xx.ravel(), yy.ravel()))).reshape(NX+2, NY+2)

# 网格: 宽域留涡街空间
NX, NY = 500, 200
scale = 180.0 / 5.333
cx0 = int(NX * 0.22)
cy0 = NY // 2
csv = np.loadtxt(os.path.join(this_dir, 'droplet_invM_analytic.csv'), delimiter=',', skiprows=1)
mask = load_mask(csv, NX, NY, scale, cx0, cy0)
mask1 = mask[1:-1, 1:-1]
print(f'Grid: {NX}x{NY}, Obstacle: {mask.sum()} cells')

# D2Q9
Q = 9; w = np.array([4/9,1/9,1/9,1/9,1/9,1/36,1/36,1/36,1/36])
cx = np.array([0,1,0,-1,0,1,-1,-1,1], np.int32)
cy = np.array([0,0,1,0,-1,1,1,-1,-1], np.int32)
opp = np.array([0,3,4,1,2,7,8,5,6], np.int32)

u0 = 0.07; tau = 0.58; omega = 1.0/tau
steps = 10000; save_every = 50
D_eff = 150; Re = u0 * D_eff * (tau-0.5) / 3.0
print(f'u0={u0} tau={tau} Re≈{Re:.0f} steps={steps} frames={steps//save_every}')

for direction, tag, ttl in [
    ('left', 'BaseToTip_v2', '逆M水滴绕流 — 钝面迎流 (Re≈%.0f)'),
    ('right', 'TipToBase_v2', '逆M水滴绕流 — 尖端迎流 (Re≈%.0f)')]:

    out_dir = os.path.join(this_dir, f'cfd_Greedy_{tag}')
    os.makedirs(out_dir, exist_ok=True)
    print(f'\n{ttl % Re}:')

    f = np.zeros((NX+2, NY+2, Q))
    for k in range(Q): f[:,:,k] = w[k]
    rho = np.ones((NX+2, NY+2)); ux_f = np.zeros((NX+2, NY+2)); uy_f = np.zeros((NX+2, NY+2))
    frames = []

    for t in range(steps):
        rho = np.sum(f, 2); de = rho + 1e-10
        ux_f = (f[:,:,1]+f[:,:,5]+f[:,:,8]-f[:,:,3]-f[:,:,6]-f[:,:,7])/de
        uy_f = (f[:,:,2]+f[:,:,5]+f[:,:,6]-f[:,:,4]-f[:,:,7]-f[:,:,8])/de
        ux_f[mask] = 0; uy_f[mask] = 0

        for k in range(Q):
            cu = 3*(cx[k]*ux_f+cy[k]*uy_f)
            f[:,:,k] -= omega*(f[:,:,k] - w[k]*rho*(1+cu+0.5*cu*cu-1.5*(ux_f**2+uy_f**2)))

        fb = np.zeros_like(f)
        for k in range(Q): fb[:,:,k] = np.roll(np.roll(f[:,:,k], -cx[k], 0), -cy[k], 1)
        for k in range(Q): f[:,:,k] = np.roll(np.roll(f[:,:,k], cx[k], 0), cy[k], 1)
        for k in range(Q): f[mask,k] = fb[mask, opp[k]]

        jy = np.arange(2, NY)
        if direction == 'left':
            rho[1,jy] = (f[1,jy,0]+f[1,jy,2]+f[1,jy,4]+2*(f[1,jy,3]+f[1,jy,6]+f[1,jy,7]))/(1-u0)
            f[1,jy,1] = f[1,jy,3] + 2*w[1]*rho[1,jy]*u0
            f[1,jy,5] = f[1,jy,7] - 0.5*(f[1,jy,2]-f[1,jy,4]) + 0.5*(f[1,jy,1]+f[1,jy,3])
            f[1,jy,8] = f[1,jy,6] + 0.5*(f[1,jy,2]-f[1,jy,4]) + 0.5*(f[1,jy,1]+f[1,jy,3])
            f[NX,jy,:] = f[NX-1,jy,:]
        else:
            rho[NX,jy] = (f[NX,jy,0]+f[NX,jy,2]+f[NX,jy,4]+2*(f[NX,jy,1]+f[NX,jy,5]+f[NX,jy,8]))/(1+u0)
            f[NX,jy,3] = f[NX,jy,1] + 2*w[3]*rho[NX,jy]*u0
            f[NX,jy,6] = f[NX,jy,8] - 0.5*(f[NX,jy,4]-f[NX,jy,2]) + 0.5*(f[NX,jy,3]+f[NX,jy,1])
            f[NX,jy,7] = f[NX,jy,5] + 0.5*(f[NX,jy,4]-f[NX,jy,2]) + 0.5*(f[NX,jy,3]+f[NX,jy,1])
            f[1,jy,:] = f[2,jy,:]

        if t % save_every == 0 or t == steps-1:
            vort = (np.roll(uy_f,-1,0)-np.roll(uy_f,1,0)-np.roll(ux_f,-1,1)+np.roll(ux_f,1,1))*0.5
            vort[mask] = 0
            frames.append(vort[1:-1,1:-1].copy())
            if t % 2000 == 0:
                vel = np.sqrt(ux_f**2+uy_f**2); vel[mask]=0
                print(f"  t={t:>5d}  frames={len(frames)}  max|v|={vel.max():.4f}")

    # ═══ 生成 GIF 动画 ═══
    print(f"  渲染 {len(frames)} 帧 → GIF...")
    fig, ax = plt.subplots(figsize=(12, 6))
    vmax = abs(frames[-1]).max() * 0.3

    def animate(i):
        ax.clear()
        # 实心障碍 — 深色填充
        bg = np.zeros((NY, NX, 4))
        bg[mask1.T, :] = [0.15, 0.18, 0.22, 1.0]  # 深灰蓝
        ax.imshow(bg, extent=[0, NX, 0, NY], origin='lower')
        # 涡量叠加
        ax.imshow(frames[i].T, cmap='RdBu_r', origin='lower', extent=[0, NX, 0, NY],
                  vmin=-vmax, vmax=vmax, alpha=0.85)
        # 白色轮廓线
        ax.contour(mask1.T, levels=[0.5], colors='white', linewidths=1.8, extent=[0, NX, 0, NY])
        # 来流箭头
        arr_x = 15 if direction == 'left' else NX-15
        arr_dx = 30 if direction == 'left' else -30
        ax.arrow(arr_x, NY*0.5, arr_dx, 0, head_width=8, head_length=12,
                 fc='cyan', ec='cyan', lw=3, zorder=10)
        ax.set_title(f'{ttl % Re}  t={i*save_every}', fontsize=13, fontweight='bold')
        ax.set_xlim(0, NX); ax.set_ylim(0, NY)
        ax.set_xlabel('X (来流方向 →)'); ax.set_ylabel('Y')

    anim = animation.FuncAnimation(fig, animate, frames=len(frames), interval=100)
    gif_path = os.path.join(out_dir, f'droplet_{tag}_vorticity.gif')
    anim.save(gif_path, writer='pillow', fps=10, dpi=90)
    plt.close(fig)
    sz = os.path.getsize(gif_path)
    print(f'   ✅ {gif_path}  ({sz//1024}KB)')

print('\n🎬 Done!')
