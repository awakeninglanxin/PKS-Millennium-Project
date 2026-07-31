#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inverse Fractal Sound Explorer (逆分形声音探索器)
==================================================
基于 CodeParade FractalSoundExplorer 相同原理，展示逆Mandelbrot集(z²+1/c)及7种逆分形。
点击分形图上的任意点 → 听到该点的轨道声音。
核心变换：所有分形的参数 c → 1/c (复反演)，实现"逆分形"的视觉与听觉体验。

依赖：numpy, matplotlib, wave, winsound, PIL (Pillow)
启动：双击 启动_逆分形声音探索器.bat
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# ★ 修复CJK字体警告
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from matplotlib.widgets import Slider
import threading
import wave
import struct
import winsound
import tempfile
import os
import time
import warnings
warnings.filterwarnings('ignore')

# ── 全局配置 ────────────────────────────────────────
WIDTH, HEIGHT = 600, 400          # 渲染分辨率
MAX_ITER = 300                     # 迭代次数(轨道层数)
ESCAPE_R_SQ = 100.0               # 逃逸半径平方(与CodeParade一致)
SAMPLE_RATE = 48000               # 音频采样率
MAX_FREQ = 4000                   # 最高频率(steps = sample_rate/max_freq ≈ 12)
VIEW_X0, VIEW_Y0 = 1.0, 0.0      # 初始视图中心(偏右，水滴在右侧)
VIEW_W = 6.0                      # 视图宽度: Re(c) ∈ [-2, 4], Im(c) ∈ [-2, 2]
INITIAL_TYPE = 0                  # 初始分形类型: 0=逆Mandelbrot
SUSTAIN_MODE = True               # 持续模式
NORMALIZED = True                 # 归一化模式

# 视图状态
view_cx = VIEW_X0
view_cy = VIEW_Y0
view_w = VIEW_W
orbit_points = []                 # [(x, y), ...] 轨道轨迹
show_orbit = False
fractal_type = INITIAL_TYPE
play_x, play_y = 0.0, 0.0
play_cx, play_cy = 0.0, 0.0
audio_thread = None
is_playing = False
take_screenshot = False
show_help = True

# ── 复反演: 计算 1/c ─────────────────────────────────
def complex_inv(px, py):
    """计算 1/(px + i*py) = px/(px²+py²) - i*py/(px²+py²)"""
    denom = px*px + py*py
    if denom < 1e-12:
        return 1e8, 0.0  # 接近原点→映射到远点
    return px / denom, -py / denom

# ── 8种分形方程 (全部使用 c→1/c 逆变换) ────────────
def fractal_mandelbrot(x, y, cx, cy):
    """逆Mandelbrot: z → z² + 1/c"""
    nx = x*x - y*y + cx
    ny = 2.0*x*y + cy
    return nx, ny

def fractal_burning_ship(x, y, cx, cy):
    """逆Burning Ship: z → (|Re(z)| + i|Im(z)|)² + 1/c"""
    nx = x*x - y*y + cx
    ny = 2.0*abs(x*y) + cy
    return nx, ny

def fractal_feather(x, y, cx, cy):
    """逆Feather: z → z³/(1+z²) + 1/c"""
    denom_re = 1.0 + x*x - y*y
    denom_im = 2.0*x*y
    denom_sq = denom_re*denom_re + denom_im*denom_im
    if denom_sq < 1e-12:
        return 1e8, 0.0
    # z³ = (x+iy)³
    z3_re = x*x*x - 3.0*x*y*y
    z3_im = 3.0*x*x*y - y*y*y
    # z³/(1+z²) = z³ * conj(1+z²) / |1+z²|²
    nx = (z3_re*denom_re + z3_im*denom_im) / denom_sq + cx
    ny = (z3_im*denom_re - z3_re*denom_im) / denom_sq + cy
    return nx, ny

def fractal_sfx(x, y, cx, cy):
    """逆SFX: z → z·|z|² − z·(1/c)² + 1/c (修正版)"""
    mag2 = x*x + y*y
    # c_inv = (cx, cy) 已是1/c
    c2_re = cx*cx - cy*cy
    c2_im = 2.0*cx*cy
    nx = x*mag2 - (x*c2_re - y*c2_im) + cx
    ny = y*mag2 - (x*c2_im + y*c2_re) + cy
    return nx, ny

def fractal_henon(x, y, cx, cy):
    """逆Hénon: x' = 1 − (1/c)_re·x² + y, y' = (1/c)_im·x"""
    nx = 1.0 - cx*x*x + y
    ny = cy*x
    return nx, ny

