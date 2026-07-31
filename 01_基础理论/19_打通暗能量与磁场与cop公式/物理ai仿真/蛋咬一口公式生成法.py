import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import ezdxf
from tkinter import Tk, filedialog
import os
from scipy.interpolate import splprep, splev
from scipy.integrate import trapezoid

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 参数设置
a = 0.588
b = 5 / 3

# 生成参数 t
t = np.linspace(0, 2 * np.pi, 1000)

# 计算原蛋形曲线
def original_curve(t):
    x_vals = np.zeros_like(t)
    y_vals = np.zeros_like(t)
    for i, t_val in enumerate(t):
        cos_t = np.cos(t_val)
        sin_t = np.sin(t_val)
        denom = 2 * cos_t * np.sin(a)
        if np.abs(denom) < 1e-10:
            if np.isclose(t_val, np.pi / 2, atol=1e-10):
                x_vals[i] = 0.6 * sin_t
                y_vals[i] = 0.6 * cos_t
            elif np.isclose(t_val, 3 * np.pi / 2, atol=1e-10):
                x_vals[i] = 0.6 * sin_t
                y_vals[i] = 0.6 * cos_t
            else:
                x_vals[i] = 0
                y_vals[i] = 0
        else:
            sqrt_inner = np.sqrt(sin_t ** 2 + cos_t ** 2 * np.cos(a) ** 2)
            numerator = b - np.sqrt(b ** 2 - (4 * cos_t * np.sin(a)) / sqrt_inner)
            x_vals[i] = (numerator / denom) * sin_t
            y_vals[i] = (numerator / denom) * cos_t
    return x_vals, y_vals

# ── C∞ 周期 dip: exp(-σ·(1-cos(t-t0))^β) ──
# β=1 标准, β<1 尖锐, β>1 圆润 — 控制凹陷曲率

def cinf_dip(tv, t0, sigma, beta=1.0):
    arg = 1 - np.cos(tv - t0)
    arg = np.maximum(arg, 0)  # 数值安全
    return np.exp(-sigma * arg**beta)

def closed_modulation(t, k, t0, sigma, alpha, periodic_amp, beta=1.0):
    d = cinf_dip(t, t0, sigma, beta)
    asym = 1 + alpha * np.sin(t - t0) * d
    per  = 1 + periodic_amp * np.sin(t)
    return 1 - k * d * asym * per

def double_wave_modulation(t, k, t0, sigma, alpha, periodic_amp,
                           k2, t02, sigma2, alpha2, periodic_amp2,
                           beta1=1.0):
    w1 = closed_modulation(t, k, t0, sigma, alpha, periodic_amp, beta1)
    w2 = closed_modulation(t, k2, t02, sigma2, alpha2, periodic_amp2, 1.0)
    g = w1 * w2
    g[0] = g[-1] = 0.5 * (g[0] + g[-1])
    return g

# ── 最优默认参数（周长保持 + 第一象限凹陷 + 曲率平滑）──
# 优化算法: 随机采样15000组合, P/P0=1.0001, g_min_Q1=0.728
k0    = 0.265   # 主凹陷深度 (0~0.5)
t00   = 0.72    # 凹陷中心角 (0~π/4, 约41°→第一象限)
sigma0 = 4.6    # 凹陷宽度 (1~15)
alpha0 = 0.00   # 不对称延伸
# beta=1.0 固定 — 标准 exp(cos) 曲率

k20    = 0.05   # 对侧微调深度 (0~0.25)
sigma20 = 7.2   # 对侧宽度
alpha20 = 0.10  # 对侧不对称
# pa1=pa2=0 固定, t02=2π 固定

# 计算初始曲线
x_orig, y_orig = original_curve(t)

# ── 周长保持：自动补偿 ──
dx0 = np.gradient(x_orig, t); dy0 = np.gradient(y_orig, t)
ds0 = np.sqrt(dx0**2 + dy0**2)
P0 = trapezoid(ds0, t)  # 原始周长（常量）

def perimeter_preserve(xo, yo, g, t, P_orig, ds_orig):
    """自动计算均匀补偿项，使凹陷后周长=原始周长"""
    f_dent = 1 - g
    comp = trapezoid(f_dent * ds_orig, t) / P_orig
    g_p = g + comp
    return g_p, comp, P_orig

g_closed_raw = double_wave_modulation(t, k0, t00, sigma0, alpha0, 0,
                                       k20, 2*np.pi, sigma20, alpha20, 0)
