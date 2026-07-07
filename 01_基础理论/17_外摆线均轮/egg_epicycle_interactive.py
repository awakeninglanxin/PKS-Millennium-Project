#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛋形均轮 — 交互式调参界面
========================
托勒密偏心均轮模型：均轮圆心偏心(不在原点)→本轮叠加→蛋形轨迹

正确模型：M = C + (R cos wt + r cos wr*wt,  R sin wt + r sin wr*wt)
  - C 是偏心点（均轮圆心偏离地球原点）
  - C_y != 0 → 打破对称 → 蛋形！

用法：python egg_epicycle_interactive.py
     或双击 运行蛋形均轮.bat
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# ============================================================
# 铁律 24：中文出图 — rcParams 必须在任何 figure 创建前设置
# ============================================================
plt.rcParams['font.sans-serif'] = [
    'Microsoft YaHei', 'SimHei', 'STXihei',
    'KaiTi', 'FangSong', 'SimSun', 'DejaVu Sans'
]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.default'] = 'regular'

# ============================================================
# 全局样式
# ============================================================
BG_COLOR = '#fafbfc'
PANEL_BG = '#ffffff'
TITLE_COLOR = '#1a1a2e'

C_EARTH   = '#2980b9'   # 地球蓝
C_DEFER   = '#3498db'   # 均轮蓝
C_EPI     = '#9b59b6'   # 本轮紫
C_CRANK   = '#f39c12'   # 曲柄橙
C_EGG     = '#2ecc71'   # 蛋形绿
C_ECC     = '#e74c3c'   # 偏心红
C_PP      = '#e67e22'   # Pp 橙

# ============================================================
# 默认参数 — k_E ≈ 2.0 八度蛋
# ============================================================
R0 = 8.0            # 均轮半径
r0 = 2.5            # 本轮半径
ecc_x0 = 0.0        # 偏心点 x（均轮圆心 x=0 居中）
ecc_y0 = 3.0        # 偏心点 y（=3 -> k_E=1.973 八度蛋！）
omega_ratio0 = 2.0  # 本轮角速度 / 均轮角速度
T = 2 * np.pi       # 公转周期固定=2π（ω=1，轨迹与T无关）

# ============================================================
# 计算函数 — 托勒密偏心均轮模型
# ============================================================
def compute_trajectory(R, r_val, ecc_x, ecc_y, omega_ratio):
    """
    托勒密偏心均轮（T=2π 固定，ω_deferent=1）"""
    omega_epi = omega_ratio
    n_pts = max(800, int(omega_epi * 50))  # 大角速比需高采样
    n_pts = min(n_pts, 20000)              # 上限防卡顿
    t_arr = np.linspace(0, 2*np.pi, n_pts)

    # 均轮圆心在 C，P_b 在均轮圆周上（ω=1）
    Pb_x = ecc_x + R * np.cos(t_arr)
    Pb_y = ecc_y + R * np.sin(t_arr)

    # 本轮行星点
    Pp_rel_x = r_val * np.cos(omega_epi * t_arr)
    Pp_rel_y = r_val * np.sin(omega_epi * t_arr)

    # M = P_p = 本轮上的行星
    M_x = Pb_x + Pp_rel_x
    M_y = Pb_y + Pp_rel_y

    return {
        't': t_arr,
        'M_x': M_x, 'M_y': M_y,
        'Pb_x': Pb_x, 'Pb_y': Pb_y,
    }

def compute_kE(M_x, M_y):
    """蛋形度 k_E = y_max / |y_min|"""
    y_max = np.max(M_y)
    y_min = np.min(M_y)
    if abs(y_min) < 1e-9:
        return float('inf')
    return y_max / abs(y_min)

# ============================================================
# 创建图窗
# ============================================================
fig = plt.figure(figsize=(14, 9), facecolor=BG_COLOR)
fig.canvas.manager.set_window_title('蛋形均轮 — 托勒密偏心模型')

