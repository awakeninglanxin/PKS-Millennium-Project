#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛋形均轮制图 — 水星绕地轨迹（均轮+本轮+活动偏心曲柄 三部件叠加）
=================================================================
历史背景：前哥白尼时代，天文学家在地心说框架下用"均轮 + 本轮 + 偏心圆"
解释行星逆行和轨迹不对称。水星相对地球的轨迹是一个 **蛋形（卵形）闭合曲线**。

三部件：
  A. 均轮(Deferent)  — 大圆，中心在地球，本轮圆心 P_b 绕其匀速公转
  B. 本轮(Epicycle)  — 小圆，圆心在 P_b，以 2× 公转速度自转
  C. 活动偏心曲柄   — 固定偏心点 C，曲柄长 L 连接 P_p → 水星 M

与 PKS 千禧蛋的关系：
  这个蛋形 = 超双曲锥 xy=1 斜切所得蛋形在特定参数下的实例。
  k_E ≈ z1/z2 由均轮/本轮半径比和偏心距共同决定。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.lines import Line2D

# ============================================================
# 铁律 24：中文出图必须设置中文字体
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 模型参数
# ============================================================
R = 8.0              # 均轮半径（Deferent radius）
r = 3.0              # 本轮半径（Epicycle radius）
L = 4.0              # 曲柄长度（Crank rod length）
ecc = 2.5            # 偏心距（Eccentricity，C 点到地球的距离）
T = 20.0             # 公转周期（任意时间单位）
n_points = 800       # 轨迹采样点数

omega = 2 * np.pi / T          # 均轮角速度
omega_epi = 2.0 * omega        # 本轮角速度（2×公转）

# ============================================================
# 计算完整轨迹
# ============================================================
t = np.linspace(0, T, n_points)

# 均轮：本轮中心位置
Pb_x = R * np.cos(omega * t)
Pb_y = R * np.sin(omega * t)

# 本轮：行星点相对本轮中心的位置（2× 角速度）
Pp_rel_x = r * np.cos(omega_epi * t)
Pp_rel_y = r * np.sin(omega_epi * t)

# 本轮上行星点的绝对位置
Pp_x = Pb_x + Pp_rel_x
Pp_y = Pb_y + Pp_rel_y

# 固定偏心点 C（略偏右上 → 打破上下对称 → 蛋形）
C_x = ecc * 0.6
C_y = ecc * 0.3

# 曲柄方向：从 C 指向 Pp
v_x = Pp_x - C_x
v_y = Pp_y - C_y
v_norm = np.sqrt(v_x**2 + v_y**2)

# 水星位置：C + L × 单位方向向量
Mercury_x = C_x + L * v_x / v_norm
Mercury_y = C_y + L * v_y / v_norm

# ============================================================
# 找一个好的快照时间点
# ============================================================
# 选择 t = 0.15*T 作为快照时间（此时各部件位置分散，便于观察）
snapshot_idx = int(0.15 * n_points)

# ============================================================
# 主图：双面板
# ============================================================
fig = plt.figure(figsize=(18, 8))

# ---- 面板 1：完整轨迹 + 快照 ----
ax1 = fig.add_subplot(1, 2, 1)

# 绘制均轮大圆
deferent = Circle((0, 0), R, fill=False, edgecolor='#3498db',
                  linewidth=1.5, linestyle='--', alpha=0.6)
ax1.add_artist(deferent)

# 绘制完整的水星蛋形轨迹
ax1.plot(Mercury_x, Mercury_y, color='#2ecc71', linewidth=2.5,
         label='水星轨迹 (蛋形闭合曲线)', zorder=3)

# 快照：本轮位置的小圆
snap_Pb = (Pb_x[snapshot_idx], Pb_y[snapshot_idx])
epicycle_snap = Circle(snap_Pb, r, fill=False, edgecolor='#e74c3c',
                       linewidth=1.5, linestyle='-', alpha=0.8)
ax1.add_artist(epicycle_snap)

# 快照：本轮中心标记
ax1.plot(snap_Pb[0], snap_Pb[1], 'o', color='#e74c3c', markersize=7,
         zorder=5, label='本轮中心 $P_b$ (快照)')

# 快照：曲柄
snap_v = (Pp_x[snapshot_idx] - C_x, Pp_y[snapshot_idx] - C_y)
snap_v_norm = np.sqrt(snap_v[0]**2 + snap_v[1]**2)
snap_M = (C_x + L * snap_v[0]/snap_v_norm,
          C_y + L * snap_v[1]/snap_v_norm)

