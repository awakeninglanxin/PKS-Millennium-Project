#!/usr/bin/env python3
"""
SEG 3D等角投影视频 — 阶梯高度 + 旋转滚筒
GPU服务器: matplotlib 3D + PolygonCollection + ffmpeg
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation, FFMpegWriter
import os, sys, time, gc

# ── 几何参数 ──
# 半径（从中心向外）
R_INNER_STATOR = 48    # 内定子（中心，最小）
R_INNER_ROLLER = 100   # 内滚筒（包裹内定子）
R_MID_STATOR   = 148   # 中定子
R_MID_ROLLER   = 195   # 中滚筒
R_OUTER_STATOR = 245   # 外定子
R_OUTER_ROLLER = 295   # 外滚筒（最外层）

ROLLER_R = 10   # 滚筒半径
N_POLES = 34    # 每滚筒磁极数
STATORS = [18522, 11466, 4410]  # 外/中/内

# 高度（内环高→外环矮，阶梯式）
H_INNER_STATOR = 50
H_INNER_ROLLER = 45
H_MID_STATOR   = 35
H_MID_ROLLER   = 30
H_OUTER_STATOR = 22
H_OUTER_ROLLER = 18

np.random.seed(42)

def make_cylinder_mesh(cx, cy, r, h, z_base, n_faces=24):
    """生成圆柱体三角面片（底面+顶面+侧面）"""
    angles = np.linspace(0, 2*np.pi, n_faces+1)[:-1]
    x_ring = cx + r * np.cos(angles)
    y_ring = cy + r * np.sin(angles)
    
    verts = []
    # 侧面
    for i in range(n_faces):
        j = (i+1) % n_faces
        v = [
            [x_ring[i], y_ring[i], z_base],
            [x_ring[j], y_ring[j], z_base],
            [x_ring[j], y_ring[j], z_base+h],
            [x_ring[i], y_ring[i], z_base+h],
        ]
        verts.append(v)
    # 顶面
    top_pts = [[x_ring[i], y_ring[i], z_base+h] for i in range(n_faces)]
    for i in range(1, n_faces-1):
        verts.append([top_pts[0], top_pts[i], top_pts[i+1]])
    # 底面
    bot_pts = [[x_ring[i], y_ring[i], z_base] for i in range(n_faces)]
    for i in range(1, n_faces-1):
        verts.append([bot_pts[0], bot_pts[i+1], bot_pts[i]])
    
    return verts


def make_ring_mesh(R, r_thick, h, z_base, n_faces=50):
    """生成环形定子（由许多小圆柱体环绕组成）"""
    angles = np.linspace(0, 2*np.pi, n_faces+1)[:-1]
    all_verts = []
    for a in angles:
        cx = R * np.cos(a)
        cy = R * np.sin(a)
        all_verts.extend(make_cylinder_mesh(cx, cy, r_thick, h, z_base, 8))
    return all_verts


def draw_frame(ax, angle, n_outer, n_mid, n_inner):
    """绘制单帧"""
    ax.clear()
    ax.set_xlim(-320, 320)
    ax.set_ylim(-320, 320)
    ax.set_zlim(0, 70)
    
    # 等角投影视角
    ax.view_init(elev=28, azim=angle*0.8)  # 缓慢旋转视角
    ax.axis('off')
    ax.set_facecolor('#0a0a14')
    ax.set_box_aspect([1,1,0.25])
    
    # ── 外定子环 ──
    v = make_ring_mesh(R_OUTER_STATOR, 3, H_OUTER_STATOR, 0, 60)
    # 色带交替
    colors = []
    for i in range(len(v)):
        seg = i // (len(v)//80)
        colors.append('#ffaa44' if seg%2==0 else '#44aaff')
    pc = Poly3DCollection(v, facecolors=colors, edgecolors='none', alpha=0.7)
    ax.add_collection3d(pc)
    
    # ── 外滚筒 ──
    oa = angle * 0.015
    for j in range(n_outer):
        th = oa + 2*np.pi*j/n_outer
        cx = R_OUTER_ROLLER * np.cos(th)
        cy = R_OUTER_ROLLER * np.sin(th)
        v = make_cylinder_mesh(cx, cy, ROLLER_R, H_OUTER_ROLLER, 1, 12)
        colors = ['#1d9e75' if i%2==0 else '#155d40' for i in range(len(v))]
        pc = Poly3DCollection(v, facecolors=colors, edgecolors='#1d9e75', 
                              linewidths=0.3, alpha=0.8)
        ax.add_collection3d(pc)
    
    # ── 中定子环 ──
    v = make_ring_mesh(R_MID_STATOR, 3, H_MID_STATOR, 1, 50)
    colors = []
    for i in range(len(v)):
        seg = i // (len(v)//50)
        colors.append('#ffcc33' if seg%2==0 else '#3399ff')
    pc = Poly3DCollection(v, facecolors=colors, edgecolors='none', alpha=0.7)
    ax.add_collection3d(pc)
    
    # ── 中滚筒 ──
    ma = angle * 0.022
    for j in range(n_mid):
        th = ma + 2*np.pi*j/n_mid
        cx = R_MID_ROLLER * np.cos(th)
        cy = R_MID_ROLLER * np.sin(th)
        v = make_cylinder_mesh(cx, cy, ROLLER_R, H_MID_ROLLER, 2, 12)
        colors = ['#378add' if i%2==0 else '#1a4a80' for i in range(len(v))]
        pc = Poly3DCollection(v, facecolors=colors, edgecolors='#378add',
                              linewidths=0.3, alpha=0.8)
        ax.add_collection3d(pc)
    
    # ── 内定子环 ──
    v = make_ring_mesh(R_INNER_STATOR, 3, H_INNER_STATOR, 2, 40)
    colors = []
    for i in range(len(v)):
        seg = i // (len(v)//40)
        colors.append('#ff8833' if seg%2==0 else '#3388ff')
    pc = Poly3DCollection(v, facecolors=colors, edgecolors='none', alpha=0.7)
    ax.add_collection3d(pc)
    
    # ── 内滚筒（包裹内定子）──
    ia = angle * 0.032
    for j in range(n_inner):
        th = ia + 2*np.pi*j/n_inner
        cx = R_INNER_ROLLER * np.cos(th)
        cy = R_INNER_ROLLER * np.sin(th)
        v = make_cylinder_mesh(cx, cy, ROLLER_R, H_INNER_ROLLER, 3, 12)
        colors = ['#ba7517' if i%2==0 else '#6a3d08' for i in range(len(v))]
        pc = Poly3DCollection(v, facecolors=colors, edgecolors='#ba7517',
                              linewidths=0.3, alpha=0.8)
        ax.add_collection3d(pc)
    
    # ── 标签 ──
    ax.text(0, 0, H_INNER_STATOR+10, '内定子\n4410极', color='#ff8833',
           fontsize=8, ha='center', fontweight='bold')
    ax.text(0, R_MID_ROLLER+5, H_MID_ROLLER+8, '中滚筒×'+str(n_mid), color='#378add',
           fontsize=7, ha='center')
    ax.text(0, R_OUTER_ROLLER+5, H_OUTER_ROLLER+6, '外滚筒×'+str(n_outer), color='#1d9e75',
           fontsize=7, ha='center')

    # 高度标注线
    for r, h, lbl in [(R_INNER_STATOR, H_INNER_STATOR, '内定子'),
                       (R_INNER_ROLLER, H_INNER_ROLLER, '内滚筒'),
                       (R_MID_STATOR, H_MID_STATOR, '中定子'),
                       (R_MID_ROLLER, H_MID_ROLLER, '中滚筒'),
                       (R_OUTER_STATOR, H_OUTER_STATOR, '外定子'),
                       (R_OUTER_ROLLER, H_OUTER_ROLLER, '外滚筒')]:
        pass  # height annotations via text labels above
    
    return []


def generate():
    print("SEG 3D等角投影视频生成...")
    print(f"配置: 外/中/内滚筒数: 34/21/13 (Fibonacci gcd=1)")
    
    fig = plt.figure(figsize=(10, 10), dpi=120, facecolor='#0a0a14')
    ax = fig.add_subplot(111, projection='3d')
    
    n_frames = 180  # 6秒@30fps, 慢速旋转一周
    print(f"总帧数: {n_frames}, 时长: {n_frames/30:.1f}秒 @30fps")
    
    def animate(frame):
        angle = frame * (360.0 / n_frames)
        return draw_frame(ax, angle, 34, 21, 13)
    
    anim = FuncAnimation(fig, animate, frames=n_frames, interval=33.3, blit=False)
    
    out = '/root/seg_3d_isometric.mp4'
    writer = FFMpegWriter(fps=30, bitrate=5000, codec='h264')
    
    t0 = time.time()
    anim.save(out, writer=writer, dpi=120)
    elapsed = time.time() - t0
    
    size = os.path.getsize(out)
    print(f"✓ 完成: {out} ({size/1024/1024:.1f}MB, {elapsed:.1f}s)")
    
    plt.close()
    gc.collect()
    return out

if __name__ == '__main__':
    generate()
