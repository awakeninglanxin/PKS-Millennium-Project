import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.widgets import RectangleSelector
from numba import jit
import time


# ==================== 核心计算函数（Numba加速） ====================
@jit(nopython=True)
def mandelbrot(c, max_iter):
    z = 0j
    for n in range(max_iter):
        if abs(z) > 4:
            return n
        z = z * z + c
    return max_iter


@jit(nopython=True)
def compute_mandelbrot(xmin, xmax, ymin, ymax, width, height, max_iter):
    result = np.zeros((height, width))
    for x in range(width):
        for y in range(height):
            re = xmin + x * (xmax - xmin) / width
            im = ymin + y * (ymax - ymin) / height
            result[y, x] = mandelbrot(re + 1j * im, max_iter)
    return result


# ==================== 交互系统 ====================
class MandelbrotViewer:
    def __init__(self):
        # 视图历史和初始参数
        self.view_stack = []
        self.max_iter = 256
        self.base_iter = 256
        self.width, self.height = 800, 600

        # 初始视图范围
        self.xmin, self.xmax = -2.0, 1.0
        self.ymin, self.ymax = -1.25, 1.25

        # 创建图形界面
        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        # 使用'hsv'色彩映射 - 颜色鲜艳且循环变化
        self.img = self.ax.imshow(
            np.zeros((self.height, self.width)),
            cmap='hsv',  # 使用HSV色彩映射，颜色鲜艳且循环
            extent=[self.xmin, self.xmax, self.ymin, self.ymax],
            origin='lower',
            interpolation='bilinear'
        )
        plt.colorbar(self.img, ax=self.ax, label='Escape Time')
        self.update_title()

        # 绑定交互事件
        self.rect = RectangleSelector(
            self.ax, self.on_select,
            useblit=True, button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        # 初始渲染
        self.update_plot()

    def update_title(self):
        zoom_factor = (2.0 / (self.xmax - self.xmin)) ** 0.5
        self.ax.set_title(
            f"Mandelbrot Set | Iter: {self.max_iter} | Zoom: {zoom_factor:.1f}x\n"
            f"x=[{self.xmin:.5f}, {self.xmax:.5f}] y=[{self.ymin:.5f}, {self.ymax:.5f}]\n"
            "[Left]Zoom [Right/Backspace]Back [1-9]Set Iter"
        )

    def update_plot(self):
        start_time = time.time()
        divergence = compute_mandelbrot(
            self.xmin, self.xmax,
            self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter
        )
        self.img.set_data(divergence)
        self.img.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        # 使用PowerNorm增强颜色对比度
        self.img.set_norm(colors.PowerNorm(0.3, vmin=0, vmax=self.max_iter))
        self.update_title()
        self.fig.canvas.draw_idle()
        print(f"Render time: {time.time() - start_time:.2f}s")

    def on_select(self, eclick, erelease):
        # 记录当前视图
        self.view_stack.append((
            self.xmin, self.xmax,
            self.ymin, self.ymax,
            self.max_iter
        ))

        # 计算新范围
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.xmin, self.xmax = sorted([x1, x2])
        self.ymin, self.ymax = sorted([y1, y2])

        # 动态增加迭代次数（基于缩放级别）
        zoom_factor = (2.0 / (self.xmax - self.xmin))
        self.max_iter = min(100000, int(self.base_iter * zoom_factor ** 0.5))

        self.update_plot()

    def on_click(self, event):
        if event.button == 3:  # 右键返回
            self.go_back()

    def on_key_press(self, event):
        if event.key == 'backspace':
            self.go_back()
        elif event.key in '123456789':
            self.base_iter = int(event.key) * 100
            self.max_iter = self.base_iter
            print(f"Set iterations to {self.max_iter}")
            self.update_plot()

    def go_back(self):
        if self.view_stack:
            (self.xmin, self.xmax,
             self.ymin, self.ymax,
             self.max_iter) = self.view_stack.pop()
            self.update_plot()


# ==================== 主程序 ====================
if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore", category=UserWarning)  # 忽略Numba警告

    print("Initializing... (first run may be slow due to Numba compilation)")
    viewer = MandelbrotViewer()
    plt.show()