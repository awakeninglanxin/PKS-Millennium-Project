import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.widgets import RectangleSelector
from numba import njit, prange
import time
import warnings

# ==================== 核心计算：平滑逃逸次数 ====================
@njit(fastmath=True)
def smooth_inverse_point(c, max_iter, escape_radius):
    if abs(c) < 1e-12:
        return max_iter
    c = 1.0 / c
    z = 0j
    for n in range(max_iter):
        z = z*z + c
        absz = abs(z)
        if absz > escape_radius:
            # ν = n+1 - log2(log|z|)
            return n + 1 - np.log(np.log(absz)) / np.log(2.0)
    return max_iter

@njit(parallel=True, fastmath=True)
def compute_smooth_inverse(xmin, xmax, ymin, ymax,
                           width, height,
                           max_iter, escape_radius):
    out = np.empty((height, width), dtype=np.float64)
    for j in prange(height):
        im = ymin + j*(ymax - ymin)/(height - 1)
        for i in range(width):
            re = xmin + i*(xmax - xmin)/(width - 1)
            out[j, i] = smooth_inverse_point(re + 1j*im,
                                             max_iter,
                                             escape_radius)
    return out

# ==================== 交互可视化 ====================
class InverseMandelbrotViewer:
    def __init__(self,
                 width=800, height=600,
                 xmin=-1.5, xmax=4.25,
                 ymin=-2.875, ymax=2.875,
                 base_iter=1024,
                 escape_radius=50.0):
        self.width, self.height = width, height
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.base_iter = base_iter
        self.max_iter = base_iter
        self.escape_radius = escape_radius
        self.view_stack = []

        # 绘图初始化：先填零，colormap 留空
        self.fig, self.ax = plt.subplots(figsize=(12,8))
        self.img = self.ax.imshow(
            np.zeros((height, width)),
            extent=[xmin, xmax, ymin, ymax],
            origin='lower',
            interpolation='bilinear'
        )
        plt.colorbar(self.img, ax=self.ax, label='Equalized & Cycled')

        # 绑定互动
        self.rect = RectangleSelector(
            self.ax, self.on_select,
            useblit=True, button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.update_plot()

    def update_title(self):
        zoom = ((self.xmax - self.xmin)/(4.25 - (-1.5)))**(-0.5)
        self.ax.set_title(
            f"Inverse Mandelbrot | Iter={self.max_iter} | Zoom={zoom:.1f}×\n"
            f"x=[{self.xmin:.5f}, {self.xmax:.5f}]  y=[{self.ymin:.5f}, {self.ymax:.5f}]\n"
            "[Left drag] Zoom   [Right click/Backspace] Back   [1–9] Set Iter"
        )

    def update_plot(self):
        t0 = time.time()
        raw = compute_smooth_inverse(
            self.xmin, self.xmax,
            self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius
        )

        # —— 1. 对逃逸值做直方图均衡化 ——
        mask = raw < self.max_iter
        flat = raw[mask]
        # 256 bins over [min, max)
        hist, bins = np.histogram(flat, bins=256,
                                  range=(flat.min(), flat.max()),
                                  density=True)
        cdf = np.cumsum(hist)
        cdf /= cdf[-1]
        # 将 raw 映射到 [0,1]
        normed = np.interp(raw, bins[:-1], cdf)
        # 对未逃逸（raw==max_iter）设为 0（或 1）
        normed[~mask] = 0.0

        # —— 2. 应用环形连续色盘 ——
        self.img.set_data(normed)
        self.img.set_cmap('rainbow')       # 环形渐变
        self.img.set_clim(0.0, 1.0)

        self.img.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        self.update_title()
        self.fig.canvas.draw_idle()
        print(f"Render time: {time.time()-t0:.2f}s")

    def on_select(self, eclick, erelease):
        self.view_stack.append((self.xmin, self.xmax,
                                self.ymin, self.ymax,
                                self.max_iter))
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.xmin, self.xmax = sorted([x1, x2])
        self.ymin, self.ymax = sorted([y1, y2])
        scale = (4.25 - (-1.5)) / (self.xmax - self.xmin)
        self.max_iter = min(200000, int(self.base_iter * np.sqrt(scale)))
        self.update_plot()

    def on_click(self, event):
        if event.button == 3:
            self.go_back()

    def on_key(self, event):
        if event.key == 'backspace':
            self.go_back()
        elif event.key in '123456789':
            self.base_iter = int(event.key)*100
            self.max_iter = self.base_iter
            print(f"Base iterations set to {self.base_iter}")
            self.update_plot()

    def go_back(self):
        if self.view_stack:
            self.xmin, self.xmax, self.ymin, self.ymax, self.max_iter = \
                self.view_stack.pop()
            self.update_plot()

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    print("初始化……（首次渲染需编译，可能较慢）")
    viewer = InverseMandelbrotViewer()
    plt.show()