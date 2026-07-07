# -*- coding: utf-8 -*-
"""
4种波纹最佳截面曲线（ln线版）— matplotlib 独立可视化
原版：Rhino脚本 30_4种波纹最佳截面曲线.py / 4种波纹最佳截面曲线ln线.py
转换：Rhino → matplotlib PNG 输出

核心数学：
- 蛋形参数方程：斜切超双曲锥 z = 1/sqrt(x^2+y^2)，平面 z=kx+b
- 参数：(k,b) = (2/3, 5/3) 来自 3-4-5 勾股三角，tg(alpha)=2/3
- 衰减因子：amp(t) = 1 / ((1 + t/(2pi)) * ln(user_num+1))  —— 对数积分衰减
- 双波纹机制：下波盘 = x(t)*amp，上波盘 = y(t)*amp
- 4组方向：0度/90度/180度/270度旋转 + Z偏移（模拟夹层）
"""

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import os

# === 铁律57：三步初始化中文字体 ===
cache_dir = matplotlib.get_cachedir()
for f in os.listdir(cache_dir):
    if f.endswith('.json'):
        os.remove(os.path.join(cache_dir, f))
fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

import numpy as np
from scipy.signal import find_peaks

# ============================================================
# 参数设置（与原Rhino脚本完全一致）
# ============================================================
k, b_val, a, m, user_num, amp1, amp2 = 2/3, 5/3, 2 * math.pi, 2/3, 5, 1, 1
t_min = 2 * math.pi / (user_num + 1)
t_max = 2 * math.pi + (2 * user_num) * math.pi
num_points = 2000
t_values = np.linspace(t_min, t_max, num_points)

# ============================================================
# 核心函数（与原Rhino脚本完全一致）
# ============================================================

def amp_continuous(t, un):
    """连续对数积分衰减因子 — 这是'ln线'版本的关键"""
    return 1.0 / ((1.0 + t/(2*math.pi)) * math.log(un + 1))

def x_fun(t, bk, kk, aa):
    denominator = bk + math.sqrt(max(0, bk**2 - 4 * kk * math.cos(t)))
    if abs(denominator) < 1e-10:
        return 0
    return aa * (2 * math.sin(t) / denominator)

def y_fun(t, bk, kk, aa, mm):
    b2_4k = max(0, bk**2 - 4*kk)
    b2_4kc = max(0, bk**2 - 4*kk*math.cos(t))
    s_b2_4k = math.sqrt(b2_4k)
    s_b2_4kc = math.sqrt(b2_4kc)
    s_1pk2 = math.sqrt(1 + kk**2)
    term1 = -((s_1pk2 * (-s_b2_4k + s_b2_4kc))) / (2*kk)
    t2n1 = ((kk**2 - 1)/kk) * bk + ((kk**2 + 1)/kk) * s_b2_4kc
    t2p1 = (1/(2*s_1pk2)) * t2n1
    t2n2 = bk*(-1 + kk**2) + s_b2_4k*(1 + kk**2)
    t2p2 = t2n2 / (2*kk*s_1pk2)
    term2 = t2p1 - t2p2
    return aa * (mm*term1 + term2)

def x_minus_fn(t, bk, kk, aa, tm, av):
    return x_fun(t, bk, kk, aa) - aa * av * tm

def y_add_fn(t, bk, kk, aa, mm, tm, av):
    return y_fun(t, bk, kk, aa, mm) + aa * av * tm

# ============================================================
# 计算所有4组曲线数据
# ============================================================

