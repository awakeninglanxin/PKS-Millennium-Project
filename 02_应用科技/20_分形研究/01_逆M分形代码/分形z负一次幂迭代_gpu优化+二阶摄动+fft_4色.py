#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified Inverse Mandelbrot Viewer with z = z^-1 + c iteration
- 使用倒数迭代公式 z = 1/z + c
- 同时显示四种初始值情况:
  z = k + k*j (红色)
  z = -k - k*j (绿色)
  z = -k + k*j (蓝色)
  z = k - k*j (黄色)
- 调整视图范围以适应新的迭代公式
- 保留原有的缓存和交互功能
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import time
import warnings
from numba import njit, prange
from matplotlib.colors import ListedColormap


@njit(fastmath=True)
def smooth_inverse_point(c, max_iter, escape_radius, initial_z):
    if abs(c) < 1e-12:
        return max_iter

    z = initial_z  # 使用传入的初始值

    for n in range(max_iter):
        if abs(z) < 1e-12:
            return n
        z = 1.0 / z + c
        if abs(z) > escape_radius:
            return n + 1 - np.log(np.log(abs(z))) / np.log(2.0)
    return max_iter


@njit(parallel=True, fastmath=True)
def compute_inverse(xmin, xmax, ymin, ymax, width, height, max_iter, escape_radius, initial_z):
    out = np.empty((height, width), dtype=np.float64)
    for j in prange(height):
        im = ymin + j * (ymax - ymin) / (height - 1)
        for i in range(width):
            re = xmin + i * (xmax - xmin) / (width - 1)
            out[j, i] = smooth_inverse_point(re + 1j * im, max_iter, escape_radius, initial_z)
    return out