ax1.plot([C_x, snap_M[0]], [C_y, snap_M[1]], color='#f39c12',
         linewidth=3, alpha=0.8, zorder=4, label='曲柄 (快照)')

# 固定点
ax1.plot(0, 0, 'o', color='#2980b9', markersize=14, zorder=6,
         label='地球 $O$ (原点)')
ax1.plot(C_x, C_y, 's', color='#8e44ad', markersize=12, zorder=6,
         label='固定偏心点 $C$ (%.1f, 0)' % ecc)

# 快照水星
ax1.plot(snap_M[0], snap_M[1], '*', color='#2ecc71', markersize=18,
         zorder=6, markeredgecolor='#1e8449', markeredgewidth=1,
         label='水星 $M$ (快照)')

# 本轮上 Pp 点
ax1.plot(Pp_x[snapshot_idx], Pp_y[snapshot_idx], 'o', color='#e67e22',
         markersize=6, zorder=5, label='本轮行星点 $P_p$ (快照)')

ax1.set_xlabel('X', fontsize=13)
ax1.set_ylabel('Y', fontsize=13)
ax1.set_title('均轮+本轮+曲柄 → 水星蛋形轨迹', fontsize=14, fontweight='bold')
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.25)
ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)

# 自动确定坐标范围
margin = 2.0
all_x = np.concatenate([Mercury_x, [C_x, 0], Pb_x, Pp_x])
all_y = np.concatenate([Mercury_y, [C_y, 0], Pb_y, Pp_y])
ax1.set_xlim(np.min(all_x) - margin, np.max(all_x) + margin)
ax1.set_ylim(np.min(all_y) - margin, np.max(all_y) + margin)

# ---- 面板 2：几何构造详解 ----
ax2 = fig.add_subplot(1, 2, 2)

# 放大显示快照时刻的几何构造
zoom = 1.1
cx, cy = snap_Pb[0] * 0.3, snap_Pb[1] * 0.3
hw = max(abs(snap_Pb[0]), abs(snap_Pb[1]), R, C_x) * zoom
ax2.set_xlim(cx - hw, cx + hw)
ax2.set_ylim(cy - hw, cy + hw)

# 均轮部分圆弧
theta_arr = np.linspace(0, 2*np.pi, 200)
ax2.plot(R*np.cos(theta_arr), R*np.sin(theta_arr), '--',
         color='#3498db', linewidth=1, alpha=0.5)

# 本轮（快照位置）
epi_theta = np.linspace(0, 2*np.pi, 100)
ax2.plot(snap_Pb[0] + r*np.cos(epi_theta),
         snap_Pb[1] + r*np.sin(epi_theta),
         '-', color='#e74c3c', linewidth=1.5, alpha=0.7)

# 重要点
ax2.plot(0, 0, 'o', color='#2980b9', markersize=16, zorder=10)
ax2.plot(C_x, C_y, 's', color='#8e44ad', markersize=14, zorder=10)
ax2.plot(snap_Pb[0], snap_Pb[1], 'o', color='#e74c3c', markersize=10, zorder=10)
ax2.plot(Pp_x[snapshot_idx], Pp_y[snapshot_idx], 'o', color='#e67e22',
         markersize=8, zorder=10)
ax2.plot(snap_M[0], snap_M[1], '*', color='#2ecc71', markersize=20,
         zorder=10, markeredgecolor='#1e8449', markeredgewidth=1.5)

# 曲柄
ax2.plot([C_x, snap_M[0]], [C_y, snap_M[1]], color='#f39c12',
         linewidth=3, alpha=0.9, zorder=5)

# 本轮半径线（P_b → P_p）
ax2.plot([snap_Pb[0], Pp_x[snapshot_idx]],
         [snap_Pb[1], Pp_y[snapshot_idx]],
         '-', color='#e67e22', linewidth=1.5, alpha=0.6, zorder=4)

# 地球→本轮中心的线
ax2.plot([0, snap_Pb[0]], [0, snap_Pb[1]], ':',
         color='#3498db', linewidth=1, alpha=0.5)

# 标注
offset = 1.5
ax2.annotate('地球 O', (0, 0), textcoords="offset points",
             xytext=(10, -20), fontsize=12, color='#2980b9',
             fontweight='bold', ha='left')
ax2.annotate('偏心点 C', (C_x, C_y), textcoords="offset points",
             xytext=(offset*5, offset*8), fontsize=11, color='#8e44ad',
             fontweight='bold', ha='left')