def fractal_duffing(x, y, cx, cy):
    """逆Duffing: x' = y, y' = −(1/c)_im·x + (1/c)_re·y − y³"""
    nx = y
    ny = -cy*x + cx*y - y*y*y
    return nx, ny

def fractal_ikeda(x, y, cx, cy):
    """逆Ikeda: t = 0.4 − 6/(1+|z|²), z' = 1 + 1/c·(z·e^{it})"""
    t = 0.4 - 6.0/(1.0 + x*x + y*y)
    st = np.sin(t)
    ct = np.cos(t)
    nx = 1.0 + cx*(x*ct - y*st)
    ny = cy*(x*st + y*ct)
    return nx, ny

def fractal_chirikov(x, y, cx, cy):
    """逆Chirikov: y' = y + (1/c)_im·sin(x), x' = x + (1/c)_re·y'"""
    ny = y + cy*np.sin(x)
    nx = x + cx*ny
    return nx, ny

FRACTAL_FUNCS = [
    fractal_mandelbrot,
    fractal_burning_ship,
    fractal_feather,
    fractal_sfx,
    fractal_henon,
    fractal_duffing,
    fractal_ikeda,
    fractal_chirikov,
]
FRACTAL_NAMES = [
    "Inverse Mandelbrot",
    "Inverse Burning Ship",
    "Inverse Feather",
    "Inverse SFX",
    "Inverse Hénon",
    "Inverse Duffing",
    "Inverse Ikeda",
    "Inverse Chirikov",
]

# ── Catmull-Rom 样条(C¹连续, 过所有控制点) ──────────
def _catmull_rom_spline(points, subdiv=6):
    """对控制点序列做 Catmull-Rom 插值, 每段产出 subdiv 个中间点"""
    n = len(points)
    if n < 2:
        return list(points)
    if n == 2:
        # 两点间线性插值
        x0, y0 = points[0]; x1, y1 = points[1]
        return [(x0 + i/subdiv*(x1-x0), y0 + i/subdiv*(y1-y0))
                for i in range(subdiv)] + [points[1]]

    result = []
    for i in range(n - 1):
        # 取四个控制点(边界处用clamp)
        p0 = points[max(i-1, 0)]
        p1 = points[i]
        p2 = points[min(i+1, n-1)]
        p3 = points[min(i+2, n-1)]

        for k in range(subdiv):
            t = k / subdiv
            t2 = t * t
            t3 = t2 * t
            # Catmull-Rom 矩阵形式
            cx = 0.5 * ((2*p1[0]) + (-p0[0] + p2[0])*t +
                        (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0])*t2 +
                        (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0])*t3)
            cy = 0.5 * ((2*p1[1]) + (-p0[1] + p2[1])*t +
                        (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1])*t2 +
                        (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1])*t3)
            result.append((cx, cy))
    result.append(points[-1])
    return result

# ── 分形渲染(向量化) ────────────────────────────────
def render_fractal(t=1.0):
    """渲染当前分形。t控制正逆混合: t=1→纯逆分形(1/c), t=0→纯正分形(c)"""
    global fractal_type
    h = int(view_w * HEIGHT / WIDTH)
    x_min = view_cx - view_w/2
    x_max = view_cx + view_w/2
    y_min = view_cy - h/2
    y_max = view_cy + h/2

    xs = np.linspace(x_min, x_max, WIDTH)
    ys = np.linspace(y_min, y_max, HEIGHT)
    X, Y = np.meshgrid(xs, ys)

    # 计算有效c: c_eff = (1-t)*c + t*(1/c), t控制插值
    denom = X*X + Y*Y + 1e-12
    cx_inv = X / denom
    cy_inv = -Y / denom
    cx_eff = (1-t)*X + t*cx_inv
    cy_eff = (1-t)*Y + t*cy_inv

    Zx = np.zeros_like(X)
    Zy = np.zeros_like(Y)
    escaped = np.full_like(X, MAX_ITER, dtype=np.float64)

    fx = FRACTAL_FUNCS[fractal_type]
    for i in range(MAX_ITER):
        mask = (Zx*Zx + Zy*Zy) < ESCAPE_R_SQ
        if not np.any(mask):
            break
        Zx[mask], Zy[mask] = fx(Zx[mask], Zy[mask], cx_eff[mask], cy_eff[mask])
        escaped[mask & ((Zx*Zx + Zy*Zy) >= ESCAPE_R_SQ)] = i

    # 平滑迭代计数
    log_zn = np.log(np.maximum(Zx*Zx + Zy*Zy, 1e-12)) / 2.0
    nu = np.log(log_zn) / np.log(2.0)
    smooth = escaped + 1.0 - np.clip(nu, 0, 1)
    smooth[np.isnan(smooth)] = MAX_ITER
    return smooth

