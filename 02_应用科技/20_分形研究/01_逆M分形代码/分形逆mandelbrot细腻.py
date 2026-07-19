#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-precision Inverse Mandelbrot Deep-Zoom Viewer
- 自动根据放大级别调整 mpmath 精度
- 双线性插值关闭，使用 nearest 确保像素比分辨率
- 平滑逃逸次数 + 直方图均衡化 + 环形色盘
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import time
import warnings
from mpmath import mp, mpc, log

# ==================== 高精度平滑逃逸计数 ====================
def smooth_inverse_point_hp(cr, ci, max_iter, escape_radius):
    c = mpc(cr, ci)
    if abs(c) < mp.mpf('1e-12'):
        return mp.mpf(max_iter)
    c = 1/c
    z = mpc(0)
    for n in range(max_iter):
        z = z*z + c
        if abs(z) > escape_radius:
            return mp.mpf(n + 1) - log(log(abs(z)), 2)
    return mp.mpf(max_iter)

class HPInverseMandelbrotViewer:
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

        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.img = self.ax.imshow(
            np.zeros((height, width)),
            extent=[xmin, xmax, ymin, ymax],
            origin='lower',
            interpolation='nearest',
            cmap='rainbow'
        )
        plt.colorbar(self.img, ax=self.ax, label='Equalized & Cycled')

        self.rect = RectangleSelector(
            self.ax, self.on_select,
            useblit=True, button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.update_plot()

    def calc_precision(self):
        span = self.xmax - self.xmin
        needed = int(-np.log10(span)) + 10
        return max(30, needed)

    def update_title(self):
        zoom = ((self.xmax - self.xmin)/(4.25 - (-1.5)))**(-0.5)
        self.ax.set_title(
            f"High-Precision Inv Mandelbrot | Iter={self.max_iter} | Zoom={zoom:.1f}×\n"
            f"x=[{self.xmin:.5g}, {self.xmax:.5g}]  y=[{self.ymin:.5g}, {self.ymax:.5g}]\n"
            "[Left drag] Zoom   [Right click/Backspace] Back   [1–9] Set Iter"
        )

    def update_plot(self):
        # 修正：直接设置 mp.dps
        mp.dps = self.calc_precision()

        t0 = time.time()
        raw = np.empty((self.height, self.width), dtype=np.float64)
        xmin_mp = mp.mpf(self.xmin)
        xmax_mp = mp.mpf(self.xmax)
        ymin_mp = mp.mpf(self.ymin)
        ymax_mp = mp.mpf(self.ymax)
        for j in range(self.height):
            im = ymin_mp + j*(ymax_mp - ymin_mp)/(self.height - 1)
            for i in range(self.width):
                re = xmin_mp + i*(xmax_mp - xmin_mp)/(self.width - 1)
                val = smooth_inverse_point_hp(re, im,
                                              self.max_iter,
                                              mp.mpf(self.escape_radius))
                raw[j, i] = float(val)

        mask = raw < self.max_iter
        flat = raw[mask]
        hist, bins = np.histogram(flat, bins=256,
                                  range=(flat.min(), flat.max()),
                                  density=True)
        cdf = np.cumsum(hist)
        cdf /= cdf[-1]
        normed = np.interp(raw, bins[:-1], cdf)
        normed[~mask] = 0.0

        self.img.set_data(normed)
        self.img.set_clim(0.0, 1.0)
        self.img.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        self.update_title()
        self.fig.canvas.draw_idle()
        print(f"Render time: {time.time()-t0:.2f}s  (dps={mp.dps})")

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
            self.base_iter = int(event.key) * 100
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
    print("初始化高精度视图器……首次运行可能较慢")
    viewer = HPInverseMandelbrotViewer()
    plt.show()