def compute_group(t_arr, use_amp, rot_deg):
    """计算一组旋转后的双波纹曲线"""
    rad = math.radians(rot_deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    xa, ya, ma = [], [], []
    for t in t_arr:
        av = amp_continuous(t, user_num)
        raw_x = x_minus_fn(t, b_val, k, a, t_min, use_amp)
        raw_y = y_add_fn(t, b_val, k, a, m, t_min, use_amp)
        # 旋转变换
        xr = cos_r * raw_x - sin_r * raw_y
        yr = sin_r * raw_x + cos_r * raw_y
        xa.append(xr)
        ya.append(yr)
        ma.append((xr + yr) / 2)
    return xa, ya, ma

g1 = compute_group(t_values, amp1, 0)     # 第1组 蓝
g2 = compute_group(t_values, amp2, 90)   # 第2组 绿
g3 = compute_group(t_values, amp1, 180)  # 第3组 红
g4 = compute_group(t_values, amp2, 270)  # 第4组 黄

groups_data = [
    ("第1组(蓝) amp1 0deg",   g1[0], g1[1], g1[2], '#0066CC', 0),
    ("第2组(绿) amp2 90deg",  g2[0], g2[1], g2[2], '#009933', -12),
    ("第3组(红) amp1 180deg", g3[0], g3[1], g3[2], '#CC0000', -24),
    ("第4组(黄) amp2 270deg", g4[0], g4[1], g4[2], '#CC9900', -36),
]

# ============================================================
# 图1：主图 — 复现参考图三视图布局
# ============================================================
fig = plt.figure(figsize=(20, 15))
fig.suptitle(
    r'4种双波纹盘截面曲线（$\ln$线衰减版）' + '\n'
    r'$(k,b)=(\frac{2}{3},\frac{5}{3})$ from 3-4-5 triangle | '
    r'$amp(t)=\frac{1}{(1+\frac{t}{2\pi})\cdot\ln(n+1)}$ | $n_{seg}=5$',
    fontsize=16, fontweight='bold', y=0.98)

# ---- 上半部：侧视图（上下波纹，对应参考图上半部分）----
ax_side = fig.add_subplot(2, 2, 1)
xa1, ya1, ma1 = g1
ax_side.plot(xa1, t_values/(2*math.pi), 'b-', lw=2.0,
             label=r'下波盘 $x_{add}$ (amp=1)')
ax_side.plot(ya1, t_values/(2*math.pi), 'r-', lw=2.0,
             label=r'上波盘 $y_{minus}$ (amp=1)')
ax_side.plot(ma1, t_values/(2*math.pi), 'g-', lw=1.2, alpha=0.7,
             label='中间包络')
ax_side.axhline(y=0, color='gray', ls=':', alpha=0.4)
ax_side.set_xlabel('振幅 X方向', fontsize=12)
ax_side.set_ylabel(r'归一化参数 $t/2\pi$ (圈数)', fontsize=12)
ax_side.set_title('侧视图：第1组双波纹盘截面\n上下波盘 + 中间线', fontsize=13, fontweight='bold')
ax_side.legend(loc='upper right', fontsize=10)
ax_side.grid(True, alpha=0.3)

# 叠加衰减包络区域
av_all = np.array([amp_continuous(t, user_num) for t in t_values])
x_range = max(xa1) - min(xa1)
y_range = max(ya1) - min(ya1)
ax_side.fill_betweenx(t_values/(2*math.pi),
                       -av_all*x_range*0.45, av_all*y_range*0.45,
                       color='cyan', alpha=0.08, label='ln衰减包络')

# ---- 左下：顶视图（4组叠加，对应参考图左下螺旋蛋叠加）----
ax_top = fig.add_subplot(2, 2, 2)
for i, (name, xa, _, ma, col, zo) in enumerate(groups_data):
    # 用x_add作为X坐标，y_minus作为Y坐标画蛋形轨迹
    ax_top.plot(xa, groups_data[i][1], color=col, lw=1.4, alpha=0.85,
                label=name.replace(' ', '\n'))
ax_top.set_xlabel('X', fontsize=12)
ax_top.set_ylabel('Y', fontsize=12)
ax_top.set_title('顶视图：4组旋转方向的蛋形截面\n(0/90/180/270 deg)', fontsize=13, fontweight='bold')
ax_top.legend(loc='lower left', fontsize=9, ncol=2)
ax_top.axis('equal')
ax_top.grid(True, alpha=0.3)
lim = 10
ax_top.set_xlim(-lim, lim)
ax_top.set_ylim(-lim, lim)

# ---- 右中：Z轴堆叠视图（对应参考图右下多层结构）----
ax_stack = fig.add_subplot(2, 2, 3)
norm_t = (t_values - t_min) / (t_max - t_min) * 60  # 展开长度
for i, (name, xa, ya, ma, col, zo) in enumerate(groups_data):
    ax_stack.plot(norm_t, [zo + v*0.25 for v in xa], color=col, lw=1.5,
                  alpha=0.9, label=f'{name[:6]} Z={zo}')
    ax_stack.plot(norm_t, [zo + v*0.25 for v in ya], color=col, lw=1.5,
                  alpha=0.9)
ax_stack.set_xlabel('展开长度（归一化参数t）', fontsize=12)
ax_stack.set_ylabel('Z层级 + Y振幅', fontsize=12)
ax_stack.set_title('侧视展开：4组Z偏移夹层堆叠\n模拟双波纹盘多层夹层结构', fontsize=13, fontweight='bold')
ax_stack.legend(loc='lower left', fontsize=9)
ax_stack.grid(True, alpha=0.3)
z_ticks = [0, -12, -24, -36]
ax_stack.set_yticks(z_ticks)
for zt in z_ticks:
    ax_stack.axhline(y=zt, color='gray', ls='--', alpha=0.3)

# ---- 右下：衰减因子详细分析 ----
ax_amp = fig.add_subplot(2, 2, 4)
ax_amp.plot(t_values/(2*math.pi), av_all, 'b-', lw=2.5,
            label=r'$amp(t)$')
ax_amp.fill_between(t_values/(2*math.pi), av_all, alpha=0.15, color='blue')
# 关键点标注
for frac, label in [(0, '起点'), (0.5, '中点'), (1.0, '终点')]:
    idx = int(frac * (num_points - 1))
    ax_amp.annotate(f'{label}\nt={t_values[idx]/(2*math.pi):.2f}π\namp={av_all[idx]:.4f}',
                    xy=(t_values[idx]/(2*math.pi), av_all[idx]),
                    xytext=(t_values[idx]/(2*math.pi)+0.5, av_all[idx]+0.02),
                    fontsize=9, arrowprops=dict(arrowstyle='->', color='navy', lw=0.8))
ax_amp.set_xlabel(r'$t / 2\pi$ (圈数)', fontsize=12)
ax_amp.set_ylabel(r'衰减因子 $amp(t)$', fontsize=12)
ax_amp.set_title(
    rf'$\ln$积分衰减包络: $user\_num={user_num}$, $\ln({user_num+1})={math.log(user_num+1):.4f}$',
    fontsize=13, fontweight='bold')
ax_amp.legend(fontsize=11)
ax_amp.grid(True, alpha=0.3)
ax_amp.set_xlim(0, max(t_values/(2*math.pi)))

plt.tight_layout(rect=[0, 0.02, 1, 0.94])
out1 = '09_4种双波纹盘截面_ln线.png'
fig.savefig(out1, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out1}")
plt.close()

# ============================================================
# 图2：4组逐组详细对比
# ============================================================
fig2, axes2 = plt.subplots(2, 2, figsize=(20, 13))
fig2.suptitle(
    r'4种波纹截面 · 逐组详细对比 | Egg Parametric + $\ln$ Decay + 4-Quadrant Rotation',
    fontsize=14, fontweight='bold')

for idx, (name, xa, ya, ma, col, zo) in enumerate(groups_data):
    ax = axes2.flat[idx]
    ax.plot(t_values/(2*math.pi), xa, '-', color=col, lw=2.0,
            label=r'下波盘 $x_{add}$')
    ax.plot(t_values/(2*math.pi), ya, '--', color=col, lw=1.6, alpha=0.7,
            label=r'上波盘 $y_{minus}$')
    ax.plot(t_values/(2*math.pi), ma, ':', color='green', lw=1.3, alpha=0.6,
            label='中线')
    # 衰减背景
    y_max = max(max(xa), max(ya))
    y_min = min(min(xa), min(ya))
    ax.fill_between(t_values/(2*math.pi), y_min*av_all, y_max*av_all,
                    color=col, alpha=0.05)
    ax.set_xlabel(r'$t/2\pi$', fontsize=11)
    ax.set_ylabel('振幅', fontsize=11)
    ax.set_title(f'{name}  Z_offset={zo}', fontsize=12, fontweight='bold',
                 color=col if col != '#CC9900' else '#B8860B')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', lw=0.5, alpha=0.25)

plt.tight_layout(rect=[0, 0, 1, 0.95])
out2 = '10_4种波纹截面逐组详细.png'
fig2.savefig(out2, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out2}")
plt.close()

# ============================================================
# 图3：最优截面候选分析 — 流体力学视角
# ============================================================
fig3, axes3 = plt.subplots(1, 3, figsize=(20, 6))
fig3.suptitle(
    r'最优波纹盘截面分析（第1组 amp1）| $(k,b)=(\frac{2}{3},\frac{5}{3})$ '
    r'| $\tan(\alpha)=2/3 \Rightarrow \alpha \approx 33.69°$',
    fontsize=14, fontweight='bold')

xa1_ref, ya1_ref, ma1_ref = g1

# --- 3a: 相空间轨迹 ---
ax_xy = axes3[0]
ax_xy.plot(xa1_ref, ya1_ref, 'b-', lw=1.6, alpha=0.85, label='双波纹耦合轨迹')
ax_xy.plot(ma1_ref, ma1_ref, 'g:', lw=1.0, alpha=0.4, label='对角参考')
sc = ax_xy.scatter(xa1_ref[::40], ya1_ref[::40],
                   c=np.arange(len(t_values))[::40], cmap='plasma', s=15,
                   alpha=0.65, zorder=5)
ax_xy.set_xlabel(r'下波盘 $x_{add}$', fontsize=11)
ax_xy.set_ylabel(r'上波盘 $y_{minus}$', fontsize=11)
ax_xy.set_title('相空间：上下波盘耦合\n外圈→内收缩=流体向心加速', fontsize=11)
ax_xy.legend(fontsize=9)
ax_xy.axis('equal')
ax_xy.grid(True, alpha=0.3)
cbar = plt.colorbar(sc, ax=ax_xy, shrink=0.82)
cbar.set_label('时间进程', fontsize=10)

# --- 3b: 齿距演化 ---
ax_wave = axes3[1]
peaks_x, _ = find_peaks(np.array(xa1_ref), distance=25)
peaks_y, _ = find_peaks(np.array(ya1_ref), distance=25)
if len(peaks_x) > 1:
    wl_x = np.diff(t_values[peaks_x]/(2*math.pi))
    ax_wave.plot(t_values[peaks_x][1:]/(2*math.pi), wl_x, 'bo-', lw=1.8,
                 markersize=6, label='下波盘齿距 Δt')
if len(peaks_y) > 1:
    wl_y = np.diff(t_values[peaks_y]/(2*math.pi))
    ax_wave.plot(t_values[peaks_y][1:]/(2*math.pi), wl_y, 'rs--', lw=1.8,
                 markersize=6, label='上波盘齿距 Δt')
ax_wave.set_xlabel(r'位置 ($t/2\pi$)', fontsize=11)
ax_wave.set_ylabel('齿距 (Δ 圈数)', fontsize=11)
ax_wave.set_title('齿距演化：向中心逐渐加密\n符合Schauberger内爆涡旋特征', fontsize=11)
ax_wave.legend(fontsize=9)
ax_wave.grid(True, alpha=0.3)

# --- 3c: 截面积 vs 衰减 ---
ax_area = axes3[2]
width = np.abs(np.array(xa1_ref) - np.array(ya1_ref))
area_proxy = width * av_all
ax_area.semilogy(t_values/(2*math.pi), area_proxy, 'purple', lw=2.2,
                  label=r'通道面积代理 $|x-y|\times amp$')
ax_area.semilogy(t_values/(2*math.pi), av_all/av_all[0]*area_proxy[0], 'b--', lw=1.2,
                  alpha=0.6, label='纯衰减因子 (归一化)')
# 1/t 参考
t_mid = len(t_values)//2
t_safe_idx = np.where(t_values > t_values[t_mid])[0]
if len(t_safe_idx) > 1:
    one_ot = 1.0 / (t_values[t_safe_idx]/(2*math.pi))
    one_ot_n = one_ot / one_ot[0] * area_proxy[t_safe_idx[0]]
    ax_area.semilogy(t_values[t_safe_idx]/(2*math.pi), one_ot_n, 'r:', lw=1.4,
                      alpha=0.6, label='1/t 参考 (归一化)')
ax_area.set_xlabel(r'$t/2\pi$ (圈数)', fontsize=11)
ax_area.set_ylabel('相对值 (log尺度)', fontsize=11)
ax_area.set_title('截面积衰减 vs 1/t 双曲线\n越近中心→面积越小→速度越高(Bernoulli)', fontsize=11)
ax_area.legend(fontsize=9)
ax_area.grid(True, alpha=0.3, which='both')

plt.tight_layout(rect=[0, 0, 1, 0.92])
out3 = '11_4种波纹截面流体力学分析.png'
fig3.savefig(out3, dpi=200, bbox_inches='tight', facecolor='white')
print(f"[OK] 保存: {out3}")
plt.close()
print("\n=== 全部完成 ===")