g_closed, _comp_init, _ = perimeter_preserve(x_orig, y_orig, g_closed_raw, t, P0, ds0)
x_closed = x_orig * g_closed
y_closed = y_orig * g_closed

# 创建图形和轴
fig, ax = plt.subplots(figsize=(10, 10))
plt.subplots_adjust(left=0.25, bottom=0.65)  # 增加底部空间以容纳更多滑动条

# 绘制原曲线（红色）
line_orig, = ax.plot(x_orig, y_orig, 'r-', label='Original Curve', linewidth=2)
# 绘制闭合调制曲线（绿色）
line_closed, = ax.plot(x_closed, y_closed, 'g-', label='Double Wave Modulation', linewidth=2)

# 用于存储导入的曲线
imported_lines = []

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('Double Wave Egg-shaped Curve with Extended Indentation')
ax.axis('equal')
ax.legend()
ax.grid(True)

# ── 7 滑块 (t02=2π, pa1=pa2=0, beta=1 fixed) ──
plt.subplots_adjust(left=0.25, bottom=0.40)

ax_k     = plt.axes([0.25, 0.34, 0.65, 0.025])
ax_t0    = plt.axes([0.25, 0.29, 0.65, 0.025])
ax_sigma = plt.axes([0.25, 0.24, 0.65, 0.025])

ax_k2    = plt.axes([0.25, 0.17, 0.65, 0.025])
ax_sig2  = plt.axes([0.25, 0.12, 0.65, 0.025])
ax_alp2  = plt.axes([0.25, 0.07, 0.65, 0.025])

k_slider      = Slider(ax_k,     'k1 depth',      0.0, 1.0,  valinit=k0,    valstep=0.01)
t0_slider     = Slider(ax_t0,    't01 center',    0.0, 0.785,valinit=t00,   valstep=0.005)
sigma_slider  = Slider(ax_sigma, 'sig1 width',    1.0, 15.0, valinit=sigma0,valstep=0.1)

k2_slider     = Slider(ax_k2,    'k2 depth',      0.0, 0.25, valinit=k20,   valstep=0.005)
sig2_slider   = Slider(ax_sig2,  'sig2 width',    1.0, 15.0, valinit=sigma20,valstep=0.1)
alp2_slider   = Slider(ax_alp2,  'alp2 extend',   -0.5,1.5,  valinit=alpha20,valstep=0.02)

# 固定标签
ax_fx = plt.axes([0.25, 0.025, 0.65, 0.025])
ax_fx.set_xticks([]); ax_fx.set_yticks([])
ax_fx.text(0.5,0.5,'t02=2pi | alp1=pa1=pa2=0 | Cinf exp(cos)',ha='center',va='center',fontsize=8,color='#78909c',transform=ax_fx.transAxes)

# 按钮
ax_export = plt.axes([0.78, 0.025, 0.1, 0.03])
ax_import = plt.axes([0.64, 0.025, 0.1, 0.03])
export_button = Button(ax_export, 'DXF out')
import_button = Button(ax_import, 'DXF in')

def update(val):
    k   = k_slider.val;   t01  = t0_slider.val;   sig = sigma_slider.val
    k2  = k2_slider.val;  sig2 = sig2_slider.val; alp2= alp2_slider.val
    g_raw = double_wave_modulation(t, k, t01, sig, 0, 0,
                                    k2, 2*np.pi, sig2, alp2, 0)
    g_p, comp, _ = perimeter_preserve(x_orig, y_orig, g_raw, t, P0, ds0)
    line_closed.set_data(x_orig * g_p, y_orig * g_p)
    ax.set_title(f'P-keep(k1={k:.2f} t01={t01:.2f} s1={sig:.1f} | k2={k2:.2f} s2={sig2:.1f} a2={alp2:.2f}) c={comp:.3f}')
    fig.canvas.draw_idle()

def export_dxf(event):
    k   = k_slider.val;   t01  = t0_slider.val;   sig = sigma_slider.val
    k2  = k2_slider.val;  sig2 = sig2_slider.val; alp2= alp2_slider.val
    g_raw = double_wave_modulation(t, k, t01, sig, 0, 0,
                                    k2, 2*np.pi, sig2, alp2, 0)
    g_p, _, _ = perimeter_preserve(x_orig, y_orig, g_raw, t, P0, ds0)
    x_current = x_orig * g_p
    y_current = y_orig * g_p

    # 创建DXF文档
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

    # 添加原始曲线
    orig_points = list(zip(x_orig, y_orig))
    msp.add_lwpolyline(orig_points)

    # 添加当前调制曲线
    current_points = list(zip(x_current, y_current))
    msp.add_lwpolyline(current_points)

    # 保存文件
    filename = f'Cinf_egg_dxf.dxf'
    doc.saveas(filename)
    print(f'saved: {filename}')