# ── 琉璃金环色图 ────────────────────────────────────
from matplotlib.colors import LinearSegmentedColormap
_ring_c = [
    (0.000, '#030618'), (0.015, '#081030'), (0.035, '#0c1840'),
    (0.060, '#1a3060'), (0.080, '#385a80'),   # 深蓝幽暗
    (0.100, '#c8a048'), (0.115, '#e8d888'),   # ★ 金环起点
    (0.125, '#fffce8'),                         # ★ 纯白圣光峰值
    (0.135, '#f8f0d0'), (0.150, '#e0d8a8'),   # 暖金渐退
    (0.165, '#90b8d0'), (0.190, '#4070a0'),   # 转蓝
    (0.210, '#102860'), (0.230, '#081840'),   # 暗回归
    (0.260, '#385a80'), (0.280, '#c8a048'),   # ★ 第二圈幽蓝→金
    (0.295, '#fffce8'), (0.305, '#f8f0d0'),   # 白金光晕
    (0.315, '#90b8d0'), (0.340, '#102860'),
    (0.370, '#c8a048'), (0.385, '#fffce8'),   # ★ 第三圈
    (0.395, '#f0d8a0'), (0.410, '#6090b0'),
    (0.450, '#c8a048'), (0.465, '#fffce8'),   # ★ 第四圈
    (0.475, '#e8d090'), (0.490, '#4070a0'),
    (0.540, '#c8a048'), (0.555, '#fffce8'),   # ★ 第五圈
    (0.565, '#d8c880'),
    (0.620, '#a08040'), (0.640, '#fffce8'),   # ★ 第六圈(弱)
    (0.660, '#c0a060'), (0.700, '#3860a0'),
    (0.780, '#081840'), (0.880, '#040c20'),
    (1.000, '#020610'),
]
GOLD_RINGS = LinearSegmentedColormap.from_list('gold_rings', _ring_c)

is_playing = False
current_audio_path = None  # 追踪当前播放的临时WAV路径

# ── 音频合成线程 ────────────────────────────────────
def stop_audio():
    """停止当前所有音频播放"""
    global is_playing, current_audio_path
    winsound.PlaySound(None, winsound.SND_ASYNC)  # 停止SND_LOOP
    is_playing = False
    # 清理旧的临时文件
    if current_audio_path:
        try:
            time.sleep(0.05)
            if os.path.exists(current_audio_path):
                os.unlink(current_audio_path)
        except:
            pass
        current_audio_path = None

