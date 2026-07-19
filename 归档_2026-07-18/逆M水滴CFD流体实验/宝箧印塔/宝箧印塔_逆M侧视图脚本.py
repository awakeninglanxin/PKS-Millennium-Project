#!/usr/bin/env python3
"""逆M宝箧印塔 — Farey九轮相轮半径 + 旋转覆钵 → 2D侧视"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ── 用已有CSV: 逆M水滴轮廓 (等价于1/3泡外廓) ──
csv = np.loadtxt(r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验\droplet_invM_analytic.csv', delimiter=',', skiprows=1)
x_drop, y_drop = csv[:,0], csv[:,1]

# ── Farey 1/q 泡中心 (标准M集公式, 逆M通过1/c映射) ──
farey_qs = [3,4,5,6,7,8,9,10,11]

def m_bulb_center(p, q):
    """Mandelbrot集 p/q 泡中心"""
    th = 2*np.pi*p/q
    return 0.5*np.exp(1j*th) - 0.25*np.exp(2j*th)

def estimate_bulb_radius(p, q, N=2000):
    """通过逃逸迭代近似泡半径：从中心向尖点方向逐步外扩直到逃逸"""
    c = m_bulb_center(p, q)
    # 泡直径方向：指向邻近泡 (p/q邻泡 或 主心形)
    # 简化：沿径向扫，周期检测
    r_test = np.linspace(0.01, 0.5, 200)
    is_inside = []
    for r in r_test:
        z = 0; c_test = c + r
        for _ in range(80):
            z = z*z + c_test
            if abs(z) > 2: is_inside.append(False); break
        else: is_inside.append(True)
    # 找第一个逃逸点
    for i, inside in enumerate(is_inside):
        if not inside: return r_test[max(0,i-1)]
    return r_test[-1]

# ── 计算九轮半径 ──
radii = []
centers = []
for q in farey_qs:
    c0 = m_bulb_center(1, q)
    r = estimate_bulb_radius(1, q)
    radii.append(r)
    centers.append(c0)
    print(f"  q={q:>2d}  c0=({c0.real:.4f}, {c0.imag:.4f})  r≈{r:.4f}")

# ── 第一张: M集泡图 ──
fig, axes = plt.subplots(1, 3, figsize=(18, 7))

# (A) M集泡圆心+近似半径
ax = axes[0]
# 画简单M集轮廓
xs = np.linspace(-2, 0.6, 600); ys = np.linspace(-1.3, 1.3, 400)
X,Y = np.meshgrid(xs,ys); C = X+1j*Y; Z = np.zeros_like(C)
for _ in range(30): Z = Z**2 + C
M = (abs(Z) < 2).astype(float)
ax.imshow(M, extent=[xs[0],xs[-1],ys[0],ys[-1]], origin='lower', cmap='binary', alpha=0.7)

# 标注泡
for i, (q, c0, r) in enumerate(zip(farey_qs, centers, radii)):
    color = plt.cm.RdYlGn(i/len(farey_qs))
    circle = plt.Circle((c0.real, c0.imag), r, fill=False, color=color, lw=2, alpha=0.8)
    ax.add_patch(circle)
    ax.plot(c0.real, c0.imag, 'o', color=color, ms=4)
    ax.text(c0.real, c0.imag+r+0.03, f'1/{q}', color=color, fontsize=8, ha='center')

ax.set_xlim(-2, 0.1); ax.set_ylim(-1.1, 1.1)
ax.set_title('M集 Farey 子泡 1/q 半径', fontsize=12, fontweight='bold')
ax.set_xlabel('Re(c)'); ax.set_ylabel('Im(c)')

# (B) 半径递减图
ax = axes[1]
ax.plot(farey_qs, radii, 'o-', color='#c0392b', lw=2, ms=8)
for q, r in zip(farey_qs, radii):
    ax.annotate(f'1/{q}\nr={r:.4f}', (q, r), textcoords="offset points", xytext=(0,12),
                ha='center', fontsize=8, color='#c0392b')
ax.set_xlabel('Farey分母 q'); ax.set_ylabel('泡近似半径')
ax.set_title('相轮九重半径递减', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)

# (C) 宝箧印塔侧视图 (2D堆叠)
ax = axes[2]
ax.set_aspect('equal')
# 塔身高度分配
z_base = 0; z_step = 0.8
tower_zs = [z_base + i*z_step for i in range(len(farey_qs))]

# 覆钵: 用逆M水滴真实轮廓，保持原始长宽比
# 水滴原始: x∈[-1.33,4.0] y∈[-1.6,1.6] → 宽高比≈1.67:1
x_center = (x_drop.max() + x_drop.min())/2
y_base = y_drop.min()
x_raw = x_drop - x_center  # 居中
y_raw = y_drop - y_base   # 底部对齐
scale_dome = 2.5 / y_raw.max()  # 统一比例因子(高度=2.5单位)
xs = x_raw * scale_dome
ys = y_raw * scale_dome + z_base

# 画左右对称轮廓
ax.plot(xs, ys, color='#5D4E37', lw=2)
ax.plot(-xs, ys, color='#5D4E37', lw=2)
# 填充
for i in range(0, len(xs), 3):
    ax.plot([-xs[i], xs[i]], [ys[i], ys[i]], color='#8B4513', lw=0.5, alpha=0.15)

# 画九轮圆盘
z_top = z_base + scale_dome
for i, (q, r) in enumerate(zip(farey_qs, radii)):
    z_pos = z_top + (i+1)*0.35
    scaled_r = r * 10  # 缩放到图大小
    ax.plot([-scaled_r, scaled_r], [z_pos, z_pos], color='#D4A017', lw=2)
    ax.fill_betweenx([z_pos-0.12, z_pos+0.12], -scaled_r, scaled_r,
                      color=plt.cm.YlOrBr((i+1)/len(farey_qs)), alpha=0.7)

# 刹尖
z_tip = z_top + 12*0.35 + 0.5
ax.plot([0, 0], [z_top+10*0.35, z_tip], color='#D4A017', lw=2)
ax.plot([0], [z_tip], marker='v', color='#FFD700', ms=10)

# 标签
for i, q in enumerate(farey_qs):
    z_pos = z_top + (i+1)*0.35 + 0.18
    ax.text(2.8, z_pos, f'1/{q}', fontsize=9, color='#555', va='center')

ax.text(2.8, z_top-0.5, '覆钵\n(1/3主泡)', fontsize=10, color='#5D4E37', ha='center')
ax.text(0, z_tip+0.3, '刹尖\n(c=1/4)', fontsize=9, color='#FFD700', ha='center')

ax.set_xlim(-4, 5); ax.set_ylim(z_base-0.5, z_tip+1.5)
ax.set_title('逆M宝箧印塔 侧视图\n(M集泡=相轮,水滴轮廓=覆钵)', fontsize=12, fontweight='bold')
ax.axis('off')

plt.tight_layout()
out = r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验\宝箧印塔_逆M侧视图.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'\n✅ {out}')
