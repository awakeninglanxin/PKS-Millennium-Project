import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.widgets import RectangleSelector
from numba import jit, prange
import time
import warnings
from typing import Tuple, List


# ==================== 核心计算函数（Numba加速） ====================
@jit(nopython=True, parallel=True)
def mandelbrot_set(xmin: float, xmax: float, ymin: float, ymax: float,
                   width: int, height: int, max_iter: int) -> np.ndarray:
    """并行计算曼德博集"""
    result = np.zeros((height, width), dtype=np.float32)
    for y in prange(height):
        for x in prange(width):
            re = xmin + x * (xmax - xmin) / (width - 1)
            im = ymin + y * (ymax - ymin) / (height - 1)
            result[y, x] = mandelbrot(re + 1j * im, max_iter)
    return result


@jit(nopython=True, parallel=True)
def inverse_mandelbrot_set(xmin: float, xmax: float, ymin: float, ymax: float,
                           width: int, height: int, max_iter: int) -> np.ndarray:
    """并行计算逆曼德博集"""
    result = np.zeros((height, width), dtype=np.float32)
    for y in prange(height):
        for x in prange(width):
            re = xmin + x * (xmax - xmin) / (width - 1)
            im = ymin + y * (ymax - ymin) / (height - 1)
            result[y, x] = inverse_mandelbrot(re + 1j * im, max_iter)
    return result


@jit(nopython=True)
def mandelbrot(c: complex, max_iter: int) -> float:
    """计算单个点的曼德博逃逸时间"""
    z = 0j
    for n in range(max_iter):
        if abs(z) > 100:
            return n
        z = z * z + c
    return max_iter


@jit(nopython=True)
def inverse_mandelbrot(c: complex, max_iter: int) -> float:
    """计算单个点的逆曼德博逃逸时间"""
    if abs(c) > 1e-5:  # 避免除以零
        z = 0j
        c_inv = 1.0 / c
        escape_radius = 100.0 / abs(c)  # 动态调整逃逸半径
        for n in range(max_iter):
            if abs(z) > escape_radius:
                return n
            z = z ** 2 + c_inv
        return max_iter
    return max_iter