def generate_orbit_audio(cx, cy, px, py, save_wav=None):
    """从轨道计算差分向量→生成PCM音频→播放"""
    global fractal_type, is_playing, current_audio_path

    ffunc = FRACTAL_FUNCS[fractal_type]
    steps = SAMPLE_RATE // MAX_FREQ  # ≈12

    # 计算轨道(最多2400步 = 1200迭代 × 2)
    orbit = [(px, py)]
    x, y = px, py
    prev_x, prev_y = px, py
    max_orbit_steps = MAX_ITER * 2

    for _ in range(max_orbit_steps):
        prev_x, prev_y = x, y
        x, y = ffunc(x, y, cx, cy)
        orbit.append((x, y))
        if x*x + y*y > ESCAPE_R_SQ:
            break

    if len(orbit) < 2:
        return

    # 计算差分向量并归一化
    mean_x = px
    mean_y = py

    # 生成PCM样本
    audio_len = len(orbit) * steps * 2  # 16-bit stereo = 2 bytes per sample
    pcm_data = bytearray()

    volume = 8000.0
    dpx, dpy = px - cx, py - cy
    dx, dy = dpx, dpy

    orbit_idx = 0
    while len(pcm_data) < audio_len and orbit_idx + 1 < len(orbit):
        for j in range(steps):
            t = j / steps
            t_interp = 0.5 - 0.5*np.cos(t * np.pi)
            wx = t_interp*dx + (1-t_interp)*dpx
            wy = t_interp*dy + (1-t_interp)*dpy

            # Clamp to 16-bit range
            sample_l = int(np.clip(wx * volume, -32000, 32000))
            sample_r = int(np.clip(wy * volume, -32000, 32000))
            pcm_data.extend(struct.pack('<hh', sample_l, sample_r))

        orbit_idx += 1
        if orbit_idx >= len(orbit):
            break

        prev_orbit_x, prev_orbit_y = orbit[orbit_idx-1]
        curr_orbit_x, curr_orbit_y = orbit[orbit_idx]

        if NORMALIZED:
            dpx = prev_orbit_x - cx
            dpy = prev_orbit_y - cy
            dx = curr_orbit_x - cx
            dy = curr_orbit_y - cy
            dpmag = 1.0 / np.sqrt(1e-12 + dpx*dpx + dpy*dpy)
            dmag = 1.0 / np.sqrt(1e-12 + dx*dx + dy*dy)
            dpx *= dpmag; dpy *= dpmag
            dx *= dmag; dy *= dmag
        else:
            mean_x = mean_x*0.99 + curr_orbit_x*0.01
            mean_y = mean_y*0.99 + curr_orbit_y*0.01
            dx = curr_orbit_x - mean_x
            dy = curr_orbit_y - mean_y
            dpx = prev_orbit_x - mean_x
            dpy = prev_orbit_y - mean_y

        if not SUSTAIN_MODE:
            volume *= 0.9992

        if len(pcm_data) >= audio_len:
            break

    # 写入临时WAV并播放
    if len(pcm_data) > 44:
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.wav')
            os.close(tmp_fd)
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(bytes(pcm_data))

            # 先停止旧音频
            stop_audio()

            # 判定轨道是否逃逸
            final_x, final_y = orbit[-1]
            bounded = (final_x*final_x + final_y*final_y <= ESCAPE_R_SQ)

            is_playing = True
            if bounded:
                # 有界轨道→循环播放(模仿CodeParade持续音效)
                winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            else:
                winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

            current_audio_path = tmp_path

        except Exception as e:
            pass

# ── UI界面 ──────────────────────────────────────────
plt.rcParams['toolbar'] = 'None'
plt.style.use('dark_background')
fig = plt.figure(figsize=(10, 7), facecolor='#060814')
fig.canvas.manager.set_window_title('Inverse Fractal Sound Explorer')

# 分形画面
ax = plt.axes([0.12, 0.18, 0.58, 0.72])
ax.set_facecolor('#060814')

# 初始渲染
data = render_fractal(1.0)
h = int(view_w * HEIGHT / WIDTH)
extent = [view_cx - view_w/2, view_cx + view_w/2, view_cy - h/2, view_cy + h/2]
im = ax.imshow(data, extent=extent, origin='lower', cmap=GOLD_RINGS,
               aspect='equal', interpolation='bilinear')
ax.set_title(f'Inverse Mandelbrot  z→z²+1/c  [Click to hear orbit]', fontsize=11, color='#c8a048')
ax.set_xlabel('Re(c)', fontsize=9, color='#6088b0')
ax.set_ylabel('Im(c)', fontsize=9, color='#6088b0')
ax.tick_params(colors='#6088b0', labelsize=7)

# 轨道线
orbit_line, = ax.plot([], [], 'r-', linewidth=1.0, alpha=0.9)
orbit_dot, = ax.plot([], [], 'ro', markersize=4)

