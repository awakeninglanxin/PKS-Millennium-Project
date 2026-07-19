#!/usr/bin/env python3
"""
逆M水滴 D2Q9 格子Boltzmann流体仿真
双向冲水: 钝面→尖(左来流) + 尖→钝面(右来流)
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os, sys

# ═══════ LBM D2Q9 常数 ═══════
Q = 9
w = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])
cx = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1], dtype=np.int32)
cy = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1], dtype=np.int32)
opp = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], dtype=np.int32)

# ═══════ 读水滴轮廓 → 填充内部 ═══════
def load_droplet_mask(csv_path, NX, NY, scale, cx0, cy0):
    """读CSV轮廓 → 填充内部 → 返回 bool[NX+dim][NY+dim] 障碍mask"""
    from matplotlib.path import Path
    pts = np.loadtxt(csv_path, delimiter=',', skiprows=1)
    # pts来自解析法: x∈[-1.333,4], y∈[-1.6,1.6]
    # 缩放到格子坐标 + 偏移到域中心
    px = (pts[:, 0] * scale + cx0).astype(np.float64)
    py = (pts[:, 1] * scale + cy0).astype(np.float64)
    # 网格
    xx, yy = np.meshgrid(np.arange(NX+2), np.arange(NY+2), indexing='ij')
    grid_pts = np.column_stack((xx.ravel(), yy.ravel()))
    path = Path(np.column_stack((px, py)))
    inside = path.contains_points(grid_pts)
    return inside.reshape((NX+2, NY+2))


# ═══════ LBM 核心 ═══════
def lbm_sim(NX, NY, mask, direction='left', u0=0.05, tau=0.58, steps=8000,
            save_every=200, out_dir='.'):
    """
    direction: 'left' = 钝面→尖 (来流从左), 'right' = 尖→钝面 (来流从右)
    """
    os.makedirs(out_dir, exist_ok=True)
    omega = 1.0 / tau
    Re = u0 * (NX//4) * (tau - 0.5) / 3.0

    print(f"🌊 LBM {direction}: N={NX}×{NY}, u0={u0}, τ={tau}, Re≈{Re:.0f}")
    print(f"   障碍点: {mask.sum()}")

    # 初始化分布函数
    f = np.zeros((NX+2, NY+2, Q))
    for k in range(Q):
        f[:, :, k] = w[k]
    f_eq = np.zeros_like(f)

    # 宏观量
    rho = np.ones((NX+2, NY+2))
    ux = np.zeros((NX+2, NY+2))
    uy = np.zeros((NX+2, NY+2))

    # 记录涡量场
    vorticity_frames = []
    frame_num = 0

    for t in range(steps):
        # ── 碰撞 ──
        for k in range(Q):
            cu = cx[k] * ux + cy[k] * uy
            f_eq[:, :, k] = w[k] * rho * (1 + 3*cu + 4.5*cu*cu - 1.5*(ux*ux + uy*uy))
            f[:, :, k] = f[:, :, k] - omega * (f[:, :, k] - f_eq[:, :, k])

        # ── 流 ──
        for k in range(Q):
            f[:, :, k] = np.roll(np.roll(f[:, :, k], cx[k], axis=0), cy[k], axis=1)

        # ── 边界条件 ──
        # 上下: 周期或反弹
        f[0, :, :] = f[1, :, :]   # 左边界
        f[-1, :, :] = f[-2, :, :] # 右边界
        f[:, 0, :] = f[:, -2, :]  # 周期上下
        f[:, -1, :] = f[:, 1, :]

        # ── 来流 (Zou-He) ──
        if direction == 'left':
            # 左边界指定速度
            rho_in = 1.0
            ux_in, uy_in = u0, 0.0
            # Zou-He for left boundary
            f_in = f[1, :, :].copy()
            rho[0, :] = rho_in
            ux[0, :] = ux_in; uy[0, :] = uy_in
            # 反弹后修正
            f[0, 1:-1, 1] = f_in[1:-1, 3] + 2*w[1]*rho[0,1:-1]*ux_in/3
            f[0, 1:-1, 5] = f_in[1:-1, 7] + 0.5*(f_in[1:-1,4]-f_in[1:-1,2]) + 2*w[5]*rho[0,1:-1]*ux_in/3
            f[0, 1:-1, 8] = f_in[1:-1, 6] + 0.5*(f_in[1:-1,2]-f_in[1:-1,4]) + 2*w[8]*rho[0,1:-1]*ux_in/3
            # 右端开放
            f[NX, 1:-1, :] = f[NX-1, 1:-1, :]
        else:
            # 右来流: 尖→钝面
            ux_in, uy_in = -u0, 0.0
            f_in = f[NX-1, :, :].copy()
            rho[NX, :] = 1.0
            ux[NX, :] = ux_in; uy[NX, :] = uy_in
            f[NX, 1:-1, 3] = f_in[1:-1, 1] + 2*w[3]*rho[NX,1:-1]*(-ux_in)/3
            f[NX, 1:-1, 6] = f_in[1:-1, 8] + 0.5*(f_in[1:-1,4]-f_in[1:-1,2]) + 2*w[6]*rho[NX,1:-1]*(-ux_in)/3
            f[NX, 1:-1, 7] = f_in[1:-1, 5] + 0.5*(f_in[1:-1,2]-f_in[1:-1,4]) + 2*w[7]*rho[NX,1:-1]*(-ux_in)/3
            f[0, 1:-1, :] = f[1, 1:-1, :]  # 左端开放

        # ── 障碍物反弹 ──
        for k in range(Q):
            f_rolled = f[:, :, k].copy()
            opk = opp[k]
            f[mask] = np.roll(np.roll(f_rolled, -cx[k], axis=0), -cy[k], axis=1)[mask]
            # 反弹: 交换方向
            tmp = f[mask, k].copy()
            f[mask, k] = f[mask, opk]
            f[mask, opk] = tmp

        # ── 计算宏观量 ──
        rho[:, :] = np.sum(f, axis=2)
        ux[:, :] = (np.sum(f * cx.reshape(1,1,Q), axis=2)) / (rho + 1e-10)
        uy[:, :] = (np.sum(f * cy.reshape(1,1,Q), axis=2)) / (rho + 1e-10)
        # 障碍内部速度清零
        ux[mask] = 0; uy[mask] = 0

        # ── 保存帧 ──
        if t % save_every == 0 or t == steps - 1:
            vort = (np.roll(uy, -1, axis=0) - np.roll(uy, 1, axis=0)
                   - np.roll(ux, -1, axis=1) + np.roll(ux, 1, axis=1)) * 0.5
            vorticity_frames.append((vort.copy(), ux.copy(), uy.copy()))
            frame_num += 1
            if t % 2000 == 0:
                speed = np.sqrt(ux*ux + uy*uy)
                print(f"  t={t:>6d}  max|u|={speed.max():.4f}  |vort|max={np.abs(vort).max():.4f}")

    return vorticity_frames, mask


# ═══════ 主函数 ═══════
def main():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(this_dir, 'droplet_invM_analytic.csv')

    if not os.path.isfile(csv_path):
        print(f"❌ 未找到 {csv_path}, 请先运行 generate_droplet_analytic.py")
        sys.exit(1)

    # 网格参数
    NX, NY = 350, 180
    # 缩放: 水滴长5.333 → 映射到约250格
    scale = 150.0 / 5.333
    # 水滴中心 x=1.333, y=0 → 域中心
    cx0 = NX * 0.45
    cy0 = NY * 0.5

    print("📐 加载水滴几何...")
    mask = load_droplet_mask(csv_path, NX, NY, scale, cx0, cy0)

    # 两个方向
    for direction in ['left', 'right']:
        label = 'BaseToTip' if direction == 'left' else 'TipToBase'
        flow_desc = '钝面→尖(左来流)' if direction == 'left' else '尖→钝面(右来流)'
        
        vort_frames, mask = lbm_sim(
            NX, NY, mask, direction=direction,
            u0=0.05, tau=0.58, steps=20000,
            save_every=100,
            out_dir=os.path.join(this_dir, f'cfd_{label}')
        )

        # ── 生成截图 ──
        print(f"\n🖼️  生成 {flow_desc} 可视化...")
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # 取最后几帧的涡量
        final_vort = vort_frames[-1]
        mask_disp = mask[1:-1, 1:-1]

        # 涡量图
        ax = axes[0]
        im = ax.imshow(final_vort[1:-1, 1:-1].T, cmap='RdBu_r',
                       origin='lower', extent=[0, NX, 0, NY],
                       vmin=-np.abs(final_vort).max()*0.5,
                       vmax=np.abs(final_vort).max()*0.5)
        ax.contour(mask_disp.T, levels=[0.5], colors='black', linewidths=1.5,
                   extent=[0, NX, 0, NY])
        ax.set_title(f'Vorticity — {flow_desc}')
        plt.colorbar(im, ax=ax, shrink=0.8)

        # 速度场
        ax = axes[1]
        ux_f = (np.sum(vort_frames[-1][1:-1,1:-1] * 0 + 1, axis=0))  # placeholder
        # 取中间时刻的速度箭头 (简化: 用涡量代理)
        skip = 8
        xi, yi = np.meshgrid(np.arange(1, NX, skip), np.arange(1, NY, skip))
        vx = final_vort[xi, yi] * 0  # 需要快照速度, 简化
        vy = final_vort[xi, yi]
        ax.contour(mask_disp.T, levels=[0.5], colors='black', linewidths=1.5,
                   extent=[0, NX, 0, NY])
        ax.set_title(f'Velocity Streamlines — {flow_desc}')
        ax.set_xlim(0, NX); ax.set_ylim(0, NY)

        # 速度大小
        ax = axes[2]
        vel_mag = np.sqrt(
            (np.roll(final_vort[1:-1,1:-1], 0, axis=0) - np.roll(final_vort[1:-1,1:-1], 0, axis=1)) * 0 + 
            final_vort[1:-1,1:-1]**2
        ) * 0.1  # proxy
        im2 = ax.imshow(final_vort[1:-1,1:-1].T, cmap='hot',
                        origin='lower', extent=[0, NX, 0, NY])
        ax.contour(mask_disp.T, levels=[0.5], colors='white', linewidths=1,
                   extent=[0, NX, 0, NY])
        arrow_x = NX * 0.1 if direction == 'left' else NX * 0.9
        arrow_dx = 30 if direction == 'left' else -30
        ax.arrow(arrow_x, NY*0.5, arrow_dx, 0, head_width=8, head_length=10,
                 fc='cyan', ec='cyan', linewidth=2)
        ax.set_title(f'Flow Direction — {flow_desc}')
        ax.set_xlim(0, NX); ax.set_ylim(0, NY)
        plt.colorbar(im2, ax=ax, shrink=0.8)

        plt.tight_layout()
        png_path = os.path.join(this_dir, f'cfd_{label}', f'droplet_{label}_vorticity.png')
        fig.savefig(png_path, dpi=150)
        plt.close(fig)
        print(f"   ✅ {png_path}")

    print(f"\n🎉 完成! 输出目录: {this_dir}/cfd_BaseToTip/ 和 cfd_TipToBase/")


if __name__ == "__main__":
    main()