# ---- 主绘图区域 ----
ax_main = plt.axes([0.08, 0.38, 0.60, 0.58], facecolor=PANEL_BG)
ax_main.set_aspect('equal')
ax_main.grid(True, alpha=0.2, linestyle='--')
ax_main.set_facecolor(PANEL_BG)

# ---- 信息面板 ----
ax_info = plt.axes([0.71, 0.80, 0.26, 0.16], facecolor=PANEL_BG)
ax_info.set_xticks([]); ax_info.set_yticks([])
for spine in ax_info.spines.values():
    spine.set_visible(True); spine.set_edgecolor('#e0e0e0')

# ============================================================
# 初始轨迹
# ============================================================
data = compute_trajectory(R0, r0, ecc_x0, ecc_y0, omega_ratio0)
kE = compute_kE(data['M_x'], data['M_y'])

theta_c = np.linspace(0, 2*np.pi, 300)

# 绿色蛋形轨迹
line_traj, = ax_main.plot(data['M_x'], data['M_y'], color=C_EGG,
                           linewidth=2.5, zorder=5, label='水星蛋形轨迹')

# 均轮虚圆（圆心在 C）
line_deferent, = ax_main.plot(
    ecc_x0 + R0 * np.cos(theta_c),
    ecc_y0 + R0 * np.sin(theta_c),
    '--', color=C_DEFER, linewidth=1.2, alpha=0.5, label='均轮 (圆心=C)')

# 快照索引
snap_idx = int(0.15 * len(data['M_x']))

# 本轮圆（快照）
line_epicycle, = ax_main.plot(
    data['Pb_x'][snap_idx] + r0 * np.cos(theta_c),
    data['Pb_y'][snap_idx] + r0 * np.sin(theta_c),
    '-', color=C_EPI, linewidth=1.2, alpha=0.6, label='本轮 (r)')

# 曲柄线 C → P_b（快照）
line_crank, = ax_main.plot(
    [ecc_x0, data['Pb_x'][snap_idx]],
    [ecc_y0, data['Pb_y'][snap_idx]],
    '-', color=C_CRANK, linewidth=3, alpha=0.8, zorder=4, label='偏心臂 (C->P_b)')

# 本轮半径线 P_b → M（快照）
line_epi_r, = ax_main.plot(
    [data['Pb_x'][snap_idx], data['M_x'][snap_idx]],
    [data['Pb_y'][snap_idx], data['M_y'][snap_idx]],
    '-', color=C_EPI, linewidth=1.5, alpha=0.5)

# 固定点
pt_earth, = ax_main.plot(0, 0, 'o', color=C_EARTH, markersize=12,
                          zorder=7, label='地球 O (原点)')
pt_ecc, = ax_main.plot(ecc_x0, ecc_y0, 's', color=C_ECC, markersize=10,
                        zorder=7, label='偏心点 C (均轮圆心)')
pt_pb, = ax_main.plot(data['Pb_x'][snap_idx], data['Pb_y'][snap_idx],
                       'o', color=C_EPI, markersize=8, zorder=7, label='本轮中心 P_b')
pt_mercury, = ax_main.plot(data['M_x'][snap_idx], data['M_y'][snap_idx],
                            '*', color=C_EGG, markersize=18, zorder=7,
                            markeredgewidth=1.5, markeredgecolor='#1e8449',
                            label='水星 M (快照)')

ax_main.legend(loc='upper right', fontsize=8, framealpha=0.85,
               facecolor='white', edgecolor='#e0e0e0')

# ============================================================
# 坐标范围
# ============================================================
def auto_limits(M_x, M_y, R, ecx, ecy):
    """确保蛋形曲线+均轮大圆始终完整可见"""
    all_x = np.concatenate([M_x, [ecx + R, ecx - R, ecx, 0]])
    all_y = np.concatenate([M_y, [ecy + R, ecy - R, ecy, 0]])
    marg = max(R * 0.30, 3.0)
    return (np.min(all_x) - marg, np.max(all_x) + marg,
            np.min(all_y) - marg, np.max(all_y) + marg)

xl0, xl1, yl0, yl1 = auto_limits(data['M_x'], data['M_y'], R0, ecc_x0, ecc_y0)
ax_main.set_xlim(xl0, xl1); ax_main.set_ylim(yl0, yl1)