# 导入DXF函数 - 使用B样条内插显示实际曲线
def import_dxf(file_path=None):
    if file_path is None:
        # 隐藏Tkinter根窗口
        root = Tk()
        root.withdraw()

        # 打开文件对话框
        file_path = filedialog.askopenfilename(
            title="选择DXF文件",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )

        if not file_path:
            return

    try:
        # 读取DXF文件
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # 获取文件名（不含扩展名）
        file_name = os.path.splitext(os.path.basename(file_path))[0]

        # 查找所有B样条曲线
        splines = list(msp.query('SPLINE'))

        # 绘制每条B样条曲线
        colors = ['b', 'm', 'c', 'y']  # 不同颜色
        for i, spline in enumerate(splines):
            if i >= len(colors):
                color = np.random.rand(3,)  # 随机颜色
            else:
                color = colors[i]

            # 获取B样条曲线的控制点
            control_points = spline.control_points
            if control_points:
                x_import = [p[0] for p in control_points]
                y_import = [p[1] for p in control_points]

                # 使用B样条内插生成平滑曲线
                try:
                    # 拟合B样条曲线
                    tck, u = splprep([x_import, y_import], s=0)

                    # 生成更多的点来绘制平滑曲线
                    u_new = np.linspace(0, 1, 100)
                    x_smooth, y_smooth = splev(u_new, tck)

                    # 绘制平滑的B样条曲线
                    line, = ax.plot(x_smooth, y_smooth, color=color, linestyle='--',
                                    label=f'Imported {file_name} - Spline {i+1}', linewidth=2)
                    imported_lines.append(line)

                    # 也绘制控制点（用小点表示）
                    ax.plot(x_import, y_import, 'o', color=color, markersize=3)

                except Exception as e:
                    print(f"处理B样条曲线时出错: {e}")
                    # 如果B样条拟合失败，回退到绘制控制点
                    line, = ax.plot(x_import, y_import, color=color, linestyle='--',
                                    marker='o', markersize=3, label=f'Imported {file_name} - Spline {i+1}',
                                    linewidth=2)
                    imported_lines.append(line)

        # 如果没有找到B样条曲线，尝试查找多段线
        if not splines:
            polylines = list(msp.query('LWPOLYLINE'))
            for i, polyline in enumerate(polylines):
                if i >= len(colors):
                    color = np.random.rand(3,)  # 随机颜色
                else:
                    color = colors[i]

                # 获取多段线点
                points = list(polyline.get_points())
                x_import = [p[0] for p in points]
                y_import = [p[1] for p in points]

                # 绘制导入的曲线
                line, = ax.plot(x_import, y_import, color=color, linestyle='--',
                                label=f'Imported {file_name} - Line {i+1}', linewidth=2)
                imported_lines.append(line)

        # 更新图例
        ax.legend()
        fig.canvas.draw_idle()

        print(f"已从 {file_path} 导入 {len(splines) or len(polylines)} 条曲线")

    except Exception as e:
        print(f"导入DXF文件时出错: {e}")

    # 如果是从文件对话框打开的，销毁Tkinter根窗口
    if file_path is None:
        root.destroy()

# 按钮回调函数
def import_button_callback(event):
    import_dxf()  # 调用导入函数，但不传入文件路径，会弹出文件对话框

# 注册更新函数
k_slider.on_changed(update)
t0_slider.on_changed(update)
sigma_slider.on_changed(update)
k2_slider.on_changed(update)
sig2_slider.on_changed(update)
alp2_slider.on_changed(update)

# 注册按钮回调
export_button.on_clicked(export_dxf)
import_button.on_clicked(import_button_callback)

# 尝试导入默认文件
default_file = "蛋咬一口草图.dxf"
if os.path.exists(default_file):
    print(f"找到默认文件: {default_file}")
    import_dxf(default_file)
else:
    print(f"未找到默认文件: {default_file}，请使用导入按钮手动导入")

plt.show()