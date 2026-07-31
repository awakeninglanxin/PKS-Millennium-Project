#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务1: Farey-编码芯片版图数据集生成器

输入: Farey 分数 (period 2-9, M=15 锚点)
输出: 256×256 像素化版图图像 (PNG) + 拓扑标注 (JSON)

用途: 训练 CNN EM 仿真器 / 验证 Farey 拓扑的物理可实现性
"""
import numpy as np, matplotlib.pyplot as plt, os, json, random
from math import gcd, pi, cos, sin

od = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(od, 'Farey_版图数据集')
os.makedirs(OUT_DIR, exist_ok=True)

# ====== 1. Farey 分数生成 (period 2-9) ======
def farey_fractions(period):
    """生成 period n 上半平面的既约分数 p/q"""
    fracs = []
    for p in range(1, period):
        if gcd(p, period) == 1:
            fracs.append((p, period))
    return fracs

# 所有 period 2-9 的 Farey 锚点
anchors = {}
for n in range(2, 10):
    fracs = farey_fractions(n)
    # 只取上半平面 (去掉对称的)
    unique = []
    for p, q in fracs:
        angle = 2 * pi * p / q
        if angle <= pi:  # 上半平面
            unique.append((p, q, angle))
    anchors[n] = unique

M15_anchors = []
for n, fracs in anchors.items():
    for p, q, angle in fracs:
        # Farey 锚点 → 心形上的坐标
        cx = 0.5 * cos(angle) - 0.25 * cos(2 * angle)
        cy = 0.5 * sin(angle) - 0.25 * sin(2 * angle)
        M15_anchors.append({'period': n, 'p': p, 'q': q,
                            'angle': angle, 'cx': cx, 'cy': cy,
                            'phi_n': len(farey_fractions(n))})

print(f'Farey anchors generated: {len(M15_anchors)}')

# ====== 2. 版图渲染引擎 ======
def render_chiplet_layout(anchors, size=256, style='pixelated'):
    """将 Farey 锚点渲染为芯片版图图像"""
    img = np.zeros((size, size, 3))
    node_positions = {}

    # 归一化坐标 → 像素
    cx_vals = [a['cx'] for a in anchors]
    cy_vals = [a['cy'] for a in anchors]
    cx_min, cx_max = min(cx_vals), max(cx_vals)
    cy_min, cy_max = min(cy_vals), max(cy_vals)

    for i, a in enumerate(anchors):
        px = int((a['cx'] - cx_min) / (cx_max - cx_min + 1e-6) * (size * 0.7) + size * 0.15)
        py = int((a['cy'] - cy_min) / (cy_max - cy_min + 1e-6) * (size * 0.7) + size * 0.15)
        px = max(1, min(size - 2, px))
        py = max(1, min(size - 2, py))
        node_positions[i] = (px, py)

        # 节点大小 ∝ Euler totient φ(n) (互联带宽权重)
        r = max(2, int(a['phi_n'] * 2.5))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        if style == 'pixelated':
                            # 像素化 (普林斯顿高频风格)
                            img[ny, nx] = [1.0, 0.5 + 0.1 * a['period'], 0.1 + 0.02 * a['phi_n']]
                        else:
                            img[ny, nx] = [0.3, 0.6, 0.9]

    # 画互联边 (Farey 树父子连接)
    for i in range(len(anchors)):
        for j in range(i + 1, len(anchors)):
            # Farey 临近性判断: 共享相同的 period 或者是 Farey 邻居
            if anchors[i]['period'] == anchors[j]['period'] or \
               abs(anchors[i]['angle'] - anchors[j]['angle']) < 0.3:
                x1, y1 = node_positions[i]
                x2, y2 = node_positions[j]
                # 画直线连线
                steps = max(abs(x2 - x1), abs(y2 - y1))
                if steps == 0: continue
                for t in range(steps + 1):
                    x = int(x1 + (x2 - x1) * t / steps)
                    y = int(y1 + (y2 - y1) * t / steps)
                    if 0 <= x < size and 0 <= y < size:
                        img[y, x] = [0.2, 0.2, 0.2]

    return img, node_positions

# ====== 3. 生成数据集 ======
N_SAMPLES = 100
dataset_index = []

for i in range(N_SAMPLES):
    # 随机选择 period 2-9 的子集 (模拟不同设计约束)
    subset_periods = random.sample(range(2, 10), random.randint(3, 8))
    subset_anchors = [a for a in M15_anchors if a['period'] in subset_periods]

    # 随机扰动锚点位置 (模拟制造偏差)
    for a in subset_anchors:
        a['cx'] += random.uniform(-0.02, 0.02)
        a['cy'] += random.uniform(-0.02, 0.02)

    style = random.choice(['pixelated', 'classical'])
    img, pos = render_chiplet_layout(subset_anchors, style=style)

    # 保存
    fname = f'farey_chiplet_{i:04d}'
    png_path = os.path.join(OUT_DIR, fname + '.png')
    plt.imsave(png_path, img)

    # 标注
    label = {
        'id': i,
        'periods': subset_periods,
        'n_anchors': len(subset_anchors),
        'style': style,
        'phi_weights': [a['phi_n'] for a in subset_anchors],
        'topology': 'farey_tree',
        'file': fname + '.png'
    }
    dataset_index.append(label)

with open(os.path.join(OUT_DIR, 'dataset_index.json'), 'w') as f:
    json.dump(dataset_index, f, indent=2)

print(f'Dataset generated: {N_SAMPLES} samples in {OUT_DIR}')
print(f'Index: {os.path.join(OUT_DIR, "dataset_index.json")}')
