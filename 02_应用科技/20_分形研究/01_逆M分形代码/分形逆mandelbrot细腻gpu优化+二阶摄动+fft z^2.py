#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Inverse Mandelbrot Viewer with Cached Back Navigation
- 直接计算平滑逃逸次数，使用 1/c 倒数映射
- 纯 NumPy + Numba CPU 并行
- 增加缓存：放大时保存当前渲染图像，上一级直接加载缓存，免重算
- 交互：拖框放大、右键/Backspace 返回、1–9 设置迭代
- nearest 插值，分段组合 11 种 colormap，指数映射强化高值
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import time
import warnings
from numba import njit, prange
from matplotlib.colors import ListedColormap

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
            return n + 1 - np.log(np.log(absz)) / np.log(2.0)
    return max_iter

@njit(parallel=True, fastmath=True)
def compute_inverse(xmin, xmax, ymin, ymax, width, height, max_iter, escape_radius):
    out = np.empty((height, width), dtype=np.float64)
    for j in prange(height):
        im = ymin + j*(ymax - ymin)/(height - 1)
        for i in range(width):
            re = xmin + i*(xmax - xmin)/(width - 1)
            out[j, i] = smooth_inverse_point(re + 1j*im, max_iter, escape_radius)
    return out

class InverseMandelViewer:
    def __init__(self, width=800, height=600,
                 xmin=-1.5, xmax=4.25,
                 ymin=-2.875, ymax=2.875,
                 base_iter=1024, escape_radius=50.0,
                 gamma=0.5):
        self.width, self.height = width, height
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.base_iter = base_iter
        self.max_iter = base_iter
        self.escape_radius = escape_radius
        self.gamma = gamma
        # 缓存视图参数与图像
        self.view_stack = []

        # 合成多段 colormap: 按指定顺序组合
        cmap_names = [
            'spring','spring_r','cool','summer','summer_r',
            'cool','autumn','autumn_r','cool',
            'winter','winter_r','cool','magma','cool',
            'inferno','cool','plasma','cool',
            'gist_rainbow','cool','hsv','cool',
            'gist_ncar','cool'
        ]
        colors = []
        nseg = 256 // len(cmap_names)
        for name in cmap_names:
            cmap = plt.get_cmap(name)
            for k in range(nseg):
                colors.append(cmap(k/(nseg-1)))
        # 若不足 256，补最后一色
        cmap_background = plt.get_cmap('hot')
        while len(colors) < 24:
            colors.append(cmap_background)
        self.combined_cmap = ListedColormap(colors)

        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.img = self.ax.imshow(
            np.zeros((height, width)),
            extent=[xmin, xmax, ymin, ymax],
            origin='lower', interpolation='nearest',
            cmap=self.combined_cmap
        )
        plt.colorbar(self.img, ax=self.ax, label='Smooth Escape')

        self.rect = RectangleSelector(
            self.ax, self.on_select, useblit=True, button=[1],
            minspanx=5, minspany=5, spancoords='pixels', interactive=True
        )
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.update_plot()

    def update_plot(self):
        t0 = time.time()
        raw = compute_inverse(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height,
            self.max_iter, self.escape_radius
        )
        mask = raw < self.max_iter
        flat = raw[mask]
        hist, bins = np.histogram(flat, bins=256,
                                  range=(flat.min(), flat.max()), density=True)
        cdf = np.cumsum(hist); cdf /= cdf[-1]
        normed = np.interp(raw, bins[:-1], cdf)
        normed[~mask] = 0.0

        # 指数映射强化高值
        exp_mapped = normed ** self.gamma

        # 更新图像，恢复色条上限到 1
        self.img.set_data(exp_mapped)
        self.img.set_clim(0, 1)
        self.img.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        zoom = ((self.xmax - self.xmin)/(4.25 - (-1.5)))**(-0.5)
        self.ax.set_title(
            f"Inverse Mandelbrot | Iter={self.max_iter} | Zoom={zoom:.1f}× | {time.time()-t0:.2f}s"
        )
        self.fig.canvas.draw_idle()
        return exp_mapped

    def on_select(self, e1, e2):
        # 缓存当前视图
        arr = self.img.get_array().copy()
        self.view_stack.append((self.xmin, self.xmax,
                                self.ymin, self.ymax,
                                self.max_iter, arr))
        # 更新范围与迭代
        x1, y1 = e1.xdata, e1.ydata
        x2, y2 = e2.xdata, e2.ydata
        self.xmin, self.xmax = sorted([x1, x2])
        self.ymin, self.ymax = sorted([y1, y2])
        scale = (4.25 - (-1.5))/(self.xmax - self.xmin)
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
        zoom = ((xmax - xmin)/(4.25 - (-1.5)))**(-0.5)
        self.ax.set_title(
            f"Inverse Mandelbrot | Iter={iters} | Zoom={zoom:.1f}× (cached)"
        )
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    print("Initializing Inverse Mandelbrot Viewer…")
    viewer = InverseMandelViewer()
    plt.show()