# 信息面板
info_text = ax.text(0.98, 0.98, '', transform=ax.transAxes, fontsize=7,
                    va='top', ha='right', color='#c8a048',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#060814', alpha=0.7))

# ── 滑块 ────────────────────────────────────────────
t_slider_ax = plt.axes([0.12, 0.07, 0.58, 0.03], facecolor='#0d1b3a')
t_slider = Slider(t_slider_ax, 'M <--> InvM', 0.0, 1.0, valinit=1.0, valfmt='%.2f',
                  color='#c8a048')
t_slider_ax.set_facecolor('#0a1020')

# ── 按钮 ────────────────────────────────────────────
type_labels = ['1:InvM', '2:Ship', '3:Fthr', '4:SFX', '5:Hén', '6:Duff', '7:Ikeda', '8:Chir']
btn_axes = []
for i in range(8):
    bx = plt.axes([0.75, 0.82 - i*0.09, 0.10, 0.07])
    bx.set_facecolor('#0d1b3a')
    btn_axes.append(bx)
    btn = plt.Button(bx, type_labels[i], color='#0d1b3a', hovercolor='#1e3a60')
    btn.label.set_color('#6088b0')
    btn.label.set_fontsize(7)

reset_ax = plt.axes([0.75, 0.07, 0.20, 0.04], facecolor='#0d1b3a')
reset_btn = plt.Button(reset_ax, 'R: Reset View', color='#0d1b3a', hovercolor='#1e3a60')
reset_btn.label.set_color('#6088b0')
reset_btn.label.set_fontsize(7)

# ── 交互变量 ────────────────────────────────────────
dragging = False
drag_start = None
pending_render = None

# ── 渲染函数 ────────────────────────────────────────
def update_image(t_val):
    global pending_render
    pending_render = None
    data = render_fractal(t_val)
    h_view = int(view_w * HEIGHT / WIDTH)
    extent_new = [view_cx - view_w/2, view_cx + view_w/2, view_cy - h_view/2, view_cy + h_view/2]
    im.set_data(data)
    im.set_extent(extent_new)
    im.set_clim(1, MAX_ITER)

    fname = FRACTAL_NAMES[fractal_type]
    if t_val > 0.99:
        ttl = f'{fname}  z→(...) + 1/c  [Click to hear orbit]'
    elif t_val < 0.01:
        ttl = f'{fname.replace("Inverse ", "Standard ")}  z→(...) + c'
    else:
        ttl = f'{fname}  [t={t_val:.2f}]'
    ax.set_title(ttl, fontsize=11, color='#c8a048')
    fig.canvas.draw_idle()

def schedule_render(t_val):
    global pending_render
    if pending_render:
        pending_render = None
    pending_render = threading.Timer(0.15, update_image, args=[t_val])
    pending_render.start()

# ── 事件回调 ────────────────────────────────────────
def on_click(event):
    global orbit_points, show_orbit, play_x, play_y, play_cx, play_cy, audio_thread

    if event.inaxes != ax:
        return

    # 点击分形图→播放轨道声音
    px, py = event.xdata, event.ydata
    if px is None or py is None:
        return

    # 计算1/c得到逆参数（这是实际用于迭代的参数）
    cinv_x, cinv_y = complex_inv(px, py)

    # ★ 核心修复：与 CodeParade 原版对齐 ——
    #   原版: z₀=c, 迭代 z²+c。因 c=f_c(0), c∈M 保证 c∈K_c → 轨道有界
    #   逆版: z₀=1/c, 迭代 z²+(1/c)。因 (px,py)∈M_inv → 1/c∈M → 轨道有界
    play_x, play_y = cinv_x, cinv_y   # ← 从1/c出发，不是点击坐标
    play_cx, play_cy = cinv_x, cinv_y

# 轨道轨迹——在标准M空间计算后映射回逆M空间，用插值光滑
    orbit_std = [(cinv_x, cinv_y)]
    x, y = cinv_x, cinv_y
    for _ in range(200):
        x, y = FRACTAL_FUNCS[fractal_type](x, y, cinv_x, cinv_y)
        orbit_std.append((x, y))
        if x*x + y*y > ESCAPE_R_SQ:
            break
    # 把标准M空间轨道 → 逆M空间轨道（逐点取1/z）
    orbit_raw = [(complex_inv(ox, oy)) for (ox, oy) in orbit_std]
    # ── Catmull-Rom 样条插值(过所有控制点, C¹连续, >线性插值) ──
    orbit_points = _catmull_rom_spline(orbit_raw, subdiv=6)
    show_orbit = True

    # 生成并播放音频(后台线程) —— 先停止旧音频
    stop_audio()
    audio_thread = threading.Thread(target=generate_orbit_audio,
                                     args=(cinv_x, cinv_y, cinv_x, cinv_y), daemon=True)
    audio_thread.start()

    update_orbit_line()
    fig.canvas.draw_idle()

def update_orbit_line():
    if show_orbit and len(orbit_points) > 0:
        xs = [p[0] for p in orbit_points]
        ys = [p[1] for p in orbit_points]
        orbit_line.set_data(xs, ys)
        if len(orbit_points) > 0:
            orbit_dot.set_data([orbit_points[0][0]], [orbit_points[0][1]])
    else:
        orbit_line.set_data([], [])
        orbit_dot.set_data([], [])

def on_press(event):
    global dragging, drag_start

    # 区分鼠标事件和键盘事件
    from matplotlib.backend_bases import MouseEvent, KeyEvent

    if isinstance(event, MouseEvent):
        if event.inaxes == ax and event.button == 2:
            dragging = True
            drag_start = (event.xdata, event.ydata)
        elif event.inaxes == ax and event.button == 3:
            global show_orbit, orbit_points
            show_orbit = False
            orbit_points = []
            stop_audio()  # 右键停止音频
            update_orbit_line()
            fig.canvas.draw_idle()
        return

    if isinstance(event, KeyEvent):
        if event.key == 'r':
            reset_view(None)
        elif event.key in ['1','2','3','4','5','6','7','8']:
            change_type(int(event.key)-1)
        elif event.key == 'd':
            global SUSTAIN_MODE
            SUSTAIN_MODE = not SUSTAIN_MODE
            update_info()
        elif event.key == 's':
            save_screenshot()
        elif event.key == 'h':
            global show_help
            show_help = not show_help
            help_panel.set_visible(show_help)
            fig.canvas.draw_idle()
        elif event.key == 'escape':
            plt.close('all')

def on_release(event):
    global dragging, drag_start
    if event.button == 2:
        dragging = False
        drag_start = None

def on_motion(event):
    global dragging, drag_start, view_cx, view_cy
    if dragging and drag_start and event.xdata and event.ydata:
        dx = drag_start[0] - event.xdata
        dy = drag_start[1] - event.ydata
        view_cx += dx
        view_cy += dy
        drag_start = (event.xdata, event.ydata)
        schedule_render(t_slider.val)
    elif event.inaxes == ax and event.xdata and event.ydata:
        # 鼠标悬停时更新坐标信息
        cx_inv, cy_inv = complex_inv(event.xdata, event.ydata)
        info_text.set_text(
            f'c = ({event.xdata:.4f}, {event.ydata:.4f})\n'
            f'1/c = ({cx_inv:.4f}, {cy_inv:.4f})\n'
            f'Type: {FRACTAL_NAMES[fractal_type][:20]}\n'
            f'Sustain: {"ON" if SUSTAIN_MODE else "OFF"}'
        )
        fig.canvas.draw_idle()

def on_scroll(event):
    global view_w, view_cx, view_cy
    if event.inaxes != ax:
        return
    zoom = 0.9 if event.button == 'up' else 1.1
    old_w = view_w
    view_w *= zoom
    view_w = np.clip(view_w, 0.01, 50.0)
    ratio = view_w / old_w
    if event.xdata and event.ydata:
        view_cx = event.xdata - ratio*(event.xdata - view_cx)
        view_cy = event.ydata - ratio*(event.ydata - view_cy)
    schedule_render(t_slider.val)

def change_type(new_type):
    global fractal_type, show_orbit, orbit_points
    fractal_type = new_type
    show_orbit = False
    orbit_points = []
    update_orbit_line()
    schedule_render(t_slider.val)

def reset_view(event):
    global view_cx, view_cy, view_w
    view_cx = VIEW_X0
    view_cy = VIEW_Y0
    view_w = VIEW_W
    schedule_render(t_slider.val)

def save_screenshot():
    timestamp = time.strftime('%m-%d-%y_%H-%M-%S')
    fname = f'screenshot_invM_{timestamp}.png'
    dirpath = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(dirpath, fname)
    fig.savefig(filepath, dpi=150, facecolor='#060814', bbox_inches='tight')
    info_text.set_text(f'Saved: {fname}')
    fig.canvas.draw_idle()

def update_info():
    info_text.set_text(
        f'Type: {FRACTAL_NAMES[fractal_type][:20]}\n'
        f'Sustain: {"ON" if SUSTAIN_MODE else "OFF"}'
    )
    fig.canvas.draw_idle()

# ── 绑定事件 ────────────────────────────────────────
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('button_press_event', on_press)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('scroll_event', on_scroll)
fig.canvas.mpl_connect('key_press_event', on_press)
t_slider.on_changed(schedule_render)

# 按钮回调
for i, bx in enumerate(btn_axes):
    def make_callback(idx):
        return lambda e: change_type(idx)
    plt.Button(bx, type_labels[i], color='#0d1b3a', hovercolor='#1e3a60').on_clicked(
        make_callback(i))

reset_btn.on_clicked(reset_view)

# ── 帮助面板 (移到标题上方，不挡分形图) ──────────
help_panel = fig.text(0.12, 0.94,
    'Click=Play  Scroll=Zoom  MidDrag=Pan  Right=Stop '
    '1-8=Fractal  R=Reset  D=Sustain  S=Screenshot  H=Help  Esc=Quit',
    fontsize=8, va='center', ha='left', color='#6088b0',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#060814', alpha=0.75))

# ── 主循环 ──────────────────────────────────────────
update_info()
plt.show()

print("Inverse Fractal Sound Explorer closed.")