# ============================================================
# 信息面板
# ============================================================
def info_str(R, r_val, ecx, ecy, wr, kE):
    return (
        f"[ 蛋形均轮参数 ]\n"
        f"------------------------\n"
        f"均轮 R = {R:.1f} (圆心=C)\n"
        f"本轮 r = {r_val:.1f}\n"
        f"偏心 C = ({ecx:.2f}, {ecy:.2f})\n"
        f"角速比 w_r = {wr:.2f}\n"
        f"------------------------\n"
        f"蛋形度 k_E = {kE:.3f}"
    )
info_text = ax_info.text(0.05, 0.95, info_str(R0, r0, ecc_x0, ecc_y0, omega_ratio0, kE),
                          transform=ax_info.transAxes, fontsize=10,
                          va='top', ha='left', color=TITLE_COLOR, linespacing=1.6)

ax_main.set_title('托勒密偏心均轮模型：M = C + 均轮 + 本轮',
                  fontsize=14, fontweight='bold', color=TITLE_COLOR, pad=10)
ax_main.set_xlabel('X', fontsize=11, color='#555')
ax_main.set_ylabel('Y', fontsize=11, color='#555')

# ============================================================
# 滑块
# ============================================================
plt.subplots_adjust(left=0.08, bottom=0.08, right=0.97, top=0.96)

ay = [0.31, 0.25, 0.19, 0.13]  # 4 行

ax_R  = plt.axes([0.08, ay[0], 0.40, 0.022], facecolor='#e8f0fe')
# T 固定=2π（ω=1），轨迹形状与 T 无关 → 不需要滑块
ax_r  = plt.axes([0.08, ay[1], 0.40, 0.022], facecolor='#f3e5f5')
ax_wr = plt.axes([0.55, ay[1], 0.40, 0.022], facecolor='#f3e5f5')
ax_ex = plt.axes([0.08, ay[2], 0.40, 0.022], facecolor='#fff3e0')
ax_ey = plt.axes([0.55, ay[2], 0.40, 0.022], facecolor='#fff3e0')

s_R  = Slider(ax_R,  '均轮半径 R', 1.0, 15.0, valinit=R0, valstep=0.1, color=C_DEFER)
s_r  = Slider(ax_r,  '本轮半径 r', 0.5, 8.0,  valinit=r0, valstep=0.1, color=C_EPI)
s_wr = Slider(ax_wr, '角速比 w_r', 0.5, 240.0, valinit=omega_ratio0, valstep=1.0, color=C_EPI)
s_ex = Slider(ax_ex, '偏心 X (均轮圆心)', -5.0, 8.0, valinit=ecc_x0, valstep=0.05, color=C_ECC)
s_ey = Slider(ax_ey, '偏心 Y (!=0→蛋形)', -5.0, 5.0, valinit=ecc_y0, valstep=0.05, color=C_ECC)

# 分组标签
def add_label(x, y, t, c, bg):
    a = plt.axes([x, y, 0.16, 0.018])
    a.set_xticks([]); a.set_yticks([]); a.set_facecolor(bg)
    for s in a.spines.values(): s.set_visible(False)
    a.text(0.5, 0.5, t, transform=a.transAxes, fontsize=10, fontweight='bold',
           color=c, ha='center', va='center')

add_label(0.08, 0.335, '[均轮 A]',  C_DEFER, '#e8f0fe')
add_label(0.08, 0.275, '[本轮 B]',  C_EPI,   '#f3e5f5')
add_label(0.08, 0.215, '[偏心 C]',  C_ECC,   '#fff3e0')

# 按钮
ax_reset  = plt.axes([0.08, 0.055, 0.10, 0.028])
ax_snap   = plt.axes([0.20, 0.055, 0.13, 0.028])
ax_export = plt.axes([0.35, 0.055, 0.10, 0.028])
btn_reset  = Button(ax_reset,  '重置默认', color='#e8e8e8', hovercolor='#d0d0d0')
btn_snap   = Button(ax_snap,   '隐藏/显示快照', color='#d5f5e3', hovercolor='#abebc6')
btn_export = Button(ax_export, '保存PNG',  color='#d6eaf8', hovercolor='#aed6f1')

