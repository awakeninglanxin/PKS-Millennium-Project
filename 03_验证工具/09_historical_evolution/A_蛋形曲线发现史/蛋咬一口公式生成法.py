import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import ezdxf
from tkinter import Tk, filedialog
import os
from scipy.interpolate import splprep, splev

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

# 改进的调制因子函数，确保b曲线闭合且凹陷延伸到第四象限
def closed_modulation(t, k, t0, sigma, alpha, periodic_amp):
    """
    改进的调制因子函数，确保曲线闭合且凹陷延伸到第四象限

    参数:
    t: 参数值
    k: 凹陷深度 (0-1)
    t0: 凹陷中心位置
    sigma: 凹陷宽度
    alpha: 控制凹陷向第四象限延伸的程度
    periodic_amp: 周期性调整的幅度
    """
    # 基础高斯函数
    gaussian = np.exp(-(t - t0) ** 2 / (2 * sigma ** 2))

    # 添加周期性调整，确保在 t=0 和 t=2π 处函数值相同
    periodic_adjust = 1 + periodic_amp * np.sin(t)

    # 不对称函数，使凹陷向第四象限延伸
    extend_factor = 1 + alpha * np.sin((t - t0) / 2)

    return 1 - k * gaussian * extend_factor * periodic_adjust

# 双波调制因子函数，产生双波叠加效应
def double_wave_modulation(t, k, t0, sigma, alpha, periodic_amp,
                           k2, t02, sigma2, alpha2, periodic_amp2):
    """
    双波调制因子函数，产生双波叠加效应

    参数:
    t: 参数值
    k, t0, sigma, alpha, periodic_amp: 第一波参数
    k2, t02, sigma2, alpha2, periodic_amp2: 第二波参数
    """
    # 计算第一波调制
    wave1 = closed_modulation(t, k, t0, sigma, alpha, periodic_amp)

    # 计算第二波调制
    wave2 = closed_modulation(t, k2, t02, sigma2, alpha2, periodic_amp2)

    # 将两波调制相乘，产生叠加效应
    return wave1 * wave2

# 初始参数 - 第一套参数按照要求修改
k0 = 0.29  # 凹陷深度
t00 = 0.49  # 凹陷中心位置
sigma0 = 0.43  # 凹陷宽度
alpha0 = 0.20  # 控制凹陷向第四象限延伸的程度
periodic_amp0 = 0.5  # 周期性调整的幅度

# 第二波初始参数
k20 = 0.3
t020 = np.pi  # 第二波凹陷中心设在π
sigma20 = 0.4
alpha20 = 0.6
periodic_amp20 = 0.05  # 第二波周期性调整的幅度

# 计算初始曲线
x_orig, y_orig = original_curve(t)
g_closed = double_wave_modulation(t, k0, t00, sigma0, alpha0, periodic_amp0,
                                  k20, t020, sigma20, alpha20, periodic_amp20)
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

# 创建滑动条轴 - 第一波参数
ax_k = plt.axes([0.25, 0.55, 0.65, 0.03])
ax_t0 = plt.axes([0.25, 0.50, 0.65, 0.03])
ax_sigma = plt.axes([0.25, 0.45, 0.65, 0.03])
ax_alpha = plt.axes([0.25, 0.40, 0.65, 0.03])
ax_periodic_amp = plt.axes([0.25, 0.35, 0.65, 0.03])

# 创建滑动条 - 第一波参数
k_slider = Slider(ax_k, 'k1 (depth)', 0.0, 1.0, valinit=k0, valstep=0.01)
t0_slider = Slider(ax_t0, 't01 (center)', 0, 2 * np.pi, valinit=t00, valstep=0.01)
sigma_slider = Slider(ax_sigma, 'sigma1 (width)', 0.1, 1.0, valinit=sigma0, valstep=0.01)
alpha_slider = Slider(ax_alpha, 'alpha1 (extend)', 0.0, 2.0, valinit=alpha0, valstep=0.05)
periodic_amp_slider = Slider(ax_periodic_amp, 'periodic amp1', 0, 1, valinit=periodic_amp0, valstep=0.01)

