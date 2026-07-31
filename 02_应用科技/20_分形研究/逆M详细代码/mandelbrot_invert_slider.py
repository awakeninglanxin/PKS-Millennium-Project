#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正Mandelbrot <-> 逆Mandelbrot 交互式滑动变换 — 彩虹同心圆·琉璃渲染版 v3

═══════════════════════════════════════════════════════════════
 渲染核心原理 (还原绚丽彩虹多圈嵌套同心圆)
═══════════════════════════════════════════════════════════════
 1) 平滑逃逸着色 (Smooth Escape):
    普通迭代次数是整数, 会产生明显"色带断层"。这里用复数模长的
    对数变换 nu = log2(log2(|z|)) 把离散迭代数映射为连续浮点数,
    从而在分形边界产生丝滑的彩虹色过渡。

 2) 轨道陷阱同心圆 (Orbit Trap to Origin):
    水滴内部(未逃逸区)不再是死黑! 我们追踪每个点迭代轨道 z_n
    距离坐标原点 (0,0) 的"历史最小距离" trap。用 log(trap) 取模,
    在复平面上等值线会形成一圈圈围绕原点的同心圆环 —— 越靠近
    原点环越密(奇点), 完美还原那种多层嵌套的圆形结构。

 3) 循环色图 (Cyclic Colormap):
    内外着色场都对循环色图取模 (v % 1.0), 首尾颜色相接, 使每一
    圈环无缝衔接, 呈现绚丽的彩虹/紫金/星云渐变。

变换公式: c_eff = c^(1-2t), t in [0,1]
  t=0 -> a=+1 -> z^2+c   (标准M)
  t=1 -> a=-1 -> z^2+1/c (逆M水滴)
  t=.5-> a= 0 -> z^2+1   (统一过渡)