class InverseMandelViewer:
    def __init__(self, width=800, height=600,
                 # 调整视图范围以适应新的迭代公式
                 xmin=-2.0, xmax=2.0,
                 ymin=-2.0, ymax=2.0,
                 base_iter=1024,
                 escape_radius=10.0,
                 gamma=0.5, k=0.5):
        self.width, self.height = width, height
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.base_iter = base_iter
        self.max_iter = base_iter
        self.escape_radius = escape_radius
        self.gamma = gamma
        self.k = k  # 存储 k 值
        # 缓存视图参数与图像
        self.view_stack = []

        # 创建图形
        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        # 初始化图像为RGB格式，用于同时显示四种初始值情况
        self.img = self.ax.imshow(
            np.zeros((height, width, 3)),
            extent=[xmin, xmax, ymin, ymax],
            origin='lower', interpolation='nearest'
        )

        self.rect = RectangleSelector(
            self.ax, self.on_select, useblit=True, button=[1],
            minspanx=5, minspany=5, spancoords='pixels', interactive=True
        )
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.update_plot()

    def update_plot(self):
        t0 = time.time()
        k = self.k  # 使用实例变量 k

        # 计算四种初始值情况
        # 红色通道: z = k + k*j
        raw_red = compute_inverse(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius,
            k + k * 1j
        )

        # 绿色通道: z = -k - k*j
        raw_green = compute_inverse(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius,
            -k - k * 1j
        )

        # 蓝色通道: z = -k + k*j
        raw_blue = compute_inverse(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius,
            -k + k * 1j
        )

        # 黄色通道: z = k - k*j (通过红色和绿色通道的组合表示)
        raw_yellow = compute_inverse(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius,
            k - k * 1j
        )

        # 对每种情况进行归一化
        def normalize_channel(raw):
            mask = raw < self.max_iter
            flat = raw[mask]
            if len(flat) > 0:
                hist, bins = np.histogram(flat, bins=256,
                                         range=(flat.min(), flat.max()), density=True)
                cdf = np.cumsum(hist);
                cdf /= cdf[-1]
                normed = np.interp(raw, bins[:-1], cdf)
            else:
                normed = np.zeros_like(raw)
            normed[~mask] = 0.0
            return normed ** self.gamma  # 指数映射强化高值

        red_channel = normalize_channel(raw_red)
        green_channel = normalize_channel(raw_green)
        blue_channel = normalize_channel(raw_blue)
        yellow_channel = normalize_channel(raw_yellow)

        # 创建RGB图像
        # 红色通道: z = k + k*j
        # 绿色通道: z = -k - k*j
        # 蓝色通道: z = -k + k*j
        # 黄色通道: z = k - k*j (通过红色和绿色通道的组合表示)
        rgb_image = np.zeros((self.height, self.width, 3))
        rgb_image[..., 0] = red_channel + yellow_channel  # 红色通道 + 黄色通道
        rgb_image[..., 1] = green_channel + yellow_channel  # 绿色通道 + 黄色通道
        rgb_image[..., 2] = blue_channel  # 蓝色通道

        # 确保值在[0, 1]范围内
        rgb_image = np.clip(rgb_image, 0, 1)

        # 更新图像
        self.img.set_data(rgb_image)
        self.img.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        zoom = ((self.xmax - self.xmin) / (4.0)) ** (-0.5)
        self.ax.set_title(
            f"Inverse Mandelbrot (z = 1/z + c) | Iter={self.max_iter} | Zoom={zoom:.1f}× | k={k:.2f} | {time.time() - t0:.2f}s\n"
            f"Red: z = {k:.2f}+{k:.2f}j | Green: z = -{k:.2f}-{k:.2f}j\n"
            f"Blue: z = -{k:.2f}+{k:.2f}j | Yellow: z = {k:.2f}-{k:.2f}j"
        )
        self.fig.canvas.draw_idle()
        return rgb_image

    def on_select(self, eclick, erelease):
        # 确保正确获取选择区域的坐标
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        # 确保坐标有效
        if x1 is None or x2 is None or y1 is None or y2 is None:
            return

        # 缓存当前视图
        arr = self.img.get_array().copy()
        self.view_stack.append((self.xmin, self.xmax,
                                self.ymin, self.ymax,
                                self.max_iter, arr))
        # 更新范围与迭代
        self.xmin, self.xmax = sorted([x1, x2])
        self.ymin, self.ymax = sorted([y1, y2])
        scale = (4.0) / (self.xmax - self.xmin)
        self.max_iter = min(200000, int(self.base_iter * np.sqrt(scale)))
        self.update_plot()

    def on_click(self, event):
        if event.button == 3:
            self.go_back()

    def on_key(self, event):
        if event.key == 'backspace':
            self.go_back()
        elif event.key in '123456789':
            self.base_iter = int(event.key) * 100
            self.max_iter = self.base_iter
            self.update_plot()
        elif event.key == 'up':  # 增加 k 值
            self.k = min(200, self.k + 20)
            self.update_plot()
        elif event.key == 'down':  # 减少 k 值
            self.k = max(0.1, self.k - 2)
            self.update_plot()

    def go_back(self):
        if not self.view_stack:
            return
        xmin, xmax, ymin, ymax, iters, imgdata = self.view_stack.pop()
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.max_iter = iters
        # 加载缓存
        self.img.set_data(imgdata)
        self.img.set_extent([xmin, xmax, ymin, ymax])
        zoom = ((xmax - xmin) / (4.0)) ** (-0.5)
        self.ax.set_title(
            f"Inverse Mandelbrot (z = 1/z + c) | Iter={iters} | Zoom={zoom:.1f}× | k={self.k:.2f} (cached)\n"
            f"Red: z = {self.k:.2f}+{self.k:.2f}j | Green: z = -{self.k:.2f}-{self.k:.2f}j\n"
            f"Blue: z = -{self.k:.2f}+{self.k:.2f}j | Yellow: z = {self.k:.2f}-{self.k:.2f}j"
        )

        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    print("Initializing Modified Inverse Mandelbrot Viewer with z = 1/z + c iteration...")
    print("Red channel: z = k + k*j")
    print("Green channel: z = -k - k*j")
    print("Blue channel: z = -k + k*j")
    print("Yellow channel: z = k - k*j")
    print("Use up/down arrow keys to adjust k value")
    viewer = InverseMandelViewer()
    plt.show()