# 底部提示
ax_hint = plt.axes([0.55, 0.05, 0.40, 0.04])
ax_hint.set_xticks([]); ax_hint.set_yticks([]); ax_hint.set_facecolor(BG_COLOR)
for s in ax_hint.spines.values(): s.set_visible(False)
ax_hint.text(0.5, 0.5,
    '模型: M = C + 均轮 + 本轮 | C_y != 0 打破对称 -> 蛋形!',
    transform=ax_hint.transAxes, fontsize=9, color='#888', ha='center', va='center')

# ============================================================
# 更新函数
# ============================================================
snap_vis = [True]

def update(val=None):
    R = s_R.val; rv = s_r.val; ex = s_ex.val; ey = s_ey.val
    wr = s_wr.val

    data = compute_trajectory(R, rv, ex, ey, wr)
    kE = compute_kE(data['M_x'], data['M_y'])

    # 轨迹
    line_traj.set_data(data['M_x'], data['M_y'])
    # 均轮（圆心在偏心点 C）
    line_deferent.set_data(
        ex + R * np.cos(theta_c), ey + R * np.sin(theta_c))
    # 视图
    xl = auto_limits(data['M_x'], data['M_y'], R, ex, ey)
    ax_main.set_xlim(xl[0], xl[1]); ax_main.set_ylim(xl[2], xl[3])

    if snap_vis[0]:
        si = int(0.15 * len(data['M_x']))
        # 本轮
        epi_x = data['Pb_x'][si] + rv * np.cos(theta_c)
        epi_y = data['Pb_y'][si] + rv * np.sin(theta_c)
        line_epicycle.set_data(epi_x, epi_y)
        # 曲柄
        line_crank.set_data([ex, data['Pb_x'][si]], [ey, data['Pb_y'][si]])
        # 本轮半径
        line_epi_r.set_data(
            [data['Pb_x'][si], data['M_x'][si]],
            [data['Pb_y'][si], data['M_y'][si]])
        # 点
        pt_ecc.set_data([ex], [ey])
        pt_pb.set_data([data['Pb_x'][si]], [data['Pb_y'][si]])
        pt_mercury.set_data([data['M_x'][si]], [data['M_y'][si]])
        for o in [line_epicycle, line_crank, line_epi_r, pt_pb, pt_mercury, pt_ecc]:
            o.set_visible(True)

    info_text.set_text(info_str(R, rv, ex, ey, wr, kE))
    fig.canvas.draw_idle()

def reset_defaults(event):
    s_R.set_val(R0); s_r.set_val(r0); s_ex.set_val(ecc_x0)
    s_ey.set_val(ecc_y0); s_wr.set_val(omega_ratio0)

def toggle_snapshot(event):
    snap_vis[0] = not snap_vis[0]
    v = snap_vis[0]
    for o in [line_epicycle, line_crank, line_epi_r, pt_pb, pt_mercury]:
        o.set_visible(v)
    pt_ecc.set_visible(True)
    if v: update()
    fig.canvas.draw_idle()

def export_png(event):
    from tkinter import Tk, filedialog
    Tk().withdraw()
    fname = filedialog.asksaveasfilename(
        defaultextension='.png', filetypes=[('PNG图片', '*.png')],
        initialdir='.', title='保存蛋形均轮轨迹图')
    if fname:
        fig.savefig(fname, dpi=200, bbox_inches='tight',
                    facecolor=BG_COLOR, edgecolor='none')
        print(f'图片已保存: {fname}')

# 绑定
s_R.on_changed(update); s_r.on_changed(update); s_ex.on_changed(update)
s_ey.on_changed(update); s_wr.on_changed(update)
btn_reset.on_clicked(reset_defaults)
btn_snap.on_clicked(toggle_snapshot)
btn_export.on_clicked(export_png)

plt.show()