"""

import numpy as np
import matplotlib.pyplot as plt

# ★ 修复CJK字体: SimHei→Microsoft YaHei→DejaVu Sans 降级链
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['font.monospace'] = ['Consolas', 'Courier New', 'DejaVu Sans Mono']
plt.rcParams['axes.unicode_minus'] = False

from matplotlib.widgets import Slider, Button, TextBox
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import time, os, threading, warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

# 脚本所在目录 (保存图片用); 打包/exec 环境 __file__ 缺失时回退到 cwd
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()


# ════════════════════════════════════════════════════
#  多套循环色图 (按 M 键切换) — 首尾同色, 同心圆无缝
# ════════════════════════════════════════════════════

def _cyclic(name, stops):
    """构造首尾闭合的循环渐变色图"""
    n = len(stops)
    pts = [(i / (n - 1), c) for i, c in enumerate(stops)]
    return LinearSegmentedColormap.from_list(name, pts, N=1024)

# 0. 紫金 Purple-Gold (深紫→品红→金→白→金→品红→深紫)
CMAP_PG = _cyclic('purple_gold', [
    '#0a0420', '#3a0a5c', '#7b1fa2', '#c026a0', '#f24d82',
    '#ff9a4d', '#ffd970', '#fff4d8',
    '#ffd970', '#ff9a4d', '#f24d82', '#c026a0', '#7b1fa2', '#3a0a5c', '#0a0420',
])

# 1. 七彩虹 Rainbow (红→橙→黄→绿→青→蓝→紫→红)
CMAP_RB = _cyclic('rainbow_cyc', [
    '#ff2b2b', '#ff8c00', '#ffe000', '#4dff4d', '#00e5d0',
    '#1e90ff', '#5b2bff', '#c02bff', '#ff2bc0', '#ff2b2b',
])

# 2. 金白圣光 Golden Halo (深蓝夜→金→白→天蓝, 4周期循环)
_ring_c = []
for _i in range(4):
    b = _i / 4.0
    _ring_c += [
        (b + 0.000, '#020610'), (b + 0.028, '#0a1840'),
        (b + 0.060, '#c89830'), (b + 0.088, '#e8d878'),
        (b + 0.112, '#fffce8'), (b + 0.140, '#f8e8b0'),
        (b + 0.170, '#8fb4e0'),
    ]
_ring_c.append((1.0, '#020610'))
CMAP_GOLD = LinearSegmentedColormap.from_list('gold_halo', _ring_c, N=1024)

# 3. 暮光 Twilight (matplotlib 内建循环色图, 极适合同心圆)
CMAP_TW = plt.get_cmap('twilight_shifted')

# 4. Turbo 光谱 (高饱和喷射色, 层次分明)
CMAP_TURBO = plt.get_cmap('turbo')

# 5. 星云 Nebula (深空→靛蓝→紫→粉→白, 梦幻全息)
CMAP_NB = _cyclic('nebula', [
    '#050318', '#101a52', '#2e2b8c', '#5a3fc4', '#8f5fdb',
    '#c77fe8', '#f3b4ec', '#fff0fb',
    '#f3b4ec', '#c77fe8', '#8f5fdb', '#5a3fc4', '#2e2b8c', '#101a52', '#050318',
])

# 6. 翡翠琉璃 Jade (墨绿→翡翠→天青→金, 治愈系)
CMAP_JADE = _cyclic('jade_glaze', [
    '#031a14', '#0a3a2c', '#128a5e', '#2fd39a', '#8ff0d0',
    '#e8fff4', '#ffe9a8', '#f0c15a',
    '#ffe9a8', '#8ff0d0', '#2fd39a', '#128a5e', '#0a3a2c', '#031a14',
])

# 7. 烈焰金 Ember (焦黑→暗红→烈焰橙→金→白, 炽热能量)
CMAP_EMBER = _cyclic('ember', [
    '#0a0300', '#3a0a02', '#8a1a05', '#d64518', '#ff7a1a',
    '#ffb84d', '#ffe89a', '#fffdf0',
    '#ffe89a', '#ffb84d', '#ff7a1a', '#d64518', '#8a1a05', '#3a0a02', '#0a0300',
])

RENDER_MODE = 0
MODE_NAMES = ['Purple-Gold', 'Rainbow', 'Golden Halo', 'Twilight', 'Turbo', 'Nebula', 'Jade', 'Ember']
MODE_CMAPS = [CMAP_PG, CMAP_RB, CMAP_GOLD, CMAP_TW, CMAP_TURBO, CMAP_NB, CMAP_JADE, CMAP_EMBER]

# 环密度 (按 [ ] 调整)
RING_FREQ = 2.2       # 内部同心圆密度 (orbit trap)
OUTER_CYCLES = 3.0    # 外部彩环层数 (平滑逃逸)

# ── 双模式配置 ────────────────────────────────────
PW, PH = 300, 300              # Preview 拖拽 (丝滑, 正方形网格)
P_MAXITER = 120
FW, FH = 600, 600              # Final 静止 (精修, 正方形网格)
F_MAXITER = 1024
ESCAPE_RADIUS = 50.0          # 大半径→宽过渡带→多层环可见

# 视图 Re(c)=[-4,4], Im(c)=[-4,4]  (正方形 8x8 复平面)
VIEW_X0, VIEW_Y0 = 0.0, 0.0
VIEW_W = 8.0

# ── 全局状态 ──────────────────────────────────────
view_cx, view_cy = VIEW_X0, VIEW_Y0
view_w = VIEW_W
dragging = False
drag_start = None
final_timer = None
current_mode = 'final'
current_t = 0.0


# ── 核心计算引擎 ──────────────────────────────────

def compute_fractal(x_min, x_max, y_min, y_max, alpha, width, height, max_iter):
    """向量化计算: 返回 (平滑逃逸场 smooth, 轨道陷阱 trap, 内部掩码 interior)"""
    x = np.linspace(x_min, x_max, width)
    y = np.linspace(y_min, y_max, height)
    X, Y = np.meshgrid(x, y)
    c_orig = X + 1j * Y

    # c_eff = c^alpha  (极坐标幂)
    eps = 1e-12
    abs_c = np.abs(c_orig)
    safe = abs_c > eps
    c_eff = np.zeros_like(c_orig, dtype=np.complex128)
    c_eff[safe] = (abs_c[safe] ** alpha) * np.exp(1j * alpha * np.angle(c_orig[safe]))
    if abs(alpha) < 1e-10:
        c_eff[~safe] = 1.0 + 0j
    elif alpha < 0:
        c_eff[~safe] = 1e6 + 0j     # c=0 在逆变换下 → 无穷

    z = np.zeros_like(c_eff, dtype=np.complex128)
    escape = np.full(c_eff.shape, max_iter, dtype=np.float64)
    alive = np.ones(c_eff.shape, dtype=bool)
    trap = np.full(c_eff.shape, 1e18, dtype=np.float64)   # 轨道到原点最小距离

    for i in range(max_iter):
        if not alive.any():
            break
        z[alive] = z[alive] ** 2 + c_eff[alive]
        az = np.abs(z)
        # Orbit Trap: 记录仍存活点轨道距原点的历史最小值 → 内部同心圆
        upd = alive & (az < trap)
        trap[upd] = az[upd]
        div = az > ESCAPE_RADIUS
        escape[div & alive] = i
        alive &= ~div

    # 平滑逃逸着色 (log 变换, 消除色带断层)
    az = np.abs(z) + 1e-12
    log_zn = np.log2(np.maximum(az, 1e-12))
    nu = np.log2(np.maximum(log_zn, 1e-12))
    smooth = escape - nu
    interior = escape >= max_iter
    smooth[interior] = 0.0
    return smooth, trap, interior


def render_image(t, mode='final'):
    """渲染一帧, 生成 [0,1] 着色场 (外环 + 内部同心圆)"""
    alpha = 1.0 - 2.0 * t
    if mode == 'preview':
        w, h, miter = PW, PH, P_MAXITER
    else:
        w, h, miter = FW, FH, F_MAXITER

    # 正方形视野: Re(c) 与 Im(c) 同宽 → 均为 [-4,4]
    half = view_w / 2
    x_min = view_cx - half       # Re(c)
    x_max = view_cx + half
    y_min = view_cy - half       # Im(c)
    y_max = view_cy + half

    t0 = time.time()
    smooth, trap, interior = compute_fractal(x_min, x_max, y_min, y_max,
                                             alpha, w, h, miter)
    elapsed = time.time() - t0

    # rot90(k=3): 水滴尖朝上, 横轴Im 纵轴Re
    smooth = np.rot90(smooth, k=3)
    trap = np.rot90(trap, k=3)
    interior = np.rot90(interior, k=3)

    field = np.zeros_like(smooth)
    ext = ~interior

    # ── 外部: 平滑逃逸 → (直方图均衡) → 循环彩环 ──
    if ext.any():
        se = smooth[ext]
        if mode == 'final':
            lo, hi = se.min(), se.max()
            if hi > lo:
                hist, bins = np.histogram(se, bins=256, range=(lo, hi), density=True)
                cdf = np.cumsum(hist)
                cdf /= cdf[-1]
                se = np.interp(se, bins[:-1], cdf)     # 均衡到 [0,1]
            else:
                se = np.full_like(se, 0.5)             # 退化(α=0)时填中间色, 避免纯黑
        else:
            se = np.clip(se / (P_MAXITER * 0.45), 0, 1)
        field[ext] = (se * OUTER_CYCLES) % 1.0

    # ── 内部: 轨道陷阱 → log 取模 → 围绕原点的同心圆 ──
    if interior.any():
        tl = np.log(trap[interior] + 1e-9)
        field[interior] = (tl * RING_FREQ) % 1.0

    extent = [y_max, y_min, x_min, x_max]
    return field, alpha, elapsed, extent


# ── UI ────────────────────────────────────────────

plt.style.use('dark_background')
fig = plt.figure(figsize=(8, 10), facecolor='#080c18')
fig.canvas.manager.set_window_title('Mandelbrot <-> Inverse Mandelbrot  (Rainbow Rings v3)')

ax = plt.axes([0.10, 0.15, 0.75, 0.78])
ax.set_facecolor('#060814')

field, alpha, elapsed, extent = render_image(0.0, 'final')
im = ax.imshow(field, extent=extent, origin='lower', cmap=MODE_CMAPS[RENDER_MODE],
               aspect='equal', interpolation='bilinear', vmin=0, vmax=1)

ax.set_title('Standard Mandelbrot  z->z^2+c  (t=0.000)', fontsize=12,
             fontweight='bold', color='#b8d4f0', pad=10)
ax.set_xlabel('Im(c)', fontsize=9, color='#8899bb')
ax.set_ylabel('Re(c)', fontsize=9, color='#8899bb')
ax.tick_params(colors='#6677aa', labelsize=8)

# 信息面板 → 视窗右侧外部 (fig.text), 不挡分形图
info_text = fig.text(0.865, 0.845, '', fontsize=7.5,
                     va='top', ha='left', color='#aac8e8', family='monospace',
                     bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a1028',
                               edgecolor='#2e6ba8', alpha=0.85))

# ── Slider ─────────────────────────────────────────

ax_slider = plt.axes([0.13, 0.06, 0.52, 0.03])
slider = Slider(ax_slider, 'c^a', -1.0, 1.0, valinit=0.0, valstep=0.1,
                valfmt='%+.2f', color='#ff4444', track_color='#333355')
ax_slider.set_facecolor('#111122')
slider.valtext.set_visible(False)   # 隐藏自带数值(U+2212来源, 且避免与右侧组件重叠), 改用TextBox

# 左端 s=-1: c^3 三次 | 中点 s=0: c 标准M | 右端 s=+1: 1/c 逆M
ax_label_left = plt.axes([0.055, 0.06, 0.05, 0.03])
ax_label_left.axis('off')
ax_label_left.text(0.5, 0.5, 'c^3', ha='center', va='center', fontsize=9,
                   fontweight='bold', color='#33cc88',
                   transform=ax_label_left.transAxes)

ax_label_mid = plt.axes([0.36, 0.093, 0.06, 0.022])
ax_label_mid.axis('off')
ax_label_mid.text(0.5, 0.5, 'c', ha='center', va='center', fontsize=9,
                  fontweight='bold', color='#4488ff',
                  transform=ax_label_mid.transAxes)

ax_label_right = plt.axes([0.655, 0.06, 0.04, 0.03])
ax_label_right.axis('off')
ax_label_right.text(0.5, 0.5, '1/c', ha='center', va='center', fontsize=9,
                    fontweight='bold', color='#ff4444',
                    transform=ax_label_right.transAxes)

# 输入框: 输入 s 值(范围 -1..+1)按回车确认并更新图
ax_tbox = plt.axes([0.715, 0.06, 0.085, 0.03])
text_box = TextBox(ax_tbox, 's=', initial='', color='#16202e', hovercolor='#22303e')
text_box.label.set_color('#88bbdd')
text_box.label.set_fontsize(9)
text_box.text_disp.set_color('#e0e8f0')
text_box.text_disp.set_fontsize(9)

ax_save = plt.axes([0.865, 0.11, 0.10, 0.03])
btn_save = Button(ax_save, 'Save PNG', color='#1a3344', hovercolor='#2a5577')
btn_save.label.set_color('#aaccee')
btn_save.label.set_fontsize(8)

ax_mode = plt.axes([0.865, 0.075, 0.10, 0.03])
btn_mode = Button(ax_mode, 'Cmap >>', color='#33244a', hovercolor='#553377')
btn_mode.label.set_color('#d8b8ee')
btn_mode.label.set_fontsize(8)

ax_reset = plt.axes([0.865, 0.04, 0.048, 0.03])
btn_reset = Button(ax_reset, 'Reset', color='#222244', hovercolor='#333366')
btn_reset.label.set_color('#8899cc')
btn_reset.label.set_fontsize(8)

ax_help = plt.axes([0.917, 0.04, 0.048, 0.03])
btn_help = Button(ax_help, 'Help', color='#1a2244', hovercolor='#2a3355')
btn_help.label.set_color('#8899cc')
btn_help.label.set_fontsize(8)

# ── 图框右上方: 以原点(0,0)为中心缩放整个视图 ──
fig.text(0.912, 0.955, 'Zoom', fontsize=8, ha='center', color='#88aacc')
ax_zin = plt.axes([0.865, 0.905, 0.048, 0.045])
btn_zin = Button(ax_zin, '+', color='#12331f', hovercolor='#1f6a3f')
btn_zin.label.set_color('#a8ffcc')
btn_zin.label.set_fontsize(17)
btn_zin.label.set_fontweight('bold')

ax_zout = plt.axes([0.917, 0.905, 0.048, 0.045])
btn_zout = Button(ax_zout, '-', color='#331222', hovercolor='#6a1f42')
btn_zout.label.set_color('#ffa8cc')
btn_zout.label.set_fontsize(17)
btn_zout.label.set_fontweight('bold')

# ── Help (纯ASCII, 避免monospace缺CJK字形警告) ──────

help_visible = False
help_panel = None
help_text = """+---------------------------------------------+
|   Mandelbrot  <->  Inverse Mandelbrot       |
+---------------------------------------------+
| Slider : c -> c^(1-2s)   s in [-1, +1]      |
| Wheel  : Zoom       Drag : Pan              |
| +/- btn: zoom about origin (0,0)            |
| Left/Right : fine s  (+-0.02)               |
| Up/Down    : coarse s (+-0.1)               |
| W/A/D      : pan view                       |
+---------------------------------------------+
| M : cycle colormap (8 sets)                 |
| [ / ] : ring density  - / +                 |
| R : Reset   H : Help   S : Save PNG   Q:Quit|
+---------------------------------------------+
| s= 0 -> z^2+c    (Standard M, center)       |
| s=+1 -> z^2+1/c  (Inverse droplet)          |
| s=-1 -> z^2+c^3  (Cubic multibrot)          |
| s=+.5-> z^2+1    (unity, single color)      |
+---------------------------------------------+
| Cmaps: 0 Purple-Gold  1 Rainbow             |
|        2 Golden Halo  3 Twilight            |
|        4 Turbo  5 Nebula  6 Jade  7 Ember   |
+---------------------------------------------+"""


def toggle_help(event):
    global help_visible, help_panel
    if help_visible and help_panel:
        help_panel.remove()
        help_panel = None
        help_visible = False
    else:
        help_panel = fig.text(0.5, 0.5, help_text, fontsize=9,
                              family='monospace', ha='center', va='center',
                              color='white',
                              bbox=dict(boxstyle='round,pad=0.8', facecolor='#111122',
                                        edgecolor='#4488ff', alpha=0.94),
                              transform=fig.transFigure)
        help_visible = True
    fig.canvas.draw_idle()


# ── 更新逻辑 ──────────────────────────────────────

def show_image(t, mode='final'):
    global current_mode
    field, alpha, elapsed, extent = render_image(t, mode)
    im.set_data(field)
    im.set_extent(extent)
    im.set_cmap(MODE_CMAPS[RENDER_MODE])
    im.set_clim(0, 1)
    current_mode = mode

    sign = '+' if alpha >= 0 else ''
    ab = f'a={sign}{alpha:.2f}'
    mode_tag = f'[{MODE_NAMES[RENDER_MODE]}]'
    s = t  # 滑条值 s in [-1,1]
    if abs(s) < 0.03:
        label = f'{mode_tag} Standard M  z->z^2+c  ({ab} s={s:+.2f}) [{elapsed:.1f}s]'
    elif s > 0.97:
        label = f'{mode_tag} Inverse M  z->z^2+1/c  ({ab} s={s:+.2f}) [{elapsed:.1f}s]'
    elif s < -0.97:
        label = f'{mode_tag} Cubic M  z->z^2+c^3  ({ab} s={s:+.2f}) [{elapsed:.1f}s]'
    elif abs(alpha) < 0.03:
        label = f'{mode_tag} Unity  z->z^2+1  ({ab} s={s:+.2f}) [{elapsed:.1f}s]'
    else:
        label = f'{mode_tag} z->z^2+c^{sign}{alpha:.2f}  (s={s:+.2f}) [{elapsed:.1f}s]'
    ax.set_title(label, fontsize=12, fontweight='bold', color='#b8d4f0', pad=10)

    info = (f'Re ={view_cx:+.3f}\n'
            f'Im ={view_cy:+.3f}\n'
            f'w  ={view_w:.2e}\n'
            f'iter={F_MAXITER if mode == "final" else P_MAXITER}\n'
            f'cmap={RENDER_MODE}:{MODE_NAMES[RENDER_MODE][:9]}\n'
            f'ring={RING_FREQ:.1f}/{OUTER_CYCLES:.1f}')
    info_text.set_text(info)
    fig.canvas.draw_idle()


def schedule_final(t):
    global final_timer
    if final_timer:
        final_timer.cancel()
    final_timer = threading.Timer(0.25, lambda: show_image(t, 'final'))
    final_timer.daemon = True
    final_timer.start()


def slider_update(val):
    global current_t
    t = slider.val
    current_t = t
    show_image(t, 'preview')
    schedule_final(t)


slider.on_changed(slider_update)


# ── 交互 ──────────────────────────────────────────

def on_scroll(event):
    global view_w
    factor = 1.25 if event.button == 'down' else 0.8
    view_w = max(1e-12, min(1e8, view_w * factor))
    show_image(slider.val, 'preview')
    schedule_final(slider.val)


def on_press(event):
    global dragging, drag_start
    if event.inaxes == ax and event.button == 1:
        dragging = True
        drag_start = (event.xdata, event.ydata)


def on_release(event):
    global dragging, drag_start
    dragging = False
    if drag_start:
        schedule_final(slider.val)


def on_motion(event):
    global view_cx, view_cy, dragging, drag_start
    if dragging and drag_start and event.xdata and event.ydata:
        view_cy += (event.xdata - drag_start[0])
        view_cx += (event.ydata - drag_start[1])
        drag_start = (event.xdata, event.ydata)
        show_image(slider.val, 'preview')


def cycle_mode():
    global RENDER_MODE
    RENDER_MODE = (RENDER_MODE + 1) % len(MODE_CMAPS)
    t = slider.val
    show_image(t, 'preview')
    schedule_final(t)


def on_key(event):
    global view_cx, view_cy, view_w, RING_FREQ, OUTER_CYCLES
    t = slider.val
    if event.key == 'left':    slider.set_val(max(-1, t - 0.02))
    elif event.key == 'right': slider.set_val(min(1, t + 0.02))
    elif event.key == 'up':    slider.set_val(min(1, t + 0.1))
    elif event.key == 'down':  slider.set_val(max(-1, t - 0.1))
    elif event.key == 'r':
        view_cx, view_cy, view_w = VIEW_X0, VIEW_Y0, VIEW_W
        slider.set_val(0.0)
    elif event.key == 'h': toggle_help(None)
    elif event.key == 'm': cycle_mode()
    elif event.key == '[':
        RING_FREQ = max(0.5, RING_FREQ - 0.4)
        OUTER_CYCLES = max(1.0, OUTER_CYCLES - 0.5)
        show_image(t, 'preview'); schedule_final(t)
    elif event.key == ']':
        RING_FREQ = min(12.0, RING_FREQ + 0.4)
        OUTER_CYCLES = min(12.0, OUTER_CYCLES + 0.5)
        show_image(t, 'preview'); schedule_final(t)
    elif event.key == 's':
        save_snapshot()
    elif event.key in ('q', 'escape'): plt.close('all')
    elif event.key in ('a', 'd', 'w'):
        step = view_w * 0.05
        if event.key == 'a': view_cy -= step
        elif event.key == 'd': view_cy += step
        elif event.key == 'w': view_cx += step
        show_image(t, 'preview'); schedule_final(t)


def on_reset(event):
    global view_cx, view_cy, view_w
    view_cx, view_cy, view_w = VIEW_X0, VIEW_Y0, VIEW_W
    slider.set_val(0.0)


# ── 绑定 ──────────────────────────────────────────
fig.canvas.mpl_connect('scroll_event', on_scroll)
fig.canvas.mpl_connect('button_press_event', on_press)
fig.canvas.mpl_connect('button_release_event', on_release)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('key_press_event', on_key)


def save_snapshot(event=None):
    """按下瞬间保存5张纯分形图(当前缩放视图): s=-1 c^3 / -0.5 c^2 / 0 标准M / +1 逆M / 当前s (跳过退化的+0.5单色)"""
    ts = time.strftime('%Y%m%d_%H%M%S')
    outdir = SCRIPT_DIR
    cmap = MODE_CMAPS[RENDER_MODE]
    ct = slider.val
    jobs = [(-1.0, 'A_cubic_s-1.0'), (-0.5, 'B_quad_s-0.5'), (0.0, 'C_std_s0.0'),
            (1.0, 'D_inv_s+1.0'), (ct, f'E_current_s{ct:+.2f}')]

    # 先提示"正在保存", 同步刷新一次(渲染逆M需数秒)
    info_text.set_text('Saving 5 PNG...')
    try:
        fig.canvas.draw()
    except Exception:
        pass

    saved = []
    for tv, tag in jobs:
        field, alpha, el, ext = render_image(tv, 'final')
        f2 = plt.figure(figsize=(6, 6), facecolor='#080c18')
        a2 = f2.add_axes([0, 0, 1, 1])
        a2.axis('off')
        a2.imshow(field, extent=ext, origin='lower', cmap=cmap,
                  aspect='equal', interpolation='bilinear', vmin=0, vmax=1)
        fn = os.path.join(outdir, f'fractal_{tag}_m{RENDER_MODE}_{ts}.png')
        f2.savefig(fn, dpi=200, facecolor='#080c18')
        plt.close(f2)
        saved.append(os.path.basename(fn))
        print(f'[Save] {fn}')
    info_text.set_text('Saved 5 PNG:\n' + '\n'.join('- ' + s[:22] for s in saved))
    fig.canvas.draw_idle()
    print(f'[Save x5] done -> {outdir}')


def zoom_origin(factor):
    """以复平面原点(0,0)为中心缩放整个视图 (factor<1 放大, >1 缩小)"""
    global view_w, view_cx, view_cy
    view_w = max(1e-12, min(1e8, view_w * factor))
    view_cx *= factor      # 中心按比例向/离原点移动 → 缩放锚定原点
    view_cy *= factor
    show_image(slider.val, 'preview')
    schedule_final(slider.val)


btn_save.on_clicked(save_snapshot)
btn_mode.on_clicked(lambda e: cycle_mode())
btn_reset.on_clicked(on_reset)
btn_help.on_clicked(toggle_help)
btn_zin.on_clicked(lambda e: zoom_origin(0.7))    # + 放大
btn_zout.on_clicked(lambda e: zoom_origin(1.4))   # - 缩小


def submit_s(text):
    """输入框回车: 解析 s 值, 限幅到 [-1,1], 更新滑条并重绘"""
    try:
        v = float(str(text).strip())
    except ValueError:
        return
    v = max(-1.0, min(1.0, v))
    slider.set_val(v)   # 触发 slider_update -> 重绘


text_box.on_submit(submit_s)

print("""
+=====================================================+
| Mandelbrot <-> Inverse Mandelbrot  (Rainbow v3)     |
+=====================================================+
| Orbit-Trap concentric rings around origin (0,0)     |
| Smooth-escape outer bands + 8 cyclic colormaps      |
| M=cmap  [ ]=ring density  Drag=pan  Wheel=zoom       |
| R=reset  H=help  S=save  Q=quit                      |
+=====================================================+
""")

plt.show()