ax2.annotate('本轮中心 $P_b$', snap_Pb, textcoords="offset points",
             xytext=(offset*5, offset*5), fontsize=11, color='#e74c3c',
             fontweight='bold', ha='left')
ax2.annotate('本轮行星点 $P_p$',
             (Pp_x[snapshot_idx], Pp_y[snapshot_idx]),
             textcoords="offset points", xytext=(offset*3, -offset*3),
             fontsize=10, color='#e67e22', ha='left')
ax2.annotate('水星 M', snap_M, textcoords="offset points",
             xytext=(offset*4, -offset*6), fontsize=12, color='#2ecc71',
             fontweight='bold', ha='left')

# 半径标注
mid_Rx = R * np.cos(omega * t[snapshot_idx]) / 2
mid_Ry = R * np.sin(omega * t[snapshot_idx]) / 2
ax2.annotate(f'R={R:.0f}', (mid_Rx, mid_Ry), fontsize=10,
             color='#3498db', ha='center', va='bottom',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

mid_rx = snap_Pb[0] + r/2 * np.cos(omega_epi * t[snapshot_idx])
mid_ry = snap_Pb[1] + r/2 * np.sin(omega_epi * t[snapshot_idx])
ax2.annotate(f'r={r:.0f}', (mid_rx, mid_ry), fontsize=10,
             color='#e74c3c', ha='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

mid_Lx = (C_x + snap_M[0]) / 2
mid_Ly = (C_y + snap_M[1]) / 2
ax2.annotate(f'L={L:.0f}', (mid_Lx, mid_Ly), fontsize=10,
             color='#f39c12', ha='center', va='bottom',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

ax2.set_aspect('equal')
ax2.set_title('快照时刻几何构造详解 (t = %.1f)' % t[snapshot_idx],
              fontsize=14, fontweight='bold')
ax2.set_xlabel('X', fontsize=13)
ax2.set_ylabel('Y', fontsize=13)
ax2.grid(True, alpha=0.2)

plt.tight_layout(pad=2.0)

# ============================================================
# 保存图片
# ============================================================
output_dir = r'D:\AAA我的文件\PKS_千禧难题_统一解\蛋形均轮'
output_png = output_dir + r'\egg_epicycle.png'

fig.savefig(output_png, dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close(fig)

print(f'✅ 蛋形均轮轨迹图已保存至：{output_png}')
print(f'   参数：R={R}, r={r}, L={L}, eccentricity={ecc}, T={T}')
print(f'   采样点：{n_points}')

# ============================================================
# 额外：单独保存一张纯轨迹图（无标注，适合做封面）
# ============================================================
fig2, ax_traj = plt.subplots(figsize=(10, 10))
ax_traj.plot(Mercury_x, Mercury_y, color='#2ecc71', linewidth=2.5)
ax_traj.plot(0, 0, 'o', color='#2980b9', markersize=12)
ax_traj.plot(C_x, C_y, 's', color='#8e44ad', markersize=10)
ax_traj.set_aspect('equal')
ax_traj.set_title('水星绕地蛋形轨迹', fontsize=16, fontweight='bold')
ax_traj.set_xlabel('X', fontsize=13)
ax_traj.set_ylabel('Y', fontsize=13)
ax_traj.grid(True, alpha=0.2)
ax_traj.set_xlim(np.min(Mercury_x) - margin, np.max(Mercury_x) + margin)
ax_traj.set_ylim(np.min(Mercury_y) - margin, np.max(Mercury_y) + margin)

output_traj = output_dir + r'\egg_epicycle_trajectory.png'
fig2.savefig(output_traj, dpi=200, bbox_inches='tight',
             facecolor='white', edgecolor='none')
plt.close(fig2)
print(f'✅ 纯轨迹图已保存至：{output_traj}')

# ============================================================
# 打印轨迹关键数据
# ============================================================
# 计算蛋形度 k_E（max y / min y 之比，近似）
y_max = np.max(Mercury_y)
y_min = np.min(Mercury_y)
k_E_approx = -y_min / y_max if y_max > 0 else float('inf')
print(f'\n📐 轨迹形状分析：')
print(f'   y_max = {y_max:.3f}')
print(f'   y_min = {y_min:.3f}')
print(f'   k_E ≈ {-y_min/y_max:.3f} (= |y_min|/y_max，蛋形度近似)')
print(f'   偏心距/均轮半径 = {ecc/R:.3f}')
print(f'   本轮半径/均轮半径 = {r/R:.3f}')