# ==================== 交互系统 ====================
class DualMandelbrotViewer:
    def __init__(self):
        # 初始化图形界面
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(16, 8))
        plt.subplots_adjust(bottom=0.1, top=0.9, left=0.05, right=0.95, wspace=0.2)

        # 视图参数
        self.view_stack: List[Tuple] = []
        self.base_iter = 1000
        self.max_iter = self.base_iter
        self.width, self.height = 800, 600  # 优化分辨率

        # 曼德博集初始视图
        self.mandel_xmin, self.mandel_xmax = -2.0, 1.0
        self.mandel_ymin, self.mandel_ymax = -1.25, 1.25

        # 逆曼德博集初始视图
        self.inv_xmin, self.inv_xmax = -1.5, 4.25
        self.inv_ymin, self.inv_ymax = -2.875, 2.875

        # 创建图像
        self.img1 = self.ax1.imshow(
            np.zeros((self.height, self.width)),
            cmap='twilight_shifted',
            extent=[self.mandel_xmin, self.mandel_xmax, self.mandel_ymin, self.mandel_ymax],
            origin='lower',
            interpolation='bilinear'
        )
        plt.colorbar(self.img1, ax=self.ax1, label='Escape Time')

        self.img2 = self.ax2.imshow(
            np.zeros((self.height, self.width)),
            cmap='twilight_shifted',
            extent=[self.inv_xmin, self.inv_xmax, self.inv_ymin, self.inv_ymax],
            origin='lower',
            interpolation='bilinear'
        )
        plt.colorbar(self.img2, ax=self.ax2, label='Escape Time')

        # 绑定交互事件
        self.rect1 = RectangleSelector(
            self.ax1, lambda eclick, erelease: self.on_select(eclick, erelease, 'mandel'),
            useblit=True, button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )
        self.rect2 = RectangleSelector(
            self.ax2, lambda eclick, erelease: self.on_select(eclick, erelease, 'inv'),
            useblit=True, button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )

        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        # 初始渲染
        self.update_plots()

    def update_titles(self):
        """更新图表标题"""
        mandel_zoom = (2.0 / (self.mandel_xmax - self.mandel_xmin)) ** 0.5
        inv_zoom = (2.0 / (self.inv_xmax - self.inv_xmin)) ** 0.5

        self.ax1.set_title(
            f"Mandelbrot Set | Iter: {self.max_iter} | Zoom: {mandel_zoom:.1f}x\n"
            f"x=[{self.mandel_xmin:.5f}, {self.mandel_xmax:.5f}] y=[{self.mandel_ymin:.5f}, {self.mandel_ymax:.5f}]"
        )
        self.ax2.set_title(
            f"Inverse Mandelbrot Set | Iter: {self.max_iter} | Zoom: {inv_zoom:.1f}x\n"
            f"x=[{self.inv_xmin:.5f}, {self.inv_xmax:.5f}] y=[{self.inv_ymin:.5f}, {self.inv_ymax:.5f}]"
        )
        self.fig.suptitle(
            "[Left]Zoom [Right/Backspace]Back [1-9]Set Iter [R]Reset",
            y=0.95, fontsize=12
        )

    def update_plots(self):
        """更新两个视图"""
        start_time = time.time()

        # 并行计算两个集合
        mandel_data = mandelbrot_set(
            self.mandel_xmin, self.mandel_xmax,
            self.mandel_ymin, self.mandel_ymax,
            self.width, self.height,
            self.max_iter
        )

        inv_data = inverse_mandelbrot_set(
            self.inv_xmin, self.inv_xmax,
            self.inv_ymin, self.inv_ymax,
            self.width, self.height,
            self.max_iter
        )

        # 更新图像
        self.img1.set_data(mandel_data)
        self.img1.set_extent([self.mandel_xmin, self.mandel_xmax, self.mandel_ymin, self.mandel_ymax])
        self.img1.set_norm(colors.PowerNorm(0.3, vmin=0, vmax=self.max_iter))

        self.img2.set_data(inv_data)
        self.img2.set_extent([self.inv_xmin, self.inv_xmax, self.inv_ymin, self.inv_ymax])
        self.img2.set_norm(colors.PowerNorm(0.3, vmin=0, vmax=self.max_iter))

        self.update_titles()
        self.fig.canvas.draw_idle()
        print(f"Render time: {time.time() - start_time:.2f}s")

    def on_select(self, eclick, erelease, set_type: str):
        """处理矩形选择事件"""
        self.view_stack.append((
            self.mandel_xmin, self.mandel_xmax,
            self.mandel_ymin, self.mandel_ymax,
            self.inv_xmin, self.inv_xmax,
            self.inv_ymin, self.inv_ymax,
            self.max_iter
        ))

        if set_type == 'mandel':
            # 更新曼德博视图
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            self.mandel_xmin, self.mandel_xmax = sorted([x1, x2])
            self.mandel_ymin, self.mandel_ymax = sorted([y1, y2])

            # 计算对应的逆曼德博视图
            self.update_inverse_view()
        else:
            # 更新逆曼德博视图
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            self.inv_xmin, self.inv_xmax = sorted([x1, x2])
            self.inv_ymin, self.inv_ymax = sorted([y1, y2])

            # 计算对应的曼德博视图
            self.update_mandel_view()

        # 动态调整迭代次数
        zoom_factor = (2.0 / (self.mandel_xmax - self.mandel_xmin))
        self.max_iter = min(100000, int(self.base_iter * zoom_factor ** 0.5))

        self.update_plots()

    def update_mandel_view(self):
        """从逆曼德博视图更新曼德博视图"""
        # 计算中心点和范围
        inv_center = complex(
            (self.inv_xmin + self.inv_xmax) / 2,
            (self.inv_ymin + self.inv_ymax) / 2
        )
        inv_width = self.inv_xmax - self.inv_xmin
        inv_height = self.inv_ymax - self.inv_ymin

        # 精确的反演变换
        if abs(inv_center) > 1e-5:
            # 计算新中心
            new_center = 1.0 / inv_center
            scale = 1.0 / (abs(inv_center) ** 2)

            # 计算新范围
            new_width = inv_width * scale
            new_height = inv_height * scale

            self.mandel_xmin = new_center.real - new_width / 2
            self.mandel_xmax = new_center.real + new_width / 2
            self.mandel_ymin = new_center.imag - new_height / 2
            self.mandel_ymax = new_center.imag + new_height / 2
        else:
            # 如果接近原点，保持默认视图
            self.reset_view()

    def update_inverse_view(self):
        """从曼德博视图更新逆曼德博视图"""
        # 计算中心点和范围
        mandel_center = complex(
            (self.mandel_xmin + self.mandel_xmax) / 2,
            (self.mandel_ymin + self.mandel_ymax) / 2
        )
        mandel_width = self.mandel_xmax - self.mandel_xmin
        mandel_height = self.mandel_ymax - self.mandel_ymin

        # 精确的反演变换
        if abs(mandel_center) > 1e-5:
            # 计算新中心
            new_center = 1.0 / mandel_center
            scale = 1.0 / (abs(mandel_center) ** 2)

            # 计算新范围
            new_width = mandel_width * scale
            new_height = mandel_height * scale

            self.inv_xmin = new_center.real - new_width / 2
            self.inv_xmax = new_center.real + new_width / 2
            self.inv_ymin = new_center.imag - new_height / 2
            self.inv_ymax = new_center.imag + new_height / 2
        else:
            # 如果接近原点，保持默认视图
            self.reset_view()

    def reset_view(self):
        """重置为初始视图"""
        self.mandel_xmin, self.mandel_xmax = -2.0, 1.0
        self.mandel_ymin, self.mandel_ymax = -1.25, 1.25
        self.inv_xmin, self.inv_xmax = -1.5, 4.25
        self.inv_ymin, self.inv_ymax = -2.875, 2.875
        self.max_iter = self.base_iter

    def on_click(self, event):
        """鼠标点击事件处理"""
        if event.button == 3:  # 右键返回
            self.go_back()

    def on_key_press(self, event):
        """键盘事件处理"""
        if event.key == 'backspace':
            self.go_back()
        elif event.key in '123456789':
            self.base_iter = int(event.key) * 1000
            self.max_iter = self.base_iter
            print(f"Set iterations to {self.max_iter}")
            self.update_plots()
        elif event.key.lower() == 'r':  # 重置视图
            self.reset_view()
            self.update_plots()

    def go_back(self):
        """返回上一视图"""
        if self.view_stack:
            (self.mandel_xmin, self.mandel_xmax,
             self.mandel_ymin, self.mandel_ymax,
             self.inv_xmin, self.inv_xmax,
             self.inv_ymin, self.inv_ymax,
             self.max_iter) = self.view_stack.pop()
            self.update_plots()


# ==================== 主程序 ====================
if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)

    print("Initializing... (first run may be slow due to Numba compilation)")
    viewer = DualMandelbrotViewer()
    plt.show()