# 创建滑动条轴 - 第二波参数
ax_k2 = plt.axes([0.25, 0.30, 0.65, 0.03])
ax_t02 = plt.axes([0.25, 0.25, 0.65, 0.03])
ax_sigma2 = plt.axes([0.25, 0.20, 0.65, 0.03])
ax_alpha2 = plt.axes([0.25, 0.15, 0.65, 0.03])
ax_periodic_amp2 = plt.axes([0.25, 0.10, 0.65, 0.03])

# 创建滑动条 - 第二波参数
k2_slider = Slider(ax_k2, 'k2 (depth)', 0.0, 1.0, valinit=k20, valstep=0.01)
t02_slider = Slider(ax_t02, 't02 (center)', 0, 2 * np.pi, valinit=t020, valstep=0.01)
sigma2_slider = Slider(ax_sigma2, 'sigma2 (width)', 0.1, 1.0, valinit=sigma20, valstep=0.01)
alpha2_slider = Slider(ax_alpha2, 'alpha2 (extend)', 0.0, 2.0, valinit=alpha20, valstep=0.05)
periodic_amp2_slider = Slider(ax_periodic_amp2, 'periodic amp2', 0, 1, valinit=periodic_amp20, valstep=0.01)

# 创建按钮轴
ax_export = plt.axes([0.8, 0.05, 0.1, 0.04])
export_button = Button(ax_export, 'Export DXF')

ax_import = plt.axes([0.65, 0.05, 0.1, 0.04])
import_button = Button(ax_import, 'Import DXF')

# 更新函数
def update(val):
    k = k_slider.val
    t0 = t0_slider.val
    sigma = sigma_slider.val
    alpha = alpha_slider.val
    periodic_amp = periodic_amp_slider.val

    k2 = k2_slider.val
    t02 = t02_slider.val
    sigma2 = sigma2_slider.val
    alpha2 = alpha2_slider.val
    periodic_amp2 = periodic_amp2_slider.val

    # 计算双波调制因子
    g_closed = double_wave_modulation(t, k, t0, sigma, alpha, periodic_amp,
                                      k2, t02, sigma2, alpha2, periodic_amp2)

    # 更新曲线
    line_closed.set_data(x_orig * g_closed, y_orig * g_closed)

    # 更新标题
    ax.set_title(
        f'Double Wave Modulation: k1={k:.2f}, t01={t0:.2f}, σ1={sigma:.2f}, α1={alpha:.2f}, periodic_amp1={periodic_amp:.2f}\n'
        f'k2={k2:.2f}, t02={t02:.2f}, σ2={sigma2:.2f}, α2={alpha2:.2f}, periodic_amp2={periodic_amp2:.2f}')

    fig.canvas.draw_idle()

# 导出DXF函数
def export_dxf(event):
    k = k_slider.val
    t0 = t0_slider.val
    sigma = sigma_slider.val
    alpha = alpha_slider.val
    periodic_amp = periodic_amp_slider.val

    k2 = k2_slider.val
    t02 = t02_slider.val
    sigma2 = sigma2_slider.val
    alpha2 = alpha2_slider.val
    periodic_amp2 = periodic_amp_slider.val

    # 计算当前调制因子和曲线
    g_closed = double_wave_modulation(t, k, t0, sigma, alpha, periodic_amp,
                                      k2, t02, sigma2, alpha2, periodic_amp2)
    x_current = x_orig * g_closed
    y_current = y_orig * g_closed

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
    filename = (
        f'double_wave_egg_curve_k1_{k:.2f}_t01_{t0:.2f}_sigma1_{sigma:.2f}_alpha1_{alpha:.2f}_periodic1_{periodic_amp:.2f}_'
        f'k2_{k2:.2f}_t02_{t02:.2f}_sigma2_{sigma2:.2f}_alpha2_{alpha2:.2f}_periodic2_{periodic_amp2:.2f}.dxf')
    doc.saveas(filename)
    print(f"曲线已导出到 {filename}")

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
alpha_slider.on_changed(update)
periodic_amp_slider.on_changed(update)

k2_slider.on_changed(update)
t02_slider.on_changed(update)
sigma2_slider.on_changed(update)
alpha2_slider.on_changed(update)
periodic_amp2_slider.on_changed(update)

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