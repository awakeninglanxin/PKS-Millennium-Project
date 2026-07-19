#!/usr/bin/env python3
"""逆M水滴 LBM CFD 动画 — 已验证稳定的 mask + 保守参数"""
import numpy as np, os, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path

this_dir = os.path.dirname(os.path.abspath(__file__))

# ═══ 加载水滴 mask (同 cfd_lbm_greedy.py, 已验证) ═══
def load_droplet_mask(csv_path, NX, NY, scale, cx0, cy0):
    pts = np.loadtxt(csv_path, delimiter=',', skiprows=1)
    px = (pts[:, 0] * scale + cx0).astype(np.float64)
    py = (pts[:, 1] * scale + cy0).astype(np.float64)
    xx, yy = np.meshgrid(np.arange(NX+2), np.arange(NY+2), indexing='ij')
    path = Path(np.column_stack((px, py)))
    inside = path.contains_points(np.column_stack((xx.ravel(), yy.ravel())))
    return inside.reshape((NX+2, NY+2))

csv_path = os.path.join(this_dir, 'droplet_invM_analytic.csv')
NX, NY = 350, 180
scale = 150.0 / 5.333
cx0 = int(NX * 0.4)
cy0 = NY // 2
mask = load_droplet_mask(csv_path, NX, NY, scale, cx0, cy0)
mask1 = mask[1:-1, 1:-1]
print(f'Mask: {mask.sum()} obstacle cells')

# ═══ LBM D2Q9 ═══
Q = 9
w = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36], dtype=np.float64)
cx = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1], dtype=np.int32)
cy = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1], dtype=np.int32)
opp = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], dtype=np.int32)

# 保守参数确保数值稳定
u0 = 0.03; tau = 0.62; omega = 1.0 / tau
steps = 5000; save_every = 25; n_frames = steps // save_every + 1
Re = u0 * (NX // 4) * (tau - 0.5) / 3.0
print(f'LBM: {NX}x{NY}, Re~{Re:.0f}, {steps} steps → {n_frames} frames')

for direction, dir_name, flow_cn in [
    ('left', 'BaseToTip', u'钝面\u2192尖端'),
    ('right', 'TipToBase', u'尖端\u2192钝面')
]:
    out_dir = os.path.join(this_dir, f'cfd_Greedy_{dir_name}')
    os.makedirs(out_dir, exist_ok=True)
    print(f'\n{flow_cn} ...')

    # 初始化
    f = np.zeros((NX+2, NY+2, Q))
    for k in range(Q): f[:, :, k] = w[k]
    rho = np.ones((NX+2, NY+2)); ux_f = np.zeros((NX+2, NY+2)); uy_f = np.zeros((NX+2, NY+2))
    frames = []

    for t in range(steps):
        # 宏观量
        rho = np.sum(f, axis=2)
        denom = rho + 1e-10
        ux_f = (f[:,:,1] + f[:,:,5] + f[:,:,8] - f[:,:,3] - f[:,:,6] - f[:,:,7]) / denom
        uy_f = (f[:,:,2] + f[:,:,5] + f[:,:,6] - f[:,:,4] - f[:,:,7] - f[:,:,8]) / denom
        ux_f[mask] = 0; uy_f[mask] = 0

        # BGK 碰撞
        for k in range(Q):
            cu = 3 * (cx[k] * ux_f + cy[k] * uy_f)
            feq = w[k] * rho * (1 + cu + 0.5*cu*cu - 1.5*(ux_f**2 + uy_f**2))
            f[:,:,k] -= omega * (f[:,:,k] - feq)

        # 传播前快照
        f_bounce = np.zeros_like(f)
        for k in range(Q):
            f_bounce[:,:,k] = np.roll(np.roll(f[:,:,k], -cx[k], axis=0), -cy[k], axis=1)

        # 传播
        for k in range(Q):
            f[:,:,k] = np.roll(np.roll(f[:,:,k], cx[k], axis=0), cy[k], axis=1)

        # 障碍反弹
        for k in range(Q):
            f[mask, k] = f_bounce[mask, opp[k]]

        # Zou-He 速度入口
        jy = np.arange(2, NY)
        if direction == 'left':
            rho[1, jy] = (f[1,jy,0]+f[1,jy,2]+f[1,jy,4] + 2*(f[1,jy,3]+f[1,jy,6]+f[1,jy,7])) / (1 - u0)
            f[1,jy,1] = f[1,jy,3] + 2*w[1]*rho[1,jy]*u0
            f[1,jy,5] = f[1,jy,7] - 0.5*(f[1,jy,2]-f[1,jy,4]) + 0.5*(f[1,jy,1]+f[1,jy,3])
            f[1,jy,8] = f[1,jy,6] + 0.5*(f[1,jy,2]-f[1,jy,4]) + 0.5*(f[1,jy,1]+f[1,jy,3])
            f[NX, jy, :] = f[NX-1, jy, :]
        else:
            rho[NX, jy] = (f[NX,jy,0]+f[NX,jy,2]+f[NX,jy,4] + 2*(f[NX,jy,1]+f[NX,jy,5]+f[NX,jy,8])) / (1 + u0)
            f[NX,jy,3] = f[NX,jy,1] + 2*w[3]*rho[NX,jy]*u0
            f[NX,jy,6] = f[NX,jy,8] - 0.5*(f[NX,jy,4]-f[NX,jy,2]) + 0.5*(f[NX,jy,3]+f[NX,jy,1])
            f[NX,jy,7] = f[NX,jy,5] + 0.5*(f[NX,jy,4]-f[NX,jy,2]) + 0.5*(f[NX,jy,3]+f[NX,jy,1])
            f[1, jy, :] = f[2, jy, :]

        # 保存帧
        if t % save_every == 0 or t == steps - 1:
            vort = (np.roll(uy_f, -1, 0) - np.roll(uy_f, 1, 0)
                   - np.roll(ux_f, -1, 1) + np.roll(ux_f, 1, 1)) * 0.5
            vort[mask] = 0
            frames.append(vort[1:-1, 1:-1].copy())
            if t % 1000 == 0:
                vel = np.sqrt(ux_f**2 + uy_f**2); vel[mask] = 0
                print(f"  t={t:>5d}  frames={len(frames)}  max|v|={vel.max():.4f}  |vort|max={abs(vort[1:-1,1:-1]).max():.4f}")

    # ═══ 生成 GIF 动画 ═══
    print(f"  Rendering {len(frames)}-frame GIF ...")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    vmax = abs(frames[-1]).max() * 0.35

    def animate_fn(i):
        ax.clear()
        ax.imshow(frames[i].T, cmap='RdBu_r', origin='lower', extent=[0, NX, 0, NY],
                  vmin=-vmax, vmax=vmax)
        ax.contour(mask1.T, levels=[0.5], colors='black', linewidths=1.5, extent=[0, NX, 0, NY])
        ax.set_title(f'{flow_cn}  t={i*save_every}  (Re~{Re:.0f})', fontsize=12)
        ax.set_xlim(0, NX); ax.set_ylim(0, NY)

    anim = animation.FuncAnimation(fig, animate_fn, frames=len(frames), interval=80, blit=False)
    gif_path = os.path.join(out_dir, f'droplet_{dir_name}_vorticity.gif')
    anim.save(gif_path, writer='pillow', fps=12, dpi=100)
    plt.close(fig)

    # 保存帧数据
    np.savez_compressed(os.path.join(out_dir, 'cfd_frames.npz'),
                        frames=np.array(frames), mask=mask1)

    print(f"  GIF: {gif_path}  ({os.path.getsize(gif_path)//1024}KB)")

print('\n🎬 Animation complete!')
